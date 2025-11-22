# StockMaster - Deployment Guide for Render

This guide walks you through deploying the StockMaster Inventory Management System to Render.com.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [Web Service Deployment](#web-service-deployment)
4. [Environment Variables](#environment-variables)
5. [Post-Deployment](#post-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:
- A GitHub account (to host your repository)
- A Render account (sign up at https://render.com)
- Your StockMaster code pushed to a GitHub repository

---

## Step 1: Database Setup

### 1.1 Create PostgreSQL Database

1. Log into your Render Dashboard: https://dashboard.render.com
2. Click **"New +"** button (top right)
3. Select **"PostgreSQL"**
4. Configure your database:
   - **Name**: `stockmaster-db` (or your preferred name)
   - **Database**: `stockmaster`
   - **User**: (auto-generated)
   - **Region**: Select closest to your users
   - **PostgreSQL Version**: 15 (or latest)
   - **Plan**: Free (for testing) or Starter ($7/month for production)

5. Click **"Create Database"**

### 1.2 Get Database Connection String

After creation:
1. Go to your database dashboard
2. Find the **"Connections"** section
3. Copy the **"Internal Database URL"** (format: `postgresql://user:pass@host/db`)
4. **IMPORTANT**: Save this URL - you'll need it for environment variables

**Note**: The internal URL is faster and free for traffic between Render services in the same region.

---

## Step 2: Web Service Deployment

### 2.1 Create Web Service

1. In Render Dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub account (if not already connected)
3. Select your StockMaster repository
4. Configure the service:

   **Basic Settings:**
   - **Name**: `stockmaster` (or your preferred name)
   - **Region**: Same as your database
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave blank (if app.py is in root)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 2 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:$PORT --timeout 120`

   **Instance Type:**
   - **Free**: Sleeps after 15 minutes of inactivity (good for testing)
   - **Starter ($7/month)**: Always on, no sleep (recommended for production)

5. Click **"Create Web Service"** (Don't deploy yet - we need to set environment variables first)

---

## Step 3: Environment Variables

### 3.1 Required Environment Variables

In your web service dashboard, go to **"Environment"** tab and add:

| Variable Name | Value | Notes |
|--------------|-------|-------|
| `DATABASE_URL` | `<paste your Internal Database URL>` | From Step 1.2 |
| `SECRET_KEY` | `<generate random 32+ char string>` | See generation below |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` | 7 days in minutes |

### 3.2 Generate SECRET_KEY

**Option 1 - Using OpenSSL** (Mac/Linux/Git Bash):
```bash
openssl rand -hex 32
```

**Option 2 - Using Python**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Option 3 - Online Generator**:
Visit https://generate-secret.vercel.app/ or similar secure random string generator

Copy the generated string and paste it as the `SECRET_KEY` value.

### 3.3 Save and Deploy

1. Click **"Save Changes"** at the bottom of the Environment tab
2. Render will automatically start deploying your application
3. Monitor the deployment in the **"Logs"** tab

---

## Step 4: Post-Deployment

### 4.1 Verify Deployment

1. Wait for deployment to complete (usually 2-5 minutes)
2. Check the **"Logs"** tab for any errors
3. Look for: `INFO:     Application startup complete.`
4. Your app URL will be: `https://stockmaster.onrender.com` (or your chosen name)

### 4.2 Initial Database Setup

The application automatically creates:
- All required database tables on first run
- Default admin user:
  - **Email**: `admin@example.com`
  - **Password**: `admin123`
- Sample warehouses, products, and stock data

### 4.3 First Login

1. Visit your deployed URL
2. Log in with default credentials above
3. **IMPORTANT**: Create a new admin user and delete/change the default one for security

### 4.4 Test All Features

Verify the following work correctly:
- ✅ Login/Logout
- ✅ Dashboard displays correctly
- ✅ Products page loads
- ✅ Stock page shows inventory
- ✅ Stock update functionality
- ✅ Create new receipts
- ✅ Create new deliveries
- ✅ Create new adjustments
- ✅ Warehouse management
- ✅ Location management

---

## Step 5: Custom Domain (Optional)

### 5.1 Add Custom Domain

If you have your own domain (e.g., `stockmaster.yourdomain.com`):

1. Go to your web service **"Settings"** tab
2. Scroll to **"Custom Domain"** section
3. Click **"Add Custom Domain"**
4. Enter your domain name
5. Follow the DNS configuration instructions provided
6. Render will automatically provision SSL certificate (free)

---

## Troubleshooting

### Issue: "Application Error" on First Visit

**Cause**: Database tables not created or connection failed

**Solution**:
1. Check **Logs** tab for specific error
2. Verify `DATABASE_URL` is correct
3. Ensure database is in same region as web service
4. Check database is running (not suspended)

---

### Issue: "502 Bad Gateway"

**Cause**: Application failed to start

**Solution**:
1. Check **Logs** for errors during startup
2. Common issues:
   - Missing dependencies → Check `requirements.txt`
   - Database connection timeout → Use Internal Database URL
   - Port binding error → Should use `$PORT` env variable (already configured)

---

### Issue: "Secret Key Not Set" Error

**Cause**: Missing or invalid `SECRET_KEY` environment variable

**Solution**:
1. Go to **Environment** tab
2. Ensure `SECRET_KEY` exists and has minimum 32 characters
3. Save changes and redeploy

---

### Issue: Application Sleeps (Free Tier)

**Behavior**: First request takes 30-60 seconds to wake up

**Solutions**:
- **Option 1**: Upgrade to Starter plan ($7/month) for always-on service
- **Option 2**: Use uptime monitoring (e.g., UptimeRobot) to ping your app every 14 minutes
- **Option 3**: Accept cold starts for low-traffic testing applications

---

### Issue: Database Connection Pool Exhausted

**Cause**: Too many concurrent connections

**Solution**:
Already configured in `database.py`:
```python
pool_size=5
max_overflow=10
pool_pre_ping=True
pool_recycle=300
```

If still seeing issues:
1. Upgrade database plan for more connections
2. Reduce `pool_size` and `max_overflow`

---

### Issue: Static Files Not Loading (CSS/JS)

**Cause**: Static files path misconfigured

**Solution**:
Already configured in `app.py`:
```python
app.mount("/static", StaticFiles(directory="static"), name="static")
```

Ensure your `static/` folder is committed to Git.

---

## Monitoring and Maintenance

### View Application Logs

1. Go to your web service dashboard
2. Click **"Logs"** tab
3. View real-time logs or search historical logs

### Monitor Database

1. Go to your database dashboard
2. View metrics: CPU, Memory, Connections, Storage
3. Set up alerts for high resource usage

### Backup Strategy

**Free Tier**: No automatic backups

**Paid Tier**:
- Daily automatic backups
- Point-in-time recovery
- Manual backup/restore available

**Recommendation**: Export database periodically using pg_dump for critical data.

---

## Cost Estimates (2025)

| Component | Free Tier | Starter Plan |
|-----------|-----------|--------------|
| PostgreSQL | $0 (90 days, then $7/month) | $7/month |
| Web Service | $0 (sleeps after 15min) | $7/month |
| **Total** | **$0** (testing only) | **$14/month** |

---

## Security Checklist

Before going to production:

- [ ] Change default admin credentials
- [ ] Use strong `SECRET_KEY` (generated randomly, not default)
- [ ] Set `DATABASE_URL` using Internal URL (faster, secure)
- [ ] Never commit `.env` file to Git
- [ ] Enable 2FA on Render account
- [ ] Review user roles and permissions
- [ ] Set up database backups
- [ ] Configure custom domain with HTTPS
- [ ] Monitor application logs regularly
- [ ] Keep dependencies updated

---

## Support and Resources

- **Render Documentation**: https://render.com/docs
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org
- **Render Community**: https://community.render.com

---

## Quick Reference Commands

### Generate New Secret Key
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Check Local Application
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

### Test Database Connection (locally)
```bash
python -c "from database import engine; print('Connected!' if engine.connect() else 'Failed')"
```

---

## Deployment Checklist

Use this checklist when deploying:

### Pre-Deployment
- [ ] Code pushed to GitHub repository
- [ ] `requirements.txt` has all dependencies
- [ ] `.env.example` exists (no secrets)
- [ ] `.gitignore` excludes `.env` and `__pycache__`
- [ ] Application runs locally without errors

### Database Setup
- [ ] PostgreSQL database created on Render
- [ ] Internal Database URL copied
- [ ] Database is in same region as web service

### Web Service Configuration
- [ ] Web service created and connected to GitHub
- [ ] Build command set correctly
- [ ] Start command set correctly
- [ ] Environment variables configured:
  - [ ] `DATABASE_URL`
  - [ ] `SECRET_KEY`
  - [ ] `ALGORITHM`
  - [ ] `ACCESS_TOKEN_EXPIRE_MINUTES`

### Post-Deployment
- [ ] Deployment completed successfully
- [ ] Application accessible at URL
- [ ] Can log in with default credentials
- [ ] All pages load correctly
- [ ] CRUD operations work (create, read, update, delete)
- [ ] Default admin user changed/deleted
- [ ] New admin user created

### Production Ready
- [ ] Custom domain configured (if applicable)
- [ ] SSL certificate active
- [ ] Monitoring/alerts set up
- [ ] Backup strategy in place
- [ ] Security checklist completed

---

**Congratulations! Your StockMaster application is now deployed to Render! 🎉**

For questions or issues, check the Troubleshooting section or Render's documentation.
