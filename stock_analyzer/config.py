"""
Configuration for Stock Analyzer
"""

# Default number of years of historical data to fetch
DEFAULT_YEARS = 10

# Output directory for analysis results
DEFAULT_OUTPUT_DIR = "output"

# Financial indicators to analyze (for function 1)
# These are the GAAP indicator names used in SEC data
FINANCIAL_INDICATORS = {
    # Income Statement
    "Revenue": "Revenues",
    "CostOfRevenue": "CostOfGoodsAndServicesSold",
    "GrossProfit": "GrossProfit",
    "OperatingIncome": "OperatingIncomeLoss",
    "NetIncome": "NetIncomeLoss",
    
    # Balance Sheet
    "TotalAssets": "Assets",
    "TotalEquity": "StockholdersEquity",
    "TotalLiabilities": "Liabilities",
    
    # Cash Flow Statement
    "OperatingCashFlow": "NetCashProvidedByUsedInOperatingActivities",
    "CapEx": "PaymentsToAcquirePropertyPlantAndEquipment",
    "Dividends": "PaymentsOfDividends",
    "ShareRepurchase": "PaymentsForRepurchaseOfCommonStock",
}

# Interest-bearing debt indicators (for total debt calculation)
DEBT_INDICATORS = [
    "ShortTermBorrowingsDebt",
    "ShortTermBorrowings",
    "LongTermDebtNoncurrent",
    "LongTermDebt",
    "LongTermDebtCurrent",
    "CurrentPortionOfLongTermDebt",
]

# Output column names mapping
OUTPUT_COLUMN_NAMES = {
    "revenue": "营业收入（亿美元）",
    "revenue_growth": "营收同比（%）",
    "net_income": "归母净利（亿美元）",
    "net_income_growth": "归母净利润同比（%）",
    "gross_margin": "毛利率（%）",
    "operating_margin": "运营利润率（%）",
    "net_margin": "净利率（%）",
    "roe": "ROE（%）",
    "roa": "ROA（%）",
    "cash_conversion": "净现比（倍）",
    "operating_cash_flow": "经营净现金流（亿美元）",
    "capex": "资本开支（CapEx，亿美元）",
    "free_cash_flow": "自由现金流（亿美元）",
    "shareholder_return": "股东回报（亿美元）",
    "interest_bearing_debt": "有息负债（亿美元）",
}
