#!/bin/bash
# ============================================================
# School FMS — Hetzner VPS Setup Script
# ============================================================
# Run this ON YOUR VPS as root after a fresh Ubuntu 22.04/24.04 install.
# Usage: ssh root@YOUR_VPS_IP "bash -s" < deploy/setup_vps.sh
# ============================================================

set -e  # Exit on any error

echo "==========================================="
echo " School FMS — VPS Setup"
echo "==========================================="

# -----------------------------------------------
# 1. SYSTEM UPDATE
# -----------------------------------------------
echo "[1/7] Updating system packages..."
apt update && apt upgrade -y

# -----------------------------------------------
# 2. INSTALL DEPENDENCIES
# -----------------------------------------------
echo "[2/7] Installing Python, MySQL, Nginx..."
apt install -y \
    python3 python3-pip python3-venv python3-dev \
    mysql-server mysql-client libmysqlclient-dev \
    nginx certbot python3-certbot-nginx \
    curl git ufw pkg-config build-essential

# -----------------------------------------------
# 3. CONFIGURE FIREWALL
# -----------------------------------------------
echo "[3/7] Configuring firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# -----------------------------------------------
# 4. SECURE MYSQL
# -----------------------------------------------
echo "[4/7] Configuring MySQL..."

# Start and enable MySQL
systemctl start mysql
systemctl enable mysql

# Create database and user
MYSQL_ROOT_PASS="$(openssl rand -base64 24)"
DB_PASS="$(openssl rand -base64 24)"

echo ""
echo "============================================"
echo " SAVE THESE CREDENTIALS IMMEDIATELY"
echo "============================================"
echo " MySQL root password: $MYSQL_ROOT_PASS"
echo " App DB user password: $DB_PASS"
echo "============================================"
echo ""

# Set root password and create app database/user
mysql -e "
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${MYSQL_ROOT_PASS}';
CREATE DATABASE IF NOT EXISTS school_fms CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'fms_user'@'localhost' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON school_fms.* TO 'fms_user'@'localhost';
FLUSH PRIVILEGES;
"

# -----------------------------------------------
# 5. CREATE APP USER & DIRECTORY
# -----------------------------------------------
echo "[5/7] Setting up application directory..."
useradd -m -s /bin/bash schoolfms 2>/dev/null || true
mkdir -p /var/www/school_fms
chown schoolfms:schoolfms /var/www/school_fms

# -----------------------------------------------
# 6. CONFIGURE NGINX
# -----------------------------------------------
echo "[6/7] Configuring Nginx..."
cat > /etc/nginx/sites-available/school_fms << 'NGINX'
server {
    listen 80;
    server_name _;  # Replace _ with your domain name

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Static files
    location /static/ {
        alias /var/www/school_fms/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files (receipts, uploads)
    location /media/ {
        alias /var/www/school_fms/media/;
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/school_fms /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# -----------------------------------------------
# 7. CREATE SYSTEMD SERVICE
# -----------------------------------------------
echo "[7/7] Creating Gunicorn service..."
cat > /etc/systemd/system/schoolfms.service << 'SERVICE'
[Unit]
Description=School FMS Gunicorn Daemon
After=network.target mysql.service

[Service]
User=schoolfms
Group=schoolfms
WorkingDirectory=/var/www/school_fms
ExecStart=/var/www/school_fms/venv/bin/gunicorn config.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile /var/www/school_fms/logs/access.log \
    --error-logfile /var/www/school_fms/logs/error.log
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable schoolfms

echo ""
echo "==========================================="
echo " VPS SETUP COMPLETE"
echo "==========================================="
echo ""
echo " Next steps:"
echo "   1. Upload your project to /var/www/school_fms/"
echo "   2. Run the deploy script: deploy/deploy_app.sh"
echo ""
echo " IMPORTANT — Save these credentials:"
echo "   MySQL root: $MYSQL_ROOT_PASS"
echo "   App DB user (fms_user): $DB_PASS"
echo "==========================================="
