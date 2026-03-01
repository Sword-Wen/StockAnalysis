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