# 🚀 The "Always Awake" Hackathon Deployment Guide

This guide will walk you through deploying **AI Traffic Inspector** using the standard "Hackathon Stack": **Vercel** (Frontend) + **Render** (Backend) + **UptimeRobot** (To keep the free backend from sleeping).

---

## Step 1: Deploy Backend to Render (Free)

Since our backend uses FastAPI, OpenCV, and AI models, Render's Docker deployment is the best free option.

1. Go to [Render.com](https://render.com/) and sign in with GitHub.
2. Click **New** -> **Web Service**.
3. Connect your GitHub repository: `AI-Traffic-Inspector-FlipKart-Gridlock-Hackathon-2.0-`.
4. Render will automatically detect the `Dockerfile` in your repository.
5. In the configuration:
   - **Name**: `ai-traffic-inspector-api`
   - **Region**: Any (e.g., Frankfurt or Ohio)
   - **Branch**: `main`
   - **Instance Type**: Free
6. Expand the **Environment Variables** section and add your API keys. Make sure to name them exactly as they are in your local `.env`:
   - `ROBOFLOW_API_KEY` = `your_key_here`
   - `GEMINI_API_KEY` = `your_key_here`
7. Click **Create Web Service**. 
8. *Wait for the build to finish.* Once it says "Live", copy the Render URL at the top left (e.g., `https://ai-traffic-inspector-api.onrender.com`).

> [!WARNING]
> The initial build on Render will take 5-10 minutes because it has to install OpenCV and download the YOLOv8 weights. Be patient!

---

## Step 2: Deploy Frontend to Vercel (Free)

Vercel is optimized for Next.js and will host your dashboard instantly.

1. Go to [Vercel.com](https://vercel.com/) and sign in with GitHub.
2. Click **Add New** -> **Project**.
3. Import your GitHub repository: `AI-Traffic-Inspector-FlipKart-Gridlock-Hackathon-2.0-`.
4. In the configuration:
   - **Framework Preset**: Next.js (It should auto-detect this)
   - **Root Directory**: `frontend` (⚠️ **CRITICAL:** Make sure you click Edit and select the `frontend` folder, not the root of the repo!)
5. Expand the **Environment Variables** section and add:
   - **Name**: `NEXT_PUBLIC_API_URL`
   - **Value**: Paste the URL you copied from Render (e.g., `https://ai-traffic-inspector-api.onrender.com`). Do NOT put a trailing slash `/` at the end.
6. Click **Deploy**.
7. In about 60 seconds, your frontend will be live with a permanent URL!

---

## Step 3: The "Always Awake" Trick (Crucial for Hackathons)

Render's free tier goes to sleep after 15 minutes of inactivity. If a judge opens your Vercel link 2 hours from now, they will get an error while the backend spends 60 seconds "waking up". We fix this with UptimeRobot.

1. Go to [UptimeRobot.com](https://uptimerobot.com/) and create a free account.
2. Click **Add New Monitor**.
3. Configure it as follows:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Traffic Inspector Keep-Alive
   - **URL (or IP)**: Paste your Render URL + `/api/health` (e.g., `https://ai-traffic-inspector-api.onrender.com/api/health`)
   - **Monitoring Interval**: 10 minutes (or 14 minutes).
4. Click **Create Monitor**.

### 🎉 You are done!
UptimeRobot will now secretly "ping" your backend every 10 minutes. Render will think you have active traffic and will **never put your server to sleep**. 

Whenever the Flipkart Gridlock judges open your Vercel link, the UI will load instantly, and the AI backend will respond immediately!
