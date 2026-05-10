from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class IncomeStatement:
    """Income statement data for a single period"""
    revenue: float = 0.0
    cogs: float = 0.0
    gross_profit: float = 0.0
    operating_expenses: float = 0.0
    operating_income: float = 0.0  # EBIT
    depreciation_amortization: float = 0.0
    ebitda: float = 0.0
    interest_expense: float = 0.0
    tax_expense: float = 0.0
    net_income: float = 0.0
    
    # Calculated fields
    gross_margin: float = 0.0
    operating_margin: float = 0.0
    net_margin: float = 0.0
    tax_rate: float = 0.0
    
    def __post_init__(self):
        if self.revenue > 0:
            self.gross_margin = self.gross_profit / self.revenue
            self.operating_margin = self.operating_income / self.revenue
            self.net_margin = self.net_income / self.revenue
        if self.operating_income > 0 and self.tax_expense > 0:
            self.tax_rate = self.tax_expense / (self.operating_income - self.interest_expense)


@dataclass
class BalanceSheet:
    """Balance sheet data for a single period"""
    # Assets
    cash: float = 0.0
    accounts_receivable: float = 0.0
    inventory: float = 0.0
    other_current_assets: float = 0.0
    total_current_assets: float = 0.0
    
    ppe: float = 0.0  # Property, Plant, Equipment
    goodwill: float = 0.0
    intangibles: float = 0.0
    other_long_term_assets: float = 0.0
    total_assets: float = 0.0
    
    # Liabilities
    accounts_payable: float = 0.0
    short_term_debt: float = 0.0
    other_current_liabilities: float = 0.0
    total_current_liabilities: float = 0.0
    
    long_term_debt: float = 0.0
    other_long_term_liabilities: float = 0.0
    total_liabilities: float = 0.0
    
    # Equity
    common_stock: float = 0.0
    retained_earnings: float = 0.0
    total_equity: float = 0.0
    
    # Calculated fields
    working_capital: float = 0.0
    net_debt: float = 0.0
    invested_capital: float = 0.0
    
    def __post_init__(self):
        self.working_capital = self.total_current_assets - self.total_current_liabilities
        self.net_debt = self.short_term_debt + self.long_term_debt - self.cash
        self.invested_capital = self.total_equity + self.net_debt


@dataclass
class CashFlowStatement:
    """Cash flow statement data for a single period"""
    net_income: float = 0.0
    depreciation_amortization: float = 0.0
    stock_based_compensation: float = 0.0
    working_capital_change: float = 0.0
    operating_cash_flow: float = 0.0
    
    capex: float = 0.0
    acquisitions: float = 0.0
    investing_cash_flow: float = 0.0
    
    debt_issued: float = 0.0
    stock_issued: float = 0.0
    dividends_paid: float = 0.0
    financing_cash_flow: float = 0.0
    
    # Calculated fields
    free_cash_flow: float = 0.0
    fcf_margin: float = 0.0
    
    def __post_init__(self):
        self.free_cash_flow = self.operating_cash_flow - self.capex


@dataclass
class FinancialData:
    """Complete financial data for a company"""
    ticker: str
    company_name: str = ""
    
    # Historical data (15 years)
    income_statements: Dict[str, IncomeStatement] = field(default_factory=dict)
    balance_sheets: Dict[str, BalanceSheet] = field(default_factory=dict)
    cash_flows: Dict[str, CashFlowStatement] = field(default_factory=dict)
    
    # Current/TTM
    current_income: Optional[IncomeStatement] = None
    current_balance: Optional[BalanceSheet] = None
    current_cashflow: Optional[CashFlowStatement] = None
    
    # Market data
    current_price: float = 0.0
    shares_outstanding: float = 0.0
    beta: float = 1.0
    market_cap: float = 0.0
    
    # Validation status
    validation_errors: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    
    def get_latest_income(self) -> Optional[IncomeStatement]:
        """Get most recent income statement"""
        if self.current_income:
            return self.current_income
        if self.income_statements:
            return list(self.income_statements.values())[0]
        return None
    
    def get_latest_balance(self) -> Optional[BalanceSheet]:
        """Get most recent balance sheet"""
        if self.current_balance:
            return self.current_balance
        if self.balance_sheets:
            return list(self.balance_sheets.values())[0]
        return None
    
    def get_latest_cashflow(self) -> Optional[CashFlowStatement]:
        """Get most recent cash flow statement"""
        if self.current_cashflow:
            return self.current_cashflow
        if self.cash_flows:
            return list(self.cash_flows.values())[0]
        return None
