# 🎯 AI Factory - Quick Reference Card

## 🚀 Start the App
```bash
streamlit run app.py
```

---

## 📋 5-Phase Workflow

### 1️⃣ Idea Input
- Enter your project idea
- Upload reference files (optional)
- Click: **"🎯 Plan Strategy"**
- → Strategy Consultant analyzes

### 2️⃣ Strategy Selection
- Review 3 solution packages
- Select: Package A, B, C, or Custom
- Add features & requirements
- Click: **"Continue →"**

### 3️⃣ Info Gathering
- System detects needed API keys
- Fill required keys (🔴)
- Optional keys (⚪) can be skipped
- Click: **"Continue to Build →"** or **"⏭️ Skip & Build"**

### 4️⃣ Building
- Orchestrator builds deployment kit
- Watch progress animation
- Wait 2-5 minutes
- → Automatically moves to complete

### 5️⃣ Complete
- View deployment kit
- Download: MD, ZIP, or Text
- Save to local folder
- Click: **"🔄 Start New Project"** to reset

---

## 🔑 Required Agents

### Strategy Consultant Agent
```json
{
  "role": "Strategy Consultant Agent",
  "goal": "Analyze ideas and generate solution packages",
  "allow_delegation": false
}
```
**Use:** Phase 1 - Creates tech stack options

### Orchestrator Agent
```json
{
  "role": "Orchestrator Agent",
  "goal": "Lead team and build complete applications",
  "allow_delegation": true
}
```
**Use:** Phase 4 - Builds the actual code

---

## 📦 What You Get

### Complete Deployment Kit
- ✅ All source code (frontend + backend)
- ✅ Configuration files
- ✅ .gitignore
- ✅ README.md
- ✅ .env.example
- ✅ Step-by-step deployment guide
- ✅ API documentation
- ✅ Troubleshooting guide

### Download Options
- 📄 **Markdown** - Full guide with formatting
- 📦 **ZIP** - All code files ready to use
- 📝 **Text** - Plain text version
- 💾 **Local Folder** - Direct filesystem save

---

## 🎨 Phase Progress Indicator

```
✓ 💡 Idea  |  ✓ 🎯 Strategy  |  ▶ 🔐 Config  |  🚀 Building  |  ✅ Complete
```

- ✓ = Done
- ▶ = Current
- Plain = Upcoming

---

## 🔍 API Key Detection

### Automatically Detected:
| Tech Stack | Keys Detected |
|-----------|---------------|
| Netlify | Netlify API Token (⚪) |
| Vercel | Vercel Token (⚪) |
| Supabase | URL + Anon Key (🔴 required) |
| Firebase | Firebase Config (🔴 required) |
| OpenAI/GPT | OpenAI API Key (⚪) |
| Stripe | API Key + Webhook Secret (⚪) |
| All | GitHub Token (⚪) |

🔴 = Required  
⚪ = Optional

---

## 🔄 Navigation

### Forward
- **Phase 1 → 2**: Click "🎯 Plan Strategy"
- **Phase 2 → 3**: Click "Continue →"
- **Phase 3 → 4**: Click "Continue to Build →"
- **Phase 4 → 5**: Automatic after build
- **Phase 5 → 1**: Click "🔄 Start New Project"

### Backward
- **Phase 2 → 1**: Click "← Back to Idea"
- **Phase 3 → 2**: Click "← Back" (in form)
- **Phase 4 → 3**: Click "← Back to Config" (on error)

---

## 💡 Pro Tips

1. **Be Specific**: "Build a todo app with auth" is better than "Build an app"

2. **Choose Right Package**: Review all 3 options before selecting

3. **Skip API Keys**: It's okay to skip - you can add them during deployment

4. **Upload References**: Include mockups, existing code, or documentation

5. **Custom Solution**: Use if none of A/B/C match your needs

6. **Save Locally**: Use local folder save for immediate development

7. **Start Over Anytime**: "🔄 Start New Project" gives you a clean slate

---

## 🐛 Quick Troubleshooting

| Issue | Fix |
|-------|-----|
| Agent not found | Create agent with correct role name |
| No API keys detected | Use keywords in package selection |
| Build takes long | Normal! Wait 2-5 minutes |
| No files in ZIP | Check Orchestrator output format |
| Can't go back | Use in-phase buttons, not browser back |

---

## 📊 Session State (For Debugging)

```python
# Add to any phase to debug
st.write("Phase:", st.session_state.phase)
st.write("Idea:", st.session_state.project_idea[:50])
st.write("Strategy:", st.session_state.chosen_strategy)
st.write("API Keys:", len(st.session_state.get('api_keys', {})))
```

---

## ✅ Success Checklist

Before using:
- [ ] Created Strategy Consultant Agent
- [ ] Created Orchestrator Agent  
- [ ] Set OpenAI API key in secrets.toml
- [ ] Installed all requirements

During use:
- [ ] Entered detailed project idea
- [ ] Selected appropriate package
- [ ] Filled required API keys (if any)
- [ ] Waited for build to complete
- [ ] Downloaded deployment kit

---

## 🎯 Example Ideas to Try

### Simple
"Build a weather app that shows current conditions"

### Medium
"Build a blog with user authentication, comments, and markdown support"

### Complex
"Build a project management tool with teams, tasks, real-time updates, and analytics"

### With Stack
"Build a recipe sharing app using Next.js, Supabase, and Vercel"

---

## 📚 Full Documentation

- **COMPLETE_WORKFLOW_FINAL.md** - Complete guide
- **PHASES_2_3_IMPLEMENTATION.md** - Phase 2 & 3 details
- **STRATEGY_CONSULTANT_UPDATE.md** - Phase 1 details
- **QUICK_TEST_PHASES_2_3.md** - Testing guide

---

## 🚀 Ready to Build!

1. Start app: `streamlit run app.py`
2. Go to **Project Execution**
3. Follow the 5 phases
4. Download your deployment kit
5. Deploy and enjoy! 🎉

**Happy Building! 🏭✨**
