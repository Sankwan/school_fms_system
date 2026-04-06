#!/bin/bash
# ============================================================
# School FMS — Docker VPS Setup Script
# ============================================================
# Usage: ssh root@YOUR_VPS_IP "bash -s" < deploy/setup_docker_vps.sh
# ============================================================

set -e

echo "==========================================="
echo " Installing Docker & Preparing VPS"
echo "==========================================="

# 1. Update System
apt update && apt upgrade -y

# 2. Install Docker
apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 3. Enable Docker
systemctl start docker
systemctl enable docker

# 4. Configure Firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# 5. Create App Directory
mkdir -p /var/www/school_fms
chown $USER:$USER /var/www/school_fms

echo ""
echo "==========================================="
echo " VPS READY FOR DOCKER"
echo "==========================================="
echo " Next steps:"
echo "   1. Clone your repo to /var/www/school_fms"
echo "   2. Create your .env file"
echo "   3. Run: docker compose up -d"
echo "==========================================="
