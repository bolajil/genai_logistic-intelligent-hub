# Ngrok Setup Guide for Hugging Face Spaces

Use ngrok to expose your local GLIH backend to Hugging Face Spaces.

---

## 🎯 What This Does

- Runs your backend **locally** on your machine
- **Exposes** it to the internet via ngrok tunnel
- Allows your **Hugging Face Space** to connect to your local backend

---

## 🚀 Quick Start

### **Step 1: Run the Setup Script**

```powershell
.\start_with_ngrok.ps1
```

This will:
1. ✅ Start your backend on `http://localhost:8000`
2. ✅ Start ngrok tunnel
3. ✅ Open two PowerShell windows (backend + ngrok)

### **Step 2: Copy the Ngrok URL**

In the **ngrok window**, you'll see something like:

```
Forwarding    https://abc123.ngrok.io -> http://localhost:8000
```

**Copy** the ngrok URL: `https://abc123.ngrok.io`

### **Step 3: Configure Hugging Face Space**

1. Go to your Space settings:
   ```
   https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE/settings
   ```

2. Scroll to **"Repository secrets"**

3. Click **"Add a secret"**

4. Add:
   - **Name**: `BACKEND_URL`
   - **Value**: `https://abc123.ngrok.io` (your ngrok URL)

5. Click **"Add secret"**

### **Step 4: Restart Your Space**

1. Go to your Space page
2. Click the **"⋮"** menu (three dots)
3. Click **"Restart this Space"**
4. Wait for it to rebuild (~1-2 minutes)

### **Step 5: Test It!**

1. Open your Hugging Face Space
2. You should see: `Backend: https://abc123.ngrok.io`
3. Try the Admin tab → Click "Check Detailed Health"
4. Should show ✅ success!

---

## 📋 Manual Setup (If Script Doesn't Work)

### **1. Start Backend**

```powershell
.\.venv\Scripts\python.exe -m uvicorn --host 0.0.0.0 --port 8000 --app-dir glih-backend/src glih_backend.api.main:app
```

### **2. Start Ngrok**

```powershell
ngrok http 8000
```

### **3. Copy URL and Configure**

Follow Steps 2-5 from Quick Start above.

---

## 🔧 Troubleshooting

### **"Command not found: ngrok"**

**Solution**: Restart your PowerShell after installation
```powershell
# Close and reopen PowerShell
# Or refresh environment:
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

### **Backend won't start**

**Check if port 8000 is in use**:
```powershell
netstat -ano | findstr :8000
```

**Kill the process**:
```powershell
# Find the PID from netstat output
taskkill /PID <PID> /F
```

### **Ngrok tunnel not working**

**Check ngrok status**:
- Look for "Forwarding" line in ngrok window
- Should show: `https://xxx.ngrok.io -> http://localhost:8000`

**Common issues**:
- Free ngrok has connection limits
- Tunnel expires after 2 hours (free tier)
- Need to restart ngrok and update URL

### **Hugging Face Space still shows error**

**Verify**:
1. ✅ Backend is running locally
2. ✅ Ngrok tunnel is active
3. ✅ `BACKEND_URL` secret is set correctly
4. ✅ Space has been restarted
5. ✅ URL in Space matches ngrok URL

**Check backend URL**:
- Look at top of Space: "Backend: https://..."
- Should match your ngrok URL

### **"Connection refused" error**

**Possible causes**:
- Backend not running
- Ngrok tunnel closed
- Wrong URL in Hugging Face secret

**Fix**:
1. Check both windows are still open
2. Verify ngrok URL hasn't changed
3. Update secret if URL changed
4. Restart Space

---

## ⚠️ Important Notes

### **Ngrok Free Tier Limitations**

- ✅ **Free**: Basic tunneling
- ⚠️ **Limits**:
  - Random URL each time (changes on restart)
  - 2-hour session limit
  - Connection limits
  - No custom domains

### **URL Changes**

**Every time you restart ngrok**, the URL changes!

**When URL changes**:
1. Copy new ngrok URL
2. Update `BACKEND_URL` secret in Hugging Face
3. Restart Space

### **Keep Windows Open**

Both windows must stay open:
- ✅ Backend window (uvicorn)
- ✅ Ngrok window (tunnel)

Closing either will break the connection.

### **Security**

⚠️ **Your local backend is exposed to the internet!**

**Recommendations**:
- Only run when needed
- Don't expose sensitive data
- Use ngrok's built-in authentication (paid)
- Consider deploying backend to cloud for production

---

## 🎯 Ngrok Paid Plans (Optional)

### **Free**
- Random URLs
- 2-hour sessions
- Basic features

### **Personal ($8/month)**
- ✅ Custom domains
- ✅ Longer sessions
- ✅ More connections
- ✅ Reserved URLs (don't change)

### **Pro ($20/month)**
- ✅ Everything in Personal
- ✅ IP whitelisting
- ✅ Authentication
- ✅ Better performance

**Get it**: https://ngrok.com/pricing

---

## 🔄 Alternative: Deploy Backend to Cloud

For **production** or **permanent** setup, consider deploying backend:

### **Options**:

1. **Hugging Face Spaces** (Docker)
   - Free tier available
   - Easy integration
   - Same platform as frontend

2. **Railway** (https://railway.app)
   - Free tier: $5 credit/month
   - Easy deployment
   - Good for FastAPI

3. **Render** (https://render.com)
   - Free tier available
   - Auto-deploy from GitHub
   - Good performance

4. **Fly.io** (https://fly.io)
   - Free tier available
   - Global edge network
   - Good for APIs

---

## 📝 Quick Commands Reference

### **Start Everything**
```powershell
.\start_with_ngrok.ps1
```

### **Start Backend Only**
```powershell
.\.venv\Scripts\python.exe -m uvicorn --host 0.0.0.0 --port 8000 --app-dir glih-backend/src glih_backend.api.main:app
```

### **Start Ngrok Only**
```powershell
ngrok http 8000
```

### **Check Backend Health**
```powershell
curl http://localhost:8000/health
```

### **Test Ngrok URL**
```powershell
curl https://YOUR_NGROK_URL/health
```

---

## 🎓 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Hugging Face Cloud                       │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Streamlit Frontend (Your Space)                     │  │
│  │  - Reads BACKEND_URL from environment                │  │
│  │  - Makes requests to ngrok URL                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            │ HTTPS
                            │
                    ┌───────▼────────┐
                    │  Ngrok Cloud   │
                    │  (Tunnel)      │
                    └───────┬────────┘
                            │
                            │ HTTP
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    Your Local Machine                       │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Ngrok Client                                        │  │
│  │  - Listens on random port                            │  │
│  │  - Forwards to localhost:8000                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
│  ┌────────────────────────▼──────────────────────────────┐ │
│  │  FastAPI Backend                                      │ │
│  │  - Running on localhost:8000                          │ │
│  │  - Handles all API requests                           │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Success Checklist

- [ ] Ngrok installed
- [ ] Backend running on localhost:8000
- [ ] Ngrok tunnel active
- [ ] Ngrok URL copied
- [ ] `BACKEND_URL` secret added to Hugging Face
- [ ] Hugging Face Space restarted
- [ ] Space shows correct backend URL
- [ ] Health check passes
- [ ] Can query and ingest documents

---

**You're all set! Your Hugging Face Space can now access your local backend via ngrok.** 🚀

For permanent deployment, consider moving the backend to a cloud provider.
