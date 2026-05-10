"""Agent configuration for smolagents"""
import os
from dotenv import load_dotenv
from smolagents import LiteLLMModel, CodeAgent, ToolCallingAgent

# Load environment variables
load_dotenv()


def get_model():
    """
    Get the LLM model for agents.
    Supports Ollama (local) or other providers via LiteLLM.
    """
    # Check if Ollama is configured
    ollama_base = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    ollama_model = os.getenv('OLLAMA_MODEL', 'qwen3:32b')
    
    # Use LiteLLM with Ollama
    return LiteLLMModel(
        model_id=f"ollama_chat/{ollama_model}",
        api_base=ollama_base,
        num_ctx=8192,
        temperature=0.2,  # Low temperature for conservative financial analysis
        max_tokens=4096,
    )


def get_agent_config(agent_type: str = "code"):
    """
    Get common agent configuration.
    
    Args:
        agent_type: "code" for CodeAgent, "tool" for ToolCallingAgent
    """
    model = get_model()
    
    # Common imports for financial analysis
    additional_imports = [
        'pandas',
        'numpy',
        'statistics',
        'math',
    ]
    
    return {
        'model': model,
        'additional_authorized_imports': additional_imports,
    }


def create_planner_agent():
    """
    Create the planner agent that determines ticker and strategy.
    
    This agent takes a user prompt like "Create DCF for Apple" and returns:
    - Ticker symbol
    - Company name
    - Execution plan
    """
    from smolagents import CodeAgent
    
    config = get_agent_config("code")
    
    planner_prompt = """You are a financial analysis planner. Your job is to:

1. Extract the ticker symbol from the user's request
2. Identify the company name
3. Create an execution plan for DCF analysis

Given a user request like "Create DCF for Apple" or "Value Tesla", you should:
- Identify the correct ticker (AAPL, TSLA, etc.)
- Verify the company name
- Determine if any special considerations apply (growth company, cyclical, etc.)

Return your response in this JSON format:
{
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "company_type": "mature|growth|cyclical|distressed",
    "special_considerations": ["list any"],
    "execution_plan": "brief description"
}

Be precise with ticker symbols. If unsure, ask for clarification."""

    return CodeAgent(
        **config,
        tools=[],  # Planner doesn't need external tools
        system_prompt=planner_prompt,
    )


def create_data_collection_agent():
    """
    Create the data collection agent that fetches financial data.
    """
    from smolagents import CodeAgent
    from tools import (
        fetch_all_financial_data,
        get_company_info,
        get_historical_prices,
    )
    
    config = get_agent_config("code")
    
    data_prompt = """You are a financial data collection specialist. Your job is to:

1. Fetch complete financial data for the given ticker
2. Retrieve income statements, balance sheets, and cash flow statements
3. Get market data (price, shares outstanding, beta)
4. Validate data completeness

Use the provided tools to fetch data from Yahoo Finance. Ensure:
- At least 10 years of historical data
- All required metrics are present
- Data is validated for consistency

Return the complete FinancialData object with all fields populated."""

    return CodeAgent(
        **config,
        tools=[
            fetch_all_financial_data,
            get_company_info,
            get_historical_prices,
        ],
        system_prompt=data_prompt,
    )


def create_analysis_agent():
    """
    Create the analysis agent that computes ratios and forecasts.
    """
    from smolagents import CodeAgent
    from tools.calculation_tools import (
        calculate_cagr,
        calculate_roic,
        calculate_roe,
        calculate_cost_of_equity,
    )
    from tools.validation_tools import (
        validate_accounting_identity,
        validate_fcf_calculation,
        validate_data_completeness,
    )
    
    config = get_agent_config("code")
    
    analysis_prompt = """You are a financial analyst. Your job is to:

1. Calculate historical financial ratios
2. Analyze trends in revenue, margins, and cash flow
3. Compute CAGR for key metrics
4. Calculate ROIC, ROE, and other efficiency metrics
5. Validate data consistency

Key metrics to compute:
- Revenue CAGR (3-yr, 5-yr, 10-yr)
- EBIT margin trend
- FCF margin trend
- ROIC and ROE trends
- Working capital efficiency
- CapEx intensity

Use conservative methods. Never extrapolate peaks. Apply mean reversion thinking.

Return a comprehensive analysis report with all calculated metrics."""

    return CodeAgent(
        **config,
        tools=[
            calculate_cagr,
            calculate_roic,
            calculate_roe,
            calculate_cost_of_equity,
            validate_accounting_identity,
            validate_fcf_calculation,
            validate_data_completeness,
        ],
        system_prompt=analysis_prompt,
    )


def create_valuation_agent():
    """
    Create the valuation agent that calculates DCF.
    """
    from smolagents import CodeAgent
    from tools.calculation_tools import (
        calculate_wacc,
        calculate_terminal_value,
        calculate_dcf,
        project_financials,
        run_dcf_valuation,
    )
    
    config = get_agent_config("code")
    
    valuation_prompt = """You are a DCF valuation specialist. Your job is to:

1. Set conservative assumptions based on historical analysis
2. Calculate WACC using CAPM
3. Project 10 years of financials
4. Calculate terminal value
5. Discount all cash flows
6. Compute intrinsic value per share
7. Determine margin of safety

Conservative modeling rules:
- Revenue growth: apply 20% decay to historical CAGR
- Margins: mean revert toward historical average
- Terminal growth: 2-4% only
- WACC must exceed terminal growth
- Terminal value < 75% of enterprise value

Return the complete DCFResult with all projections and final valuation."""

    return CodeAgent(
        **config,
        tools=[
            calculate_wacc,
            calculate_terminal_value,
            calculate_dcf,
            project_financials,
            run_dcf_valuation,
        ],
        system_prompt=valuation_prompt,
    )


def create_spreadsheet_agent():
    """
    Create the spreadsheet agent that generates the Univer workbook.
    """
    from smolagents import CodeAgent
    
    config = get_agent_config("code")
    
    spreadsheet_prompt = """You are a spreadsheet generation specialist. Your job is to:

1. Generate a single-sheet DCF model using Univer Facade API
2. Layout: Income Statement → Balance Sheet → Cash Flow → Metrics → Assumptions → WACC → DCF
3. Include all formulas (never hardcode derived values)
4. Add sensitivity analysis tables
5. Format professionally with headers

The spreadsheet must include:
- 15 years historical data
- Current year (TTM)
- 10-year forecast
- 100-year long-term projection
- Complete DCF calculation with formulas
- Sensitivity tables (WACC vs growth, CAGR vs margin)

All calculations must use spreadsheet formulas, not static values."""

    return CodeAgent(
        **config,
        tools=[],  # Spreadsheet agent uses Node.js subprocess
        system_prompt=spreadsheet_prompt,
    )
