#!/usr/bin/env python3
"""
Generate Amazon DCF Model matching sample format exactly

Structure based on AMZN.xlsx:
- 2 sheets: Main (summary + DCF results) + Model (detailed quarterly + DCF calc)
- Historical quarters Q117-Q226 (40 quarters)
- Revenue segmentation (NorthAmerica, International, AWS)
- Full P&L, Balance Sheet, Cash Flow
- DCF: WACC, FCF projections, Terminal Value, PV, NPV, Target Price
- All Excel formulas linking cells
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("Installing openpyxl...")
    os.system(f"{sys.executable} -m pip install openpyxl pandas -q")
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter


def get_amazon_quarterly_data():
    """Get Amazon quarterly financial data from Yahoo Finance"""
    try:
        import yfinance as yf
        
        stock = yf.Ticker("AMZN")
        
        # Get quarterly financials
        quarterly_income = stock.quarterly_income_stmt
        quarterly_balance = stock.quarterly_balance_sheet
        quarterly_cash = stock.quarterly_cashflow
        
        info = stock.info
        
        return {
            'income': quarterly_income,
            'balance': quarterly_balance,
            'cash': quarterly_cash,
            'info': info
        }
    except Exception as e:
        print(f"Error fetching AMZN data: {e}")
        return None


def create_amazon_dcf_model():
    """Create Amazon DCF Excel matching sample format"""
    
    print(f"\n{'='*60}")
    print(f"Generating Amazon DCF Model (AMZN.xlsx format)")
    print(f"{'='*60}")
    
    # Get Amazon data
    data = get_amazon_quarterly_data()
    if not data:
        print("❌ Failed to get AMZN data")
        return None
    
    # Create workbook
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    
    # Create sheets
    main = wb.create_sheet("Main", 0)
    model = wb.create_sheet("Model")
    
    info = data.get('info', {})
    income = data.get('income')
    balance = data.get('balance')
    cash = data.get('cash')
    
    # Get quarters
    if income is not None and not income.empty:
        quarters = list(income.columns)[:40]  # Max 40 quarters
    else:
        quarters = []
    
    # ==========================================
    # MAIN SHEET (Summary + DCF Results)
    # ==========================================
    
    # Company info (left side)
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
    
    # Amazon section
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
    
    # Financial summary (right side - columns J-K)
    current_price = info.get('currentPrice', info.get('regularMarketPrice', 226))
    shares = info.get('sharesOutstanding', 0) / 1e6  # in millions
    
    main['J2'] = "Price"
    main['K2'] = current_price
    main['K2'].number_format = '$#,##0.00'
    
    main['J3'] = "Shares"
    main['K3'] = shares / 1e3  # in billions
    main['K3'].number_format = '#,##0'
    main['L3'] = "Q225"
    
    main['J4'] = "MC"
    main['K4'] = f"=K3*K2*1000"  # Convert back to millions
    main['K4'].number_format = '$#,##0'
    
    total_cash = info.get('totalCash', info.get('cash', 93180)) / 1e6
    total_debt = info.get('totalDebt', info.get('totalDebt', 50718)) / 1e6
    
    main['J5'] = "Cash"
    main['K5'] = total_cash
    main['K5'].number_format = '$#,##0'
    main['L5'] = "Q225"
    
    main['J6'] = "Debt"
    main['K6'] = total_debt
    main['K6'].number_format = '$#,##0'
    main['L6'] = "Q225"
    
    main['J7'] = "EV"
    main['K7'] = f"=K4-K5+K6"
    main['K7'].number_format = '$#,##0'
    
    # DCF Results Section on Main
    main['J10'] = "DCF VALUATION"
    main['J10'].font = Font(bold=True, size=12)
    
    main['J12'] = "WACC"
    main['K12'] = 0.09  # 9% assumption
    main['K12'].number_format = '0.0%'
    
    main['J13'] = "Terminal Growth"
    main['K13'] = 0.03  # 3% assumption
    main['K13'].number_format = '0.0%'
    
    main['J14'] = "PV of FCF (5yr)"
    main['K14'] = f"=Model!C101"  # Reference to model DCF calc
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
    
    # Formatting Main
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
    # MODEL SHEET (Detailed Financials + DCF)
    # ==========================================
    
    # Row 1: Reference to Main
    model['A1'] = "Main"
    
    # Quarter headers (Row 2)
    # Generate 40 quarters from Q117 to Q226
    quarter_list = []
    years = range(17, 27)  # 2017-2026
    for year in years:
        for q in range(1, 5):
            quarter_list.append(f"Q{q}{year:02d}")
    
    # Write quarter headers
    for idx, q_str in enumerate(quarter_list[:40], start=3):  # C onwards
        col_letter = get_column_letter(idx)
        model[f'{col_letter}2'] = q_str
        model[f'{col_letter}2'].alignment = Alignment(horizontal='center')
    
    # Add forecast quarter headers with formulas
    for idx in range(43, 51):  # AM-AU (8 forecast quarters)
        col_letter = get_column_letter(idx)
        prev_col = get_column_letter(idx - 1)
        model[f'{col_letter}2'] = f"=+{prev_col}2+1"
        model[f'{col_letter}2'].alignment = Alignment(horizontal='center')
    
    # Add yearly columns (1995-2000 historical + future years)
    yearly_start = 65  # Column BM
    for year_idx in range(30):  # 30 years
        col_idx = yearly_start + year_idx
        col_letter = get_column_letter(col_idx)
        if year_idx == 0:
            model[f'{col_letter}2'] = 1995
        else:
            prev_col = get_column_letter(col_idx - 1)
            model[f'{col_letter}2'] = f"=+{prev_col}2+1"
    
    # Helper to fill data from Yahoo Finance
    def fill_data_from_yahoo(row, yahoo_key, is_expense=False, ratio=None):
        model[f'B{row}'] = yahoo_key
        if income is not None and not income.empty and yahoo_key in income.index:
            for idx, quarter in enumerate(quarters, start=3):
                col_letter = get_column_letter(idx)
                try:
                    val = income.loc[yahoo_key, quarter]
                    if pd.notna(val):
                        val_millions = abs(val) / 1e6 if is_expense else val / 1e6
                        model[f'{col_letter}{row}'] = val_millions
                        model[f'{col_letter}{row}'].number_format = '$#,##0'
                except:
                    pass
        
        # Fill forecasts with formulas
        for idx in range(len(quarters) + 3, min(len(quarters) + 12, 51)):
            col_letter = get_column_letter(idx)
            if ratio:
                ref_col = get_column_letter(idx if idx < len(quarters) + 3 else 3)
                model[f'{col_letter}{row}'] = f"=+{ref_col}20*{ratio}"
            else:
                prev_col = get_column_letter(idx - 4)  # Same quarter last year
                model[f'{col_letter}{row}'] = f"=+{prev_col}{row}*1.05"
            model[f'{col_letter}{row}'].number_format = '$#,##0'
    
    # Row 3: North America Revenue
    model['B3'] = "NorthAmerica"
    model['B3'].font = Font(bold=True)
    # Since Yahoo doesn't break this down, use total as placeholder
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                if 'Total Revenue' in income.index:
                    val = income.loc['Total Revenue', quarter]
                    if pd.notna(val):
                        model[f'{col_letter}3'] = val * 0.6 / 1e6  # 60% NA estimate
                        model[f'{col_letter}3'].number_format = '$#,##0'
            except:
                pass
    
    # Forecast NA
    for idx in range(len(quarters) + 3, 51):
        col_letter = get_column_letter(idx)
        prev_col = get_column_letter(idx - 4)
        model[f'{col_letter}3'] = f"=+{prev_col}3*1.08"  # 8% growth
        model[f'{col_letter}3'].number_format = '$#,##0'
    
    # Row 4: Media (sub)
    model['B4'] = "  Media"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}4'] = f"=+{col_letter}3*0.3"  # 30% of NA
        model[f'{col_letter}4'].number_format = '$#,##0'
    
    # Row 5: Electronics (sub)
    model['B5'] = "  Electronics/General"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}5'] = f"=+{col_letter}3*0.7"  # 70% of NA
        model[f'{col_letter}5'].number_format = '$#,##0'
    
    # Row 6: International
    model['B6'] = "International"
    model['B6'].font = Font(bold=True)
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                if 'Total Revenue' in income.index:
                    val = income.loc['Total Revenue', quarter]
                    if pd.notna(val):
                        model[f'{col_letter}6'] = val * 0.25 / 1e6  # 25% Int'l estimate
                        model[f'{col_letter}6'].number_format = '$#,##0'
            except:
                pass
    
    for idx in range(len(quarters) + 3, 51):
        col_letter = get_column_letter(idx)
        prev_col = get_column_letter(idx - 4)
        model[f'{col_letter}6'] = f"=+{prev_col}6*1.05"  # 5% growth
        model[f'{col_letter}6'].number_format = '$#,##0'
    
    # Row 7: Int'l Media (sub)
    model['B7'] = "  Media"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}7'] = f"=+{col_letter}6*0.3"
        model[f'{col_letter}7'].number_format = '$#,##0'
    
    # Row 8: Int'l Electronics (sub)
    model['B8'] = "  Electronics/General"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}8'] = f"=+{col_letter}6*0.7"
        model[f'{col_letter}8'].number_format = '$#,##0'
    
    # Row 9: AWS
    model['B9'] = "AWS"
    model['B9'].font = Font(bold=True)
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                if 'Total Revenue' in income.index:
                    val = income.loc['Total Revenue', quarter]
                    if pd.notna(val):
                        model[f'{col_letter}9'] = val * 0.15 / 1e6  # 15% AWS estimate
                        model[f'{col_letter}9'].number_format = '$#,##0'
            except:
                pass
    
    for idx in range(len(quarters) + 3, 51):
        col_letter = get_column_letter(idx)
        prev_col = get_column_letter(idx - 4)
        model[f'{col_letter}9'] = f"=+{prev_col}9*1.15"  # 15% growth (AWS faster)
        model[f'{col_letter}9'].number_format = '$#,##0'
    
    # Row 11: Online Stores
    model['B11'] = "Online Stores"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}11'] = f"=+{col_letter}5+{col_letter}8"
        model[f'{col_letter}11'].number_format = '$#,##0'
    
    # Row 12: Physical Stores
    model['B12'] = "Physical Stores"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}12'] = f"=+{col_letter}20*0.02"  # 2% of total
        model[f'{col_letter}12'].number_format = '$#,##0'
    
    # Row 13: Third-party
    model['B13'] = "Third-party"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}13'] = f"=+{col_letter}20*0.25"  # 25% of total
        model[f'{col_letter}13'].number_format = '$#,##0'
    
    # Row 14: Subscription
    model['B14'] = "Subscription"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}14'] = f"=+{col_letter}20*0.08"  # 8% of total
        model[f'{col_letter}14'].number_format = '$#,##0'
    
    # Row 15: Ads
    model['B15'] = "Ads"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}15'] = f"=+{col_letter}20*0.12"  # 12% of total
        model[f'{col_letter}15'].number_format = '$#,##0'
    
    # Row 16: Other
    model['B16'] = "Other"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}16'] = f"=+{col_letter}20-SUM({col_letter}11:{col_letter}15)"
        model[f'{col_letter}16'].number_format = '$#,##0'
    
    # Row 18: Product
    model['B18'] = "Product"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}18'] = f"=+{col_letter}3+{col_letter}6-{col_letter}9"
        model[f'{col_letter}18'].number_format = '$#,##0'
    
    # Row 19: Services
    model['B19'] = "Services"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}19'] = f"=+{col_letter}9+{col_letter}14+{col_letter}15"
        model[f'{col_letter}19'].number_format = '$#,##0'
    
    # Row 20: Total Revenue
    model['B20'] = "Revenue"
    model['B20'].font = Font(bold=True, size=11)
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}20'] = f"=+{col_letter}3+{col_letter}6+{col_letter}9"
        model[f'{col_letter}20'].number_format = '$#,##0'
        model[f'{col_letter}20'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
    
    # Row 21: Cost of Sales
    model['B21'] = "Cost of Sales"
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                if 'Cost Of Revenue' in income.index:
                    val = income.loc['Cost Of Revenue', quarter]
                    if pd.notna(val):
                        model[f'{col_letter}21'] = abs(val) / 1e6
                        model[f'{col_letter}21'].number_format = '$#,##0'
            except:
                pass
    
    for idx in range(len(quarters) + 3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}21'] = f"=+{col_letter}20*0.55"  # 55% of revenue
        model[f'{col_letter}21'].number_format = '$#,##0'
    
    # Row 22: Fulfillment
    model['B22'] = "Fulfillment"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}22'] = f"=+{col_letter}20*0.15"  # 15% estimate
        model[f'{col_letter}22'].number_format = '$#,##0'
    
    # Row 23: Gross Margin
    model['B23'] = "Gross Margin"
    model['B23'].font = Font(bold=True)
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}23'] = f"=+{col_letter}20-{col_letter}21-{col_letter}22"
        model[f'{col_letter}23'].number_format = '$#,##0'
        model[f'{col_letter}23'].fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    # Row 24: Technology (R&D)
    model['B24'] = "Technology"
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                if 'Research Development' in income.index:
                    val = income.loc['Research Development', quarter]
                    if pd.notna(val):
                        model[f'{col_letter}24'] = abs(val) / 1e6
                        model[f'{col_letter}24'].number_format = '$#,##0'
            except:
                pass
    
    for idx in range(len(quarters) + 3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}24'] = f"=+{col_letter}20*0.16"  # 16% of revenue
        model[f'{col_letter}24'].number_format = '$#,##0'
    
    # Row 25: S&M (Sales & Marketing / SG&A)
    model['B25'] = "S&M"
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                if 'Selling General Administrative' in income.index:
                    val = income.loc['Selling General Administrative', quarter]
                    if pd.notna(val):
                        model[f'{col_letter}25'] = abs(val) / 1e6
                        model[f'{col_letter}25'].number_format = '$#,##0'
            except:
                pass
    
    for idx in range(len(quarters) + 3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}25'] = f"=+{col_letter}20*0.12"  # 12% of revenue
        model[f'{col_letter}25'].number_format = '$#,##0'
    
    # Row 26: G&A
    model['B26'] = "G&A"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}26'] = f"=+{col_letter}25*0.3"  # 30% of S&M
        model[f'{col_letter}26'].number_format = '$#,##0'
    
    # Row 27: OpEx
    model['B27'] = "OpEx"
    model['B27'].font = Font(bold=True)
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}27'] = f"=SUM({col_letter}24:{col_letter}26)"
        model[f'{col_letter}27'].number_format = '$#,##0'
    
    # Row 28: OpInc
    model['B28'] = "OpInc"
    model['B28'].font = Font(bold=True)
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}28'] = f"=+{col_letter}23-{col_letter}27"
        model[f'{col_letter}28'].number_format = '$#,##0'
        model[f'{col_letter}28'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
    
    # Row 29: Interest Expense
    model['B29'] = "Interest Expense"
    fill_data_from_yahoo(29, 'Interest Expense', is_expense=True, ratio=0.005)
    
    # Row 30: Pretax
    model['B30'] = "Pretax"
    model['B30'].font = Font(bold=True)
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}30'] = f"=+{col_letter}28-{col_letter}29"
        model[f'{col_letter}30'].number_format = '$#,##0'
    
    # Row 31: Taxes
    model['B31'] = "Taxes"
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                if 'Tax Provision' in income.index:
                    val = income.loc['Tax Provision', quarter]
                    if pd.notna(val):
                        model[f'{col_letter}31'] = abs(val) / 1e6
                        model[f'{col_letter}31'].number_format = '$#,##0'
            except:
                pass
    
    for idx in range(len(quarters) + 3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}31'] = f"=+{col_letter}30*0.18"  # 18% tax rate
        model[f'{col_letter}31'].number_format = '$#,##0'
    
    # Row 32: Net Income
    model['B32'] = "Net Income"
    model['B32'].font = Font(bold=True)
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}32'] = f"=+{col_letter}30-{col_letter}31"
        model[f'{col_letter}32'].number_format = '$#,##0'
        model[f'{col_letter}32'].fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    # Row 33: EPS
    model['B33'] = "EPS"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}33'] = f"=IF({col_letter}34=0,0,+{col_letter}32/{col_letter}34)"
        model[f'{col_letter}33'].number_format = '$0.00'
    
    # Row 34: Shares
    model['B34'] = "Shares"
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                shares_val = None
                for key in ['Basic Average Shares', 'Basic Shares Outstanding', 'Shareholders Equity']:
                    if key in income.index:
                        val = income.loc[key, quarter]
                        if pd.notna(val):
                            shares_val = val / 1e6
                            break
                if shares_val:
                    model[f'{col_letter}34'] = shares_val
                    model[f'{col_letter}34'].number_format = '#,##0'
            except:
                pass
    
    # Use latest for forecasts
    for idx in range(len(quarters) + 3, 51):
        col_letter = get_column_letter(idx)
        prev_col = get_column_letter(3 if len(quarters) == 0 else len(quarters) + 2)
        model[f'{col_letter}34'] = f"={prev_col}34"  # Keep flat
        model[f'{col_letter}34'].number_format = '#,##0'
    
    # Row 36: Revenue y/y
    model['B36'] = "Revenue y/y"
    model['B36'].font = Font(bold=True, italic=True)
    for idx in range(7, 51):  # Start Q4 for y/y
        col_letter = get_column_letter(idx)
        prev_year_col = get_column_letter(idx - 4)
        model[f'{col_letter}36'] = f"=IF({prev_year_col}20=0,0,+{col_letter}20/{prev_year_col}20-1)"
        model[f'{col_letter}36'].number_format = '0.0%'
    
    # Row 37: Revenue CC (Constant Currency - same as y/y for now)
    model['B37'] = "Revenue CC"
    model['B37'].font = Font(italic=True)
    for idx in range(7, 51):
        col_letter = get_column_letter(idx)
        prev_year_col = get_column_letter(idx - 4)
        model[f'{col_letter}37'] = f"=IF({prev_year_col}20=0,0,+{col_letter}20/{prev_year_col}20-1)"
        model[f'{col_letter}37'].number_format = '0.0%'
    
    # Row 38: Product y/y
    model['B38'] = "  Product y/y"
    for idx in range(7, 51):
        col_letter = get_column_letter(idx)
        prev_year_col = get_column_letter(idx - 4)
        model[f'{col_letter}38'] = f"=IF({prev_year_col}18=0,0,+{col_letter}18/{prev_year_col}18-1)"
        model[f'{col_letter}38'].number_format = '0.0%'
    
    # Row 39: Service y/y
    model['B39'] = "  Service y/y"
    for idx in range(7, 51):
        col_letter = get_column_letter(idx)
        prev_year_col = get_column_letter(idx - 4)
        model[f'{col_letter}39'] = f"=IF({prev_year_col}19=0,0,+{col_letter}19/{prev_year_col}19-1)"
        model[f'{col_letter}39'].number_format = '0.0%'
    
    # Row 40: Online Stores y/y
    model['B40'] = "Online Stores y/y"
    for idx in range(7, 51):
        col_letter = get_column_letter(idx)
        prev_year_col = get_column_letter(idx - 4)
        model[f'{col_letter}40'] = f"=IF({prev_year_col}11=0,0,+{col_letter}11/{prev_year_col}11-1)"
        model[f'{col_letter}40'].number_format = '0.0%'
    
    # Row 41: Third-party y/y
    model['B41'] = "Third-party y/y"
    for idx in range(7, 51):
        col_letter = get_column_letter(idx)
        prev_year_col = get_column_letter(idx - 4)
        model[f'{col_letter}41'] = f"=IF({prev_year_col}13=0,0,+{col_letter}13/{prev_year_col}13-1)"
        model[f'{col_letter}41'].number_format = '0.0%'
    
    # Row 42: Subscription y/y
    model['B42'] = "Subscription y/y"
    for idx in range(7, 51):
        col_letter = get_column_letter(idx)
        prev_year_col = get_column_letter(idx - 4)
        model[f'{col_letter}42'] = f"=IF({prev_year_col}14=0,0,+{col_letter}14/{prev_year_col}14-1)"
        model[f'{col_letter}42'].number_format = '0.0%'
    
    # Row 43: Ads y/y
    model['B43'] = "Ads y/y"
    for idx in range(7, 51):
        col_letter = get_column_letter(idx)
        prev_year_col = get_column_letter(idx - 4)
        model[f'{col_letter}43'] = f"=IF({prev_year_col}15=0,0,+{col_letter}15/{prev_year_col}15-1)"
        model[f'{col_letter}43'].number_format = '0.0%'
    
    # Row 44: AWS y/y
    model['B44'] = "AWS y/y"
    for idx in range(7, 51):
        col_letter = get_column_letter(idx)
        prev_year_col = get_column_letter(idx - 4)
        model[f'{col_letter}44'] = f"=IF({prev_year_col}9=0,0,+{col_letter}9/{prev_year_col}9-1)"
        model[f'{col_letter}44'].number_format = '0.0%'
    
    # Row 45: Gross Margin %
    model['B45'] = "Gross Margin"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}45'] = f"=IF({col_letter}20=0,0,+{col_letter}23/{col_letter}20)"
        model[f'{col_letter}45'].number_format = '0.0%'
    
    # Balance Sheet rows (47-64)
    model['B47'] = "Net Cash"
    model['B48'] = "Cash"
    model['B49'] = "AR"
    model['B50'] = "Inventories"
    model['B51'] = "PP&E"
    model['B52'] = "Leases"
    model['B53'] = "Goodwill"
    model['B54'] = "OA"
    model['B55'] = "Assets"
    model['B57'] = "AP"
    model['B58'] = "AE"
    model['B59'] = "DR"
    model['B60'] = "Leases"
    model['B61'] = "Debt"
    model['B62'] = "OLTL"
    model['B63'] = "SE"
    model['B64'] = "L+SE"
    
    # Fill balance sheet data if available
    if balance is not None and not balance.empty:
        bs_mapping = {
            48: 'Cash And Cash Equivalents',
            49: 'Accounts Receivable',
            50: 'Inventory',
            51: 'Net PPE',
            53: 'Goodwill',
            57: 'Accounts Payable',
            61: 'Long Term Debt'
        }
        for row, key in bs_mapping.items():
            for idx, quarter in enumerate(quarters, start=3):
                col_letter = get_column_letter(idx)
                try:
                    if key in balance.index:
                        val = balance.loc[key, quarter]
                        if pd.notna(val):
                            model[f'{col_letter}{row}'] = val / 1e6
                            model[f'{col_letter}{row}'].number_format = '$#,##0'
                except:
                    pass
    
    # Cash Flow rows (66-96)
    model['B66'] = "Model NI"
    model['B67'] = "Reported NI"
    model['B68'] = "D&A"
    model['B69'] = "SBC"
    model['B70'] = "Other"
    model['B71'] = "Other"
    model['B72'] = "DT"
    model['B73'] = "WC"
    model['B74'] = "CFFO"
    model['B76'] = "CapEx"
    model['B77'] = "Sale of CapEx"
    model['B78'] = "Acquisitions"
    model['B79'] = "Investments"
    model['B80'] = "CFFI"
    model['B82'] = "Buybacks"
    model['B83'] = "Debt"
    model['B84'] = "CFFF"
    model['B85'] = "FX"
    model['B86'] = "CIC"
    model['B88'] = "Headcount"
    
    # Row 90: North America OI
    model['B90'] = "North America OI"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}90'] = f"=+{col_letter}28*0.7"  # 70% of OpInc
        model[f'{col_letter}90'].number_format = '$#,##0'
    
    # Row 91: International OI
    model['B91'] = "International OI"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}91'] = f"=+{col_letter}28*0.15"  # 15% of OpInc (often negative)
        model[f'{col_letter}91'].number_format = '$#,##0'
    
    # Row 92: AWS OI
    model['B92'] = "AWS OI"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}92'] = f"=+{col_letter}28*0.25"  # 25% of OpInc (high margin)
        model[f'{col_letter}92'].number_format = '$#,##0'
    
    # Row 93: Shipping
    model['B93'] = "Shipping"
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}93'] = f"=+{col_letter}22*0.8"  # Part of fulfillment
        model[f'{col_letter}93'].number_format = '$#,##0'
    
    # Fill cash flow data
    if cash is not None and not cash.empty:
        cf_mapping = {
            68: 'Depreciation',
            69: 'Stock Based Compensation',
            74: 'Operating Cash Flow',
            76: 'Capital Expenditure',
            80: 'Investing Cash Flow',
            82: 'Repurchase Of Capital Stock',
            84: 'Financing Cash Flow',
            86: 'Free Cash Flow'
        }
        for row, key in cf_mapping.items():
            for idx, quarter in enumerate(quarters, start=3):
                col_letter = get_column_letter(idx)
                try:
                    if key in cash.index:
                        val = cash.loc[key, quarter]
                        if pd.notna(val):
                            model[f'{col_letter}{row}'] = val / 1e6
                            model[f'{col_letter}{row}'].number_format = '$#,##0'
                except:
                    pass
    
    # Link Model NI to Net Income
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}66'] = f"={col_letter}32"
        model[f'{col_letter}67'] = f"={col_letter}32"
    
    # Row 95: FCF
    model['B95'] = "FCF"
    model['B95'].font = Font(bold=True, size=11)
    for idx in range(3, 51):
        col_letter = get_column_letter(idx)
        model[f'{col_letter}95'] = f"=+{col_letter}74+{col_letter}76+{col_letter}77+{col_letter}78+{col_letter}79"
        model[f'{col_letter}95'].number_format = '$#,##0'
    
    # Row 96: FCF TTM
    model['B96'] = "FCF TTM"
    model['B96'].font = Font(bold=True)
    for idx in range(6, 51):  # Need 4 quarters
        col_letter = get_column_letter(idx)
        col1 = get_column_letter(idx - 3)
        col2 = get_column_letter(idx - 2)
        col3 = get_column_letter(idx - 1)
        model[f'{col_letter}96'] = f"=SUM({col1}95:{col_letter}95)"
        model[f'{col_letter}96'].number_format = '$#,##0'
    
    # ==========================================
    # DCF CALCULATIONS (Rows 98-105)
    # ==========================================
    
    model['B98'] = "DCF CALCULATION"
    model['B98'].font = Font(bold=True, size=12, color="006100")
    
    model['B99'] = "WACC"
    model['C99'] = 0.09  # 9%
    model['C99'].number_format = '0.0%'
    
    model['B100'] = "Terminal Growth"
    model['C100'] = 0.03  # 3%
    model['C100'].number_format = '0.0%'
    
    # FCF Forecast (next 5 years annual)
    model['B101'] = "Year 1 FCF"
    model['B102'] = "Year 2 FCF"
    model['B103'] = "Year 3 FCF"
    model['B104'] = "Year 4 FCF"
    model['B105'] = "Year 5 FCF"
    
    # Calculate annual FCF from quarterly (sum of next 4 quarters)
    last_q_idx = len(quarters) + 2 if quarters else 5
    for year in range(1, 6):
        row = 100 + year
        # Sum 4 quarters starting from forecast period
        col1 = get_column_letter(last_q_idx + (year-1)*4 + 1)
        col2 = get_column_letter(last_q_idx + (year-1)*4 + 4)
        model[f'C{row}'] = f"=SUM({col1}95:{col2}95)"  # Sum quarterly FCF
        model[f'C{row}'].number_format = '$#,##0'
    
    # DCF rows
    model['B107'] = "PV of FCF Y1"
    model['B108'] = "PV of FCF Y2"
    model['B109'] = "PV of FCF Y3"
    model['B110'] = "PV of FCF Y4"
    model['B111'] = "PV of FCF Y5"
    
    for year in range(1, 6):
        row = 106 + year
        fcf_row = 100 + year
        model[f'C{row}'] = f"=C{fcf_row}/(1+$C$99)^{year}"
        model[f'C{row}'].number_format = '$#,##0'
    
    # Terminal Value
    model['B113'] = "Terminal Value"
    model['C113'] = f"=C105*(1+C100)/(C99-C100)"  # Gordon Growth: FCF5*(1+g)/(WACC-g)
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
    model['C116'] = total_cash
    model['C116'].number_format = '$#,##0'
    
    model['B117'] = "- Debt"
    model['C117'] = total_debt
    model['C117'].number_format = '$#,##0'
    
    model['B118'] = "Equity Value"
    model['B118'].font = Font(bold=True, size=11, color="006100")
    model['C118'] = f"=C115+C116-C117"
    model['C118'].number_format = '$#,##0'
    model['C118'].fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    
    model['B119'] = "Shares Outstanding"
    model['C119'] = shares / 1e3  # in billions
    model['C119'].number_format = '#,##0.0'
    
    model['B120'] = "Per Share Value"
    model['B120'].font = Font(bold=True, size=14, color="006100")
    model['C120'] = f"=C118/(C119*1000)"  # Convert millions to billions
    model['C120'].number_format = '$0.00'
    
    # Stock Price reference
    model['B122'] = "Stock Price"
    model['C122'] = current_price
    model['C122'].number_format = '$0.00'
    
    model['B123'] = "Upside/Downside"
    model['C123'] = f"=C120/C122-1"
    model['C123'].number_format = '0.0%'
    if model['C123'].value and isinstance(model['C123'].value, (int, float)) and model['C123'].value > 0:
        model['C123'].font = Font(color="006100")
    else:
        model['C123'].font = Font(color="C00000")
    
    # Formatting Model sheet
    model.column_dimensions['A'].width = 3
    model.column_dimensions['B'].width = 22
    
    for col_idx in range(3, 100):
        col_letter = get_column_letter(col_idx)
        model.column_dimensions[col_letter].width = 10
    
    # Bold all row labels
    for row in range(1, 130):
        cell = model.cell(row=row, column=2)
        if cell.value:
            cell.font = Font(bold=True)
    
    # Save
    output_dir = './output'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'AMZN_DCF_Model.xlsx')
    wb.save(output_path)
    
    size_kb = os.path.getsize(output_path) / 1024
    print(f"✅ Generated: {output_path} ({size_kb:.1f} KB)")
    
    return output_path


if __name__ == "__main__":
    create_amazon_dcf_model()
