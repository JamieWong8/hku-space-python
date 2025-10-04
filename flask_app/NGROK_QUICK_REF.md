# 🚀 ngrok Quick Reference

## Your Public URL
```
https://jealously-unsensible-dona.ngrok-free.dev
```

**Share this with anyone to give them access to your Deal Scout app!**

---

## Important URLs

| Purpose | URL |
|---------|-----|
| 🌍 **Public Access** | https://jealously-unsensible-dona.ngrok-free.dev |
| 🏠 **Local Flask** | http://127.0.0.1:5000 |
| 📊 **ngrok Dashboard** | http://127.0.0.1:4040 |
| 🔧 **ngrok Config** | C:\Users\jamie\AppData\Local\ngrok\ngrok.yml |

---

## Quick Commands

### Start ngrok
```powershell
ngrok http 5000
```

### Get Public URL
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" | 
  Select-Object -ExpandProperty tunnels | 
  Select-Object -ExpandProperty public_url
```

### Stop ngrok
```powershell
Get-Process ngrok | Stop-Process -Force
```

### Restart Deployment
```powershell
.\start_ngrok.ps1
```

---

## Status Check

**Current Status:** ✅ ACTIVE

- ✅ ngrok installed (v3.30.0)
- ✅ Auth token configured
- ✅ Tunnel active
- ✅ Flask running (port 5000)
- ✅ Public URL live
- ✅ HTTPS enabled

---

## Features

- ✅ Accessible from any device
- ✅ Works on mobile
- ✅ HTTPS auto-enabled
- ✅ Real-time traffic monitoring
- ✅ Request inspection
- ✅ Auto-reload on code changes

---

## Notes

⚠️ **Free Tier:** URL changes on each restart  
⚠️ **Warning Page:** First-time visitors must click "Visit Site"  
⚠️ **Public Access:** Anyone with URL can access  

💡 **Pro Tip:** Keep ngrok window open to maintain tunnel  
💡 **Monitoring:** Visit http://127.0.0.1:4040 to see real-time traffic  

---

## Documentation

- **Full Guide:** NGROK_DEPLOYMENT_GUIDE.md
- **Completion Summary:** NGROK_DEPLOYMENT_COMPLETE.md
- **Start Script:** start_ngrok.ps1
- **Install Script:** install_ngrok.ps1

---

**Last Updated:** December 2024  
**Tunnel Status:** 🟢 ACTIVE
