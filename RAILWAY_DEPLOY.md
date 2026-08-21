# Railway Deployment Guide

## Quick Setup (5 minutes)

### Step 1: Create GitHub Repo
1. Go to https://github.com/new
2. Create repo named `cascade-system` (or similar)
3. Copy the repo URL (e.g., `https://github.com/SystemicFailure/cascade-system.git`)

### Step 2: Push Your Code to GitHub
On your Windows PowerShell:

```powershell
cd "C:\Users\Dr. Strangelove\cascade_app_package"
git init
git add .
git commit -m "Initial Project Cascade commit"
git branch -M main
git remote add origin https://github.com/SystemicFailure/cascade-system.git
git push -u origin main
```

(You'll be prompted for GitHub credentials - use your GitHub username and a personal access token)

### Step 3: Deploy to Railway
1. Go to https://railway.app
2. Sign up with GitHub (click "Start with GitHub")
3. Authorize Railway to access your GitHub account
4. Click "New Project"
5. Select "Deploy from GitHub repo"
6. Find and select `cascade-system`
7. Railway automatically detects Python and deploys
8. Wait ~2-3 minutes for deployment
9. Click the project, go to "Deployments" tab
10. Find your live URL (e.g., `cascade-system.up.railway.app`)

### Step 4: Point Your Domain
In your strangelove.com DNS settings (at blacksun):
- Create CNAME record: `cascade` → `cascade-system.up.railway.app`
- Your site will be live at `cascade.strangelove.com`

Done! Your live cascade analysis system is running.

## What Railway Handles
- Hosting
- Auto-restart if it crashes
- SSL certificate (HTTPS)
- Scaling

## Database Note
Your `cascade_data.db` SQLite database will work on Railway, but it persists to the container's ephemeral storage. For production, consider migrating to PostgreSQL (Railway can provision one free tier).
