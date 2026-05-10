"""Financial data fetching tools using yfinance"""
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from models import FinancialData, IncomeStatement, BalanceSheet, CashFlowStatement


def fetch_income_statement(ticker: str, years: int = 15) -> Dict[str, IncomeStatement]:
    """
    Fetch annual income statement data from Yahoo Finance.
    Returns dict with year keys and IncomeStatement values.
    """
    try:
        stock = yf.Ticker(ticker)
        income_stmt = stock.income_stmt
        
        if income_stmt is None or income_stmt.empty:
            return {}
        
        statements = {}
        # Get columns (dates) - most recent first
        columns = list(income_stmt.columns)[:years]
        
        for col in columns:
            year = str(col.year) if hasattr(col, 'year') else str(col)[:4]
            
            stmt = IncomeStatement(
                revenue=_get_value(income_stmt, 'Total Revenue', col),
                cogs=_get_value(income_stmt, 'Cost Of Revenue', col),
                gross_profit=_get_value(income_stmt, 'Gross Profit', col),
                operating_expenses=_get_value(income_stmt, 'Operating Expense', col),
                operating_income=_get_value(income_stmt, 'Operating Income', col),
                depreciation_amortization=_get_value(income_stmt, 'Depreciation Amortization Depletion', col),
                ebitda=_get_value(income_stmt, 'EBITDA', col),
                interest_expense=_get_value(income_stmt, 'Interest Expense', col),
                tax_expense=_get_value(income_stmt, 'Tax Provision', col),
                net_income=_get_value(income_stmt, 'Net Income', col),
            )
            statements[year] = stmt
        
        return statements
    except Exception as e:
        print(f"Error fetching income statement for {ticker}: {e}")
        return {}


def fetch_balance_sheet(ticker: str, years: int = 15) -> Dict[str, BalanceSheet]:
    """Fetch annual balance sheet data from Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        balance_sheet = stock.balance_sheet
        
        if balance_sheet is None or balance_sheet.empty:
            return {}
        
        sheets = {}
        columns = list(balance_sheet.columns)[:years]
        
        for col in columns:
            year = str(col.year) if hasattr(col, 'year') else str(col)[:4]
            
            sheet = BalanceSheet(
                cash=_get_value(balance_sheet, 'Cash And Cash Equivalents', col),
                accounts_receivable=_get_value(balance_sheet, 'Accounts Receivable', col),
                inventory=_get_value(balance_sheet, 'Inventory', col),
                other_current_assets=_get_value(balance_sheet, 'Other Current Assets', col),
                total_current_assets=_get_value(balance_sheet, 'Current Assets', col),
                ppe=_get_value(balance_sheet, 'Net PPE', col),
                goodwill=_get_value(balance_sheet, 'Goodwill', col),
                intangibles=_get_value(balance_sheet, 'Other Intangible Assets', col),
                other_long_term_assets=_get_value(balance_sheet, 'Other Non Current Assets', col),
                total_assets=_get_value(balance_sheet, 'Total Assets', col),
                accounts_payable=_get_value(balance_sheet, 'Accounts Payable', col),
                short_term_debt=_get_value(balance_sheet, 'Current Debt', col),
                other_current_liabilities=_get_value(balance_sheet, 'Other Current Liabilities', col),
                total_current_liabilities=_get_value(balance_sheet, 'Current Liabilities', col),
                long_term_debt=_get_value(balance_sheet, 'Long Term Debt', col),
                other_long_term_liabilities=_get_value(balance_sheet, 'Other Non Current Liabilities', col),
                total_liabilities=_get_value(balance_sheet, 'Total Liabilities Net Minority Interest', col),
                common_stock=_get_value(balance_sheet, 'Common Stock', col),
                retained_earnings=_get_value(balance_sheet, 'Retained Earnings', col),
                total_equity=_get_value(balance_sheet, 'Stockholders Equity', col),
            )
            sheets[year] = sheet
        
        return sheets
    except Exception as e:
        print(f"Error fetching balance sheet for {ticker}: {e}")
        return {}


def fetch_cash_flow(ticker: str, years: int = 15) -> Dict[str, CashFlowStatement]:
    """Fetch annual cash flow statement data from Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        cashflow = stock.cashflow
        
        if cashflow is None or cashflow.empty:
            return {}
        
        flows = {}
        columns = list(cashflow.columns)[:years]
        
        for col in columns:
            year = str(col.year) if hasattr(col, 'year') else str(col)[:4]
            
            cf = CashFlowStatement(
                net_income=_get_value(cashflow, 'Net Income', col),
                depreciation_amortization=_get_value(cashflow, 'Depreciation Amortization Depletion', col),
                stock_based_compensation=_get_value(cashflow, 'Stock Based Compensation', col),
                working_capital_change=_get_value(cashflow, 'Change In Working Capital', col),
                operating_cash_flow=_get_value(cashflow, 'Operating Cash Flow', col),
                capex=_get_value(cashflow, 'Capital Expenditure', col),
                acquisitions=_get_value(cashflow, 'Acquisitions', col),
                investing_cash_flow=_get_value(cashflow, 'Investing Cash Flow', col),
                debt_issued=_get_value(cashflow, 'Issuance Of Debt', col),
                stock_issued=_get_value(cashflow, 'Issuance Of Capital Stock', col),
                dividends_paid=_get_value(cashflow, 'Cash Dividends Paid', col),
                financing_cash_flow=_get_value(cashflow, 'Financing Cash Flow', col),
            )
            flows[year] = cf
        
        return flows
    except Exception as e:
        print(f"Error fetching cash flow for {ticker}: {e}")
        return {}


def get_company_info(ticker: str) -> Dict[str, Any]:
    """Get company info, shares outstanding, current price, beta"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            "company_name": info.get("longName", ticker),
            "shares_outstanding": info.get("sharesOutstanding", 0),
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
            "beta": info.get("beta", 1.0),
            "market_cap": info.get("marketCap", 0),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "currency": info.get("currency", "USD"),
        }
    except Exception as e:
        print(f"Error fetching company info for {ticker}: {e}")
        return {
            "company_name": ticker,
            "shares_outstanding": 0,
            "current_price": 0,
            "beta": 1.0,
            "market_cap": 0,
        }


def get_historical_prices(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Get historical price data for volatility/cost of equity calculations"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        return hist
    except Exception as e:
        print(f"Error fetching historical prices for {ticker}: {e}")
        return pd.DataFrame()


def fetch_all_financial_data(ticker: str, years: int = 15) -> FinancialData:
    """
    Fetch all financial data for a company.
    This is the main entry point for data collection.
    """
    print(f"Fetching financial data for {ticker}...")
    
    # Fetch in parallel would be ideal, but do sequentially for now
    income_statements = fetch_income_statement(ticker, years)
    balance_sheets = fetch_balance_sheet(ticker, years)
    cash_flows = fetch_cash_flow(ticker, years)
    company_info = get_company_info(ticker)
    
    # Create FinancialData object
    financial_data = FinancialData(
        ticker=ticker,
        company_name=company_info.get("company_name", ticker),
        income_statements=income_statements,
        balance_sheets=balance_sheets,
        cash_flows=cash_flows,
        current_price=company_info.get("current_price", 0),
        shares_outstanding=company_info.get("shares_outstanding", 0),
        beta=company_info.get("beta", 1.0),
        market_cap=company_info.get("market_cap", 0),
        data_sources=["yfinance"],
    )
    
    print(f"Data fetch complete: {len(income_statements)} income, "
          f"{len(balance_sheets)} balance, {len(cash_flows)} cash flow statements")
    
    return financial_data


def _get_value(df: pd.DataFrame, row_name: str, col) -> float:
    """Safely get a value from a dataframe"""
    try:
        if row_name in df.index:
            val = df.loc[row_name, col]
            if pd.isna(val):
                return 0.0
            return float(val)
        return 0.0
    except:
        return 0.0
