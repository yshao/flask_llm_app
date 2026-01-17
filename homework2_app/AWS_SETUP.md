# AWS Setup Guide for EC2 Deployment

Follow these steps to get AWS credentials and deploy your Flask app to EC2 Free Tier.

---

## Step 1: Create an AWS Account (if you don't have one)

1. Go to https://aws.amazon.com/
2. Click "Create an AWS Account"
3. Follow the signup process (requires credit card, but free tier is free)
4. Verify your email address
5. Choose "Basic" (Free Tier) support plan

**Note:** AWS requires a credit card for sign-up, but you won't be charged for free tier usage.

---

## Step 2: Create an IAM User for Deployment

Using the root account is not recommended. Let's create a dedicated IAM user.

### Option A: Via AWS Console (Easier)

1. **Sign in to AWS Console**
   - Go to https://console.aws.amazon.com/
   - Sign in with your root account

2. **Navigate to IAM**
   - Search for "IAM" in the search bar
   - Click "IAM" to open the Identity and Access Management dashboard

3. **Create a New User**
   - Click "Users" in the left sidebar
   - Click "Create user"
   - User name: `ec2-deployment`
   - Select "Attach policies directly"
   - Search for and select: `AdministratorAccess` (for easy deployment)
   - Click "Create user"

4. **Create Access Keys**
   - Find the user you just created (`ec2-deployment`)
   - Click on the username
   - Go to "Security credentials" tab
   - Click "Create access key"
   - Select "Application running outside AWS"
   - Click "Next"
   - **IMPORTANT:** Click "Download .csv file" or copy the keys now
   - You'll need:
     - Access Key ID (starts with `AKIA...`)
     - Secret Access Key (longer string)

### Option B: Via AWS CLI (If you have root access)

```bash
# Create IAM user
aws iam create-user --user-name ec2-deployment

# Attach AdministratorAccess policy
aws iam attach-user-policy \
  --user-name ec2-deployment \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Create access key
aws iam create-access-key --user-name ec2-deployment
```

This will return JSON with your `AccessKeyId` and `SecretAccessKey`.

---

## Step 3: Configure AWS CLI

Once you have your credentials:

### Run the configure command:

```bash
aws configure
```

You'll be prompted for:

```
AWS Access Key ID [None]: AKIA... (paste your Access Key ID)
AWS Secret Access Key [None]: (paste your Secret Access Key)
Default region name [None]: us-east-1
Default output format [None]: json
```

### Verify Configuration:

```bash
aws configure list
```

You should see:
```
Name                    Value             Type    Location
----                    -----             ----    --------
profile                <not set>             None    None
access_key             AKIA...           shared-credentials-file
secret_key            ...                shared-credentials-file
region                 us-east-1           config-file
```

### Test Configuration:

```bash
aws ec2 describe-security-groups --region us-east-1
```

If this returns a list of security groups (or empty list), you're configured correctly!

---

## Step 4: Deploy Your Application

Now that AWS is configured, run the deployment script:

```bash
cd /mnt/c/Users/yshao/Desktop/2025/codes/ai_interview/flask_llm_app/homework2_app
./deploy-ec2-local.sh
```

This will:
1. ✅ Create SSH key pair
2. ✅ Set up security group
3. ✅ Launch EC2 t2.micro (FREE tier)
4. ✅ Copy your app to EC2
5. ✅ Build Docker image on EC2
6. ✅ Start all services

---

## Step 5: Get Your API Keys

While EC2 is deploying (takes 5-10 minutes), get your LLM API keys:

### Groq API Key (Required for chat)

1. Go to https://console.groq.com/
2. Sign up or log in
3. Click "Create Key" or go to https://console.groq.com/keys
4. Copy your key (starts with `gsk_...`)

### Gemini API Key (Required for embeddings)

1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API key"
4. Copy your API key

---

## Step 6: Add API Keys to Your Deployment

Once the deployment script completes, it will show you a **Public IP**.

```bash
# SSH into your EC2 instance
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP>

# Edit environment file
cd /home/ec2-user/flask-app
nano .env
```

Update these values:
```bash
GROQ_API_KEY=gsk_your_actual_groq_key
GEMINI_API_KEY=your_actual_gemini_key
```

Save and exit (Ctrl+X, Y, Enter).

```bash
# Restart services with new keys
docker-compose restart

# Check logs
docker logs flask-app
```

---

## Step 7: Access Your Application

Open your browser:
```
http://<PUBLIC_IP>
```

Or check health:
```
http://<PUBLIC_IP>/health
```

---

## Troubleshooting

### "Unable to locate credentials"

Run: `aws configure` and enter your credentials again.

### "ssh: connect to host port 22: Connection refused"

Wait 1-2 minutes for the EC2 instance to fully start up, then try again.

### "Permission denied (publickey)"

Make sure you're using the correct key file: `flask-app-key.pem`

### "Key file has incorrect permissions"

Run: `chmod 400 flask-app-key.pem`

### Application not loading after adding API keys

```bash
ssh -i flask-app-key.pem ec2-user@<PUBLIC_IP>
cd /home/ec2-user/flask-app
docker logs flask-app
docker-compose restart
```

---

## Managing Your Deployment

### Stop Instance (save free tier hours)
```bash
aws ec2 stop-instances --instance-ids <INSTANCE_ID>
```

### Start Instance
```bash
aws ec2 start-instances --instance-ids <INSTANCE_ID>
```

### Check Status
```bash
aws ec2 describe-instances --instance-ids <INSTANCE_ID>
```

### Terminate (delete) Instance
```bash
aws ec2 terminate-instances --instance-ids <INSTANCE_ID>
```

---

## Cost Monitoring

### Check Free Tier Usage

Go to: https://console.aws.amazon.com/billing/home#/account

### Set Up Billing Alert

1. Go to AWS Billing Console
2. Click "Billing preferences"
3. Enable "Receive Free Tier Usage Alerts"
4. Enter your email

---

## Summary

**What You Need:**
- ✅ AWS Account with credentials
- ✅ AWS CLI configured
- ✅ Groq API key
- ✅ Gemini API key

**What You Get:**
- ✅ Flask app running on EC2 t2.micro (FREE)
- ✅ PostgreSQL with pgvector
- ✅ WebSocket chat support
- ✅ Public URL

**Monthly Cost:** $0 (within free tier limits)

---

Need help? Check the main deployment documentation in `instructions.md` and `EC2_DEPLOYMENT.md`.
