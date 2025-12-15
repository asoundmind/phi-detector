# Deployment Guide - PHI Detector

This guide will help you deploy the PHI Detector app to **Streamlit Community Cloud** (100% FREE) with **auto-deploy on git push**.

---

## 🎯 What You'll Get

- ✅ **Free hosting** (unlimited for public apps)
- ✅ **Auto-deploy** on every git push to master
- ✅ **Live URL** to share (e.g., `https://your-app.streamlit.app`)
- ✅ **Free LLM API** (Hugging Face - 1000 requests/hour)

---

## 📋 Prerequisites

1. **GitHub account** (free)
2. **Hugging Face account** (free)
3. Your code pushed to GitHub repository

---

## Step 1: Get Hugging Face API Token (FREE)

1. Go to: https://huggingface.co/join
2. Sign up (free)
3. Go to: https://huggingface.co/settings/tokens
4. Click **"New token"**
5. Name it: `phi-detector-app`
6. Type: **Read**
7. Click **"Generate token"**
8. **Copy the token** (starts with `hf_...`)

**Keep this token safe - you'll need it in Step 3!**

---

## Step 2: Push Code to GitHub

If you haven't already:

```bash
# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Deploy PHI detector with HuggingFace"

# Create GitHub repo and push
# (Follow GitHub instructions to create a new repo)
git remote add origin https://github.com/YOUR_USERNAME/phi-detector.git
git branch -M master
git push -u origin master
```

**Important:** Make sure `.streamlit/secrets.toml` is NOT pushed (it's in `.gitignore`)

---

## Step 3: Deploy to Streamlit Cloud

### 3.1 Sign Up for Streamlit Cloud

1. Go to: https://share.streamlit.io/
2. Click **"Continue with GitHub"**
3. Authorize Streamlit to access your repos

### 3.2 Deploy Your App

1. Click **"New app"**
2. Select your repository: `phi-detector`
3. Branch: `master`
4. Main file path: `app.py`
5. Click **"Advanced settings"**

### 3.3 Configure Secrets (API Key)

In the **Secrets** section, paste:

```toml
HF_TOKEN = "hf_your_actual_token_here"
```

Replace `hf_your_actual_token_here` with your **actual Hugging Face token** from Step 1.

### 3.4 Deploy!

1. Click **"Deploy!"**
2. Wait 2-5 minutes for deployment
3. Your app will be live at: `https://[your-app-name].streamlit.app`

---

## Step 4: Auto-Deploy Setup ✅

**Already configured!** Every time you push to `master`:

```bash
git add .
git commit -m "Update feature"
git push origin master
```

Streamlit Cloud will **automatically redeploy** your app within 1-2 minutes.

---

## 🧪 Test Your Deployment

1. Visit your app URL
2. Click **"Reload Policy Documents"** in sidebar
3. Try the example buttons:
   - 📋 Support Ticket
   - 🛠️ Chat Encryption
   - ❓ What is PII?
4. Verify responses are generated

---

## 🔧 Troubleshooting

### App shows "HuggingFace API health check failed"

**Solution:** Check your API token in Streamlit secrets
1. Go to app settings
2. Click "Secrets"
3. Verify `HF_TOKEN` is correct

### ChromaDB errors

**Solution:** First time loading documents may fail
1. Click **"Reload Policy Documents"** button in sidebar
2. Wait for success message

### Slow responses

**Normal!** Free Hugging Face API can be slower than local Ollama
- First request may take 10-30 seconds (model loading)
- Subsequent requests: 3-10 seconds

### Rate limits

Free tier: **1000 requests/hour**
- More than enough for demos
- If you hit limit, wait 1 hour or upgrade to Pro (paid)

---

## 💰 Cost Breakdown

| Service | Cost |
|---------|------|
| Streamlit Cloud | **FREE** |
| Hugging Face API | **FREE** (1000 req/hr) |
| **Total** | **$0/month** |

---

## 🚀 Next Steps

**For better performance (optional):**

1. **Upgrade Hugging Face to Pro** ($9/month)
   - Faster inference
   - Higher rate limits

2. **Use OpenAI API** (paid)
   - Better quality responses
   - ~$5-10/month for light usage
   - Update `src/chatbot.py` to use OpenAI client

**For production (not for demo):**

- Self-host on AWS/GCP with GPU (~$800-1000/month)
- Required for actual PHI compliance

---

## 📝 Configuration Options

### Change LLM Model

Edit `src/chatbot.py`:

```python
# Current model (default)
model = "mistralai/Mistral-7B-Instruct-v0.2"

# Alternative free models:
# model = "meta-llama/Llama-2-7b-chat-hf"
# model = "google/flan-t5-xl"
```

### Adjust Response Length

Edit `src/chatbot.py` - look for `max_tokens` parameters:

```python
# Current: 600-800 tokens
# Increase for longer responses (uses more quota)
max_tokens=1000
```

---

## 🎬 Demo Tips

1. **Pre-load documents** before presenting
   - Click "Reload Policy Documents" before demo
   - Verify "✅ Documents loaded" message

2. **Use example buttons** for smooth demo
   - Examples are pre-loaded and tested
   - Shows all feature types

3. **Share the live URL** with audience
   - They can try it themselves
   - Shows real deployment capability

4. **Show the Chain of Thought** reasoning
   - Click expandable sections in results
   - Demonstrates AI transparency

---

## 📞 Support

- **Streamlit Docs:** https://docs.streamlit.io/
- **Hugging Face Docs:** https://huggingface.co/docs
- **Issues:** Create issue in your GitHub repo

---

## 🔒 Security Notes

**For demo/prototype only!**

- This setup is **NOT HIPAA compliant**
- Do **NOT use real PHI/PII** data
- Use **synthetic/example data** only
- For production, self-host with proper security

---

**You're all set! 🎉**

Your app should now be deployed and auto-deploying on every git push.
