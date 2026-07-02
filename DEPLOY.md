# SaveIt — Deployment Guide (Non-Coder Friendly)

Follow these steps exactly. Each step tells you exactly what to click.

---

## STEP 1 — Upload to GitHub

1. Go to https://github.com and sign in
2. Click the green **"New"** button (top left)
3. Name your repo: `saveit`
4. Keep it **Public**, click **"Create repository"**
5. On the next screen, click **"uploading an existing file"**
6. Drag and drop the entire `saveit` folder you downloaded
7. Click **"Commit changes"** (green button at the bottom)

Your code is now on GitHub. ✅

---

## STEP 2 — Deploy Backend on Railway

1. Go to https://railway.app and sign in with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your `saveit` repo
4. Railway will ask for the root directory — type: `backend`
5. Click **Deploy**
6. Wait ~2 minutes for it to build
7. Go to **Settings** → **Networking** → click **"Generate Domain"**
8. Copy the domain it gives you (looks like: `saveit-backend.up.railway.app`)

Backend is live. ✅

---

## STEP 3 — Deploy Frontend on Vercel

1. Go to https://vercel.com and sign in with GitHub
2. Click **"Add New Project"**
3. Find and select your `saveit` repo
4. Set **Root Directory** to `frontend`
5. Framework preset will auto-detect as **Vite** ✅
6. Click **"Environment Variables"** and add:
   - Key: `VITE_API_BASE`
   - Value: `https://YOUR-RAILWAY-DOMAIN` (paste what you copied in Step 2)
7. Click **Deploy**
8. Wait ~1 minute

Frontend is live. ✅

---

## STEP 4 — Lock Down CORS (Security)

1. Open your `saveit/backend/main.py` file on GitHub
2. Click the ✏️ pencil icon to edit
3. Find this line:
   ```
   allow_origins=["*"],
   ```
4. Change it to:
   ```
   allow_origins=["https://your-vercel-app.vercel.app"],
   ```
   (use your actual Vercel URL)
5. Click **"Commit changes"**
6. Railway will auto-redeploy ✅

---

## STEP 5 — Test Everything

Visit your Vercel URL and test each tool:
- [ ] Instagram Reels downloader
- [ ] Instagram Video downloader
- [ ] YouTube Video downloader
- [ ] YouTube MP3 downloader

If something doesn't work, come back to Claude and paste the error. ✅

---

## STEP 6 — Connect Your Domain (When Ready)

When you buy a domain (e.g. from Namecheap):
1. In Vercel: go to your project → **Settings** → **Domains** → Add your domain
2. Vercel gives you DNS settings to copy into Namecheap
3. Takes 10–30 minutes to go live

---

## Ongoing Maintenance (Very Simple)

**When downloads stop working** (Instagram/YouTube pushed an update):
1. Go to GitHub → your repo → `backend/requirements.txt`
2. The GitHub Action runs every Monday automatically and updates yt-dlp
3. Or manually: edit `requirements.txt`, change `yt-dlp==X.X.X` to latest version from https://github.com/yt-dlp/yt-dlp/releases
4. Commit the change → Railway auto-redeploys

**Checking your site is alive:**
- Backend: visit `https://YOUR-RAILWAY-DOMAIN/` — should show `{"status":"Xendrop API running"}`
- Frontend: visit your Vercel URL

---

## Your Monthly Cost

| Item | Cost |
|---|---|
| Railway Hobby (backend) | $5/mo |
| Vercel (frontend) | Free |
| Domain (optional) | ~$1/mo |
| **Total** | **$5–6/mo** |
