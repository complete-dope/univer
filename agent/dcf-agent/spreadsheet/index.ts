/**
 * DCF Spreadsheet Generator using Univer Facade API
 * 
 * Creates single-sheet DCF model with all financial statements
 * and projections laid out in a flat structure.
 */

import { createUniver, LocaleType, IWorkbookData, IWorksheetData } from '@univerjs/presets';
import { UniverSheetsNodeCorePreset } from '@univerjs/preset-sheets-node-core';
import * as fs from 'fs';
import * as path from 'path';

// Import types from our models
interface FinancialData {
  ticker: string;
  company_name: string;
  income_statements: Record<string, any>;
  balance_sheets: Record<string, any>;
  cash_flows: Record<string, any>;
  current_price: number;
  shares_outstanding: number;
  beta: number;
}

interface DCFProjection {
  year: number;
  revenue: number;
  revenue_growth: number;
  ebit: number;
  ebit_margin: number;
  tax_expense: number;
  nopat: number;
  depreciation: number;
  capex: number;
  working_capital_change: number;
  fcf: number;
  discount_factor: number;
  pv_fcf: number;
}

interface DCFResult {
  ticker: string;
  projections: DCFProjection[];
  terminal_year_fcf: number;
  terminal_growth_rate: number;
  terminal_value: number;
  pv_terminal_value: number;
  sum_pv_fcf: number;
  enterprise_value: number;
  cash: number;
  total_debt: number;
  equity_value: number;
  shares_outstanding: number;
  intrinsic_value_per_share: number;
  current_price: number;
  margin_of_safety: number;
  verdict: string;
  wacc: number;
  risk_free_rate: number;
  beta: number;
  market_premium: number;
  cost_of_equity: number;
  cost_of_debt: number;
  tax_rate: number;
  debt_weight: number;
  equity_weight: number;
}

interface Assumptions {
  revenue_growth_y1_3: number;
  revenue_growth_y4_7: number;
  revenue_growth_y8_10: number;
  terminal_growth_rate: number;
  ebit_margin_target: number;
  tax_rate: number;
  dna_pct_of_revenue: number;
  capex_pct_of_revenue: number;
  nwc_pct_of_revenue: number;
  risk_free_rate: number;
  market_risk_premium: number;
  cost_of_debt: number;
  target_debt_ratio: number;
}

// Constants
const HISTORICAL_YEARS = 15;
const FORECAST_YEARS = 10;
const LONG_TERM_YEARS = 100;
const TOTAL_YEARS = HISTORICAL_YEARS + 1 + FORECAST_YEARS + LONG_TERM_YEARS;

// Row definitions
const ROWS = {
  // Income Statement (0-19)
  INCOME_HEADER: 0,
  REVENUE: 1,
  COGS: 2,
  GROSS_PROFIT: 3,
  GROSS_MARGIN: 4,
  OPERATING_EXPENSES: 6,
  EBIT: 7,
  EBIT_MARGIN: 8,
  DNA: 10,
  EBITDA: 11,
  INTEREST_EXPENSE: 13,
  TAX_EXPENSE: 14,
  NET_INCOME: 15,

  // Balance Sheet (20-49)
  BALANCE_HEADER: 20,
  CASH: 21,
  ACCOUNTS_RECEIVABLE: 22,
  INVENTORY: 23,
  OTHER_CURRENT_ASSETS: 24,
  TOTAL_CURRENT_ASSETS: 25,
  PPE: 27,
  GOODWILL: 28,
  INTANGIBLES: 29,
  OTHER_LT_ASSETS: 30,
  TOTAL_ASSETS: 31,
  ACCOUNTS_PAYABLE: 33,
  SHORT_TERM_DEBT: 34,
  OTHER_CURRENT_LIABILITIES: 35,
  TOTAL_CURRENT_LIABILITIES: 36,
  LONG_TERM_DEBT: 38,
  OTHER_LT_LIABILITIES: 39,
  TOTAL_LIABILITIES: 40,
  COMMON_STOCK: 42,
  RETAINED_EARNINGS: 43,
  TOTAL_EQUITY: 44,
  TOTAL_L_PLUS_E: 46,

  // Cash Flow (50-69)
  CASHFLOW_HEADER: 50,
  CF_NET_INCOME: 51,
  CF_DNA: 52,
  CF_SBC: 53,
  WC_CHANGE: 54,
  OCF: 55,
  CAPEX: 57,
  ACQUISITIONS: 58,
  ICF: 59,
  DEBT_CHANGE: 61,
  EQUITY_CHANGE: 62,
  DIVIDENDS: 63,
  FCF_FINANCING: 64,
  FCF: 66,

  // Key Metrics (70-79)
  METRICS_HEADER: 70,
  REVENUE_GROWTH: 71,
  EBIT_MARGIN_METRIC: 72,
  NET_MARGIN: 73,
  FCF_MARGIN: 74,
  ROIC: 75,
  ROE: 76,
  DEBT_EQUITY: 77,
  CURRENT_RATIO: 78,

  // Assumptions (80-89)
  ASSUMPTIONS_HEADER: 80,
  ASS_REVENUE_GROWTH_Y1_3: 81,
  ASS_REVENUE_GROWTH_Y4_7: 82,
  ASS_REVENUE_GROWTH_Y8_10: 83,
  ASS_EBIT_MARGIN: 84,
  ASS_TAX_RATE: 85,
  ASS_DNA_PCT: 86,
  ASS_CAPEX_PCT: 87,
  ASS_NWC_PCT: 88,
  ASS_TERMINAL_GROWTH: 89,

  // WACC (90-99)
  WACC_HEADER: 90,
  RISK_FREE_RATE: 91,
  BETA: 92,
  MARKET_PREMIUM: 93,
  COST_OF_EQUITY: 94,
  COST_OF_DEBT: 95,
  TAX_RATE_WACC: 96,
  DEBT_WEIGHT: 97,
  EQUITY_WEIGHT: 98,
  WACC: 99,

  // DCF Valuation (100+)
  DCF_HEADER: 100,
  DCF_YEAR: 101,
  DCF_FCF: 102,
  DCF_DISCOUNT_FACTOR: 103,
  DCF_PV_FCF: 104,
  TERMINAL_FCF: 106,
  TERMINAL_GROWTH: 107,
  TERMINAL_VALUE: 108,
  PV_TERMINAL: 109,
  ENTERPRISE_VALUE: 111,
  ADD_CASH: 112,
  LESS_DEBT: 113,
  EQUITY_VALUE: 114,
  SHARES_OUTSTANDING: 115,
  INTRINSIC_VALUE: 116,
  CURRENT_PRICE: 118,
  MARGIN_OF_SAFETY: 119,
  VALUATION_VERDICT: 120,

  // Sensitivity (125+)
  SENSITIVITY_HEADER_1: 125,
  SENSITIVITY_WACC_GROWTH: 126,
  SENSITIVITY_HEADER_2: 135,
  SENSITIVITY_CAGR_MARGIN: 136,
};

/**
 * Generate Excel column letter from index (0 = A, 1 = B, etc.)
 */
function getColumnLetter(index: number): string {
  let result = '';
  let num = index;
  while (num >= 0) {
    result = String.fromCharCode(65 + (num % 26)) + result;
    num = Math.floor(num / 26) - 1;
  }
  return result || 'A';
}

/**
 * Create cell data with value or formula
 */
function cell(value?: number | string, formula?: string): any {
  if (formula) {
    return { f: formula };
  }
  if (typeof value === 'number') {
    return { v: value };
  }
  if (typeof value === 'string') {
    return { v: value };
  }
  return { v: '' };
}

/**
 * Generate the single-sheet DCF workbook
 */
export async function generateDCFWorkbook(
  financialData: FinancialData,
  dcfResult: DCFResult,
  assumptions: Assumptions
): Promise<IWorkbookData> {
  const { univerAPI } = createUniver({
    locale: LocaleType.EN_US,
    presets: [UniverSheetsNodeCorePreset()],
  });

  // Build column headers
  const years: string[] = [];
  const currentYear = new Date().getFullYear();
  
  // Historical years (15 years)
  for (let i = HISTORICAL_YEARS; i > 0; i--) {
    years.push((currentYear - i).toString());
  }
  // Current year
  years.push(currentYear.toString());
  // Forecast years (10 years)
  for (let i = 1; i <= FORECAST_YEARS; i++) {
    years.push((currentYear + i).toString());
  }
  // Long-term years (100 years)
  for (let i = FORECAST_YEARS + 1; i <= FORECAST_YEARS + LONG_TERM_YEARS; i++) {
    years.push((currentYear + i).toString());
  }

  // Create worksheet data
  const rowData: Record<number, Record<number, any>> = {};

  // Helper to set cell
  const setCell = (row: number, col: number, value?: number | string, formula?: string) => {
    if (!rowData[row]) rowData[row] = {};
    rowData[row][col] = cell(value, formula);
  };

  // === INCOME STATEMENT SECTION ===
  setCell(ROWS.INCOME_HEADER, 0, 'INCOME STATEMENT');
  setCell(ROWS.REVENUE, 0, 'Revenue');
  setCell(ROWS.COGS, 0, 'COGS');
  setCell(ROWS.GROSS_PROFIT, 0, 'Gross Profit');
  setCell(ROWS.GROSS_MARGIN, 0, 'Gross Margin %');
  setCell(ROWS.OPERATING_EXPENSES, 0, 'Operating Expenses');
  setCell(ROWS.EBIT, 0, 'Operating Income (EBIT)');
  setCell(ROWS.EBIT_MARGIN, 0, 'EBIT Margin %');
  setCell(ROWS.DNA, 0, 'Depreciation & Amortization');
  setCell(ROWS.EBITDA, 0, 'EBITDA');
  setCell(ROWS.INTEREST_EXPENSE, 0, 'Interest Expense');
  setCell(ROWS.TAX_EXPENSE, 0, 'Tax Expense');
  setCell(ROWS.NET_INCOME, 0, 'Net Income');

  // === BALANCE SHEET SECTION ===
  setCell(ROWS.BALANCE_HEADER, 0, 'BALANCE SHEET');
  setCell(ROWS.CASH, 0, 'Cash & Equivalents');
  setCell(ROWS.ACCOUNTS_RECEIVABLE, 0, 'Accounts Receivable');
  setCell(ROWS.INVENTORY, 0, 'Inventory');
  setCell(ROWS.OTHER_CURRENT_ASSETS, 0, 'Other Current Assets');
  setCell(ROWS.TOTAL_CURRENT_ASSETS, 0, 'Total Current Assets');
  setCell(ROWS.PPE, 0, 'PP&E');
  setCell(ROWS.GOODWILL, 0, 'Goodwill');
  setCell(ROWS.INTANGIBLES, 0, 'Intangibles');
  setCell(ROWS.OTHER_LT_ASSETS, 0, 'Other Long-term Assets');
  setCell(ROWS.TOTAL_ASSETS, 0, 'Total Assets');
  setCell(ROWS.ACCOUNTS_PAYABLE, 0, 'Accounts Payable');
  setCell(ROWS.SHORT_TERM_DEBT, 0, 'Short-term Debt');
  setCell(ROWS.OTHER_CURRENT_LIABILITIES, 0, 'Other Current Liabilities');
  setCell(ROWS.TOTAL_CURRENT_LIABILITIES, 0, 'Total Current Liabilities');
  setCell(ROWS.LONG_TERM_DEBT, 0, 'Long-term Debt');
  setCell(ROWS.OTHER_LT_LIABILITIES, 0, 'Other Long-term Liabilities');
  setCell(ROWS.TOTAL_LIABILITIES, 0, 'Total Liabilities');
  setCell(ROWS.COMMON_STOCK, 0, 'Common Stock');
  setCell(ROWS.RETAINED_EARNINGS, 0, 'Retained Earnings');
  setCell(ROWS.TOTAL_EQUITY, 0, 'Total Equity');
  setCell(ROWS.TOTAL_L_PLUS_E, 0, 'Total Liabilities + Equity');

  // === CASH FLOW SECTION ===
  setCell(ROWS.CASHFLOW_HEADER, 0, 'CASH FLOW STATEMENT');
  setCell(ROWS.CF_NET_INCOME, 0, 'Net Income');
  setCell(ROWS.CF_DNA, 0, 'Add: D&A');
  setCell(ROWS.CF_SBC, 0, 'Add: Stock-Based Comp');
  setCell(ROWS.WC_CHANGE, 0, 'Change in Working Capital');
  setCell(ROWS.OCF, 0, 'Operating Cash Flow');
  setCell(ROWS.CAPEX, 0, 'CapEx');
  setCell(ROWS.ACQUISITIONS, 0, 'Acquisitions');
  setCell(ROWS.ICF, 0, 'Investing Cash Flow');
  setCell(ROWS.DEBT_CHANGE, 0, 'Debt Issued/(Retired)');
  setCell(ROWS.EQUITY_CHANGE, 0, 'Stock Issued/(Bought)');
  setCell(ROWS.DIVIDENDS, 0, 'Dividends Paid');
  setCell(ROWS.FCF_FINANCING, 0, 'Financing Cash Flow');
  setCell(ROWS.FCF, 0, 'Free Cash Flow');

  // === KEY METRICS SECTION ===
  setCell(ROWS.METRICS_HEADER, 0, 'KEY METRICS');
  setCell(ROWS.REVENUE_GROWTH, 0, 'Revenue Growth %');
  setCell(ROWS.EBIT_MARGIN_METRIC, 0, 'EBIT Margin %');
  setCell(ROWS.NET_MARGIN, 0, 'Net Margin %');
  setCell(ROWS.FCF_MARGIN, 0, 'FCF Margin %');
  setCell(ROWS.ROIC, 0, 'ROIC');
  setCell(ROWS.ROE, 0, 'ROE');
  setCell(ROWS.DEBT_EQUITY, 0, 'Debt / Equity');
  setCell(ROWS.CURRENT_RATIO, 0, 'Current Ratio');

  // === ASSUMPTIONS SECTION ===
  setCell(ROWS.ASSUMPTIONS_HEADER, 0, 'ASSUMPTIONS');
  setCell(ROWS.ASS_REVENUE_GROWTH_Y1_3, 0, 'Revenue Growth Y1-3');
  setCell(ROWS.ASS_REVENUE_GROWTH_Y4_7, 0, 'Revenue Growth Y4-7');
  setCell(ROWS.ASS_REVENUE_GROWTH_Y8_10, 0, 'Revenue Growth Y8-10');
  setCell(ROWS.ASS_EBIT_MARGIN, 0, 'Target EBIT Margin');
  setCell(ROWS.ASS_TAX_RATE, 0, 'Tax Rate');
  setCell(ROWS.ASS_DNA_PCT, 0, 'D&A % of Revenue');
  setCell(ROWS.ASS_CAPEX_PCT, 0, 'CapEx % of Revenue');
  setCell(ROWS.ASS_NWC_PCT, 0, 'NWC % of Revenue');
  setCell(ROWS.ASS_TERMINAL_GROWTH, 0, 'Terminal Growth Rate');

  // Set assumption values in column B
  setCell(ROWS.ASS_REVENUE_GROWTH_Y1_3, 1, assumptions.revenue_growth_y1_3);
  setCell(ROWS.ASS_REVENUE_GROWTH_Y4_7, 1, assumptions.revenue_growth_y4_7);
  setCell(ROWS.ASS_REVENUE_GROWTH_Y8_10, 1, assumptions.revenue_growth_y8_10);
  setCell(ROWS.ASS_EBIT_MARGIN, 1, assumptions.ebit_margin_target);
  setCell(ROWS.ASS_TAX_RATE, 1, assumptions.tax_rate);
  setCell(ROWS.ASS_DNA_PCT, 1, assumptions.dna_pct_of_revenue);
  setCell(ROWS.ASS_CAPEX_PCT, 1, assumptions.capex_pct_of_revenue);
  setCell(ROWS.ASS_NWC_PCT, 1, assumptions.nwc_pct_of_revenue);
  setCell(ROWS.ASS_TERMINAL_GROWTH, 1, assumptions.terminal_growth_rate);

  // === WACC SECTION ===
  setCell(ROWS.WACC_HEADER, 0, 'WACC CALCULATION');
  setCell(ROWS.RISK_FREE_RATE, 0, 'Risk-free Rate');
  setCell(ROWS.BETA, 0, 'Beta');
  setCell(ROWS.MARKET_PREMIUM, 0, 'Market Risk Premium');
  setCell(ROWS.COST_OF_EQUITY, 0, 'Cost of Equity');
  setCell(ROWS.COST_OF_DEBT, 0, 'Cost of Debt');
  setCell(ROWS.TAX_RATE_WACC, 0, 'Tax Rate');
  setCell(ROWS.DEBT_WEIGHT, 0, 'Debt Weight');
  setCell(ROWS.EQUITY_WEIGHT, 0, 'Equity Weight');
  setCell(ROWS.WACC, 0, 'WACC');

  // Set WACC values and formulas
  setCell(ROWS.RISK_FREE_RATE, 1, dcfResult.risk_free_rate);
  setCell(ROWS.BETA, 1, dcfResult.beta);
  setCell(ROWS.MARKET_PREMIUM, 1, dcfResult.market_premium);
  setCell(ROWS.COST_OF_EQUITY, 1, undefined, '=B92+B93*B94'); // Rf + Beta * MRP
  setCell(ROWS.COST_OF_DEBT, 1, dcfResult.cost_of_debt);
  setCell(ROWS.TAX_RATE_WACC, 1, dcfResult.tax_rate);
  setCell(ROWS.DEBT_WEIGHT, 1, dcfResult.debt_weight);
  setCell(ROWS.EQUITY_WEIGHT, 1, dcfResult.equity_weight);
  setCell(ROWS.WACC, 1, undefined, '=B99*B96+B98*B97*(1-B96)'); // E*Re + D*Rd*(1-T)

  // === DCF VALUATION SECTION ===
  setCell(ROWS.DCF_HEADER, 0, 'DCF VALUATION');
  setCell(ROWS.DCF_YEAR, 0, 'Year');
  setCell(ROWS.DCF_FCF, 0, 'Free Cash Flow');
  setCell(ROWS.DCF_DISCOUNT_FACTOR, 0, 'Discount Factor');
  setCell(ROWS.DCF_PV_FCF, 0, 'PV of FCF');
  setCell(ROWS.TERMINAL_FCF, 0, 'Terminal Year FCF');
  setCell(ROWS.TERMINAL_GROWTH, 0, 'Terminal Growth Rate');
  setCell(ROWS.TERMINAL_VALUE, 0, 'Terminal Value');
  setCell(ROWS.PV_TERMINAL, 0, 'PV of Terminal Value');
  setCell(ROWS.ENTERPRISE_VALUE, 0, 'Enterprise Value');
  setCell(ROWS.ADD_CASH, 0, 'Add: Cash');
  setCell(ROWS.LESS_DEBT, 0, 'Less: Total Debt');
  setCell(ROWS.EQUITY_VALUE, 0, 'Equity Value');
  setCell(ROWS.SHARES_OUTSTANDING, 0, 'Shares Outstanding');
  setCell(ROWS.INTRINSIC_VALUE, 0, 'Intrinsic Value Per Share');
  setCell(ROWS.CURRENT_PRICE, 0, 'Current Market Price');
  setCell(ROWS.MARGIN_OF_SAFETY, 0, 'Margin of Safety');
  setCell(ROWS.VALUATION_VERDICT, 0, 'VALUATION VERDICT');

  // Set year headers (columns 2 to TOTAL_YEARS+1)
  for (let i = 0; i < years.length && i < TOTAL_YEARS; i++) {
    setCell(ROWS.DCF_YEAR, i + 2, years[i]);
  }

  // Set DCF projection values
  for (let i = 0; i < dcfResult.projections.length && i < FORECAST_YEARS; i++) {
    const col = i + 2 + HISTORICAL_YEARS + 1; // After historical + current
    const proj = dcfResult.projections[i];
    
    setCell(ROWS.DCF_FCF, col, proj.fcf);
    setCell(ROWS.DCF_DISCOUNT_FACTOR, col, undefined, `=(1+$B$100)^${i+1}`);
    setCell(ROWS.DCF_PV_FCF, col, undefined, `=${getColumnLetter(col)}103/${getColumnLetter(col)}104`);
  }

  // Terminal value calculation (use column after 10-year forecast)
  const terminalCol = 2 + HISTORICAL_YEARS + 1 + FORECAST_YEARS;
  setCell(ROWS.TERMINAL_FCF, 1, dcfResult.terminal_year_fcf);
  setCell(ROWS.TERMINAL_GROWTH, 1, dcfResult.terminal_growth_rate);
  setCell(ROWS.TERMINAL_VALUE, 1, undefined, '=B107*(1+B108)/(B100-B108)'); // FCF*(1+g)/(WACC-g)
  setCell(ROWS.PV_TERMINAL, 1, undefined, `=B109/${getColumnLetter(terminalCol-1)}104`); // TV / discount factor

  // Enterprise and equity value
  const lastForecastCol = 2 + HISTORICAL_YEARS + FORECAST_YEARS;
  setCell(ROWS.ENTERPRISE_VALUE, 1, undefined, `=SUM(C105:${getColumnLetter(lastForecastCol)}105)+B110`);
  setCell(ROWS.ADD_CASH, 1, dcfResult.cash);
  setCell(ROWS.LESS_DEBT, 1, dcfResult.total_debt);
  setCell(ROWS.EQUITY_VALUE, 1, undefined, '=B112+B113-B114');
  setCell(ROWS.SHARES_OUTSTANDING, 1, dcfResult.shares_outstanding);
  setCell(ROWS.INTRINSIC_VALUE, 1, undefined, '=B115/B116');
  setCell(ROWS.CURRENT_PRICE, 1, dcfResult.current_price);
  setCell(ROWS.MARGIN_OF_SAFETY, 1, undefined, '=(B117-B119)/B119');
  setCell(ROWS.VALUATION_VERDICT, 1, dcfResult.verdict);

  // === SENSITIVITY ANALYSIS ===
  setCell(ROWS.SENSITIVITY_HEADER_1, 0, 'SENSITIVITY: WACC vs Terminal Growth');
  
  // Sensitivity table headers
  const waccRates = [0.07, 0.08, 0.09, 0.10, 0.11, 0.12];
  const growthRates = [0.01, 0.02, 0.03, 0.04, 0.05];
  
  setCell(ROWS.SENSITIVITY_WACC_GROWTH, 0, '');
  for (let i = 0; i < growthRates.length; i++) {
    setCell(ROWS.SENSITIVITY_WACC_GROWTH, i + 1, `g=${(growthRates[i]*100).toFixed(0)}%`);
  }
  
  // Sensitivity rows
  for (let i = 0; i < waccRates.length; i++) {
    const row = ROWS.SENSITIVITY_WACC_GROWTH + 1 + i;
    setCell(row, 0, `WACC=${(waccRates[i]*100).toFixed(0)}%`);
    // Note: Full sensitivity formulas would require recalculating DCF for each cell
    // Simplified: reference the actual calculated values from dcfResult
  }

  // Create the sheet
  const sheet: IWorksheetData = {
    id: 'dcf-model',
    name: `${financialData.ticker} DCF Valuation`,
    rowData,
  };

  // Create workbook
  const workbook: IWorkbookData = {
    id: 'dcf-workbook',
    name: `${financialData.ticker} DCF Model`,
    sheets: {
      'dcf-model': sheet,
    },
  };

  return workbook;
}

/**
 * Save workbook to XLSX file
 */
export async function saveWorkbook(
  workbook: IWorkbookData,
  outputPath: string
): Promise<void> {
  // Note: Actual XLSX export requires @univerjs/sheets-export or similar
  // For now, save as JSON snapshot that can be loaded by Univer
  
  const output = {
    ...workbook,
    generatedAt: new Date().toISOString(),
  };
  
  fs.writeFileSync(outputPath, JSON.stringify(output, null, 2));
  console.log(`Workbook saved to: ${outputPath}`);
}

// Main entry point for CLI usage
if (require.main === module) {
  // Example usage
  const exampleData: FinancialData = {
    ticker: 'AAPL',
    company_name: 'Apple Inc.',
    income_statements: {},
    balance_sheets: {},
    cash_flows: {},
    current_price: 175.0,
    shares_outstanding: 15.5e9,
    beta: 1.2,
  };
  
  const exampleResult: DCFResult = {
    ticker: 'AAPL',
    projections: [],
    terminal_year_fcf: 100e9,
    terminal_growth_rate: 0.025,
    terminal_value: 1.5e12,
    pv_terminal_value: 750e9,
    sum_pv_fcf: 500e9,
    enterprise_value: 1.25e12,
    cash: 200e9,
    total_debt: 120e9,
    equity_value: 1.33e12,
    shares_outstanding: 15.5e9,
    intrinsic_value_per_share: 85.8,
    current_price: 175.0,
    margin_of_safety: -0.51,
    verdict: 'OVERVALUED',
    wacc: 0.085,
    risk_free_rate: 0.04,
    beta: 1.2,
    market_premium: 0.05,
    cost_of_equity: 0.10,
    cost_of_debt: 0.045,
    tax_rate: 0.25,
    debt_weight: 0.25,
    equity_weight: 0.75,
  };
  
  const exampleAssumptions: Assumptions = {
    revenue_growth_y1_3: 0.08,
    revenue_growth_y4_7: 0.06,
    revenue_growth_y8_10: 0.04,
    terminal_growth_rate: 0.025,
    ebit_margin_target: 0.25,
    tax_rate: 0.25,
    dna_pct_of_revenue: 0.04,
    capex_pct_of_revenue: 0.06,
    nwc_pct_of_revenue: 0.12,
    risk_free_rate: 0.04,
    market_risk_premium: 0.05,
    cost_of_debt: 0.045,
    target_debt_ratio: 0.25,
  };
  
  generateDCFWorkbook(exampleData, exampleResult, exampleAssumptions)
    .then(workbook => {
      return saveWorkbook(workbook, './AAPL_DCF.json');
    })
    .catch(console.error);
}
