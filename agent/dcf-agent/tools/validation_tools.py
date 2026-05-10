"""Data validation tools for financial data consistency"""
from typing import List, Dict, Tuple, Optional
from models import FinancialData, IncomeStatement, BalanceSheet, CashFlowStatement


def validate_accounting_identity(
    assets: float,
    liabilities: float,
    equity: float,
    tolerance: float = 0.01
) -> Tuple[bool, float]:
    """
    Verify Assets = Liabilities + Equity.
    Returns (is_valid, difference).
    """
    expected_assets = liabilities + equity
    diff = abs(assets - expected_assets)
    diff_pct = diff / assets if assets > 0 else 0
    
    is_valid = diff_pct <= tolerance
    return is_valid, diff_pct


def validate_fcf_calculation(
    ocf: float,
    capex: float,
    expected_fcf: float,
    tolerance: float = 0.01
) -> Tuple[bool, float]:
    """
    Verify FCF = OCF - CapEx.
    Returns (is_valid, calculated_fcf).
    """
    calculated_fcf = ocf - capex
    diff = abs(calculated_fcf - expected_fcf)
    diff_pct = diff / abs(expected_fcf) if expected_fcf != 0 else 0
    
    is_valid = diff_pct <= tolerance
    return is_valid, calculated_fcf


def validate_data_completeness(financial_data: FinancialData) -> List[str]:
    """
    Check if all required data is present.
    Returns list of missing data warnings.
    """
    errors = []
    
    # Check income statements
    if not financial_data.income_statements:
        errors.append("Missing income statements")
    else:
        years = len(financial_data.income_statements)
        if years < 5:
            errors.append(f"Only {years} years of income data (recommend 10+)")
    
    # Check balance sheets
    if not financial_data.balance_sheets:
        errors.append("Missing balance sheets")
    
    # Check cash flows
    if not financial_data.cash_flows:
        errors.append("Missing cash flow statements")
    
    # Check market data
    if financial_data.current_price <= 0:
        errors.append("Missing current stock price")
    
    if financial_data.shares_outstanding <= 0:
        errors.append("Missing shares outstanding")
    
    if financial_data.beta <= 0:
        errors.append(f"Invalid beta ({financial_data.beta}), using default 1.0")
        financial_data.beta = 1.0
    
    return errors


def validate_financial_consistency(financial_data: FinancialData) -> List[str]:
    """
    Validate consistency across financial statements.
    Checks:
    - Net income matches between income and cash flow
    - Balance sheet balances
    - FCF calculations
    """
    errors = []
    
    for year in financial_data.income_statements.keys():
        income = financial_data.income_statements.get(year)
        balance = financial_data.balance_sheets.get(year)
        cashflow = financial_data.cash_flows.get(year)
        
        if not (income and balance and cashflow):
            continue
        
        # Check balance sheet balances
        valid, diff = validate_accounting_identity(
            balance.total_assets,
            balance.total_liabilities,
            balance.total_equity
        )
        if not valid:
            errors.append(f"{year}: Balance sheet off by {diff:.1%}")
        
        # Check net income consistency
        if abs(income.net_income - cashflow.net_income) > income.net_income * 0.05:
            errors.append(f"{year}: Net income mismatch between statements")
        
        # Check FCF calculation
        valid, calc_fcf = validate_fcf_calculation(
            cashflow.operating_cash_flow,
            cashflow.capex,
            cashflow.free_cash_flow
        )
        if not valid:
            errors.append(f"{year}: FCF calculation inconsistent")
    
    return errors


def cross_validate_metrics(
    financial_data: FinancialData,
    metrics: List[str] = ["revenue", "net_income", "total_assets"]
) -> Dict[str, Dict]:
    """
    Cross-validate key metrics across sources (if multiple available).
    Currently only uses Yahoo Finance, but structure supports multiple sources.
    """
    results = {}
    
    for metric in metrics:
        values = []
        sources = []
        
        # Get values from Yahoo Finance
        if financial_data.income_statements:
            latest_year = list(financial_data.income_statements.keys())[0]
            income = financial_data.income_statements[latest_year]
            
            if metric == "revenue":
                values.append(income.revenue)
                sources.append("yfinance_income")
            elif metric == "net_income":
                values.append(income.net_income)
                sources.append("yfinance_income")
        
        if values:
            median = sorted(values)[len(values) // 2]
            variance = max(values) - min(values) if len(values) > 1 else 0
            variance_pct = variance / median if median > 0 else 0
            
            results[metric] = {
                "values": values,
                "sources": sources,
                "median": median,
                "variance": variance,
                "variance_pct": variance_pct,
                "consistent": variance_pct < 0.05  # 5% variance threshold
            }
    
    return results


def flag_anomalies(financial_data: FinancialData) -> List[str]:
    """
    Flag unusual values that may indicate data issues.
    """
    warnings = []
    
    if not financial_data.income_statements:
        return warnings
    
    # Get recent years
    years = sorted(financial_data.income_statements.keys(), reverse=True)[:5]
    
    for year in years:
        income = financial_data.income_statements.get(year)
        if not income:
            continue
        
        # Flag negative revenue
        if income.revenue < 0:
            warnings.append(f"{year}: Negative revenue detected")
        
        # Flag margins > 100%
        if income.gross_margin > 1.0:
            warnings.append(f"{year}: Gross margin > 100%")
        if income.operating_margin > 1.0:
            warnings.append(f"{year}: Operating margin > 100%")
        
        # Flag declining revenue > 50%
        prev_year = str(int(year) - 1)
        if prev_year in financial_data.income_statements:
            prev_income = financial_data.income_statements[prev_year]
            if prev_income.revenue > 0:
                decline = (prev_income.revenue - income.revenue) / prev_income.revenue
                if decline > 0.5:
                    warnings.append(f"{year}: Revenue declined >50% from prior year")
    
    return warnings


def run_all_validations(financial_data: FinancialData) -> Dict[str, List[str]]:
    """
    Run all validation checks and return categorized results.
    """
    return {
        "completeness": validate_data_completeness(financial_data),
        "consistency": validate_financial_consistency(financial_data),
        "anomalies": flag_anomalies(financial_data),
    }
