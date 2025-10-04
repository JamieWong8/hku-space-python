# 🌐 Deploy Deal Scout to ngrok - Complete Guide

## What is ngrok?

**ngrok** creates a secure public URL for your local Flask app, allowing you to:
- ✅ Share your app with anyone on the internet
- ✅ Demo to clients/investors without deployment
- ✅ Test webhooks and integrations
- ✅ Access your local app from mobile devices
- ✅ Get HTTPS automatically (SSL certificate included)

**Your Public URL will look like:** `https://abc123.ngrok.io`

---

## 📋 Prerequisites

- [x] Flask app working locally (port 5000)
- [x] ngrok account created
- [x] Auth token: `33adT18UpEgZsio7QsTk2hL0eIR_6dU1kNTrWrUQagBvqGFKR`

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install ngrok

**Option A: Using Chocolatey (Recommended)**
```powershell
# Install Chocolatey if not already installed
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install ngrok
choco install ngrok -y
```

**Option B: Manual Download**
1. Download from: https://ngrok.com/download
2. Extract `ngrok.exe` to `C:\Windows\System32\` (or any folder in PATH)
3. Or add ngrok folder to PATH manually

**Option C: Using Scoop**
```powershell
scoop install ngrok
```

---

### Step 2: Configure ngrok with Your Auth Token

```powershell
ngrok config add-authtoken 33adT18UpEgZsio7QsTk2hL0eIR_6dU1kNTrWrUQagBvqGFKR
```

**Expected Output:**
```
Authtoken saved to configuration file: C:\Users\jamie\.ngrok2\ngrok.yml
```

---

### Step 3: Start Your Flask App

```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
.\run_web_app.ps1
```

**Wait for:**
```
* Running on http://127.0.0.1:5000
```

---

### Step 4: Start ngrok (New Terminal)

Open a **NEW** PowerShell terminal and run:

```powershell
ngrok http 5000
```

**Expected Output:**
```
ngrok                                                                           

Session Status                online
Account                       your_account
Version                       3.x.x
Region                        United States (us)
Latency                       10ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:5000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

---

### Step 5: Access Your App

**Your public URL:** Copy the `Forwarding` URL (e.g., `https://abc123.ngrok-free.app`)

**Share this URL with anyone!**
- No deployment needed
- Works on any device/network
- HTTPS included
- Real-time updates (they see your changes)

---

## 📱 Testing Your Deployment

### 1. Test the URL
Open the ngrok URL in your browser:
```
https://abc123.ngrok-free.app
```

### 2. Test API Endpoints
```powershell
# Test companies API
curl https://abc123.ngrok-free.app/api/companies

# Test health check
curl https://abc123.ngrok-free.app/admin/health
```

### 3. Test on Mobile
- Open the URL on your phone
- Test responsiveness
- Check dark mode toggle
- Test company analysis

---

## 🛠️ Automated Deployment Script

I've created `start_ngrok.ps1` for easy deployment:

```powershell
.\start_ngrok.ps1
```

**What it does:**
1. ✅ Checks if ngrok is installed
2. ✅ Configures auth token
3. ✅ Starts Flask app
4. ✅ Starts ngrok tunnel
5. ✅ Displays public URL
6. ✅ Opens browser automatically

---

## 🔒 Security Considerations

### Free Plan Limitations
- ⚠️ URL changes every restart (new random subdomain)
- ⚠️ Sessions expire after inactivity
- ⚠️ Limited to 1 tunnel at a time
- ⚠️ Shows ngrok warning page before first visit

### Security Best Practices
```python
# Add to app.py if deploying publicly:

# 1. Enable production mode
app.config['DEBUG'] = False
app.config['ENV'] = 'production'

# 2. Set secure session key
app.config['SECRET_KEY'] = 'your-secure-random-key-here'

# 3. Add basic auth (optional)
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    return username == 'admin' and password == 'secure-pass'

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')
```

### Rate Limiting (Recommended)
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

---

## 🎯 ngrok Pro Features (Optional Upgrade)

### Free Plan
- ✅ 1 tunnel
- ✅ Random subdomain
- ✅ HTTPS
- ❌ Custom domain
- ❌ Reserved subdomain
- ❌ No warning page

### Pro Plan ($8/month)
- ✅ 3 tunnels
- ✅ Custom subdomain (e.g., `dealscout.ngrok.io`)
- ✅ Reserved URLs (same URL every time)
- ✅ No warning page
- ✅ Basic auth
- ✅ IP whitelisting

### Enterprise Plan
- ✅ Custom domain (e.g., `app.yourcompany.com`)
- ✅ Unlimited tunnels
- ✅ Advanced security
- ✅ SSO integration

**Upgrade:** https://dashboard.ngrok.com/billing/subscription

---

## 🔧 Troubleshooting

### Issue 1: "ngrok: command not found"

**Solution A: Add to PATH**
```powershell
# Find ngrok.exe location
$ngrokPath = "C:\path\to\ngrok"

# Add to PATH permanently
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", "User") + ";$ngrokPath",
    "User"
)

# Restart PowerShell
```

**Solution B: Use full path**
```powershell
C:\path\to\ngrok.exe http 5000
```

---

### Issue 2: "Failed to validate tunnel"

**Cause:** Auth token not configured

**Solution:**
```powershell
ngrok config add-authtoken 33adT18UpEgZsio7QsTk2hL0eIR_6dU1kNTrWrUQagBvqGFKR
```

---

### Issue 3: "Port 5000 already in use"

**Solution 1: Kill existing Flask process**
```powershell
# Find process on port 5000
Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess

# Kill it
Stop-Process -Id <process_id> -Force
```

**Solution 2: Use different port**
```powershell
# Start Flask on port 5001
$env:FLASK_RUN_PORT = "5001"
python app.py

# Start ngrok on port 5001
ngrok http 5001
```

---

### Issue 4: "Connection refused"

**Checklist:**
- [ ] Is Flask app running? (check terminal output)
- [ ] Is Flask listening on `0.0.0.0` (not `127.0.0.1`)?
- [ ] Is the port correct (5000)?
- [ ] Is firewall blocking ngrok?

**Fix Flask binding:**
```python
# In app.py, change:
app.run(host='127.0.0.1', port=5000)

# To:
app.run(host='0.0.0.0', port=5000)
```

---

### Issue 5: ngrok Warning Page

**Cause:** Free plan shows warning before first visit

**Solutions:**
1. Click "Visit Site" on warning page (one-time)
2. Upgrade to Pro plan (removes warning)
3. Add `?skip_browser_warning=true` to URL

---

## 📊 Monitoring with ngrok Dashboard

### Web Interface
Open: http://127.0.0.1:4040

**Features:**
- 📊 Request logs
- ⏱️ Response times
- 🔍 Request inspector
- 📝 Request/response details
- 🔁 Replay requests

### Dashboard Commands
```powershell
# View all tunnels
ngrok api tunnels list

# View tunnel details
ngrok api tunnels get <tunnel-id>

# Close tunnel
ngrok api tunnels close <tunnel-id>
```

---

## 🌟 Advanced Configuration

### Custom Configuration File
Create `ngrok.yml`:

```yaml
version: 2
authtoken: 33adT18UpEgZsio7QsTk2hL0eIR_6dU1kNTrWrUQagBvqGFKR
region: us
console_ui: true
log_level: info
log: C:\Users\jamie\ngrok.log

tunnels:
  dealscout:
    proto: http
    addr: 5000
    subdomain: dealscout  # Requires Pro plan
    bind_tls: true
    inspect: true
    host_header: rewrite
```

**Start with config:**
```powershell
ngrok start dealscout
```

---

### Multiple Tunnels (Pro Plan)

```yaml
tunnels:
  web:
    proto: http
    addr: 5000
  
  api:
    proto: http
    addr: 8000
  
  database:
    proto: tcp
    addr: 5432
```

**Start all:**
```powershell
ngrok start --all
```

---

## 🎬 Complete Deployment Workflow

### Development Workflow
```
1. Code changes in VS Code
   ↓
2. Flask auto-reloads (debug mode)
   ↓
3. Changes visible immediately on ngrok URL
   ↓
4. Share URL with team for testing
   ↓
5. View logs in ngrok web interface (http://127.0.0.1:4040)
```

### Demo Workflow
```
1. Start Flask app with production settings
   ↓
2. Start ngrok tunnel
   ↓
3. Copy public URL
   ↓
4. Share URL with client/investor
   ↓
5. Present live demo (they access your local app)
   ↓
6. Stop tunnel when done
```

---

## 📱 Mobile Testing

### Test Responsive Design
1. Get ngrok URL (e.g., `https://abc123.ngrok-free.app`)
2. Open on mobile browser
3. Test features:
   - Company catalog scrolling
   - Search functionality
   - Modal analysis view
   - Tab navigation
   - Dark mode toggle

### Debug Mobile Issues
1. Open ngrok web interface: http://127.0.0.1:4040
2. View requests from mobile device
3. Inspect headers, user agent
4. Check response codes
5. Review console logs

---

## 🔄 Continuous Deployment

### Option 1: Keep Tunnel Running
```powershell
# Start in background (not recommended for long-term)
Start-Process powershell -ArgumentList "ngrok http 5000" -WindowStyle Hidden
```

### Option 2: Use Persistent URL (Pro Plan)
```powershell
# Reserved subdomain stays the same
ngrok http 5000 --subdomain=dealscout
# Always accessible at: https://dealscout.ngrok.io
```

### Option 3: Use Custom Domain (Enterprise)
```powershell
# Your own domain
ngrok http 5000 --hostname=app.yourcompany.com
```

---

## 💰 Cost Comparison

| Feature | Free | Pro ($8/mo) | Enterprise |
|---------|------|-------------|------------|
| **Tunnels** | 1 | 3 | Unlimited |
| **URLs** | Random | Reserved | Custom Domain |
| **Warning Page** | Yes | No | No |
| **Support** | Community | Email | Priority |
| **Team Members** | 1 | 5 | Unlimited |
| **Best For** | Testing | Demos/Dev | Production |

---

## 🎯 Use Cases

### 1. Client Demos
- Share live app without deployment
- Make changes in real-time during demo
- Show different features on the fly
- Get immediate feedback

### 2. Team Collaboration
- Share development progress
- Test on different devices
- Collaborate on debugging
- Review UI/UX together

### 3. Webhook Testing
- Test payment webhooks (Stripe)
- Test notification webhooks (Twilio)
- Test API integrations
- Debug callback URLs

### 4. Mobile Testing
- Test responsive design
- Check mobile-specific features
- Debug touch interactions
- Test on different screen sizes

---

## 🛑 Stopping ngrok

### Stop Tunnel
Press `Ctrl+C` in ngrok terminal

### Stop Flask App
Press `Ctrl+C` in Flask terminal

### Stop All
```powershell
# Kill all ngrok processes
Get-Process ngrok | Stop-Process -Force

# Kill all Python processes (Flask)
Get-Process python | Stop-Process -Force
```

---

## 📚 Additional Resources

- **ngrok Docs:** https://ngrok.com/docs
- **ngrok Dashboard:** https://dashboard.ngrok.com
- **Flask Deployment:** https://flask.palletsprojects.com/en/latest/deploying/
- **ngrok Pricing:** https://ngrok.com/pricing
- **Support:** https://ngrok.com/support

---

## ✅ Quick Checklist

Before sharing your ngrok URL:

- [ ] Flask app running (`http://127.0.0.1:5000`)
- [ ] ngrok tunnel active (`https://abc123.ngrok-free.app`)
- [ ] Tested URL in browser
- [ ] Tested API endpoints
- [ ] Checked for sensitive data in logs
- [ ] Set `DEBUG = False` for public demos
- [ ] Removed any test/debug endpoints
- [ ] Verified HTTPS working
- [ ] Tested on mobile device
- [ ] Reviewed ngrok web interface logs

---

## 🎉 Success!

Once everything is running:

```
✅ Flask App:  http://127.0.0.1:5000
✅ ngrok URL:  https://abc123.ngrok-free.app
✅ ngrok Web:  http://127.0.0.1:4040
```

**Share the ngrok URL with anyone** and they can access your Deal Scout app!

---

## 🆘 Need Help?

**Quick Support:**
1. Check ngrok web interface: http://127.0.0.1:4040
2. Review Flask logs in terminal
3. Check troubleshooting section above
4. Visit ngrok docs: https://ngrok.com/docs

**Common Issues:**
- Auth token not configured → Rerun config command
- Port already in use → Kill process or use different port
- Connection refused → Check Flask is running on 0.0.0.0
- Tunnel expired → Restart ngrok (free plan limitation)

---

**Your Auth Token:** `33adT18UpEgZsio7QsTk2hL0eIR_6dU1kNTrWrUQagBvqGFKR`

Keep this secure and don't share publicly! 🔒
