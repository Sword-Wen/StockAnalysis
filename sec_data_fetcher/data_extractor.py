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
                'ShortTermBorrowingsDebt': [
                    'ShortTermBorrowings',
                    'DebtCurrent',
                    'NotesPayableCurrent',
                    'ShortTermDebt',
                    'CurrentPortionOfLongTermDebt'
                ],
                'LongTermDebtCurrent': [
                    'CurrentPortionOfLongTermDebt',
                    'LongTermDebtCurrent',
                    'DebtCurrentMaturitiesOfLongTermDebt'
                ],
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
        Remove duplicate data points with improved logic:
        For the same reporting period and indicator, keep the data point with the latest filed date.
        This ensures we get the most recent revision of the financial data.
        
        IMPORTANT: For companies with non-standard fiscal years (like Apple, whose fiscal year ends in September),
        we need to handle the case where FY data and Q1 data of the next calendar year have the same calendar year.
        We prioritize FY (annual) data over quarterly data when they fall in the same calendar year.
        
        Args:
            data_points: List of data point dictionaries
            Returns:
            Deduplicated list of data points
        """
        if not data_points:
            return []
        
        # Group data points by (calendar_year, indicator)
        grouped_data = {}
        
        logger.debug(f"Starting deduplication with {len(data_points)} data points")
        
        for point in data_points:
            end_date = point.get('end', '')
            indicator = point.get('indicator', '')
            fy = point.get('fy', '')  # Fiscal year
            fp = point.get('fp', '')  # Fiscal period (FY, Q1, Q2, Q3, Q4)
            filed_date = point.get('filed', '')
            
            # Extract calendar year from end date
            calendar_year = None
            if end_date:
                try:
                    calendar_year = int(end_date[:4])
                except (ValueError, IndexError):
                    pass
            
            if calendar_year is None:
                logger.debug(f"  Skipping: {indicator} at {end_date} - no valid calendar year from end date")
                continue
            
            # Create grouping key: (calendar_year, indicator)
            # We don't use fy in the group key because SEC API can return data with same end date but different fy values
            # e.g., Apple FY2024 (ends 2024-09-28) may have fy=2024 and fy=2025 in different records
            # We handle this by prioritizing FY data over quarterly data when they have the same calendar year
            group_key = (calendar_year, indicator)
            
            # Parse filed date for comparison
            try:
                filed_datetime = TimeProcessor.parse_date(filed_date) if filed_date else None
            except (ValueError, KeyError):
                filed_datetime = None
            
            # Check if new point is FY (annual) data - annual data takes priority
            is_new_fy = (fp == 'FY')
            
            if group_key in grouped_data:
                existing_point = grouped_data[group_key]
                existing_filed = existing_point.get('filed', '')
                existing_end = existing_point.get('end', '')
                existing_fp = existing_point.get('fp', '')
                is_existing_fy = (existing_fp == 'FY')
                
                # Priority decision:
                # 1. If new is FY and existing is not FY, always replace (annual > quarterly)
                # 2. If existing is FY and new is not FY, keep existing (annual > quarterly)
                # 3. If both are same type (both FY or both quarterly), use filed date
                if is_new_fy and not is_existing_fy:
                    grouped_data[group_key] = point
                    logger.debug(f"  Replacing: CY:{calendar_year}, {indicator} at {end_date} - FY data takes priority over quarterly")
                    continue
                elif is_existing_fy and not is_new_fy:
                    logger.debug(f"  Keeping existing: CY:{calendar_year}, {indicator} at {existing_end} - existing is FY, new is quarterly")
                    continue
                
                # Both are same type - use filed date for decision
                try:
                    existing_filed_datetime = TimeProcessor.parse_date(existing_filed) if existing_filed else None
                except (ValueError, KeyError):
                    existing_filed_datetime = None
                
                # Decision: keep the one with later filed date (most recent revision)
                if filed_datetime and existing_filed_datetime:
                    if filed_datetime > existing_filed_datetime:
                        grouped_data[group_key] = point
                        logger.debug(f"  Replacing: CY:{calendar_year}, {indicator} at {end_date} - newer filed date: {filed_date} > {existing_filed}")
                    else:
                        logger.debug(f"  Keeping existing: CY:{calendar_year}, {indicator} at {end_date} - older filed date: {filed_date} <= {existing_filed}")
                elif filed_datetime and not existing_filed_datetime:
                    grouped_data[group_key] = point
                    logger.debug(f"  Replacing: CY:{calendar_year}, {indicator} at {end_date} - has filed date: {filed_date}")
                elif not filed_datetime and existing_filed_datetime:
                    logger.debug(f"  Keeping existing: CY:{calendar_year}, {indicator} at {end_date} - existing has filed date: {existing_filed}")
                else:
                    # Neither has filed date, keep existing (prefer later end date)
                    if end_date > existing_end:
                        grouped_data[group_key] = point
                        logger.debug(f"  Replacing: CY:{calendar_year}, {indicator} at {end_date} - later end date: {end_date} > {existing_end}")
                    else:
                        logger.debug(f"  Keeping existing: CY:{calendar_year}, {indicator} at {end_date} - neither has filed date")
            else:
                grouped_data[group_key] = point
                logger.debug(f"  Adding: CY:{calendar_year}, {indicator} at {end_date}, fp={fp} - filed: {filed_date}")
        
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
        elif annual_only:
            # Annual only mode: we already filtered using TimeProcessor.filter_data_points with annual_only=True
            # which correctly uses frame to filter annual data
            # So we don't need additional filtering here - just log the result
            logger.debug(f"Income statement after annual_only filter: {len(filtered_data)} data points (annual data from TimeProcessor)")
        else:
            # Income statement: filter based on accumulated flag
            if accumulated:
                # Keep only accumulated data (Frame is empty or None)
                filtered_data = [point for point in filtered_data if not point.get('frame')]
                logger.debug(f"Income statement after accumulated filter: {len(filtered_data)} data points (accumulated data only)")
            else:
                # Keep only quarterly data (Frame is not empty) AND fiscal period is not FY
                # This ensures we don't include annual FY data when requesting quarterly data
                # But we need to handle Q4 specially - if there's no Q4 quarterly data, we should calculate it
                quarterly_data = []
                fy_data_by_indicator = {}
                q3_accumulated_data_by_indicator = {}
                
                # First pass: collect data
                for point in filtered_data:
                    fp = point.get('fp', '')
                    frame = point.get('frame', '')
                    indicator = point.get('indicator', '')
                    end = point.get('end', '')
                    
                    if fp == 'FY' and '12-31' in end:
                        # This is annual FY data (year-end)
                        # Extract year from end date
                        year = end.split('-')[0] if end else ''
                        key = (indicator, year)
                        fy_data_by_indicator[key] = point
                        logger.debug(f"FY data for {indicator} at {end}: fp={fp}, frame={frame}, year={year}")
                    elif fp == 'Q3' and not frame:
                        # This is Q3 accumulated data (Q1+Q2+Q3)
                        # Extract year from end date
                        year = end.split('-')[0] if end else ''
                        key = (indicator, year)
                        # For Q3 accumulated data, keep the one with MAXIMUM value
                        # This ensures we keep true accumulated data (Q1+Q2+Q3) over single-quarter data
                        current_val = float(point.get('val', 0))
                        if key in q3_accumulated_data_by_indicator:
                            existing_val = float(q3_accumulated_data_by_indicator[key].get('val', 0))
                            if current_val > existing_val:
                                q3_accumulated_data_by_indicator[key] = point
                                logger.debug(f"Q3 accumulated data for {indicator} at {end}: fp={fp}, frame={frame}, year={year} (updated with higher value {current_val})")
                        else:
                            q3_accumulated_data_by_indicator[key] = point
                            logger.debug(f"Q3 accumulated data for {indicator} at {end}: fp={fp}, frame={frame}, year={year}")
                    elif frame and fp != 'FY':
                        # This is regular quarterly data
                        quarterly_data.append(point)
                
                logger.debug(f"Found {len(quarterly_data)} quarterly data points, {len(fy_data_by_indicator)} FY data points, {len(q3_accumulated_data_by_indicator)} Q3 accumulated data points")
                logger.debug(f"FY data indicators: {list(fy_data_by_indicator.keys())}")
                logger.debug(f"Q3 accumulated data indicators: {list(q3_accumulated_data_by_indicator.keys())}")
                
                # Second pass: calculate Q4 data if missing
                for (indicator, year_key), fy_point in fy_data_by_indicator.items():
                    # Check if we already have Q4 data for this indicator and year
                    has_q4 = False
                    for q_point in quarterly_data:
                        if (q_point.get('indicator') == indicator and 
                            q_point.get('end', '').endswith('12-31') and
                            q_point.get('end', '').startswith(year_key)):
                            has_q4 = True
                            logger.debug(f"Indicator {indicator} already has Q4 data at {q_point.get('end')}")
                            break
                    
                    q3_key = (indicator, year_key)
                    if not has_q4 and q3_key in q3_accumulated_data_by_indicator:
                        # Calculate Q4 = FY - Q3 accumulated
                        try:
                            fy_value = float(fy_point.get('val', 0))
                            q3_accumulated_value = float(q3_accumulated_data_by_indicator[q3_key].get('val', 0))
                            q4_value = fy_value - q3_accumulated_value
                            
                            # Create Q4 data point (allow negative values for expenses)
                            q4_point = fy_point.copy()
                            q4_point['val'] = q4_value
                            q4_point['fp'] = 'Q4'
                            
                            # Determine correct frame based on year
                            end_date = fy_point.get('end', '')
                            if '2024' in end_date:
                                q4_point['frame'] = 'CY2024Q4'
                            elif '2025' in end_date:
                                q4_point['frame'] = 'CY2025Q4'
                            else:
                                # Extract year from date
                                year = end_date.split('-')[0]
                                q4_point['frame'] = f'CY{year}Q4'
                            
                            q4_point['form'] = '10-K'  # Derived from 10-K
                            
                            logger.debug(f"Calculated Q4 data for {indicator} year {year_key}: FY={fy_value}, Q3_accumulated={q3_accumulated_value}, Q4={q4_value}")
                            quarterly_data.append(q4_point)
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Failed to calculate Q4 data for {indicator} year {year_key}: {e}")
                    elif not has_q4:
                        logger.debug(f"Indicator {indicator} year {year_key} has no Q3 accumulated data, cannot calculate Q4")
                
                # Special handling for Revenues indicator
                # If we have RevenueFromContractWithCustomerExcludingAssessedTax Q4 data but not Revenues Q4 data,
                # we can use the RevenueFromContractWithCustomerExcludingAssessedTax Q4 data for Revenues
                # Also handle the case where Revenues has Q3 accumulated data but no Q4 data
                # We need to check for each year separately
                for (indicator, year_key), fy_point in fy_data_by_indicator.items():
                    if indicator == 'Revenues':
                        # Check if we already have Revenues Q4 data for this year
                        fy_end_date = fy_point.get('end', '')
                        fy_year = year_key
                        
                        logger.debug(f"Checking Revenues Q4 data for year {fy_year}, fy_end_date={fy_end_date}")
                        
                        has_revenues_q4_for_year = False
                        for q_point in quarterly_data:
                            if (q_point.get('indicator') == 'Revenues' and 
                                q_point.get('end', '').endswith('12-31') and
                                q_point.get('end', '').startswith(fy_year)):
                                has_revenues_q4_for_year = True
                                logger.debug(f"Found Revenues Q4 data for year {fy_year}: {q_point.get('end')}")
                                break
                        
                        if not has_revenues_q4_for_year:
                            logger.debug(f"No Revenues Q4 data found for year {fy_year}, looking for RevenueFromContractWithCustomerExcludingAssessedTax Q4 data")
                            # Try to find RevenueFromContractWithCustomerExcludingAssessedTax Q4 data for the same year
                            for q_point in quarterly_data:
                                logger.debug(f"Checking quarterly data point: indicator={q_point.get('indicator')}, end={q_point.get('end')}, fp={q_point.get('fp')}")
                                if (q_point.get('indicator') == 'RevenueFromContractWithCustomerExcludingAssessedTax' and 
                                    q_point.get('end', '').endswith('12-31') and
                                    q_point.get('end', '').startswith(fy_year) and
                                    q_point.get('fp') == 'Q4'):
                                    # Use this data for Revenues as well
                                    revenues_q4_point = q_point.copy()
                                    revenues_q4_point['indicator'] = 'Revenues'
                                    revenues_q4_point['label'] = 'Revenues'
                                    quarterly_data.append(revenues_q4_point)
                                    logger.debug(f"Using RevenueFromContractWithCustomerExcludingAssessedTax Q4 data for Revenues indicator for year {fy_year}")
                                    break
                            else:
                                # If no RevenueFromContractWithCustomerExcludingAssessedTax Q4 data, try to calculate Revenues Q4
                                logger.debug(f"No RevenueFromContractWithCustomerExcludingAssessedTax Q4 data found for year {fy_year}")
                                q3_key = ('Revenues', fy_year)
                                if q3_key in q3_accumulated_data_by_indicator:
                                    try:
                                        fy_value = float(fy_point.get('val', 0))
                                        q3_accumulated_value = float(q3_accumulated_data_by_indicator[q3_key].get('val', 0))
                                        q4_value = fy_value - q3_accumulated_value
                                        
                                        # Create Q4 data point
                                        q4_point = fy_point.copy()
                                        q4_point['val'] = q4_value
                                        q4_point['fp'] = 'Q4'
                                        
                                        # Determine correct frame based on year
                                        end_date = q4_point.get('end', '')
                                        if '2024' in end_date:
                                            q4_point['frame'] = 'CY2024Q4'
                                        elif '2025' in end_date:
                                            q4_point['frame'] = 'CY2025Q4'
                                        else:
                                            # Extract year from date
                                            year = end_date.split('-')[0]
                                            q4_point['frame'] = f'CY{year}Q4'
                                        
                                        q4_point['form'] = '10-K'  # Derived from 10-K
                                        
                                        logger.debug(f"Calculated Revenues Q4 data for year {fy_year}: FY={fy_value}, Q3_accumulated={q3_accumulated_value}, Q4={q4_value}")
                                        quarterly_data.append(q4_point)
                                    except (ValueError, TypeError) as e:
                                        logger.warning(f"Failed to calculate Revenues Q4 data for year {fy_year}: {e}")
                                else:
                                    logger.debug(f"No Q3 accumulated data for Revenues year {fy_year}, cannot calculate Q4")
                
                filtered_data = quarterly_data
                logger.debug(f"Income statement after quarterly filter: {len(filtered_data)} data points (quarterly data with calculated Q4)")
        
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
            # IMPORTANT: Use calendar year (from end date) as 'Year' column for grouping
            # This is more reliable than using SEC API's 'fy' field which can be inconsistent
            date_str = data_point.get('end', '')
            if date_str:
                try:
                    date_obj = TimeProcessor.parse_date(date_str)
                    # Use calendar year from end date for grouping
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
