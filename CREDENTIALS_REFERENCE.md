# Credentials Reference

This document shows you exactly what your Kalshi API credentials should look like.

---

## What You Need

You need **TWO things** from Kalshi to use this app:

### 1. API Key ID (a text string)
### 2. Private Key File (a .pem file)

---

## 1. API Key ID Format

### What it looks like:

```
12345678-90ab-cdef-1234-567890abcdef
```

### Characteristics:
- ✅ A string with hyphens (dashes)
- ✅ Contains letters (a-f) and numbers (0-9)
- ✅ Usually 36 characters long (including hyphens)
- ✅ Looks like a UUID/GUID format
- ✅ Case-insensitive (lowercase or uppercase works)

### Examples of valid formats:
```
abcd1234-5678-90ef-ghij-klmnopqrstuv
01234567-89ab-cdef-0123-456789abcdef
FEDCBA98-7654-3210-FEDC-BA9876543210
```

### Where to enter it:
- In the browser UI, paste it into the **"Kalshi API Key ID"** text field
- No quotes needed, just the string itself
- Make sure there are no spaces before or after

---

## 2. Private Key File Format

### File name examples:
```
kalshi_private_key.pem
api_key_12345678.pem
my_kalshi_key.pem
.key
private_key.key
```

### What it looks like inside:
When you open the `.pem` or `.key` file in a text editor, it should look like this:

```
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj
MzEfYyjiWA4R4/M2bS1+fWIcPm15j9FprYe+6VnrPPXjRw9C...
[Many more lines of random-looking characters]
...kKoWXK/T9aRYp2e8vC6qP0r3xUlMGk+C9w==
-----END PRIVATE KEY-----
```

### Characteristics:
- ✅ Starts with `-----BEGIN PRIVATE KEY-----`
- ✅ Ends with `-----END PRIVATE KEY-----`
- ✅ Contains many lines of base64-encoded characters (letters, numbers, +, /, =)
- ✅ Usually 20-40 lines long
- ✅ File extension is `.pem` or `.key`

### Common Mistakes:
- ❌ Using a `.txt` file instead of `.pem` or `.key`
- ❌ File is empty or corrupted
- ❌ File contains HTML or error messages (means download failed)
- ❌ Wrong file (e.g., a certificate instead of a private key)

### Where to upload it:
- In the browser UI, click **"📁 Upload Private Key File"**
- Select your `.pem` file
- You should see "✓ Loaded: [filename]" in green

---

## How to Get These Credentials

If you don't have these yet, follow the detailed guide in [SETUP_GUIDE.md](./SETUP_GUIDE.md).

**Quick summary:**
1. Log in to Kalshi.com
2. Go to Settings → API
3. Click "Generate API Key"
4. Copy the API Key ID
5. Download the .pem file (only available once!)
6. Save both somewhere safe

---

## Where Your Credentials Are Stored

### In the App:

When you enter your credentials in the browser:
- **API Key ID**: Stored in browser localStorage (persists between sessions)
- **Private Key**: Stored in browser localStorage (persists between sessions)

### Security:

- ✅ Only stored on **your computer** in **your browser**
- ✅ Never sent to any server except Kalshi's API
- ✅ Used only for authentication
- ✅ Can be cleared by clearing browser data

### Browser Storage Location:

To view/clear in Chrome:
1. F12 (Developer Tools)
2. Application tab
3. Storage → Local Storage → http://localhost:5002
4. Look for `kalshi_api_key` and `kalshi_private_key_contents`

---

## Testing Your Credentials

### ✅ Good Signs:

When you enter credentials and click "Connect":
- Status changes to "Connected" with a dark/green dot
- RFQs start appearing in the feed
- Terminal shows "✅ WebSocket connected"

### ❌ Bad Signs:

If something is wrong:
- Error message: "API Key ID and Private Key are required"
  - → You didn't enter both credentials
- Error message: "Failed to get authentication headers"
  - → Private key file is wrong format or corrupted
- Error message: "WebSocket error" or "401 Unauthorized"
  - → API Key ID is incorrect or the key was deleted on Kalshi
- Status stays "Disconnected"
  - → Check terminal/console for error messages

---

## Common Issues and Solutions

### "I can't find my .pem file"

- Check your Downloads folder
- Search your computer for `*.pem`
- If you can't find it, you'll need to generate a new API key on Kalshi

### "My .pem or .key file won't upload"

- Make sure it has the `.pem` or `.key` extension (not `.txt`)
- Open it in a text editor - it should start with `-----BEGIN PRIVATE KEY-----`
- If it looks wrong, generate a new API key on Kalshi
- If the file picker doesn't show your file, try typing the filename directly or selecting "All Files"

### "Connection works but then disconnects"

- Kalshi API key might have been revoked
- Check if the key still exists in your Kalshi account settings
- Network connection issues
- Try generating a new key

### "I lost my private key file"

You **cannot** recover a lost private key. You must:
1. Go to Kalshi.com → Settings → API
2. Delete the old API key (for security)
3. Generate a new API key
4. Download the new .pem file
5. Update the app with new credentials

---

## Example: Complete Setup

Here's what a successful setup looks like:

### Step 1: You have these files
```
API Key ID: 12345678-90ab-cdef-1234-567890abcdef
Private Key: kalshi_private_key.pem (contains BEGIN/END PRIVATE KEY)
```

### Step 2: In the browser
1. Paste `12345678-90ab-cdef-1234-567890abcdef` into "Kalshi API Key ID"
2. Click "Upload Private Key File" and select `kalshi_private_key.pem`
3. See: "✓ Loaded: kalshi_private_key.pem"

### Step 3: Connect
1. Click "Connect"
2. Status changes to "Connected"
3. RFQs start appearing

### Step 4: Done!
- Next time you visit, credentials are already filled in
- Just click "Connect" and you're ready

---

## Need More Help?

- Detailed setup: [SETUP_GUIDE.md](./SETUP_GUIDE.md)
- Quick start: [QUICKSTART.md](./QUICKSTART.md)
- Full docs: [README.md](./README.md)

---

**Remember: Keep your API credentials private and secure! Don't share them with anyone.**

