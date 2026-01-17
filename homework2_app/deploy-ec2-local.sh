#!/bin/bash
# EC2 Deployment Script - Build on EC2 (No Docker Hub Required)
# This script deploys your app to EC2 and builds the Docker image directly on the instance

set -e

#==================================================
# CONFIGURATION
#==================================================
KEY_NAME="flask-app-key"
SG_NAME="flask-app-sg"
REGION="us-east-1"
INSTANCE_TYPE="t2.micro"  # Free tier
LOCAL_APP_PATH="/mnt/c/Users/yshao/Desktop/2025/codes/ai_interview/flask_llm_app/homework2_app"

echo "========================================="
echo "Flask LLM App - EC2 Deployment"
echo "(No Docker Hub - Build on EC2)"
echo "========================================="
echo ""

#==================================================
# Step 1: Create SSH Key
#==================================================
echo "[1/7] Creating SSH key pair..."

if aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" &>/dev/null; then
    echo "  ✓ Key pair already exists"
else
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --query 'KeyMaterial' \
        --output text \
        --region "$REGION" > "${KEY_NAME}.pem"
    chmod 400 "${KEY_NAME}.pem"
    echo "  ✓ Created: ${KEY_NAME}.pem"
fi

#==================================================
# Step 2: Create Security Group
#==================================================
echo "[2/7] Creating security group..."

SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text \
    --region "$REGION" 2>/dev/null || echo "")

if [ -z "$SG_ID" ] || [ "$SG_ID" = "None" ]; then
    SG_ID=$(aws ec2 create-security-group \
        --group-name "$SG_NAME" \
        --description "Flask LLM app" \
        --output text \
        --region "$REGION")
fi

# Add firewall rules
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 80 --cidr 0.0.0.0/0 --region "$REGION" 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 8080 --cidr 0.0.0.0/0 --region "$REGION" 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 22 --cidr 0.0.0.0/0 --region "$REGION" 2>/dev/null || true

echo "  ✓ Security group: $SG_ID"

#==================================================
# Step 3: Get Latest AMI
#==================================================
echo "[3/7] Getting latest Amazon Linux AMI..."
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=al2023-ami-2023.*-x86_64" \
    --query "sort_by(Images, &CreationDate)[-1].ImageId" \
    --output text --region "$REGION")
echo "  ✓ AMI: $AMI_ID"

#==================================================
# Step 4: Launch EC2 Instance
#==================================================
echo "[4/7] Launching EC2 instance..."

cat > user-data.sh << 'EOF'
#!/bin/bash
# EC2 User Data Script - Setup Environment

# Update system
yum update -y

# Install Docker and required tools
yum install -y docker git nginx
systemctl start docker nginx
systemctl enable docker nginx

# Install Docker Compose
curl -SL https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create app directory
mkdir -p /home/ec2-user/flask-app
chown -R ec2-user:ec2-user /home/ec2-user/flask-app

# Signal setup complete
echo "Setup complete at $(date)" > /var/log/setup-complete.log
EOF

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

echo "  ✓ Instance launched: $INSTANCE_ID"
echo "  Waiting for instance to initialize..."

aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"

PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text \
    --region "$REGION")

echo "  ✓ Instance IP: $PUBLIC_IP"

#==================================================
# Step 5: Copy Application Files to EC2
#==================================================
echo "[5/7] Copying application files to EC2..."
echo "  This may take a few minutes..."

# Wait for SSH to be available
echo "  Waiting for SSH to be ready..."
sleep 30

# Create tarball of application
echo "  Creating application tarball..."
cd "$LOCAL_APP_PATH"
tar -czf /tmp/flask-app.tar.gz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='logs/*' \
    --exclude='.env' \
    . 2>/dev/null || tar -czf /tmp/flask-app.tar.gz .

# Copy tarball to EC2
echo "  Uploading to EC2 (this may take 2-3 minutes)..."
scp -i "${KEY_NAME}.pem" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    /tmp/flask-app.tar.gz \
    ec2-user@"$PUBLIC_IP":/tmp/

# Extract on EC2
echo "  Extracting files on EC2..."
ssh -i "${KEY_NAME}.pem" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    ec2-user@"$PUBLIC_IP" \
    "mkdir -p /home/ec2-user/flask-app && tar -xzf /tmp/flask-app.tar.gz -C /home/ec2-user/flask-app"

echo "  ✓ Files copied successfully"

#==================================================
# Step 6: Build and Start Application
#==================================================
echo "[6/7] Building Docker image on EC2..."
echo "  This will take 3-5 minutes..."

ssh -i "${KEY_NAME}.pem" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    ec2-user@"$PUBLIC_IP" << 'ENDSSH'
cd /home/ec2-user/flask-app

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
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
    build: .
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
      SECRET_KEY: ${SECRET_KEY:-default-secret-change-me}
      ENCRYPTION_REVERSIBLE_KEY: ${ENCRYPTION_KEY:-default-key-change-me}
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
EOF

# Create .env file (API keys will be added manually)
cat > .env << 'ENVEOF'
# Database
POSTGRES_PASSWORD=changeme
SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# LLM API Keys - ADD THESE MANUALLY!
GROQ_API_KEY=
GEMINI_API_KEY=
ENVEOF

# Build and start
echo "Building Docker image (this takes 3-5 minutes)..."
docker-compose build
docker-compose up -d

# Wait for containers to be healthy
echo "Waiting for services to start..."
sleep 30

# Configure nginx
cat > /tmp/flask-app-nginx.conf << 'NGINXEOF'
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
NGINXEOF

sudo mv /tmp/flask-app-nginx.conf /etc/nginx/conf.d/flask-app.conf
sudo systemctl restart nginx

echo "Build complete!"
ENDSSH

echo "  ✓ Docker image built and services started"

#==================================================
# Step 7: Deployment Complete
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
echo ""
echo "Access URLs:"
echo "  Application: http://$PUBLIC_IP"
echo "  Health Check: http://$PUBLIC_IP/health"
echo ""
echo "⚠️  IMPORTANT - Next Steps:"
echo ""
echo "1. ADD YOUR API KEYS:"
echo "   ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
echo "   nano /home/ec2-user/flask-app/.env"
echo "   # Update these values:"
echo "   GROQ_API_KEY=gsk_your_actual_key"
echo "   GEMINI_API_KEY=your_actual_key"
echo "   # Save and exit"
echo ""
echo "2. RESTART SERVICES:"
echo "   ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
echo "   cd /home/ec2-user/flask-app"
echo "   docker-compose restart"
echo ""
echo "3. VERIFY DEPLOYMENT:"
echo "   ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP 'docker ps'"
echo "   curl http://$PUBLIC_IP/health"
echo ""
echo "4. VIEW LOGS:"
echo "   ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP 'docker logs flask-app'"
echo ""
echo "Management Commands:"
echo "  Stop: aws ec2 stop-instances --instance-ids $INSTANCE_ID"
echo "  Start: aws ec2 start-instances --instance-ids $INSTANCE_ID"
echo "  Terminate: aws ec2 terminate-instances --instance-ids $INSTANCE_ID"
echo ""
echo "⏳  Note: Build may take another 2-3 minutes to complete"
echo "========================================="

# Cleanup temp files
rm -f /tmp/flask-app.tar.gz user-data.sh
