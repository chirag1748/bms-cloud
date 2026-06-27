# BMS Cloud — Deployment Guide
## Step 1: MongoDB Atlas (Free Database)

1. Go to https://cloud.mongodb.com → Sign up free
2. Create a new project → "BMS"
3. Click "Build a Database" → Choose FREE (M0 Sandbox)
4. Choose any region → Create
5. Create a user:
   - Username: bmsadmin
   - Password: (pick something strong, save it)
6. Network Access → Add IP Address → Allow Access from Anywhere (0.0.0.0/0)
7. Go to Database → Connect → Drivers → Copy the connection string
   Looks like: mongodb+srv://bmsadmin:<password>@cluster0.xxxxx.mongodb.net/

---

## Step 2: GitHub (to deploy on Render)

1. Go to https://github.com → Sign up / Login
2. Create a new repository → Name: "bms-cloud" → Public → Create
3. Upload all files from this folder to the repository
   (or use GitHub Desktop app — easier)

---

## Step 3: Render.com (Free Hosting)

1. Go to https://render.com → Sign up with GitHub
2. Click "New" → "Web Service"
3. Connect your GitHub repo "bms-cloud"
4. Fill in:
   - Name: bms-cloud
   - Runtime: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT
   - Instance Type: Free
5. Click "Advanced" → Add Environment Variables:
   - MONGODB_URI = (paste your MongoDB connection string, replace <password>)
   - DB_NAME = bms
   - SECRET_KEY = (any random text, e.g. mysecretbms2024)
6. Click "Create Web Service"
7. Wait 2-3 minutes for deployment
8. Your URL will be: https://bms-cloud.onrender.com

---

## Step 4: Use It

- Open the URL on any device, anywhere in the world
- Default logins:
  - Admin:       username=admin       password=admin123
  - BD Incharge: username=bdincharge  password=bd123
- CHANGE THESE PASSWORDS immediately from the Admin Panel!

---

## Notes

- Free Render tier sleeps after 15 mins of inactivity — first load may take 30 sec
- MongoDB free tier: 512MB storage (enough for thousands of tickets)
- To upgrade to always-on: Render paid plan starts at $7/month
- All data is in MongoDB Atlas — safe even if Render restarts

---

## Default Credentials (CHANGE IMMEDIATELY)
Admin:       admin / admin123
BD Incharge: bdincharge / bd123
