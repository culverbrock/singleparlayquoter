# Single Parlay Quoter

A streamlined WebSocket integration for Kalshi that monitors and auto-quotes custom parlay markets.

> 🆕 **First time here?** Check out the [**SETUP_GUIDE.md**](./SETUP_GUIDE.md) for a step-by-step walkthrough on getting your Kalshi API credentials and starting the app!

## Features

- 🎯 **Dynamic Target Selection**: Build custom parlays by selecting legs from RFQ stream
- 📡 **Real-time WebSocket**: Connects to Kalshi Communications API
- 🤖 **Auto-quoting**: Automatically quotes with configurable prices when matching RFQs arrive
- 📊 **Clean UI**: Simple dashboard showing RFQs and quotes
- ✅ **Match Detection**: Shows when your quotes are accepted
- 🔒 **Browser-only Auth**: All credentials stored locally in your browser

## Quick Start (No Technical Setup Required!)

### Step 1: Get Your Kalshi API Credentials

1. **Log in to your Kalshi account** at [kalshi.com](https://kalshi.com)

2. **Navigate to API Settings**:
   - Click on your profile/avatar (top right)
   - Select "Settings" or "Account Settings"
   - Find the "API" or "Developer" section

3. **Generate API Credentials**:
   - Click "Create API Key" or "Generate New Key"
   - You'll receive two things:
     - **API Key ID**: A string like `abcd1234-5678-90ef-ghij-klmnopqrstuv`
     - **Private Key File**: A `.pem` file that downloads to your computer (e.g., `kalshi_private_key.pem`)
   - ⚠️ **IMPORTANT**: Save both immediately! The private key file can only be downloaded once.

4. **Keep your credentials safe**:
   - Don't share your API Key ID or private key with anyone
   - The private key file is needed every time you connect

### Step 2: Install and Run

1. **Install Python dependencies** (one-time setup):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app**:
   ```bash
   python3 app.py
   ```

3. **Open your browser**:
   ```
   http://localhost:5002
   ```

### Step 3: Connect with Your Credentials

1. In the browser UI, you'll see an "**API Credentials**" section at the top

2. **Enter your API Key ID**: 
   - Paste the API Key ID you got from Kalshi (the long string)

3. **Upload your Private Key File**:
   - **Drag & drop** your `.pem` or `.key` file onto the upload box, OR
   - Click "Browse Files" and select the file you downloaded from Kalshi

4. **Click "Connect"**

That's it! The app will:
- ✅ Store your credentials securely in your browser (localStorage)
- ✅ Auto-fill them next time you visit
- ✅ Connect to Kalshi's WebSocket to monitor RFQs

### Step 4: Build Your Target Parlay

1. **Click "Show Builder"** to open the leg builder panel

2. **Wait for legs to populate** as RFQs come through the WebSocket

3. **Select the legs** you want to target by clicking them (they'll turn blue)

4. **Click "Activate Target"** to start matching and quoting on those legs

## How It Works

1. **WebSocket Connection**: Connects to Kalshi's WebSocket API using your credentials and subscribes to the RFQ channel
2. **Leg Discovery**: As RFQs come through, the app extracts and categorizes all available legs by sport and market type
3. **Target Matching**: When an RFQ arrives containing all your selected target legs, it's identified as a match
4. **Auto-quoting**: When a matching RFQ arrives:
   - Logs the RFQ details
   - Immediately sends a quote with your configured prices
   - Shows the result in the UI
5. **Match Tracking**: When a quote is accepted, it updates the UI to show the match

## UI Elements

- **API Credentials Section**: Where you enter your Kalshi API Key ID and upload your private key file
- **Quote Prices**: Editable YES and NO bid prices (defaults: $0.001 for YES, $0.56 for NO)
- **Connection Status**: Shows if WebSocket is connected
- **Stats**: RFQs seen and quotes sent
- **All RFQs Feed** (left): All incoming RFQs, color-coded (green = match, red = no match)
- **Matching RFQs Feed** (right): Only RFQs that match your target legs
- **Quote Feed**: All quotes you've sent, with full request/response details
- **Accepted Quotes**: Quotes that were accepted by the RFQ creator
- **Leg Builder**: Build custom target parlays by selecting legs from discovered options

## Port

Runs on **port 5002** locally (Railway and other cloud platforms will use their own port automatically)

## 🚀 Deployment

Want to host this publicly so anyone can use it?

**See [DEPLOYMENT.md](./DEPLOYMENT.md)** for complete step-by-step instructions on deploying to:
- ⭐ **Railway** (recommended - easiest, free tier available)
- Heroku
- Render
- Google Cloud Run
- AWS

**Quick Deploy Script:**
```bash
./deploy.sh
```

This interactive script will:
- Initialize git repository
- Commit your changes
- Push to GitHub
- Provide Railway deployment instructions

**What gets deployed:**
- ✅ Application code (no credentials)
- ✅ UI and documentation
- ✅ Python dependencies
- ❌ NO private keys or sensitive data (protected by `.gitignore`)

**For users of your deployed app:**
- They access your public URL
- They enter their own Kalshi API credentials in the browser
- Everything works client-side (credentials in their browser only)

## About API Credentials

### Where are my credentials stored?

Your credentials are stored **only in your browser's localStorage**. They are:
- ✅ Never sent to any server except Kalshi's API
- ✅ Stored locally on your machine
- ✅ Only used to authenticate WebSocket connections and send quotes
- ✅ Auto-filled when you return to the app

### Do I need a `.env` file?

**No!** The `.env` file approach is optional and only for advanced users. You can use the app entirely through the browser UI by:
1. Entering your API Key ID in the input field
2. Uploading your private key file

Your browser will remember these credentials for next time.

### What if I lose my private key file?

If you lose your `.pem` file, you'll need to:
1. Go back to Kalshi's API settings
2. Delete the old API key (for security)
3. Generate a new API key (which gives you a new `.pem` file)
4. Update the credentials in the app

## Files

- `app.py` - Main Flask application
- `websocket_simple_client.py` - Simple WebSocket client
- `templates/index.html` - UI
- `requirements.txt` - Dependencies
- `README.md` - This file

## Differences from Main Integration

This is much simpler than the full Kalshi WS integration:
- ✅ Only one market
- ✅ Fixed quote prices
- ✅ No simulation API
- ✅ No adaptive pricing
- ✅ No complex quote generation
- ✅ Just monitor, quote, track

## Troubleshooting

**"Please enter API Key ID and upload a Private Key file before connecting"**
- Make sure you've pasted your API Key ID into the text field
- Make sure you've clicked "Upload Private Key File" and selected your `.pem` file
- You should see "✓ Loaded: [filename]" under the upload button

**WebSocket won't connect:**
- Verify your API Key ID is correct (no extra spaces)
- Verify your private key file is the correct `.pem` file from Kalshi
- Check the browser console (F12) and terminal logs for authentication errors
- Make sure your API key hasn't been deleted or revoked on Kalshi

**Not seeing RFQs:**
- RFQs only appear when someone requests quotes for a parlay market
- The WebSocket must be connected (green dot at the top)
- Check the terminal logs to see if RFQs are being received
- Try during active trading hours when more RFQs are likely

**Not seeing legs in the builder:**
- Legs populate automatically as RFQs come through
- Click "Show Builder" and wait a few minutes for RFQs to arrive
- The more RFQs that come through, the more legs will be available

**Quotes not sending:**
- Check the Quote Feed for error messages (shown in red)
- Verify your Kalshi account has quoting/market-maker permissions
- Check if the RFQ is still open when you try to quote (they expire quickly)
- Look at the terminal logs for detailed API error messages

**Private key won't upload:**
- Make sure the file has a `.pem` extension
- Try opening the file in a text editor - it should start with `-----BEGIN PRIVATE KEY-----`
- If the file looks corrupted, you may need to generate a new API key from Kalshi

**Credentials not saving between sessions:**
- Check that your browser allows localStorage
- Try a different browser if you're in incognito/private mode
- You can manually re-enter credentials each time if localStorage isn't working

## Logs

All activity is logged to console. Watch for:
- `📨 RFQ received for our market` - RFQ matched your target
- `📤 Sending quote` - Quote being sent
- `✅ Quote sent successfully` - Quote accepted by API
- `🎯 Quote matched` - Your quote was accepted by the RFQ creator

---

*Built for monitoring and quoting a single parlay market on Kalshi*

