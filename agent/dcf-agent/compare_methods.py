#!/usr/bin/env python3
"""
Compare Standard DCF vs Buffett Owner Earnings Method

Shows side-by-side comparison for the 4 companies.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def load_standard_valuation(ticker: str) -> dict:
    """Load standard DCF results"""
    try:
        with open(f'./output/{ticker}_trace.json', 'r') as f:
            return json.load(f)['valuation']
    except:
        return None

def load_buffett_valuation(ticker: str) -> dict:
    """Load Buffett DCF results"""
    try:
        with open(f'./output/{ticker}_buffett_valuation.json', 'r') as f:
            data = json.load(f)
            # Merge valuation with other fields
            result = data.get('valuation', {})
            result['assumptions'] = data.get('assumptions', {})
            result['market_expectations'] = data.get('market_expectations', {})
            return result
    except:
        return None

def print_comparison():
    """Print side-by-side comparison"""
    
    companies = {
        'AAPL': 'Apple Inc.',
        'GOOGL': 'Alphabet/Google',
        'INFY': 'Infosys',
    }
    
    print("=" * 100)
    print("DCF METHODOLOGY COMPARISON")
    print("=" * 100)
    print()
    print("Standard DCF: FCF - WACC - Complex assumptions")
    print("Buffett Method: Owner Earnings - Simple 5% rate - Maintenance CapEx separated")
    print()
    print("-" * 100)
    print(f"{'Company':<20} {'Current':<10} {'Std DCF':<12} {'Buffett':<12} {'EV/EBITDA':<12} {'Avg':<12} {'Verdict':<15}")
    print("-" * 100)
    
    for ticker, name in companies.items():
        std = load_standard_valuation(ticker)
        buff = load_buffett_valuation(ticker)
        
        if std and buff:
            current = std['current_price']
            std_val = std['intrinsic_value']
            buff_val = buff['buffett_dcf']
            ev_ebitda = buff['ev_ebitda']
            final = buff['final_value']
            verdict = buff['verdict']
            
            print(f"{name:<20} ${current:<9.2f} ${std_val:<11.2f} ${buff_val:<11.2f} ${ev_ebitda:<11.2f} ${final:<11.2f} {verdict:<15}")
    
    print("-" * 100)
    print()
    
    # Detailed analysis
    print("=" * 100)
    print("DETAILED ANALYSIS BY COMPANY")
    print("=" * 100)
    print()
    
    for ticker, name in companies.items():
        std = load_standard_valuation(ticker)
        buff = load_buffett_valuation(ticker)
        
        if not (std and buff):
            continue
        
        print(f"\n{name} ({ticker})")
        print("-" * 80)
        print(f"  Current Price:        ${std['current_price']:.2f}")
        print()
        print(f"  Standard DCF:         ${std['intrinsic_value']:.2f} (Margin: {std['margin_of_safety']:+.1f}%)")
        print(f"    - Uses: FCF - WACC ({std['wacc']:.1f}%) - 10yr forecast")
        print(f"    - Problem: Complex, sensitive to terminal value assumptions")
        print()
        print(f"  Buffett Owner Earn:   ${buff['buffett_dcf']:.2f}")
        print(f"    - Uses: Owner Earnings - 5% discount - Maintenance CapEx")
        print(f"    - Better: Simpler, focuses on true owner cash flow")
        print()
        ev_mult = buff.get('assumptions', {}).get('ev_ebitda_multiple', 15)
        print(f"  EV/EBITDA ({ev_mult:.0f}x):    ${buff['ev_ebitda']:.2f}")
        print(f"    - Market sanity check")
        print()
        print(f"  Final (Average):      ${buff['final_value']:.2f}")
        print(f"  VERDICT: {buff['verdict']}")
        print()
        print(f"  Market Expects:     {buff['market_expectations']['implied_growth']:.1%} growth")
        print(f"  Our Assumption:     {buff['assumptions']['growth_y1_5']:.1%} growth")
        
        # Commentary
        implied = buff['market_expectations']['implied_growth']
        assumed = buff['assumptions']['growth_y1_5']
        
        if implied > assumed * 1.5:
            print(f"  ⚠️  Market expects much higher growth than our conservative model")
        elif implied < assumed * 0.5:
            print(f"  ✅ Market expects lower growth - potential opportunity if we\'re right")
    
    print()
    print("=" * 100)
    print("KEY INSIGHTS")
    print("=" * 100)
    print()
    print("1. Buffett Method vs Standard DCF:")
    print("   - Apple: $260 vs $111 (Buffett higher due to better owner earnings)")
    print("   - Google: $2260 vs $248 (HUGE difference - low maintenance CapEx, simple discount rate)")
    print("   - Infosys: $30 vs $19 (Similar range)")
    print()
    print("2. Why Differences:")
    print("   - Standard DCF uses total CapEx (over-penalizes growth investments)")
    print("   - Buffett method separates maintenance vs growth CapEx")
    print("   - Simple 5% discount vs complex WACC (often 8-12%)")
    print("   - Owner Earnings often > FCF for tech companies with low maintenance needs")
    print()
    print("3. Which is Right?")
    print("   - Neither is 'perfect' - both are approximations")
    print("   - Buffett method closer to how businesses actually generate cash")
    print("   - Multiple methods (triangulation) better than single model")
    print("   - Google at $400 vs Buffett $2260 suggests market pricing in low growth")
    print()
    print("4. Conservative Assumptions Still Matter:")
    print("   - Even Buffett method uses 20% growth decay")
    print("   - Terminal growth capped at 2.5%")
    print("   - Margin of safety required for conviction")
    print()
    print("=" * 100)

if __name__ == "__main__":
    print_comparison()
