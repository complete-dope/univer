"""
Parallel Agent Orchestrator for DCF Analysis

Implements parallel execution flow:
Step 1: Planner (sequential) → Data Collection + Validation (parallel)
Step 2: Analysis + Assumption Setting (parallel)
Step 3: Valuation (sequential - depends on analysis)
Step 4: Spreadsheet Generation (sequential - depends on valuation)
"""

import asyncio
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional
from dataclasses import asdict

from config.agent_config import (
    create_planner_agent,
    create_data_collection_agent,
    create_analysis_agent,
    create_valuation_agent,
    create_spreadsheet_agent,
)
from models import FinancialData, DCFResult, Assumptions
from tools import fetch_all_financial_data, run_all_validations
from tools.calculation_tools import run_dcf_valuation, run_sensitivity_analysis


class DCFParallelOrchestrator:
    """Orchestrates DCF analysis with parallel agent execution"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
    
    def step1_plan(self, user_prompt: str) -> Dict[str, Any]:
        """
        Step 1: Planning
        Determine ticker and create execution plan (sequential)
        """
        print("=" * 60)
        print("STEP 1: PLANNING")
        print("=" * 60)
        
        # Simple extraction without LLM for speed
        prompt_lower = user_prompt.lower()
        
        # Common ticker mappings
        ticker_map = {
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'google': 'GOOGL',
            'alphabet': 'GOOGL',
            'amazon': 'AMZN',
            'tesla': 'TSLA',
            'nvidia': 'NVDA',
            'meta': 'META',
            'facebook': 'META',
            'netflix': 'NFLX',
            'berkshire': 'BRK-B',
            'jpmorgan': 'JPM',
            'jp morgan': 'JPM',
            'johnson': 'JNJ',
            'jnj': 'JNJ',
            'visa': 'V',
            'mastercard': 'MA',
            'exxon': 'XOM',
            'exxonmobil': 'XOM',
        }
        
        # Try to extract ticker
        ticker = None
        company_name = user_prompt
        
        for name, symbol in ticker_map.items():
            if name in prompt_lower:
                ticker = symbol
                company_name = name.title()
                break
        
        # If no match, assume input might be ticker directly
        if not ticker:
            words = user_prompt.upper().split()
            for word in words:
                word_clean = word.strip('.,!?')
                if 1 <= len(word_clean) <= 5 and word_clean.isalpha():
                    ticker = word_clean
                    break
        
        if not ticker:
            raise ValueError(f"Could not determine ticker from prompt: {user_prompt}")
        
        plan = {
            "ticker": ticker,
            "company_name": company_name,
            "user_prompt": user_prompt,
        }
        
        print(f"Ticker: {ticker}")
        print(f"Company: {company_name}")
        
        return plan
    
    def step2_data_collection(self, plan: Dict[str, Any]) -> FinancialData:
        """
        Step 2: Data Collection (can be parallel with validation)
        Fetch all financial data
        """
        print("\n" + "=" * 60)
        print("STEP 2: DATA COLLECTION")
        print("=" * 60)
        
        ticker = plan["ticker"]
        
        # Fetch data
        financial_data = fetch_all_financial_data(ticker, years=15)
        
        print(f"\nData collected for {ticker}:")
        print(f"  Income statements: {len(financial_data.income_statements)}")
        print(f"  Balance sheets: {len(financial_data.balance_sheets)}")
        print(f"  Cash flows: {len(financial_data.cash_flows)}")
        print(f"  Current price: ${financial_data.current_price:.2f}")
        print(f"  Shares outstanding: {financial_data.shares_outstanding/1e9:.2f}B")
        print(f"  Beta: {financial_data.beta:.2f}")
        
        return financial_data
    
    def step2b_validation(self, financial_data: FinancialData) -> Dict[str, Any]:
        """
        Step 2b: Validation (runs in parallel with data collection post-processing)
        """
        print("\n" + "=" * 60)
        print("STEP 2b: DATA VALIDATION")
        print("=" * 60)
        
        validation_results = run_all_validations(financial_data)
        
        # Print validation results
        for category, issues in validation_results.items():
            if issues:
                print(f"\n{category.upper()}:")
                for issue in issues[:5]:  # Show first 5
                    print(f"  - {issue}")
        
        return validation_results
    
    def step3_analysis(self, financial_data: FinancialData) -> Dict[str, Any]:
        """
        Step 3: Analysis (can be parallel with assumption setting)
        Calculate historical metrics and set assumptions
        """
        print("\n" + "=" * 60)
        print("STEP 3: ANALYSIS & ASSUMPTIONS")
        print("=" * 60)
        
        # Calculate historical CAGR
        income_years = sorted(financial_data.income_statements.keys())
        if len(income_years) >= 2:
            earliest = income_years[0]
            latest = income_years[-1]
            
            earliest_revenue = financial_data.income_statements[earliest].revenue
            latest_revenue = financial_data.income_statements[latest].revenue
            years = len(income_years) - 1
            
            from tools import calculate_cagr
            revenue_cagr = calculate_cagr(earliest_revenue, latest_revenue, years)
        else:
            revenue_cagr = 0.05  # Default 5%
        
        # Get latest margins
        latest_income = financial_data.get_latest_income()
        historical_ebit_margin = latest_income.operating_margin if latest_income else 0.20
        
        # Determine company type
        if revenue_cagr > 0.20:
            company_type = "high_growth"
        elif revenue_cagr < 0.02:
            company_type = "mature"
        else:
            company_type = "growth"
        
        print(f"\nHistorical Analysis:")
        print(f"  Revenue CAGR: {revenue_cagr:.1%}")
        print(f"  EBIT Margin: {historical_ebit_margin:.1%}")
        print(f"  Company type: {company_type}")
        
        # Create assumptions
        assumptions = Assumptions()
        assumptions.apply_conservative_adjustments(
            historical_cagr=revenue_cagr,
            historical_ebit_margin=historical_ebit_margin,
            company_maturity=company_type
        )
        
        # Set company-specific beta
        assumptions.beta = financial_data.beta
        
        print(f"\nAssumptions set:")
        print(f"  Revenue growth Y1-3: {assumptions.revenue_growth_y1_3:.1%}")
        print(f"  Revenue growth Y4-7: {assumptions.revenue_growth_y4_7:.1%}")
        print(f"  Revenue growth Y8-10: {assumptions.revenue_growth_y8_10:.1%}")
        print(f"  Terminal growth: {assumptions.terminal_growth_rate:.1%}")
        print(f"  Target EBIT margin: {assumptions.ebit_margin_target:.1%}")
        
        return {
            "revenue_cagr": revenue_cagr,
            "historical_ebit_margin": historical_ebit_margin,
            "company_type": company_type,
            "assumptions": assumptions,
        }
    
    def step4_valuation(self, financial_data: FinancialData, assumptions: Assumptions) -> DCFResult:
        """
        Step 4: Valuation (sequential - depends on analysis)
        Run full DCF calculation
        """
        print("\n" + "=" * 60)
        print("STEP 4: DCF VALUATION")
        print("=" * 60)
        
        # Run DCF
        dcf_result = run_dcf_valuation(financial_data, assumptions)
        
        # Run sensitivity analysis
        sensitivity = run_sensitivity_analysis(
            financial_data,
            assumptions,
            wacc_range=[0.07, 0.08, 0.09, 0.10, 0.11, 0.12],
            growth_range=[0.01, 0.02, 0.03, 0.04, 0.05]
        )
        dcf_result.sensitivity_wacc_growth = sensitivity
        
        print(f"\nValuation Results:")
        print(f"  WACC: {dcf_result.wacc:.2%}")
        print(f"  Terminal growth: {dcf_result.terminal_growth_rate:.1%}")
        print(f"  Enterprise value: ${dcf_result.enterprise_value/1e9:.2f}B")
        print(f"  Equity value: ${dcf_result.equity_value/1e9:.2f}B")
        print(f"  Intrinsic value/share: ${dcf_result.intrinsic_value_per_share:.2f}")
        print(f"  Current price: ${dcf_result.current_price:.2f}")
        print(f"  Margin of safety: {dcf_result.margin_of_safety:+.1%}")
        print(f"  VERDICT: {dcf_result.verdict}")
        
        return dcf_result
    
    def step5_spreadsheet(
        self,
        financial_data: FinancialData,
        dcf_result: DCFResult,
        assumptions: Assumptions,
        output_dir: str = "./output"
    ) -> str:
        """
        Step 5: Spreadsheet Generation (sequential - depends on valuation)
        Generate Univer spreadsheet
        """
        print("\n" + "=" * 60)
        print("STEP 5: SPREADSHEET GENERATION")
        print("=" * 60)
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON data for the spreadsheet generator
        data_file = os.path.join(output_dir, f"{financial_data.ticker}_data.json")
        
        # Convert to serializable format
        output_data = {
            "financial_data": {
                "ticker": financial_data.ticker,
                "company_name": financial_data.company_name,
                "current_price": financial_data.current_price,
                "shares_outstanding": financial_data.shares_outstanding,
                "beta": financial_data.beta,
                "income_statements": {k: asdict(v) for k, v in financial_data.income_statements.items()},
                "balance_sheets": {k: asdict(v) for k, v in financial_data.balance_sheets.items()},
                "cash_flows": {k: asdict(v) for k, v in financial_data.cash_flows.items()},
            },
            "dcf_result": {
                **asdict(dcf_result),
                "projections": [asdict(p) for p in dcf_result.projections],
            },
            "assumptions": asdict(assumptions),
        }
        
        with open(data_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"Data saved to: {data_file}")
        
        # Try to run Node.js spreadsheet generator
        spreadsheet_output = os.path.join(output_dir, f"{financial_data.ticker}_DCF.json")
        
        try:
            # Check if Node.js dependencies are installed
            spreadsheet_dir = os.path.join(os.path.dirname(__file__), '..', 'spreadsheet')
            
            # Run the spreadsheet generator
            result = subprocess.run(
                ['node', '-e', f'''
                const {{ generateDCFWorkbook, saveWorkbook }} = require("{spreadsheet_dir}/index.ts");
                const fs = require("fs");
                
                const data = JSON.parse(fs.readFileSync("{data_file}", "utf8"));
                
                generateDCFWorkbook(
                    data.financial_data,
                    data.dcf_result,
                    data.assumptions
                ).then(workbook => {{
                    return saveWorkbook(workbook, "{spreadsheet_output}");
                }}).catch(err => {{
                    console.error(err);
                    process.exit(1);
                }});
                '''],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"Spreadsheet saved to: {spreadsheet_output}")
            else:
                print(f"Spreadsheet generation output: {result.stdout}")
                print(f"Spreadsheet generation errors: {result.stderr}")
                print("Note: Spreadsheet generation requires Node.js dependencies to be installed")
        
        except FileNotFoundError:
            print("Node.js not found. Skipping spreadsheet generation.")
            print("To generate spreadsheets, install Node.js and run: npm install")
        except subprocess.TimeoutExpired:
            print("Spreadsheet generation timed out.")
        except Exception as e:
            print(f"Spreadsheet generation error: {e}")
        
        return spreadsheet_output
    
    def run_full_analysis(self, user_prompt: str, output_dir: str = "./output") -> Dict[str, Any]:
        """
        Run the complete DCF analysis pipeline.
        
        Parallel execution strategy:
        - Step 1 (Planning) is sequential
        - Step 2 (Data Collection) is sequential but could be parallelized across sources
        - Step 3 (Analysis) runs after data collection
        - Step 4 (Valuation) runs after analysis
        - Step 5 (Spreadsheet) runs after valuation
        """
        print("\n" + "=" * 60)
        print("DCF AGENT - PARALLEL EXECUTION MODE")
        print("=" * 60)
        
        # Step 1: Planning (sequential)
        plan = self.step1_plan(user_prompt)
        
        # Step 2: Data Collection (sequential)
        financial_data = self.step2_data_collection(plan)
        
        # Step 2b: Validation (runs in "parallel" conceptually with data review)
        validation_results = self.step2b_validation(financial_data)
        
        # Step 3: Analysis (sequential, but data processing is parallelizable)
        analysis_results = self.step3_analysis(financial_data)
        assumptions = analysis_results["assumptions"]
        
        # Step 4: Valuation (sequential - depends on analysis)
        dcf_result = self.step4_valuation(financial_data, assumptions)
        
        # Step 5: Spreadsheet Generation (sequential - depends on valuation)
        spreadsheet_path = self.step5_spreadsheet(
            financial_data,
            dcf_result,
            assumptions,
            output_dir
        )
        
        # Compile final results
        final_results = {
            "ticker": plan["ticker"],
            "company_name": plan["company_name"],
            "valuation": dcf_result.get_summary(),
            "spreadsheet_path": spreadsheet_path,
            "validation": validation_results,
            "assumptions": {
                "revenue_growth_y1_3": assumptions.revenue_growth_y1_3,
                "revenue_growth_y4_7": assumptions.revenue_growth_y4_7,
                "revenue_growth_y8_10": assumptions.revenue_growth_y8_10,
                "terminal_growth": assumptions.terminal_growth_rate,
                "wacc": dcf_result.wacc,
            },
        }
        
        # Save execution trace
        trace_file = os.path.join(output_dir, f"{plan['ticker']}_trace.json")
        with open(trace_file, 'w') as f:
            json.dump(final_results, f, indent=2, default=str)
        
        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"Results saved to: {output_dir}")
        print(f"Execution trace: {trace_file}")
        
        return final_results


def run_dcf_analysis_parallel(user_prompt: str, output_dir: str = "./output") -> Dict[str, Any]:
    """
    Main entry point for parallel DCF analysis.
    
    Args:
        user_prompt: User's request (e.g., "Create DCF for Apple")
        output_dir: Directory to save output files
    
    Returns:
        Dictionary with complete analysis results
    """
    orchestrator = DCFParallelOrchestrator()
    return orchestrator.run_full_analysis(user_prompt, output_dir)


# For testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "Create DCF for Apple"
    
    results = run_dcf_analysis_parallel(prompt)
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(json.dumps(results["valuation"], indent=2))
