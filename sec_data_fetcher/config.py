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
        # 流动负债 - 按流动性排序
        "ShortTermBorrowingsDebt",  # 短期借款（有息）
        "LongTermDebtCurrent",      # 一年内到期的非流动负债
        "AccountsPayableCurrent",   # 应付账款
        "LiabilitiesCurrent",       # 流动负债合计
        # 非流动负债
        "LongTermDebtNoncurrent",   # 长期借款（排除一年内到期）
        # 负债合计
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

# 指标简称映射（用于透视表输出）
INDICATOR_SHORT_NAMES = {
    # 资产负债表
    "CashAndCashEquivalentsAtCarryingValue": "Cash",
    "ShortTermBorrowings": "Short-term Borrowings",
    "AccountsReceivableNetCurrent": "Accounts Receivable",
    "InventoryNet": "Inventory",
    "AssetsCurrent": "Total Current Assets",
    "PropertyPlantAndEquipmentNet": "PP&E",
    "Goodwill": "Goodwill",
    "IntangibleAssetsNetExcludingGoodwill": "Intangibles",
    "Assets": "Total Assets",
    "AccountsPayableCurrent": "Accounts Payable",
    "LiabilitiesCurrent": "Total Current Liabilities",
    # 有息负债相关指标
    "ShortTermBorrowingsDebt": "Short-term Debt",
    "LongTermDebtCurrent": "Current Portion of Long-term Debt",
    "LongTermDebtNoncurrent": "Long-term Debt",
    "Liabilities": "Total Liabilities",
    "RetainedEarningsAccumulatedDeficit": "Retained Earnings",
    "StockholdersEquity": "Total Equity",
    
    # 利润表
    "Revenues": "Revenue",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "Revenue",
    "CostOfGoodsAndServicesSold": "Cost of Revenue",
    "GrossProfit": "Gross Profit",
    "ResearchAndDevelopmentExpense": "R&D",
    "SellingGeneralAndAdministrativeExpense": "SG&A",
    "GeneralAndAdministrativeExpense": "G&A",
    "OperatingExpenses": "Operating Expenses",
    "DepreciationDepletionAndAmortization": "Depreciation & Amortization",
    "OperatingIncomeLoss": "Operating Income",
    "InterestExpense": "Interest Expense",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": "Pre-tax Income",
    "IncomeTaxExpenseBenefit": "Income Tax",
    "NetIncomeLoss": "Net Income",
    "EarningsPerShareBasic": "EPS (Basic)",
    "EarningsPerShareDiluted": "EPS (Diluted)",
    
    # 现金流量表
    "NetCashProvidedByUsedInOperatingActivities": "Operating Cash Flow",
    "PaymentsToAcquirePropertyPlantAndEquipment": "CapEx",
    "ProceedsFromSaleOfPropertyPlantAndEquipment": "PP&E Sale Proceeds",
    "PaymentsToAcquireBusinessesNetOfCashAcquired": "Acquisitions",
    "ProceedsFromDivestitureOfBusinessesNetOfCashDivested": "Divestitures",
    "NetCashProvidedByUsedInInvestingActivities": "Investing Cash Flow",
    "PaymentsForRepurchaseOfCommonStock": "Share Repurchase",
    "ProceedsFromIssuanceOfCommonStock": "Stock Issuance",
    "PaymentsOfDividends": "Dividends",
    "NetPaymentsRelatedToStockBasedAwardActivities": "Stock-based Compensation",
    "NetCashProvidedByUsedInFinancingActivities": "Financing Cash Flow",
    "CashAndCashEquivalentsPeriodIncreaseDecrease": "Net Change in Cash"
}
