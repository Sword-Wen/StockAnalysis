#!/usr/bin/env python3
"""
Main entry point for SEC Financial Data Extractor
Command-line interface for fetching and exporting financial statements
"""

import argparse
import sys
import logging
import json
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import local modules
from .client import SECClient
from .ticker_mapper import TickerMapper
from .data_extractor import DataExtractor
from .time_processor import TimeProcessor
from .csv_exporter import CSVExporter
from .config import USER_AGENT


class SECFinancialExtractor:
    """Main class for extracting financial data from SEC"""
    
    def __init__(self, user_agent: Optional[str] = None, proxy_url: Optional[str] = None):
        """Initialize the extractor"""
        self.user_agent = user_agent or USER_AGENT
        self.proxy_url = proxy_url
        self.client = SECClient(user_agent=self.user_agent, proxy_url=self.proxy_url)
        self.ticker_mapper = TickerMapper()
        self.data_extractor = DataExtractor()
    
    def fetch_financial_data(
        self,
        ticker: str,
        year: Optional[int] = None,
        quarter: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
        output_dir: str = "output",
        format_for_csv: bool = True,
        accumulated: bool = False,
        annual_only: bool = False
    ) -> dict:
        """
        Main method to fetch and process financial data
        
        Args:
            ticker: Stock ticker symbol
            year: Specific year
            quarter: Specific quarter (1-4)
            start_year: Start year for range
            end_year: End year for range
            start_quarter: Start quarter for range
            end_quarter: End quarter for range
            output_dir: Output directory for CSV files
            format_for_csv: Whether to format data for CSV export
            accumulated: Whether to use accumulated data (Nine Months Ended) instead of quarterly data
            annual_only: Whether to keep only annual data (FY) when filtering by year
            
        Returns:
            Dictionary with results and file paths
        """
        # Validate time parameters
        is_valid, error_msg = TimeProcessor.validate_time_parameters(
            year=year,
            quarter=quarter,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter
        )
        
        if not is_valid:
            raise ValueError(f"Invalid time parameters: {error_msg}")
        
        # Convert ticker to CIK
        logger.info(f"Looking up CIK for ticker: {ticker}")
        cik = self.ticker_mapper.ticker_to_cik(ticker)
        
        if not cik:
            raise ValueError(f"Ticker '{ticker}' not found in SEC database")
        
        logger.info(f"Found CIK {cik} for ticker {ticker}")
        
        # Fetch company data from SEC API
        logger.info(f"Fetching financial data for {ticker} (CIK: {cik})")
        company_data = self.client.get_company_facts(cik)
        
        # Extract financial statements
        logger.info("Extracting financial statements...")
        statements = self.data_extractor.extract_financial_statements(
            company_data,
            year=year,
            quarter=quarter,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
            accumulated=accumulated,
            annual_only=annual_only
        )
        
        # Check if we got any data
        total_points = sum(len(stmt) for stmt in statements.values())
        if total_points == 0:
            logger.warning(f"No financial data found for {ticker} with the specified parameters")
        
        # Format data for CSV if requested
        formatted_statements = {}
        if format_for_csv:
            for stmt_type, stmt_data in statements.items():
                formatted_statements[stmt_type] = self.data_extractor.format_data_for_csv(stmt_data)
        
        # Export to CSV
        logger.info("Exporting to CSV files...")
        if format_for_csv:
            exported_files = CSVExporter.export_formatted_statements(
                formatted_statements,
                ticker,
                output_dir=output_dir,
                year=year,
                quarter=quarter,
                start_year=start_year,
                end_year=end_year
            )
        else:
            exported_files = CSVExporter.export_statements(
                statements,
                ticker,
                output_dir=output_dir,
                year=year,
                quarter=quarter,
                start_year=start_year,
                end_year=end_year
            )
        
        # Create summary report
        summary_path = CSVExporter.create_summary_report(exported_files, output_dir)
        
        # Get available indicators info
        available_indicators = self.data_extractor.get_available_indicators(company_data)
        
        # Prepare result
        result = {
            'ticker': ticker,
            'cik': cik,
            'company_name': company_data.get('entityName', '').replace('\\', ''),
            'statements_found': {
                'balance_sheet': len(statements['balance_sheet']),
                'income_statement': len(statements['income_statement']),
                'cash_flow': len(statements['cash_flow'])
            },
            'exported_files': exported_files,
            'summary_report': summary_path,
            'available_indicators': available_indicators.get('configured', {}),
            'total_indicators': available_indicators.get('total_count', 0),
            'time_parameters': {
                'year': year,
                'quarter': quarter,
                'start_year': start_year,
                'end_year': end_year,
                'start_quarter': start_quarter,
                'end_quarter': end_quarter
            },
            'accumulated': accumulated,
            'annual_only': annual_only
        }
        
        return result
    
    def search_tickers(self, query: str, limit: int = 10) -> dict:
        """
        Search for tickers by partial match
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            Dictionary of search results
        """
        results = self.ticker_mapper.search_tickers(query, limit)
        return {
            'query': query,
            'results': results,
            'count': len(results)
        }
    
    def get_mapping_stats(self) -> dict:
        """Get statistics about ticker-CIK mapping"""
        return self.ticker_mapper.get_mapping_stats()
    
    def clear_cache(self, cik: Optional[str] = None):
        """Clear cache for specific CIK or all cache"""
        self.client.clear_cache(cik)


def main():
    """Main command-line interface"""
    parser = argparse.ArgumentParser(
        description='Fetch US stock financial statements from SEC REST API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s AAPL --year 2023
  %(prog)s MSFT --year 2023 --quarter 4
  %(prog)s GOOGL --start-year 2020 --end-year 2023
  %(prog)s AMZN --start-year 2021 --start-quarter 1 --end-year 2023 --end-quarter 4
  %(prog)s GOOG --year 2025 --quarter 3 --accumulated  # 使用累计数据（截至Q3的9个月合计）
  %(prog)s META --start-year 2024 --end-year 2025 --annual-only  # 只获取年度数据（FY）
  %(prog)s search AAP --limit 5
  %(prog)s stats
        """
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch financial data for a ticker')
    fetch_parser.add_argument('ticker', help='Stock ticker symbol (e.g., AAPL)')
    
    # Time filtering options
    fetch_parser.add_argument('--year', type=int, help='Specific year to fetch')
    fetch_parser.add_argument('--quarter', type=int, choices=[1, 2, 3, 4], 
                          help='Specific quarter (requires --year)')
    fetch_parser.add_argument('--start-year', type=int, help='Start year for range')
    fetch_parser.add_argument('--end-year', type=int, help='End year for range')
    fetch_parser.add_argument('--start-quarter', type=int, choices=[1, 2, 3, 4],
                            help='Start quarter for range (requires --start-year)')
    fetch_parser.add_argument('--end-quarter', type=int, choices=[1, 2, 3, 4],
                            help='End quarter for range (requires --end-year)')
    
    fetch_parser.add_argument('--output-dir', default='output', help='Output directory for CSV files')
    fetch_parser.add_argument('--user-agent', help='Custom User-Agent string for SEC API')
    fetch_parser.add_argument('--proxy', help='Proxy URL (e.g., http://127.0.0.1:10808)')
    fetch_parser.add_argument('--accumulated', action='store_true', 
                            help='Use accumulated data (Nine Months Ended) instead of quarterly data')
    fetch_parser.add_argument('--annual-only', action='store_true',
                            help='Keep only annual data (FY) when filtering by year')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for tickers')
    search_parser.add_argument('query', help='Search query (partial ticker match)')
    search_parser.add_argument('--limit', type=int, default=10, help='Maximum number of results')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show ticker mapping statistics')
    
    # Clear cache command
    clear_parser = subparsers.add_parser('clear-cache', help='Clear cached data')
    clear_parser.add_argument('--cik', help='Specific CIK to clear cache for')
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    try:
        extractor = SECFinancialExtractor(
            user_agent=args.user_agent if hasattr(args, 'user_agent') else None,
            proxy_url=args.proxy if hasattr(args, 'proxy') else None
        )
        
        if args.command == 'fetch':
            # Validate quarter parameters
            if args.quarter and not args.year:
                fetch_parser.error("--quarter requires --year")
            if args.start_quarter and not args.start_year:
                fetch_parser.error("--start-quarter requires --start-year")
            if args.end_quarter and not args.end_year:
                fetch_parser.error("--end-quarter requires --end-year")
            
            # Determine if annual_only should be enabled by default
            # Default to True when using year range mode (start_year and end_year specified)
            # unless explicitly overridden by --annual-only
            default_annual_only = False
            
            # If using year range mode without quarter specification, default to annual_only
            if args.start_year is not None and args.end_year is not None:
                # Year range mode
                if args.start_quarter is None and args.end_quarter is None:
                    # No quarter range specified, default to annual_only
                    default_annual_only = True
            
            # If using single year mode without quarter, also default to annual_only
            elif args.year is not None and args.quarter is None:
                # Single year mode without quarter, default to annual_only
                default_annual_only = True
            
            # IMPORTANT: If user explicitly requests quarter range (e.g., Q1-Q4), 
            # we should NOT default to annual_only, even if they didn't specify --annual-only
            # This ensures quarterly data is returned when quarter range is specified
            if args.start_quarter is not None and args.end_quarter is not None:
                # User explicitly requested quarter range, don't default to annual_only
                default_annual_only = False
            
            # Use explicit --annual-only flag if provided, otherwise use default
            # Note: args.annual_only will be True if --annual-only is specified, False otherwise
            # We need to check if it was explicitly set to True
            if hasattr(args, 'annual_only') and args.annual_only:
                # User explicitly requested annual_only
                annual_only_value = True
            else:
                # Use default behavior
                annual_only_value = default_annual_only
            
            # Fetch financial data
            result = extractor.fetch_financial_data(
                ticker=args.ticker,
                year=args.year,
                quarter=args.quarter,
                start_year=args.start_year,
                end_year=args.end_year,
                start_quarter=args.start_quarter,
                end_quarter=args.end_quarter,
                output_dir=args.output_dir,
                accumulated=args.accumulated if hasattr(args, 'accumulated') else False,
                annual_only=annual_only_value
            )
            
            # Print summary
            print("\n" + "="*60)
            print("SEC Financial Data Export Complete")
            print("="*60)
            print(f"Company: {result['company_name']} ({result['ticker']})")
            print(f"CIK: {result['cik']}")
            print(f"\nData Points Found:")
            print(f"  Balance Sheet: {result['statements_found']['balance_sheet']}")
            print(f"  Income Statement: {result['statements_found']['income_statement']}")
            print(f"  Cash Flow: {result['statements_found']['cash_flow']}")
            print(f"\nExported Files:")
            for stmt_type, filepath in result['exported_files'].items():
                stmt_name = stmt_type.replace('_', ' ').title()
                print(f"  {stmt_name}: {filepath}")
            
            if result['summary_report']:
                print(f"\nSummary Report: {result['summary_report']}")
            
            print(f"\nAvailable GAAP Indicators: {result['total_indicators']}")
            print("="*60)
            
            # Also print as JSON for programmatic use
            print("\nJSON Output:")
            print(json.dumps(result, indent=2, default=str))
            
        elif args.command == 'search':
            results = extractor.search_tickers(args.query, args.limit)
            print(f"\nSearch Results for '{args.query}':")
            print("-" * 40)
            if results['results']:
                for ticker, cik in results['results'].items():
                    print(f"{ticker}: CIK {cik}")
                print(f"\nTotal matches: {results['count']}")
            else:
                print("No matches found")
                
        elif args.command == 'stats':
            stats = extractor.get_mapping_stats()
            print("\nTicker-CIK Mapping Statistics:")
            print("-" * 40)
            print(f"Total Tickers: {stats['total_tickers']:,}")
            print(f"Total CIKs: {stats['total_ciks']:,}")
            
        elif args.command == 'clear-cache':
            extractor.clear_cache(args.cik)
            if args.cik:
                print(f"Cleared cache for CIK {args.cik}")
            else:
                print("Cleared all cache files")
                
        else:
            parser.print_help()
            
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        logger.exception("Unexpected error occurred")
        sys.exit(1)


if __name__ == '__main__':
    main()