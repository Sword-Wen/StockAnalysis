"""
SEC API Client for fetching financial data
"""

import requests
import time
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from .config import (
    SEC_API_BASE_URL,
    COMPANY_FACTS_ENDPOINT,
    USER_AGENT,
    RATE_LIMIT,
    CACHE_DIR,
    CACHE_EXPIRY_DAYS
)

logger = logging.getLogger(__name__)


class SECClient:
    """Client for interacting with SEC REST API"""
    
    def __init__(self, user_agent: Optional[str] = None):
        """
        Initialize SEC API client
        
        Args:
            user_agent: Custom User-Agent string (required by SEC API)
        """
        self.user_agent = user_agent or USER_AGENT
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "application/json"
        })
        self.last_request_time = 0
        self.min_request_interval = 1.0 / RATE_LIMIT
        
        # Create cache directory if it doesn't exist
        os.makedirs(CACHE_DIR, exist_ok=True)
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_cache_path(self, cik: str) -> str:
        """Get cache file path for a CIK"""
        return os.path.join(CACHE_DIR, f"cik_{cik}.json")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if cache is still valid"""
        if not os.path.exists(cache_path):
            return False
        
        cache_time = os.path.getmtime(cache_path)
        cache_age = time.time() - cache_time
        max_age = CACHE_EXPIRY_DAYS * 24 * 60 * 60
        
        return cache_age < max_age
    
    def get_company_facts(self, cik: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get company facts data from SEC API
        
        Args:
            cik: Central Index Key (10-digit zero-padded)
            use_cache: Whether to use cached data if available
            
        Returns:
            Dictionary containing company facts data
        """
        # Ensure CIK is 10-digit zero-padded
        cik_padded = str(cik).zfill(10)
        
        # Check cache first
        cache_path = self._get_cache_path(cik_padded)
        
        # Try to load from cache first (regardless of validity) if use_cache is True
        if use_cache and os.path.exists(cache_path):
            try:
                logger.info(f"Loading cached data for CIK {cik_padded}")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Return cache if valid, otherwise try to refresh
                if self._is_cache_valid(cache_path):
                    return data
                else:
                    logger.info(f"Cache expired for CIK {cik_padded}, trying to refresh...")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error reading cache for CIK {cik_padded}: {e}")
        
        # Make API request
        self._rate_limit()
        
        url = f"{SEC_API_BASE_URL}{COMPANY_FACTS_ENDPOINT.format(cik=cik_padded)}"
        
        try:
            logger.info(f"Fetching data from SEC API for CIK {cik_padded}")
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the response
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data for CIK {cik_padded}: {e}")
            
            # Try to load from cache even if expired
            if os.path.exists(cache_path):
                logger.warning(f"Loading expired cache for CIK {cik_padded}")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            raise
    
    def clear_cache(self, cik: Optional[str] = None):
        """
        Clear cache for specific CIK or all cache
        
        Args:
            cik: Specific CIK to clear cache for, or None to clear all cache
        """
        if cik:
            cache_path = self._get_cache_path(str(cik).zfill(10))
            if os.path.exists(cache_path):
                os.remove(cache_path)
                logger.info(f"Cleared cache for CIK {cik}")
        else:
            # Clear all cache files
            for filename in os.listdir(CACHE_DIR):
                if filename.startswith("cik_") and filename.endswith(".json"):
                    os.remove(os.path.join(CACHE_DIR, filename))
            logger.info("Cleared all cache files")