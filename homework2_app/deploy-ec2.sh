#!/bin/bash
# EC2 Deployment Script for Flask LLM Application
# This script automates the entire EC2 deployment process

set -e  # Exit on error

# Configuration
KEY_NAME="flask-app-key"
SG_NAME="flask-app-sg"
INSTANCE_TYPE="t2.micro"
REGION="us-east-1"
DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME:-your-dockerhub-username}"

echo "========================================="
echo "Flask LLM App - EC2 Deployment"
echo "========================================="
echo ""
echo "Configuration:"
echo "  Region: $REGION"
echo "  Instance Type: $INSTANCE_TYPE (Free Tier)"
echo "  Key Name: $KEY_NAME"
echo "  Docker Hub: $DOCKERHUB_USERNAME"
echo ""

#==================================================
# Step 1: Create SSH Key Pair
#==================================================
echo "[1/6] Creating SSH key pair..."

if aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" &>/dev/null; then
    echo "  Key pair already exists, skipping..."
else
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --query 'KeyMaterial' \
        --output text \
        --region "$REGION" > "${KEY_NAME}.pem"

    chmod 400 "${KEY_NAME}.pem"
    echo "  ✅ Key pair created: ${KEY_NAME}.pem"
fi

#==================================================
# Step 2: Create Security Group
#==================================================
echo "[2/6] Creating security group..."

SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text \
    --region "$REGION" 2>/dev/null || echo "")

if [ -n "$SG_ID" ] && [ "$SG_ID" != "None" ]; then
    echo "  Security group already exists: $SG_ID"
else
    SG_ID=$(aws ec2 create-security-group \
        --group-name "$SG_NAME" \
        --description "Security group for Flask LLM app" \
        --output text \
        --region "$REGION")

    echo "  ✅ Security group created: $SG_ID"
fi

# Add rules (ignore if already exists)
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region "$REGION" 2>/dev/null || echo "    Port 80 already open"

aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 8080 \
    --cidr 0.0.0.0/0 \
    --region "$REGION" 2>/dev/null || echo "    Port 8080 already open"

aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0 \
    --region "$REGION" 2>/dev/null || echo "    Port 22 already open"

echo "  ✅ Security group configured"

#==================================================
# Step 3: Get Latest AMI
#==================================================
echo "[3/6] Getting latest Amazon Linux 2023 AMI..."

AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=al2023-ami-2023.*-x86_64" "Name=state,Values=available" \
    --query "sort_by(Images, &CreationDate)[-1].ImageId" \
    --output text \
    --region "$REGION")

echo "  ✅ AMI ID: $AMI_ID"

#==================================================
# Step 4: Prompt for API Keys
#==================================================
echo ""
echo "[4/6] API Keys Required"
echo "========================================="
echo "You'll need to provide your LLM API keys."
echo "These will be set in the .env file on the EC2 instance."
echo ""
read -p "Enter your Groq API Key (gsk_...): " GROQ_API_KEY
read -p "Enter your Gemini API Key: " GEMINI_API_KEY
read -p "Enter a secure database password: " DB_PASSWORD

if [ -z "$GROQ_API_KEY" ] || [ -z "$GEMINI_API_KEY" ]; then
    echo "  ⚠️  Warning: API keys not provided. You'll need to update .env manually."
fi

#==================================================
# Step 5: Create User Data Script
#==================================================
echo "[5/6] Creating user-data script..."

cat > user-data.sh << 'EOF_SCRIPT'
#!/bin/bash
# User data script for EC2 automatic setup

# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -SL https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install nginx
yum install -y nginx
systemctl start nginx
systemctl enable nginx

# Create application directory
mkdir -p /home/ec2-user/flask-app
cd /home/ec2-user/flask-app

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF_COMPOSE'
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: flask-postgres
    environment:
      POSTGRES_DB: homework_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
      POSTGRES_HOST_AUTH_METHOD: password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d homework_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  flask-app:
    image: ${FLASK_IMAGE:-flask-llm-app:latest}
    container_name: flask-app
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      FLASK_ENV: production
      DATABASE_HOST: postgres
      DATABASE_PORT: 5432
      DATABASE_NAME: homework_db
      DATABASE_USER: postgres
      DATABASE_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
      SECRET_KEY: ${SECRET_KEY}
      ENCRYPTION_REVERSIBLE_KEY: ${ENCRYPTION_KEY}
      GROQ_API_KEY: ${GROQ_API_KEY}
      GEMINI_API_KEY: ${GEMINI_API_KEY}
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 60s
    restart: unless-stopped

volumes:
  postgres-data:
EOF_COMPOSE

# Generate secure keys
SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Create .env file
cat > .env << EOF_ENV
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
SECRET_KEY=$SECRET_KEY
ENCRYPTION_KEY=$ENCRYPTION_KEY
GROQ_API_KEY=${GROQ_API_KEY}
GEMINI_API_KEY=${GEMINI_API_KEY}
FLASK_IMAGE=${FLASK_IMAGE}
EOF_ENV

# Pull and start services
docker-compose pull
docker-compose up -d

# Configure nginx as reverse proxy
cat > /etc/nginx/conf.d/flask-app.conf << 'EOF_NGINX'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts for long LLM requests
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
EOF_NGINX

systemctl restart nginx

# Log completion
echo "Deployment completed at $(date)" > /var/log/user-data-complete.log
EOF_SCRIPT

# Inject API keys into user-data script
sed -i "s/\${GROQ_API_KEY}/${GROQ_API_KEY}/g" user-data.sh
sed -i "s/\${GEMINI_API_KEY}/${GEMINI_API_KEY}/g" user-data.sh
sed -i "s/\${POSTGRES_PASSWORD}/${DB_PASSWORD}/g" user-data.sh
sed -i "s/\${FLASK_IMAGE}/${DOCKERHUB_USERNAME}\/flask-llm-app:latest/g" user-data.sh

echo "  ✅ User-data script created"

#==================================================
# Step 6: Launch EC2 Instance
#==================================================
echo "[6/6] Launching EC2 instance..."

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --count 1 \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --user-data file://user-data.sh \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=flask-llm-app}]" \
    --output text \
    --region "$REGION")

echo "  ✅ Instance launched: $INSTANCE_ID"
echo ""
echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text \
    --region "$REGION")

#==================================================
# Summary
#==================================================
echo ""
echo "========================================="
echo "🎉 Deployment Complete!"
echo "========================================="
echo ""
echo "Instance Details:"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP: $PUBLIC_IP"
echo "  Region: $REGION"
echo "  Key Pair: ${KEY_NAME}.pem"
echo ""
echo "Access URLs:"
echo "  Application: http://$PUBLIC_IP"
echo "  Health Check: http://$PUBLIC_IP/health"
echo ""
echo "⏳  Wait 3-5 minutes for Docker setup to complete"
echo ""
echo "SSH Command:"
echo "  ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
echo ""
echo "To check deployment status:"
echo "  ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP 'docker ps'"
echo ""
echo "To view logs:"
echo "  ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP 'docker logs flask-app'"
echo ""
echo "⚠️  IMPORTANT:"
echo "  - Save the key file: ${KEY_NAME}.pem"
echo "  - API keys are configured in .env"
echo "  - Monitor free tier usage to avoid charges"
echo "========================================="
