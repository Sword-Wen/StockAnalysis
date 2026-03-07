"""
CSV exporter for financial statement data
"""

import csv
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CSVExporter:
    """Exports financial statement data to CSV files"""
    
    @staticmethod
    def export_statements(
        statements: Dict[str, List[Dict[str, Any]]],
        ticker: str,
        output_dir: str = ".",
        year: Optional[int] = None,
        quarter: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Export financial statements to CSV files
        
        Args:
            statements: Dictionary with 'balance_sheet', 'income_statement', 'cash_flow' keys
            ticker: Stock ticker symbol
            output_dir: Output directory for CSV files
            year: Specific year (for filename)
            quarter: Specific quarter (for filename)
            start_year: Start year (for filename)
            end_year: End year (for filename)
            
        Returns:
            Dictionary mapping statement type to file path
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename prefix
        filename_prefix = CSVExporter._generate_filename_prefix(
            ticker, year, quarter, start_year, end_year
        )
        
        exported_files = {}
        
        # Export each statement
        statement_types = {
            'balance_sheet': 'Balance Sheet',
            'income_statement': 'Income Statement',
            'cash_flow': 'Cash Flow'
        }
        
        for statement_key, statement_name in statement_types.items():
            if statement_key in statements and statements[statement_key]:
                filename = f"{filename_prefix}_{statement_name.replace(' ', '_')}.csv"
                filepath = os.path.join(output_dir, filename)
                
                try:
                    CSVExporter._export_to_csv(
                        statements[statement_key],
                        filepath,
                        statement_name
                    )
                    exported_files[statement_key] = filepath
                    logger.info(f"Exported {statement_name} to {filepath}")
                except Exception as e:
                    logger.error(f"Failed to export {statement_name}: {e}")
        
        return exported_files
    
    @staticmethod
    def _generate_filename_prefix(
        ticker: str,
        year: Optional[int] = None,
        quarter: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> str:
        """Generate filename prefix based on parameters"""
        ticker_upper = ticker.upper()
        
        if quarter is not None and year is not None:
            # Single quarter mode
            return f"{ticker_upper}_Q{quarter}_{year}"
        elif year is not None:
            # Single year mode
            return f"{ticker_upper}_{year}"
        elif start_year is not None and end_year is not None:
            # Year range mode
            return f"{ticker_upper}_{start_year}_{end_year}"
        else:
            # All data mode
            return f"{ticker_upper}_all_data"
    
    @staticmethod
    def _export_to_csv(
        data: List[Dict[str, Any]],
        filepath: str,
        statement_name: str
    ):
        """
        Export data to CSV file
        
        Args:
            data: List of data dictionaries
            filepath: Path to output CSV file
            statement_name: Name of the financial statement
        """
        if not data:
            logger.warning(f"No data to export for {statement_name}")
            return
        
        # Get all possible field names from data
        fieldnames = set()
        for item in data:
            fieldnames.update(item.keys())
        
        # Convert to list and sort for consistent output
        fieldnames = sorted(fieldnames)
        
        # Write to CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write data rows
            for item in data:
                # Ensure all fields are present in each row
                row = {field: item.get(field, '') for field in fieldnames}
                writer.writerow(row)
    
    @staticmethod
    def export_formatted_statements(
        formatted_statements: Dict[str, List[Dict[str, Any]]],
        ticker: str,
        output_dir: str = ".",
        year: Optional[int] = None,
        quarter: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Export pre-formatted statements to CSV files
        
        Args:
            formatted_statements: Dictionary with formatted statement data
            ticker: Stock ticker symbol
            output_dir: Output directory for CSV files
            year: Specific year (for filename)
            quarter: Specific quarter (for filename)
            start_year: Start year (for filename)
            end_year: End year (for filename)
            
        Returns:
            Dictionary mapping statement type to file path
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename prefix
        filename_prefix = CSVExporter._generate_filename_prefix(
            ticker, year, quarter, start_year, end_year
        )
        
        exported_files = {}
        
        # Export each statement
        statement_types = {
            'balance_sheet': 'Balance_Sheet',
            'income_statement': 'Income_Statement',
            'cash_flow': 'Cash_Flow'
        }
        
        for statement_key, statement_suffix in statement_types.items():
            if statement_key in formatted_statements:
                filename = f"{filename_prefix}_{statement_suffix}.csv"
                filepath = os.path.join(output_dir, filename)
                
                try:
                    if formatted_statements[statement_key]:
                        CSVExporter._export_formatted_to_csv(
                            formatted_statements[statement_key],
                            filepath
                        )
                    else:
                        # Create empty CSV with header only
                        CSVExporter._create_empty_csv_with_header(filepath, statement_suffix)
                    
                    exported_files[statement_key] = filepath
                    logger.info(f"Exported {statement_suffix.replace('_', ' ')} to {filepath}")
                except Exception as e:
                    logger.error(f"Failed to export {statement_suffix}: {e}")
        
        return exported_files
    
    @staticmethod
    def _create_empty_csv_with_header(filepath: str, statement_suffix: str):
        """
        Create an empty CSV file with header only
        
        Args:
            filepath: Path to output CSV file
            statement_suffix: Statement suffix for logging
        """
        # Standard fieldnames for formatted data (from data_extractor.format_data_for_csv)
        standard_fieldnames = [
            'Date', 'Indicator', 'Label', 'Value', 'Unit', 'Accumulated',
            'Fiscal Year', 'Fiscal Period', 'Form', 'Filed', 'Frame',
            'Company Name', 'Ticker', 'CIK', 'SIC', 'SIC Description',
            'Year', 'Month', 'Day', 'Quarter'
        ]
        
        # Write to CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=standard_fieldnames)
            writer.writeheader()
        
        logger.debug(f"Created empty CSV with header for {statement_suffix.replace('_', ' ')}")
    
    @staticmethod
    def _export_formatted_to_csv(
        formatted_data: List[Dict[str, Any]],
        filepath: str
    ):
        """
        Export formatted data to CSV file
        
        Args:
            formatted_data: List of formatted data dictionaries
            filepath: Path to output CSV file
        """
        if not formatted_data:
            logger.warning(f"No formatted data to export")
            return
        
        # Get fieldnames from first item
        if formatted_data:
            fieldnames = list(formatted_data[0].keys())
        
        # Write to CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write data rows
            for item in formatted_data:
                writer.writerow(item)
    
    @staticmethod
    def create_summary_report(
        exported_files: Dict[str, str],
        output_dir: str = "."
    ) -> Optional[str]:
        """
        Create a summary report of exported files
        
        Args:
            exported_files: Dictionary of exported file paths
            output_dir: Output directory for summary report
            
        Returns:
            Path to summary report file, or None if no files exported
        """
        if not exported_files:
            return None
        
        # Get ticker from first filename
        first_file = next(iter(exported_files.values()))
        ticker = os.path.basename(first_file).split('_')[0]
        
        # Create summary filename
        summary_filename = f"{ticker}_export_summary.txt"
        summary_path = os.path.join(output_dir, summary_filename)
        
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Write summary
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"SEC Financial Data Export Summary\n")
            f.write(f"==================================\n\n")
            f.write(f"Export Time: {timestamp}\n")
            f.write(f"Ticker: {ticker}\n\n")
            f.write(f"Exported Files:\n")
            f.write(f"---------------\n")
            
            for statement_type, filepath in exported_files.items():
                filename = os.path.basename(filepath)
                file_size = os.path.getsize(filepath)
                
                # Get row count
                row_count = 0
                try:
                    with open(filepath, 'r', encoding='utf-8') as csvfile:
                        row_count = sum(1 for _ in csvfile) - 1  # Subtract header
                except:
                    pass
                
                statement_name = statement_type.replace('_', ' ').title()
                f.write(f"\n{statement_name}:\n")
                f.write(f"  File: {filename}\n")
                f.write(f"  Size: {file_size:,} bytes\n")
                f.write(f"  Rows: {row_count:,}\n")
                f.write(f"  Path: {filepath}\n")
            
            f.write(f"\n\nTotal Files: {len(exported_files)}\n")
        
        logger.info(f"Created summary report at {summary_path}")
        return summary_path
    
    @staticmethod
    def export_pivot_table(
        formatted_statements: Dict[str, List[Dict[str, Any]]],
        ticker: str,
        period_type: str = 'annual',
        output_dir: str = "output",
        year: Optional[int] = None,
        quarter: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Dict[str, str]:
        """
        导出为透视表格式
        - 列：年份/季度（从左到右，由远及近）
        - 行：指标（简洁财报命名）
        - 值：数值
        
        Args:
            formatted_statements: Dictionary with formatted statement data
            ticker: Stock ticker symbol
            period_type: 'annual' or 'quarterly'
            output_dir: Output directory for CSV files
            year: Specific year (for filename)
            quarter: Specific quarter (for filename)
            start_year: Start year (for filename)
            end_year: End year (for filename)
            
        Returns:
            Dictionary mapping statement type to file path
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename prefix
        filename_prefix = CSVExporter._generate_filename_prefix(
            ticker, year, quarter, start_year, end_year
        )
        
        exported_files = {}
        
        # Export each statement as pivot table
        statement_types = {
            'balance_sheet': 'Balance_Sheet',
            'income_statement': 'Income_Statement',
            'cash_flow': 'Cash_Flow'
        }
        
        for statement_key, statement_suffix in statement_types.items():
            if statement_key in formatted_statements:
                filename = f"{filename_prefix}_{statement_suffix}_Pivot.csv"
                filepath = os.path.join(output_dir, filename)
                
                try:
                    if formatted_statements[statement_key]:
                        CSVExporter._export_pivot_to_csv(
                            formatted_statements[statement_key],
                            filepath,
                            period_type,
                            statement_key
                        )
                    else:
                        # 创建空的透视表CSV文件
                        CSVExporter._create_empty_pivot_csv(filepath, statement_suffix)
                    
                    exported_files[statement_key] = filepath
                    logger.info(f"Exported {statement_suffix.replace('_', ' ')} pivot table to {filepath}")
                except Exception as e:
                    logger.error(f"Failed to export {statement_suffix} pivot table: {e}")
        
        return exported_files
    
    @staticmethod
    def _export_pivot_to_csv(
        formatted_data: List[Dict[str, Any]],
        filepath: str,
        period_type: str = 'annual',
        statement_key: str = None
    ):
        """
        导出透视表到CSV文件
        
        Args:
            formatted_data: List of formatted data dictionaries
            filepath: Path to output CSV file
            period_type: 'annual' or 'quarterly'
            statement_key: Statement type key ('balance_sheet', 'income_statement', 'cash_flow')
        """
        if not formatted_data:
            logger.warning(f"No formatted data to export for pivot table")
            return
        
        # 导入指标简称映射和顺序
        from .config import INDICATOR_SHORT_NAMES, GAAP_INDICATORS
        
        # 获取该报表类型的指标顺序
        gaap_order = []
        if statement_key == 'balance_sheet':
            gaap_order = GAAP_INDICATORS.get('BalanceSheet', [])
        elif statement_key == 'income_statement':
            gaap_order = GAAP_INDICATORS.get('IncomeStatement', [])
        elif statement_key == 'cash_flow':
            gaap_order = GAAP_INDICATORS.get('CashFlowStatement', [])
        
        # 1. 数据去重：对于同一指标同一期间，取最新filed日期的记录
        deduplicated_data = CSVExporter._deduplicate_for_pivot(formatted_data)
        
        # 2. 转换为透视表格式
        pivot_data = CSVExporter._convert_to_pivot_table(
            deduplicated_data, 
            period_type,
            INDICATOR_SHORT_NAMES,
            gaap_order
        )
        
        if not pivot_data:
            logger.warning(f"No data to export after pivot conversion")
            return
        
        # 3. 写入CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # 获取所有列（第一列是指标，后续是期间列）
            all_periods = sorted(pivot_data['periods'])
            fieldnames = ['Indicator'] + all_periods
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # 写入每一行
            for indicator in pivot_data['indicators']:
                row = {'Indicator': indicator}
                for period in all_periods:
                    value = pivot_data['data'].get((indicator, period), '')
                    # 格式化数值：千分位分隔符，EPS保持小数格式
                    if isinstance(value, (int, float)) and value != '':
                        # 判断是否为EPS指标（以"EPS"开头）
                        if indicator.startswith('EPS'):
                            # EPS保持2位小数
                            row[period] = f"{value:.2f}"
                        else:
                            # 普通数值使用千分位分隔符，无小数位
                            row[period] = f"{value:,.0f}"
                    else:
                        row[period] = value
                writer.writerow(row)
    
    @staticmethod
    def _deduplicate_for_pivot(
        formatted_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        为透视表进行数据去重
        
        对于同一指标同一期间，取最新filed日期的记录
        如果filed日期相同，取最新的Fiscal Year
        
        Args:
            formatted_data: List of formatted data dictionaries
            
        Returns:
            Deduplicated list of data dictionaries
        """
        # 按(指标, 期间)分组
        grouped_data = {}
        
        for item in formatted_data:
            indicator = item.get('Indicator', '')
            date_str = item.get('Date', '')
            filed_date = item.get('Filed', '')
            fiscal_year = item.get('Fiscal Year', '')
            
            if not indicator or not date_str:
                continue
            
            # 提取年份
            try:
                year = int(date_str[:4])
                month = int(date_str[5:7])
                day = int(date_str[8:10])
                
                # 确定期间
                period_key = f"{year}-12-31"  # 年度数据
                
                # 季度数据：如果月份不是12月，则视为季度数据
                if month != 12:
                    quarter = (month - 1) // 3 + 1
                    period_key = f"{year}Q{quarter}"
            except (ValueError, IndexError):
                continue
            
            group_key = (indicator, period_key)
            
            # 解析filed日期
            try:
                filed_datetime = datetime.strptime(filed_date, "%Y-%m-%d") if filed_date else None
            except (ValueError, TypeError):
                filed_datetime = None
            
            # 如果这个组已经有数据，比较filed日期
            if group_key in grouped_data:
                existing_item = grouped_data[group_key]
                existing_filed = existing_item.get('Filed', '')
                existing_fiscal_year = existing_item.get('Fiscal Year', '')
                
                try:
                    existing_filed_datetime = datetime.strptime(existing_filed, "%Y-%m-%d") if existing_filed else None
                except (ValueError, TypeError):
                    existing_filed_datetime = None
                
                # 比较规则：
                # 1. 优先使用最新filed日期的记录
                # 2. 如果filed日期相同，使用最新的Fiscal Year
                should_replace = False
                
                if filed_datetime and existing_filed_datetime:
                    if filed_datetime > existing_filed_datetime:
                        should_replace = True
                    elif filed_datetime == existing_filed_datetime:
                        # filed日期相同，比较Fiscal Year
                        try:
                            if int(fiscal_year) > int(existing_fiscal_year):
                                should_replace = True
                        except (ValueError, TypeError):
                            pass
                elif filed_datetime and not existing_filed_datetime:
                    # 新记录有filed日期，旧记录没有，替换
                    should_replace = True
                
                if should_replace:
                    grouped_data[group_key] = item
            else:
                grouped_data[group_key] = item
        
        return list(grouped_data.values())
    
    @staticmethod
    def _convert_to_pivot_table(
        deduplicated_data: List[Dict[str, Any]],
        period_type: str,
        indicator_short_names: Dict[str, str],
        gaap_order: List[str] = None
    ) -> Dict[str, Any]:
        """
        将去重后的数据转换为透视表格式
        
        Args:
            deduplicated_data: Deduplicated list of data dictionaries
            period_type: 'annual' or 'quarterly'
            indicator_short_names: Dictionary mapping indicator names to short names
            gaap_order: List of indicator names in desired order
            
        Returns:
            Dictionary with 'periods', 'indicators', and 'data' keys
        """
        periods_set = set()
        indicators_set = set()
        data_dict = {}  # (indicator, period) -> value
        
        for item in deduplicated_data:
            indicator = item.get('Indicator', '')
            date_str = item.get('Date', '')
            value_str = item.get('Value', '')
            
            if not indicator or not date_str:
                continue
            
            # 获取指标简称
            short_name = indicator_short_names.get(indicator, indicator)
            
            try:
                year = int(date_str[:4])
                month = int(date_str[5:7])
                day = int(date_str[8:10])
                
                # 确定期间
                if period_type == 'annual':
                    # 年度数据：使用年份
                    period = str(year)
                else:
                    # 季度数据
                    quarter = (month - 1) // 3 + 1
                    period = f"{year}Q{quarter}"
                
                # 清理数值（移除千位分隔符和引号）
                # 首先确保value_str是字符串类型
                if value_str is not None and value_str != '':
                    # 如果已经是数值类型，直接使用
                    if isinstance(value_str, (int, float)):
                        value = float(value_str)
                    else:
                        # 移除引号
                        if isinstance(value_str, str) and value_str.startswith('"') and value_str.endswith('"'):
                            value_str = value_str[1:-1]
                        
                        # 移除千位分隔符
                        if isinstance(value_str, str):
                            value_str = value_str.replace(',', '')
                        
                        # 尝试转换为数值
                        try:
                            value = float(value_str)
                        except (ValueError, TypeError):
                            value = value_str if isinstance(value_str, str) else str(value_str)
                else:
                    value = ''
                
                periods_set.add(period)
                indicators_set.add(short_name)
                data_dict[(short_name, period)] = value
                
            except (ValueError, IndexError) as e:
                logger.warning(f"Error processing data point {indicator} at {date_str}: {e}")
                continue
        
        # 按顺序排序
        if period_type == 'annual':
            periods = sorted(periods_set, key=lambda x: int(x))
        else:
            # 季度数据排序：先按年份，再按季度
            periods = sorted(periods_set, key=lambda x: (int(x[:4]), int(x[5:])))
        
        # 使用GAAP顺序排序指标，如果没有顺序则按字母排序
        if gaap_order:
            # 创建short_name到原始indicator的映射（反向映射）
            short_to_original = {v: k for k, v in indicator_short_names.items()}
            
            # 对indicators_set进行排序：首先按gaap_order的顺序，然后是剩余的按字母顺序
            def sort_key(item):
                # 找到item对应的原始indicator名称
                original = short_to_original.get(item, item)
                # 查找在gaap_order中的位置
                if original in gaap_order:
                    return (0, gaap_order.index(original))
                elif item in gaap_order:
                    return (0, gaap_order.index(item))
                else:
                    return (1, item)  # 未在gaap_order中的排在后面
            
            indicators = sorted(indicators_set, key=sort_key)
        else:
            indicators = sorted(indicators_set)
        
        return {
            'periods': periods,
            'indicators': indicators,
            'data': data_dict
        }
    
    @staticmethod
    def _create_empty_pivot_csv(filepath: str, statement_suffix: str):
        """
        创建空的透视表CSV文件
        
        Args:
            filepath: Path to output CSV file
            statement_suffix: Statement suffix for logging
        """
        # 透视表只有Indicator列
        fieldnames = ['Indicator']
        
        # Write to CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        
        logger.debug(f"Created empty pivot CSV for {statement_suffix.replace('_', ' ')}")
