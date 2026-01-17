# EC2 Free-Tier Deployment Guide for Flask LLM Application

## Overview

Deploy the Flask AI agent application on AWS EC2 using Docker, completely within AWS Free Tier limits.

**Architecture:**
```
Internet → EC2 Instance (t2.micro) → Docker Compose
                                      ├── Flask App (port 8080)
                                      └── PostgreSQL (port 5432)
```

**Free Tier Resources:**
- **EC2 t2.micro**: 750 hours/month × 12 months free
- **Data Transfer**: 100 GB/month free
- **Public IP**: 750 hours/month free
- **Total Cost**: $0/month (within free tier)

---

## Prerequisites

- AWS Account with free tier eligibility
- AWS CLI installed locally
- SSH key pair created in AWS
- Docker Hub account (for container registry)

---

## Step 1: Create SSH Key Pair

```bash
# Create SSH key pair (us-east-1)
aws ec2 create-key-pair \
  --key-name flask-app-key \
  --query 'KeyMaterial' \
  --output text > flask-app-key.pem

# Set proper permissions
chmod 400 flask-app-key.pem
```

---

## Step 2: Create Security Group

```bash
# Create security group
SG_ID=$(aws ec2 create-security-group \
  --group-name flask-app-sg \
  --description "Security group for Flask LLM app" \
  --output text)

# Add HTTP access (port 80 - for nginx redirect to 8080)
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Add direct access to Flask app (port 8080)
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 8080 \
  --cidr 0.0.0.0/0

# Add SSH access
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

echo "Security Group ID: $SG_ID"
```

---

## Step 3: Build and Push Docker Image

```bash
cd homework2_app

# Login to Docker Hub
docker login

# Build image
docker build -t flask-llm-app:latest .

# Tag for Docker Hub
docker tag flask-llm-app:latest your-dockerhub-username/flask-llm-app:latest

# Push to Docker Hub
docker push your-dockerhub-username/flask-llm-app:latest
```

---

## Step 4: Launch EC2 Instance

The EC2 instance will automatically set up Docker and deploy your application using a user-data script.

```bash
# Get latest AMI ID for Amazon Linux 2023 in us-east-1
AMI_ID=$(aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=al2023-ami-2023.*-x86_64" "Name=state,Values=available" \
  --query "sort_by(Images, &CreationDate)[-1].ImageId" \
  --output text)

# Create user-data script for automatic setup
cat > user-data.sh << 'EOF'
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

# Install Git
yum install -y git

# Create application directory
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
    image: ${FLASK_IMAGE:-your-dockerhub-username/flask-llm-app:latest}
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
      SECRET_KEY: ${SECRET_KEY:-change-this-secret-key}
      ENCRYPTION_REVERSIBLE_KEY: ${ENCRYPTION_KEY:-change-this-encryption-key}
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
COMPOSE_EOF

# Create .env file from instance metadata or defaults
cat > .env << 'ENV_EOF'
# Database Configuration
POSTGRES_PASSWORD=secure-password-change-me

# Flask Security (generate secure keys)
SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# LLM API Keys (set these!)
GROQ_API_KEY=your-groq-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here

# Docker Image
FLASK_IMAGE=your-dockerhub-username/flask-llm-app:latest
ENV_EOF

# Pull images and start services
docker-compose pull
docker-compose up -d

# Install nginx as reverse proxy (optional, for port 80 access)
yum install -y nginx
systemctl start nginx
systemctl enable nginx

# Configure nginx to proxy to Flask app
cat > /etc/nginx/conf.d/flask-app.conf << 'NGINX_EOF'
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
NGINX_EOF

# Restart nginx
systemctl restart nginx

# Output status
echo "========================================="
echo "Flask LLM Application Deployed!"
echo "========================================="
echo "Application URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "Health Check: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)/health"
echo ""
echo "To update API keys:"
echo "  1. SSH into the instance"
echo "  2. Edit /home/ec2-user/flask-app/.env"
echo "  3. Run: docker-compose restart"
echo "========================================="

# Send completion signal
echo "User data script completed successfully" > /var/log/user-data-complete.log
EOF

# Launch EC2 instance with user-data script
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --count 1 \
  --instance-type t2.micro \
  --key-name flask-app-key \
  --security-group-ids $SG_ID \
  --user-data file://user-data.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=flask-llm-app}]' \
  --output text)

echo "Launching EC2 instance: $INSTANCE_ID"
echo "Waiting for instance to initialize..."

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo ""
echo "========================================="
echo "EC2 Instance Launching!"
echo "========================================="
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "URL: http://$PUBLIC_IP"
echo ""
echo "Wait 3-5 minutes for Docker setup to complete"
echo "Then access: http://$PUBLIC_IP"
echo "========================================="
```

---

## Step 5: Monitor Deployment

```bash
# SSH into the instance (replace with your IP)
ssh -i flask-app-key.pem ec2-user@$PUBLIC_IP

# Check Docker containers
docker ps

# Check application logs
docker logs flask-app

# Check database logs
docker logs flask-postgres

# View health status
curl http://localhost:8080/health
```

---

## Step 6: Update API Keys (Important!)

The deployment starts with placeholder API keys. Update them:

```bash
# SSH into instance
ssh -i flask-app-key.pem ec2-user@$PUBLIC_IP

# Edit environment file
cd /home/ec2-user/flask-app
nano .env

# Update these values:
# GROQ_API_KEY=gsk_your_actual_groq_api_key
# GEMINI_API_KEY=your_actual_gemini_api_key

# Restart services
docker-compose restart

# Verify
docker logs flask-app
```

---

## Step 7: Access Application

```
URL: http://<PUBLIC_IP>
Health Check: http://<PUBLIC_IP>/health
```

---

## Management Commands

### View Logs
```bash
ssh -i flask-app-key.pem ec2-user@$PUBLIC_IP
docker logs -f flask-app
```

### Restart Services
```bash
ssh -i flask-app-key.pem ec2-user@$PUBLIC_IP
cd /home/ec2-user/flask-app
docker-compose restart
```

### Update Application
```bash
# Build new image locally
docker build -t flask-llm-app:v2 .
docker tag flask-llm-app:v2 your-dockerhub-username/flask-llm-app:latest
docker push your-dockerhub-username/flask-llm-app:latest

# SSH into EC2 and pull
ssh -i flask-app-key.pem ec2-user@$PUBLIC_IP
cd /home/ec2-user/flask-app
docker-compose pull
docker-compose up -d
```

### Backup Database
```bash
ssh -i flask-app-key.pem ec2-user@$PUBLIC_IP
docker exec flask-postgres pg_dump -U postgres homework_db > backup.sql
docker cp flask-postgres:/backup.sql ./backup_$(date +%Y%m%d).sql
```

### Stop Instance (to save free tier hours)
```bash
aws ec2 stop-instances --instance-ids $INSTANCE_ID
```

### Start Instance
```bash
aws ec2 start-instances --instance-ids $INSTANCE_ID
```

---

## Cost Monitoring

### Check Free Tier Usage
```bash
# View running instances
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=$INSTANCE_ID \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average
```

### Set Up Billing Alerts
1. Go to AWS Billing Console
2. Create a budget for $0
3. Set email alerts for any usage

---

## Troubleshooting

### Application Not Accessible
```bash
# Check security group
aws ec2 describe-security-groups --group-ids $SG_ID

# Check instance status
aws ec2 describe-instance-status --instance-ids $INSTANCE_ID

# Check nginx status
ssh -i flask-app-key.pem ec2-user@$PUBLIC_IP
systemctl status nginx
```

### Database Connection Issues
```bash
docker logs flask-postgres
docker exec -it flask-postgres psql -U postgres -d homework_db
```

### Out of Memory (t2.micro has 1GB RAM)
```bash
# Check memory usage
free -h

# Check Docker stats
docker stats

# If needed, upgrade to t2.small (2GB RAM, not free):
aws ec2 modify-instance-attribute \
  --instance-id $INSTANCE_ID \
  --instance-type "{\"Value\": \"t2.small\"}"
```

---

## Security Notes

### Change These Default Values
- POSTGRES_PASSWORD in .env
- SECRET_KEY in .env
- ENCRYPTION_KEY in .env
- Add your actual API keys

### Recommended Security Improvements
1. Set up AWS Secrets Manager for API keys
2. Enable VPC with private subnets
3. Use AWS Certificate Manager for HTTPS
4. Set up security group rules for specific IPs only
5. Regularly update the OS: `sudo yum update`

---

## Scaling Beyond Free Tier

When ready to scale beyond free tier:

1. **Upgrade Instance Type:**
   ```bash
   # t2.small: 2GB RAM (~$15/month)
   # t2.medium: 4GB RAM (~$30/month)
   # t3.medium: 2 vCPU, 4GB RAM (~$25/month)
   aws ec2 modify-instance-attribute \
     --instance-id $INSTANCE_ID \
     --instance-type "{\"Value\": \"t2.medium\"}"
   ```

2. **Add EBS Storage for Database:**
   - Create EBS volume
   - Attach to EC2
   - Mount as PostgreSQL data directory

3. **Use Load Balancer:**
   - Deploy multiple EC2 instances
   - Add Application Load Balancer
   - Configure health checks

---

## Cleanup (Delete Resources)

```bash
# Terminate instance
aws ec2 terminate-instances --instance-ids $INSTANCE_ID

# Delete security group (wait for instance to terminate first)
aws ec2 delete-security-group --group-id $SG_ID

# Delete key pair
aws ec2 delete-key-pair --key-name flask-app-key
rm flask-app-key.pem

# Remove local files
rm user-data.sh
```

---

## Summary

**What Was Created:**
- ✅ EC2 t2.micro instance (free tier)
- ✅ Docker + Docker Compose auto-installed
- ✅ Flask app + PostgreSQL deployed
- ✅ Nginx reverse proxy (port 80 → 8080)
- ✅ WebSocket support via nginx
- ✅ Health checks configured
- ✅ Auto-start on boot

**Access URLs:**
- Application: `http://<PUBLIC_IP>`
- Health Check: `http://<PUBLIC_IP>/health`

**Monthly Cost:** $0 (within free tier limits)
