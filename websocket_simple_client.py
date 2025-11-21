#!/usr/bin/env python3
"""
Simple WebSocket client for Kalshi Communications API
Only monitors for specific parlay market
"""

import asyncio
import json
import logging
import os
import sys
import websockets
from datetime import datetime
from dotenv import load_dotenv

# Import from local kalshi_client
from kalshi_client import KalshiClient

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

logger = logging.getLogger(__name__)


class SimpleWebSocketClient:
    """Simple WebSocket client for Kalshi Communications."""
    
    def __init__(self, message_callback=None, api_key_id=None, private_key_path=None):
        self.ws = None
        self.message_callback = message_callback
        self.connected = False
        self.should_stop = False
        
        # Get credentials from parameters or environment
        self.api_key_id = api_key_id or os.getenv('KALSHI_API_KEY_ID')
        self.private_key_path = private_key_path or os.getenv('KALSHI_PRIVATE_KEY_PATH')
        
        # Convert to absolute path if needed
        if self.private_key_path and not os.path.isabs(self.private_key_path):
            self.private_key_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                self.private_key_path
            )
        
        self.api_base = 'https://api.elections.kalshi.com'
        self.ws_url = 'wss://api.elections.kalshi.com/trade-api/ws/v2'
        
        # Create KalshiClient for authentication
        self.kalshi_client = KalshiClient(
            api_base=self.api_base,
            api_key_id=self.api_key_id,
            private_key_path=self.private_key_path
        )
    
    async def disconnect(self):
        """Disconnect from WebSocket."""
        self.should_stop = True
        if self.ws and self.connected:
            await self.ws.close()
            logger.info("🔌 WebSocket disconnected by user")
        self.connected = False
        
    def _get_auth_headers(self):
        """Get authentication headers for WebSocket connection."""
        try:
            # Use KalshiClient's authentication method
            # Format: timestamp + "GET" + "/trade-api/ws/v2"
            return self.kalshi_client._get_auth_headers("GET", "/trade-api/ws/v2")
        except Exception as e:
            logger.error(f"❌ Failed to get auth headers: {e}")
            return {}
    
    async def connect_and_listen(self):
        """Connect to WebSocket and listen for messages."""
        try:
            # Get authentication headers
            auth_headers = self._get_auth_headers()
            if not auth_headers:
                logger.error("❌ Failed to get authentication headers")
                return
            
            logger.info(f"📡 Connecting to Kalshi WebSocket...")
            logger.info(f"📋 Using API Key: {self.api_key_id[:8]}...")
            
            # Create SSL context that doesn't verify certificates (for development)
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Connect with authentication headers
            async with websockets.connect(
                self.ws_url,
                additional_headers=auth_headers,
                ssl=ssl_context,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5
            ) as websocket:
                self.ws = websocket
                self.connected = True
                logger.info("✅ WebSocket connected!")
                
                # Subscribe to communications channel
                subscribe_msg = {
                    "id": 1,
                    "cmd": "subscribe",
                    "params": {
                        "channels": ["communications"]
                    }
                }
                
                await websocket.send(json.dumps(subscribe_msg))
                logger.info("📨 Subscribed to communications channel")
                
                # Listen for messages
                message_count = 0
                async for message in websocket:
                    # Check if we should stop
                    if self.should_stop:
                        logger.info("🛑 Stop requested, closing connection")
                        break
                    
                    try:
                        message_count += 1
                        data = json.loads(message)
                        
                        # Log every message for debugging
                        msg_type = data.get('type', 'unknown')
                        
                        if msg_type == 'rfq_created':
                            rfq = data.get('msg', {})
                            market_ticker = rfq.get('market_ticker', '')
                            
                            logger.info(f"📩 RFQ #{message_count}: {market_ticker}")
                            
                            # Call callback
                            if self.message_callback:
                                self.message_callback(data)
                        
                        elif msg_type == 'rfq_deleted':
                            rfq_id = data.get('msg', {}).get('rfq_id', 'unknown')
                            logger.info(f"🗑️ RFQ deleted: {rfq_id}")
                        
                        elif msg_type in ['quote_created', 'quote_accepted', 'quote_confirmed']:
                            quote_id = data.get('msg', {}).get('quote_id', 'unknown')
                            logger.info(f"🎯 Quote event: {msg_type} - {quote_id}")
                            
                            if self.message_callback:
                                self.message_callback(data)
                        
                        elif msg_type == 'subscribed':
                            logger.info(f"✅ Subscription confirmed")
                        
                        else:
                            logger.info(f"📬 WS message type: {msg_type}")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
                        
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            self.connected = False
        except Exception as e:
            logger.error(f"Error in connect_and_listen: {e}", exc_info=True)
            self.connected = False
        finally:
            self.connected = False
            logger.info("WebSocket disconnected")


if __name__ == "__main__":
    # Test the client
    logging.basicConfig(level=logging.INFO)
    
    def test_callback(data):
        print(f"Received: {data.get('type')}")
    
    client = SimpleWebSocketClient(message_callback=test_callback)
    asyncio.run(client.connect_and_listen())

