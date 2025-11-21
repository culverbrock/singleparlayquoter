# Deployment Guide - Single Parlay Quoter

This guide will walk you through deploying the Single Parlay Quoter to Railway (or any cloud platform).

---

## 🚀 Quick Deploy to Railway

### Step 1: Push to GitHub

1. **Initialize Git Repository** (if not already done):
   ```bash
   cd "/Users/brockculver/kalshi rfq/single_parlay_quoter"
   git init
   ```

2. **Add all files**:
   ```bash
   git add .
   ```

3. **Commit**:
   ```bash
   git commit -m "Initial commit - Single Parlay Quoter"
   ```

4. **Create a new GitHub repository**:
   - Go to [github.com](https://github.com) and click "New Repository"
   - Name it: `single-parlay-quoter` (or whatever you prefer)
   - Don't initialize with README (you already have one)
   - Click "Create repository"

5. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/single-parlay-quoter.git
   git branch -M main
   git push -u origin main
   ```

---

### Step 2: Deploy on Railway

1. **Sign up for Railway**:
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub (easiest option)

2. **Create a New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `single-parlay-quoter` repository
   - Railway will automatically detect it's a Python app

3. **Railway will automatically**:
   - Install dependencies from `requirements.txt`
   - Use the `Procfile` to know how to start the app
   - Assign a public URL (e.g., `https://single-parlay-quoter-production.up.railway.app`)

4. **Wait for deployment** (usually 2-3 minutes):
   - Watch the build logs in Railway dashboard
   - You'll see it installing Flask, SocketIO, etc.
   - When it says "Deployed", you're live! 🎉

5. **Get your public URL**:
   - Click on your deployment in Railway
   - Find the "Settings" tab
   - Under "Domains", you'll see your public URL
   - Click it to open your app!

---

## 🌐 Using the Deployed App

### Important Notes:

1. **No Environment Variables Needed**:
   - The app doesn't use `.env` files
   - All authentication happens in the browser
   - Users enter their own Kalshi credentials in the UI

2. **CORS and WebSockets**:
   - The app is configured to accept connections from any origin
   - WebSocket connections work out of the box
   - No additional Railway configuration needed

3. **Sharing with Others**:
   - Just send them the Railway URL
   - They open it in their browser
   - They enter their own Kalshi API credentials
   - Each user's credentials are stored in their own browser

---

## 📋 Files Created for Deployment

### `Procfile`
Tells Railway how to start the app:
```
web: python app.py
```

### `railway.json`
Railway-specific configuration:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python app.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### `.gitignore`
Prevents sensitive files from being committed:
- `.key` and `.pem` files (private keys)
- `.env` files
- `__pycache__` and logs

### Updated `app.py`
Now uses Railway's `PORT` environment variable:
```python
port = int(os.getenv('PORT', 5002))
```

---

## 🔧 Alternative Deployment Options

### Option 1: Heroku

1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create single-parlay-quoter`
4. Push: `git push heroku main`
5. Open: `heroku open`

### Option 2: Render

1. Go to [render.com](https://render.com)
2. Click "New Web Service"
3. Connect your GitHub repository
4. Render auto-detects Python and uses `requirements.txt`
5. Deploy!

### Option 3: Google Cloud Run

1. Build container: `gcloud builds submit --tag gcr.io/PROJECT-ID/single-parlay-quoter`
2. Deploy: `gcloud run deploy --image gcr.io/PROJECT-ID/single-parlay-quoter --platform managed`

### Option 4: AWS (EC2 or App Runner)

More complex but gives you more control. Requires more setup.

---

## 🔒 Security Considerations

### What's Safe to Deploy:

✅ **Application code** - No credentials in the code
✅ **UI templates** - Just HTML/CSS/JS
✅ **Documentation** - Public-facing guides
✅ **Requirements** - Just Python packages

### What's NOT in the Repository:

❌ **Private keys** (`.key`, `.pem` files) - Excluded by `.gitignore`
❌ **Environment files** (`.env`) - Excluded by `.gitignore`
❌ **User credentials** - Stored only in user's browser localStorage

### For Users:

When users access your deployed app:
- They enter their own Kalshi API Key ID
- They upload their own private key file
- Everything is stored in their browser (localStorage)
- Nothing is sent to your server except for proxying to Kalshi's API

---

## 📊 Monitoring Your Deployment

### Railway Dashboard:

- **Logs**: See real-time application logs
- **Metrics**: CPU, Memory, Network usage
- **Deployments**: History of all deployments
- **Settings**: Environment variables, custom domains

### Useful Railway Commands:

```bash
# View logs
railway logs

# Redeploy
git push origin main  # Automatic redeployment

# Rollback
# Use Railway dashboard to rollback to previous deployment
```

---

## 🛠️ Updating Your Deployment

### When you make changes:

1. **Make your code changes locally**

2. **Test locally**:
   ```bash
   python app.py
   # Open http://localhost:5002
   ```

3. **Commit and push**:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```

4. **Railway auto-deploys**:
   - Railway detects the push
   - Automatically rebuilds and redeploys
   - Usually takes 2-3 minutes

---

## 🎯 Custom Domain (Optional)

### Using Your Own Domain:

1. **In Railway Dashboard**:
   - Go to Settings → Domains
   - Click "Add Custom Domain"
   - Enter your domain (e.g., `quoter.yourdomain.com`)

2. **In Your DNS Provider**:
   - Add a CNAME record
   - Point to Railway's provided domain
   - Wait for DNS propagation (5-60 minutes)

3. **SSL Certificate**:
   - Railway automatically provisions SSL
   - Your site will be `https://` automatically

---

## ⚡ Performance Tips

### For Railway Deployment:

1. **Keep the free tier**:
   - Railway free tier is usually sufficient
   - Upgrade if you have many concurrent users

2. **Monitor usage**:
   - Check Railway dashboard for resource usage
   - Upgrade plan if needed

3. **WebSocket connections**:
   - Railway handles WebSocket connections well
   - No special configuration needed

---

## 🆘 Troubleshooting Deployment

### Build Fails:

**Check requirements.txt**:
```bash
pip freeze > requirements.txt
```

**Check Python version**:
Railway uses Python 3.11 by default. Add `runtime.txt` if you need a specific version:
```
python-3.11.0
```

### App Crashes on Startup:

**Check logs in Railway dashboard**:
- Look for error messages
- Common issues: missing dependencies, port binding

**Ensure PORT is read from environment**:
The app now reads `PORT` from environment, which Railway provides.

### WebSocket Doesn't Connect:

**Check CORS settings**:
The app has `cors_allowed_origins="*"` which allows all origins.

**Check protocol**:
Use `wss://` for WebSocket over HTTPS (Railway handles this automatically).

### "Cannot find module" errors:

Make sure all imports are in `requirements.txt`:
```bash
pip freeze | grep -i MODULE_NAME
```

---

## 📈 Scaling (If Needed)

### Railway Scaling:

1. **Vertical Scaling**:
   - Upgrade to a paid plan
   - Get more CPU/RAM

2. **Horizontal Scaling**:
   - Deploy multiple instances
   - Railway handles load balancing

### For Heavy Traffic:

- Consider adding Redis for session storage
- Use a CDN for static files
- Implement rate limiting

---

## 💰 Costs

### Railway Pricing:

- **Free Tier**: $5 of usage per month (usually sufficient for personal use)
- **Pro Plan**: $20/month for more resources
- **Usage-based**: Pay only for what you use

### Typical Usage:

- Small app like this: Usually stays within free tier
- With moderate traffic: $5-15/month
- Heavy usage: $20-50/month

---

## ✅ Deployment Checklist

Before deploying, make sure:

- [ ] `.gitignore` includes `.key`, `.pem`, `.env`
- [ ] `requirements.txt` has all dependencies
- [ ] `Procfile` exists and is correct
- [ ] App uses `PORT` from environment variable
- [ ] All code is committed and pushed to GitHub
- [ ] Railway project is created and connected to GitHub
- [ ] Deployment is successful (check Railway logs)
- [ ] Public URL works in browser
- [ ] You can enter credentials and connect

---

## 🎉 You're Deployed!

Share your Railway URL with anyone who wants to use the Single Parlay Quoter!

Remember: Each user needs their own Kalshi API credentials. They'll enter them in the browser UI when they first connect.

---

**Need help?** Check Railway's [documentation](https://docs.railway.app/) or their Discord community!

