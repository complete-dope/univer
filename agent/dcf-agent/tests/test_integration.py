"""Integration tests for end-to-end DCF analysis"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import FinancialData, IncomeStatement, BalanceSheet, CashFlowStatement, Assumptions
from tools.calculation_tools import run_dcf_valuation
from agents.parallel_orchestrator import DCFParallelOrchestrator


class TestDCFFlow:
    """Test complete DCF calculation flow"""
    
    @pytest.fixture
    def sample_financial_data(self):
        """Create sample financial data for testing"""
        # Create 5 years of income statements
        income_statements = {}
        for i, year in enumerate([2020, 2021, 2022, 2023, 2024]):
            revenue = 100 * (1.1 ** i)  # 10% growth
            income_statements[str(year)] = IncomeStatement(
                revenue=revenue,
                cogs=revenue * 0.6,
                gross_profit=revenue * 0.4,
                operating_expenses=revenue * 0.2,
                operating_income=revenue * 0.2,  # 20% EBIT margin
                depreciation_amortization=revenue * 0.05,
                ebitda=revenue * 0.25,
                interest_expense=revenue * 0.02,
                tax_expense=revenue * 0.2 * 0.25,  # 25% tax on EBIT
                net_income=revenue * 0.15,  # 15% net margin
            )
        
        # Create balance sheets
        balance_sheets = {}
        for i, year in enumerate([2020, 2021, 2022, 2023, 2024]):
            revenue = 100 * (1.1 ** i)
            balance_sheets[str(year)] = BalanceSheet(
                cash=20,
                accounts_receivable=revenue * 0.1,
                inventory=revenue * 0.05,
                other_current_assets=5,
                total_current_assets=50 + revenue * 0.15,
                ppe=100 + i * 10,
                goodwill=20,
                intangibles=10,
                other_long_term_assets=5,
                total_assets=185 + revenue * 0.15 + i * 10,
                accounts_payable=20,
                short_term_debt=10,
                other_current_liabilities=10,
                total_current_liabilities=40,
                long_term_debt=50,
                other_long_term_liabilities=5,
                total_liabilities=95,
                common_stock=50,
                retained_earnings=40 + i * 10,
                total_equity=90 + i * 10,
            )
        
        # Create cash flow statements
        cash_flows = {}
        for i, year in enumerate([2020, 2021, 2022, 2023, 2024]):
            revenue = 100 * (1.1 ** i)
            net_income = revenue * 0.15
            cash_flows[str(year)] = CashFlowStatement(
                net_income=net_income,
                depreciation_amortization=revenue * 0.05,
                stock_based_compensation=2,
                working_capital_change=-1,
                operating_cash_flow=net_income + revenue * 0.05 + 2 - 1,
                capex=10,
                acquisitions=0,
                investing_cash_flow=-10,
                debt_issued=0,
                stock_issued=5,
                dividends_paid=-5,
                financing_cash_flow=0,
            )
        
        return FinancialData(
            ticker="TEST",
            company_name="Test Company",
            income_statements=income_statements,
            balance_sheets=balance_sheets,
            cash_flows=cash_flows,
            current_price=50.0,
            shares_outstanding=10.0,  # 10 shares
            beta=1.0,
            market_cap=500.0,
        )
    
    def test_full_dcf_valuation(self, sample_financial_data):
        """Test complete DCF valuation flow"""
        # Create assumptions
        assumptions = Assumptions()
        assumptions.apply_conservative_adjustments(
            historical_cagr=0.10,
            historical_ebit_margin=0.20,
            company_maturity="mature"
        )
        
        # Run DCF
        result = run_dcf_valuation(sample_financial_data, assumptions)
        
        # Validate results
        assert result.ticker == "TEST"
        assert result.enterprise_value > 0
        assert result.equity_value > 0
        assert result.intrinsic_value_per_share > 0
        assert result.wacc > 0
        assert result.verdict in ["UNDERVALUED", "OVERVALUED", "FAIRLY_VALUED"]
        
        # Check projections
        assert len(result.projections) == 10
        for proj in result.projections:
            assert proj.revenue > 0
            assert proj.fcf > 0
        
        print(f"\nTest DCF Results:")
        print(f"  Intrinsic value: ${result.intrinsic_value_per_share:.2f}")
        print(f"  Current price: ${result.current_price:.2f}")
        print(f"  Verdict: {result.verdict}")
    
    def test_stable_company_scenario(self, sample_financial_data):
        """Test DCF for stable company (Apple-like)"""
        assumptions = Assumptions()
        assumptions.revenue_growth_y1_3 = 0.05
        assumptions.revenue_growth_y4_7 = 0.04
        assumptions.revenue_growth_y8_10 = 0.03
        assumptions.ebit_margin_target = 0.25
        
        result = run_dcf_valuation(sample_financial_data, assumptions)
        
        # Stable company should have reasonable valuation
        assert result.intrinsic_value_per_share > 0
        assert result.wacc < 0.15
        
        print(f"\nStable Company Test:")
        print(f"  Value/share: ${result.intrinsic_value_per_share:.2f}")
    
    def test_high_growth_scenario(self, sample_financial_data):
        """Test DCF for high growth company"""
        # Set higher beta on financial data directly
        sample_financial_data.beta = 2.0
        
        assumptions = Assumptions()
        assumptions.revenue_growth_y1_3 = 0.30
        assumptions.revenue_growth_y4_7 = 0.20
        assumptions.revenue_growth_y8_10 = 0.10
        assumptions.ebit_margin_target = 0.15
        
        result = run_dcf_valuation(sample_financial_data, assumptions)
        
        # Higher beta (2.0) should lead to higher cost of equity
        # Cost of equity = 4% + 2.0 * 5% = 14%
        assert result.cost_of_equity > 0.12
        assert result.beta == 2.0
        
        print(f"\nHigh Growth Test:")
        print(f"  Beta: {result.beta}")
        print(f"  Cost of Equity: {result.cost_of_equity:.2%}")
        print(f"  WACC: {result.wacc:.2%}")
        print(f"  Value/share: ${result.intrinsic_value_per_share:.2f}")


class TestOrchestrator:
    """Test the parallel orchestrator"""
    
    def test_orchestrator_planning(self):
        """Test the planning step"""
        orchestrator = DCFParallelOrchestrator()
        
        plan = orchestrator.step1_plan("Create DCF for Apple")
        
        assert plan["ticker"] == "AAPL"
        assert "company_name" in plan
    
    def test_orchestrator_planning_ticker(self):
        """Test planning with direct ticker"""
        orchestrator = DCFParallelOrchestrator()
        
        plan = orchestrator.step1_plan("MSFT DCF")
        
        assert plan["ticker"] == "MSFT"
    
    def test_orchestrator_planning_tesla(self):
        """Test planning for Tesla"""
        orchestrator = DCFParallelOrchestrator()
        
        plan = orchestrator.step1_plan("Create DCF for Tesla")
        
        assert plan["ticker"] == "TSLA"


@pytest.mark.slow
class TestLiveData:
    """Tests that fetch real data (marked as slow)"""
    
    def test_fetch_apple_data(self):
        """Test fetching real Apple data"""
        from tools import fetch_all_financial_data
        
        data = fetch_all_financial_data("AAPL", years=5)
        
        assert data.ticker == "AAPL"
        assert len(data.income_statements) > 0
        assert data.current_price > 0
        assert data.shares_outstanding > 0
        
        print(f"\nApple Data Test:")
        print(f"  Price: ${data.current_price:.2f}")
        print(f"  Shares: {data.shares_outstanding/1e9:.2f}B")
        print(f"  Beta: {data.beta:.2f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
