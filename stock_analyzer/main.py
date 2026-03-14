#!/usr/bin/env python3
"""
Main entry point for Stock Analyzer
Command-line interface for analyzing US stock financial data
"""

import argparse
import sys
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from .analyzer import StockAnalyzer
from .config import DEFAULT_YEARS, DEFAULT_OUTPUT_DIR


def main():
    """Main command-line interface"""
    parser = argparse.ArgumentParser(
        description='Analyze US stock financial data and generate core financial indicators',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s AAPL --function 1
  %(prog)s MSFT --function 1 --years 10 --output-dir output
  %(prog)s GOOGL --function 1 --years 5
        """
    )
    
    # Main arguments
    parser.add_argument('ticker', help='Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)')
    parser.add_argument('--function', type=int, default=1, 
                       help='Function to execute (1: Core financial indicators, default: 1)')
    parser.add_argument('--years', type=int, default=DEFAULT_YEARS,
                       help=f'Number of years of historical data (default: {DEFAULT_YEARS})')
    parser.add_argument('--output-dir', default=DEFAULT_OUTPUT_DIR,
                       help=f'Output directory for CSV files (default: {DEFAULT_OUTPUT_DIR})')
    parser.add_argument('--user-agent', help='Custom User-Agent string for SEC API')
    parser.add_argument('--proxy', help='Proxy URL (e.g., http://127.0.0.1:10808)')
    
    args = parser.parse_args()
    
    try:
        # Validate function parameter
        if args.function != 1:
            print(f"Error: Function {args.function} is not supported yet.")
            print("Currently only function 1 (Core financial indicators) is available.")
            sys.exit(1)
        
        # Initialize analyzer
        analyzer = StockAnalyzer(output_dir=args.output_dir)
        
        # Execute function 1: Core financial indicators
        if args.function == 1:
            print(f"\n{'='*60}")
            print(f"Stock Analyzer - Core Financial Indicators")
            print(f"{'='*60}")
            print(f"Ticker: {args.ticker.upper()}")
            print(f"Years: {args.years}")
            print(f"Output Directory: {args.output_dir}")
            print(f"{'='*60}\n")
            
            # Get financial indicators
            result = analyzer.get_financial_indicators(
                ticker=args.ticker,
                years=args.years
            )
            
            # Export to CSV
            output_file = analyzer.export_to_csv(
                ticker=args.ticker,
                indicators=result['indicators']
            )
            
            # Print summary
            print(f"\n{'='*60}")
            print("Analysis Complete")
            print(f"{'='*60}")
            print(f"Company: {result['company_name']} ({result['ticker']})")
            print(f"CIK: {result['cik']}")
            print(f"\nYears Analyzed: {len(result['indicators'])}")
            print(f"Year Range: {min(result['indicators'].keys())} - {max(result['indicators'].keys())}")
            print(f"\nOutput File: {output_file}")
            print(f"{'='*60}\n")
            
            # Also print as JSON for programmatic use
            print("JSON Output:")
            print(json.dumps({
                'ticker': result['ticker'],
                'company_name': result['company_name'],
                'cik': result['cik'],
                'years': list(result['indicators'].keys()),
                'output_file': output_file
            }, indent=2, default=str))
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        logger.exception("Unexpected error occurred")
        sys.exit(1)


if __name__ == '__main__':
    main()
