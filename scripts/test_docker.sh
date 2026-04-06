#!/bin/bash
set -e

echo "🚀 Starting Docker Implementation Test..."

# Backup existing .env if it exists
if [ -f .env ]; then
    echo "📦 Backing up existing .env..."
    mv .env .env.bak
fi

# Use a temporary .env for testing
echo "📝 Creating temporary .env for testing..."
cat > .env << EOF
SECRET_KEY=test-secret-key-12345
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production
ALLOWED_HOSTS=localhost,127.0.0.1,web
DB_NAME=school_fms
DB_USER=fms_user
DB_PASSWORD=test_pass
DB_HOST=db
DB_PORT=3306
MYSQL_ROOT_PASSWORD=root_pass
MYSQL_DATABASE=school_fms
MYSQL_USER=fms_user
MYSQL_PASSWORD=test_pass
EOF

# Build and start
echo "🏗️ Building and starting containers..."
docker compose build web
docker compose up -d

# Wait for healthy stack
echo "⏳ Waiting for services to be ready..."
MAX_RETRIES=30
COUNT=0
SUCCESS=false

while [ $COUNT -lt $MAX_RETRIES ]; do
    # Try to curl the app. We check for a 200 or 302 (redirect to login)
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
    if [ "$STATUS" == "200" ] || [ "$STATUS" == "302" ] || [ "$STATUS" == "301" ]; then
        SUCCESS=true
        break
    fi
    echo -n "."
    sleep 3
    COUNT=$((COUNT+1))
done

echo ""

if [ "$SUCCESS" = true ]; then
    echo "✅ TEST PASSED: School FMS is responsive on http://localhost/ (Status: $STATUS)"
    echo "📊 Container Status:"
    docker compose ps
else
    echo "❌ TEST FAILED: Application did not respond in time."
    echo "📜 Web Container Logs:"
    docker compose logs web --tail 50
    echo "📜 Nginx Container Logs:"
    docker compose logs nginx --tail 20
fi

# Cleanup
echo "🧹 Cleaning up test environment..."
docker compose down -v

# Restore .env
rm .env
if [ -f .env.bak ]; then
    echo "🔄 Restoring original .env..."
    mv .env.bak .env
fi

if [ "$SUCCESS" = true ]; then
    echo "🎉 Docker implementation is verified and production-ready!"
else
    exit 1
fi
