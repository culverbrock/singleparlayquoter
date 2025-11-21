# Quick Start Guide

> 🆕 **Need detailed setup instructions?** See [**SETUP_GUIDE.md**](./SETUP_GUIDE.md) for step-by-step credential setup!

## Prerequisites

- Python 3.7+
- Kalshi API credentials (see SETUP_GUIDE.md for how to get these)

## To Run

```bash
cd "/Users/brockculver/kalshi rfq/single_parlay_quoter"
pip install -r requirements.txt  # First time only
python3 app.py
```

Or use the start script:
```bash
./start.sh
```

## Access

Open your browser to: **http://localhost:5002**

## First-Time Setup (In Browser)

1. **Enter your Kalshi API Key ID** in the text field
2. **Upload your private key file** (.pem or .key):
   - Drag & drop it onto the upload box, OR
   - Click "Browse Files" to select it
3. **Click "Connect"** to start the WebSocket
4. Your credentials are saved in your browser for next time!

> Don't have credentials yet? See [SETUP_GUIDE.md](./SETUP_GUIDE.md) for detailed instructions on getting them from Kalshi.

## What You'll See

1. **API Credentials Section** - Enter your Kalshi credentials here
2. **Quote Prices** - Editable YES/NO bid prices
3. **Connection Status** - Shows if WebSocket is connected
4. **Stats** - RFQ count and quote count
5. **All RFQs Feed** (left) - All incoming RFQs (color-coded)
6. **Matching RFQs Feed** (right) - Only RFQs matching your target
7. **Quote Feed** - All quotes sent with full request/response
8. **Accepted Quotes** - Quotes that were accepted
9. **Leg Builder** - Build custom target parlays

## Default Quote Prices

- **YES Bid**: $0.001 (0.1 cents)
- **NO Bid**: $0.56 (56 cents)

You can change these in the UI and click "Update Prices".

## How to Use

### Basic Flow:

1. **Start the app** (port 5002)
2. **Enter credentials** in the browser UI
3. **Click "Connect"** to start WebSocket
4. **Click "Show Builder"** to open the leg builder
5. **Wait for legs to populate** (happens as RFQs come through)
6. **Select the legs** you want to target (click to select/deselect)
7. **Click "Activate Target"** to start quoting on those legs
8. **Watch the feeds** for matching RFQs and quotes

### Advanced Options:

- **Change quote prices** in the "Quote Prices" section
- **Enable Auto-Confirm** to automatically confirm accepted quotes
- **Clear matches** to reset the matching RFQs feed
- **Monitor multiple targets** by updating your leg selection

## Target Selection

The app now supports **dynamic target building**:
- Legs are discovered automatically from the RFQ stream
- You select which legs to target using the Leg Builder
- Only RFQs containing ALL your selected legs will be quoted
- You can change your target at any time

## Common Use Cases

### 1. Quote on a specific 2-leg parlay
1. Open Leg Builder
2. Select 2 legs (e.g., "YES KXNFLGAME-49ERS" + "YES KXNFLSINGLEGAME-CMMCCAFFREY-REC")
3. Click "Activate Target"
4. App will now quote on any RFQ containing both legs

### 2. Quote on a player prop + game outcome combo
1. Wait for legs to populate in the builder
2. Select a player prop (e.g., "Josh Allen Touchdown")
3. Select a game outcome (e.g., "Buffalo Win")
4. Click "Activate Target"

### 3. Monitor multiple similar parlays
1. Select several related legs
2. Activate target
3. Watch both feeds to see which combinations are being requested

## Files Structure

```
single_parlay_quoter/
├── app.py                          # Main Flask app
├── websocket_simple_client.py      # WebSocket client
├── templates/
│   └── index.html                  # UI with leg builder
├── requirements.txt                # Dependencies
├── start.sh                        # Start script
├── SETUP_GUIDE.md                  # Detailed credential setup
├── README.md                       # Full documentation
└── QUICKSTART.md                   # This file
```

## Logs

Watch the terminal for:
- 📨 RFQ received (no match / match)
- 📤 Sending quote for RFQ
- ✅ Quote sent successfully
- 🎯 Quote accepted/matched
- 🗑️ RFQ deleted

## Troubleshooting

**Connection fails?**
- Check API Key ID has no extra spaces
- Verify .pem file is correct
- See SETUP_GUIDE.md for credential help

**No legs appearing?**
- Wait for RFQs to come through (takes a few minutes)
- Make sure WebSocket is connected
- Try during active trading hours

**Quotes not sending?**
- Check Quote Feed for error messages
- Verify your Kalshi account has quoting permissions
- Check terminal logs for API errors

---

**Ready to go! Run `python3 app.py` and open http://localhost:5002**

For detailed credential setup: [SETUP_GUIDE.md](./SETUP_GUIDE.md)  
For full feature docs: [README.md](./README.md)

