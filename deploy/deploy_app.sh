#!/bin/bash
# ============================================================
# School FMS — Application Deployment Script
# ============================================================
# Run this ON YOUR VPS after setup_vps.sh has completed.
# Usage: bash deploy/deploy_app.sh
# ============================================================

set -e

APP_DIR="/var/www/school_fms"
VENV="$APP_DIR/venv"

echo "==========================================="
echo " Deploying School FMS"
echo "==========================================="

# -----------------------------------------------
# 1. CREATE VENV & INSTALL DEPS
# -----------------------------------------------
echo "[1/5] Setting up Python environment..."
cd $APP_DIR

python3 -m venv venv
source $VENV/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# -----------------------------------------------
# 2. CONFIGURE ENVIRONMENT
# -----------------------------------------------
echo "[2/5] Checking .env configuration..."
if [ ! -f .env ]; then
    echo ""
    echo "ERROR: .env file not found!"
    echo "Create it with the following template:"
    echo ""
    echo "SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
    echo "DEBUG=False"
    echo "ALLOWED_HOSTS=your-domain.com,your-vps-ip"
    echo "DB_NAME=school_fms"
    echo "DB_USER=fms_user"
    echo "DB_PASSWORD=YOUR_DB_PASSWORD_FROM_SETUP"
    echo "DB_HOST=127.0.0.1"
    echo "DB_PORT=3306"
    echo ""
    exit 1
fi

# -----------------------------------------------
# 3. RUN MIGRATIONS & COLLECT STATIC
# -----------------------------------------------
echo "[3/5] Running migrations..."
export DJANGO_SETTINGS_MODULE=config.settings.production
python3 manage.py migrate --noinput

echo "[4/5] Collecting static files..."
python3 manage.py collectstatic --noinput

# Create logs directory
mkdir -p $APP_DIR/logs

# -----------------------------------------------
# 4. SEED DATA (first deploy only)
# -----------------------------------------------
echo "[5/5] Seeding initial data..."
python3 manage.py seed_data 2>/dev/null || echo "  (Data already exists, skipping)"

# -----------------------------------------------
# 5. SET PERMISSIONS & START
# -----------------------------------------------
chown -R schoolfms:schoolfms $APP_DIR
systemctl restart schoolfms
systemctl restart nginx

echo ""
echo "==========================================="
echo " DEPLOYMENT COMPLETE"
echo "==========================================="
echo ""
echo " Your app is live at: http://$(hostname -I | awk '{print $1}')/"
echo " Login: admin@school.edu / admin123"
echo ""
echo " Useful commands:"
echo "   sudo systemctl status schoolfms    # Check app status"
echo "   sudo journalctl -u schoolfms -f    # View live logs"
echo "   sudo systemctl restart schoolfms   # Restart app"
echo "==========================================="
