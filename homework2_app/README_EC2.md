# Flask LLM App - EC2 Deployment (Free Tier)

Quick deployment guide for running the Flask LLM application on AWS EC2 free tier.

## 🚀 Quick Start

### Option 1: Automated Deployment (Recommended)

```bash
# 1. Edit deploy-ec2-quick.sh and set your configuration:
#    - DOCKERHUB_USERNAME
#    - GROQ_API_KEY
#    - GEMINI_API_KEY

# 2. Run the script
chmod +x deploy-ec2-quick.sh
./deploy-ec2-quick.sh

# 3. Wait 3-5 minutes, then access your app at the provided URL
```

### Option 2: Interactive Deployment

```bash
chmod +x deploy-ec2.sh
./deploy-ec2.sh
# Follow prompts for API keys and configuration
```

### Option 3: Manual Deployment

See `EC2_DEPLOYMENT.md` for detailed manual steps.

---

## 📋 Prerequisites

- AWS Account with free tier eligibility
- AWS CLI installed and configured
- Docker Hub account
- Your Groq API key: https://console.groq.com/keys
- Your Gemini API key: https://makersuite.google.com/app/apikey

---

## 🏗️ Architecture

```
Internet → EC2 (t2.micro) → Nginx (port 80)
                             ↓
                         Flask App (port 8080)
                             ↓
                         PostgreSQL (port 5432)
```

**Free Tier Resources:**
- EC2 t2.micro: 750 hours/month (12 months free)
- Total cost: $0/month

---

## 📦 Files Created

| File | Purpose |
|------|---------|
| `deploy-ec2-quick.sh` | Quick deployment (edit config first) |
| `deploy-ec2.sh` | Interactive deployment with prompts |
| `EC2_DEPLOYMENT.md` | Complete deployment documentation |
| `docker-compose.ec2.yml` | Docker Compose for EC2 |
| `.env.ec2.example` | Environment variables template |
| `README_EC2.md` | This file |

---

## 🔑 Required Settings

Before deployment, ensure you have:

1. **Docker Image** built and pushed:
   ```bash
   docker build -t flask-llm-app:latest .
   docker tag flask-llm-app:latest your-username/flask-llm-app:latest
   docker push your-username/flask-llm-app:latest
   ```

2. **API Keys** ready:
   - Groq API key (gsk_...)
   - Gemini API key

---

## 🖥️ Accessing Your Application

After deployment:
- **Application**: `http://<PUBLIC_IP>`
- **Health Check**: `http://<PUBLIC_IP>/health`

SSH into instance:
```bash
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP>
```

---

## 📊 Monitoring

### Check Status
```bash
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP>
docker ps                    # Running containers
docker logs flask-app        # Flask logs
docker logs flask-postgres   # Database logs
```

### Restart Services
```bash
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP>
cd /home/ec2-user/flask-app
docker-compose restart
```

### Update Application
```bash
# Build and push new image locally
docker build -t flask-llm-app:v2 .
docker push your-username/flask-llm-app:latest

# Pull and restart on EC2
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP
cd /home/ec2-user/flask-app
docker-compose pull
docker-compose up -d
```

---

## 💰 Cost Management

### Check Free Tier Usage
```bash
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"
```

### Stop Instance (save free tier hours)
```bash
aws ec2 stop-instances --instance-ids <INSTANCE_ID>
```

### Start Instance
```bash
aws ec2 start-instances --instance-ids <INSTANCE_ID>
```

---

## 🧹 Cleanup

```bash
# Terminate instance
aws ec2 terminate-instances --instance-ids <INSTANCE_ID>

# Delete security group
aws ec2 delete-security-group --group-id <SG_ID>

# Delete key pair
aws ec2 delete-key-pair --key-name flask-app-key
rm flask-app-key.pem
```

---

## ⚠️ Important Notes

1. **API Keys**: These are stored in `.env` on the EC2 instance
2. **Database Password**: Change the default in `.env`
3. **Free Tier Limits**: Monitor usage to avoid unexpected charges
4. **Instance Size**: t2.micro has 1GB RAM - upgrade if needed
5. **Security**: Consider using AWS Secrets Manager for production

---

## 🆘 Troubleshooting

### Application Not Loading
```bash
# Check if containers are running
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP> 'docker ps'

# Check nginx status
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP> 'systemctl status nginx'

# View logs
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP> 'docker logs flask-app'
```

### Database Connection Issues
```bash
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP>
docker logs flask-postgres
docker exec -it flask-postgres psql -U postgres -d homework_db
```

### Out of Memory (t2.micro limit: 1GB)
```bash
# Check memory
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP> 'free -h'

# Upgrade to t2.small (2GB RAM, ~$15/month)
aws ec2 modify-instance-attribute \
  --instance-id <INSTANCE_ID> \
  --instance-type "{\"Value\": \"t2.small\"}"
```

---

## 📚 Full Documentation

See `EC2_DEPLOYMENT.md` for:
- Detailed architecture
- Security hardening
- Scaling beyond free tier
- Backup strategies
- HTTPS setup with ACM

---

## 🎯 What's Deployed

✅ EC2 t2.micro instance (free tier)
✅ Docker + Docker Compose
✅ Flask application with WebSocket support
✅ PostgreSQL with pgvector extension
✅ Nginx reverse proxy
✅ Health checks
✅ Auto-start on boot
✅ Persistent database storage

---

## 🔄 Next Steps

1. **Access your application** at the provided URL
2. **Update API keys** if needed via `.env` file
3. **Monitor free tier usage** in AWS Billing Console
4. **Set up billing alerts** to avoid unexpected charges
5. **Consider HTTPS** for production (see EC2_DEPLOYMENT.md)

---

**Total Monthly Cost: $0** (within AWS Free Tier limits)
