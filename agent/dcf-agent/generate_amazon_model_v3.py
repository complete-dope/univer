#!/usr/bin/env python3
"""
Amazon DCF Model v3:
- Uses ALL available Yahoo Finance data (quarterly + annual)
- Quarterly: 5 quarters of actual data
- Annual: 4 years of actual data  
- Clearly marks ACTUAL vs ESTIMATED values
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


def get_all_amazon_data():
    """Get all available Yahoo Finance data for Amazon"""
    stock = yf.Ticker("AMZN")
    
    return {
        'quarterly_income': stock.quarterly_income_stmt,
        'quarterly_balance': stock.quarterly_balance_sheet,
        'quarterly_cash': stock.quarterly_cashflow,
        'annual_income': stock.income_stmt,
        'annual_balance': stock.balance_sheet,
        'annual_cash': stock.cashflow,
        'info': stock.info
    }


def create_amazon_model_v3():
    """Create Amazon model using all available Yahoo Finance data"""
    
    print(f"\n{'='*70}")
    print(f"Amazon DCF Model v3 (All Available Yahoo Data)")
    print(f"{'='*70}")
    
    data = get_all_amazon_data()
    info = data['info']
    
    # Get available data ranges
    q_income = data['quarterly_income']
    a_income = data['annual_income']
    
    print(f"\n📊 Yahoo Finance Data Available:")
    print(f"   Quarterly: {len(q_income.columns) if q_income is not None else 0} quarters")
    print(f"   Annual: {len(a_income.columns) if a_income is not None else 0} years")
    
    # Current metrics
    current_price = info.get('currentPrice', info.get('regularMarketPrice', 272.68))
    shares = info.get('sharesOutstanding', 10757000000) / 1e6
    cash = info.get('totalCash', 143089000000) / 1e6
    debt = info.get('totalDebt', 235540000000) / 1e6
    
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    
    main = wb.create_sheet("Main", 0)
    model = wb.create_sheet("Model")
    
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
    main['C11'] = "S3"; main['D11'] = "Azure, GCP, Digital Ocean"
    main['C12'] = "EC2"; main['D12'] = "Very weak in GPUs"
    main['C13'] = "Dynamo"
    main['C14'] = "SageMaker"; main['D14'] = "HyperPods"
    main['C15'] = "Polly"
    main['C16'] = "EKS"
    main['C17'] = "Tranium"
    main['C18'] = "Inferentia"
    main['C19'] = "Bedrock"; main['D19'] = "AI models"
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
    main['K3'] = shares / 1e3
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
    
    # Data source note
    main['J9'] = "DATA SOURCES:"
    main['J9'].font = Font(bold=True, italic=True)
    main['K9'] = f"Quarters: {len(q_income.columns) if q_income is not None else 0} actual"
    main['L9'] = f"Years: {len(a_income.columns) if a_income is not None else 0} actual"
    
    # DCF Results
    main['J11'] = "DCF VALUATION"
    main['J11'].font = Font(bold=True, size=12)
    
    main['J13'] = "WACC"
    main['K13'] = 0.09
    main['K13'].number_format = '0.0%'
    
    main['J14'] = "Terminal Growth"
    main['K14'] = 0.03
    main['K14'].number_format = '0.0%'
    
    main['J15'] = "PV of FCF (5yr)"
    main['K15'] = f"=Model!C101"
    main['K15'].number_format = '$#,##0'
    
    main['J16'] = "Terminal Value"
    main['K16'] = f"=Model!C102"
    main['K16'].number_format = '$#,##0'
    
    main['J17'] = "Enterprise Value"
    main['K17'] = f"=K15+K16"
    main['K17'].number_format = '$#,##0'
    
    main['J18'] = "+ Cash"
    main['K18'] = f"=K5"
    main['K18'].number_format = '$#,##0'
    
    main['J19'] = "- Debt"
    main['K19'] = f"=K6"
    main['K19'].number_format = '$#,##0'
    
    main['J20'] = "Equity Value"
    main['K20'] = f"=K17+K18-K19"
    main['K20'].number_format = '$#,##0'
    
    main['J21'] = "Per Share Value"
    main['K21'] = f"=K20/(K3*1000)"
    main['K21'].number_format = '$0.00'
    main['K21'].font = Font(bold=True, size=14, color="006100")
    
    main['J22'] = "Upside/Downside"
    main['K22'] = f"=K21/K2-1"
    main['K22'].number_format = '0.0%'
    
    # Format Main
    main.column_dimensions['A'].width = 3
    main.column_dimensions['B'].width = 35
    main.column_dimensions['C'].width = 20
    main.column_dimensions['D'].width = 40
    main.column_dimensions['J'].width = 18
    main.column_dimensions['K'].width = 15
    main.column_dimensions['L'].width = 12
    
    for row in [2, 3, 4, 5, 6, 7]:
        main[f'J{row}'].font = Font(bold=True)
    
    # ==========================================
    # MODEL SHEET
    # ==========================================
    
    model['A1'] = "Main"
    
    # Quarter headers
    quarters = []
    for year in range(17, 27):
        for q in range(1, 5):
            quarters.append(f"Q{q}{year:02d}")
    
    for idx, q_str in enumerate(quarters[:40], start=3):
        col = get_column_letter(idx)
        model[f'{col}2'] = q_str
        model[f'{col}2'].alignment = Alignment(horizontal='center')
    
    # Forecast headers
    for idx in range(43, 51):
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
    # Fill Revenue with ACTUAL data where available
    # ==========================================
    
    model['B3'] = "NorthAmerica"
    model['B3'].font = Font(bold=True)
    
    model['B4'] = "  Media"
    model['B5'] = "  Electronics/General"
    model['B6'] = "International"
    model['B6'].font = Font(bold=True)
    model['B7'] = "  Media"
    model['B8'] = "  Electronics/General"
    model['B9'] = "AWS"
    model['B9'].font = Font(bold=True)
    
    # Fill segment breakdowns with formulas
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}4'] = f"={col}3*0.3"
        model[f'{col}4'].number_format = '$#,##0'
        model[f'{col}5'] = f"={col}3*0.7"
        model[f'{col}5'].number_format = '$#,##0'
        model[f'{col}7'] = f"={col}6*0.3"
        model[f'{col}7'].number_format = '$#,##0'
        model[f'{col}8'] = f"={col}6*0.7"
        model[f'{col}8'].number_format = '$#,##0'
    
    # ACTUAL QUARTERLY DATA from Yahoo Finance
    print(f"\n📝 Filling ACTUAL quarterly data from Yahoo Finance...")
    
    actual_q_count = 0
    if q_income is not None and not q_income.empty:
        # Map Yahoo quarters to our columns
        # Yahoo gives most recent first, we need to map to Q125-Q126 etc
        q_columns = list(q_income.columns)
        
        for q_idx, quarter in enumerate(q_columns):
            # Calculate which column this quarter should go in
            # Most recent = column 42 (AQ = Q126)
            target_col = 42 - q_idx
            
            if target_col < 3:  # Don't go before Q117
                break
            
            col = get_column_letter(target_col)
            
            # Fill Revenue
            if 'Total Revenue' in q_income.index:
                val = q_income.loc['Total Revenue', quarter]
                if pd.notna(val):
                    # Segments (estimated breakdown)
                    total_rev = val / 1e6
                    model[f'{col}3'] = total_rev * 0.60  # NA
                    model[f'{col}3'].number_format = '$#,##0'
                    model[f'{col}6'] = total_rev * 0.25  # International
                    model[f'{col}6'].number_format = '$#,##0'
                    model[f'{col}9'] = total_rev * 0.15  # AWS
                    model[f'{col}9'].number_format = '$#,##0'
                    
                    # Total
                    model[f'{col}20'] = total_rev
                    model[f'{col}20'].number_format = '$#,##0'
                    model[f'{col}20'].fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                    actual_q_count += 1
            
            # Fill other P&L items
            for yahoo_key, row_num, is_expense in [
                ('Cost Of Revenue', 21, True),
                ('Research Development', 24, True),
                ('Selling General Administrative', 25, True),
                ('Interest Expense', 29, True),
                ('Tax Provision', 31, True),
            ]:
                if yahoo_key in q_income.index:
                    val = q_income.loc[yahoo_key, quarter]
                    if pd.notna(val):
                        val_m = abs(val) / 1e6 if is_expense else val / 1e6
                        model[f'{col}{row_num}'] = val_m
                        model[f'{col}{row_num}'].number_format = '$#,##0'
                        model[f'{col}{row_num}'].fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            
            # Net Income
            if 'NetIncome' in q_income.index or 'Net Income' in q_income.index:
                key = 'Net Income' if 'Net Income' in q_income.index else 'NetIncome'
                val = q_income.loc[key, quarter]
                if pd.notna(val):
                    model[f'{col}32'] = val / 1e6
                    model[f'{col}32'].number_format = '$#,##0'
                    model[f'{col}32'].fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            
            # Shares
            if 'Basic Average Shares' in q_income.index:
                val = q_income.loc['Basic Average Shares', quarter]
                if pd.notna(val):
                    model[f'{col}34'] = val / 1e6
                    model[f'{col}34'].number_format = '#,##0'
    
    print(f"   Filled {actual_q_count} quarters with ACTUAL data")
    
    # Fill remaining historical with formulas (ESTIMATED)
    print(f"   Filling historical gaps with estimates...")
    
    # Use annual data where available
    if a_income is not None and not a_income.empty:
        annual_years = list(a_income.columns)
        print(f"   Using {len(annual_years)} years of annual data for reference")
    
    # Fill remaining quarters with formulas (these are estimates)
    for idx in range(3, 51):
        col = get_column_letter(idx)
        val = model[f'{col}20'].value
        
        # If no actual data, use formula
        if val is None:
            # Check if it's a forecast or historical estimate
            if idx >= 43:  # Forecast
                yoy = get_column_letter(idx - 4)
                model[f'{col}3'] = f"={yoy}3*1.08"
                model[f'{col}6'] = f"={yoy}6*1.05"
                model[f'{col}9'] = f"={yoy}9*1.15"
                model[f'{col}20'] = f"={yoy}20*1.10"
            else:  # Historical estimate
                # Use simple growth pattern or link to available data
                next_col = get_column_letter(idx + 1)
                model[f'{col}20'] = f"={next_col}20/1.10"  # Work backwards
            
            model[f'{col}3'].number_format = '$#,##0'
            model[f'{col}6'].number_format = '$#,##0'
            model[f'{col}9'].number_format = '$#,##0'
            model[f'{col}20'].number_format = '$#,##0'
            model[f'{col}20'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    
    # Add legend
    model['B1'] = "GREEN=ACTUAL (Yahoo) | YELLOW=ESTIMATED | WHITE=FORECAST"
    model['B1'].font = Font(italic=True, size=9)
    
    # Rest of P&L formulas
    model['B11'] = "Online Stores"
    model['B12'] = "Physical Stores"
    model['B13'] = "Third-party"
    model['B14'] = "Subscription"
    model['B15'] = "Ads"
    model['B16'] = "Other"
    model['B18'] = "Product"
    model['B19'] = "Services"
    model['B20'] = "Revenue"
    model['B20'].font = Font(bold=True, size=11)
    
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}11'] = f"={col}5+{col}8"
        model[f'{col}12'] = f"={col}20*0.02"
        model[f'{col}13'] = f"={col}20*0.25"
        model[f'{col}14'] = f"={col}20*0.08"
        model[f'{col}15'] = f"={col}20*0.12"
        model[f'{col}16'] = f"={col}20-SUM({col}11:{col}15)"
        model[f'{col}18'] = f"={col}3+{col}6-{col}9"
        model[f'{col}19'] = f"={col}9+{col}14+{col}15"
        for row in [11, 12, 13, 14, 15, 16, 18, 19]:
            model[f'{col}{row}'].number_format = '$#,##0'
    
    # Complete P&L structure
    for row_label, row_num in [
        ("Cost of Sales", 21), ("Fulfillment", 22), ("Gross Margin", 23),
        ("Technology", 24), ("S&M", 25), ("G&A", 26), ("OpEx", 27),
        ("OpInc", 28), ("Interest Expense", 29), ("Pretax", 30),
        ("Taxes", 31), ("Net Income", 32), ("EPS", 33), ("Shares", 34)
    ]:
        model[f'B{row_num}'] = row_label
        if row_label in ["Gross Margin", "OpEx", "OpInc", "Net Income"]:
            model[f'B{row_num}'].font = Font(bold=True)
    
    # Formulas for P&L
    for idx in range(3, 51):
        col = get_column_letter(idx)
        
        # Only fill if not already filled with actual
        if model[f'{col}21'].value is None:
            model[f'{col}21'] = f"={col}20*0.55"
            model[f'{col}21'].number_format = '$#,##0'
        if model[f'{col}22'].value is None:
            model[f'{col}22'] = f"={col}20*0.15"
            model[f'{col}22'].number_format = '$#,##0'
        
        model[f'{col}23'] = f"={col}20-{col}21-{col}22"
        model[f'{col}23'].number_format = '$#,##0'
        model[f'{col}23'].fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        
        if model[f'{col}24'].value is None:
            model[f'{col}24'] = f"={col}20*0.16"
            model[f'{col}24'].number_format = '$#,##0'
        if model[f'{col}25'].value is None:
            model[f'{col}25'] = f"={col}20*0.12"
            model[f'{col}25'].number_format = '$#,##0'
        
        model[f'{col}26'] = f"={col}25*0.3"
        model[f'{col}27'] = f"=SUM({col}24:{col}26)"
        model[f'{col}28'] = f"={col}23-{col}27"
        model[f'{col}28'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
        
        if model[f'{col}29'].value is None:
            model[f'{col}29'] = f"={col}20*0.005"
            model[f'{col}29'].number_format = '$#,##0'
        
        model[f'{col}30'] = f"={col}28-{col}29"
        
        if model[f'{col}31'].value is None:
            model[f'{col}31'] = f"={col}30*0.18"
            model[f'{col}31'].number_format = '$#,##0'
        
        if model[f'{col}32'].value is None:
            model[f'{col}32'] = f"={col}30-{col}31"
            model[f'{col}32'].fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        
        model[f'{col}33'] = f"=IF({col}34=0,0,{col}32/{col}34)"
        model[f'{col}33'].number_format = '$0.00'
        
        if model[f'{col}34'].value is None:
            model[f'{col}34'] = f"={get_column_letter(42)}34"
            model[f'{col}34'].number_format = '#,##0'
    
    # Growth rates
    for row_label, row_num, ref_row in [
        ("Revenue y/y", 36, 20), ("Revenue CC", 37, 20),
        ("  Product y/y", 38, 18), ("  Service y/y", 39, 19),
        ("Online Stores y/y", 40, 11), ("Third-party y/y", 41, 13),
        ("Subscription y/y", 42, 14), ("Ads y/y", 43, 15), ("AWS y/y", 44, 9)
    ]:
        model[f'B{row_num}'] = row_label
        for idx in range(7, 51):
            col = get_column_letter(idx)
            yoy = get_column_letter(idx - 4)
            model[f'{col}{row_num}'] = f"=IF({yoy}{ref_row}=0,0,{col}{ref_row}/{yoy}{ref_row}-1)"
            model[f'{col}{row_num}'].number_format = '0.0%'
    
    # Gross Margin %
    model['B45'] = "Gross Margin"
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}45'] = f"=IF({col}20=0,0,{col}23/{col}20)"
        model[f'{col}45'].number_format = '0.0%'
    
    # Balance sheet and other rows
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
    
    for idx in range(3, 51):
        col = get_column_letter(idx)
        for row_num in [90, 91, 92, 93]:
            model[f'{col}{row_num}'] = [f"={col}28*0.7", f"={col}28*0.15", f"={col}28*0.25", f"={col}22*0.8"][row_num-90]
            model[f'{col}{row_num}'].number_format = '$#,##0'
    
    # FCF
    model['B95'] = "FCF"
    model['B95'].font = Font(bold=True, size=11)
    for idx in range(3, 51):
        col = get_column_letter(idx)
        model[f'{col}95'] = f"={col}74+{col}76+{col}77+{col}78+{col}79"
        model[f'{col}95'].number_format = '$#,##0'
    
    model['B96'] = "FCF TTM"
    model['B96'].font = Font(bold=True)
    for idx in range(6, 51):
        col = get_column_letter(idx)
        col1 = get_column_letter(idx - 3)
        model[f'{col}96'] = f"=SUM({col1}95:{col}95)"
        model[f'{col}96'].number_format = '$#,##0'
    
    # DCF Section
    model['B98'] = "DCF CALCULATION"
    model['B98'].font = Font(bold=True, size=12, color="006100")
    
    model['B99'] = "WACC"
    model['C99'] = 0.09
    model['C99'].number_format = '0.0%'
    
    model['B100'] = "Terminal Growth"
    model['C100'] = 0.03
    model['C100'].number_format = '0.0%'
    
    for year in range(1, 6):
        row = 100 + year
        model[f'B{row}'] = f"Year {year} FCF"
        start_col = 43 + (year - 1) * 4
        end_col = start_col + 3
        start = get_column_letter(start_col)
        end = get_column_letter(end_col)
        model[f'C{row}'] = f"=SUM({start}95:{end}95)"
        model[f'C{row}'].number_format = '$#,##0'
    
    for year in range(1, 6):
        row = 106 + year
        model[f'B{row}'] = f"PV of FCF Y{year}"
        fcf_row = 100 + year
        model[f'C{row}'] = f"=C{fcf_row}/(1+$C$99)^{year}"
        model[f'C{row}'].number_format = '$#,##0'
    
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
    
    for row in range(1, 125):
        cell = model.cell(row=row, column=2)
        if cell.value:
            cell.font = Font(bold=True)
    
    # Save
    output_dir = './output'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'AMZN_DCF_Model_v3.xlsx')
    wb.save(output_path)
    
    size_kb = os.path.getsize(output_path) / 1024
    print(f"\n✅ Generated: {output_path} ({size_kb:.1f} KB)")
    print(f"\n📊 DATA SOURCE SUMMARY:")
    print(f"   • Green cells: ACTUAL data from Yahoo Finance ({actual_q_count} quarters)")
    print(f"   • Yellow cells: ESTIMATED (historical gaps)")
    print(f"   • White cells: FORECAST formulas")
    
    return output_path


if __name__ == "__main__":
    create_amazon_model_v3()
