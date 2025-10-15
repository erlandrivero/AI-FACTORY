# MongoDB Setup Guide

## Why MongoDB?
MongoDB allows your agents to persist across deployments and sync between local development and production environments.

---

## Quick Setup

### 1. Get Your MongoDB Connection String

If you already have MongoDB, get your connection string. It looks like:
```
mongodb+srv://username:password@cluster.mongodb.net/ai_factory?retryWrites=true&w=majority
```

**OR** sign up for free at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register):
- Free tier: 512 MB storage
- No credit card required
- Takes 2 minutes

---

### 2. Add to Streamlit Secrets

#### Local Development
Create or edit `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "sk-your-key-here"
MONGODB_URI = "mongodb+srv://username:password@cluster.mongodb.net/ai_factory"
```

#### Production (Streamlit Cloud)
1. Go to your app settings on Streamlit Cloud
2. Click "Secrets"
3. Add:
```toml
MONGODB_URI = "mongodb+srv://username:password@cluster.mongodb.net/ai_factory"
```

---

## Features

### ✅ What You Get:
- **Persistent agents** - Agents survive deployments
- **Sync across environments** - Same agents in local & production
- **Auto-migration** - Existing `agents.json` automatically migrated
- **Fallback mode** - Works without MongoDB (uses JSON)

### 📊 Database Structure:
- **Database:** `ai_factory`
- **Collection:** `agents`
- **Documents:** Each agent with `id`, `role`, `goal`, `backstory`, `allow_delegation`

---

## Testing

1. **Add MongoDB URI** to secrets
2. **Restart app** - Migration happens automatically
3. **Check success** - You'll see "✅ Migrated X agents from JSON to MongoDB"
4. **Add new agent** - It's saved to MongoDB
5. **Redeploy app** - Agents persist! 🎉

---

## Troubleshooting

### "MongoDB connection failed"
- Check your connection string
- Ensure IP whitelist includes `0.0.0.0/0` (allow all) in MongoDB Atlas
- Verify username/password are correct

### "No module named 'pymongo'"
Run: `pip install pymongo>=4.6.0`

### Agents not syncing
- Confirm both local and production use the **same MongoDB URI**
- Check MongoDB Atlas dashboard to verify data

---

## Without MongoDB

The app works perfectly without MongoDB - it just uses the local `agents.json` file. You'll see a tip message suggesting MongoDB for persistence.
