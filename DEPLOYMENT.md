# Deploying SmartGov Attendance to a Real Server (Render)

This moves your backend off your personal laptop onto a real, always-on
public server — no more local IP addresses, sleep/wake issues, or needing
your PC turned on for the app to work. Every phone anywhere can then reach
it at a permanent public web address.

We'll use **Render** (render.com) because its free tier supports both
Docker (needed to compile the face-recognition library) and a free
PostgreSQL database, with almost no configuration.

---

## Before you start: two honest limitations of the free tier

1. **Free web services "spin down" after 15 minutes of no traffic** and take
   ~30-60 seconds to wake up on the next request. Fine for testing/small
   teams; for always-instant response, upgrade to a paid instance later.
2. **Uploaded face photos are stored on the server's local disk**, which on
   Render's free tier is **not persistent** — it's wiped on every redeploy.
   This won't affect face *matching* (the actual 128-number encoding is
   saved safely in the database, not the photo file), but the raw photo
   used for enrollment will be lost on redeploy. For a production rollout,
   the proper fix is to store photos in an object storage service (e.g.
   Cloudflare R2 or AWS S3) instead of local disk — ask me if/when you're
   ready to add that.

---

## Step 1: Put your code on GitHub

Render deploys directly from a Git repository, so your code needs to live
on GitHub first.

1. Create a free account at [github.com](https://github.com) if you don't have one.
2. Download **GitHub Desktop** ([desktop.github.com](https://desktop.github.com)) —
   this gives you a visual interface, no command-line Git needed.
3. Install it, sign in with your GitHub account.
4. In GitHub Desktop: **File → New Repository**.
   - Name: `smartgov-attendance-backend`
   - Local Path: choose your existing `smartgov` backend folder's *parent*
     directory, then point it at the `smartgov` folder itself when prompted
     (or just create the repo, then copy your existing `smartgov` folder's
     contents into the new repo folder GitHub Desktop creates).
5. Back in GitHub Desktop, you should see all your project files listed as
   changes. Add a summary like "Initial commit", click **Commit to main**.
6. Click **Publish repository** (top bar). Keep it **Private** unless you
   want it public. Click **Publish**.

Your code is now on GitHub.

## Step 2: Create a Render account

1. Go to [render.com](https://render.com) → **Get Started** → sign up (you
   can sign up directly with your GitHub account, which also makes the
   next step easier).

## Step 3: Deploy using the Blueprint file (fastest method)

I've included a `render.yaml` file in your project — this tells Render
exactly how to set up both the web service and the database automatically.

1. In the Render dashboard, click **New +** → **Blueprint**.
2. Connect your GitHub account if prompted, then select your
   `smartgov-attendance-backend` repository.
3. Render will detect `render.yaml` and show you a preview: one **Web
   Service** (`smartgov-attendance-api`) and one **PostgreSQL database**
   (`smartgov-db`).
4. Click **Apply**.
5. Render will now build your Docker image (this takes 5-15 minutes the
   first time, since it's compiling the face-recognition library) and spin
   up the database.

## Step 4: Watch the build logs

1. Click into the `smartgov-attendance-api` service.
2. Click the **Logs** tab.
3. Wait for the build to finish. You're looking for the final lines to show
   your gunicorn server starting, something like:
   ```
   [INFO] Starting gunicorn
   [INFO] Listening at: http://0.0.0.0:5000
   ```
4. If the build fails, copy the error from the logs and send it to me —
   I'll help you fix it (common causes: a typo in `requirements.txt`, or a
   missing system library for `dlib`, easily patchable in the `Dockerfile`).

## Step 5: Get your public URL

Once deployed, Render shows a URL at the top of the service page, like:
```
https://smartgov-attendance-api.onrender.com
```
Test it directly in your browser:
```
https://smartgov-attendance-api.onrender.com/api/health
```
You should see `{"status": "ok", ...}`.

## Step 6: Seed your admin account on the live server

Since there's no local terminal for the live server, run the seed script
as a **one-off job** instead:

1. In the Render dashboard, go to your `smartgov-attendance-api` service.
2. Click **Shell** (in the left sidebar) — this opens a live terminal
   connected to your actual running server.
3. Run:
   ```
   python seed_data.py
   ```
4. You should see the same "Created default admin" message as before.

## Step 7: Point your mobile app at the live server

This is the easy part now, since we made the server address configurable
in-app:
1. Open the SmartGov app on your phone.
2. Tap **"⚙️ Server Settings"** on the login screen.
3. Enter your new public address:
   ```
   https://smartgov-attendance-api.onrender.com
   ```
4. Tap **Test Connection** → should say "Connected!"
5. Tap **Save & Continue**.

From now on, this works from **any Wi-Fi or mobile data connection,
anywhere** — no more matching IP addresses, no more keeping your laptop
awake, no more tunnel mode for Expo. Everyone on your team can install the
same app and just enter this same public address once.

## Step 8: Change the default admin password immediately

Since `ADMIN001` / `Admin@123` is a publicly-known default from this
project, log in as admin and change the password before inviting real
employees. (There's no "change password" screen built yet — let me know if
you'd like one added; for now, this can be done via Postman calling a
password-update endpoint, which we'd need to add if you want it.)

---

## Ongoing: how updates work from here

Whenever you want to change the backend code:
1. Edit the files locally in VS Code as before.
2. In GitHub Desktop: review the changes, write a commit summary, **Commit to main**, then **Push origin**.
3. Render automatically detects the new commit and redeploys within a few minutes — no manual redeploy needed.

## If you outgrow the free tier

When you have a real user base and need instant responses (no 30-60s
wake-up delay) and persistent file storage for face photos, consider:
- Upgrading the Render web service to a paid "Starter" instance (removes spin-down)
- Adding a Render persistent disk, or moving face photo storage to S3/R2
- Upgrading the free Postgres plan (it also expires after 90 days on some
  Render free-tier terms — check current Render pricing when you're ready)
