"""Financial calculation tools for DCF modeling"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from models import (
    FinancialData, IncomeStatement, BalanceSheet, CashFlowStatement,
    DCFResult, DCFProjection, Assumptions
)


def calculate_cagr(beginning_value: float, ending_value: float, years: int) -> float:
    """
    Calculate Compound Annual Growth Rate.
    CAGR = (Ending Value / Beginning Value)^(1/n) - 1
    """
    if beginning_value <= 0 or ending_value <= 0 or years <= 0:
        return 0.0
    return (ending_value / beginning_value) ** (1 / years) - 1


def calculate_wacc(
    cost_of_equity: float,
    cost_of_debt: float,
    equity_weight: float,
    debt_weight: float,
    tax_rate: float
) -> float:
    """
    Calculate Weighted Average Cost of Capital.
    WACC = (E/V × Re) + (D/V × Rd × (1 - Tc))
    """
    if not (0 <= equity_weight <= 1) or not (0 <= debt_weight <= 1):
        raise ValueError("Weights must be between 0 and 1")
    
    if abs(equity_weight + debt_weight - 1.0) > 0.01:
        raise ValueError("Equity weight + debt weight must equal 1")
    
    wacc = (equity_weight * cost_of_equity + 
            debt_weight * cost_of_debt * (1 - tax_rate))
    
    return max(0.05, min(wacc, 0.20))  # Clamp between 5% and 20%


def calculate_terminal_value(
    fcf: float,
    wacc: float,
    growth_rate: float
) -> float:
    """
    Calculate Terminal Value using Gordon Growth Model.
    TV = FCF(n+1) / (WACC - g) = FCF(n) × (1+g) / (WACC - g)
    """
    if wacc <= growth_rate:
        raise ValueError(f"WACC ({wacc:.2%}) must exceed growth rate ({growth_rate:.2%})")
    
    if fcf <= 0:
        return 0.0
    
    return fcf * (1 + growth_rate) / (wacc - growth_rate)


def calculate_dcf(
    cash_flows: List[float],
    wacc: float,
    terminal_value: float,
    years: int
) -> Dict[str, any]:
    """
    Discount all cash flows and terminal value to present.
    Returns dict with PV of each cash flow, PV of terminal value, and enterprise value.
    """
    if wacc <= 0:
        raise ValueError("WACC must be positive")
    
    pv_cash_flows = []
    for i, cf in enumerate(cash_flows):
        if i < years:
            discount_factor = (1 + wacc) ** (i + 1)
            pv = cf / discount_factor
            pv_cash_flows.append(pv)
    
    # Discount terminal value
    pv_terminal = terminal_value / ((1 + wacc) ** years)
    
    enterprise_value = sum(pv_cash_flows) + pv_terminal
    
    return {
        "pv_cash_flows": pv_cash_flows,
        "pv_terminal": pv_terminal,
        "enterprise_value": enterprise_value,
        "sum_pv_fcf": sum(pv_cash_flows),
    }


def calculate_roic(nopat: float, invested_capital: float) -> float:
    """Calculate Return on Invested Capital"""
    if invested_capital <= 0:
        return 0.0
    return nopat / invested_capital


def calculate_roe(net_income: float, shareholders_equity: float) -> float:
    """Calculate Return on Equity"""
    if shareholders_equity <= 0:
        return 0.0
    return net_income / shareholders_equity


def calculate_cost_of_equity(risk_free_rate: float, beta: float, market_premium: float) -> float:
    """Calculate cost of equity using CAPM"""
    return risk_free_rate + beta * market_premium


def project_revenue(
    base_revenue: float,
    years: int,
    growth_rates: List[float]
) -> List[float]:
    """Project revenue for forecast years"""
    projections = []
    revenue = base_revenue
    
    for i in range(years):
        growth = growth_rates[i] if i < len(growth_rates) else growth_rates[-1]
        revenue = revenue * (1 + growth)
        projections.append(revenue)
    
    return projections


def project_financials(
    financial_data: FinancialData,
    assumptions: Assumptions,
    forecast_years: int = 10
) -> List[DCFProjection]:
    """
    Project financials for DCF model.
    Returns list of DCFProjection objects for each forecast year.
    """
    # Get base year data
    latest_income = financial_data.get_latest_income()
    latest_balance = financial_data.get_latest_balance()
    latest_cashflow = financial_data.get_latest_cashflow()
    
    if not latest_income or not latest_balance or not latest_cashflow:
        raise ValueError("Missing financial data for projections")
    
    base_revenue = latest_income.revenue
    
    # Determine growth rates for each year
    growth_rates = []
    for year in range(forecast_years):
        if year < 3:
            growth_rates.append(assumptions.revenue_growth_y1_3)
        elif year < 7:
            growth_rates.append(assumptions.revenue_growth_y4_7)
        elif year < 10:
            growth_rates.append(assumptions.revenue_growth_y8_10)
        else:
            growth_rates.append(assumptions.terminal_growth_rate)
    
    # Project revenue
    revenue_projections = project_revenue(base_revenue, forecast_years, growth_rates)
    
    # Calculate target EBIT margin (with mean reversion)
    historical_ebit_margin = latest_income.operating_margin
    target_margin = assumptions.ebit_margin_target
    
    projections = []
    for i, revenue in enumerate(revenue_projections):
        year = i + 1
        
        # Gradually converge to target margin
        convergence_factor = min(1.0, (i + 1) * assumptions.margin_mean_reversion_speed)
        ebit_margin = historical_ebit_margin + (target_margin - historical_ebit_margin) * convergence_factor
        
        ebit = revenue * ebit_margin
        tax_expense = ebit * assumptions.tax_rate
        nopat = ebit - tax_expense
        
        # Calculate D&A as % of revenue
        depreciation = revenue * assumptions.dna_pct_of_revenue
        
        # Calculate CapEx
        capex = revenue * assumptions.capex_pct_of_revenue
        
        # Calculate working capital change
        # Simplified: assume NWC grows with revenue
        if i == 0:
            # Calculate base NWC from balance sheet
            base_nwc = latest_balance.working_capital
            prev_revenue = base_revenue
        else:
            base_nwc = projections[i-1].revenue * assumptions.nwc_pct_of_revenue
            prev_revenue = projections[i-1].revenue
        
        current_nwc = revenue * assumptions.nwc_pct_of_revenue
        wc_change = current_nwc - base_nwc
        
        # Calculate FCF
        fcf = nopat + depreciation - capex - wc_change
        
        projection = DCFProjection(
            year=year,
            revenue=revenue,
            revenue_growth=growth_rates[i],
            ebit=ebit,
            ebit_margin=ebit_margin,
            tax_expense=tax_expense,
            nopat=nopat,
            depreciation=depreciation,
            capex=capex,
            working_capital_change=wc_change,
            fcf=fcf,
        )
        projections.append(projection)
    
    return projections


def run_dcf_valuation(
    financial_data: FinancialData,
    assumptions: Assumptions
) -> DCFResult:
    """
    Run full DCF valuation.
    Main entry point for DCF calculation.
    """
    # Get latest balance sheet for capital structure
    latest_balance = financial_data.get_latest_balance()
    
    # Calculate WACC
    total_capital = latest_balance.total_equity + latest_balance.long_term_debt
    if total_capital > 0:
        debt_ratio = latest_balance.long_term_debt / total_capital
        equity_ratio = latest_balance.total_equity / total_capital
    else:
        debt_ratio = assumptions.target_debt_ratio
        equity_ratio = 1 - debt_ratio
    
    cost_of_equity = calculate_cost_of_equity(
        assumptions.risk_free_rate,
        financial_data.beta,
        assumptions.market_risk_premium
    )
    
    wacc = calculate_wacc(
        cost_of_equity,
        assumptions.cost_of_debt,
        equity_ratio,
        debt_ratio,
        assumptions.tax_rate
    )
    
    # Project financials
    projections = project_financials(financial_data, assumptions, forecast_years=10)
    
    # Get cash flows
    cash_flows = [p.fcf for p in projections]
    
    # Calculate terminal value
    terminal_fcf = projections[-1].fcf if projections else 0
    terminal_value = calculate_terminal_value(
        terminal_fcf,
        wacc,
        assumptions.terminal_growth_rate
    )
    
    # Discount cash flows
    dcf_result = calculate_dcf(cash_flows, wacc, terminal_value, years=10)
    
    # Add discount factors and PV to projections
    for i, proj in enumerate(projections):
        proj.discount_factor = (1 + wacc) ** (i + 1)
        proj.pv_fcf = proj.fcf / proj.discount_factor
    
    # Calculate equity value
    enterprise_value = dcf_result["enterprise_value"]
    cash = latest_balance.cash if latest_balance else 0
    total_debt = latest_balance.long_term_debt + latest_balance.short_term_debt if latest_balance else 0
    equity_value = enterprise_value + cash - total_debt
    
    # Per share value
    shares = financial_data.shares_outstanding
    if shares > 0:
        value_per_share = equity_value / shares
    else:
        value_per_share = 0
    
    # Calculate margin of safety
    current_price = financial_data.current_price
    if current_price > 0:
        margin_of_safety = (value_per_share - current_price) / current_price
    else:
        margin_of_safety = 0
    
    # Create result
    result = DCFResult(
        ticker=financial_data.ticker,
        projections=projections,
        terminal_year_fcf=terminal_fcf,
        terminal_growth_rate=assumptions.terminal_growth_rate,
        terminal_value=terminal_value,
        pv_terminal_value=dcf_result["pv_terminal"],
        sum_pv_fcf=dcf_result["sum_pv_fcf"],
        enterprise_value=enterprise_value,
        cash=cash,
        total_debt=total_debt,
        equity_value=equity_value,
        shares_outstanding=shares,
        intrinsic_value_per_share=value_per_share,
        current_price=current_price,
        margin_of_safety=margin_of_safety,
        risk_free_rate=assumptions.risk_free_rate,
        beta=financial_data.beta,
        market_premium=assumptions.market_risk_premium,
        cost_of_equity=cost_of_equity,
        cost_of_debt=assumptions.cost_of_debt,
        tax_rate=assumptions.tax_rate,
        debt_weight=debt_ratio,
        equity_weight=equity_ratio,
        wacc=wacc,
        assumptions=assumptions.__dict__,
    )
    
    # Calculate verdict
    result.verdict = result.calculate_verdict(threshold=0.20)
    
    return result


def run_sensitivity_analysis(
    financial_data: FinancialData,
    assumptions: Assumptions,
    wacc_range: List[float] = [0.07, 0.08, 0.09, 0.10, 0.11, 0.12],
    growth_range: List[float] = [0.01, 0.02, 0.03, 0.04, 0.05]
) -> List[List[Dict]]:
    """
    Run sensitivity analysis on WACC and terminal growth.
    Returns 2D matrix of value per share for each combination.
    """
    from models.dcf_model import SensitivityResult
    
    results = []
    
    for wacc in wacc_range:
        row = []
        for growth in growth_range:
            # Create modified assumptions
            temp_assumptions = Assumptions(
                terminal_growth_rate=growth,
                risk_free_rate=assumptions.risk_free_rate,
                beta=assumptions.beta,
                market_risk_premium=assumptions.market_risk_premium,
            )
            
            try:
                # Quick DCF calculation
                projections = project_financials(financial_data, temp_assumptions, 10)
                terminal_fcf = projections[-1].fcf if projections else 0
                
                tv = calculate_terminal_value(terminal_fcf, wacc, growth)
                dcf = calculate_dcf([p.fcf for p in projections], wacc, tv, 10)
                
                latest_balance = financial_data.get_latest_balance()
                ev = dcf["enterprise_value"]
                eq_value = ev + latest_balance.cash - latest_balance.long_term_debt
                per_share = eq_value / financial_data.shares_outstanding if financial_data.shares_outstanding > 0 else 0
                
                row.append(SensitivityResult(
                    wacc=wacc,
                    terminal_growth=growth,
                    enterprise_value=ev,
                    equity_value=eq_value,
                    value_per_share=per_share
                ))
            except Exception as e:
                row.append(SensitivityResult(
                    wacc=wacc,
                    terminal_growth=growth,
                    enterprise_value=0,
                    equity_value=0,
                    value_per_share=0
                ))
        
        results.append(row)
    
    return results
