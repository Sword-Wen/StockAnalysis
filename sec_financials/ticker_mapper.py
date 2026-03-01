"""
Ticker to CIK mapper for SEC API
"""

import requests
import json
import os
import time
from typing import Dict, Optional, Tuple
import logging

from .config import (
    COMPANY_TICKERS_URL,
    USER_AGENT,
    CACHE_DIR,
    TICKER_CACHE_FILE,
    CACHE_EXPIRY_DAYS
)

logger = logging.getLogger(__name__)


class TickerMapper:
    """Maps stock tickers to CIK numbers"""
    
    def __init__(self):
        """Initialize ticker mapper"""
        self._ticker_to_cik: Dict[str, str] = {}
        self._cik_to_ticker: Dict[str, str] = {}
        self.cache_path = os.path.join(CACHE_DIR, TICKER_CACHE_FILE)
        
        # Create cache directory if it doesn't exist
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        # Load mapping
        self._load_mapping()
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not os.path.exists(self.cache_path):
            return False
        
        cache_time = os.path.getmtime(self.cache_path)
        cache_age = time.time() - cache_time
        max_age = CACHE_EXPIRY_DAYS * 24 * 60 * 60
        
        return cache_age < max_age
    
    def _load_mapping(self):
        """Load ticker-CIK mapping from cache or download from SEC"""
        # Try to load from cache first
        if self._is_cache_valid():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    self._ticker_to_cik = cached_data.get('ticker_to_cik', {})
                    self._cik_to_ticker = cached_data.get('cik_to_ticker', {})
                logger.info(f"Loaded {len(self._ticker_to_cik)} ticker mappings from cache")
                return
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load cache: {e}")
        
        # Download from SEC
        self._download_mapping()
    
    def _download_mapping(self):
        """Download ticker-CIK mapping from SEC website"""
        logger.info("Downloading ticker-CIK mapping from SEC...")
        
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json"
        }
        
        try:
            # 尝试使用requests，如果失败则使用urllib
            try:
                response = requests.get(COMPANY_TICKERS_URL, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
            except (requests.exceptions.SSLError, requests.exceptions.RequestException) as e:
                logger.warning(f"Requests failed with SSL error, trying urllib: {e}")
                # 使用urllib作为备选
                import urllib.request
                import ssl
                import json as json_module
                
                # 创建不验证SSL的上下文
                ssl_context = ssl._create_unverified_context()
                req = urllib.request.Request(COMPANY_TICKERS_URL, headers=headers)
                response = urllib.request.urlopen(req, timeout=30, context=ssl_context)
                data_str = response.read().decode('utf-8')
                data = json_module.loads(data_str)
            
            # Process the data
            self._ticker_to_cik = {}
            self._cik_to_ticker = {}
            
            for item in data.values():
                ticker = item.get("ticker", "").upper()
                cik = str(item.get("cik_str", ""))
                
                if ticker and cik:
                    self._ticker_to_cik[ticker] = cik
                    self._cik_to_ticker[cik] = ticker
            
            # Save to cache
            cache_data = {
                'ticker_to_cik': self._ticker_to_cik,
                'cik_to_ticker': self._cik_to_ticker,
                'download_time': time.time()
            }
            
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Downloaded and cached {len(self._ticker_to_cik)} ticker mappings")
            
        except Exception as e:
            logger.error(f"Failed to download ticker mapping: {e}")
            
            # If we have old cache, use it even if expired
            if os.path.exists(self.cache_path):
                logger.warning("Using expired cache as fallback")
                try:
                    with open(self.cache_path, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                        self._ticker_to_cik = cached_data.get('ticker_to_cik', {})
                        self._cik_to_ticker = cached_data.get('cik_to_ticker', {})
                except (json.JSONDecodeError, IOError):
                    pass
    
    def ticker_to_cik(self, ticker: str) -> Optional[str]:
        """
        Convert stock ticker to CIK
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            
        Returns:
            CIK as string, or None if not found
        """
        ticker_upper = ticker.upper()
        return self._ticker_to_cik.get(ticker_upper)
    
    def cik_to_ticker(self, cik: str) -> Optional[str]:
        """
        Convert CIK to stock ticker
        
        Args:
            cik: Central Index Key
            
        Returns:
            Stock ticker symbol, or None if not found
        """
        return self._cik_to_ticker.get(str(cik))
    
    def get_ticker_info(self, ticker: str) -> Optional[Tuple[str, str]]:
        """
        Get both ticker and CIK for validation
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Tuple of (ticker, cik) or None if not found
        """
        cik = self.ticker_to_cik(ticker)
        if cik:
            return (ticker.upper(), cik)
        return None
    
    def search_tickers(self, query: str, limit: int = 10) -> Dict[str, str]:
        """
        Search for tickers by partial match
        
        Args:
            query: Search query (case-insensitive)
            limit: Maximum number of results
            
        Returns:
            Dictionary of {ticker: cik} matches
        """
        query_upper = query.upper()
        results = {}
        
        for ticker, cik in self._ticker_to_cik.items():
            if query_upper in ticker:
                results[ticker] = cik
                if len(results) >= limit:
                    break
        
        return results
    
    def refresh_mapping(self):
        """Force refresh of ticker-CIK mapping"""
        logger.info("Refreshing ticker-CIK mapping...")
        if os.path.exists(self.cache_path):
            os.remove(self.cache_path)
        self._download_mapping()
    
    def get_mapping_stats(self) -> Dict[str, int]:
        """Get statistics about the mapping"""
        return {
            'total_tickers': len(self._ticker_to_cik),
            'total_ciks': len(self._cik_to_ticker)
        }
