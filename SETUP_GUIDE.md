# Single Parlay Quoter - Setup Guide

## 🚀 Get Started in 5 Minutes (No Technical Knowledge Required)

This guide will help you get your Kalshi API credentials and start using the Single Parlay Quoter.

---

## Step 1: Get Your Kalshi API Credentials (5 minutes)

### What You Need:
1. **API Key ID** - A unique identifier string
2. **Private Key File** - A `.pem` or `.key` file that proves you own the API key

### How to Get Them:

#### 1.1 Log in to Kalshi

Go to [kalshi.com](https://kalshi.com) and sign in to your account.

#### 1.2 Navigate to API Settings

- Click on your **profile picture or avatar** in the top-right corner
- Select **"Settings"** or **"Account Settings"**
- Look for a section called **"API"**, **"Developer"**, or **"API Keys"**

> **Can't find it?** Look in the sidebar or tabs for "Developer Tools", "API Access", or similar.

#### 1.3 Generate a New API Key

- Click the button that says **"Create API Key"**, **"Generate New Key"**, or **"Add API Key"**
- You may need to:
  - Give your key a name (e.g., "Parlay Quoter")
  - Confirm your password
  - Complete 2FA if enabled

#### 1.4 Save Your Credentials Immediately

After generating the key, Kalshi will show you:

1. **API Key ID**: 
   - Looks like: `12345678-abcd-efgh-ijkl-mnopqrstuvwx`
   - Copy this and paste it somewhere safe (or you can enter it directly in the app)

2. **Private Key File**: 
   - A file named something like `kalshi_private_key.pem`, `.key`, or `api_key_12345678.pem`
   - This file will **automatically download** to your computer
   - **⚠️ CRITICAL**: This file can only be downloaded ONCE. If you lose it, you must generate a new API key!

#### 1.5 Store Your Files Safely

- Keep the `.pem` or `.key` file in a safe location on your computer
- Don't share it with anyone
- Don't commit it to version control
- If you lose it, you'll need to generate a new API key

---

## Step 2: Install the App (One-time Setup)

### 2.1 Install Python Dependencies

Open a terminal/command prompt and run:

```bash
cd /path/to/single_parlay_quoter
pip install -r requirements.txt
```

> **Note**: You only need to do this once, unless dependencies change.

---

## Step 3: Run the App

### 3.1 Start the Server

In your terminal, run:

```bash
python3 app.py
```

You should see:
```
🎯 Single Parlay Quoter Starting
...
Running on http://0.0.0.0:5002
```

### 3.2 Open in Browser

Open your web browser and go to:

```
http://localhost:5002
```

---

## Step 4: Connect with Your Credentials

### 4.1 Enter API Key ID

1. Look for the **"API Credentials (Required)"** section at the top of the page
2. In the **"Kalshi API Key ID"** field, paste your API Key ID
3. The app will automatically save it in your browser for next time

### 4.2 Upload Private Key File

You have two options:

**Option A: Drag & Drop**
1. Simply drag your `.pem` or `.key` file from your computer
2. Drop it onto the upload box (it will turn blue when you drag over it)
3. You should see: **"✓ Loaded: [filename]"** in green

**Option B: Browse Files**
1. Click the blue **"Browse Files"** button
2. Browse to where you saved the `.pem` or `.key` file from Kalshi
3. Select the file
4. You should see: **"✓ Loaded: [filename]"** in green

### 4.3 Click Connect

1. Click the big **"Connect"** button
2. The status should change to **"Connected"** with a dark dot
3. You should start seeing RFQs appear in the feed

---

## Step 5: Build and Activate Your Target Parlay

### 5.1 Open the Leg Builder

1. Scroll down to **"RFQ Leg Builder"**
2. Click **"Show Builder"**

### 5.2 Wait for Legs to Populate

- As RFQs come through the WebSocket, the builder will populate with available legs
- This happens automatically - just wait a minute or two
- Legs are organized by sport (NFL, NBA, etc.) and category (Spreads, Totals, Player Props, etc.)

### 5.3 Select Your Target Legs

1. Click on the legs you want to target (they'll turn blue when selected)
2. You can select as many legs as you want for your parlay
3. The **"Current Target"** section shows what you've selected

### 5.4 Activate Your Target

1. When you're happy with your selection, click **"Activate Target"**
2. The app will now only quote on RFQs that match ALL of your selected legs
3. The monitoring panel at the top will update to show your active target

### 5.5 Adjust Quote Prices (Optional)

- In the **"Quote Prices (Editable)"** section, you can change:
  - **YES Bid**: The price you'll bid for YES side (default: $0.001)
  - **NO Bid**: The price you'll bid for NO side (default: $0.56)
- Click **"Update Prices"** after changing them

---

## Step 6: Monitor and Quote

### What Happens Now:

1. **All RFQs** appear in the left feed (color-coded: green = match, red = no match)
2. **Matching RFQs** (those containing all your target legs) appear in the right feed
3. When a matching RFQ arrives:
   - The app automatically sends a quote with your configured prices
   - The quote appears in the **Quote Feed** with full request/response details
4. If your quote is accepted:
   - It appears in the **Accepted Quotes** section
   - You can enable **Auto-Confirm** to automatically confirm accepted quotes

---

## Troubleshooting

### "Please enter API Key ID and upload a Private Key file before connecting"

- Make sure you've pasted the API Key ID (no extra spaces)
- Make sure you've uploaded the `.pem` file by clicking the upload button
- Check that it says "✓ Loaded: [filename]" under the upload button

### WebSocket won't connect

- Double-check your API Key ID is correct
- Make sure the `.pem` file you uploaded is the right one
- Check the terminal/console for error messages
- Verify your API key hasn't been deleted on Kalshi

### Not seeing any RFQs

- RFQs only appear when someone creates them on Kalshi
- Make sure the WebSocket is connected (green dot)
- Try during active trading hours (more RFQs during the day)
- Check the terminal logs to see if RFQs are being received

### Legs not appearing in builder

- Legs populate as RFQs come through - this is normal
- Wait a few minutes for RFQs to arrive
- The more RFQs that come through, the more legs will be available
- Click "Show Builder" to refresh

### Lost my private key file

If you lost your `.pem` or `.key` file:
1. Go back to Kalshi's API settings
2. **Delete** the old API key (for security)
3. **Generate a new** API key
4. Download the new private key file
5. Update the credentials in the app

---

## Security Best Practices

✅ **DO:**
- Keep your private key file (`.pem` or `.key`) secure and private
- Store it in a safe location
- Use different API keys for different applications
- Delete old API keys you're not using

❌ **DON'T:**
- Share your API Key ID or private key file with anyone
- Commit your private key file to GitHub or version control
- Use the same API key across multiple untrusted applications
- Leave old API keys active indefinitely

---

## What Gets Stored Where?

- **Browser localStorage**: API Key ID and private key contents (for convenience)
- **Kalshi servers**: Your quotes and RFQ activity (normal Kalshi operations)
- **Nowhere else**: The app doesn't send your credentials to any other servers

Your credentials stay on your machine and are only used to authenticate with Kalshi.

---

## Need More Help?

- Check the main README.md for detailed feature documentation
- Check the terminal/console logs for error messages
- Look for error messages in the browser's developer console (F12)

---

**You're all set! Happy quoting! 🎯**

