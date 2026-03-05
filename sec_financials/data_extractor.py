"""
Financial data extractor from SEC API responses
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .config import GAAP_INDICATORS
from .time_processor import TimeProcessor

logger = logging.getLogger(__name__)


class DataExtractor:
    """Extracts financial data from SEC API responses"""
    
    def __init__(self):
        """Initialize data extractor"""
        self.gaap_indicators = GAAP_INDICATORS
        
        # Create indicator aliases for better matching
        # Primary indicators are in GAAP_INDICATORS, these are alternatives
        self.indicator_aliases = {
            'BalanceSheet': {
                'LongTermDebtNoncurrent': [
                    'LongTermDebt',
                    'LongTermDebtExcludingCurrentMaturities',
                    'DebtNoncurrent',
                    'LongTermDebtAndCapitalLeaseObligationsNoncurrent'
                ]
            },
            'IncomeStatement': {
                'RevenueFromContractWithCustomerExcludingAssessedTax': [
                    'Revenues',
                    'SalesRevenueNet',
                    'Revenue',
                    'SalesRevenueGoodsNet'
                ],
                'CostOfGoodsAndServicesSold': [
                    'CostOfRevenue',
                    'CostOfGoodsSold',
                    'CostOfSales'
                ],
                'SellingGeneralAndAdministrativeExpense': [
                    'SellingAndMarketingExpense',
                    'SellingGeneralAndAdministrativeExpenses',
                    'MarketingExpense'
                ],
                'GeneralAndAdministrativeExpense': [
                    'GeneralAndAdministrativeExpenses',
                    'GeneralAdministrativeExpense',
                    'GeneralAdministrativeExpenses',
                    'GeneralAndAdministrative'
                ],
                'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest': [
                    'IncomeLossFromContinuingOperationsBeforeIncomeTaxes',
                    'IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments',
                    'IncomeBeforeIncomeTaxes',
                    'IncomeLossBeforeIncomeTaxes',
                    'IncomeBeforeTax',
                    'IncomeLossBeforeTax'
                ],
                'IncomeLossFromContinuingOperationsBeforeIncomeTaxes': [
                    'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
                    'IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments',
                    'IncomeBeforeIncomeTaxes',
                    'IncomeLossBeforeIncomeTaxes',
                    'IncomeBeforeTax',
                    'IncomeLossBeforeTax'
                ],
                'GrossProfit': [
                    'GrossProfitLoss'
                ],
                'OperatingExpenses': [
                    'OperatingExpense',
                    'OperatingCostsAndExpenses'
                ]
            },
            'CashFlowStatement': {
                'NetPaymentsRelatedToStockBasedAwardActivities': [
                    'PaymentsForStockBasedAwardActivities',
                    'StockCompensationPayments',
                    'PaymentsRelatedToStockBasedCompensation',
                    'NetPaymentsForStockBasedCompensation',
                    'AdjustmentsRelatedToTaxWithholdingForShareBasedCompensation'
                ]
            }
        }
        
        # Reverse mapping for deduplication: actual SEC indicator -> primary indicator
        self._build_reverse_alias_mapping()
    
    def _build_reverse_alias_mapping(self):
        """Build reverse mapping from actual indicators to primary indicators"""
        self.reverse_aliases = {}
        for statement_type, aliases in self.indicator_aliases.items():
            for primary_indicator, alternative_list in aliases.items():
                for alternative in alternative_list:
                    self.reverse_aliases[alternative] = primary_indicator
                # Also map primary to itself
                self.reverse_aliases[primary_indicator] = primary_indicator
    
    def extract_financial_statements(
        self,
        company_data: Dict[str, Any],
        year: Optional[int] = None,
        quarter: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
        accumulated: bool = False,
        annual_only: bool = False
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract financial statements from company data
        
        Args:
            company_data: Company facts data from SEC API
            year: Specific year to filter
            quarter: Specific quarter to filter (1-4)
            start_year: Start year for range
            end_year: End year for range
            start_quarter: Start quarter for range
            end_quarter: End quarter for range
            accumulated: Whether to use accumulated data (Nine Months Ended) instead of quarterly data
            annual_only: Whether to keep only annual data (FY) when filtering by year
            
        Returns:
            Dictionary with keys: 'balance_sheet', 'income_statement', 'cash_flow'
        """
        if 'facts' not in company_data or 'us-gaap' not in company_data['facts']:
            logger.warning("No GAAP facts found in company data")
            return {
                'balance_sheet': [],
                'income_statement': [],
                'cash_flow': []
            }
        
        gaap_facts = company_data['facts']['us-gaap']
        
        # Extract company information
        company_info = self._extract_company_info(company_data)
        
        # Extract each statement
        balance_sheet = self._extract_statement(
            gaap_facts, 'BalanceSheet', company_info,
            year, quarter, start_year, end_year, start_quarter, end_quarter,
            accumulated, annual_only
        )
        
        income_statement = self._extract_statement(
            gaap_facts, 'IncomeStatement', company_info,
            year, quarter, start_year, end_year, start_quarter, end_quarter,
            accumulated, annual_only
        )
        
        cash_flow = self._extract_statement(
            gaap_facts, 'CashFlowStatement', company_info,
            year, quarter, start_year, end_year, start_quarter, end_quarter,
            accumulated, annual_only
        )
        
        return {
            'balance_sheet': balance_sheet,
            'income_statement': income_statement,
            'cash_flow': cash_flow
        }
    
    def _extract_company_info(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract company information from data"""
        company_info = {
            'cik': company_data.get('cik'),
            'entityName': company_data.get('entityName', ''),
            'ticker': company_data.get('ticker', ''),
            'sic': company_data.get('sic', ''),
            'sicDescription': company_data.get('sicDescription', '')
        }
        
        # Clean up entity name
        if company_info['entityName']:
            company_info['entityName'] = company_info['entityName'].replace('\\', '')
        
        return company_info
    
    def _find_indicator_match(self, indicator: str, available_indicators: List[str]) -> Optional[str]:
        """
        Find the best matching indicator in available indicators
        
        Args:
            indicator: Target indicator name
            available_indicators: List of available indicator names
            
        Returns:
            Matched indicator name or None
        """
        # Debug logging
        logger.debug(f"Looking for match for {indicator} in {len(available_indicators)} available indicators")
        
        # Exact match
        if indicator in available_indicators:
            logger.debug(f"Exact match found: {indicator}")
            return indicator
        
        # Check aliases
        for stmt_type, aliases in self.indicator_aliases.items():
            if indicator in aliases:
                logger.debug(f"Checking aliases for {indicator}: {aliases[indicator]}")
                for alias in aliases[indicator]:
                    if alias in available_indicators:
                        logger.debug(f"Using alias {alias} for {indicator}")
                        return alias
        
        # Try partial matching
        indicator_lower = indicator.lower()
        for avail_ind in available_indicators:
            avail_lower = avail_ind.lower()
            
            # Check if indicator is contained in available indicator or vice versa
            if indicator_lower in avail_lower or avail_lower in indicator_lower:
                logger.debug(f"Partial match: {indicator} -> {avail_ind}")
                return avail_ind
        
        # Try word-based matching
        indicator_words = set(re.findall(r'[A-Z][a-z]+', indicator))
        for avail_ind in available_indicators:
            avail_words = set(re.findall(r'[A-Z][a-z]+', avail_ind))
            
            # Check for significant word overlap
            common_words = indicator_words.intersection(avail_words)
            if len(common_words) >= 2:  # At least 2 common words
                logger.debug(f"Word-based match: {indicator} -> {avail_ind} (common words: {common_words})")
                return avail_ind
        
        logger.debug(f"No match found for {indicator}")
        return None
    
    def _find_exact_or_alias_match(self, indicator: str, available_indicators: List[str]) -> Optional[str]:
        """
        Find exact match or alias match only (no partial or word-based matching)
        
        Args:
            indicator: Target indicator name
            available_indicators: List of available indicator names
            
        Returns:
            Matched indicator name or None
        """
        # Debug logging
        logger.debug(f"Looking for exact/alias match for {indicator} in {len(available_indicators)} available indicators")
        
        # Exact match
        if indicator in available_indicators:
            logger.debug(f"Exact match found: {indicator}")
            return indicator
        
        # Check aliases only (no partial or word-based matching)
        for stmt_type, aliases in self.indicator_aliases.items():
            if indicator in aliases:
                logger.debug(f"Checking aliases for {indicator}: {aliases[indicator]}")
                for alias in aliases[indicator]:
                    if alias in available_indicators:
                        logger.debug(f"Using alias {alias} for {indicator}")
                        return alias
        
        logger.debug(f"No exact or alias match found for {indicator}")
        return None
    
    def _deduplicate_data_points(self, data_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate data points where multiple configured indicators match the same SEC indicator
        
        Args:
            data_points: List of data point dictionaries
            Returns:
            Deduplicated list of data points
        """
        if not data_points:
            return []
        
        # Group data points by (date, indicator)
        # Keep only the latest filed date for each group
        grouped_data = {}
        
        logger.debug(f"Starting deduplication with {len(data_points)} data points")
        
        for point in data_points:
            date = point.get('end', '')
            indicator = point.get('indicator', '')
            fiscal_year = point.get('fy', '')
            filed_date = point.get('filed', '')
            matched_indicator = point.get('matched_indicator', '')
            value = point.get('val', '')
            frame = point.get('frame', '')
            
            # Create a grouping key: (date, indicator)
            group_key = (date, indicator)
            
            # Parse filed date for comparison
            try:
                filed_datetime = TimeProcessor.parse_date(filed_date) if filed_date else None
            except (ValueError, KeyError):
                filed_datetime = None
            
            # If this group already has an entry, keep the one with the latest filed date
            if group_key in grouped_data:
                existing_point = grouped_data[group_key]
                existing_filed = existing_point.get('filed', '')
                existing_filed_datetime = None
                
                try:
                    existing_filed_datetime = TimeProcessor.parse_date(existing_filed) if existing_filed else None
                except (ValueError, KeyError):
                    existing_filed_datetime = None
                
                # Compare filed dates
                if filed_datetime and existing_filed_datetime:
                    if filed_datetime > existing_filed_datetime:
                        # New point has later filed date, replace
                        grouped_data[group_key] = point
                        logger.debug(f"  Replacing: {indicator} at {date} - newer filed date: {filed_date} > {existing_filed}")
                    else:
                        logger.debug(f"  Keeping existing: {indicator} at {date} - older filed date: {filed_date} <= {existing_filed}")
                elif filed_datetime and not existing_filed_datetime:
                    # New point has filed date, existing doesn't, replace
                    grouped_data[group_key] = point
                    logger.debug(f"  Replacing: {indicator} at {date} - has filed date: {filed_date}")
                else:
                    # Keep existing (either both have no filed date or existing is newer)
                    logger.debug(f"  Keeping existing: {indicator} at {date}")
            else:
                # First entry for this group
                grouped_data[group_key] = point
                logger.debug(f"  Adding: {indicator} at {date} - filed: {filed_date}")
        
        # Convert back to list
        deduplicated = list(grouped_data.values())
        
        logger.debug(f"After deduplication: {len(deduplicated)} data points")
        return deduplicated
    
    def _extract_statement(
        self,
        gaap_facts: Dict[str, Any],
        statement_type: str,
        company_info: Dict[str, Any],
        year: Optional[int] = None,
        quarter: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
        accumulated: bool = False,
        annual_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Extract specific statement data
        
        Args:
            gaap_facts: GAAP facts dictionary
            statement_type: Type of statement ('BalanceSheet', 'IncomeStatement', 'CashFlowStatement')
            company_info: Company information dictionary
            year: Specific year to filter
            quarter: Specific quarter to filter
            start_year: Start year for range
            end_year: End year for range
            start_quarter: Start quarter for range
            end_quarter: End quarter for range
            accumulated: Whether to use accumulated data (Nine Months Ended) instead of quarterly data
            annual_only: Whether to keep only annual data (FY) when filtering by year
            
        Returns:
            List of data points for the statement
        """
        statement_data = []
        indicators = self.gaap_indicators.get(statement_type, [])
        available_indicators = list(gaap_facts.keys())
        
        # Track which actual SEC indicators have been matched
        matched_sec_indicators = {}
        
        logger.debug(f"Extracting {statement_type} with {len(indicators)} configured indicators")
        logger.debug(f"Available indicators in SEC data: {len(available_indicators)}")
        
        for indicator in indicators:
            # Try to find matching indicator
            matched_indicator = self._find_indicator_match(indicator, available_indicators)
            
            if not matched_indicator:
                logger.debug(f"Indicator {indicator} not found in available indicators")
                continue
            
            # Check if this SEC indicator has already been matched by another configured indicator
            if matched_indicator in matched_sec_indicators:
                existing_primary = matched_sec_indicators[matched_indicator]
                logger.debug(f"SEC indicator {matched_indicator} already matched by {existing_primary}, skipping {indicator}")
                continue
            
            # Record this match
            matched_sec_indicators[matched_indicator] = indicator
            
            fact_data = gaap_facts[matched_indicator]
            
            # Get units (usually USD)
            units = list(fact_data.get('units', {}).keys())
            if not units:
                logger.debug(f"No units found for {matched_indicator}")
                continue
            
            primary_unit = units[0]  # Usually 'USD' or 'shares'
            unit_data = fact_data['units'][primary_unit]
            
            logger.debug(f"Found {len(unit_data)} data points for {indicator} -> {matched_indicator}")
            
            # Extract data points
            for data_point in unit_data:
                # Add metadata
                data_point_with_meta = data_point.copy()
                data_point_with_meta.update({
                    'indicator': indicator,  # Use original indicator name for consistency
                    'matched_indicator': matched_indicator,  # Store the actual matched indicator
                    'label': fact_data.get('label', indicator),
                    'description': fact_data.get('description', ''),
                    'unit': primary_unit,
                    'statement_type': statement_type,
                    **company_info
                })
                
                statement_data.append(data_point_with_meta)
        
        logger.debug(f"Extracted {len(statement_data)} data points before filtering for {statement_type}")
        
        # Apply time filtering
        filtered_data = TimeProcessor.filter_data_points(
            statement_data,
            year=year,
            quarter=quarter,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
            annual_only=annual_only
        )
        
        logger.debug(f"After time filtering: {len(filtered_data)} data points for {statement_type}")
        
        # Filter by accumulated flag
        # Special handling for different statement types:
        # - BalanceSheet: Instant data (时点数据) - always keep all data regardless of accumulated flag
        # - IncomeStatement: Duration data (期间数据) - filter based on accumulated flag
        # - CashFlowStatement: Duration data (期间数据) - usually only has accumulated data, keep all
        if statement_type == 'BalanceSheet':
            # Balance sheet is instant data - always keep all data
            logger.debug(f"Balance sheet (instant data): keeping all {len(filtered_data)} data points (no frame filtering)")
        elif statement_type == 'CashFlowStatement':
            # Cash flow statement usually only has accumulated data - keep all
            logger.debug(f"Cash flow statement: keeping all {len(filtered_data)} data points (no frame filtering)")
        else:
            # Income statement: filter based on accumulated flag
            if accumulated:
                # Keep only accumulated data (Frame is empty or None)
                filtered_data = [point for point in filtered_data if not point.get('frame')]
                logger.debug(f"Income statement after accumulated filter: {len(filtered_data)} data points (accumulated data only)")
            else:
                # Keep only quarterly data (Frame is not empty)
                filtered_data = [point for point in filtered_data if point.get('frame')]
                logger.debug(f"Income statement after quarterly filter: {len(filtered_data)} data points (quarterly data only)")
        
        # Additional deduplication (in case same data appears multiple times)
        filtered_data = self._deduplicate_data_points(filtered_data)
        
        logger.debug(f"After deduplication: {len(filtered_data)} data points for {statement_type}")
        
        # Sort by date
        filtered_data.sort(key=lambda x: x.get('end', ''), reverse=True)
        
        return filtered_data
    
    def get_available_indicators(self, company_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Get list of available indicators in company data
        
        Args:
            company_data: Company facts data from SEC API
            
        Returns:
            Dictionary of available indicators by statement type
        """
        if 'facts' not in company_data or 'us-gaap' not in company_data['facts']:
            return {}
        
        gaap_facts = company_data['facts']['us-gaap']
        
        available_indicators = {
            'BalanceSheet': [],
            'IncomeStatement': [],
            'CashFlowStatement': []
        }
        
        # Check which configured indicators are available
        # Use exact or alias match only (no partial or word-based matching)
        for statement_type, indicators in self.gaap_indicators.items():
            for indicator in indicators:
                matched = self._find_exact_or_alias_match(indicator, list(gaap_facts.keys()))
                if matched:
                    available_indicators[statement_type].append(indicator)
        
        # Also get all available indicators (not just configured ones)
        all_indicators = list(gaap_facts.keys())
        
        return {
            'configured': available_indicators,
            'all': all_indicators,
            'total_count': len(all_indicators)
        }
    
    def format_data_for_csv(
        self,
        statement_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format statement data for CSV export
        
        Args:
            statement_data: List of data point dictionaries
            
        Returns:
            Formatted data ready for CSV export
        """
        formatted_data = []
        
        for data_point in statement_data:
            indicator = data_point.get('indicator', '')
            value = data_point.get('val', '')
            unit = data_point.get('unit', '')
            
            # Debug logging
            logger.debug(f"Formatting data point: {indicator} = {value} {unit}")
            
            # Format value based on unit
            formatted_value = value
            formatted_unit = unit
            
            # Convert USD values to millions with thousand separators
            if unit == 'USD' and value is not None and value != '':
                try:
                    # Convert to float and divide by 1,000,000
                    numeric_value = float(value)
                    value_in_millions = numeric_value / 1000000.0
                    
                    # Format with thousand separators and 2 decimal places
                    # Use locale-independent formatting
                    if value_in_millions.is_integer():
                        formatted_value = f"{int(value_in_millions):,}"
                    else:
                        formatted_value = f"{value_in_millions:,.2f}"
                    
                    # Update unit to indicate millions
                    formatted_unit = 'USD(Millions)'
                    logger.debug(f"Converted {value} USD to {formatted_value} {formatted_unit}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to convert value {value} for {indicator}: {e}")
                    # Keep original value if conversion fails
                    formatted_value = value
                    formatted_unit = unit
            
            formatted_point = {
                'Date': data_point.get('end', ''),
                'Indicator': indicator,
                'Label': data_point.get('label', ''),
                'Value': formatted_value,
                'Unit': formatted_unit,
                'Accumulated': data_point.get('accn', ''),
                'Fiscal Year': data_point.get('fy', ''),
                'Fiscal Period': data_point.get('fp', ''),
                'Form': data_point.get('form', ''),
                'Filed': data_point.get('filed', ''),
                'Frame': data_point.get('frame', ''),
                'Company Name': data_point.get('entityName', ''),
                'Ticker': data_point.get('ticker', ''),
                'CIK': data_point.get('cik', ''),
                'SIC': data_point.get('sic', ''),
                'SIC Description': data_point.get('sicDescription', '')
            }
            
            # Parse date for additional fields
            date_str = data_point.get('end', '')
            if date_str:
                try:
                    date_obj = TimeProcessor.parse_date(date_str)
                    formatted_point['Year'] = date_obj.year
                    formatted_point['Month'] = date_obj.month
                    formatted_point['Day'] = date_obj.day
                    
                    # Add quarter
                    quarter = TimeProcessor.get_year_quarter(date_obj)[1]
                    formatted_point['Quarter'] = f"Q{quarter}"
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error parsing date {date_str} for {indicator}: {e}")
                    formatted_point['Year'] = ''
                    formatted_point['Month'] = ''
                    formatted_point['Day'] = ''
                    formatted_point['Quarter'] = ''
            
            formatted_data.append(formatted_point)
        
        logger.debug(f"Formatted {len(formatted_data)} data points for CSV")
        return formatted_data
