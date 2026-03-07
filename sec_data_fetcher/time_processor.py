"""
Time range processor for financial data filtering
"""

from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
import logging

from .config import QUARTER_MONTHS

logger = logging.getLogger(__name__)


class TimeProcessor:
    """Processes time ranges for financial data filtering"""
    
    @staticmethod
    def parse_date(date_str: str) -> datetime:
        """
        Parse date string to datetime
        
        Args:
            date_str: Date string in format 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SSZ'
            
        Returns:
            datetime object
        """
        # Remove timezone and time part if present
        if 'T' in date_str:
            date_str = date_str.split('T')[0]
        
        return datetime.strptime(date_str, '%Y-%m-%d')
    
    @staticmethod
    def get_year_quarter(date: datetime) -> Tuple[int, int]:
        """
        Get year and quarter from date
        
        Args:
            date: datetime object
            
        Returns:
            Tuple of (year, quarter)
        """
        month = date.month
        year = date.year
        
        for quarter, (start_month, end_month) in QUARTER_MONTHS.items():
            if start_month <= month <= end_month:
                return year, quarter
        
        # Should never reach here
        return year, 4
    
    @staticmethod
    def filter_by_year(
        data_points: List[Dict[str, Any]],
        year: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter data points by year or year range
        
        Args:
            data_points: List of data point dictionaries
            year: Specific year to filter (mutually exclusive with start_year/end_year)
            start_year: Start year for range
            end_year: End year for range
            
        Returns:
            Filtered list of data points
        """
        if not data_points:
            return []
        
        filtered_points = []
        
        for point in data_points:
            if 'end' not in point:
                continue
            
            try:
                end_date = TimeProcessor.parse_date(point['end'])
                point_year = end_date.year
                
                if year is not None:
                    # Single year mode
                    if point_year == year:
                        filtered_points.append(point)
                elif start_year is not None and end_year is not None:
                    # Year range mode
                    if start_year <= point_year <= end_year:
                        filtered_points.append(point)
                else:
                    # No year filter
                    filtered_points.append(point)
                    
            except (ValueError, KeyError) as e:
                logger.warning(f"Error parsing date in data point: {e}")
                continue
        
        return filtered_points
    
    @staticmethod
    def filter_by_quarter(
        data_points: List[Dict[str, Any]],
        year: Optional[int] = None,
        quarter: Optional[int] = None,
        start_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_year: Optional[int] = None,
        end_quarter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter data points by quarter or quarter range
        
        Args:
            data_points: List of data point dictionaries
            year: Specific year for single quarter mode
            quarter: Specific quarter (1-4) for single quarter mode
            start_year: Start year for quarter range
            start_quarter: Start quarter (1-4) for quarter range
            end_year: End year for quarter range
            end_quarter: End quarter (1-4) for quarter range
            
        Returns:
            Filtered list of data points
        """
        if not data_points:
            return []
        
        filtered_points = []
        
        for point in data_points:
            if 'end' not in point:
                continue
            
            try:
                end_date = TimeProcessor.parse_date(point['end'])
                point_year, point_quarter = TimeProcessor.get_year_quarter(end_date)
                
                if year is not None and quarter is not None:
                    # Single quarter mode
                    if point_year == year and point_quarter == quarter:
                        filtered_points.append(point)
                elif start_year is not None and start_quarter is not None and \
                     end_year is not None and end_quarter is not None:
                    # Quarter range mode
                    start_date_num = start_year * 10 + start_quarter
                    end_date_num = end_year * 10 + end_quarter
                    point_date_num = point_year * 10 + point_quarter
                    
                    if start_date_num <= point_date_num <= end_date_num:
                        filtered_points.append(point)
                else:
                    # No quarter filter
                    filtered_points.append(point)
                    
            except (ValueError, KeyError) as e:
                logger.warning(f"Error parsing date in data point: {e}")
                continue
        
        return filtered_points
    
    @staticmethod
    def filter_data_points(
        data_points: List[Dict[str, Any]],
        year: Optional[int] = None,
        quarter: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
        annual_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Main filtering function that handles all time filtering modes
        
        Args:
            data_points: List of data point dictionaries
            year: Specific year
            quarter: Specific quarter (1-4)
            start_year: Start year for range
            end_year: End year for range
            start_quarter: Start quarter for range
            end_quarter: End quarter for range
            annual_only: Whether to keep only annual data (FY) when filtering by year
            
        Returns:
            Filtered list of data points
        """
        if not data_points:
            return []
        
        # Determine filtering mode
        if quarter is not None:
            # Quarter mode (single quarter or quarter range)
            if start_quarter is not None and end_quarter is not None:
                # Quarter range mode
                return TimeProcessor.filter_by_quarter(
                    data_points,
                    start_year=start_year,
                    start_quarter=start_quarter,
                    end_year=end_year,
                    end_quarter=end_quarter
                )
            else:
                # Single quarter mode
                return TimeProcessor.filter_by_quarter(
                    data_points,
                    year=year,
                    quarter=quarter
                )
        elif year is not None or (start_year is not None and end_year is not None):
            # Year mode (single year or year range)
            # First filter by year
            year_filtered = TimeProcessor.filter_by_year(
                data_points,
                year=year,
                start_year=start_year,
                end_year=end_year
            )
            
            logger.debug(f"Year filtered: {len(year_filtered)} data points after year filter")
            
            # Then filter to keep only annual data (not quarterly) when annual_only is True
            # or when year is specified without quarter AND without quarter range (backward compatibility)
            # This ensures that when user explicitly requests quarter range (e.g., Q1-Q4), we don't filter out quarterly data
            should_apply_annual_filter = annual_only or (
                year is not None and quarter is None and 
                start_quarter is None and end_quarter is None
            )
            
            if should_apply_annual_filter:
                # Keep only annual data points (frame indicates annual)
                annual_data = []
                for point in year_filtered:
                    frame = point.get('frame', '')
                    indicator = point.get('indicator', 'Unknown')
                    end_date = point.get('end', '')
                    fp = point.get('fp', '')  # Fiscal period
                    fy = point.get('fy', '')  # Fiscal year
                    
                    # Debug logging
                    logger.debug(f"Annual filter: {indicator}, frame={frame}, end={end_date}, fp={fp}, fy={fy}, year={year}")
                    
                    # Check for annual data points
                    # 1. End date is Dec 31 (year end)
                    if end_date and end_date.endswith('12-31'):
                        logger.debug(f"  Accepted (year end): {indicator}, end={end_date}")
                        annual_data.append(point)
                        continue
                    
                    # 2. Frame indicates annual data
                    if frame:
                        # Remove 'I' suffix if present (instant)
                        frame_clean = frame.replace('I', '')
                        # Debug logging for frame analysis
                        logger.debug(f"  Frame analysis: {frame} -> {frame_clean}, ends with Q4={frame_clean.endswith('Q4')}, CY{year}={frame_clean == f'CY{year}'}")
                        # Check if it's annual: either just CY{year} or ends with Q4
                        if frame_clean == f'CY{year}' or frame_clean.endswith('Q4'):
                            logger.debug(f"  Accepted (annual frame): {indicator}, frame_clean={frame_clean}")
                            annual_data.append(point)
                            continue
                    
                    # 3. Fiscal period is FY (annual)
                    if fp == 'FY' and (fy == str(year) if year is not None else True):
                        logger.debug(f"  Accepted (fiscal year): {indicator}, fp={fp}, fy={fy}")
                        annual_data.append(point)
                        continue
                    
                    # 4. Frame is exactly the year (e.g., '2025')
                    if frame == str(year) and year is not None:
                        logger.debug(f"  Accepted (year frame): {indicator}, frame={frame}")
                        annual_data.append(point)
                        continue
                    
                    logger.debug(f"  Rejected (not annual): {indicator}, frame={frame}, end={end_date}, fp={fp}, fy={fy}")
                logger.debug(f"Annual filter result: {len(annual_data)} data points")
                return annual_data
            
            return year_filtered
        else:
            # No time filter
            return data_points
    
    @staticmethod
    def validate_time_parameters(
        year: Optional[int] = None,
        quarter: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Validate time parameters for consistency
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check quarter validity
        if quarter is not None and (quarter < 1 or quarter > 4):
            return False, f"Quarter must be between 1 and 4, got {quarter}"
        
        if start_quarter is not None and (start_quarter < 1 or start_quarter > 4):
            return False, f"Start quarter must be between 1 and 4, got {start_quarter}"
        
        if end_quarter is not None and (end_quarter < 1 or end_quarter > 4):
            return False, f"End quarter must be between 1 and 4, got {end_quarter}"
        
        # Check year validity
        current_year = datetime.now().year
        if year is not None and (year < 1900 or year > current_year + 1):
            return False, f"Year must be between 1900 and {current_year + 1}, got {year}"
        
        if start_year is not None and (start_year < 1900 or start_year > current_year + 1):
            return False, f"Start year must be between 1900 and {current_year + 1}, got {start_year}"
        
        if end_year is not None and (end_year < 1900 or end_year > current_year + 1):
            return False, f"End year must be between 1900 and {current_year + 1}, got {end_year}"
        
        # Check range consistency
        if start_year is not None and end_year is not None:
            if start_year > end_year:
                return False, f"Start year ({start_year}) cannot be after end year ({end_year})"
            
            if start_quarter is not None and end_quarter is not None:
                if start_year == end_year and start_quarter > end_quarter:
                    return False, f"Start quarter ({start_quarter}) cannot be after end quarter ({end_quarter}) in same year"
        
        # Check parameter combinations
        if quarter is not None and year is None:
            return False, "Quarter parameter requires year parameter"
        
        if start_quarter is not None and start_year is None:
            return False, "Start quarter parameter requires start year parameter"
        
        if end_quarter is not None and end_year is None:
            return False, "End quarter parameter requires end year parameter"
        
        if (start_quarter is not None and end_quarter is None) or \
           (start_quarter is None and end_quarter is not None):
            return False, "Both start_quarter and end_quarter must be specified together"
        
        return True, ""