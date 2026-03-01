"""
Configuration settings for SEC Financial Data Extractor
"""

# SEC API Configuration
SEC_API_BASE_URL = "https://data.sec.gov/api/xbrl"
COMPANY_FACTS_ENDPOINT = "/companyfacts/CIK{cik}.json"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# User-Agent configuration (required by SEC API)
USER_AGENT = "StockAnalysis/1.0 (contact: your-email@example.com)"

# Rate limiting (requests per second)
RATE_LIMIT = 10  # SEC recommended limit

# Cache configuration
CACHE_DIR = ".sec_cache"
TICKER_CACHE_FILE = "ticker_cik_mapping.json"
CACHE_EXPIRY_DAYS = 7

# GAAP Standard Indicators Mapping - Primary indicators only
# Secondary/alternative indicators are handled in DataExtractor.indicator_aliases
# Reordered to match SEC 10-K/10-Q financial statement presentation order
GAAP_INDICATORS = {
    "BalanceSheet": [
        # Assets (in order of liquidity)
        "CashAndCashEquivalentsAtCarryingValue",
        "ShortTermBorrowings",  # Cash, Cash Equivalents, and Short-term Investments
        "AccountsReceivableNetCurrent",
        "InventoryNet",
        "AssetsCurrent",
        "PropertyPlantAndEquipmentNet",
        "Goodwill",
        "IntangibleAssetsNetExcludingGoodwill",
        "Assets",
        # Liabilities (current then non-current)
        "AccountsPayableCurrent",
        "LiabilitiesCurrent",
        "LongTermDebtNoncurrent",  # Changed from LongTermDebt to match 10-K value
        "Liabilities",
        # Equity
        "RetainedEarningsAccumulatedDeficit",
        "StockholdersEquity"
    ],
    "IncomeStatement": [
        # Revenue and cost of revenue
        "Revenues",  # Primary revenue indicator (Google uses 'Revenues' not 'RevenueFromContractWithCustomerExcludingAssessedTax')
        "RevenueFromContractWithCustomerExcludingAssessedTax",  # Fallback revenue indicator
        "CostOfGoodsAndServicesSold",  # Primary cost indicator
        "GrossProfit",
        # Operating expenses
        "ResearchAndDevelopmentExpense",
        "SellingGeneralAndAdministrativeExpense",  # Primary SG&A indicator
        "GeneralAndAdministrativeExpense",  # General and administrative expense (separate for Google)
        "OperatingExpenses",
        "DepreciationDepletionAndAmortization",
        # Operating income
        "OperatingIncomeLoss",
        # Non-operating items
        "InterestExpense",
        # Pre-tax income
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",  # Income before taxes
        # Income tax
        "IncomeTaxExpenseBenefit",
        # Net income
        "NetIncomeLoss",
        # Earnings per share
        "EarningsPerShareBasic",
        "EarningsPerShareDiluted"
    ],
    "CashFlowStatement": [
        # Operating activities
        "NetCashProvidedByUsedInOperatingActivities",
        # Investing activities
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "ProceedsFromSaleOfPropertyPlantAndEquipment",
        "PaymentsToAcquireBusinessesNetOfCashAcquired",
        "ProceedsFromDivestitureOfBusinessesNetOfCashDivested",
        "NetCashProvidedByUsedInInvestingActivities",
        # Financing activities
        "PaymentsForRepurchaseOfCommonStock",
        "ProceedsFromIssuanceOfCommonStock",
        "PaymentsOfDividends",
        "NetPaymentsRelatedToStockBasedAwardActivities",  # Net payments related to stock-based award activities
        "NetCashProvidedByUsedInFinancingActivities",
        # Net change in cash
        "CashAndCashEquivalentsPeriodIncreaseDecrease"
    ]
}

# Quarter mapping
QUARTER_MONTHS = {
    1: (1, 3),   # Q1: Jan-Mar
    2: (4, 6),   # Q2: Apr-Jun
    3: (7, 9),   # Q3: Jul-Sep
    4: (10, 12)  # Q4: Oct-Dec
}