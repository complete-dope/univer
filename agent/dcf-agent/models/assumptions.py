from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Assumptions:
    """DCF modeling assumptions with conservative bias"""
    
    # Revenue growth assumptions
    revenue_cagr_historical: float = 0.0  # Calculated from data
    revenue_growth_y1_3: float = 0.08
    revenue_growth_y4_7: float = 0.06
    revenue_growth_y8_10: float = 0.04
    terminal_growth_rate: float = 0.025
    
    # Margin assumptions
    ebit_margin_target: float = 0.20
    ebit_margin_max: float = 0.35  # Cap at 35% unless exceptional
    tax_rate: float = 0.25
    
    # Reinvestment assumptions
    dna_pct_of_revenue: float = 0.05
    capex_pct_of_revenue: float = 0.08
    nwc_pct_of_revenue: float = 0.15
    sales_to_capital_ratio: float = 2.0
    
    # WACC assumptions
    risk_free_rate: float = 0.04  # 10-year Treasury
    beta: float = 1.0
    market_risk_premium: float = 0.05  # 5% historical premium
    cost_of_debt: float = 0.05
    target_debt_ratio: float = 0.3
    
    # Conservative adjustments
    margin_mean_reversion_speed: float = 0.3  # 30% per year
    growth_decay_factor: float = 0.8  # Reduce historical by 20%
    max_growth_mature_company: float = 0.15  # Cap mature companies
    min_growth_all_companies: float = 0.02  # Floor at 2%
    
    # Validation thresholds
    max_terminal_value_pct: float = 0.75  # Terminal value max 75% of EV
    min_wacc: float = 0.06
    max_wacc: float = 0.15
    
    # Audit trail
    rationale: Dict[str, str] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    def apply_conservative_adjustments(self, historical_cagr: float, 
                                       historical_ebit_margin: float,
                                       company_maturity: str = "mature"):
        """Apply conservative adjustments based on historical data"""
        
        # Revenue growth: reduce historical by decay factor
        adjusted_cagr = historical_cagr * self.growth_decay_factor
        
        # Cap based on maturity
        if company_maturity == "mature":
            adjusted_cagr = min(adjusted_cagr, self.max_growth_mature_company)
        
        # Floor at minimum
        adjusted_cagr = max(adjusted_cagr, self.min_growth_all_companies)
        
        self.revenue_cagr_historical = historical_cagr
        self.revenue_growth_y1_3 = adjusted_cagr
        self.revenue_growth_y4_7 = adjusted_cagr * 0.75  # Decay
        self.revenue_growth_y8_10 = max(adjusted_cagr * 0.5, self.terminal_growth_rate)
        
        # EBIT margin: mean revert toward historical average
        # Never exceed historical peak + 5%
        peak_margin = historical_ebit_margin * 1.05
        self.ebit_margin_target = min(
            historical_ebit_margin * (1 - self.margin_mean_reversion_speed * 0.5),
            peak_margin,
            self.ebit_margin_max
        )
        
        # Store rationale
        self.rationale['revenue_growth'] = (
            f"Historical CAGR: {historical_cagr:.1%}, "
            f"Adjusted: {adjusted_cagr:.1%} (applied {self.growth_decay_factor:.0%} decay)"
        )
        self.rationale['ebit_margin'] = (
            f"Historical: {historical_ebit_margin:.1%}, "
            f"Target: {self.ebit_margin_target:.1%} (mean reversion applied)"
        )
    
    def calculate_wacc(self, current_debt_ratio: float = None) -> float:
        """Calculate WACC from assumptions"""
        cost_of_equity = self.risk_free_rate + self.beta * self.market_risk_premium
        
        debt_ratio = current_debt_ratio if current_debt_ratio else self.target_debt_ratio
        equity_ratio = 1 - debt_ratio
        
        wacc = (equity_ratio * cost_of_equity + 
                debt_ratio * self.cost_of_debt * (1 - self.tax_rate))
        
        # Clamp to reasonable bounds
        return max(self.min_wacc, min(wacc, self.max_wacc))
    
    def validate(self) -> List[str]:
        """Validate assumptions are reasonable"""
        errors = []
        
        if self.terminal_growth_rate >= self.risk_free_rate:
            errors.append(f"Terminal growth ({self.terminal_growth_rate:.1%}) should be below risk-free rate")
        
        if self.wacc() <= self.terminal_growth_rate:
            errors.append(f"WACC ({self.wacc():.1%}) must exceed terminal growth ({self.terminal_growth_rate:.1%})")
        
        if self.ebit_margin_target > 0.5:
            errors.append(f"EBIT margin target ({self.ebit_margin_target:.1%}) seems unusually high")
        
        if self.revenue_growth_y1_3 > 0.50:
            errors.append(f"Revenue growth ({self.revenue_growth_y1_3:.1%}) may be too aggressive")
        
        return errors
    
    def wacc(self) -> float:
        """Shorthand for calculate_wacc"""
        return self.calculate_wacc()
