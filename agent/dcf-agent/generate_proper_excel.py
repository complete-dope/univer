#!/usr/bin/env python3
"""
Generate Proper Excel DCF Models (Matching Sample Format)

Structure based on AMZN.xlsx sample:
- 2 sheets: Main (summary) + Model (detailed quarterly)
- 40 quarters of historical + forecast data
- Revenue segmentation by geography/business line
- Operating metrics (S&M, G&A, Tech, etc.)
- Excel formulas linking cells (not static values)
- Growth rate calculations
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
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
    from openpyxl.utils import get_column_letter
    from openpyxl.formatting.rule import FormulaRule
except ImportError:
    print("Installing openpyxl...")
    os.system(f"{sys.executable} -m pip install openpyxl pandas -q")
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
    from openpyxl.utils import get_column_letter


def get_quarterly_data(ticker):
    """Get quarterly financial data from Yahoo Finance"""
    try:
        import yfinance as yf
        
        stock = yf.Ticker(ticker)
        
        # Get quarterly financials
        quarterly_income = stock.quarterly_income_stmt
        quarterly_balance = stock.quarterly_balance_sheet
        quarterly_cash = stock.quarterly_cashflow
        
        info = stock.info
        
        return {
            'income': quarterly_income,
            'balance': quarterly_balance,
            'cash': quarterly_cash,
            'info': info,
            'ticker': ticker
        }
    except Exception as e:
        print(f"Error fetching quarterly data for {ticker}: {e}")
        return None


def create_proper_excel(ticker, output_dir='./output'):
    """Create Excel file matching sample format"""
    
    print(f"\n{'='*60}")
    print(f"Generating Proper Excel Model - {ticker}")
    print(f"{'='*60}")
    
    # Get data
    data = get_quarterly_data(ticker)
    if not data:
        print(f"❌ Failed to get data for {ticker}")
        return None
    
    # Load existing JSON data for additional context
    json_data = {}
    json_path = f"{output_dir}/{ticker}_data.json"
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            json_data = json.load(f)
    
    # Create workbook
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    
    # Create sheets
    create_main_sheet(wb, ticker, data, json_data)
    create_model_sheet(wb, ticker, data, json_data)
    
    # Save
    output_path = os.path.join(output_dir, f"{ticker}_Proper_DCF.xlsx")
    wb.save(output_path)
    
    size_kb = os.path.getsize(output_path) / 1024
    print(f"✅ Generated: {output_path} ({size_kb:.1f} KB)")
    
    return output_path


def create_main_sheet(wb, ticker, data, json_data):
    """Create Main sheet with summary"""
    ws = wb.create_sheet("Main", 0)
    
    info = data.get('info', {})
    
    # Title section
    ws['J2'] = "Price"
    ws['K2'] = info.get('currentPrice', info.get('regularMarketPrice', 0))
    ws['K2'].number_format = '$#,##0.00'
    
    ws['J3'] = "Shares"
    shares = info.get('sharesOutstanding', 0) / 1e6  # in millions
    ws['K3'] = shares
    ws['K3'].number_format = '#,##0'
    ws['L3'] = "Q225"  # Placeholder quarter
    
    ws['J4'] = "MC"
    ws['K4'] = f"=K3*K2"
    ws['K4'].number_format = '$#,##0'
    
    ws['J5'] = "Cash"
    cash = info.get('totalCash', 0) / 1e6
    ws['K5'] = cash
    ws['K5'].number_format = '$#,##0'
    ws['L5'] = "Q225"
    
    ws['J6'] = "Debt"
    debt = info.get('totalDebt', 0) / 1e6
    ws['K6'] = debt
    ws['K6'].number_format = '$#,##0'
    ws['L6'] = "Q225"
    
    ws['J7'] = "EV"
    ws['K7'] = f"=K4-K5+K6"
    ws['K7'].number_format = '$#,##0'
    
    # Company info section (left side)
    company_name = info.get('longName', ticker)
    ws['B4'] = company_name
    ws['B4'].font = Font(size=12, bold=True)
    
    ws['B5'] = f"Ticker: {ticker}"
    ws['B6'] = f"Sector: {info.get('sector', 'N/A')}"
    ws['B7'] = f"Industry: {info.get('industry', 'N/A')}"
    ws['B8'] = f"CEO: {info.get('companyOfficers', [{}])[0].get('name', 'N/A') if info.get('companyOfficers') else 'N/A'}"
    
    # Formatting
    for row in range(2, 8):
        ws[f'J{row}'].font = Font(bold=True)
    
    # Column widths
    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 40
    ws.column_dimensions['J'].width = 12
    ws.column_dimensions['K'].width = 15
    ws.column_dimensions['L'].width = 8


def create_model_sheet(wb, ticker, data, json_data):
    """Create Model sheet matching sample format (Main + detailed quarterly model)"""
    ws = wb.create_sheet("Model")
    
    income = data.get('income')
    balance = data.get('balance')
    cash = data.get('cash')
    info = data.get('info', {})
    
    # Get quarters (columns) - Yahoo provides up to ~32 quarters
    if income is not None and not income.empty:
        quarters = list(income.columns)[:40]  # Max 40 quarters
    else:
        quarters = []
    
    total_cols = max(len(quarters) + 8, 45)  # Ensure minimum columns for forecasts
    
    # Row 1: Reference to Main sheet
    ws['A1'] = "Main"
    
    # Row 2: Headers (Quarters + Yearly forecast columns)
    ws['B2'] = None
    
    # Add quarter headers
    for idx, quarter in enumerate(quarters, start=3):
        col_letter = get_column_letter(idx)
        
        # Convert datetime to quarter format
        if hasattr(quarter, 'strftime'):
            year = quarter.year % 100
            month = quarter.month
            q = (month - 1) // 3 + 1
            quarter_str = f"Q{q}{year:02d}"
        else:
            quarter_str = str(quarter)[:6]
        
        ws[f'{col_letter}2'] = quarter_str
        ws[f'{col_letter}2'].alignment = Alignment(horizontal='center')
    
    # Add forecast quarter headers (with formulas)
    forecast_start = len(quarters) + 3
    for idx in range(forecast_start, min(forecast_start + 8, 43)):
        col_letter = get_column_letter(idx)
        prev_col = get_column_letter(idx - 1)
        ws[f'{col_letter}2'] = f"=+{prev_col}2+1"
        ws[f'{col_letter}2'].alignment = Alignment(horizontal='center')
    
    # Add yearly columns at the end
    yearly_start = max(43, len(quarters) + 12)
    for year_idx in range(6):  # 6 forecast years
        col_idx = yearly_start + year_idx
        col_letter = get_column_letter(col_idx)
        if year_idx == 0:
            base_year = datetime.now().year
            ws[f'{col_letter}2'] = base_year
        else:
            prev_col = get_column_letter(col_idx - 1)
            ws[f'{col_letter}2'] = f"=+{prev_col}2+1"
    
    # Row 3: Revenue (Total)
    ws['B3'] = "Revenue"
    ws['B3'].font = Font(bold=True)
    
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                if 'Total Revenue' in income.index:
                    rev = income.loc['Total Revenue', quarter]
                elif 'Revenue' in income.index:
                    rev = income.loc['Revenue', quarter]
                else:
                    rev = None
                
                if pd.notna(rev):
                    ws[f'{col_letter}3'] = rev / 1e6  # Convert to millions
                    ws[f'{col_letter}3'].number_format = '$#,##0'
            except:
                pass
    
    # Add forecast formulas for revenue
    for idx in range(len(quarters) + 3, min(len(quarters) + 12, 43)):
        col_letter = get_column_letter(idx)
        # Use previous quarter with growth assumption
        prev_col = get_column_letter(idx - 1)
        # Growth formula (conservative 5% QoQ or use y/y if available)
        if idx >= len(quarters) + 7:  # Far forecast - use y/y growth
            yoy_col = get_column_letter(idx - 4)
            ws[f'{col_letter}3'] = f"=+{yoy_col}3*1.05"
        else:
            ws[f'{col_letter}3'] = f"=+{prev_col}3*1.02"  # Near forecast - 2% QoQ
        ws[f'{col_letter}3'].number_format = '$#,##0'
    
    # Row 20: Total Revenue (consolidated line - links to row 3)
    ws['B20'] = "Revenue"
    ws['B20'].font = Font(bold=True, size=11)
    
    for idx in range(3, min(len(quarters) + 12, 45)):
        col_letter = get_column_letter(idx)
        ws[f'{col_letter}20'] = f"=+{col_letter}3"
        ws[f'{col_letter}20'].number_format = '$#,##0'
        ws[f'{col_letter}20'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
    
    # Row 21: Cost of Sales
    ws['B21'] = "Cost of Sales"
    
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                cost = None
                if 'Cost Of Revenue' in income.index:
                    cost = income.loc['Cost Of Revenue', quarter]
                elif 'Cost of Revenue' in income.index:
                    cost = income.loc['Cost of Revenue', quarter]
                
                if pd.notna(cost):
                    ws[f'{col_letter}21'] = abs(cost) / 1e6
                    ws[f'{col_letter}21'].number_format = '$#,##0'
            except:
                pass
    
    # Forecast for COGS (as % of revenue)
    for idx in range(len(quarters) + 3, min(len(quarters) + 12, 43)):
        col_letter = get_column_letter(idx)
        ws[f'{col_letter}21'] = f"=+{col_letter}20*0.55"  # 55% COGS ratio
        ws[f'{col_letter}21'].number_format = '$#,##0'
    
    # Row 22: Gross Margin
    ws['B22'] = "Gross Margin"
    ws['B22'].font = Font(bold=True)
    
    for idx in range(3, min(len(quarters) + 12, 45)):
        col_letter = get_column_letter(idx)
        ws[f'{col_letter}22'] = f"=+{col_letter}20-{col_letter}21"
        ws[f'{col_letter}22'].number_format = '$#,##0'
        ws[f'{col_letter}22'].fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    # Row 24: Technology / R&D
    ws['B24'] = "Technology"
    
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                rd = None
                if 'Research Development' in income.index:
                    rd = income.loc['Research Development', quarter]
                elif 'Research & Development' in income.index:
                    rd = income.loc['Research & Development', quarter]
                
                if pd.notna(rd):
                    ws[f'{col_letter}24'] = abs(rd) / 1e6
                    ws[f'{col_letter}24'].number_format = '$#,##0'
            except:
                pass
    
    # Forecast R&D (as % of revenue)
    for idx in range(len(quarters) + 3, min(len(quarters) + 12, 43)):
        col_letter = get_column_letter(idx)
        ws[f'{col_letter}24'] = f"=+{col_letter}20*0.08"  # 8% R&D ratio
        ws[f'{col_letter}24'].number_format = '$#,##0'
    
    # Row 25: S&M (Sales & Marketing)
    ws['B25'] = "S&M"
    
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                if 'Selling General Administrative' in income.index:
                    sga = income.loc['Selling General Administrative', quarter]
                    if pd.notna(sga):
                        ws[f'{col_letter}25'] = abs(sga) / 1e6
                        ws[f'{col_letter}25'].number_format = '$#,##0'
            except:
                pass
    
    # Forecast S&M
    for idx in range(len(quarters) + 3, min(len(quarters) + 12, 43)):
        col_letter = get_column_letter(idx)
        ws[f'{col_letter}25'] = f"=+{col_letter}20*0.12"  # 12% S&M ratio
        ws[f'{col_letter}25'].number_format = '$#,##0'
    
    # Row 26: G&A (General & Administrative - subset of S&M)
    ws['B26'] = "G&A"
    
    for idx in range(3, min(len(quarters) + 12, 45)):
        col_letter = get_column_letter(idx)
        # G&A is typically ~30% of total SG&A
        ws[f'{col_letter}26'] = f"=+{col_letter}25*0.3"
        ws[f'{col_letter}26'].number_format = '$#,##0'
    
    # Row 27: Total OpEx
    ws['B27'] = "OpEx"
    ws['B27'].font = Font(bold=True)
    
    for idx in range(3, min(len(quarters) + 12, 45)):
        col_letter = get_column_letter(idx)
        ws[f'{col_letter}27'] = f"=+{col_letter}24+{col_letter}25"
        ws[f'{col_letter}27'].number_format = '$#,##0'
    
    # Row 28: Operating Income
    ws['B28'] = "OpInc"
    ws['B28'].font = Font(bold=True)
    
    for idx in range(3, min(len(quarters) + 12, 45)):
        col_letter = get_column_letter(idx)
        ws[f'{col_letter}28'] = f"=+{col_letter}22-{col_letter}27"
        ws[f'{col_letter}28'].number_format = '$#,##0'
        ws[f'{col_letter}28'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
    
    # Row 29: Interest Expense
    ws['B29'] = "Interest Expense"
    
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                if 'Interest Expense' in income.index:
                    interest = income.loc['Interest Expense', quarter]
                    if pd.notna(interest):
                        ws[f'{col_letter}29'] = abs(interest) / 1e6
                        ws[f'{col_letter}29'].number_format = '$#,##0'
            except:
                pass
    
    # Forecast interest (estimate)
    for idx in range(len(quarters) + 3, min(len(quarters) + 12, 43)):
        col_letter = get_column_letter(idx)
        ws[f'{col_letter}29'] = f"=+{col_letter}20*0.005"  # 0.5% of revenue
        ws[f'{col_letter}29'].number_format = '$#,##0'
    
    # Row 30: Pretax Income
    ws['B30'] = "Pretax"
    ws['B30'].font = Font(bold=True)
    
    for idx in range(3, min(len(quarters) + 12, 45)):
        col_letter = get_column_letter(idx)
        ws[f'{col_letter}30'] = f"=+{col_letter}28-{col_letter}29"
        ws[f'{col_letter}30'].number_format = '$#,##0'
    
    # Row 31: Taxes
    ws['B31'] = "Taxes"
    
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                if 'Tax Provision' in income.index:
                    tax = income.loc['Tax Provision', quarter]
                    if pd.notna(tax):
                        ws[f'{col_letter}31'] = abs(tax) / 1e6
                        ws[f'{col_letter}31'].number_format = '$#,##0'
            except:
                pass
    
    # Forecast taxes (at 25% rate)
    for idx in range(len(quarters) + 3, min(len(quarters) + 12, 43)):
        col_letter = get_column_letter(idx)
        ws[f'{col_letter}31'] = f"=+{col_letter}30*0.25"
        ws[f'{col_letter}31'].number_format = '$#,##0'
    
    # Row 32: Net Income
    ws['B32'] = "Net Income"
    ws['B32'].font = Font(bold=True)
    
    for idx in range(3, min(len(quarters) + 12, 45)):
        col_letter = get_column_letter(idx)
        ws[f'{col_letter}32'] = f"=+{col_letter}30-{col_letter}31"
        ws[f'{col_letter}32'].number_format = '$#,##0'
        ws[f'{col_letter}32'].fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    # Row 33: EPS
    ws['B33'] = "EPS"
    
    for idx in range(3, min(len(quarters) + 12, 45)):
        col_letter = get_column_letter(idx)
        ws[f'{col_letter}33'] = f"=IF({col_letter}34=0,0,+{col_letter}32/{col_letter}34)"
        ws[f'{col_letter}33'].number_format = '$0.00'
    
    # Row 34: Shares (Basic Average)
    ws['B34'] = "Shares"
    
    if income is not None and not income.empty:
        for idx, quarter in enumerate(quarters, start=3):
            col_letter = get_column_letter(idx)
            try:
                shares_col = None
                if 'Basic Average Shares' in income.index:
                    shares_col = 'Basic Average Shares'
                elif 'Basic Shares Outstanding' in income.index:
                    shares_col = 'Basic Shares Outstanding'
                elif 'Average Diluted Earnings Per Share' in income.index:
                    # Derive from EPS
                    pass
                
                if shares_col:
                    shares = income.loc[shares_col, quarter]
                    if pd.notna(shares):
                        ws[f'{col_letter}34'] = shares / 1e6
                        ws[f'{col_letter}34'].number_format = '#,##0'
            except:
                pass
    
    # Use latest shares for forecasts
    if quarters:
        latest_shares = None
        try:
            for col in ['Basic Average Shares', 'Basic Shares Outstanding']:
                if col in income.index:
                    val = income.loc[col, quarters[-1]]
                    if pd.notna(val):
                        latest_shares = val / 1e6
                        break
        except:
            pass
        
        if latest_shares:
            for idx in range(len(quarters) + 3, min(len(quarters) + 12, 45)):
                col_letter = get_column_letter(idx)
                ws[f'{col_letter}34'] = latest_shares
                ws[f'{col_letter}34'].number_format = '#,##0'
    
    # Row 36: Revenue y/y growth
    ws['B36'] = "Revenue y/y"
    ws['B36'].font = Font(bold=True, italic=True)
    
    for idx in range(7, min(len(quarters) + 12, 45)):  # Start from 7th quarter for y/y
        col_letter = get_column_letter(idx)
        prev_year_col = get_column_letter(idx - 4)
        ws[f'{col_letter}36'] = f"=IF({prev_year_col}20=0,0,+{col_letter}20/{prev_year_col}20-1)"
        ws[f'{col_letter}36'].number_format = '0.0%'
    
    # Add more growth metrics
    ws['B37'] = "OpInc Margin"
    for idx in range(3, min(len(quarters) + 12, 45)):
        col_letter = get_column_letter(idx)
        ws[f'{col_letter}37'] = f"=IF({col_letter}20=0,0,+{col_letter}28/{col_letter}20)"
        ws[f'{col_letter}37'].number_format = '0.0%'
    
    ws['B38'] = "Net Margin"
    for idx in range(3, min(len(quarters) + 12, 45)):
        col_letter = get_column_letter(idx)
        ws[f'{col_letter}38'] = f"=IF({col_letter}20=0,0,+{col_letter}32/{col_letter}20)"
        ws[f'{col_letter}38'].number_format = '0.0%'
    
    # Formatting
    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 22
    
    # Set width for data columns
    for col_idx in range(3, min(total_cols + 1, 60)):
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = 10
    
    # Bold all row labels
    for row in range(1, 45):
        cell = ws.cell(row=row, column=2)
        if cell.value:
            cell.font = Font(bold=True)


def create_empty_model_structure(ws, ticker):
    """Create empty model structure when data unavailable"""
    ws['A1'] = "Main"
    ws['B2'] = "Model"
    ws['B3'] = "Revenue"
    ws['B20'] = "Revenue"
    ws['B21'] = "Cost of Sales"
    ws['B22'] = "Gross Margin"
    ws['B24'] = "Technology"
    ws['B25'] = "S&M"
    ws['B26'] = "G&A"
    ws['B27'] = "OpEx"
    ws['B28'] = "OpInc"
    ws['B29'] = "Interest Expense"
    ws['B30'] = "Pretax"
    ws['B31'] = "Taxes"
    ws['B32'] = "Net Income"
    ws['B33'] = "EPS"
    ws['B34'] = "Shares"
    
    for row in range(1, 35):
        ws.cell(row=row, column=2).font = Font(bold=True)


def generate_all_proper_excel():
    """Generate proper Excel for all available companies"""
    
    # Find all companies with JSON data
    output_files = os.listdir('./output')
    tickers = set()
    for f in output_files:
        if '_data.json' in f:
            tickers.add(f.replace('_data.json', ''))
    
    print(f"\n{'='*60}")
    print(f"GENERATING PROPER EXCEL MODELS")
    print(f"{'='*60}")
    print(f"Found {len(tickers)} companies: {sorted(tickers)}")
    
    generated = []
    for ticker in sorted(tickers):
        try:
            path = create_proper_excel(ticker)
            if path:
                generated.append(path)
        except Exception as e:
            print(f"❌ Error with {ticker}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"Generated {len(generated)} Excel files")
    print(f"{'='*60}")
    
    return generated


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Proper Excel DCF Models')
    parser.add_argument('tickers', nargs='*', help='Stock tickers')
    parser.add_argument('--all', action='store_true', help='Generate for all available')
    
    args = parser.parse_args()
    
    if args.all or not args.tickers:
        generate_all_proper_excel()
    else:
        for ticker in args.tickers:
            create_proper_excel(ticker)
