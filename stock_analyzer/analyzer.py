"""
Stock Analyzer - Core financial analysis module
"""

import os
import csv
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from sec_data_fetcher import SECDataFetcher

logger = logging.getLogger(__name__)


class StockAnalyzer:
    """Analyzes US stock financial data and generates core financial indicators"""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the stock analyzer
        
        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = output_dir
        self.fetcher = SECDataFetcher()
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_financial_indicators(
        self,
        ticker: str,
        years: int = 10,
        start_year: int = None,
        end_year: int = None
    ) -> Dict[str, Any]:
        """
        Get core financial indicators for the past N years
        
        Args:
            ticker: Stock ticker symbol
            years: Number of years of historical data (used if start_year/end_year not provided)
            start_year: Optional start year (overrides years calculation)
            end_year: Optional end year (defaults to current year if not provided)
            
        Returns:
            Dictionary containing financial indicators and metadata
        """
        # Calculate year range
        current_year = datetime.now().year
        
        # If start_year/end_year are provided, use them directly
        if start_year is None:
            start_year = current_year - years + 1
        if end_year is None:
            end_year = current_year
        
        logger.info(f"Fetching financial data for {ticker} from {start_year} to {end_year}")
        
        # Use SECDataFetcher to get raw data (not pivot format)
        result = self.fetcher.fetch_financial_data(
            ticker=ticker,
            start_year=start_year,
            end_year=end_year,
            output_dir=self.output_dir,
            pivot=False,
            annual_only=True
        )
        
        # Get company info from result
        company_name = result.get('company_name', '')
        cik = result.get('cik', '')
        
        logger.info(f"Statements found: {result.get('statements_found')}")
        
        # Read the generated CSV files (non-pivot format)
        income_data = self._read_standard_csv(result['exported_files'].get('income_statement'))
        balance_data = self._read_standard_csv(result['exported_files'].get('balance_sheet'))
        cash_flow_data = self._read_standard_csv(result['exported_files'].get('cash_flow'))
        
        logger.info(f"Income indicators: {list(income_data.keys())[:5]}")
        
        # Get the actual years from the data
        available_years = set()
        for data_dict in [income_data, balance_data, cash_flow_data]:
            for indicator, year_data in data_dict.items():
                available_years.update(year_data.keys())
        
        # Filter to only include requested years and sort (year is integer)
        available_years = sorted([int(y) for y in available_years if str(y).isdigit() and int(y) >= start_year and int(y) <= end_year])
        
        logger.info(f"Available years: {available_years}")
        
        if not available_years:
            raise ValueError(f"No financial data found for {ticker}")
        
        # Calculate financial indicators
        indicators = self._calculate_indicators(
            income_data,
            balance_data,
            cash_flow_data,
            available_years
        )
        
        return {
            'ticker': ticker,
            'company_name': company_name,
            'cik': cik,
            'indicators': indicators,
            'data_sources': {
                'income_statement': result['exported_files'].get('income_statement', ''),
                'balance_sheet': result['exported_files'].get('balance_sheet', ''),
                'cash_flow': result['exported_files'].get('cash_flow', '')
            },
            'years': available_years
        }
    
    def _read_standard_csv(self, filepath: str) -> Dict[str, Dict[str, Any]]:
        """
        Read standard (non-pivot) CSV and convert to dictionary
        
        The standard CSV has columns: Date, Indicator, Label, Value, Unit, Year, etc.
        We use the 'Year' column directly for grouping.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            Dictionary with {indicator: {year: value}}
        """
        if not filepath or not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return {}
        
        logger.info(f"Reading standard CSV: {filepath}")
        
        data = {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                indicator = row.get('Indicator', '')
                if not indicator:
                    continue
                
                # Use 'Year' column (calendar year) for grouping, not 'Fiscal Year' column
                # The 'Fiscal Year' column from SEC API is unreliable for companies with non-standard fiscal years
                # (like Apple whose fiscal year ends in September)
                # The 'Year' column is derived from the end date and represents the calendar year
                year_str = row.get('Year', '')
                year = None
                
                if year_str:
                    try:
                        year = int(year_str)
                    except ValueError:
                        pass
                
                if year is None:
                    continue
                
                # Get the value (already formatted as string with commas)
                value_str = row.get('Value', '')
                if not value_str:
                    continue
                
                # Clean and convert value
                try:
                    clean_value = value_str.strip().replace(',', '').replace('"', '')
                    if clean_value:
                        value = float(clean_value)
                    else:
                        continue
                except ValueError:
                    continue
                
                # Store in data structure
                if indicator not in data:
                    data[indicator] = {}
                
                # If year already exists, keep the first occurrence
                if year not in data[indicator]:
                    data[indicator][year] = value
        
        logger.info(f"Read {len(data)} indicators from {filepath}")
        
        return data
    
    def _calculate_indicators(
        self,
        income_data: Dict[str, Dict[str, Any]],
        balance_data: Dict[str, Dict[str, Any]],
        cash_flow_data: Dict[str, Dict[str, Any]],
        years: List[int]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Calculate all financial indicators
        
        Args:
            income_data: Income statement data
            balance_data: Balance sheet data
            cash_flow_data: Cash flow data
            years: List of years to calculate indicators for
            
        Returns:
            Dictionary with years as keys and indicator values as list
        """
        # Map indicator names - using the actual names from standard CSV
        # Includes multiple possible names (aliases) for each indicator to handle different SEC reporting formats across years
        indicator_map = {
            # Revenue - multiple possible names for different years/companies
            'Revenue': [
                'Revenues',
                'RevenueFromContractWithCustomerExcludingAssessedTax',
                'SalesRevenueNet',
                'Revenue',
                'SalesRevenueGoodsNet'
            ],
            # Net Income
            'NetIncome': [
                'NetIncomeLoss',
                'Net Income (Loss) Attributable to Parent'
            ],
            # Cost of Goods Sold (for calculating Gross Profit)
            'CostOfGoodsSold': [
                'CostOfGoodsAndServicesSold',
                'CostOfRevenue',
                'CostOfGoodsSold',
                'CostOfSales'
            ],
            # Operating Income
            'OperatingIncome': [
                'OperatingIncomeLoss'
            ],
            # Total Assets
            'TotalAssets': [
                'Assets'
            ],
            # Total Equity
            'TotalEquity': [
                'StockholdersEquity'
            ],
            # Operating Cash Flow
            'OperatingCashFlow': [
                'NetCashProvidedByUsedInOperatingActivities'
            ],
            # CapEx (capital expenditures)
            'CapEx': [
                'PaymentsToAcquirePropertyPlantAndEquipment'
            ],
            # Dividends
            'Dividends': [
                'PaymentsOfDividends'
            ],
            # Share Repurchase
            'ShareRepurchase': [
                'PaymentsForRepurchaseOfCommonStock'
            ],
            # Short-term Debt - use CommercialPaper if available, otherwise ShortTermDebt
            # Only use ONE value, don't sum multiple indicators
            'ShortTermDebt': [
                'CommercialPaper',              # Commercial Paper (苹果等公司使用)
                'CommercialPaperObligations',  # Commercial Paper Obligations
                'ShortTermDebt',                # Short-term debt (汇总)
                'ShortTermBorrowingsDebt'       # Short-term borrowings (最后fallback)
            ],
            # Long-term Debt - prefer total LongTermDebt, otherwise sum components
            'LongTermDebt': [
                'LongTermDebt',                 # Long-term debt (汇总)
                'LongTermDebtNoncurrent',       # Long-term debt non-current
                'LongTermDebtCurrent'           # Long-term debt current (for summing)
            ],
        }
        
        # Build year data
        year_data = {}
        for year in years:
            year_data[year] = {
                'revenue': self._find_value(income_data, indicator_map['Revenue'], year),
                'net_income': self._find_value(income_data, indicator_map['NetIncome'], year),
                'cost_of_goods': self._find_value(income_data, indicator_map['CostOfGoodsSold'], year),
                'operating_income': self._find_value(income_data, indicator_map['OperatingIncome'], year),
                'total_assets': self._find_value(balance_data, indicator_map['TotalAssets'], year),
                'total_equity': self._find_value(balance_data, indicator_map['TotalEquity'], year),
                'operating_cash_flow': self._find_value(cash_flow_data, indicator_map['OperatingCashFlow'], year),
                'capex': self._find_value(cash_flow_data, indicator_map['CapEx'], year),
                'dividends': self._find_value(cash_flow_data, indicator_map['Dividends'], year),
                'share_repurchase': self._find_value(cash_flow_data, indicator_map['ShareRepurchase'], year),
                # For short-term debt, we use priority lookup (not sum) - take the first available
                'short_term_debt': self._find_value(balance_data, indicator_map['ShortTermDebt'], year),
                # For long-term debt, we also need to sum components when total is not available
                'long_term_debt': self._find_sum(balance_data, indicator_map['LongTermDebt'], year),
            }
        
        # Calculate derived indicators
        for i, year in enumerate(years):
            yd = year_data[year]
            
            # Get values
            revenue = yd.get('revenue')
            net_income = yd.get('net_income')
            cost_of_goods = yd.get('cost_of_goods')
            operating_income = yd.get('operating_income')
            total_assets = yd.get('total_assets')
            total_equity = yd.get('total_equity')
            operating_cash_flow = yd.get('operating_cash_flow')
            capex = yd.get('capex')
            dividends = yd.get('dividends')
            share_repurchase = yd.get('share_repurchase')
            short_term_debt = yd.get('short_term_debt')
            long_term_debt = yd.get('long_term_debt')
            
            # Calculate Gross Profit = Revenue - Cost of Goods Sold
            gross_profit = None
            if revenue is not None and cost_of_goods is not None:
                gross_profit = revenue - cost_of_goods
            
            # Convert from millions to 100 million USD (divide by 100)
            # SEC data is in millions, so divide by 100 to get 100M units
            
            # Revenue (100M USD)
            yd['revenue_100m'] = revenue / 100.0 if revenue else None
            
            # Net Income (100M USD)
            yd['net_income_100m'] = net_income / 100.0 if net_income else None
            
            # Operating Cash Flow (100M USD)
            yd['operating_cash_flow_100m'] = operating_cash_flow / 100.0 if operating_cash_flow else None
            
            # CapEx (100M USD)
            yd['capex_100m'] = abs(capex) / 100.0 if capex else None
            
            # Free Cash Flow = Operating Cash Flow - CapEx
            if operating_cash_flow is not None and capex is not None:
                yd['free_cash_flow_100m'] = (operating_cash_flow - abs(capex)) / 100.0
            else:
                yd['free_cash_flow_100m'] = None
            
            # Shareholder Return = Dividends + Share Repurchase
            # Note: These are typically negative in SEC data (cash outflow)
            div_value = abs(dividends) if dividends else 0
            repurchase_value = abs(share_repurchase) if share_repurchase else 0
            yd['shareholder_return_100m'] = (div_value + repurchase_value) / 100.0 if (dividends or share_repurchase) else None
            
            # Interest-bearing Debt
            debt_value = 0
            if short_term_debt:
                debt_value += abs(short_term_debt)
            if long_term_debt:
                debt_value += abs(long_term_debt)
            yd['interest_bearing_debt_100m'] = debt_value / 100.0 if debt_value else None
            
            # Calculate percentages and ratios
            # Revenue YoY growth
            if i > 0:
                prev_year = years[i - 1]
                prev_revenue = year_data.get(prev_year, {}).get('revenue')
                if revenue and prev_revenue and prev_revenue != 0:
                    yd['revenue_growth'] = ((revenue - prev_revenue) / abs(prev_revenue)) * 100
                else:
                    yd['revenue_growth'] = None
            else:
                yd['revenue_growth'] = None
            
            # Net Income YoY growth
            if i > 0:
                prev_year = years[i - 1]
                prev_net_income = year_data.get(prev_year, {}).get('net_income')
                if net_income and prev_net_income and prev_net_income != 0:
                    yd['net_income_growth'] = ((net_income - prev_net_income) / abs(prev_net_income)) * 100
                else:
                    yd['net_income_growth'] = None
            else:
                yd['net_income_growth'] = None
            
            # Gross Margin = Gross Profit / Revenue
            if gross_profit is not None and revenue and revenue != 0:
                yd['gross_margin'] = (gross_profit / revenue) * 100
            else:
                yd['gross_margin'] = None
            
            # Operating Margin = Operating Income / Revenue
            if operating_income and revenue and revenue != 0:
                yd['operating_margin'] = (operating_income / revenue) * 100
            else:
                yd['operating_margin'] = None
            
            # Net Margin = Net Income / Revenue
            if net_income and revenue and revenue != 0:
                yd['net_margin'] = (net_income / revenue) * 100
            else:
                yd['net_margin'] = None
            
            # ROE = Net Income / Total Equity
            if net_income and total_equity and total_equity != 0:
                yd['roe'] = (net_income / total_equity) * 100
            else:
                yd['roe'] = None
            
            # ROA = Net Income / Total Assets
            if net_income and total_assets and total_assets != 0:
                yd['roa'] = (net_income / total_assets) * 100
            else:
                yd['roa'] = None
            
            # Cash Conversion = Operating Cash Flow / Net Income
            if operating_cash_flow and net_income and net_income != 0:
                yd['cash_conversion'] = operating_cash_flow / net_income
            else:
                yd['cash_conversion'] = None
        
        return year_data
    
    def _find_value(
        self,
        data: Dict[str, Dict[str, Any]],
        indicator_names: List[str],
        year: int
    ) -> Optional[float]:
        """
        Find a value for a given year from available indicators
        
        Args:
            data: Data dictionary with year keys (integer)
            indicator_names: List of possible indicator names
            year: Year to find (integer)
            
        Returns:
            Value or None
        """
        for name in indicator_names:
            if name in data:
                year_data = data[name]
                # Try integer key
                if year in year_data:
                    return year_data[year]
        return None
    
    def _find_sum(
        self,
        data: Dict[str, Dict[str, Any]],
        indicator_names: List[str],
        year: int
    ) -> Optional[float]:
        """
        Find and sum values for a given year from multiple available indicators
        
        Args:
            data: Data dictionary with year keys (integer)
            indicator_names: List of possible indicator names
            year: Year to find (integer)
            
        Returns:
            Sum of values or None
        """
        total = 0.0
        found = False
        
        for name in indicator_names:
            if name in data:
                year_data = data[name]
                # Try integer key
                if year in year_data:
                    total += year_data[year]
                    found = True
        
        return total if found else None
    
    def export_to_csv(
        self,
        ticker: str,
        indicators: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """
        Export financial indicators to CSV file
        
        Args:
            ticker: Stock ticker symbol
            indicators: Calculated indicators
            
        Returns:
            Path to exported CSV file
        """
        # Output column names
        output_columns = [
            ('revenue_100m', '营业收入（亿美元）'),
            ('revenue_growth', '营收同比（%）'),
            ('net_income_100m', '归母净利（亿美元）'),
            ('net_income_growth', '归母净利润同比（%）'),
            ('gross_margin', '毛利率（%）'),
            ('operating_margin', '运营利润率（%）'),
            ('net_margin', '净利率（%）'),
            ('roe', 'ROE（%）'),
            ('roa', 'ROA（%）'),
            ('cash_conversion', '净现比（倍）'),
            ('operating_cash_flow_100m', '经营净现金流（亿美元）'),
            ('capex_100m', '资本开支（CapEx，亿美元）'),
            ('free_cash_flow_100m', '自由现金流（亿美元）'),
            ('shareholder_return_100m', '股东回报（亿美元）'),
            ('interest_bearing_debt_100m', '有息负债（亿美元）'),
        ]
        
        # Generate filename
        filename = f"{ticker.upper()}_financial_indicators.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        # Get years
        years = sorted(indicators.keys())
        
        # Write CSV
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            # Header row: first column is empty (indicator names), then years
            header = ['指标'] + [str(year) for year in years]
            writer = csv.writer(f)
            writer.writerow(header)
            
            # Data rows
            for col_key, col_name in output_columns:
                row = [col_name]
                for year in years:
                    value = indicators[year].get(col_key)
                    if value is not None:
                        # Format based on unit type
                        if '亿美元' in col_name:
                            # 亿美元单位：使用千位分隔符，2位小数
                            row.append(f"{value:,.2f}")
                        elif '（%）' in col_name:
                            # 百分比：1位小数
                            row.append(f"{value:.1f}")
                        else:
                            # 倍数等其他类型：2位小数
                            row.append(f"{value:.2f}")
                    else:
                        row.append('')
                writer.writerow(row)
        
        logger.info(f"Exported financial indicators to {filepath}")
        return filepath
