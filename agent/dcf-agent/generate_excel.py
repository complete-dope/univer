#!/usr/bin/env python3
"""
Generate Excel Spreadsheets from DCF JSON Data

Creates actual .xlsx files with:
- Income Statement
- Balance Sheet
- Cash Flow
- DCF Model
- Formulas and formatting
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("Installing openpyxl...")
    os.system(f"{sys.executable} -m pip install openpyxl -q")
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter


def load_json_data(ticker: str) -> dict:
    """Load DCF data from JSON file"""
    data_path = f"./output/{ticker}_data.json"
    buffett_path = f"./output/{ticker}_buffett_valuation.json"
    
    data = {}
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            data = json.load(f)
    
    buffett = {}
    if os.path.exists(buffett_path):
        with open(buffett_path, 'r') as f:
            buffett = json.load(f)
    
    return data, buffett


def create_excel_workbook(ticker: str, output_dir: str = "./output"):
    """Create Excel workbook with DCF model"""
    
    data, buffett = load_json_ticker(ticker)
    
    if not data:
        print(f"❌ No data found for {ticker}")
        return None
    
    wb = openpyxl.Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # Create sheets
    create_summary_sheet(wb, ticker, data, buffett)
    create_income_statement_sheet(wb, data)
    create_balance_sheet_sheet(wb, data)
    create_cash_flow_sheet(wb, data)
    create_dcf_model_sheet(wb, data, buffett)
    
    # Save
    output_path = os.path.join(output_dir, f"{ticker}_DCF_Model.xlsx")
    wb.save(output_path)
    print(f"✅ Generated: {output_path}")
    
    return output_path


def create_summary_sheet(wb, ticker, data, buffett):
    """Create summary sheet with key metrics"""
    ws = wb.create_sheet("Summary", 0)
    
    # Title
    ws['A1'] = f"DCF Valuation Model - {ticker}"
    ws['A1'].font = Font(size=16, bold=True)
    ws.merge_cells('A1:D1')
    
    company_name = data.get('financial_data', {}).get('company_name', ticker)
    ws['A2'] = company_name
    ws['A2'].font = Font(size=12, bold=True)
    ws['A2'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
    ws.merge_cells('A2:D2')
    
    # Valuation Summary
    row = 4
    ws[f'A{row}'] = "VALUATION SUMMARY"
    ws[f'A{row}'].font = Font(bold=True, size=11)
    ws[f'A{row}'].fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    ws[f'A{row}'].font = Font(bold=True, color="FFFFFF")
    ws.merge_cells(f'A{row}:D{row}')
    
    row += 1
    
    # Get values
    if 'dcf_result' in data:
        dcf = data['dcf_result']
        current_price = dcf.get('current_price', 0)
        
        # Standard DCF
        ws[f'A{row}'] = "Standard DCF Value:"
        ws[f'B{row}'] = dcf.get('intrinsic_value_per_share', 0)
        ws[f'B{row}'].number_format = '$#,##0.00'
        row += 1
        
        ws[f'A{row}'] = "Current Price:"
        ws[f'B{row}'] = current_price
        ws[f'B{row}'].number_format = '$#,##0.00'
        row += 1
        
        ws[f'A{row}'] = "Margin of Safety (Std):"
        margin_std = (dcf.get('intrinsic_value_per_share', 0) - current_price) / current_price if current_price else 0
        ws[f'B{row}'] = margin_std
        ws[f'B{row}'].number_format = '0.0%'
        if margin_std > 0:
            ws[f'B{row}'].font = Font(color="00B050")
        else:
            ws[f'B{row}'].font = Font(color="FF0000")
        row += 2
    
    # Buffett Method
    if buffett and 'valuation' in buffett:
        val = buffett['valuation']
        
        ws[f'A{row}'] = "BUFFETT METHOD"
        ws[f'A{row}'].font = Font(bold=True, size=11)
        ws[f'A{row}'].fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
        ws[f'A{row}'].font = Font(bold=True, color="FFFFFF")
        ws.merge_cells(f'A{row}:D{row}')
        row += 1
        
        ws[f'A{row}'] = "Owner Earnings DCF:"
        ws[f'B{row}'] = val.get('buffett_dcf', 0)
        ws[f'B{row}'].number_format = '$#,##0.00'
        row += 1
        
        ws[f'A{row}'] = "EV/EBITDA Value:"
        ws[f'B{row}'] = val.get('ev_ebitda', 0)
        ws[f'B{row}'].number_format = '$#,##0.00'
        row += 1
        
        ws[f'A{row}'] = "Final Triangulated:"
        ws[f'B{row}'] = val.get('final_value', 0)
        ws[f'B{row}'].number_format = '$#,##0.00'
        ws[f'B{row}'].font = Font(bold=True, size=12)
        row += 1
        
        ws[f'A{row}'] = "Margin of Safety:"
        margin = val.get('margin_of_safety', 0)
        ws[f'B{row}'] = margin
        ws[f'B{row}'].number_format = '0.0%'
        if margin > 0:
            ws[f'B{row}'].font = Font(color="00B050", bold=True)
        else:
            ws[f'B{row}'].font = Font(color="FF0000", bold=True)
        row += 1
        
        ws[f'A{row}'] = "Verdict:"
        ws[f'B{row}'] = val.get('verdict', '')
        if 'UNDERVALUED' in val.get('verdict', ''):
            ws[f'B{row}'].font = Font(color="00B050", bold=True)
        elif 'OVERVALUED' in val.get('verdict', ''):
            ws[f'B{row}'].font = Font(color="FF0000", bold=True)
        row += 2
    
    # Key Metrics
    ws[f'A{row}'] = "KEY METRICS"
    ws[f'A{row}'].font = Font(bold=True, size=11)
    ws[f'A{row}'].fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    ws[f'A{row}'].font = Font(bold=True, color="FFFFFF")
    ws.merge_cells(f'A{row}:D{row}')
    row += 1
    
    if 'dcf_result' in data:
        dcf = data['dcf_result']
        ws[f'A{row}'] = "Enterprise Value:"
        ws[f'B{row}'] = dcf.get('enterprise_value', 0) / 1e9
        ws[f'B{row}'].number_format = '$#,##0.0"B"'
        row += 1
        
        ws[f'A{row}'] = "Equity Value:"
        ws[f'B{row}'] = dcf.get('equity_value', 0) / 1e9
        ws[f'B{row}'].number_format = '$#,##0.0"B"'
        row += 1
        
        ws[f'A{row}'] = "WACC:"
        ws[f'B{row}'] = dcf.get('wacc', 0)
        ws[f'B{row}'].number_format = '0.00%'
        row += 1
        
        ws[f'A{row}'] = "Terminal Growth:"
        ws[f'B{row}'] = dcf.get('terminal_growth_rate', 0)
        ws[f'B{row}'].number_format = '0.0%'
        row += 1
        
        ws[f'A{row}'] = "Shares Outstanding:"
        shares = dcf.get('shares_outstanding', 0)
        ws[f'B{row}'] = shares / 1e9 if shares > 1e9 else shares / 1e6
        ws[f'B{row}'].number_format = '#,##0.00"B"' if shares > 1e9 else '#,##0.00"M"'
        row += 1
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 15


def create_income_statement_sheet(wb, data):
    """Create income statement sheet"""
    ws = wb.create_sheet("Income Statement")
    
    ws['A1'] = "INCOME STATEMENT"
    ws['A1'].font = Font(size=14, bold=True)
    ws.merge_cells('A1:F1')
    
    # Headers
    headers = ['Year', 'Revenue', 'EBIT', 'Net Income', 'EBIT Margin', 'Net Margin']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal='center')
    
    # Data
    income_data = data.get('financial_data', {}).get('income_statements', {})
    years = sorted(income_data.keys(), reverse=True)
    
    for idx, year in enumerate(years[:15], start=4):  # Last 15 years
        inc = income_data[year]
        ws.cell(row=idx, column=1, value=year)
        ws.cell(row=idx, column=2, value=inc.get('revenue', 0)).number_format = '$#,##0'
        ws.cell(row=idx, column=3, value=inc.get('operating_income', 0)).number_format = '$#,##0'
        ws.cell(row=idx, column=4, value=inc.get('net_income', 0)).number_format = '$#,##0'
        ws.cell(row=idx, column=5, value=inc.get('operating_margin', 0)).number_format = '0.0%'
        ws.cell(row=idx, column=6, value=inc.get('net_margin', 0)).number_format = '0.0%'
    
    # Adjust columns
    for col in range(1, 7):
        ws.column_dimensions[get_column_letter(col)].width = 15


def create_balance_sheet_sheet(wb, data):
    """Create balance sheet"""
    ws = wb.create_sheet("Balance Sheet")
    
    ws['A1'] = "BALANCE SHEET"
    ws['A1'].font = Font(size=14, bold=True)
    ws.merge_cells('A1:F1')
    
    # Headers
    headers = ['Year', 'Cash', 'Total Assets', 'Total Debt', 'Equity', 'Working Capital']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal='center')
    
    # Data
    balance_data = data.get('financial_data', {}).get('balance_sheets', {})
    years = sorted(balance_data.keys(), reverse=True)
    
    for idx, year in enumerate(years[:15], start=4):
        bs = balance_data[year]
        ws.cell(row=idx, column=1, value=year)
        ws.cell(row=idx, column=2, value=bs.get('cash', 0)).number_format = '$#,##0'
        ws.cell(row=idx, column=3, value=bs.get('total_assets', 0)).number_format = '$#,##0'
        ws.cell(row=idx, column=4, value=bs.get('long_term_debt', 0) + bs.get('short_term_debt', 0)).number_format = '$#,##0'
        ws.cell(row=idx, column=5, value=bs.get('total_equity', 0)).number_format = '$#,##0'
        ws.cell(row=idx, column=6, value=bs.get('working_capital', 0)).number_format = '$#,##0'
    
    # Adjust columns
    for col in range(1, 7):
        ws.column_dimensions[get_column_letter(col)].width = 18


def create_cash_flow_sheet(wb, data):
    """Create cash flow statement"""
    ws = wb.create_sheet("Cash Flow")
    
    ws['A1'] = "CASH FLOW STATEMENT"
    ws['A1'].font = Font(size=14, bold=True)
    ws.merge_cells('A1:F1')
    
    # Headers
    headers = ['Year', 'Operating CF', 'CapEx', 'Free Cash Flow', 'D&A', 'FCF Margin']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal='center')
    
    # Data
    cf_data = data.get('financial_data', {}).get('cash_flows', {})
    years = sorted(cf_data.keys(), reverse=True)
    
    for idx, year in enumerate(years[:15], start=4):
        cf = cf_data[year]
        ocf = cf.get('operating_cash_flow', 0)
        capex = abs(cf.get('capex', 0))
        fcf = ocf - capex
        
        ws.cell(row=idx, column=1, value=year)
        ws.cell(row=idx, column=2, value=ocf).number_format = '$#,##0'
        ws.cell(row=idx, column=3, value=capex).number_format = '$#,##0'
        ws.cell(row=idx, column=4, value=fcf).number_format = '$#,##0'
        ws.cell(row=idx, column=5, value=cf.get('depreciation_amortization', 0)).number_format = '$#,##0'
        
        # Get revenue for FCF margin
        inc = data.get('financial_data', {}).get('income_statements', {}).get(year, {})
        revenue = inc.get('revenue', 0)
        fcf_margin = fcf / revenue if revenue else 0
        ws.cell(row=idx, column=6, value=fcf_margin).number_format = '0.0%'
    
    # Adjust columns
    for col in range(1, 7):
        ws.column_dimensions[get_column_letter(col)].width = 16


def create_dcf_model_sheet(wb, data, buffett):
    """Create DCF model sheet"""
    ws = wb.create_sheet("DCF Model")
    
    ws['A1'] = "DISCOUNTED CASH FLOW MODEL"
    ws['A1'].font = Font(size=14, bold=True)
    ws.merge_cells('A1:G1')
    
    row = 3
    
    # Assumptions
    ws[f'A{row}'] = "ASSUMPTIONS"
    ws[f'A{row}'].font = Font(bold=True, size=12)
    ws[f'A{row}'].fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
    ws[f'A{row}'].font = Font(bold=True, color="FFFFFF")
    ws.merge_cells(f'A{row}:G{row}')
    row += 1
    
    if 'dcf_result' in data:
        dcf = data['dcf_result']
        
        ws[f'A{row}'] = "Discount Rate (WACC):"
        ws[f'B{row}'] = dcf.get('wacc', 0)
        ws[f'B{row}'].number_format = '0.00%'
        row += 1
        
        ws[f'A{row}'] = "Terminal Growth Rate:"
        ws[f'B{row}'] = dcf.get('terminal_growth_rate', 0)
        ws[f'B{row}'].number_format = '0.0%'
        row += 2
    
    # DCF Projections
    ws[f'A{row}'] = "DCF PROJECTIONS"
    ws[f'A{row}'].font = Font(bold=True, size=12)
    ws[f'A{row}'].fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    ws[f'A{row}'].font = Font(bold=True, color="FFFFFF")
    ws.merge_cells(f'A{row}:G{row}')
    row += 1
    
    # Headers
    headers = ['Year', 'Revenue', 'EBIT', 'Tax', 'NOPAT', 'D&A', 'FCF']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        cell.alignment = Alignment(horizontal='center')
    row += 1
    
    # Projection data
    if 'dcf_result' in data and 'projections' in data['dcf_result']:
        projections = data['dcf_result']['projections']
        
        for proj in projections:
            ws.cell(row=row, column=1, value=f"Year {proj.get('year', 0)}")
            ws.cell(row=row, column=2, value=proj.get('revenue', 0)).number_format = '$#,##0'
            ws.cell(row=row, column=3, value=proj.get('ebit', 0)).number_format = '$#,##0'
            ws.cell(row=row, column=4, value=proj.get('tax_expense', 0)).number_format = '$#,##0'
            ws.cell(row=row, column=5, value=proj.get('nopat', 0)).number_format = '$#,##0'
            ws.cell(row=row, column=6, value=proj.get('depreciation', 0)).number_format = '$#,##0'
            ws.cell(row=row, column=7, value=proj.get('fcf', 0)).number_format = '$#,##0'
            row += 1
        
        # Terminal Value
        ws[f'A{row}'] = "Terminal Value"
        ws[f'A{row}'].font = Font(bold=True)
        ws.merge_cells(f'A{row}:F{row}')
        ws.cell(row=row, column=7, value=dcf.get('terminal_value', 0)).number_format = '$#,##0'
        ws.cell(row=row, column=7).font = Font(bold=True)
        row += 2
        
        # Summary
        ws[f'A{row}'] = "VALUATION SUMMARY"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        ws[f'A{row}'].fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
        ws[f'A{row}'].font = Font(bold=True, color="FFFFFF")
        ws.merge_cells(f'A{row}:G{row}')
        row += 1
        
        ws[f'A{row}'] = "Enterprise Value:"
        ws[f'B{row}'] = dcf.get('enterprise_value', 0)
        ws[f'B{row}'].number_format = '$#,##0'
        ws[f'B{row}'].font = Font(bold=True)
        row += 1
        
        ws[f'A{row}'] = "Add: Cash"
        ws[f'B{row}'] = dcf.get('cash', 0)
        ws[f'B{row}'].number_format = '$#,##0'
        row += 1
        
        ws[f'A{row}'] = "Less: Total Debt"
        ws[f'B{row}'] = dcf.get('total_debt', 0)
        ws[f'B{row}'].number_format = '$#,##0'
        row += 1
        
        ws[f'A{row}'] = "Equity Value:"
        ws[f'B{row}'] = dcf.get('equity_value', 0)
        ws[f'B{row}'].number_format = '$#,##0'
        ws[f'B{row}'].font = Font(bold=True, size=12)
        ws[f'B{row}'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        row += 1
        
        ws[f'A{row}'] = "Shares Outstanding:"
        ws[f'B{row}'] = dcf.get('shares_outstanding', 0)
        ws[f'B{row}'].number_format = '#,##0'
        row += 1
        
        ws[f'A{row}'] = "INTRINSIC VALUE PER SHARE:"
        ws[f'A{row}'].font = Font(bold=True, size=13)
        ws[f'B{row}'] = dcf.get('intrinsic_value_per_share', 0)
        ws[f'B{row}'].number_format = '$#,##0.00'
        ws[f'B{row}'].font = Font(bold=True, size=14, color="4472C4")
        ws[f'B{row}'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        row += 1
        
        ws[f'A{row}'] = "Current Market Price:"
        ws[f'B{row}'] = dcf.get('current_price', 0)
        ws[f'B{row}'].number_format = '$#,##0.00'
        row += 1
        
        ws[f'A{row}'] = "Margin of Safety:"
        margin = (dcf.get('intrinsic_value_per_share', 0) - dcf.get('current_price', 0)) / dcf.get('current_price', 1)
        ws[f'B{row}'] = margin
        ws[f'B{row}'].number_format = '0.0%'
        if margin > 0:
            ws[f'B{row}'].font = Font(bold=True, color="00B050")
        else:
            ws[f'B{row}'].font = Font(bold=True, color="FF0000")
    
    # Adjust columns
    for col in range(1, 8):
        ws.column_dimensions[get_column_letter(col)].width = 16


def generate_all_excel_files(companies=None):
    """Generate Excel files for all companies"""
    if companies is None:
        companies = ['AAPL', 'GOOGL', 'INFY', 'MSFT', 'NVDA']
    
    output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)
    
    print("="*60)
    print("GENERATING EXCEL SPREADSHEETS")
    print("="*60)
    print()
    
    generated = []
    for ticker in companies:
        try:
            path = create_excel_workbook(ticker, output_dir)
            if path:
                generated.append(path)
        except Exception as e:
            print(f"❌ Error generating {ticker}: {e}")
    
    print()
    print("="*60)
    print(f"Generated {len(generated)} Excel files")
    print("="*60)
    
    for path in generated:
        size = os.path.getsize(path) / 1024
        print(f"  📊 {path} ({size:.1f} KB)")
    
    return generated


def load_json_ticker(ticker):
    """Helper to load JSON data"""
    data_path = f"./output/{ticker}_data.json"
    buffett_path = f"./output/{ticker}_buffett_valuation.json"
    
    data = {}
    buffett = {}
    
    try:
        if os.path.exists(data_path):
            with open(data_path, 'r') as f:
                data = json.load(f)
    except Exception as e:
        print(f"Warning: Could not load {data_path}: {e}")
    
    try:
        if os.path.exists(buffett_path):
            with open(buffett_path, 'r') as f:
                buffett = json.load(f)
    except Exception as e:
        print(f"Warning: Could not load {buffett_path}: {e}")
    
    return data, buffett


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Excel DCF Models')
    parser.add_argument('tickers', nargs='*', help='Stock tickers to generate')
    parser.add_argument('--all', action='store_true', help='Generate for all available')
    
    args = parser.parse_args()
    
    if args.all or not args.tickers:
        # Find all available tickers
        output_files = os.listdir('./output')
        tickers = set()
        for f in output_files:
            if '_data.json' in f:
                tickers.add(f.replace('_data.json', ''))
        generate_all_excel_files(sorted(tickers))
    else:
        generate_all_excel_files(args.tickers)
