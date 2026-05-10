#!/usr/bin/env python3
"""
Generate Amazon DCF Model with:
- Historical data: Actual reported values from filings (static)
- Forecast data: Formula-based projections (dynamic)
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    import yfinance as yf
except ImportError:
    os.system(f"{sys.executable} -m pip install openpyxl pandas yfinance -q")
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    import yfinance as yf


def get_amazon_data():
    """Get Amazon financial data from Yahoo Finance"""
    stock = yf.Ticker("AMZN")
    
    return {
        'quarterly_income': stock.quarterly_income_stmt,
        'quarterly_balance': stock.quarterly_balance_sheet,
        'quarterly_cash': stock.quarterly_cashflow,
        'info': stock.info
    }


def create_amazon_model_v2():
    """Create Amazon model with actual historical data + forecast formulas"""
    
    print(f"\n{'='*60}")
    print(f"Amazon DCF Model v2 (Actuals + Forecasts)")
    print(f"{'='*60}")
    
    data = get_amazon_data()
    info = data['info']
    
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    
    main = wb.create_sheet("Main", 0)
    model = wb.create_sheet("Model")
    
    # Current metrics
    current_price = info.get('currentPrice', info.get('regularMarketPrice', 272.68))
    shares = info.get('sharesOutstanding', 10757000000) / 1e6  # in millions
    cash = info.get('totalCash', 143089000000) / 1e6
    debt = info.get('totalDebt', 235540000000) / 1e6
    
    # ==========================================
    # MAIN SHEET
    # ==========================================
    
    # Company info
    main['B4'] = "Incorporated in Washington in 1994"
    main['B5'] = "July 1995 - store opened"
    main['B6'] = "IPO 1997"
    main['B9'] = "CEO: Andy Jassy"
    
    # AWS section
    main['B10'] = "AWS"
    main['C11'] = "S3"
    main['D11'] = "Azure, GCP, Digital Ocean"
    main['C12'] = "EC2"
    main['D12'] = "Very weak in GPUs"
    main['C13'] = "Dynamo"
    main['C14'] = "SageMaker"
    main['D14'] = "HyperPods"
    main['C15'] = "Polly"
    main['C16'] = "EKS"
    main['C17'] = "Tranium"
    main['C18'] = "Inferentia"
    main['C19'] = "Bedrock"
    main['D19'] = "AI models"
    main['B20'] = "Amazon"
    main['C21'] = "Prime"
    main['C22'] = "Video"
    main['C23'] = "Music"
    main['C24'] = "Audible"
    main['B26'] = "Devices"
    main['C27'] = "Echo"
    main['C28'] = "Kindle"
    main['C29'] = "Fire"
    main['B32'] = "Advertising"
    main['C33'] = "Twitch"
    main['B35'] = "Whole Foods"
    main['B37'] = "3PS"
    main['B38'] = "Healthcare"
    
    # Financial summary
    main['J2'] = "Price"
    main['K2'] = current_price
    main['K2'].number_format = '$#,##0.00'
    
    main['J3'] = "Shares"
    main['K3'] = shares / 1e3  # in billions
    main['K3'].number_format = '#,##0'
    main['L3'] = "Q225"
    
    main['J4'] = "MC"
    main['K4'] = f"=K3*K2*1000"
    main['K4'].number_format = '$#,##0'
    
    main['J5'] = "Cash"
    main['K5'] = cash
    main['K5'].number_format = '$#,##0'
    main['L5'] = "Q225"
    
    main['J6'] = "Debt"
    main['K6'] = debt
    main['K6'].number_format = '$#,##0'
    main['L6'] = "Q225"
    
    main['J7'] = "EV"
    main['K7'] = f"=K4-K5+K6"
    main['K7'].number_format = '$#,##0'
    
    # DCF Results
    main['J10'] = "DCF VALUATION"
    main['J10'].font = Font(bold=True, size=12)
    
    main['J12'] = "WACC"
    main['K12'] = 0.09
    main['K12'].number_format = '0.0%'
    
    main['J13'] = "Terminal Growth"
    main['K13'] = 0.03
    main['K13'].number_format = '0.0%'
    
    main['J14'] = "PV of FCF (5yr)"
    main['K14'] = f"=Model!C101"
    main['K14'].number_format = '$#,##0'
    
    main['J15'] = "Terminal Value"
    main['K15'] = f"=Model!C102"
    main['K15'].number_format = '$#,##0'
    
    main['J16'] = "Enterprise Value"
    main['K16'] = f"=K14+K15"
    main['K16'].number_format = '$#,##0'
    
    main['J17'] = "+ Cash"
    main['K17'] = f"=K5"
    main['K17'].number_format = '$#,##0'
    
    main['J18'] = "- Debt"
    main['K18'] = f"=K6"
    main['K18'].number_format = '$#,##0'
    
    main['J19'] = "Equity Value"
    main['K19'] = f"=K16+K17-K18"
    main['K19'].number_format = '$#,##0'
    
    main['J20'] = "Per Share Value"
    main['K20'] = f"=K19/(K3*1000)"
    main['K20'].number_format = '$0.00'
    main['K20'].font = Font(bold=True, size=14, color="006100")
    
    main['J21'] = "Upside/Downside"
    main['K21'] = f"=K20/K2-1"
    main['K21'].number_format = '0.0%'
    
    # Format Main
    main.column_dimensions['A'].width = 3
    main.column_dimensions['B'].width = 35
    main.column_dimensions['C'].width = 20
    main.column_dimensions['D'].width = 40
    main.column_dimensions['J'].width = 18
    main.column_dimensions['K'].width = 15
    main.column_dimensions['L'].width = 8
    
    for row in [2, 3, 4, 5, 6, 7]:
        main[f'J{row}'].font = Font(bold=True)
    
    # ==========================================
    # MODEL SHEET - Headers
    # ==========================================
    
    model['A1'] = "Main"
    
    # Quarter headers Q117 through Q426 (40 quarters)
    quarters = []
    for year in range(17, 27):  # 2017-2026
        for q in range(1, 5):
            quarters.append(f"Q{q}{year:02d}")
    
    for idx, q_str in enumerate(quarters[:40], start=3):  # C to AZ
        col = get_column_letter(idx)
        model[f'{col}2'] = q_str
        model[f'{col}2'].alignment = Alignment(horizontal='center')
    
    # Forecast headers with formulas
    for idx in range(43, 51):  # AM-AU
        col = get_column_letter(idx)
        prev = get_column_letter(idx - 1)
        model[f'{col}2'] = f"=+{prev}2+1"
        model[f'{col}2'].alignment = Alignment(horizontal='center')
    
    # Yearly columns
    yearly_start = 65
    for year_idx in range(30):
        col_idx = yearly_start + year_idx
        col = get_column_letter(col_idx)
        if year_idx == 0:
            model[f'{col}2'] = 1995
        else:
            prev = get_column_letter(col_idx - 1)
            model[f'{col}2'] = f"=+{prev}2+1"
    
    # ==========================================
    # Helper function to fill row with actuals + forecasts
    # ==========================================
    
    def fill_row_data(row_num, label, yahoo_key=None, yahoo_data=None, is_expense=False, 
                      calc_formula=None, forecast_ratio=None, static_estimate=None):
        """Fill row: actuals from Yahoo, forecasts as formulas"""
        model[f'B{row_num}'] = label
        
        income = data['quarterly_income']
        
        # Get actual data from Yahoo
        if yahoo_key and income is not None and yahoo_key in income.index:
            quarters_data = list(income.columns)[:40]
            for idx, quarter in enumerate(quarters_data, start=3):
                if idx > 42:  # Don't exceed our column limit
                    break
                col = get_column_letter(idx)
                try:
                    val = income.loc[yahoo_key, quarter]
                    if pd.notna(val):
                        val_m = abs(val) / 1e6 if is_expense else val / 1e6
                        model[f'{col}{row_num}'] = val_m
                        model[f'{col}{row_num}'].number_format = '$#,##0'
                except:
                    pass
        
        # Fill remaining with formulas
        last_actual_col = 2 + min(40, len(income.columns) if income is not None else 0)
        
        for idx in range(last_actual_col, 51):
            col = get_column_letter(idx)
            
            if forecast_ratio:
                # Forecast as % of revenue row 20
                ref_col = get_column_letter(idx)
                model[f'{col}{row_num}'] = f"={ref_col}20*{forecast_ratio}"
            elif calc_formula:
                # Custom formula
                formula = calc_formula.replace('COL', col)
                model[f'{col}{row_num}'] = formula
            elif static_estimate:
                # Static value for all forecast periods
                model[f'{col}{row_num}'] = static_estimate
            else:
                # Default: grow from same quarter last year
                yoy_col = get_column_letter(idx - 4)
                model[f'{col}{row_num}'] = f"={yoy_col}{row_num}*1.05"
            
            model[f'{col}{row_num}'].number_format = '$#,##0'
    
    # ==========================================
    # MODEL SHEET - Revenue Segments
    # ==========================================
    
    # Row 3: North America
    model['B3'] = "NorthAmerica"
    model['B3'].font = Font(bold=True)
    fill_row_data(3, "NorthAmerica", forecast_ratio=0.60)
    
    # Row 4: NA Media (sub)
    model['B4'] = "  Media"
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}4'] = f"={col}3*0.3"
        model[f'{col}4'].number_format = '$#,##0'
    
    # Row 5: NA Electronics (sub)
    model['B5'] = "  Electronics/General"
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}5'] = f"={col}3*0.7"
        model[f'{col}5'].number_format = '$#,##0'
    
    # Row 6: International
    model['B6'] = "International"
    model['B6'].font = Font(bold=True)
    fill_row_data(6, "International", forecast_ratio=0.25)
    
    # Row 7: Int'l Media (sub)
    model['B7'] = "  Media"
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}7'] = f"={col}6*0.3"
        model[f'{col}7'].number_format = '$#,##0'
    
    # Row 8: Int'l Electronics (sub)
    model['B8'] = "  Electronics/General"
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}8'] = f"={col}6*0.7"
        model[f'{col}8'].number_format = '$#,##0'
    
    # Row 9: AWS
    model['B9'] = "AWS"
    model['B9'].font = Font(bold=True)
    fill_row_data(9, "AWS", forecast_ratio=0.15)
    
    # Row 11-16: Business lines
    model['B11'] = "Online Stores"
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}11'] = f"={col}5+{col}8"
        model[f'{col}11'].number_format = '$#,##0'
    
    model['B12'] = "Physical Stores"
    fill_row_data(12, "Physical Stores", forecast_ratio=0.02)
    
    model['B13'] = "Third-party"
    fill_row_data(13, "Third-party", forecast_ratio=0.25)
    
    model['B14'] = "Subscription"
    fill_row_data(14, "Subscription", forecast_ratio=0.08)
    
    model['B15'] = "Ads"
    fill_row_data(15, "Ads", forecast_ratio=0.12)
    
    model['B16'] = "Other"
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}16'] = f"={col}20-SUM({col}11:{col}15)"
        model[f'{col}16'].number_format = '$#,##0'
    
    # Row 18-19: Product/Services
    model['B18'] = "Product"
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}18'] = f"={col}3+{col}6-{col}9"
        model[f'{col}18'].number_format = '$#,##0'
    
    model['B19'] = "Services"
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}19'] = f"={col}9+{col}14+{col}15"
        model[f'{col}19'].number_format = '$#,##0'
    
    # Row 20: Total Revenue (actual from Yahoo)
    model['B20'] = "Revenue"
    model['B20'].font = Font(bold=True, size=11)
    
    income = data['quarterly_income']
    if income is not None and 'Total Revenue' in income.index:
        quarters_data = list(income.columns)[:40]
        for idx, quarter in enumerate(quarters_data, start=3):
            if idx > 42:
                break
            col = get_column_letter(idx)
            try:
                val = income.loc['Total Revenue', quarter]
                if pd.notna(val):
                    model[f'{col}20'] = val / 1e6
                    model[f'{col}20'].number_format = '$#,##0'
                    model[f'{col}20'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
            except:
                pass
    
    # Forecast revenue
    for idx in range(43, 51):
        col = get_column_letter(idx)
        yoy_col = get_column_letter(idx - 4)
        model[f'{col}20'] = f"={yoy_col}20*1.10"  # 10% growth
        model[f'{col}20'].number_format = '$#,##0'
        model[f'{col}20'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
    
    # ==========================================
    # P&L (Actuals from Yahoo where available)
    # ==========================================
    
    # Row 21: Cost of Sales
    fill_row_data(21, "Cost of Sales", 'Cost Of Revenue', is_expense=True, forecast_ratio=0.55)
    
    # Row 22: Fulfillment
    fill_row_data(22, "Fulfillment", forecast_ratio=0.15)
    
    # Row 23: Gross Margin
    model['B23'] = "Gross Margin"
    model['B23'].font = Font(bold=True)
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}23'] = f"={col}20-{col}21-{col}22"
        model[f'{col}23'].number_format = '$#,##0'
        model[f'{col}23'].fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    # Row 24: Technology
    fill_row_data(24, "Technology", 'Research Development', is_expense=True, forecast_ratio=0.16)
    
    # Row 25: S&M
    fill_row_data(25, "S&M", 'Selling General Administrative', is_expense=True, forecast_ratio=0.12)
    
    # Row 26: G&A
    model['B26'] = "G&A"
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}26'] = f"={col}25*0.3"
        model[f'{col}26'].number_format = '$#,##0'
    
    # Row 27: OpEx
    model['B27'] = "OpEx"
    model['B27'].font = Font(bold=True)
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}27'] = f"=SUM({col}24:{col}26)"
        model[f'{col}27'].number_format = '$#,##0'
    
    # Row 28: OpInc
    model['B28'] = "OpInc"
    model['B28'].font = Font(bold=True)
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}28'] = f"={col}23-{col}27"
        model[f'{col}28'].number_format = '$#,##0'
        model[f'{col}28'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
    
    # Row 29: Interest Expense
    fill_row_data(29, "Interest Expense", 'Interest Expense', is_expense=True, forecast_ratio=0.005)
    
    # Row 30: Pretax
    model['B30'] = "Pretax"
    model['B30'].font = Font(bold=True)
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}30'] = f"={col}28-{col}29"
        model[f'{col}30'].number_format = '$#,##0'
    
    # Row 31: Taxes
    fill_row_data(31, "Taxes", 'Tax Provision', is_expense=True, forecast_ratio=0.18)
    
    # Row 32: Net Income
    model['B32'] = "Net Income"
    model['B32'].font = Font(bold=True)
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}32'] = f"={col}30-{col}31"
        model[f'{col}32'].number_format = '$#,##0'
        model[f'{col}32'].fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    # Row 33: EPS
    model['B33'] = "EPS"
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}33'] = f"=IF({col}34=0,0,{col}32/{col}34)"
        model[f'{col}33'].number_format = '$0.00'
    
    # Row 34: Shares (actual from Yahoo)
    model['B34'] = "Shares"
    if income is not None and 'Basic Average Shares' in income.index:
        quarters_data = list(income.columns)[:40]
        for idx, quarter in enumerate(quarters_data, start=3):
            if idx > 42:
                break
            col = get_column_letter(idx)
            try:
                val = income.loc['Basic Average Shares', quarter]
                if pd.notna(val):
                    model[f'{col}34'] = val / 1e6
                    model[f'{col}34'].number_format = '#,##0'
            except:
                pass
    
    # Forecast shares (flat)
    for idx in range(43, 51):
        col = get_column_letter(idx)
        prev_col = get_column_letter(42)
        model[f'{col}34'] = f"={prev_col}34"
        model[f'{col}34'].number_format = '#,##0'
    
    # ==========================================
    # Growth Rates
    # ==========================================
    
    # Row 36: Revenue y/y
    model['B36'] = "Revenue y/y"
    model['B36'].font = Font(bold=True, italic=True)
    for idx in range(7, 51):
        col = get_column_letter(idx)
        yoy = get_column_letter(idx - 4)
        model[f'{col}36'] = f"=IF({yoy}20=0,0,{col}20/{yoy}20-1)"
        model[f'{col}36'].number_format = '0.0%'
    
    # Additional growth rates
    model['B37'] = "Revenue CC"
    for idx in range(7, 51):
        col = get_column_letter(idx)
        yoy = get_column_letter(idx - 4)
        model[f'{col}37'] = f"=IF({yoy}20=0,0,{col}20/{yoy}20-1)"
        model[f'{col}37'].number_format = '0.0%'
    
    model['B38'] = "  Product y/y"
    for idx in range(7, 51):
        col = get_column_letter(idx)
        yoy = get_column_letter(idx - 4)
        model[f'{col}38'] = f"=IF({yoy}18=0,0,{col}18/{yoy}18-1)"
        model[f'{col}38'].number_format = '0.0%'
    
    model['B39'] = "  Service y/y"
    for idx in range(7, 51):
        col = get_column_letter(idx)
        yoy = get_column_letter(idx - 4)
        model[f'{col}39'] = f"=IF({yoy}19=0,0,{col}19/{yoy}19-1)"
        model[f'{col}39'].number_format = '0.0%'
    
    model['B40'] = "Online Stores y/y"
    for idx in range(7, 51):
        col = get_column_letter(idx)
        yoy = get_column_letter(idx - 4)
        model[f'{col}40'] = f"=IF({yoy}11=0,0,{col}11/{yoy}11-1)"
        model[f'{col}40'].number_format = '0.0%'
    
    model['B41'] = "Third-party y/y"
    for idx in range(7, 51):
        col = get_column_letter(idx)
        yoy = get_column_letter(idx - 4)
        model[f'{col}41'] = f"=IF({yoy}13=0,0,{col}13/{yoy}13-1)"
        model[f'{col}41'].number_format = '0.0%'
    
    model['B42'] = "Subscription y/y"
    for idx in range(7, 51):
        col = get_column_letter(idx)
        yoy = get_column_letter(idx - 4)
        model[f'{col}42'] = f"=IF({yoy}14=0,0,{col}14/{yoy}14-1)"
        model[f'{col}42'].number_format = '0.0%'
    
    model['B43'] = "Ads y/y"
    for idx in range(7, 51):
        col = get_column_letter(idx)
        yoy = get_column_letter(idx - 4)
        model[f'{col}43'] = f"=IF({yoy}15=0,0,{col}15/{yoy}15-1)"
        model[f'{col}43'].number_format = '0.0%'
    
    model['B44'] = "AWS y/y"
    for idx in range(7, 51):
        col = get_column_letter(idx)
        yoy = get_column_letter(idx - 4)
        model[f'{col}44'] = f"=IF({yoy}9=0,0,{col}9/{yoy}9-1)"
        model[f'{col}44'].number_format = '0.0%'
    
    # Row 45: Gross Margin %
    model['B45'] = "Gross Margin"
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}45'] = f"=IF({col}20=0,0,{col}23/{col}20)"
        model[f'{col}45'].number_format = '0.0%'
    
    # ==========================================
    # Balance Sheet & Cash Flow placeholders
    # ==========================================
    
    for row_num, label in [
        (47, "Net Cash"), (48, "Cash"), (49, "AR"), (50, "Inventories"),
        (51, "PP&E"), (52, "Leases"), (53, "Goodwill"), (54, "OA"), (55, "Assets"),
        (57, "AP"), (58, "AE"), (59, "DR"), (60, "Leases"), (61, "Debt"),
        (62, "OLTL"), (63, "SE"), (64, "L+SE"),
        (66, "Model NI"), (67, "Reported NI"), (68, "D&A"), (69, "SBC"),
        (70, "Other"), (71, "Other"), (72, "DT"), (73, "WC"), (74, "CFFO"),
        (76, "CapEx"), (77, "Sale of CapEx"), (78, "Acquisitions"), (79, "Investments"),
        (80, "CFFI"), (82, "Buybacks"), (83, "Debt"), (84, "CFFF"), (85, "FX"),
        (86, "CIC"), (88, "Headcount"),
        (90, "North America OI"), (91, "International OI"), (92, "AWS OI"), (93, "Shipping")
    ]:
        model[f'B{row_num}'] = label
    
    # Fill segment OIs
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}90'] = f"={col}28*0.7"
        model[f'{col}90'].number_format = '$#,##0'
        model[f'{col}91'] = f"={col}28*0.15"
        model[f'{col}91'].number_format = '$#,##0'
        model[f'{col}92'] = f"={col}28*0.25"
        model[f'{col}92'].number_format = '$#,##0'
        model[f'{col}93'] = f"={col}22*0.8"
        model[f'{col}93'].number_format = '$#,##0'
    
    # ==========================================
    # FCF and DCF
    # ==========================================
    
    # Row 95: FCF
    model['B95'] = "FCF"
    model['B95'].font = Font(bold=True, size=11)
    
    # Get actual FCF from cash flow data
    cash_flow = data['quarterly_cash']
    if cash_flow is not None:
        for key in ['Operating Cash Flow', 'Capital Expenditure']:
            if key in cash_flow.index:
                quarters_data = list(cash_flow.columns)[:40]
                for idx, quarter in enumerate(quarters_data, start=3):
                    if idx > 42:
                        break
                    col = get_column_letter(idx)
                    try:
                        if key == 'Operating Cash Flow':
                            ocf = cash_flow.loc[key, quarter]
                        else:
                            capex = cash_flow.loc[key, quarter]
                            
                        # Calculate FCF = OCF + CapEx (CapEx is negative)
                        # This is simplified - in reality need both values
                    except:
                        pass
    
    # FCF formula for all periods
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}95'] = f"={col}74+{col}76+{col}77+{col}78+{col}79"
        model[f'{col}95'].number_format = '$#,##0'
    
    # Row 96: FCF TTM
    model['B96'] = "FCF TTM"
    model['B96'].font = Font(bold=True)
    for idx in range(6, 51):
        col = get_column_letter(idx)
        col1 = get_column_letter(idx - 3)
        model[f'{col}96'] = f"=SUM({col1}95:{col}95)"
        model[f'{col}96'].number_format = '$#,##0'
    
    # ==========================================
    # DCF Calculation Section
    # ==========================================
    
    model['B98'] = "DCF CALCULATION"
    model['B98'].font = Font(bold=True, size=12, color="006100")
    
    model['B99'] = "WACC"
    model['C99'] = 0.09
    model['C99'].number_format = '0.0%'
    
    model['B100'] = "Terminal Growth"
    model['C100'] = 0.03
    model['C100'].number_format = '0.0%'
    
    # Annual FCF (sum of 4 quarters)
    for year in range(1, 6):
        row = 100 + year
        model[f'B{row}'] = f"Year {year} FCF"
        # Sum forecast quarters
        start_col = 43 + (year - 1) * 4
        end_col = start_col + 3
        start = get_column_letter(start_col)
        end = get_column_letter(end_col)
        model[f'C{row}'] = f"=SUM({start}95:{end}95)"
        model[f'C{row}'].number_format = '$#,##0'
    
    # PV of FCFs
    for year in range(1, 6):
        row = 106 + year
        model[f'B{row}'] = f"PV of FCF Y{year}"
        fcf_row = 100 + year
        model[f'C{row}'] = f"=C{fcf_row}/(1+$C$99)^{year}"
        model[f'C{row}'].number_format = '$#,##0'
    
    # Terminal Value
    model['B113'] = "Terminal Value"
    model['C113'] = f"=C105*(1+C100)/(C99-C100)"
    model['C113'].number_format = '$#,##0'
    
    model['B114'] = "PV of Terminal Value"
    model['C114'] = f"=C113/(1+C99)^5"
    model['C114'].number_format = '$#,##0'
    
    model['B115'] = "Enterprise Value"
    model['B115'].font = Font(bold=True, size=11)
    model['C115'] = f"=SUM(C107:C111)+C114"
    model['C115'].number_format = '$#,##0'
    model['C115'].fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    
    model['B116'] = "+ Cash"
    model['C116'] = cash
    model['C116'].number_format = '$#,##0'
    
    model['B117'] = "- Debt"
    model['C117'] = debt
    model['C117'].number_format = '$#,##0'
    
    model['B118'] = "Equity Value"
    model['B118'].font = Font(bold=True, size=11, color="006100")
    model['C118'] = f"=C115+C116-C117"
    model['C118'].number_format = '$#,##0'
    model['C118'].fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    
    model['B119'] = "Shares Outstanding"
    model['C119'] = shares / 1e3
    model['C119'].number_format = '#,##0.0'
    
    model['B120'] = "Per Share Value"
    model['B120'].font = Font(bold=True, size=14, color="006100")
    model['C120'] = f"=C118/(C119*1000)"
    model['C120'].number_format = '$0.00'
    
    model['B122'] = "Stock Price"
    model['C122'] = current_price
    model['C122'].number_format = '$0.00'
    
    model['B123'] = "Upside/Downside"
    model['C123'] = f"=C120/C122-1"
    model['C123'].number_format = '0.0%'
    
    # Formatting
    model.column_dimensions['A'].width = 3
    model.column_dimensions['B'].width = 22
    for col_idx in range(3, 100):
        col = get_column_letter(col_idx)
        model.column_dimensions[col].width = 10
    
    # Bold labels
    for row in range(1, 125):
        cell = model.cell(row=row, column=2)
        if cell.value:
            cell.font = Font(bold=True)
    
    # Save
    output_dir = './output'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'AMZN_DCF_Model_v2.xlsx')
    wb.save(output_path)
    
    size_kb = os.path.getsize(output_path) / 1024
    print(f"✅ Generated: {output_path} ({size_kb:.1f} KB)")
    
    return output_path


if __name__ == "__main__":
    create_amazon_model_v2()
