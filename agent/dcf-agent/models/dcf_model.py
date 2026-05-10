from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class DCFProjection:
    """Single year DCF projection"""
    year: int
    revenue: float
    revenue_growth: float
    ebit: float
    ebit_margin: float
    tax_expense: float
    nopat: float  # Net Operating Profit After Tax
    depreciation: float
    capex: float
    working_capital_change: float
    fcf: float
    
    # Discounting
    discount_factor: float = 0.0
    pv_fcf: float = 0.0


@dataclass
class SensitivityResult:
    """Sensitivity analysis result for a single scenario"""
    wacc: float
    terminal_growth: float
    enterprise_value: float
    equity_value: float
    value_per_share: float


@dataclass
class DCFResult:
    """Complete DCF valuation results"""
    ticker: str
    
    # Projections (10 years)
    projections: List[DCFProjection] = field(default_factory=list)
    
    # Terminal value
    terminal_year_fcf: float = 0.0
    terminal_growth_rate: float = 0.025
    terminal_value: float = 0.0
    pv_terminal_value: float = 0.0
    
    # Enterprise value components
    sum_pv_fcf: float = 0.0
    enterprise_value: float = 0.0
    
    # Equity value
    cash: float = 0.0
    total_debt: float = 0.0
    equity_value: float = 0.0
    
    # Per share
    shares_outstanding: float = 0.0
    intrinsic_value_per_share: float = 0.0
    current_price: float = 0.0
    margin_of_safety: float = 0.0
    
    # Valuation verdict
    verdict: str = ""  # UNDERVALUED, OVERVALUED, FAIRLY_VALUED
    
    # WACC components (for audit)
    risk_free_rate: float = 0.04
    beta: float = 1.0
    market_premium: float = 0.05
    cost_of_equity: float = 0.09
    cost_of_debt: float = 0.05
    tax_rate: float = 0.25
    debt_weight: float = 0.3
    equity_weight: float = 0.7
    wacc: float = 0.08
    
    # Sensitivity analysis
    sensitivity_wacc_growth: List[List[SensitivityResult]] = field(default_factory=list)
    sensitivity_cagr_margin: List[List[SensitivityResult]] = field(default_factory=list)
    
    # Assumptions audit
    assumptions: Dict[str, any] = field(default_factory=dict)
    
    def calculate_verdict(self, threshold: float = 0.2) -> str:
        """Determine valuation verdict based on margin of safety"""
        if self.margin_of_safety > threshold:
            return "UNDERVALUED"
        elif self.margin_of_safety < -threshold:
            return "OVERVALUED"
        return "FAIRLY_VALUED"
    
    def get_summary(self) -> Dict:
        """Get summary for display"""
        return {
            "ticker": self.ticker,
            "intrinsic_value": round(self.intrinsic_value_per_share, 2),
            "current_price": round(self.current_price, 2),
            "margin_of_safety": round(self.margin_of_safety * 100, 1),
            "verdict": self.verdict,
            "wacc": round(self.wacc * 100, 2),
            "terminal_growth": round(self.terminal_growth_rate * 100, 2),
            "enterprise_value": round(self.enterprise_value / 1e9, 2),  # In billions
            "equity_value": round(self.equity_value / 1e9, 2),
        }
