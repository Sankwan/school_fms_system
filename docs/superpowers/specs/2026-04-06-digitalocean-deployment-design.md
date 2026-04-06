# 🚀 Deployment Design: School FMS (DigitalOcean Single Container)

**Topic:** Deploying School FMS to a DigitalOcean Droplet with Host-level MySQL and Nginx.
**Status:** PROPOSED (Awaiting User Review)
**Target Environment:** DigitalOcean Ubuntu Droplet
**Architecture:** Django (Docker) + MySQL (Host) + Nginx (Host)

---

## 🏗️ Architecture Overview

The application will be deployed as a single Docker container for the Django logic, while leveraging the database and web server already installed on the Droplet host.

### Components:
1.  **Application (Docker):** Built using the existing `Dockerfile`. Runs on Gunicorn (port 8000).
2.  **Database (Host):** MySQL 8.x running directly on Ubuntu.
3.  **Proxy & Static Files (Host):** Nginx running directly on Ubuntu.
4.  **Automation:** GitHub Actions (`deploy.yml`) for push-to-deploy.

---

## 🛠️ Step 1: Database configuration (Host)

Since the database is running on the host, we must ensure the Docker container can reach it.

### MySQL Host Setup:
1.  **Listen on all interfaces:** In `/etc/mysql/mysql.conf.d/mysqld.cnf`, set `bind-address = 0.0.0.0` or ensure it's listening on the docker bridge IP (`172.17.0.1`).
2.  **User Access:** Create a database user that can connect from the Docker IP subnet:
    ```sql
    CREATE USER 'school_user'@'172.%.%.%' IDENTIFIED BY 'your_secure_password';
    GRANT ALL PRIVILEGES ON school_fms.* TO 'school_user'@'172.%.%.%';
    FLUSH PRIVILEGES;
    ```

---

## 📁 Step 2: Directory Structure & Volumes (Host)

We'll mount host folders into the container to ensure data persistence and allow Host Nginx to serve files.

### Path on Server: `/var/www/school_fms`
*   `/var/www/school_fms/static/` -> Shared static files (Django `collectstatic`)
*   `/var/www/school_fms/media/` -> Persistent student/vendor uploads
*   `/var/www/school_fms/.env` -> Production environment variables

---

## 🌐 Step 3: Nginx Configuration (Host)

Create `/etc/nginx/sites-available/school_fms`:

```nginx
server {
    listen 80;
    server_name YOUR_DROPLET_IP;

    # Serve static files directly from the host folder
    location /static/ {
        alias /var/www/school_fms/static/;
    }

    # Serve media files directly from the host folder
    location /media/ {
        alias /var/www/school_fms/media/;
    }

    # Proxy all other traffic to the Docker Container
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🚀 Step 4: Deployment Command (GitHub Action)

The updated deployment script will look like this:

```bash
# 1. Build the image
docker build -t school_fms .

# 2. Run the container
docker run -d \
  --name school_fms_app \
  --restart always \
  -p 8000:8000 \
  --env-file /var/www/school_fms/.env \
  -v /var/www/school_fms/static:/app/staticfiles \
  -v /var/www/school_fms/media:/app/media \
  school_fms
```

---

## 📂 Step 5: Environment Variables (.env)

On the server, your `.env` should look like this:

```env
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=yoursecretkey
DATABASE_URL=mysql://school_user:your_secure_password@172.17.0.1:3306/school_fms
DB_HOST=172.17.0.1
DB_PORT=3306
# ... other vars
```

---

## ✅ Ready for Implementation?

This design document explains exactly what we will do. Once you approve, I will help you set up the secrets and run the initial deployment!
