#!/bin/bash
# Quick EC2 Deployment Script
# Simplified deployment with minimal prompts

set -e

#==================================================
# CONFIGURATION - Edit these values
#==================================================
KEY_NAME="flask-app-key"
SG_NAME="flask-app-sg"
REGION="us-east-1"
INSTANCE_TYPE="t2.micro"  # Free tier

# IMPORTANT: Set these values before running!
DOCKERHUB_USERNAME="your-dockerhub-username"
GROQ_API_KEY="gsk_your-groq-api-key"
GEMINI_API_KEY="your-gemini-api-key"
DB_PASSWORD="secure-db-password"

#==================================================
# VALIDATION
#==================================================
echo "Validating configuration..."

if [ "$DOCKERHUB_USERNAME" = "your-dockerhub-username" ]; then
    echo "❌ ERROR: Please edit this script and set DOCKERHUB_USERNAME"
    exit 1
fi

if [ -z "$GROQ_API_KEY" ] || [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ ERROR: Please set your API keys in this script"
    exit 1
fi

echo "✅ Configuration valid"
echo ""

#==================================================
# CREATE SSH KEY
#==================================================
echo "Creating SSH key pair..."

if aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" &>/dev/null; then
    echo "  Key already exists"
else
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --query 'KeyMaterial' \
        --output text \
        --region "$REGION" > "${KEY_NAME}.pem"
    chmod 400 "${KEY_NAME}.pem"
    echo "  ✅ Created: ${KEY_NAME}.pem"
fi

#==================================================
# CREATE SECURITY GROUP
#==================================================
echo "Creating security group..."

SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text \
    --region "$REGION" 2>/dev/null || echo "")

if [ -z "$SG_ID" ] || [ "$SG_ID" = "None" ]; then
    SG_ID=$(aws ec2 create-security-group \
        --group-name "$SG_NAME" \
        --description "Flask LLM app security group" \
        --output text \
        --region "$REGION")
fi

# Add rules (ignore duplicates)
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" --protocol tcp --port 80 --cidr 0.0.0.0/0 \
    --region "$REGION" 2>/dev/null || true
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" --protocol tcp --port 8080 --cidr 0.0.0.0/0 \
    --region "$REGION" 2>/dev/null || true
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" --protocol tcp --port 22 --cidr 0.0.0.0/0 \
    --region "$REGION" 2>/dev/null || true

echo "  ✅ Security group: $SG_ID"

#==================================================
# GET AMI
#==================================================
echo "Getting latest Amazon Linux AMI..."
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=al2023-ami-2023.*-x86_64" \
    --query "sort_by(Images, &CreationDate)[-1].ImageId" \
    --output text --region "$REGION")
echo "  ✅ AMI: $AMI_ID"

#==================================================
# CREATE USER DATA
#==================================================
echo "Creating deployment script..."
cat > user-data.sh << EOF
#!/bin/bash
yum update -y
yum install -y docker nginx
systemctl start docker nginx
systemctl enable docker nginx

curl -SL https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

mkdir -p /home/ec2-user/flask-app
cd /home/ec2-user/flask-app

# Create docker-compose.yml
cat > docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: flask-postgres
    environment:
      POSTGRES_DB: homework_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}
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
    image: ${DOCKERHUB_USERNAME}/flask-llm-app:latest
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
      DATABASE_PASSWORD: \${POSTGRES_PASSWORD}
      SECRET_KEY: \${SECRET_KEY}
      ENCRYPTION_REVERSIBLE_KEY: \${ENCRYPTION_KEY}
      GROQ_API_KEY: \${GROQ_API_KEY}
      GEMINI_API_KEY: \${GEMINI_API_KEY}
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
COMPOSE_EOF

# Create .env file
cat > .env << ENVEOF
POSTGRES_PASSWORD=${DB_PASSWORD}
SECRET_KEY=\$(openssl rand -hex 32)
ENCRYPTION_KEY=\$(openssl rand -hex 32)
GROQ_API_KEY=${GROQ_API_KEY}
GEMINI_API_KEY=${GEMINI_API_KEY}
ENVEOF

# Deploy
docker-compose pull
docker-compose up -d

# Configure nginx
cat > /etc/nginx/conf.d/flask-app.conf << 'NGINXEOF'
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
NGINXEOF

systemctl restart nginx
echo "Done at \$(date)" > /var/log/user-data-complete.log
EOF

#==================================================
# LAUNCH INSTANCE
#==================================================
echo "Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --count 1 \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --user-data file://user-data.sh \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=flask-llm-app}]" \
    --output text --region "$REGION")

aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text --region "$REGION")

#==================================================
# DONE
#==================================================
echo ""
echo "========================================="
echo "🎉 Deployed!"
echo "========================================="
echo "Instance: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "URL: http://$PUBLIC_IP"
echo ""
echo "SSH: ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
echo "Logs: ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP 'docker logs flask-app'"
echo ""
echo "Wait 3-5 minutes for Docker setup..."
echo "========================================="
