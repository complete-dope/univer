#!/usr/bin/env python3
"""
DCF Automation - Pure Python DCF Calculator

No AI. No smolagents. Just:
1. Fetch data from Yahoo Finance (yfinance)
2. Run deterministic calculations
3. Generate spreadsheet

Usage:
    python dcf_automation.py AAPL
    python dcf_automation.py MSFT --output ./results
"""

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

from models import FinancialData, Assumptions
from tools import fetch_all_financial_data, calculate_cagr, run_all_validations
from tools.calculation_tools import run_dcf_valuation, run_sensitivity_analysis


def extract_ticker(prompt: str) -> str:
    """Extract ticker from user input - simple string matching, no AI."""
    prompt_lower = prompt.lower().strip()
    
    # Common mappings - check these first (before extracting raw words)
    ticker_map = {
        'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL',
        'alphabet': 'GOOGL', 'amazon': 'AMZN', 'tesla': 'TSLA',
        'nvidia': 'NVDA', 'meta': 'META', 'facebook': 'META',
        'netflix': 'NFLX', 'berkshire': 'BRK-B', 'jpmorgan': 'JPM',
        'johnson': 'JNJ', 'jnj': 'JNJ', 'visa': 'V',
        'mastercard': 'MA', 'exxon': 'XOM', 'exxonmobil': 'XOM',
        'chevron': 'CVX', 'procter': 'PG', 'pg': 'PG',
        'unitedhealth': 'UNH', 'home depot': 'HD', 'hd': 'HD',
        'salesforce': 'CRM', 'adobe': 'ADBE', 'paypal': 'PYPL',
        'intel': 'INTC', 'amd': 'AMD', 'qualcomm': 'QCOM',
        'cisco': 'CSCO', 'pepsi': 'PEP', 'coca cola': 'KO',
        'ko': 'KO', 'disney': 'DIS', 'nike': 'NKE',
        'mcdonalds': 'MCD', 'starbucks': 'SBUX', 'costco': 'COST',
        'walmart': 'WMT', 'target': 'TGT', 'lowes': 'LOW',
    }
    
    # Check mappings first
    for name, symbol in ticker_map.items():
        if name in prompt_lower:
            return symbol
    
    # Try to extract uppercase ticker directly from words
    words = prompt.upper().split()
    for word in words:
        clean = word.strip('.,!?-')
        # Valid tickers: 1-12 letters/numbers (US: 1-5, International up to 12)
        if 1 <= len(clean) <= 12 and clean.replace('.', '').isalnum():
            return clean
    
    raise ValueError(f"Could not extract ticker from: {prompt}")


def run_dcf(ticker: str, output_dir: str = "./output") -> Dict[str, Any]:
    """Run complete DCF analysis - fully automated, no AI."""
    
    print("=" * 60)
    print(f"DCF AUTOMATION - {ticker}")
    print("=" * 60)
    
    # Step 1: Fetch data
    print("\n[1/5] Fetching financial data from Yahoo Finance...")
    data = fetch_all_financial_data(ticker, years=15)
    
    if not data.income_statements:
        raise ValueError(f"No financial data found for {ticker}")
    
    print(f"  ✓ {len(data.income_statements)} income statements")
    print(f"  ✓ {len(data.balance_sheets)} balance sheets")
    print(f"  ✓ {len(data.cash_flows)} cash flow statements")
    print(f"  ✓ Current price: ${data.current_price:.2f}")
    
    # Step 2: Validate
    print("\n[2/5] Validating data...")
    validation = run_all_validations(data)
    issues = sum(len(v) for v in validation.values())
    if issues > 0:
        print(f"  ⚠ {issues} warnings found (see trace file)")
    else:
        print("  ✓ All validations passed")
    
    # Step 3: Calculate historical metrics
    print("\n[3/5] Analyzing historical performance...")
    
    years = sorted(data.income_statements.keys())
    if len(years) >= 2:
        earliest_rev = data.income_statements[years[0]].revenue
        latest_rev = data.income_statements[years[-1]].revenue
        num_years = len(years) - 1
        revenue_cagr = calculate_cagr(earliest_rev, latest_rev, num_years)
    else:
        revenue_cagr = 0.05
        num_years = 0
    
    latest_income = data.get_latest_income()
    ebit_margin = latest_income.operating_margin if latest_income else 0.20
    
    print(f"  ✓ Revenue CAGR ({num_years}yr): {revenue_cagr:.1%}")
    print(f"  ✓ EBIT Margin: {ebit_margin:.1%}")
    
    # Step 4: Set conservative assumptions
    print("\n[4/5] Setting conservative assumptions...")
    
    assumptions = Assumptions()
    
    # Determine company type by growth
    if revenue_cagr > 0.20:
        company_type = "high_growth"
    elif revenue_cagr < 0.05:
        company_type = "mature"
    else:
        company_type = "growth"
    
    # Apply conservative adjustments
    assumptions.apply_conservative_adjustments(
        historical_cagr=revenue_cagr,
        historical_ebit_margin=ebit_margin,
        company_maturity=company_type
    )
    
    print(f"  ✓ Type: {company_type}")
    print(f"  ✓ Growth Y1-3: {assumptions.revenue_growth_y1_3:.1%}")
    print(f"  ✓ Growth Y4-7: {assumptions.revenue_growth_y4_7:.1%}")
    print(f"  ✓ Growth Y8-10: {assumptions.revenue_growth_y8_10:.1%}")
    print(f"  ✓ Terminal: {assumptions.terminal_growth_rate:.1%}")
    
    # Step 5: Run DCF
    print("\n[5/5] Running DCF valuation...")
    dcf = run_dcf_valuation(data, assumptions)
    
    # Run sensitivity
    sensitivity = run_sensitivity_analysis(
        data, assumptions,
        wacc_range=[0.07, 0.08, 0.09, 0.10, 0.11, 0.12],
        growth_range=[0.01, 0.02, 0.03, 0.04, 0.05]
    )
    dcf.sensitivity_wacc_growth = sensitivity
    
    # Save outputs
    os.makedirs(output_dir, exist_ok=True)
    
    # JSON data for spreadsheet
    data_file = os.path.join(output_dir, f"{ticker}_data.json")
    output_data = {
        "financial_data": {
            "ticker": data.ticker,
            "company_name": data.company_name,
            "current_price": data.current_price,
            "shares_outstanding": data.shares_outstanding,
            "beta": data.beta,
            "income_statements": {k: asdict(v) for k, v in data.income_statements.items()},
            "balance_sheets": {k: asdict(v) for k, v in data.balance_sheets.items()},
            "cash_flows": {k: asdict(v) for k, v in data.cash_flows.items()},
        },
        "dcf_result": {
            **asdict(dcf),
            "projections": [asdict(p) for p in dcf.projections],
        },
        "assumptions": asdict(assumptions),
    }
    with open(data_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    # Execution trace
    trace = {
        "ticker": ticker,
        "company_name": data.company_name,
        "valuation": dcf.get_summary(),
        "assumptions": {
            "revenue_growth_y1_3": assumptions.revenue_growth_y1_3,
            "revenue_growth_y4_7": assumptions.revenue_growth_y4_7,
            "revenue_growth_y8_10": assumptions.revenue_growth_y8_10,
            "terminal_growth": assumptions.terminal_growth_rate,
            "wacc": dcf.wacc,
        },
        "validation": validation,
        "files": {
            "data": data_file,
        }
    }
    trace_file = os.path.join(output_dir, f"{ticker}_trace.json")
    with open(trace_file, 'w') as f:
        json.dump(trace, f, indent=2)
    
    # Print results
    print("\n" + "=" * 60)
    print("VALUATION COMPLETE")
    print("=" * 60)
    print(f"\n📊 {data.company_name} ({ticker})")
    print(f"\n💰 Intrinsic Value:     ${dcf.intrinsic_value_per_share:.2f}")
    print(f"📈 Current Price:       ${dcf.current_price:.2f}")
    print(f"📉 Margin of Safety:    {dcf.margin_of_safety:+.1f}%")
    
    verdict_emoji = {
        'UNDERVALUED': '🟢', 'OVERVALUED': '🔴', 'FAIRLY_VALUED': '🟡',
    }.get(dcf.verdict, '⚪')
    print(f"\n{verdict_emoji} VERDICT: {dcf.verdict}")
    
    print(f"\n📊 Enterprise Value:    ${dcf.enterprise_value/1e9:.1f}B")
    print(f"📊 Equity Value:        ${dcf.equity_value/1e9:.1f}B")
    print(f"📊 WACC:                {dcf.wacc:.2%}")
    print(f"📊 Terminal Growth:     {dcf.terminal_growth_rate:.1%}")
    
    print(f"\n📁 Output files:")
    print(f"   • {data_file}")
    print(f"   • {trace_file}")
    
    return trace


def main():
    parser = argparse.ArgumentParser(
        description='DCF Automation - Pure Python DCF Calculator (No AI)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dcf_automation.py AAPL
  python dcf_automation.py --prompt "DCF for Apple"
  python dcf_automation.py "Create DCF for Microsoft"
  python dcf_automation.py TSLA --output ./results
        """
    )
    parser.add_argument('input', nargs='?', help='Ticker or natural language prompt')
    parser.add_argument('--ticker', '-t', help='Stock ticker (e.g., AAPL)')
    parser.add_argument('--prompt', '-p', help='Natural language prompt (e.g., "DCF for Apple")')
    parser.add_argument('--output', '-o', default='./output', help='Output directory')
    
    args = parser.parse_args()
    
    # Get ticker
    if args.ticker:
        ticker = args.ticker.upper()
    elif args.prompt:
        ticker = extract_ticker(args.prompt)
    elif args.input:
        # Try to determine if input is ticker or prompt
        input_clean = args.input.strip().upper()
        # If single word 1-12 chars and alphanumeric, treat as ticker
        is_single_word = len(input_clean.split()) == 1
        is_ticker_format = 1 <= len(input_clean) <= 12 and input_clean.replace('.', '').isalnum()
        
        if is_single_word and is_ticker_format and ' ' not in args.input.strip():
            ticker = input_clean
        else:
            # Treat as natural language prompt
            ticker = extract_ticker(args.input)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Run DCF
    try:
        results = run_dcf(ticker, args.output)
        return results
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
