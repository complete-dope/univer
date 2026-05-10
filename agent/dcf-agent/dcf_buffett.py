#!/usr/bin/env python3
"""
Buffett-Style DCF Automation

Improved methodology based on:
1. Owner Earnings (not FCF) - separates maintenance from growth CapEx
2. Simple discount rate (long-term Treasury rate, not complex WACC)
3. Maintenance CapEx estimation via 5-year PPE/Sales ratio
4. Multiple valuation methods for triangulation
5. Data caching to avoid repeated API calls

Usage:
    python dcf_buffett.py AAPL
    python dcf_buffett.py --cache-dir ./cache --use-cache
"""

import argparse
import json
import os
import pickle
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from models import FinancialData, Assumptions
from tools import fetch_all_financial_data, calculate_cagr
from tools.calculation_tools import calculate_cost_of_equity


# Cache configuration
CACHE_DIR = "./cache"
CACHE_EXPIRY_DAYS = 7


def get_cache_path(ticker: str) -> str:
    """Get cache file path for ticker"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{ticker}_financial_data.pkl")


def is_cache_valid(cache_path: str) -> bool:
    """Check if cache file exists and is not expired"""
    if not os.path.exists(cache_path):
        return False
    
    # Check age
    mtime = os.path.getmtime(cache_path)
    age_days = (datetime.now().timestamp() - mtime) / (24 * 3600)
    return age_days < CACHE_EXPIRY_DAYS


def load_cached_data(ticker: str) -> Optional[FinancialData]:
    """Load financial data from cache if available and valid"""
    cache_path = get_cache_path(ticker)
    
    if is_cache_valid(cache_path):
        print(f"  📦 Loading cached data for {ticker}")
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    return None


def save_cached_data(ticker: str, data: FinancialData):
    """Save financial data to cache"""
    cache_path = get_cache_path(ticker)
    with open(cache_path, 'wb') as f:
        pickle.dump(data, f)
    print(f"  💾 Saved data to cache: {cache_path}")


def calculate_maintenance_capex(
    financial_data: FinancialData,
    year: str
) -> float:
    """
    Estimate maintenance CapEx using Greenwald method.
    
    Formula: (Current Sales × 5yr avg PPE/Sales) - Depreciation
    If negative, use 50% of D&A as proxy.
    """
    # Get 5-year historical PPE/Sales ratio
    ppe_sales_ratios = []
    years = sorted(financial_data.balance_sheets.keys())[:5]
    
    for y in years:
        bs = financial_data.balance_sheets.get(y)
        inc = financial_data.income_statements.get(y)
        if bs and inc and inc.revenue > 0:
            ratio = bs.ppe / inc.revenue
            ppe_sales_ratios.append(ratio)
    
    if not ppe_sales_ratios:
        return 0.0
    
    avg_ppe_sales = sum(ppe_sales_ratios) / len(ppe_sales_ratios)
    
    # Get current year data
    bs = financial_data.balance_sheets.get(year)
    inc = financial_data.income_statements.get(year)
    cf = financial_data.cash_flows.get(year)
    
    if not (bs and inc and cf):
        return 0.0
    
    # Calculate required PPE for current sales
    required_ppe = inc.revenue * avg_ppe_sales
    
    # Maintenance CapEx = Required PPE growth + Depreciation replacement
    # Simplified: (New PPE - Old PPE) + Depreciation
    # But we use Greenwald method:
    maintenance_capex = max(0, required_ppe - bs.ppe) + cf.depreciation_amortization
    
    # If calculation gives negative, use 50% of D&A as proxy
    if maintenance_capex <= 0:
        maintenance_capex = cf.depreciation_amortization * 0.5
    
    return maintenance_capex


def calculate_owner_earnings(
    financial_data: FinancialData,
    year: str
) -> float:
    """
    Calculate Buffett's Owner Earnings.
    
    Owner Earnings = Net Income 
                     + Depreciation/Amortization 
                     - Maintenance CapEx
                     +/- Change in Working Capital
    """
    inc = financial_data.income_statements.get(year)
    cf = financial_data.cash_flows.get(year)
    
    if not inc or not cf:
        return 0.0
    
    maintenance_capex = calculate_maintenance_capex(financial_data, year)
    
    owner_earnings = (
        inc.net_income
        + cf.depreciation_amortization
        - maintenance_capex
        + cf.working_capital_change
    )
    
    return owner_earnings


def calculate_buffett_dcf(
    financial_data: FinancialData,
    discount_rate: float = 0.05,  # 5% - simple treasury-based rate
    growth_rate_years_1_5: float = 0.06,
    growth_rate_years_6_10: float = 0.04,
    terminal_growth: float = 0.025
) -> Dict[str, Any]:
    """
    Buffett-style DCF using Owner Earnings.
    
    Simpler than standard DCF:
    - No complex WACC calculation
    - Uses Owner Earnings (not FCF)
    - Maintenance CapEx properly separated
    - Simple discount rate (4-6% based on long-term Treasury)
    """
    
    # Get base owner earnings (latest year)
    years = sorted(financial_data.income_statements.keys())
    if not years:
        raise ValueError("No financial data available")
    
    base_year = years[-1]
    base_oe = calculate_owner_earnings(financial_data, base_year)
    
    if base_oe <= 0:
        # Try to find a year with positive owner earnings
        for year in reversed(years):
            oe = calculate_owner_earnings(financial_data, year)
            if oe > 0:
                base_oe = oe
                base_year = year
                break
        else:
            raise ValueError("No positive owner earnings found in any year")
    
    # Project owner earnings for 10 years
    projections = []
    current_oe = base_oe
    
    for year in range(1, 11):
        if year <= 5:
            growth = growth_rate_years_1_5
        else:
            growth = growth_rate_years_6_10
        
        current_oe = current_oe * (1 + growth)
        
        # Discount to present
        discount_factor = (1 + discount_rate) ** year
        pv_oe = current_oe / discount_factor
        
        projections.append({
            'year': year,
            'owner_earnings': current_oe,
            'growth_rate': growth,
            'discount_factor': discount_factor,
            'pv_oe': pv_oe
        })
    
    # Sum of discounted owner earnings
    sum_pv_oe = sum(p['pv_oe'] for p in projections)
    
    # Terminal Value using Gordon Growth Model
    terminal_oe = projections[-1]['owner_earnings'] * (1 + terminal_growth)
    terminal_value = terminal_oe / (discount_rate - terminal_growth)
    
    # Discount terminal value
    pv_terminal = terminal_value / ((1 + discount_rate) ** 10)
    
    # Enterprise Value
    enterprise_value = sum_pv_oe + pv_terminal
    
    # Equity Value (simpler than standard - no complex adjustments)
    latest_bs = financial_data.get_latest_balance()
    net_debt = latest_bs.long_term_debt - latest_bs.cash if latest_bs else 0
    
    equity_value = enterprise_value - net_debt
    
    # Per share
    shares = financial_data.shares_outstanding
    if shares > 0:
        value_per_share = equity_value / shares
    else:
        value_per_share = 0
    
    return {
        'ticker': financial_data.ticker,
        'base_owner_earnings': base_oe,
        'base_year': base_year,
        'projections': projections,
        'sum_pv_oe': sum_pv_oe,
        'terminal_value': terminal_value,
        'pv_terminal': pv_terminal,
        'enterprise_value': enterprise_value,
        'net_debt': net_debt,
        'equity_value': equity_value,
        'shares_outstanding': shares,
        'intrinsic_value_per_share': value_per_share,
        'current_price': financial_data.current_price,
        'discount_rate': discount_rate,
        'terminal_growth': terminal_growth,
        'margin_of_safety': (value_per_share - financial_data.current_price) / financial_data.current_price if financial_data.current_price > 0 else 0,
        'verdict': 'UNDERVALUED' if value_per_share > financial_data.current_price * 1.2 else ('OVERVALUED' if value_per_share < financial_data.current_price * 0.8 else 'FAIRLY_VALUED')
    }


def calculate_ev_ebitda_multiple(
    financial_data: FinancialData,
    target_multiple: float = 15.0  # Conservative market average
) -> float:
    """
    Simple EV/EBITDA multiple valuation as sanity check.
    
    EV = EBITDA × Multiple
    Equity Value = EV - Net Debt
    """
    latest_inc = financial_data.get_latest_income()
    latest_bs = financial_data.get_latest_balance()
    
    if not latest_inc or not latest_bs:
        return 0.0
    
    ebitda = latest_inc.ebitda
    enterprise_value = ebitda * target_multiple
    
    net_debt = latest_bs.long_term_debt - latest_bs.cash
    equity_value = enterprise_value - net_debt
    
    if financial_data.shares_outstanding > 0:
        return equity_value / financial_data.shares_outstanding
    return 0.0


def calculate_reverse_dcf(
    financial_data: FinancialData,
    max_growth: float = 0.20
) -> float:
    """
    Reverse DCF: Find implied growth rate at current price.
    
    Asks: What growth rate justifies current market price?
    """
    current_price = financial_data.current_price
    years = sorted(financial_data.income_statements.keys())
    
    if not years:
        return 0.0
    
    # Binary search for implied growth rate
    low, high = 0.0, max_growth
    
    for _ in range(50):  # 50 iterations for precision
        mid = (low + high) / 2
        
        # Calculate DCF with this growth rate
        try:
            result = calculate_buffett_dcf(
                financial_data,
                growth_rate_years_1_5=mid,
                growth_rate_years_6_10=mid * 0.7,
                discount_rate=0.05
            )
            
            implied_price = result['intrinsic_value_per_share']
            
            if implied_price < current_price:
                low = mid
            else:
                high = mid
        except:
            high = mid
    
    return (low + high) / 2


def run_comprehensive_valuation(
    ticker: str,
    use_cache: bool = True,
    save_results: bool = True
) -> Dict[str, Any]:
    """
    Run comprehensive valuation using multiple methods:
    1. Buffett Owner Earnings DCF
    2. EV/EBITDA Multiple (sanity check)
    3. Reverse DCF (market expectations)
    
    Returns triangulated valuation.
    """
    print(f"\n{'='*60}")
    print(f"BUFFETT-STYLE VALUATION - {ticker}")
    print(f"{'='*60}")
    
    # Step 1: Get data (from cache or fetch)
    print("\n[1/5] Loading financial data...")
    
    financial_data = None
    if use_cache:
        financial_data = load_cached_data(ticker)
    
    if financial_data is None:
        print(f"  🌐 Fetching from Yahoo Finance...")
        financial_data = fetch_all_financial_data(ticker, years=10)
        if save_results:
            save_cached_data(ticker, financial_data)
    
    print(f"  ✓ {financial_data.company_name}")
    print(f"  ✓ Current price: ${financial_data.current_price:.2f}")
    
    # Step 2: Calculate historical metrics
    print("\n[2/5] Analyzing historical performance...")
    
    years = sorted(financial_data.income_statements.keys())
    if len(years) >= 2:
        earliest_oe = calculate_owner_earnings(financial_data, years[0])
        latest_oe = calculate_owner_earnings(financial_data, years[-1])
        num_years = len(years) - 1
        
        if earliest_oe > 0:
            oe_cagr = calculate_cagr(earliest_oe, latest_oe, num_years)
        else:
            oe_cagr = 0.05
    else:
        oe_cagr = 0.05
    
    print(f"  ✓ Owner Earnings CAGR ({num_years}yr): {oe_cagr:.1%}")
    print(f"  ✓ Latest Owner Earnings: ${latest_oe/1e9:.1f}B" if latest_oe > 1e9 else f"  ✓ Latest Owner Earnings: ${latest_oe/1e6:.1f}M")
    
    # Step 3: Buffett DCF
    print("\n[3/5] Running Buffett Owner Earnings DCF...")
    
    # Conservative growth assumptions (decay historical by 20%)
    growth_y1_5 = max(0.02, min(oe_cagr * 0.8, 0.15))
    growth_y6_10 = growth_y1_5 * 0.7
    
    buffett_dcf = calculate_buffett_dcf(
        financial_data,
        discount_rate=0.05,  # 5% - simple, conservative
        growth_rate_years_1_5=growth_y1_5,
        growth_rate_years_6_10=growth_y6_10,
        terminal_growth=0.025
    )
    
    print(f"  ✓ Discount rate: 5.0% (simple Treasury-based)")
    print(f"  ✓ Growth Y1-5: {growth_y1_5:.1%}")
    print(f"  ✓ Growth Y6-10: {growth_y6_10:.1%}")
    print(f"  ✓ Intrinsic value: ${buffett_dcf['intrinsic_value_per_share']:.2f}")
    
    # Step 4: Multiple valuation
    print("\n[4/5] Running EV/EBITDA sanity check...")
    
    # Determine appropriate multiple based on sector/metrics
    latest_inc = financial_data.get_latest_income()
    if latest_inc:
        if latest_inc.revenue > 200e9:  # Mega-cap
            target_multiple = 12.0  # Lower for mature giants
        elif latest_inc.revenue > 50e9:
            target_multiple = 15.0
        else:
            target_multiple = 18.0
    else:
        target_multiple = 15.0
    
    ev_ebitda_value = calculate_ev_ebitda_multiple(financial_data, target_multiple)
    print(f"  ✓ EV/EBITDA multiple: {target_multiple:.1f}x")
    print(f"  ✓ Implied value: ${ev_ebitda_value:.2f}")
    
    # Step 5: Reverse DCF
    print("\n[5/5] Running Reverse DCF (market expectations)...")
    
    implied_growth = calculate_reverse_dcf(financial_data)
    print(f"  ✓ Market pricing in growth: {implied_growth:.1%}")
    
    # Triangulate final value
    print("\n" + "="*60)
    print("VALUATION TRIANGULATION")
    print("="*60)
    
    values = [
        buffett_dcf['intrinsic_value_per_share'],
        ev_ebitda_value,
    ]
    
    # Filter out zeros/negatives
    valid_values = [v for v in values if v > 0]
    
    if valid_values:
        median_value = sorted(valid_values)[len(valid_values)//2]
        avg_value = sum(valid_values) / len(valid_values)
    else:
        median_value = buffett_dcf['intrinsic_value_per_share']
        avg_value = median_value
    
    # Conservative: use average of methods
    final_value = avg_value
    
    current_price = financial_data.current_price
    margin_of_safety = (final_value - current_price) / current_price if current_price > 0 else 0
    
    if margin_of_safety > 0.2:
        verdict = "UNDERVALUED"
        emoji = "🟢"
    elif margin_of_safety < -0.2:
        verdict = "OVERVALUED"
        emoji = "🔴"
    else:
        verdict = "FAIRLY_VALUED"
        emoji = "🟡"
    
    print(f"\n📊 {financial_data.company_name} ({ticker})")
    print(f"\n  Buffett DCF:     ${buffett_dcf['intrinsic_value_per_share']:.2f}")
    print(f"  EV/EBITDA ({target_multiple:.0f}x): ${ev_ebitda_value:.2f}")
    print(f"  ─────────────────────────")
    print(f"  Final Value:     ${final_value:.2f}")
    print(f"  Current Price:   ${current_price:.2f}")
    print(f"  Margin of Safety: {margin_of_safety:+.1f}%")
    print(f"\n  {emoji} VERDICT: {verdict}")
    
    print(f"\n📈 Market expects: {implied_growth:.1%} growth (reverse DCF)")
    print(f"📈 Our assumption: {growth_y1_5:.1%} growth (conservative)")
    
    # Save results
    if save_results:
        output_dir = "./output"
        os.makedirs(output_dir, exist_ok=True)
        
        results = {
            'ticker': ticker,
            'company_name': financial_data.company_name,
            'date': datetime.now().isoformat(),
            'methodology': 'Buffett Owner Earnings',
            'valuation': {
                'buffett_dcf': buffett_dcf['intrinsic_value_per_share'],
                'ev_ebitda': ev_ebitda_value,
                'final_value': final_value,
                'current_price': current_price,
                'margin_of_safety': margin_of_safety,
                'verdict': verdict,
            },
            'assumptions': {
                'discount_rate': 0.05,
                'growth_y1_5': growth_y1_5,
                'growth_y6_10': growth_y6_10,
                'terminal_growth': 0.025,
                'ev_ebitda_multiple': target_multiple,
            },
            'market_expectations': {
                'implied_growth': implied_growth,
            },
            'owner_earnings': {
                'base_year': buffett_dcf['base_year'],
                'base_oe': buffett_dcf['base_owner_earnings'],
                'oe_cagr': oe_cagr,
            }
        }
        
        output_file = os.path.join(output_dir, f"{ticker}_buffett_valuation.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Saved to: {output_file}")
    
    return results


def extract_ticker(prompt: str) -> str:
    """Extract ticker from user input"""
    prompt_lower = prompt.lower().strip()
    
    ticker_map = {
        'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL',
        'alphabet': 'GOOGL', 'amazon': 'AMZN', 'tesla': 'TSLA',
        'nvidia': 'NVDA', 'meta': 'META', 'facebook': 'META',
        'netflix': 'NFLX', 'infosys': 'INFY', 'jpmorgan': 'JPM',
        'johnson': 'JNJ', 'jnj': 'JNJ', 'visa': 'V',
        'mastercard': 'MA', 'exxon': 'XOM',
    }
    
    for name, symbol in ticker_map.items():
        if name in prompt_lower:
            return symbol
    
    words = prompt.upper().split()
    for word in words:
        clean = word.strip('.,!?-')
        if 1 <= len(clean) <= 12 and clean.replace('.', '').isalnum():
            return clean
    
    raise ValueError(f"Could not extract ticker from: {prompt}")


def main():
    parser = argparse.ArgumentParser(
        description='Buffett-Style DCF with Owner Earnings (Better Methodology)'
    )
    parser.add_argument('input', nargs='?', help='Ticker or prompt')
    parser.add_argument('--ticker', '-t', help='Stock ticker')
    parser.add_argument('--prompt', '-p', help='Natural language prompt')
    parser.add_argument('--no-cache', action='store_true', help='Skip cache, fetch fresh data')
    parser.add_argument('--cache-dir', default='./cache', help='Cache directory')
    parser.add_argument('--output', '-o', default='./output', help='Output directory')
    
    args = parser.parse_args()
    
    # Determine ticker
    if args.ticker:
        ticker = args.ticker.upper()
    elif args.prompt:
        ticker = extract_ticker(args.prompt)
    elif args.input:
        input_clean = args.input.strip().upper()
        if len(input_clean.split()) == 1 and 1 <= len(input_clean) <= 12:
            ticker = input_clean
        else:
            ticker = extract_ticker(args.input)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Run valuation
    global CACHE_DIR
    CACHE_DIR = args.cache_dir
    
    try:
        results = run_comprehensive_valuation(
            ticker,
            use_cache=not args.no_cache,
            save_results=True
        )
        return results
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
