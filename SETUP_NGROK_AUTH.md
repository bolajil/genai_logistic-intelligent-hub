# Ngrok Authentication Setup

Your backend is running! Now you need to authenticate ngrok.

---

## ✅ Your Backend is Running

```
✅ Backend: http://0.0.0.0:8000
✅ Status: Running
✅ Ready for ngrok tunnel
```

---

## 🔑 Step 1: Get Ngrok Authtoken

### **1. Sign up for free ngrok account**

Go to: https://dashboard.ngrok.com/signup

- Use your email or GitHub
- 100% free for basic use
- No credit card required

### **2. Get your authtoken**

After signing up, you'll see your authtoken at:
https://dashboard.ngrok.com/get-started/your-authtoken

It looks like: `2abc123def456ghi789jkl012mno345_6pqrstu789vwxyz123ABC`

### **3. Copy the authtoken**

Click the **"Copy"** button to copy your authtoken.

---

## 🔧 Step 2: Configure Ngrok

### **Option A: Using the command (Recommended)**

```powershell
# Replace YOUR_AUTHTOKEN with your actual token
$env:LOCALAPPDATA\Microsoft\WinGet\Packages\ngrok.ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe config add-authtoken YOUR_AUTHTOKEN
```

### **Option B: Manual configuration**

1. Create/edit file: `C:\Users\bolaf\.ngrok2\ngrok.yml`

2. Add this line:
   ```yaml
   authtoken: YOUR_AUTHTOKEN
   ```

3. Save the file

---

## 🚀 Step 3: Start Ngrok Tunnel

```powershell
$env:LOCALAPPDATA\Microsoft\WinGet\Packages\ngrok.ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe http 8000
```

You should see:

```
Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

---

## 📋 Step 4: Copy Your Ngrok URL

Look for the **"Forwarding"** line:

```
Forwarding    https://abc123-xyz.ngrok.io -> http://localhost:8000
```

**Copy** the URL: `https://abc123-xyz.ngrok.io`

---

## 🌐 Step 5: Configure Hugging Face Space

### **1. Go to your Space settings**

```
https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE/settings
```

### **2. Add Repository Secret**

- Scroll to **"Repository secrets"**
- Click **"Add a secret"**
- **Name**: `BACKEND_URL`
- **Value**: `https://abc123-xyz.ngrok.io` (your ngrok URL)
- Click **"Add secret"**

### **3. Restart your Space**

- Go to your Space page
- Click **"⋮"** (three dots)
- Click **"Restart this Space"**
- Wait ~1-2 minutes

---

## ✅ Step 6: Test It!

1. Open your Hugging Face Space
2. Check top shows: `Backend: https://abc123-xyz.ngrok.io`
3. Go to **Admin** tab
4. Click **"Check Detailed Health"**
5. Should show ✅ success!

---

## 🎯 Quick Commands

### **Configure authtoken**
```powershell
$env:LOCALAPPDATA\Microsoft\WinGet\Packages\ngrok.ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe config add-authtoken YOUR_AUTHTOKEN
```

### **Start tunnel**
```powershell
$env:LOCALAPPDATA\Microsoft\WinGet\Packages\ngrok.ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe http 8000
```

### **View web interface**
```
http://127.0.0.1:4040
```

---

## 📊 Ngrok Web Interface

Ngrok provides a web interface at: **http://127.0.0.1:4040**

Features:
- See all requests in real-time
- Inspect request/response details
- Replay requests
- View connection stats

---

## ⚠️ Important Notes

### **Free Tier Limits**
- ✅ Unlimited tunnels
- ✅ HTTPS support
- ⚠️ Random URL each restart
- ⚠️ 2-hour session limit
- ⚠️ Connection limits

### **URL Changes**
Every time you restart ngrok, the URL changes!

**When URL changes:**
1. Copy new ngrok URL
2. Update `BACKEND_URL` in Hugging Face
3. Restart Space

### **Keep Running**
Both must stay open:
- ✅ Backend terminal (uvicorn)
- ✅ Ngrok terminal (tunnel)

---

## 🔧 Troubleshooting

### **"authentication failed"**
- You need to add your authtoken first
- Follow Step 2 above

### **"command not found"**
- Use the full path shown above
- Or restart PowerShell after installation

### **"connection refused"**
- Make sure backend is running on port 8000
- Check: http://localhost:8000/health

### **"tunnel not found"**
- Ngrok might have expired (2-hour limit)
- Restart ngrok and update URL

---

## 🎓 Alternative: Add to PATH

To use `ngrok` command directly:

```powershell
# Add to PATH (permanent)
$ngrokPath = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\ngrok.ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe"
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$ngrokPath", "User")

# Restart PowerShell, then:
ngrok http 8000
```

---

**Once configured, you'll be able to access your local backend from Hugging Face Spaces!** 🚀
