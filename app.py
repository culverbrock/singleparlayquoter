#!/usr/bin/env python3
"""
Single Parlay Quoter - Dynamic WebSocket integration for custom parlays
Select legs from the UI to build your target parlay
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import sys

# Import from local kalshi_client
from kalshi_client import KalshiClient

# Load environment
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'single-parlay-quoter-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Quote configuration
QUOTE_YES_BID = "0.0010"  # $0.001 (0.1 cents) for YES
QUOTE_NO_BID = "0.5600"   # $0.56 (56 cents) for NO

# State
rfq_history = []
quote_history = []
accepted_quotes = []
auto_confirm_enabled = False
ws_client = None
ws_connected = False

# User credentials (set when WebSocket connects)
user_api_key_id = None
user_private_key_path = None

# Leg tracking for dynamic target building
available_legs = {}  # {market_type: {leg_ticker: leg_description}}
selected_target_legs = []  # List of selected leg tickers that define the target RFQ


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get current connection status."""
    return jsonify({
        'connected': ws_connected,
        'target_market': {
            'description': f'{len(selected_target_legs)} legs selected',
            'legs': selected_target_legs,
            'yes_bid': QUOTE_YES_BID,
            'no_bid': QUOTE_NO_BID
        },
        'stats': {
            'rfqs_seen': len(rfq_history),
            'quotes_sent': len(quote_history)
        }
    })


@app.route('/api/rfq-history')
def get_rfq_history():
    """Get RFQ history for our target market."""
    return jsonify({
        'rfqs': rfq_history[-50:]  # Last 50
    })


@app.route('/api/quote-history')
def get_quote_history():
    """Get quote history."""
    return jsonify({
        'quotes': quote_history[-50:]  # Last 50
    })


@app.route('/api/accepted-quotes')
def get_accepted_quotes():
    """Get accepted quotes history."""
    return jsonify({
        'quotes': accepted_quotes[-50:],  # Last 50
        'auto_confirm_enabled': auto_confirm_enabled
    })


@app.route('/api/auto-confirm/toggle', methods=['POST'])
def toggle_auto_confirm():
    """Toggle auto-confirm setting."""
    global auto_confirm_enabled
    auto_confirm_enabled = not auto_confirm_enabled
    logger.info(f"🤖 Auto-confirm {'enabled' if auto_confirm_enabled else 'disabled'}")
    
    # Emit to all connected clients
    socketio.emit('auto_confirm_changed', {'enabled': auto_confirm_enabled})
    
    return jsonify({
        'auto_confirm_enabled': auto_confirm_enabled
    })


@app.route('/api/quote-prices/update', methods=['POST'])
def update_quote_prices():
    """Update quote prices."""
    global QUOTE_YES_BID, QUOTE_NO_BID
    data = request.get_json()
    
    yes_bid = data.get('yes_bid')
    no_bid = data.get('no_bid')
    
    if yes_bid is not None:
        QUOTE_YES_BID = str(yes_bid)
        logger.info(f"💰 Updated YES bid to: {QUOTE_YES_BID}")
    
    if no_bid is not None:
        QUOTE_NO_BID = str(no_bid)
        logger.info(f"💰 Updated NO bid to: {QUOTE_NO_BID}")
    
    return jsonify({
        'yes_bid': QUOTE_YES_BID,
        'no_bid': QUOTE_NO_BID
    })


@app.route('/api/confirm-quote/<quote_id>', methods=['POST'])
def manual_confirm_quote(quote_id):
    """Manually confirm a quote."""
    # Find the accepted quote
    accepted_quote = None
    for quote in accepted_quotes:
        if quote.get('quote_id') == quote_id:
            accepted_quote = quote
            break
    
    if not accepted_quote:
        return jsonify({'error': 'Quote not found'}), 404
    
    # Trigger confirmation
    asyncio.create_task(confirm_quote(
        quote_id,
        accepted_quote.get('rfq_id'),
        accepted_quote.get('market_ticker', '')
    ))
    
    return jsonify({'status': 'confirming', 'quote_id': quote_id})


@app.route('/api/available-legs')
def get_available_legs():
    """Get all available legs organized by market type."""
    return jsonify({
        'legs': available_legs
    })


@app.route('/api/target-legs', methods=['GET'])
def get_target_legs():
    """Get currently selected target legs."""
    return jsonify({
        'target_legs': selected_target_legs
    })


@app.route('/api/target-legs', methods=['POST'])
def set_target_legs():
    """Set target legs to match."""
    global selected_target_legs
    data = request.get_json()
    
    selected_target_legs = data.get('target_legs', [])
    logger.info(f"🎯 Updated target legs: {selected_target_legs}")
    
    return jsonify({
        'target_legs': selected_target_legs,
        'count': len(selected_target_legs)
    })


def extract_market_type(leg_ticker, side=""):
    """Extract structured market type from a leg ticker and side.
    Returns (sport, category) tuple.
    """
    try:
        ticker_upper = leg_ticker.upper()
        side_upper = side.upper()
        
        # NFL
        if 'NFL' in ticker_upper:
            # Check for spreads and totals based on ticker patterns or side
            if 'SPRD' in ticker_upper or 'SPREAD' in ticker_upper:
                return ('NFL', 'Spreads')
            elif 'TOTL' in ticker_upper or 'TOTAL' in ticker_upper or 'OVER' in side_upper or 'UNDER' in side_upper:
                return ('NFL', 'Totals')
            elif 'NFLGAME' in ticker_upper:
                return ('NFL', 'Moneylines')
            elif 'NFLANYTD' in ticker_upper or 'NFLFIRSTTD' in ticker_upper:
                return ('NFL', 'Player Props - Touchdowns')
            elif 'NFLSINGLEGAME' in ticker_upper or 'VENFLSINGLEGAME' in ticker_upper:
                # Try to parse what type of player prop
                if 'PASS' in ticker_upper or 'YDS' in ticker_upper:
                    return ('NFL', 'Player Props - Passing')
                elif 'RUSH' in ticker_upper:
                    return ('NFL', 'Player Props - Rushing')
                elif 'REC' in ticker_upper:
                    return ('NFL', 'Player Props - Receiving')
                else:
                    return ('NFL', 'Player Props - Other')
            else:
                return ('NFL', 'Other')
        
        # NBA
        elif 'NBA' in ticker_upper:
            # Check for spreads and totals based on ticker patterns or side
            if 'SPRD' in ticker_upper or 'SPREAD' in ticker_upper:
                return ('NBA', 'Spreads')
            elif 'TOTL' in ticker_upper or 'TOTAL' in ticker_upper or 'OVER' in side_upper or 'UNDER' in side_upper:
                return ('NBA', 'Totals')
            elif 'NBAGAME' in ticker_upper:
                return ('NBA', 'Moneylines')
            elif 'NBAPTS' in ticker_upper or 'POINTS' in ticker_upper:
                return ('NBA', 'Player Props - Points')
            elif 'AST' in ticker_upper or 'ASSISTS' in ticker_upper:
                return ('NBA', 'Player Props - Assists')
            elif 'REB' in ticker_upper or 'REBOUNDS' in ticker_upper:
                return ('NBA', 'Player Props - Rebounds')
            elif 'THREE' in ticker_upper or '3PT' in ticker_upper:
                return ('NBA', 'Player Props - Threes')
            elif 'NBASINGLEGAME' in ticker_upper or 'VENBASINGLEGAME' in ticker_upper:
                return ('NBA', 'Player Props - Other')
            else:
                return ('NBA', 'Other')
        
        # NHL
        elif 'NHL' in ticker_upper:
            if 'SPRD' in ticker_upper or 'SPREAD' in ticker_upper:
                return ('NHL', 'Spreads')
            elif 'TOTL' in ticker_upper or 'TOTAL' in ticker_upper or 'OVER' in side_upper or 'UNDER' in side_upper:
                return ('NHL', 'Totals')
            elif 'NHLGAME' in ticker_upper:
                return ('NHL', 'Moneylines')
            else:
                return ('NHL', 'Other')
        
        # Multi-game parlays
        elif 'SPORTSMULTIGAME' in ticker_upper:
            return ('Other', 'Multi-Game Parlays')
        
        else:
            return ('Other', 'Unknown')
            
    except Exception as e:
        logger.error(f"Error extracting market type: {e}")
        return ('Other', 'Unknown')


def matches_target_market(rfq_data):
    """Check if an RFQ matches our selected target legs."""
    global selected_target_legs
    
    try:
        # If no target legs selected, nothing matches
        if not selected_target_legs:
            return False
        
        # Extract legs from RFQ
        rfq_legs = rfq_data.get('mve_selected_legs', [])
        rfq_leg_tickers = set()
        
        for leg in rfq_legs:
            leg_market = leg.get('market_ticker', '')
            side = leg.get('side', '')
            # Create a unique identifier for this leg (side + ticker)
            leg_id = f"{side}:{leg_market}".upper()
            rfq_leg_tickers.add(leg_id)
        
        # Convert selected legs to same format
        selected_set = set(leg.upper() for leg in selected_target_legs)
        
        # Check if all selected legs are in the RFQ
        if selected_set.issubset(rfq_leg_tickers):
            logger.info(f"✅ Found matching RFQ with legs: {rfq_leg_tickers}")
            return True
            
        return False
    except Exception as e:
        logger.error(f"Error checking market match: {e}")
        return False


async def handle_rfq(rfq_data):
    """Handle an incoming RFQ (matches our target or not)."""
    global available_legs
    
    try:
        rfq_id = rfq_data.get('id', 'unknown')
        market_ticker = rfq_data.get('market_ticker', 'unknown')
        
        # Extract legs if available
        legs = rfq_data.get('mve_selected_legs', [])
        leg_descriptions = []
        for leg in legs:
            event_ticker = leg.get('event_ticker', '')
            leg_market = leg.get('market_ticker', '')
            side = leg.get('side', '')
            leg_descriptions.append(f"{side} {leg_market}")
            
            # Track this leg for the available legs list
            leg_id = f"{side}:{leg_market}"
            sport, category = extract_market_type(leg_market, side)
            
            # Add to available legs with hierarchical structure
            if sport not in available_legs:
                available_legs[sport] = {}
            
            if category not in available_legs[sport]:
                available_legs[sport][category] = {}
            
            if leg_id not in available_legs[sport][category]:
                available_legs[sport][category][leg_id] = f"{side} {leg_market}"
                logger.debug(f"Added new leg to {sport} -> {category}: {leg_id}")
        
        # Check if this matches our target market
        matches = matches_target_market(rfq_data)
        
        # Add to history
        rfq_entry = {
            'timestamp': datetime.now().isoformat(),
            'rfq_id': rfq_id,
            'market_ticker': market_ticker,
            'contracts': rfq_data.get('contracts', 0),
            'target_cost': rfq_data.get('target_cost_dollars', rfq_data.get('target_cost_centi_cents', 0)),
            'legs': leg_descriptions,
            'matches': matches
        }
        rfq_history.append(rfq_entry)
        
        # Emit to frontend immediately
        socketio.emit('rfq_received', rfq_entry)
        
        if matches:
            logger.info(f"✅ RFQ MATCH: {rfq_id}")
            logger.info(f"   Market: {market_ticker}")
            logger.info(f"   Legs: {leg_descriptions}")
            logger.info(f"   Contracts: {rfq_data.get('contracts', 0)}")
            
            # Create quote for matching RFQ
            await send_quote(rfq_id, market_ticker)
        else:
            logger.info(f"📨 RFQ (no match): {rfq_id}")
            logger.info(f"   Market: {market_ticker}")
        
    except Exception as e:
        logger.error(f"Error handling RFQ: {e}", exc_info=True)


async def send_quote(rfq_id, market_ticker):
    """Send a quote for the RFQ."""
    global user_api_key_id, user_private_key_path
    
    try:
        # Use user-provided credentials or fall back to environment
        api_key_id = user_api_key_id or os.getenv('KALSHI_API_KEY_ID')
        private_key_path = user_private_key_path or os.getenv('KALSHI_PRIVATE_KEY_PATH')
        
        if not os.path.isabs(private_key_path):
            private_key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), private_key_path)
        
        client = KalshiClient(
            api_base='https://api.elections.kalshi.com',
            api_key_id=api_key_id,
            private_key_path=private_key_path
        )
        
        # Create quote
        logger.info(f"📤 Sending quote for RFQ {rfq_id}")
        logger.info(f"   YES bid: {QUOTE_YES_BID}")
        logger.info(f"   NO bid: {QUOTE_NO_BID}")
        
        # Prepare the request payload for logging
        request_payload = {
            "rfq_id": rfq_id,
            "yes_bid": QUOTE_YES_BID,
            "no_bid": QUOTE_NO_BID,
            "rest_remainder": False
        }
        logger.info(f"   Request payload: {request_payload}")
        
        result = client.create_quote(
            rfq_id=rfq_id,
            yes_bid=QUOTE_YES_BID,
            no_bid=QUOTE_NO_BID,
            rest_remainder=False
        )
        
        quote_id = result.get('quote', {}).get('quote_id') if 'quote' in result else result.get('quote_id')
        
        # Prepare response payload for display
        response_payload = {
            "status": "201 Created",
            "body": result
        }
        logger.info(f"   Response payload: {response_payload}")
        
        # Add to history
        quote_entry = {
            'timestamp': datetime.now().isoformat(),
            'rfq_id': rfq_id,
            'quote_id': quote_id,
            'market_ticker': market_ticker,
            'yes_bid': QUOTE_YES_BID,
            'no_bid': QUOTE_NO_BID,
            'request_payload': request_payload,
            'response_payload': response_payload,
            'status': 'sent',
            'matched': False  # Will be updated if we get a match notification
        }
        quote_history.append(quote_entry)
        
        # Emit to frontend immediately
        socketio.emit('quote_sent', quote_entry)
        
        logger.info(f"✅ Quote sent successfully: {quote_id}")
        
        return quote_id
        
    except Exception as e:
        logger.error(f"Error sending quote: {e}", exc_info=True)
        
        # Prepare the request payload for logging (even on error)
        request_payload = {
            "rfq_id": rfq_id,
            "yes_bid": QUOTE_YES_BID,
            "no_bid": QUOTE_NO_BID,
            "rest_remainder": False
        }
        
        # Try to extract response details from HTTPError
        response_payload = None
        if hasattr(e, 'response') and e.response is not None:
            try:
                response_payload = {
                    "status": f"{e.response.status_code} {e.response.reason}",
                    "body": e.response.json() if e.response.text else {}
                }
            except:
                response_payload = {
                    "status": str(e),
                    "body": {}
                }
        else:
            response_payload = {
                "status": "Error",
                "body": {"error": str(e)}
            }
        
        # Add error to history
        quote_entry = {
            'timestamp': datetime.now().isoformat(),
            'rfq_id': rfq_id,
            'market_ticker': market_ticker,
            'yes_bid': QUOTE_YES_BID,
            'no_bid': QUOTE_NO_BID,
            'request_payload': request_payload,
            'response_payload': response_payload,
            'status': 'error',
            'error': str(e)
        }
        quote_history.append(quote_entry)
        socketio.emit('quote_error', quote_entry)


async def confirm_quote(quote_id, rfq_id, market_ticker):
    """Confirm an accepted quote."""
    global accepted_quotes, user_api_key_id, user_private_key_path
    
    try:
        # Use user-provided credentials or fall back to environment
        api_key_id = user_api_key_id or os.getenv('KALSHI_API_KEY_ID')
        private_key_path = user_private_key_path or os.getenv('KALSHI_PRIVATE_KEY_PATH')
        
        if not api_key_id or not private_key_path:
            raise RuntimeError("API Key ID and private key are required for confirmation.")
        
        # Convert relative path to absolute if needed
        if not os.path.isabs(private_key_path):
            private_key_path = os.path.join(os.path.dirname(__file__), '..', private_key_path)
        
        # Initialize client
        client = KalshiClient(
            api_base='https://api.elections.kalshi.com',
            api_key_id=api_key_id,
            private_key_path=private_key_path
        )
        
        # Confirm quote
        logger.info(f"✅ Confirming quote {quote_id} for RFQ {rfq_id}")
        
        # Prepare request payload for logging
        confirmation_url = f"https://api.elections.kalshi.com/trade-api/v2/communications/quotes/{quote_id}/confirm"
        
        # Send confirmation request using the correct method
        result = client.confirm_quote(quote_id)
        
        # Prepare response payload
        response_payload = {
            "status": "200 OK",
            "body": result if result else {"confirmed": True}
        }
        logger.info(f"   Confirmation response: {response_payload}")
        
        # Find and update the accepted quote
        for quote in accepted_quotes:
            if quote.get('quote_id') == quote_id:
                quote['confirmed'] = True
                quote['confirmation_response'] = response_payload
                quote['confirmation_time'] = datetime.now().isoformat()
                
                # Emit confirmation to frontend
                socketio.emit('quote_confirmed', quote)
                break
        
        logger.info(f"✅ Quote {quote_id} confirmed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"Error confirming quote {quote_id}: {e}", exc_info=True)
        
        # Prepare error response
        response_payload = None
        if hasattr(e, 'response') and e.response is not None:
            try:
                response_payload = {
                    "status": f"{e.response.status_code} {e.response.reason}",
                    "body": e.response.json() if e.response.text else {}
                }
            except:
                response_payload = {
                    "status": str(e),
                    "body": {}
                }
        else:
            response_payload = {
                "status": "Error",
                "body": {"error": str(e)}
            }
        
        # Update the accepted quote with error
        for quote in accepted_quotes:
            if quote.get('quote_id') == quote_id:
                quote['confirmed'] = False
                quote['confirmation_error'] = str(e)
                quote['confirmation_response'] = response_payload
                
                # Emit error to frontend
                socketio.emit('quote_confirmation_error', quote)
                break


def handle_ws_message(message_data):
    """Handle incoming WebSocket message."""
    try:
        msg_type = message_data.get('type')
        
        if msg_type == 'rfq_created':
            rfq = message_data.get('msg', {})
            
            # Handle ALL RFQs (will highlight matches in UI)
            asyncio.create_task(handle_rfq(rfq))
        
        elif msg_type == 'rfq_deleted':
            rfq_id = message_data.get('msg', {}).get('rfq_id', 'unknown')
            logger.info(f"🗑️ RFQ deleted: {rfq_id}")
                
        elif msg_type == 'quote_accepted':
            # Handle accepted quote
            quote_msg = message_data.get('msg', {})
            quote_id = quote_msg.get('quote_id')
            rfq_id = quote_msg.get('rfq_id')
            
            logger.info(f"🎯 Quote accepted: {quote_id} for RFQ {rfq_id}")
            
            # Create accepted quote entry
            accepted_entry = {
                'timestamp': datetime.now().isoformat(),
                'quote_id': quote_id,
                'rfq_id': rfq_id,
                'market_ticker': quote_msg.get('market_ticker', ''),
                'yes_price': quote_msg.get('yes_price'),
                'no_price': quote_msg.get('no_price'),
                'confirmed': False,
                'auto_confirmed': False
            }
            accepted_quotes.append(accepted_entry)
            
            # Emit to frontend
            socketio.emit('quote_accepted', accepted_entry)
            
            # Auto-confirm if enabled
            if auto_confirm_enabled:
                logger.info(f"🤖 Auto-confirming quote {quote_id}")
                accepted_entry['auto_confirmed'] = True
                asyncio.create_task(confirm_quote(quote_id, rfq_id, quote_msg.get('market_ticker', '')))
            
            # Also update quote history to show match
            for quote in quote_history:
                if quote.get('quote_id') == quote_id:
                    quote['matched'] = True
                    quote['matched_at'] = datetime.now().isoformat()
                    socketio.emit('quote_matched', quote)
                    break
        
        elif msg_type in ['quote_created', 'quote_confirmed']:
            # Update quote history to show match
            quote_id = message_data.get('msg', {}).get('quote_id')
            for quote in quote_history:
                if quote.get('quote_id') == quote_id:
                    quote['matched'] = True
                    quote['matched_at'] = datetime.now().isoformat()
                    socketio.emit('quote_matched', quote)
                    logger.info(f"🎯 Quote matched: {quote_id}")
                    break
                    
    except Exception as e:
        logger.error(f"Error handling WS message: {e}", exc_info=True)


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info("🔌 Client connected to SocketIO")
    emit('connection_status', {'connected': ws_connected})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info("🔌 Client disconnected from SocketIO")


@socketio.on('start_websocket')
def start_websocket(credentials=None):
    """Start the Kalshi WebSocket connection with user-provided credentials."""
    global ws_client, ws_connected, user_api_key_id, user_private_key_path
    
    logger.info("🚀 Starting WebSocket connection...")
    
    # Extract credentials from the payload
    api_key = None
    private_key_contents = None
    
    if credentials:
        api_key = credentials.get('api_key')
        private_key_contents = credentials.get('private_key_contents')
    
    # Validate credentials
    if not api_key or not private_key_contents:
        logger.error("❌ Missing API credentials")
        emit('connection_status', {
            'connected': False, 
            'error': 'API Key and Private Key file are required'
        })
        return
    
    # Store credentials globally for quoting
    user_api_key_id = api_key
    
    # Save private key to a temporary file
    import tempfile
    try:
        # Create a temporary file for the private key
        temp_key_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False)
        temp_key_file.write(private_key_contents)
        temp_key_file.close()
        user_private_key_path = temp_key_file.name
        
        logger.info(f"🔑 Using API Key: {api_key[:10]}...")
        logger.info(f"🔑 Saved private key to: {user_private_key_path}")
        
        # Import and start WebSocket client
        from websocket_simple_client import SimpleWebSocketClient
        
        ws_client = SimpleWebSocketClient(
            message_callback=handle_ws_message,
            api_key_id=api_key,
            private_key_path=user_private_key_path
        )
        
        # Start in background
        import threading
        def run_ws():
            asyncio.run(ws_client.connect_and_listen())
        
        ws_thread = threading.Thread(target=run_ws, daemon=True)
        ws_thread.start()
        
        ws_connected = True
        emit('connection_status', {'connected': True})
        logger.info("✅ WebSocket connection started")
        
    except Exception as e:
        logger.error(f"Error starting WebSocket: {e}", exc_info=True)
        emit('connection_status', {'connected': False, 'error': str(e)})


@socketio.on('stop_websocket')
def stop_websocket():
    """Stop the Kalshi WebSocket connection."""
    global ws_client, ws_connected
    
    logger.info("🛑 Stopping WebSocket connection...")
    
    try:
        if ws_client:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(ws_client.disconnect())
            loop.close()
            
        ws_connected = False
        ws_client = None
        emit('connection_status', {'connected': False})
        logger.info("✅ WebSocket connection stopped")
        
    except Exception as e:
        logger.error(f"Error stopping WebSocket: {e}", exc_info=True)
        emit('connection_status', {'connected': False, 'error': str(e)})


if __name__ == '__main__':
    logger.info("="*80)
    logger.info("🎯 Single Parlay Quoter Starting")
    logger.info("="*80)
    logger.info("Select legs from the UI to build your target parlay")
    logger.info(f"YES Bid: {QUOTE_YES_BID}")
    logger.info(f"NO Bid: {QUOTE_NO_BID}")
    logger.info("="*80)
    
    # Use PORT from environment (Railway) or default to 5002 for local
    port = int(os.getenv('PORT', 5002))
    logger.info(f"Starting on port {port}")
    
    socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True, use_reloader=False)

