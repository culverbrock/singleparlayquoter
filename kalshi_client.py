#!/usr/bin/env python3
from __future__ import annotations

import os
import base64
import datetime
import json
import logging
from typing import Any, Dict, Optional

import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)


class KalshiClient:
    def __init__(self, api_base: Optional[str] = None, api_key_id: Optional[str] = None, private_key_path: Optional[str] = None) -> None:
        self.api_base = (api_base or os.getenv("KALSHI_API_BASE") or "https://api.elections.kalshi.com").rstrip("/")
        self.api_key_id = api_key_id or os.getenv("KALSHI_API_KEY_ID")
        self.private_key_path = private_key_path or os.getenv("KALSHI_PRIVATE_KEY_PATH")
        self._session = requests.Session()
        self._private_key = None
        
        # Load private key if path is provided
        if self.private_key_path and os.path.exists(self.private_key_path):
            self._load_private_key()

    def _load_private_key(self) -> None:
        """Load the private key from file."""
        try:
            with open(self.private_key_path, "rb") as f:
                self._private_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
        except Exception as e:
            print(f"Warning: Could not load private key from {self.private_key_path}: {e}")
            self._private_key = None

    def _create_signature(self, timestamp: str, method: str, path: str) -> str:
        """Create the request signature using RSA-PSS."""
        if not self._private_key:
            raise RuntimeError("Private key not loaded. Set KALSHI_PRIVATE_KEY_PATH environment variable.")
        
        # Strip query parameters before signing
        path_without_query = path.split('?')[0]
        message = f"{timestamp}{method}{path_without_query}".encode('utf-8')
        
        signature = self._private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode('utf-8')

    def _get_auth_headers(self, method: str, path: str) -> Dict[str, str]:
        """Get authentication headers for the request."""
        if not self.api_key_id or not self._private_key:
            raise RuntimeError("API Key ID and private key are required for authentication.")
        
        timestamp = str(int(datetime.datetime.now().timestamp() * 1000))
        signature = self._create_signature(timestamp, method, path)
        
        return {
            'KALSHI-ACCESS-KEY': self.api_key_id,
            'KALSHI-ACCESS-SIGNATURE': signature,
            'KALSHI-ACCESS-TIMESTAMP': timestamp
        }

    def _headers(self) -> Dict[str, str]:
        """Get basic headers (without authentication)."""
        return {
            "Accept": "application/json",
            "User-Agent": "kalshi-rfq-integration/0.1",
        }

    def get_communications_id(self) -> str:
        """Get communications ID using new RSA authentication."""
        path = "/trade-api/v2/communications/id"
        url = f"{self.api_base}{path}"
        
        # Get authentication headers
        auth_headers = self._get_auth_headers("GET", path)
        headers = {**self._headers(), **auth_headers}
        
        resp = self._session.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data: Dict[str, Any] = resp.json()
        comm_id = data.get("communications_id")
        if not isinstance(comm_id, str) or not comm_id:
            raise RuntimeError("Invalid response: missing communications_id")
        return comm_id

    def get_communications_id(self) -> str:
        """Get the communications ID of the logged-in user."""
        path = "/trade-api/v2/communications/id"
        url = f"{self.api_base}{path}"
        
        auth_headers = self._get_auth_headers("GET", path)
        headers = {**self._headers(), **auth_headers}
        
        print(f"\n🔍 GETTING COMMUNICATIONS ID:")
        print(f"   📍 URL: {url}")
        print(f"   🛤️  Path: {path}")
        print(f"   📝 Method: GET")
        print(f"   🔑 Headers:")
        for key, value in headers.items():
            if 'SIGNATURE' in key:
                print(f"      {key}: {value[:50]}...{value[-10:]}")
            else:
                print(f"      {key}: {value}")
        
        resp = self._session.get(url, headers=headers, timeout=10)
        print(f"   📈 Response Status: {resp.status_code}")
        print(f"   📋 Response Headers: {dict(resp.headers)}")
        if resp.status_code != 200:
            print(f"   ❌ Response Body: {resp.text}")
        
        resp.raise_for_status()
        data = resp.json()
        comm_id = data.get("communications_id")
        if not isinstance(comm_id, str) or not comm_id:
            raise RuntimeError("Invalid response: missing communications_id")
        return comm_id

    def get_quotes(self, cursor: Optional[str] = None, limit: Optional[int] = None, 
                   creator_user_id: Optional[str] = None, rfq_creator_user_id: Optional[str] = None,
                   rfq_id: Optional[str] = None, market_ticker: Optional[str] = None,
                   event_ticker: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """
        Get quotes with optional filtering.
        
        Args:
            cursor: Pagination cursor
            limit: Number of results per page (default: 500, max: 500)
            creator_user_id: Filter by quote creator user ID
            rfq_creator_user_id: Filter by RFQ creator user ID
            rfq_id: Filter quotes by RFQ ID (for getting quotes on a specific RFQ)
            market_ticker: Filter quotes by market ticker
            event_ticker: Filter quotes by event ticker
            status: Filter quotes by status (e.g., 'open')
        
        Returns:
            Dict with 'quotes' list and optional 'cursor' for pagination
        """
        path = "/trade-api/v2/communications/quotes"
        url = f"{self.api_base}{path}"
        params: Dict[str, str] = {}
        if cursor:
            params["cursor"] = cursor
        if limit:
            params["limit"] = str(limit)
        if creator_user_id:
            params["creator_user_id"] = creator_user_id
        if rfq_creator_user_id:
            params["rfq_creator_user_id"] = rfq_creator_user_id
        if rfq_id:
            params["rfq_id"] = rfq_id
        if market_ticker:
            params["market_ticker"] = market_ticker
        if event_ticker:
            params["event_ticker"] = event_ticker
        if status:
            params["status"] = status
        
        auth_headers = self._get_auth_headers("GET", path)
        headers = {**self._headers(), **auth_headers}
        
        print(f"\n🔍 COMPLETE QUOTES API REQUEST DEBUG:")
        print(f"   📍 URL: {url}")
        print(f"   🛤️  Path: {path}")
        print(f"   📝 Method: GET")
        print(f"   📊 Params: {params}")
        print(f"   🔑 Headers:")
        for key, value in headers.items():
            if 'SIGNATURE' in key:
                print(f"      {key}: {value[:50]}...{value[-10:]}")
            else:
                print(f"      {key}: {value}")
        
        resp = self._session.get(url, headers=headers, params=params, timeout=10)
        print(f"   📈 Response Status: {resp.status_code}")
        print(f"   📋 Response Headers: {dict(resp.headers)}")
        if resp.status_code != 200:
            print(f"   ❌ Response Body: {resp.text}")
        
        resp.raise_for_status()
        return resp.json()

    # Quote lifecycle
    def create_quote(self, rfq_id: str, yes_bid: Optional[str] = None, no_bid: Optional[str] = None, rest_remainder: bool = True) -> Dict[str, Any]:
        path = "/trade-api/v2/communications/quotes"
        url = f"{self.api_base}{path}"
        # Use the exact format from Kalshi API documentation
        body: Dict[str, Any] = {
            "rfq_id": rfq_id,
            "rest_remainder": rest_remainder,
        }
        
        # Both yes_bid and no_bid are required according to the API docs
        body["yes_bid"] = str(yes_bid) if yes_bid is not None else "0.0000"
        body["no_bid"] = str(no_bid) if no_bid is not None else "0.0000"
        
        print(f"Creating quote with body: {body}")
        
        # Get authentication headers
        auth_headers = self._get_auth_headers("POST", path)
        
        resp = self._session.post(url, headers={**self._headers(), **auth_headers, "Content-Type": "application/json"}, json=body, timeout=10)
        
        # Log detailed error information for debugging
        if resp.status_code != 200:
            try:
                error_detail = resp.json()
                print(f"Kalshi API Error Details: {error_detail}")
            except:
                print(f"Kalshi API Error Response: {resp.text}")
        
        resp.raise_for_status()
        return resp.json()

    def get_quote(self, quote_id: str) -> Dict[str, Any]:
        path = f"/trade-api/v2/communications/quotes/{quote_id}"
        url = f"{self.api_base}{path}"
        auth_headers = self._get_auth_headers("GET", path)
        resp = self._session.get(url, headers={**self._headers(), **auth_headers}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def delete_quote(self, quote_id: str) -> Dict[str, Any]:
        path = f"/trade-api/v2/communications/quotes/{quote_id}"
        url = f"{self.api_base}{path}"
        auth_headers = self._get_auth_headers("DELETE", path)
        resp = self._session.delete(url, headers={**self._headers(), **auth_headers}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def accept_quote(self, quote_id: str, accepted_side: str) -> Dict[str, Any]:
        path = f"/trade-api/v2/communications/quotes/{quote_id}/accept"
        url = f"{self.api_base}{path}"
        body = {"accepted_side": accepted_side}
        auth_headers = self._get_auth_headers("PUT", path)
        
        logger.info(f"Accepting quote {quote_id} with body: {body}")
        logger.info(f"URL: {url}")
        
        resp = self._session.put(url, headers={**self._headers(), **auth_headers, "Content-Type": "application/json"}, json=body, timeout=10)
        
        logger.info(f"Accept quote response status: {resp.status_code}")
        logger.info(f"Accept quote response text: {resp.text[:500] if resp.text else '(empty)'}")
        
        # Handle rate limiting
        if resp.status_code == 429:
            logger.warning(f"⚠️ Rate limited (429) when accepting quote {quote_id}")
            raise Exception("Rate limited by Kalshi API (429). Please reduce request frequency.")
        
        # Check if response is successful
        if resp.status_code not in [200, 201, 204]:
            try:
                error_detail = resp.json()
                logger.error(f"Kalshi API Accept Quote Error Details: {error_detail}")
            except:
                logger.error(f"Kalshi API Accept Quote Error Response: {resp.text}")
            resp.raise_for_status()
        
        # Handle empty response (204 No Content)
        if resp.status_code == 204 or not resp.text:
            logger.info("Accept quote returned empty response (success)")
            return {"success": True, "message": "Quote accepted successfully"}
        
        # Try to parse JSON response
        try:
            return resp.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {resp.text}")
            # Return a success indicator if status was 200/201
            if resp.status_code in [200, 201]:
                return {"success": True, "message": "Quote accepted (non-JSON response)", "raw_response": resp.text}
            raise

    def confirm_quote(self, quote_id: str) -> Dict[str, Any]:
        path = f"/trade-api/v2/communications/quotes/{quote_id}/confirm"
        url = f"{self.api_base}{path}"
        
        import time
        import logging
        logger = logging.getLogger(__name__)
        
        # Try to confirm 3 times
        last_error = None
        request_info = None
        for attempt in range(1, 4):
            try:
                # Generate fresh auth headers for each attempt
                auth_headers = self._get_auth_headers("PUT", path)
                
                # Add Content-Type header as required by Kalshi API
                auth_headers['Content-Type'] = 'application/json'
                
                # Store request info for debugging
                request_info = {
                    "method": "PUT",
                    "url": url,
                    "headers": {k: v for k, v in auth_headers.items()}
                }
                
                # Create a fresh session with no default headers to avoid Content-Type
                fresh_session = requests.Session()
                fresh_session.headers.clear()  # Remove ALL default headers
                
                # Prepare the request to see what headers will actually be sent
                req = requests.Request('PUT', url, headers=auth_headers)
                prepared = fresh_session.prepare_request(req)
                
                # Remove Content-Length header which triggers Content-Type requirement
                if 'Content-Length' in prepared.headers:
                    del prepared.headers['Content-Length']
                
                # Log the ACTUAL headers that will be sent
                logger.info(f"🔍 Confirm Quote Request - Attempt {attempt}/3:")
                logger.info(f"   URL: {url}")
                logger.info(f"   Method: PUT")
                logger.info(f"   Headers being sent: {dict(prepared.headers)}")
                
                # Make the PUT request
                resp = fresh_session.send(prepared)
                
                # Log detailed error information for debugging
                if resp.status_code in [200, 204]:  # 204 = No Content (success)
                    logger.info(f"✅ Confirm successful on attempt {attempt}/3 (status: {resp.status_code})")
                    # 204 returns no content, so handle both cases
                    if resp.status_code == 200 and resp.text:
                        result = resp.json()
                    else:
                        result = {'status': 'confirmed', 'quote_id': quote_id}
                    # Add request info to the response
                    result['_request_info'] = request_info
                    return result
                else:
                    logger.error(f"❌ Status code: {resp.status_code}")
                    logger.error(f"❌ Response headers: {dict(resp.headers)}")
                    try:
                        error_detail = resp.json()
                        error_msg = f"❌ Kalshi Confirm Quote Error ({resp.status_code}): {error_detail}"
                        logger.error(error_msg)
                        
                        # Check if it's an auth error
                        if 'code' in error_detail:
                            if error_detail['code'] in ['invalid_signature', 'invalid_timestamp', 'invalid_api_key']:
                                logger.error(f"🔐 AUTHENTICATION ERROR: {error_detail}")
                        
                        last_error = Exception(f"{resp.status_code} Client Error: {error_detail.get('message', 'Bad Request')} for url: {url}")
                        last_error.request_info = request_info  # Attach immediately
                    except:
                        error_msg = f"❌ Kalshi Confirm Quote Error ({resp.status_code}): {resp.text}"
                        logger.error(error_msg)
                        last_error = Exception(f"{resp.status_code} Client Error: Bad Request for url: {url}")
                        last_error.request_info = request_info  # Attach immediately
                    
                    # If not the last attempt, wait a bit before retrying
                    if attempt < 3:
                        wait_time = 0.5 * attempt  # 0.5s, 1.0s
                        logger.info(f"⏳ Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
            except Exception as e:
                logger.error(f"❌ Exception on attempt {attempt}/3: {e}")
                last_error = e
                # Attach request info if we have it
                if request_info and not hasattr(last_error, 'request_info'):
                    last_error.request_info = request_info
                if attempt < 3:
                    wait_time = 0.5 * attempt
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        # If we get here, all 3 attempts failed
        logger.error(f"❌ All 3 confirmation attempts failed for quote {quote_id}")
        # Attach request info to the exception
        if last_error and request_info:
            last_error.request_info = request_info
        raise last_error if last_error else Exception(f"Failed to confirm quote {quote_id} after 3 attempts")

    def get_events(self, series_ticker: Optional[str] = None, limit: Optional[int] = None, cursor: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """Get events from Kalshi API.
        
        Args:
            series_ticker: Filter by series ticker (e.g., 'KXNFL', 'KXNFLGAME')
            limit: Number of results per page (1-1000, defaults to 100)
            cursor: Pagination cursor for next page
            status: Filter by status (e.g., 'open', 'closed')
            
        Returns:
            Dictionary containing events data
        """
        path = "/trade-api/v2/events"
        url = f"{self.api_base}{path}"
        params: Dict[str, str] = {}
        
        if series_ticker:
            params["series_ticker"] = series_ticker
        if limit:
            params["limit"] = str(limit)
        if cursor:
            params["cursor"] = cursor
        if status:
            params["status"] = status
        
        auth_headers = self._get_auth_headers("GET", path)
        headers = {**self._headers(), **auth_headers}
        
        resp = self._session.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_event(self, event_ticker: str, with_nested_markets: bool = False) -> Dict[str, Any]:
        """Get event information including all markets for that event.
        
        Args:
            event_ticker: The event ticker to retrieve
            with_nested_markets: If true, markets are included within the event object
            
        Returns:
            Dictionary containing event data and markets
        """
        path = f"/trade-api/v2/events/{event_ticker}"
        url = f"{self.api_base}{path}"
        params: Dict[str, str] = {}
        
        if with_nested_markets:
            params["with_nested_markets"] = "true"
        
        auth_headers = self._get_auth_headers("GET", path)
        headers = {**self._headers(), **auth_headers}
        
        print(f"\n Getting Event:")
        print(f"   URL: {url}")
        print(f"   Path: {path}")
        print(f"   Method: GET")
        print(f"   Params: {params}")
        
        resp = self._session.get(url, headers=headers, params=params, timeout=10)
        print(f"   Response Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"   Response Body: {resp.text}")
        
        resp.raise_for_status()
        return resp.json()
    
    def get_market(self, ticker: str) -> Dict[str, Any]:
        """Get detailed market information for a specific ticker.
        
        Args:
            ticker: Market ticker to retrieve
            
        Returns:
            Dictionary containing market data with yes_bid, no_bid, yes_ask, no_ask
        """
        path = f"/trade-api/v2/markets/{ticker}"
        url = f"{self.api_base}{path}"
        
        auth_headers = self._get_auth_headers("GET", path)
        headers = {**self._headers(), **auth_headers}
        
        print(f"\n Getting Market:")
        print(f"   URL: {url}")
        print(f"   Ticker: {ticker}")
        
        resp = self._session.get(url, headers=headers, timeout=10)
        print(f"   Response Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"   Response Body: {resp.text}")
        
        resp.raise_for_status()
        return resp.json()
    
    def get_market_orderbook(self, ticker: str) -> Dict[str, Any]:
        """Get the current order book for a specific market.
        
        Args:
            ticker: Market ticker to retrieve orderbook for
            
        Returns:
            Dictionary containing orderbook data with yes and no bid levels
        """
        path = f"/trade-api/v2/markets/{ticker}/orderbook"
        url = f"{self.api_base}{path}"
        
        auth_headers = self._get_auth_headers("GET", path)
        headers = {**self._headers(), **auth_headers}
        
        resp = self._session.get(url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            print(f"   Orderbook API Error for {ticker}: {resp.status_code} - {resp.text}")
        
        resp.raise_for_status()
        return resp.json()
    
    def get_markets(self, tickers: Optional[str] = None, limit: Optional[int] = None, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Get market information from Kalshi API.
        
        Args:
            tickers: Comma-separated list of market tickers to retrieve
            limit: Number of results per page (1-1000, defaults to 100)
            cursor: Pagination cursor for next page
            
        Returns:
            Dictionary containing market data
        """
        path = "/trade-api/v2/markets"
        url = f"{self.api_base}{path}"
        params: Dict[str, str] = {}
        
        if tickers:
            params["tickers"] = tickers
        if limit:
            params["limit"] = str(limit)
        if cursor:
            params["cursor"] = cursor
        
        auth_headers = self._get_auth_headers("GET", path)
        headers = {**self._headers(), **auth_headers}
        
        print(f"\n🔍 GETTING MARKETS:")
        print(f"   📍 URL: {url}")
        print(f"   🛤️  Path: {path}")
        print(f"   📝 Method: GET")
        print(f"   📊 Params: {params}")
        print(f"   🔑 Headers:")
        for key, value in headers.items():
            if 'SIGNATURE' in key:
                print(f"      {key}: {value[:50]}...{value[-10:]}")
            else:
                print(f"      {key}: {value}")
        
        resp = self._session.get(url, headers=headers, params=params, timeout=10)
        print(f"   📈 Response Status: {resp.status_code}")
        print(f"   📋 Response Headers: {dict(resp.headers)}")
        if resp.status_code != 200:
            print(f"   ❌ Response Body: {resp.text}")
        
        resp.raise_for_status()
        return resp.json()

    def get_trades(self, ticker: Optional[str] = None, limit: Optional[int] = None, cursor: Optional[str] = None, min_ts: Optional[int] = None, max_ts: Optional[int] = None) -> Dict[str, Any]:
        """Get trades data from Kalshi API.
        
        Args:
            ticker: Filter trades by market ticker
            limit: Number of results per page (1-1000, defaults to 100)
            cursor: Pagination cursor for next page
            min_ts: Filter trades after this Unix timestamp
            max_ts: Filter trades before this Unix timestamp
            
        Returns:
            Dictionary containing trades data
        """
        path = "/trade-api/v2/markets/trades"
        url = f"{self.api_base}{path}"
        params: Dict[str, str] = {}
        
        if ticker:
            params["ticker"] = ticker
        if limit:
            params["limit"] = str(limit)
        if cursor:
            params["cursor"] = cursor
        if min_ts:
            params["min_ts"] = str(min_ts)
        if max_ts:
            params["max_ts"] = str(max_ts)
        
        auth_headers = self._get_auth_headers("GET", path)
        headers = {**self._headers(), **auth_headers}
        
        print(f"\n🔍 GETTING TRADES:")
        print(f"   📍 URL: {url}")
        print(f"   🛤️  Path: {path}")
        print(f"   📝 Method: GET")
        print(f"   📊 Params: {params}")
        print(f"   🔑 Headers:")
        for key, value in headers.items():
            if 'SIGNATURE' in key:
                print(f"      {key}: {value[:50]}...{value[-10:]}")
            else:
                print(f"      {key}: {value}")
        
        resp = self._session.get(url, headers=headers, params=params, timeout=10)
        print(f"   📈 Response Status: {resp.status_code}")
        print(f"   📋 Response Headers: {dict(resp.headers)}")
        if resp.status_code != 200:
            print(f"   ❌ Response Body: {resp.text}")
        
        resp.raise_for_status()
        return resp.json()

    # RFQ lifecycle
    def get_rfqs(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        path = "/trade-api/v2/communications/rfqs"
        url = f"{self.api_base}{path}"
        params: Dict[str, str] = {}
        if cursor:
            params["cursor"] = cursor
        
        auth_headers = self._get_auth_headers("GET", path)
        headers = {**self._headers(), **auth_headers}
        
        resp = self._session.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def create_rfq(self, market_ticker: str, contracts: int, target_cost_centi_cents: int, rest_remainder: bool = True) -> Dict[str, Any]:
        """
        Create a new RFQ (Request for Quote).
        
        Args:
            market_ticker: The ticker of the market for which to create an RFQ
            contracts: The number of contracts for the RFQ
            target_cost_centi_cents: The target cost for the RFQ in centi-cents
            rest_remainder: Whether to rest the remainder of the RFQ after execution (default: True)
        
        Returns:
            Dict containing the RFQ response with 'rfq' key containing the created RFQ data
        """
        path = "/trade-api/v2/communications/rfqs"
        url = f"{self.api_base}{path}"
        
        # Kalshi API requires EITHER contracts OR target_cost_centi_cents, not both
        # If target_cost_centi_cents is provided, don't send contracts (even if 0)
        body: Dict[str, Any] = {
            "market_ticker": market_ticker,
            "rest_remainder": rest_remainder,
        }
        
        if target_cost_centi_cents > 0:
            body["target_cost_centi_cents"] = target_cost_centi_cents
        elif contracts > 0:
            body["contracts"] = contracts
        else:
            # Must have at least one
            body["contracts"] = contracts
            body["target_cost_centi_cents"] = target_cost_centi_cents
        # Get authentication headers
        auth_headers = self._get_auth_headers("POST", path)
        
        resp = self._session.post(url, headers={**self._headers(), **auth_headers, "Content-Type": "application/json"}, json=body, timeout=10)
        
        # Log response details for debugging
        if resp.status_code != 200 and resp.status_code != 201:
            logger.error(f"❌ create_rfq failed with status {resp.status_code}")
            logger.error(f"   Request body: {body}")
            logger.error(f"   Response: {resp.text}")
        
        resp.raise_for_status()
        return resp.json()

    def get_rfq(self, rfq_id: str) -> Dict[str, Any]:
        path = f"/trade-api/v2/communications/rfqs/{rfq_id}"
        url = f"{self.api_base}{path}"
        auth_headers = self._get_auth_headers("GET", path)
        resp = self._session.get(url, headers={**self._headers(), **auth_headers}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def delete_rfq(self, rfq_id: str) -> None:
        path = f"/trade-api/v2/communications/rfqs/{rfq_id}"
        url = f"{self.api_base}{path}"
        
        # Get authentication headers
        auth_headers = self._get_auth_headers("DELETE", path)
        
        resp = self._session.delete(url, headers={**self._headers(), **auth_headers}, timeout=10)
        resp.raise_for_status()
    
    def create_quote(self, rfq_id: str, yes_bid: str, no_bid: str, rest_remainder: bool = True) -> Dict[str, Any]:
        """Create a quote for an RFQ.
        
        Args:
            rfq_id: ID of the RFQ to quote on
            yes_bid: Bid price for YES contracts (in dollars, e.g., "0.2300")
            no_bid: Bid price for NO contracts (in dollars, e.g., "0.2300")
            rest_remainder: Whether to rest the remainder of the quote after execution
            
        Returns:
            Dictionary containing the created quote data
        """
        path = "/trade-api/v2/communications/quotes"
        url = f"{self.api_base}{path}"
        
        # Use the correct Kalshi API format with string values
        # Keep bid values as strings as the API expects them
        try:
            # Validate that the strings are valid numbers
            float(yes_bid)
            float(no_bid)
        except ValueError:
            print(f"⚠️  Invalid price format: {yes_bid}, {no_bid}")
            yes_bid = "0.50"  # Default price as string
            no_bid = "0.50"   # Default price as string
        
        # Prepare request body with string values (as Kalshi API expects)
        body = {
            "rfq_id": rfq_id,
            "yes_bid": yes_bid,  # String, as API expects
            "no_bid": no_bid,    # String, as API expects
            "rest_remainder": rest_remainder
        }
        
        auth_headers = self._get_auth_headers("POST", path)
        headers = {**self._headers(), **auth_headers}
        
        print(f"🎯 Creating quote for RFQ {rfq_id}: YES={yes_bid}, NO={no_bid}")
        
        print(f"📤 Sending request to Kalshi API: {body}")
        print(f"🔍 Request details:")
        print(f"   URL: {url}")
        print(f"   Headers: {headers}")
        print(f"   Body: {body}")
        print(f"   Body types: rfq_id={type(body['rfq_id'])}, yes_bid={type(body['yes_bid'])}, no_bid={type(body['no_bid'])}, rest_remainder={type(body['rest_remainder'])}")
        
        resp = self._session.post(url, headers=headers, json=body, timeout=10)
        
        # Log detailed response for debugging
        print(f"📥 Response status: {resp.status_code}")
        print(f"📥 Response headers: {dict(resp.headers)}")
        
        try:
            result = resp.json()
            print(f"📥 Response body: {result}")
        except:
            print(f"📥 Response text: {resp.text}")
        
        # Check for errors and provide detailed error messages
        if resp.status_code not in [200, 201]:  # 201 is also success for quote creation
            try:
                error_data = resp.json()
                if 'error' in error_data:
                    error_msg = error_data['error'].get('message', 'Unknown error')
                    error_code = error_data['error'].get('code', 'unknown')
                    raise Exception(f"{error_msg} (Code: {error_code})")
                else:
                    raise Exception(f"HTTP {resp.status_code}: {resp.text}")
            except Exception as e:
                if "HTTP" in str(e):
                    raise e
                else:
                    raise Exception(f"HTTP {resp.status_code}: {str(e)}")
        
        # If we get here, the request was successful (200 or 201)
        result = resp.json()
        print(f"✅ Quote created successfully: {result.get('id', 'unknown')}")
        
        return result

    def get_positions(self, limit: Optional[int] = None, cursor: Optional[str] = None, 
                     settlement_status: Optional[str] = None, 
                     count_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get portfolio positions from Kalshi API.
        
        Args:
            limit: Number of results per page (1-1000, defaults to 100)
            cursor: Pagination cursor for next page
            settlement_status: Filter by settlement status ('settled', 'unsettled', or 'all')
            count_filter: Comma-separated list of fields that must be non-zero
                         (e.g., 'position,total_traded,resting_order_count')
            
        Returns:
            Dictionary containing positions data with market_positions and event_positions
        """
        path = "/trade-api/v2/portfolio/positions"
        url = f"{self.api_base}{path}"
        params: Dict[str, str] = {}
        
        if limit:
            params["limit"] = str(limit)
        if cursor:
            params["cursor"] = cursor
        if settlement_status:
            params["settlement_status"] = settlement_status
        if count_filter:
            params["count_filter"] = count_filter
        
        auth_headers = self._get_auth_headers("GET", path)
        headers = {**self._headers(), **auth_headers}
        
        print(f"\n📊 Getting Positions:")
        print(f"   URL: {url}")
        print(f"   Path: {path}")
        print(f"   Method: GET")
        print(f"   Params: {params}")
        
        resp = self._session.get(url, headers=headers, params=params, timeout=10)
        print(f"   Response Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   Response Body: {resp.text}")
        
        resp.raise_for_status()
        return resp.json()

    def create_order(self, ticker: str, side: str, action: str, count: int, yes_price: Optional[int] = None, no_price: Optional[int] = None) -> Dict[str, Any]:
        """Create an order on Kalshi.
        
        Args:
            ticker: Market ticker
            side: 'yes' or 'no'
            action: 'buy' or 'sell'
            count: Number of contracts
            yes_price: Price in cents (1-99) for YES side
            no_price: Price in cents (1-99) for NO side
            
        Returns:
            Dictionary containing order response
        """
        path = "/trade-api/v2/portfolio/orders"
        url = f"{self.api_base}{path}"
        
        payload = {
            "ticker": ticker,
            "side": side,
            "action": action,
            "count": count,
            "type": "limit"
        }
        
        # Add the appropriate price field
        if yes_price is not None:
            payload["yes_price"] = yes_price
        if no_price is not None:
            payload["no_price"] = no_price
        
        auth_headers = self._get_auth_headers("POST", path)
        headers = {**self._headers(), **auth_headers, "Content-Type": "application/json"}
        
        print(f"\n📤 Creating Order:")
        print(f"   URL: {url}")
        print(f"   Path: {path}")
        print(f"   Method: POST")
        print(f"   Payload: {payload}")
        
        resp = self._session.post(url, json=payload, headers=headers, timeout=10)
        print(f"   Response Status: {resp.status_code}")
        print(f"   Response Body: {resp.text}")
        
        if resp.status_code != 201:
            # Parse the error response to get more details
            try:
                error_data = resp.json()
                error_msg = error_data.get('error', {}).get('message', resp.text)
                raise Exception(f"Kalshi API Error: {error_msg}")
            except (ValueError, KeyError):
                pass
        
        resp.raise_for_status()
        return resp.json()


