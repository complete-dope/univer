#!/usr/bin/env python3
"""
DCF AI Agent - Main Entry Point

Autonomous DCF valuation agent using:
- smolagents for agent orchestration
- Ollama for local LLM inference
- yfinance for financial data
- Univer for spreadsheet generation

Usage:
    python main.py "Create DCF for Apple"
    python main.py --ticker AAPL
    python main.py --prompt "Value Tesla"
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent))

from agents import run_dcf_analysis_parallel


def print_banner():
    """Print the startup banner"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║                  DCF AI AGENT                                  ║
║                                                                ║
║  Autonomous Discounted Cash Flow Valuation System             ║
║  Using smolagents + Ollama + Univer Spreadsheet Engine         ║
╚════════════════════════════════════════════════════════════════╝
    """)


def print_results(results: dict):
    """Pretty print the valuation results"""
    valuation = results.get("valuation", {})
    
    print("\n" + "=" * 60)
    print("VALUATION SUMMARY")
    print("=" * 60)
    
    print(f"\n📊 {results.get('company_name', 'Unknown')} ({results.get('ticker', 'N/A')})")
    print(f"\n💰 Intrinsic Value:     ${valuation.get('intrinsic_value', 0):.2f}")
    print(f"📈 Current Price:       ${valuation.get('current_price', 0):.2f}")
    print(f"📉 Margin of Safety:    {valuation.get('margin_of_safety', 0):+.1f}%")
    
    verdict = valuation.get('verdict', 'UNKNOWN')
    verdict_emoji = {
        'UNDERVALUED': '🟢',
        'OVERVALUED': '🔴',
        'FAIRLY_VALUED': '🟡',
    }.get(verdict, '⚪')
    
    print(f"\n{verdict_emoji} VERDICT: {verdict}")
    
    print(f"\n📊 Enterprise Value:    ${valuation.get('enterprise_value', 0):.2f}B")
    print(f"📊 Equity Value:        ${valuation.get('equity_value', 0):.2f}B")
    print(f"📊 WACC:                {valuation.get('wacc', 0):.2f}%")
    print(f"📊 Terminal Growth:     {valuation.get('terminal_growth', 0):.1f}%")
    
    print("\n" + "=" * 60)
    
    # Show output files
    output_dir = results.get('output_dir', './output')
    ticker = results.get('ticker', 'UNKNOWN')
    
    print(f"\n📁 Output files:")
    print(f"   • {output_dir}/{ticker}_trace.json")
    print(f"   • {output_dir}/{ticker}_DCF.json")
    print(f"   • {output_dir}/{ticker}_data.json")


def interactive_mode():
    """Run in interactive mode"""
    print_banner()
    
    print("\nEnter your DCF request (e.g., 'Create DCF for Apple'):")
    print("Or type 'quit' to exit\n")
    
    while True:
        try:
            user_input = input("> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye! 👋")
                break
            
            if not user_input:
                continue
            
            # Run analysis
            results = run_dcf_analysis_parallel(user_input)
            print_results(results)
            
            print("\n" + "-" * 60)
            print("Enter another request or 'quit' to exit:")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'quit' to exit.")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='DCF AI Agent - Autonomous valuation system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Create DCF for Apple"
  python main.py --ticker AAPL
  python main.py --prompt "Value Tesla" --output ./results
  python main.py --interactive
        """
    )
    
    parser.add_argument(
        'prompt',
        nargs='?',
        help='DCF request (e.g., "Create DCF for Apple")'
    )
    parser.add_argument(
        '--ticker',
        '-t',
        help='Stock ticker symbol (e.g., AAPL)'
    )
    parser.add_argument(
        '--prompt',
        '-p',
        help='DCF request prompt'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='./output',
        help='Output directory (default: ./output)'
    )
    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help='Run in interactive mode'
    )
    parser.add_argument(
        '--json',
        '-j',
        action='store_true',
        help='Output results as JSON'
    )
    
    args = parser.parse_args()
    
    # Interactive mode
    if args.interactive:
        interactive_mode()
        return
    
    # Determine the prompt
    user_prompt = None
    
    if args.ticker:
        user_prompt = f"Create DCF for {args.ticker}"
    elif args.prompt:
        user_prompt = args.prompt
    elif args.prompt_positional:
        user_prompt = args.prompt_positional
    else:
        # No prompt provided, run interactive mode
        interactive_mode()
        return
    
    # Run analysis
    try:
        print_banner()
        print(f"\n🎯 Request: {user_prompt}\n")
        
        results = run_dcf_analysis_parallel(user_prompt, args.output)
        results['output_dir'] = args.output
        
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            print_results(results)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
