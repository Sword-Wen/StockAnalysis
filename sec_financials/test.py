#!/usr/bin/env python3
"""
Test script for SEC Financial Data Extractor
"""

import sys
import os
import json
import logging

# Add parent directory to path for testing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sec_financials import SECFinancialExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_ticker_mapping():
    """Test ticker to CIK mapping"""
    print("Testing ticker mapping...")
    extractor = SECFinancialExtractor()
    
    # Test known tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    for ticker in test_tickers:
        cik = extractor.ticker_mapper.ticker_to_cik(ticker)
        if cik:
            print(f"  ✓ {ticker} -> CIK {cik}")
        else:
            print(f"  ✗ {ticker} not found")
    
    # Test search
    print("\nTesting ticker search...")
    results = extractor.search_tickers('AAP', limit=5)
    print(f"  Search for 'AAP' found {results['count']} results")
    for ticker, cik in results['results'].items():
        print(f"    {ticker}: CIK {cik}")
    
    # Test stats
    stats = extractor.get_mapping_stats()
    print(f"\nMapping statistics:")
    print(f"  Total tickers: {stats['total_tickers']:,}")
    print(f"  Total CIKs: {stats['total_ciks']:,}")


def test_fetch_single_year():
    """Test fetching data for a single year"""
    print("\n" + "="*60)
    print("Testing fetch for single year (AAPL 2023)...")
    print("="*60)
    
    extractor = SECFinancialExtractor()
    
    try:
        result = extractor.fetch_financial_data(
            ticker='AAPL',
            year=2023,
            output_dir='test_output'
        )
        
        print(f"\n✓ Successfully fetched data for AAPL 2023")
        print(f"  Company: {result['company_name']}")
        print(f"  Data points found:")
        print(f"    Balance Sheet: {result['statements_found']['balance_sheet']}")
        print(f"    Income Statement: {result['statements_found']['income_statement']}")
        print(f"    Cash Flow: {result['statements_found']['cash_flow']}")
        
        print(f"\n  Exported files:")
        for stmt_type, filepath in result['exported_files'].items():
            stmt_name = stmt_type.replace('_', ' ').title()
            print(f"    {stmt_name}: {os.path.basename(filepath)}")
        
        if result['summary_report']:
            print(f"  Summary report: {os.path.basename(result['summary_report'])}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error fetching data: {e}")
        return False


def test_fetch_single_quarter():
    """Test fetching data for a single quarter"""
    print("\n" + "="*60)
    print("Testing fetch for single quarter (MSFT Q4 2023)...")
    print("="*60)
    
    extractor = SECFinancialExtractor()
    
    try:
        result = extractor.fetch_financial_data(
            ticker='MSFT',
            year=2023,
            quarter=4,
            output_dir='test_output'
        )
        
        print(f"\n✓ Successfully fetched data for MSFT Q4 2023")
        print(f"  Company: {result['company_name']}")
        print(f"  Data points found:")
        print(f"    Balance Sheet: {result['statements_found']['balance_sheet']}")
        print(f"    Income Statement: {result['statements_found']['income_statement']}")
        print(f"    Cash Flow: {result['statements_found']['cash_flow']}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error fetching data: {e}")
        return False


def test_fetch_year_range():
    """Test fetching data for a year range"""
    print("\n" + "="*60)
    print("Testing fetch for year range (GOOGL 2021-2023)...")
    print("="*60)
    
    extractor = SECFinancialExtractor()
    
    try:
        result = extractor.fetch_financial_data(
            ticker='GOOGL',
            start_year=2021,
            end_year=2023,
            output_dir='test_output'
        )
        
        print(f"\n✓ Successfully fetched data for GOOGL 2021-2023")
        print(f"  Company: {result['company_name']}")
        print(f"  Data points found:")
        print(f"    Balance Sheet: {result['statements_found']['balance_sheet']}")
        print(f"    Income Statement: {result['statements_found']['income_statement']}")
        print(f"    Cash Flow: {result['statements_found']['cash_flow']}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error fetching data: {e}")
        return False


def test_fetch_quarter_range():
    """Test fetching data for a quarter range"""
    print("\n" + "="*60)
    print("Testing fetch for quarter range (AMZN Q1 2022 - Q4 2023)...")
    print("="*60)
    
    extractor = SECFinancialExtractor()
    
    try:
        result = extractor.fetch_financial_data(
            ticker='AMZN',
            start_year=2022,
            start_quarter=1,
            end_year=2023,
            end_quarter=4,
            output_dir='test_output'
        )
        
        print(f"\n✓ Successfully fetched data for AMZN Q1 2022 - Q4 2023")
        print(f"  Company: {result['company_name']}")
        print(f"  Data points found:")
        print(f"    Balance Sheet: {result['statements_found']['balance_sheet']}")
        print(f"    Income Statement: {result['statements_found']['income_statement']}")
        print(f"    Cash Flow: {result['statements_found']['cash_flow']}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error fetching data: {e}")
        return False


def test_invalid_ticker():
    """Test with invalid ticker"""
    print("\n" + "="*60)
    print("Testing invalid ticker...")
    print("="*60)
    
    extractor = SECFinancialExtractor()
    
    try:
        result = extractor.fetch_financial_data(
            ticker='INVALID123',
            year=2023
        )
        print(f"\n✗ Should have failed but didn't")
        return False
    except ValueError as e:
        print(f"\n✓ Correctly rejected invalid ticker: {e}")
        return True
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


def test_cache_operations():
    """Test cache operations"""
    print("\n" + "="*60)
    print("Testing cache operations...")
    print("="*60)
    
    extractor = SECFinancialExtractor()
    
    try:
        # First fetch should create cache
        print("First fetch (should create cache)...")
        result1 = extractor.fetch_financial_data(
            ticker='TSLA',
            year=2023,
            output_dir='test_output'
        )
        print(f"  ✓ Fetched TSLA 2023 data")
        
        # Second fetch should use cache
        print("Second fetch (should use cache)...")
        result2 = extractor.fetch_financial_data(
            ticker='TSLA',
            year=2023,
            output_dir='test_output'
        )
        print(f"  ✓ Used cached data for TSLA 2023")
        
        # Clear cache
        print("Clearing cache...")
        extractor.clear_cache()
        print(f"  ✓ Cleared cache")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("SEC Financial Data Extractor - Test Suite")
    print("="*60)
    
    # Create test output directory
    os.makedirs('test_output', exist_ok=True)
    
    test_results = []
    
    # Run tests
    test_results.append(("Ticker Mapping", test_ticker_mapping()))
    test_results.append(("Single Year Fetch", test_fetch_single_year()))
    test_results.append(("Single Quarter Fetch", test_fetch_single_quarter()))
    test_results.append(("Year Range Fetch", test_fetch_year_range()))
    test_results.append(("Quarter Range Fetch", test_fetch_quarter_range()))
    test_results.append(("Invalid Ticker", test_invalid_ticker()))
    test_results.append(("Cache Operations", test_cache_operations()))
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    # Check if all tests passed
    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())