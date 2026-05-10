"""Unit tests for financial calculation logic"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.calculation_tools import (
    calculate_cagr,
    calculate_wacc,
    calculate_terminal_value,
    calculate_dcf,
    calculate_roic,
    calculate_roe,
    calculate_cost_of_equity,
)
from tools.validation_tools import (
    validate_accounting_identity,
    validate_fcf_calculation,
)


class TestCAGR:
    """Test Compound Annual Growth Rate calculations"""
    
    def test_basic_cagr(self):
        """Test basic CAGR calculation"""
        # $100 growing to $200 over 5 years = ~14.87% CAGR
        result = calculate_cagr(100, 200, 5)
        assert abs(result - 0.1487) < 0.001
    
    def test_zero_beginning(self):
        """Test CAGR with zero beginning value"""
        result = calculate_cagr(0, 100, 5)
        assert result == 0.0
    
    def test_zero_ending(self):
        """Test CAGR with zero ending value"""
        result = calculate_cagr(100, 0, 5)
        assert result == 0.0
    
    def test_negative_years(self):
        """Test CAGR with negative years"""
        result = calculate_cagr(100, 200, -1)
        assert result == 0.0


class TestWACC:
    """Test WACC calculations"""
    
    def test_basic_wacc(self):
        """Test basic WACC calculation"""
        # Cost of equity 10%, cost of debt 5%, 70% equity, 30% debt, 25% tax
        result = calculate_wacc(0.10, 0.05, 0.7, 0.3, 0.25)
        expected = 0.7 * 0.10 + 0.3 * 0.05 * (1 - 0.25)
        assert abs(result - expected) < 0.001
    
    def test_wacc_bounds(self):
        """Test WACC is clamped between 5% and 20%"""
        # Very high WACC should be clamped
        result = calculate_wacc(0.50, 0.30, 0.5, 0.5, 0.25)
        assert result <= 0.20
        
        # Very low WACC should be clamped
        result = calculate_wacc(0.01, 0.01, 0.5, 0.5, 0.25)
        assert result >= 0.05
    
    def test_invalid_weights(self):
        """Test WACC with invalid weights"""
        with pytest.raises(ValueError):
            calculate_wacc(0.10, 0.05, 0.8, 0.3, 0.25)  # Sum > 1


class TestTerminalValue:
    """Test Terminal Value calculations"""
    
    def test_basic_terminal_value(self):
        """Test Gordon Growth Model"""
        # FCF = 100, WACC = 10%, g = 3%
        # TV = 100 * 1.03 / (0.10 - 0.03) = 1471.43
        result = calculate_terminal_value(100, 0.10, 0.03)
        expected = 100 * 1.03 / (0.10 - 0.03)
        assert abs(result - expected) < 0.1
    
    def test_wacc_less_than_growth(self):
        """Test that WACC must exceed growth"""
        with pytest.raises(ValueError):
            calculate_terminal_value(100, 0.03, 0.05)  # WACC < g
    
    def test_zero_fcf(self):
        """Test with zero FCF"""
        result = calculate_terminal_value(0, 0.10, 0.03)
        assert result == 0.0


class TestDCF:
    """Test DCF calculations"""
    
    def test_basic_dcf(self):
        """Test basic DCF calculation"""
        cash_flows = [100, 110, 120]  # 3 years
        wacc = 0.10
        terminal_value = 1000
        
        result = calculate_dcf(cash_flows, wacc, terminal_value, 3)
        
        # PV of year 1: 100 / 1.1 = 90.91
        # PV of year 2: 110 / 1.1^2 = 90.91
        # PV of year 3: 120 / 1.1^3 = 90.16
        # PV of TV: 1000 / 1.1^3 = 751.31
        
        assert abs(result["sum_pv_fcf"] - 271.98) < 1.0
        assert abs(result["pv_terminal"] - 751.31) < 1.0
        assert abs(result["enterprise_value"] - 1023.29) < 1.0
    
    def test_zero_wacc(self):
        """Test that zero WACC raises error"""
        with pytest.raises(ValueError):
            calculate_dcf([100], 0, 1000, 1)


class TestROIC:
    """Test ROIC calculations"""
    
    def test_basic_roic(self):
        """Test basic ROIC"""
        nopat = 100
        invested_capital = 500
        result = calculate_roic(nopat, invested_capital)
        assert result == 0.20  # 20%
    
    def test_zero_capital(self):
        """Test with zero invested capital"""
        result = calculate_roic(100, 0)
        assert result == 0.0


class TestROE:
    """Test ROE calculations"""
    
    def test_basic_roe(self):
        """Test basic ROE"""
        net_income = 100
        equity = 500
        result = calculate_roe(net_income, equity)
        assert result == 0.20  # 20%
    
    def test_zero_equity(self):
        """Test with zero equity"""
        result = calculate_roe(100, 0)
        assert result == 0.0


class TestCostOfEquity:
    """Test CAPM calculations"""
    
    def test_basic_capm(self):
        """Test basic CAPM"""
        rf = 0.04
        beta = 1.2
        premium = 0.05
        result = calculate_cost_of_equity(rf, beta, premium)
        assert abs(result - 0.10) < 0.001  # 4% + 1.2 * 5% = 10%


class TestValidation:
    """Test validation tools"""
    
    def test_accounting_identity_valid(self):
        """Test valid accounting identity"""
        is_valid, diff = validate_accounting_identity(1000, 600, 400)
        assert is_valid is True
        assert abs(diff) < 0.01
    
    def test_accounting_identity_invalid(self):
        """Test invalid accounting identity"""
        is_valid, diff = validate_accounting_identity(1000, 600, 300)  # Should be 400
        assert is_valid is False
        assert diff > 0.01
    
    def test_fcf_calculation_valid(self):
        """Test valid FCF calculation"""
        is_valid, calc_fcf = validate_fcf_calculation(100, 30, 70)
        assert is_valid is True
        assert calc_fcf == 70
    
    def test_fcf_calculation_invalid(self):
        """Test invalid FCF calculation"""
        is_valid, calc_fcf = validate_fcf_calculation(100, 30, 80)  # Should be 70
        assert is_valid is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
