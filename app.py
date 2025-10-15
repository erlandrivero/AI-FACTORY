# app.py
# ──────────────────────────────────────────────────────────────────────────────
# AI Factory — Streamlit + CrewAI app (Full Dark Mode Redesign)
# Requirements:
#   - streamlit
#   - crewai
#   - crewai-tools
#   - openai
#
# SECURITY NOTE:
#   Your OpenAI API key must be provided via Streamlit secrets:
#   In .streamlit/secrets.toml set:
#       OPENAI_API_KEY = "sk-...."
#   We DO NOT hardcode any keys in this file.
# THEME NOTE:
#   Streamlit's official theming is handled via .streamlit/config.toml.
#   Here we emulate a full dark theme using CSS injection for an immediate result.
# ──────────────────────────────────────────────────────────────────────────────

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4

import streamlit as st
from crewai import Agent, Task, Crew, Process
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# ------------------------------------------------------------------------------
# App & Security Setup
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Factory",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ensure API key comes from Streamlit secrets; never hard-code.
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", "")
if not OPENAI_KEY:
    st.warning(
        "🔐 OpenAI API key not found in Streamlit secrets. "
        'Add it to `.streamlit/secrets.toml` as: OPENAI_API_KEY = "<your key>".'
    )
# CrewAI / OpenAI SDKs pick up the key from environment variables
os.environ["OPENAI_API_KEY"] = OPENAI_KEY

# MongoDB connection - get from Streamlit secrets or environment
MONGODB_URI = st.secrets.get("MONGODB_URI", os.getenv("MONGODB_URI", ""))
USE_MONGODB = bool(MONGODB_URI)

if not USE_MONGODB:
    st.info(
        "💡 **Tip:** Add MongoDB connection to persist agents across deployments. "
        'Add `MONGODB_URI = "your-connection-string"` to `.streamlit/secrets.toml`'
    )

# ------------------------------------------------------------------------------
# Dark Mode CSS Injection (palette, fonts, components)
# ------------------------------------------------------------------------------
DARK_CSS = """
<style>
/* Google Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

/* Color System */
:root {
  --bg: #1E1E1E;
  --surface: #2D2D2D;
  --surface-2: #242424;
  --border: #3A3A3A;
  --accent: #7C5CFF;      /* Vibrant purple accent */
  --accent-hover: #6B4CFA;
  --text: #EAEAEA;        /* Primary text */
  --text-muted: #BDBDBD;  /* Secondary text */
  --success: #22c55e;
  --error: #ef4444;
  --warning: #f59e0b;
}

/* Base App */
html, body, [data-testid="stAppViewContainer"], .stApp {
  background-color: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji" !important;
}

/* Header */
[data-testid="stHeader"] {
  background: linear-gradient(180deg, rgba(0,0,0,0.35), rgba(0,0,0,0)) !important;
  color: var(--text) !important;
  border-bottom: 1px solid var(--border) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
  background-color: var(--surface) !important;
  color: var(--text) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
  color: var(--text) !important;
}

/* Cards, containers, expanders */
.block-container, .stTabs, .stDataFrame, .stMarkdown, .stMetric {
  color: var(--text) !important;
}
div[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
}
div[data-testid="stExpander"] > details > summary {
  background: var(--surface-2) !important;
  border-bottom: 1px solid var(--border) !important;
  padding: 12px 14px !important;
  font-weight: 600 !important;
  color: var(--text) !important;
}
div[data-testid="stExpander"] p,
div[data-testid="stExpander"] .stMarkdown {
  color: var(--text) !important;
}

/* Inputs */
textarea, input[type="text"], input[type="search"], input[type="email"], input[type="password"] {
  background: var(--surface) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}
textarea::placeholder, input::placeholder {
  color: var(--text-muted) !important;
}

/* Selects and combos */
div[data-baseweb="select"] > div {
  background: var(--surface) !important;
  border-color: var(--border) !important;
  color: var(--text) !important;
  border-radius: 12px !important;
}
div[data-baseweb="select"] svg {
  fill: var(--text-muted) !important;
}
/* Dropdown menu options */
[data-baseweb="menu"],
[data-baseweb="popover"] {
  background: var(--surface) !important;
}
[role="option"] {
  background: var(--surface) !important;
  color: var(--text) !important;
}
[role="option"]:hover {
  background: var(--surface-2) !important;
}

/* Buttons */
.stButton > button, button[kind="secondary"] {
  background: var(--accent) !important;
  color: #ffffff !important;
  border: 1px solid transparent !important;
  padding: 0.6rem 1rem !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
  transition: all .15s ease-in-out;
}
.stButton > button:hover, button[kind="secondary"]:hover {
  background: var(--accent-hover) !important;
  transform: translateY(-1px);
}
.stButton > button:focus {
  outline: 2px solid var(--accent-hover) !important;
}

/* Primary and secondary base buttons (newer Streamlit) */
button[data-testid="baseButton-primary"],
button[kind="primary"],
.stForm button[type="submit"] {
  background: var(--accent) !important;
  color: #ffffff !important;
  border: 1px solid transparent !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
}
button[data-testid="baseButton-secondary"] {
  background: var(--surface-2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}
button[data-testid="baseButton-primary"]:hover,
button[kind="primary"]:hover,
.stForm button[type="submit"]:hover {
  background: var(--accent-hover) !important;
}

/* Form help icons and text */
.stCheckbox label span,
[data-testid="stCaptionContainer"],
.stCheckbox [data-testid="stMarkdownContainer"] {
  color: var(--text) !important;
}

/* Help icons - make them visible */
svg.info-icon,
.stCheckbox svg,
.stSelectbox svg[data-testid="stTooltipHoverTarget"],
.stTextInput svg[data-testid="stTooltipHoverTarget"],
.stTextArea svg[data-testid="stTooltipHoverTarget"],
[data-testid="stTooltipHoverTarget"] svg,
.st-emotion-cache-1gulkj5 svg {
  fill: var(--text) !important;
  color: var(--text) !important;
  opacity: 0.7 !important;
}

/* Help icon container */
[data-testid="stTooltipHoverTarget"] {
  color: var(--text) !important;
  opacity: 0.7 !important;
}

/* Ensure help icons are visible in all contexts */
.stSelectbox [data-testid="stTooltipHoverTarget"],
.stTextInput [data-testid="stTooltipHoverTarget"],
.stCheckbox [data-testid="stTooltipHoverTarget"] {
  display: inline-flex !important;
  visibility: visible !important;
}

/* Alerts and info boxes */
div[data-testid="stAlert"],
div[data-testid="stNotification"],
.stAlert {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  color: var(--text) !important;
}
div[data-testid="stAlert"] *,
div[data-testid="stNotification"] *,
.stAlert *,
div[data-testid="stAlert"] p,
div[data-testid="stAlert"] strong {
  color: var(--text) !important;
  background: transparent !important;
}

/* Code blocks & markdown text */
code, pre {
  background: var(--surface-2) !important;
  color: var(--text) !important;
  border-radius: 10px !important;
}

/* Spinners */
div[data-testid="stSpinner"] {
  background: var(--surface-2) !important;
  color: var(--text) !important;
  border-radius: 12px !important;
  padding: 0.75rem 1rem !important;
  border: 1px solid var(--border) !important;
}

/* Dividers, hr, borders */
hr, .stDivider {
  border-color: var(--border) !important;
}

/* Headings & text */
h1, h2, h3, h4, h5, h6, label, p, li, span {
  color: var(--text) !important;
}

/* Scrollbars (WebKit) */
*::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}
*::-webkit-scrollbar-track {
  background: var(--bg);
}
*::-webkit-scrollbar-thumb {
  background-color: var(--surface-2);
  border-radius: 10px;
  border: 2px solid var(--bg);
}

/* Text area sizing for nicer look */
textarea {
  line-height: 1.45 !important;
}

/* Hide the "Press Ctrl+Enter to apply" hint in text areas */
[data-testid="InputInstructions"],
.stTextArea [data-testid="stMarkdownContainer"] small,
.stTextArea small {
  display: none !important;
}

/* Fix tooltips and help text visibility */
[data-baseweb="tooltip"],
[role="tooltip"],
.stTooltipIcon,
[data-testid="stTooltipHoverTarget"] + div,
[data-baseweb="tooltip"] > div {
  background-color: var(--surface) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  padding: 8px 12px !important;
}

/* Ensure help icon and tooltip content are visible */
.stTooltipIcon svg,
[data-testid="stMarkdownContainer"] p,
[role="tooltip"] *,
[data-baseweb="tooltip"] *,
.stTextInput [data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] {
  color: var(--text) !important;
  background: transparent !important;
}

/* Help text under inputs */
[data-testid="stCaptionContainer"],
.stTextInput small,
.stTextArea small {
  color: var(--text-muted) !important;
  background: transparent !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: 1rem !important;
}
[data-testid="stFileUploader"] section {
  background: var(--surface-2) !important;
  border: 2px dashed var(--border) !important;
  border-radius: 10px !important;
}
[data-testid="stFileUploader"] section:hover {
  border-color: var(--accent) !important;
}
[data-testid="stFileUploader"] button {
  background: var(--accent) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
}
[data-testid="stFileUploader"] button:hover {
  background: var(--accent-hover) !important;
}
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] span {
  color: var(--text) !important;
}
/* Uploaded file list */
[data-testid="stFileUploader"] ul {
  background: var(--surface-2) !important;
  padding: 0.5rem !important;
  border-radius: 8px !important;
}
[data-testid="stFileUploader"] li {
  color: var(--text) !important;
  background: var(--surface) !important;
  padding: 0.5rem !important;
  margin: 0.25rem 0 !important;
  border-radius: 6px !important;
  border: 1px solid var(--border) !important;
}
[data-testid="stFileUploader"] li span,
[data-testid="stFileUploader"] li div {
  color: var(--text) !important;
}
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Constants & Storage Helpers
# ------------------------------------------------------------------------------
AGENTS_FILE = Path("agents.json")

# MongoDB setup
@st.cache_resource
def get_mongodb_client():
    """Get MongoDB client with connection pooling."""
    if not USE_MONGODB:
        return None
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        st.error(f"❌ MongoDB connection failed: {e}")
        return None
    except Exception as e:
        st.error(f"❌ MongoDB error: {e}")
        return None

def get_agents_collection():
    """Get the agents collection from MongoDB."""
    client = get_mongodb_client()
    if client is None:
        return None
    db = client.get_database("ai_factory")
    return db.get_collection("agents")

def migrate_json_to_mongodb() -> None:
    """Migrate agents from JSON file to MongoDB (one-time migration)."""
    if not USE_MONGODB:
        return
    
    collection = get_agents_collection()
    if collection is None:
        return
    
    # Check if migration already done
    if collection.count_documents({}) > 0:
        return  # Already have data in MongoDB
    
    # Check if JSON file exists with data
    if not AGENTS_FILE.exists():
        return
    
    try:
        data = json.loads(AGENTS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list) and len(data) > 0:
            # Insert all agents to MongoDB
            for agent in data:
                if "_id" in agent:
                    del agent["_id"]  # Remove _id if exists
            collection.insert_many(data)
            st.success(f"✅ Migrated {len(data)} agents from JSON to MongoDB")
    except Exception as e:
        st.warning(f"⚠️ Migration warning: {e}")

def load_agents() -> List[Dict[str, Any]]:
    """Load agent profiles from MongoDB or JSON fallback."""
    if USE_MONGODB:
        collection = get_agents_collection()
        if collection is not None:
            try:
                agents = list(collection.find({}))
                # Convert MongoDB _id to string id for consistency
                for agent in agents:
                    if "_id" in agent:
                        if "id" not in agent:
                            agent["id"] = str(agent["_id"])
                        del agent["_id"]
                return agents
            except Exception as e:
                st.error(f"❌ Error loading from MongoDB: {e}")
                return []
    
    # Fallback to JSON file
    if not AGENTS_FILE.exists():
        AGENTS_FILE.write_text(json.dumps([], indent=2), encoding="utf-8")
    try:
        data = json.loads(AGENTS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []

def save_agents(all_agents: List[Dict[str, Any]]) -> None:
    """Persist the full agent list to MongoDB or JSON."""
    if USE_MONGODB:
        collection = get_agents_collection()
        if collection is not None:
            try:
                # Clear and reinsert all
                collection.delete_many({})
                if all_agents:
                    # Remove _id fields before insert
                    for agent in all_agents:
                        if "_id" in agent:
                            del agent["_id"]
                    collection.insert_many(all_agents)
                return
            except Exception as e:
                st.error(f"❌ Error saving to MongoDB: {e}")
    
    # Fallback to JSON
    AGENTS_FILE.write_text(json.dumps(all_agents, indent=2), encoding="utf-8")

def add_agent(role: str, goal: str, backstory: str, allow_delegation: bool) -> Dict[str, Any]:
    """Append a new agent to storage and return it."""
    agent = {
        "id": str(uuid4()),
        "role": role.strip(),
        "goal": goal.strip(),
        "backstory": backstory.strip(),
        "allow_delegation": bool(allow_delegation),
    }
    
    if USE_MONGODB:
        collection = get_agents_collection()
        if collection is not None:
            try:
                collection.insert_one(agent.copy())
                return agent
            except Exception as e:
                st.error(f"❌ Error adding agent to MongoDB: {e}")
    
    # Fallback to JSON
    all_agents = load_agents()
    all_agents.append(agent)
    save_agents(all_agents)
    return agent

def delete_agent(agent_id: str) -> None:
    """Delete an agent by id."""
    if USE_MONGODB:
        collection = get_agents_collection()
        if collection is not None:
            try:
                collection.delete_one({"id": agent_id})
                return
            except Exception as e:
                st.error(f"❌ Error deleting agent from MongoDB: {e}")
    
    # Fallback to JSON
    all_agents = load_agents()
    filtered = [a for a in all_agents if a.get("id") != agent_id]
    save_agents(filtered)

# Run migration on app start
if USE_MONGODB:
    migrate_json_to_mongodb()

def find_orchestrator(agents: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    """Find the orchestrator agent (by role containing 'orchestrator')."""
    for a in agents:
        if "orchestrator" in a.get("role", "").lower():
            return a
    return None

def format_time(seconds: int) -> str:
    """Format seconds into a human-readable time string."""
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds == 0:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        return f"{minutes} minute{'s' if minutes != 1 else ''} {remaining_seconds} second{'s' if remaining_seconds != 1 else ''}"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"

def parse_uploaded_file(uploaded_file) -> Dict[str, Any]:
    """Parse uploaded file and extract content."""
    file_name = uploaded_file.name
    file_type = file_name.split('.')[-1].lower()
    
    try:
        if file_type == 'ipynb':
            # Parse Jupyter notebook
            content = json.loads(uploaded_file.read().decode('utf-8'))
            cells = content.get('cells', [])
            text_content = []
            for cell in cells:
                cell_type = cell.get('cell_type', '')
                source = ''.join(cell.get('source', []))
                if cell_type == 'markdown':
                    text_content.append(f"### Markdown Cell\n{source}\n")
                elif cell_type == 'code':
                    text_content.append(f"### Code Cell\n```python\n{source}\n```\n")
            return {
                'name': file_name,
                'type': 'Jupyter Notebook',
                'content': '\n'.join(text_content),
                'icon': '📓'
            }
        
        elif file_type in ['md', 'markdown']:
            content = uploaded_file.read().decode('utf-8')
            return {
                'name': file_name,
                'type': 'Markdown',
                'content': content,
                'icon': '📝'
            }
        
        elif file_type == 'csv':
            content = uploaded_file.read().decode('utf-8')
            lines = content.split('\n')[:20]  # Preview first 20 lines
            preview = '\n'.join(lines)
            return {
                'name': file_name,
                'type': 'CSV Data',
                'content': f"CSV File Preview (first 20 rows):\n```\n{preview}\n```\n\nNote: Full dataset available for analysis.",
                'icon': '📊'
            }
        
        elif file_type == 'txt':
            content = uploaded_file.read().decode('utf-8')
            return {
                'name': file_name,
                'type': 'Text File',
                'content': content,
                'icon': '📄'
            }
        
        elif file_type == 'py':
            content = uploaded_file.read().decode('utf-8')
            return {
                'name': file_name,
                'type': 'Python Code',
                'content': f"```python\n{content}\n```",
                'icon': '🐍'
            }
        
        elif file_type == 'json':
            content = json.loads(uploaded_file.read().decode('utf-8'))
            formatted = json.dumps(content, indent=2)
            return {
                'name': file_name,
                'type': 'JSON Data',
                'content': f"```json\n{formatted}\n```",
                'icon': '📋'
            }
        
        else:
            # Try to read as text
            content = uploaded_file.read().decode('utf-8', errors='ignore')
            return {
                'name': file_name,
                'type': 'File',
                'content': content[:5000],  # Limit to 5000 chars
                'icon': '📎'
            }
    
    except Exception as e:
        return {
            'name': file_name,
            'type': 'Error',
            'content': f"Could not parse file: {str(e)}",
            'icon': '⚠️'
        }

def build_context_from_files(files_data: List[Dict[str, Any]]) -> str:
    """Build context string from uploaded files."""
    if not files_data:
        return ""
    
    context_parts = ["\n\n---\n## 📚 Background Materials & Reference Documents\n"]
    context_parts.append("The following files have been provided as background knowledge for this project:\n")
    
    for idx, file_data in enumerate(files_data, 1):
        context_parts.append(f"\n### {file_data['icon']} File {idx}: {file_data['name']} ({file_data['type']})\n")
        context_parts.append(file_data['content'])
        context_parts.append("\n---\n")
    
    return ''.join(context_parts)

# ------------------------------------------------------------------------------
# Deployment Helper Functions
# ------------------------------------------------------------------------------

def detect_required_secrets(text: str) -> List[str]:
    """Detect environment variables used in code."""
    import re
    secrets = set()
    
    # Patterns to detect env var usage
    patterns = [
        r'os\.getenv\(["\']([^"\']+)["\']\)',
        r'os\.environ\[["\']([^"\']+)["\']\]',
        r'st\.secrets\[["\']([^"\']+)["\']\]',
        r'st\.secrets\.get\(["\']([^"\']+)["\']\)',
        r'process\.env\.([A-Z_]+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        secrets.update(matches)
    
    return sorted(list(secrets))

def get_secret_description(key: str) -> str:
    """Get helpful description for common API keys."""
    descriptions = {
        "OPENAI_API_KEY": "OpenAI API key (get from platform.openai.com/api-keys)",
        "ANTHROPIC_API_KEY": "Anthropic Claude API key (get from console.anthropic.com)",
        "DATABASE_URL": "PostgreSQL connection string (e.g., postgresql://user:pass@host:5432/db)",
        "REDIS_URL": "Redis connection string (e.g., redis://localhost:6379)",
        "SECRET_KEY": "Random secret key for session security (generate with: openssl rand -hex 32)",
        "API_KEY": "Generic API key - check your project requirements",
        "SUPABASE_URL": "Your Supabase project URL",
        "SUPABASE_KEY": "Your Supabase anon/public key",
        "STRIPE_API_KEY": "Stripe API key (get from dashboard.stripe.com)",
        "GOOGLE_API_KEY": "Google Cloud API key",
    }
    return descriptions.get(key, f"Environment variable: {key}")

def analyze_project_type(text: str) -> Dict[str, Any]:
    """Analyze the project and recommend deployment platform."""
    text_lower = text.lower()
    
    # Detect technologies
    tech_stack = {
        "streamlit": "streamlit" in text_lower or "st." in text,
        "react": "react" in text_lower or "jsx" in text_lower or "npm" in text_lower,
        "next": "next" in text_lower or "nextjs" in text_lower,
        "vue": "vue" in text_lower,
        "python": "python" in text_lower or "def " in text or "import " in text,
        "node": "node" in text_lower or "express" in text_lower,
        "static": any(ext in text_lower for ext in [".html", ".css", ".js"]) and "server" not in text_lower,
        "database": any(db in text_lower for db in ["postgres", "mysql", "mongodb", "redis", "database"]),
        "ml": any(term in text_lower for term in ["tensorflow", "pytorch", "scikit", "machine learning", "model"]),
    }
    
    # Determine app category
    if tech_stack["streamlit"]:
        category = "streamlit_app"
    elif tech_stack["static"] and not tech_stack["database"]:
        category = "static_site"
    elif tech_stack["next"]:
        category = "nextjs_app"
    elif tech_stack["react"] and not tech_stack["next"]:
        category = "react_app"
    elif tech_stack["python"] and tech_stack["database"]:
        category = "python_backend"
    elif tech_stack["node"] and tech_stack["database"]:
        category = "node_backend"
    else:
        category = "general_app"
    
    # Platform recommendations with cost and features
    platforms = {
        "streamlit_app": [
            {
                "name": "Streamlit Cloud",
                "cost": "Free",
                "tier_details": "1 app free, $20/month for unlimited",
                "pros": ["Native Streamlit support", "Easy secrets management", "Auto-deploy from GitHub"],
                "cons": ["Python only", "Limited compute resources on free tier"],
                "best_for": "Data apps, ML demos, internal dashboards",
                "difficulty": "Easy ⭐",
            },
            {
                "name": "Railway",
                "cost": "$5/month minimum",
                "tier_details": "$5 free credit monthly, pay-as-you-go after",
                "pros": ["More compute power", "Database included", "Custom domains"],
                "cons": ["Costs more", "Requires Dockerfile"],
                "best_for": "Production apps with databases",
                "difficulty": "Medium ⭐⭐",
            },
        ],
        "static_site": [
            {
                "name": "Netlify",
                "cost": "Free",
                "tier_details": "100GB bandwidth/month, $19/month for more",
                "pros": ["Instant deploys", "CDN", "Forms & serverless functions"],
                "cons": ["No backend support"],
                "best_for": "Landing pages, portfolios, docs sites",
                "difficulty": "Easy ⭐",
            },
            {
                "name": "Vercel",
                "cost": "Free",
                "tier_details": "Unlimited personal projects, $20/month for teams",
                "pros": ["Great DX", "Edge network", "Serverless functions"],
                "cons": ["No backend support"],
                "best_for": "Modern web apps, fast static sites",
                "difficulty": "Easy ⭐",
            },
        ],
        "nextjs_app": [
            {
                "name": "Vercel",
                "cost": "Free",
                "tier_details": "Unlimited personal projects, $20/month for teams",
                "pros": ["Made by Next.js creators", "Optimal performance", "Edge functions"],
                "cons": ["Vendor lock-in for some features"],
                "best_for": "Next.js apps (obviously!)",
                "difficulty": "Easy ⭐",
            },
            {
                "name": "Netlify",
                "cost": "Free",
                "tier_details": "100GB bandwidth/month",
                "pros": ["Good Next.js support", "Flexible"],
                "cons": ["Slightly slower than Vercel"],
                "best_for": "Next.js apps without Vercel lock-in",
                "difficulty": "Easy ⭐",
            },
        ],
        "react_app": [
            {
                "name": "Vercel",
                "cost": "Free",
                "tier_details": "Unlimited personal projects",
                "pros": ["Fast deploys", "Preview URLs", "Analytics"],
                "cons": ["Backend requires serverless functions"],
                "best_for": "React SPAs, frontend apps",
                "difficulty": "Easy ⭐",
            },
            {
                "name": "Netlify",
                "cost": "Free",
                "tier_details": "100GB bandwidth/month",
                "pros": ["Great CI/CD", "Form handling", "Split testing"],
                "cons": ["None really"],
                "best_for": "React apps with forms",
                "difficulty": "Easy ⭐",
            },
        ],
        "python_backend": [
            {
                "name": "Railway",
                "cost": "$5/month minimum",
                "tier_details": "$5 free credit monthly",
                "pros": ["Includes Postgres", "Easy deploys", "Great DX"],
                "cons": ["Costs money", "US/EU only"],
                "best_for": "Full-stack Python apps",
                "difficulty": "Medium ⭐⭐",
            },
            {
                "name": "Render",
                "cost": "Free",
                "tier_details": "Free tier available, $7/month for production",
                "pros": ["Free tier", "Database included", "Good docs"],
                "cons": ["Free tier sleeps after inactivity"],
                "best_for": "Python APIs, full-stack apps",
                "difficulty": "Medium ⭐⭐",
            },
        ],
        "node_backend": [
            {
                "name": "Railway",
                "cost": "$5/month minimum",
                "tier_details": "$5 free credit monthly",
                "pros": ["Easy Node.js deploys", "Database support", "Docker support"],
                "cons": ["Costs money"],
                "best_for": "Express, Fastify, NestJS apps",
                "difficulty": "Medium ⭐⭐",
            },
            {
                "name": "Render",
                "cost": "Free",
                "tier_details": "Free tier available, $7/month for production",
                "pros": ["Free tier", "Auto-deploy from GitHub"],
                "cons": ["Free tier sleeps"],
                "best_for": "Node.js APIs",
                "difficulty": "Medium ⭐⭐",
            },
        ],
        "general_app": [
            {
                "name": "Railway",
                "cost": "$5/month minimum",
                "tier_details": "$5 free credit monthly",
                "pros": ["Supports any language", "Flexible", "Database options"],
                "cons": ["Costs money", "Requires more setup"],
                "best_for": "Any application type",
                "difficulty": "Medium ⭐⭐",
            },
            {
                "name": "Render",
                "cost": "Free",
                "tier_details": "Free tier available",
                "pros": ["Free tier", "Multiple languages", "Docker support"],
                "cons": ["Free tier limitations"],
                "best_for": "General web apps",
                "difficulty": "Medium ⭐⭐",
            },
        ],
    }
    
    return {
        "category": category,
        "tech_stack": tech_stack,
        "platforms": platforms.get(category, platforms["general_app"]),
    }

# ------------------------------------------------------------------------------
# UI — Sidebar Navigation
# ------------------------------------------------------------------------------
st.sidebar.title("🏭 AI Factory")
page = st.sidebar.radio(
    "Navigate",
    options=["Project Execution", "Agent Management"],
    index=0,
    help="Switch between running a project and managing your agents.",
)

with st.sidebar.expander("ℹ️ Help", expanded=False):
    st.markdown(
        """
**How it works**

- Create agents in **Agent Management** (add role, goal, backstory, delegation).
- Be sure to create **one 'Orchestrator Agent'** to lead projects.
- Go to **Project Execution**, describe your project idea, and click **Launch Crew**.

**Security**: Your OpenAI key is read from Streamlit secrets (never stored in code).
"""
    )

# ------------------------------------------------------------------------------
# PAGE: Agent Management
# ------------------------------------------------------------------------------
def agent_management_page():
    st.header("🧠 Agent Management")
    st.write(
        "Create, view, and delete agents. Add **one Orchestrator Agent** to lead projects."
    )

    st.subheader("➕ Create a New Agent")
    with st.form("create_agent_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            role = st.text_input("Role*", placeholder="e.g., Orchestrator Agent")
            allow_delegation = st.checkbox(
                "Allow Delegation",
                value=False,
                help="✨ If enabled, the agent can delegate work to others. Recommended for Orchestrator agents."
            )
        with col2:
            goal = st.text_input("Goal*", placeholder="e.g., Coordinate and deliver projects end-to-end")

        backstory = st.text_area(
            "Backstory*",
            placeholder="Brief background/personality to guide how this agent behaves."
        )

        submitted = st.form_submit_button("💾 Save Agent", use_container_width=True, type="primary")
        if submitted:
            if not role.strip() or not goal.strip() or not backstory.strip():
                st.error("Please fill in Role, Goal, and Backstory.")
            else:
                agent = add_agent(role, goal, backstory, allow_delegation)
                st.success(f"Agent '{agent['role']}' saved.")

    st.subheader("📒 Current Agents")
    agents = load_agents()
    if not agents:
        st.info("No agents saved yet. Use the form above to add your first agent.")
        return

    # Collapsible display of agents with clear bold labels
    for a in agents:
        with st.expander(f"🧩 {a.get('role', 'Unknown Role')}", expanded=False):
            st.markdown(f"**Goal:** {a.get('goal','')}")
            st.markdown(f"**Backstory:** {a.get('backstory','')}")
            st.markdown(f"**Allow Delegation:** {'Yes' if a.get('allow_delegation') else 'No'}")
            cols = st.columns(2)
            with cols[0]:
                if st.button("🗑️ Delete", key=f"del_{a['id']}"):
                    delete_agent(a["id"])
                    st.rerun()

# ------------------------------------------------------------------------------
# Helper: Instantiate CrewAI Agents from stored profiles
# ------------------------------------------------------------------------------
def build_crewai_agent(profile: Dict[str, Any]) -> Agent:
    """
    Build a CrewAI Agent from a stored profile.

    We pass `allow_delegation` through and specify a model name.
    CrewAI will read the OpenAI key from the environment.
    """
    default_model = "gpt-4o-mini"

    return Agent(
        role=profile.get("role", "Agent"),
        goal=profile.get("goal", ""),
        backstory=profile.get("backstory", ""),
        allow_delegation=bool(profile.get("allow_delegation", True)),
        model=default_model,
        verbose=True,
    )

# ------------------------------------------------------------------------------
# PAGE: Project Execution
# ------------------------------------------------------------------------------
def project_execution_page():
    st.header("🚀 Project Execution")
    st.write("Describe your project idea and launch your crew.")

    # Initialize session state for results
    if 'execution_result' not in st.session_state:
        st.session_state.execution_result = None
    if 'execution_metadata' not in st.session_state:
        st.session_state.execution_metadata = {}

    idea = st.text_area(
        "Project Idea",
        height=220,
        placeholder=(
            "Describe what you want to build or accomplish. "
            "The Orchestrator will break it down, plan, and delegate tasks to other agents."
        ),
        help="Type or paste your project idea here, then click the Launch button below.",
        key="project_idea_input",
    )
    
    # File upload section
    st.subheader("📚 Background Materials (Optional)")
    st.caption("Upload reference files for agents to review (notebooks, docs, datasets, code, etc.)")
    
    uploaded_files = st.file_uploader(
        "Upload files",
        type=['ipynb', 'md', 'markdown', 'csv', 'txt', 'py', 'json'],
        accept_multiple_files=True,
        help="Upload Jupyter notebooks, markdown files, datasets, or code for context",
        label_visibility="collapsed"
    )
    
    # Parse and display uploaded files
    files_data = []
    if uploaded_files:
        st.write(f"**{len(uploaded_files)} file(s) uploaded:**")
        cols = st.columns(min(len(uploaded_files), 3))
        for idx, uploaded_file in enumerate(uploaded_files):
            parsed = parse_uploaded_file(uploaded_file)
            files_data.append(parsed)
            with cols[idx % 3]:
                st.info(f"{parsed['icon']} **{parsed['name']}**\n\n{parsed['type']}")
    
    # Launch button right below the file upload for better UX
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        launch = st.button(
            "🚀 Launch Crew",
            type="primary",
            use_container_width=True,
            disabled=not bool(idea.strip()),
            help="Click to start the crew with your project idea" if idea.strip() else "Enter a project idea to enable"
        )
    
    # Clear results button
    if st.session_state.execution_result is not None:
        with col3:
            if st.button("🗑️ Clear Results", help="Clear previous execution results"):
                st.session_state.execution_result = None
                st.session_state.execution_metadata = {}
                st.rerun()

    st.divider()

    # Two neat side-by-side columns: Agents Loaded (left) and Settings (right)
    colL, colR = st.columns([1, 1], gap="large")
    with colL:
        st.subheader("👥 Agents Loaded")
        agents = load_agents()
        if agents:
            for a in agents:
                st.write(f"- **{a.get('role','(no role)')}** — "
                         f"{'delegates' if a.get('allow_delegation') else 'individual contributor'}")
        else:
            st.info("No agents found. Create agents first in **Agent Management**.")

    with colR:
        st.subheader("🎛️ Settings")
        process_type = st.selectbox(
            "Process Type",
            options=["Hierarchical", "Sequential", "Consensus"],
            index=0,
            help="Choose how agents work together on your project."
        )
        
        # Show description based on selected process
        process_descriptions = {
            "Hierarchical": "🎯 **Manager-Led**: Orchestrator acts as a manager, delegating tasks to specialized agents.",
            "Sequential": "📝 **Step-by-Step**: Tasks execute one after another in order. Each agent completes their work before the next begins.",
            "Consensus": "🤝 **Collaborative**: Agents work together and reach consensus on the best approach."
        }
        st.info(process_descriptions[process_type])
    if launch:
        if not OPENAI_KEY:
            st.error("OpenAI API key missing. Add it to `.streamlit/secrets.toml` and reload the app.")
            return

        saved_agents = load_agents()
        if not saved_agents:
            st.error("No agents are configured. Please add agents in **Agent Management**.")
            return

        # Convert profiles to CrewAI Agent instances
        try:
            crew_agents: List[Agent] = [build_crewai_agent(p) for p in saved_agents]
        except Exception as e:
            st.error(f"Failed to initialize agents: {e}")
            return

        # Build tasks and crew based on selected process type
        tasks = []
        crew_process = None
        manager_agent = None
        
        if process_type == "Hierarchical":
            # Hierarchical requires an orchestrator
            orchestrator_profile = find_orchestrator(saved_agents)
            if not orchestrator_profile:
                st.error("Hierarchical mode requires an Orchestrator Agent. Create an agent with 'Orchestrator' in the role name.")
                return
            
            # Build context from uploaded files
            file_context = build_context_from_files(files_data)
            
            # Single high-level task for orchestrator
            task_description = (
                "You are the Orchestrator for this project. Analyze the user's idea, "
                "develop a clear execution plan, break it into tasks, and coordinate the work. "
                "Delegate to other available agents as needed. "
                "Deliver a final, cohesive result, including the plan, key decisions, artifacts, and next steps.\n\n"
                f"User's idea:\n{idea.strip()}"
                f"{file_context}"
            )
            tasks.append(Task(
                description=task_description,
                expected_output=(
                    "A comprehensive final deliverable that includes: "
                    "(1) a concise project summary, "
                    "(2) a prioritized plan with milestones, "
                    "(3) delegated tasks and outcomes, "
                    "(4) final recommendations or artifacts, and "
                    "(5) clear next steps."
                ),
                agent=build_crewai_agent(orchestrator_profile),
            ))
            crew_process = Process.hierarchical
            manager_agent = build_crewai_agent(orchestrator_profile)
            
        elif process_type == "Sequential":
            # Build context from uploaded files
            file_context = build_context_from_files(files_data)
            
            # Sequential: Create a task for each agent in order
            crew_process = Process.sequential
            for agent_profile in saved_agents:
                task_desc = (
                    f"As the {agent_profile.get('role', 'Agent')}, analyze the user's project idea and contribute your specialized expertise. "
                    f"Build upon previous work if available.\n\n"
                    f"Project idea: {idea.strip()}\n\n"
                    f"Your goal: {agent_profile.get('goal', 'Contribute to the project')}"
                    f"{file_context}"
                )
                tasks.append(Task(
                    description=task_desc,
                    expected_output=f"Detailed analysis and contribution from the {agent_profile.get('role', 'Agent')} perspective.",
                    agent=build_crewai_agent(agent_profile),
                ))
                
        else:  # Consensus
            # Build context from uploaded files
            file_context = build_context_from_files(files_data)
            
            # Consensus: Each agent contributes to collaborative solution
            crew_process = Process.sequential
            for agent_profile in saved_agents:
                task_desc = (
                    f"As the {agent_profile.get('role', 'Agent')}, collaborate on the user's project idea. "
                    f"Review previous contributions and add your unique perspective. "
                    f"Work toward a consensus solution that incorporates all viewpoints.\n\n"
                    f"Project idea: {idea.strip()}\n\n"
                    f"Your goal: {agent_profile.get('goal', 'Contribute collaboratively')}"
                    f"{file_context}"
                )
                tasks.append(Task(
                    description=task_desc,
                    expected_output=f"Collaborative contribution from {agent_profile.get('role', 'Agent')} that builds consensus.",
                    agent=build_crewai_agent(agent_profile),
                ))

        # Create the crew with appropriate configuration
        crew_config = {
            "agents": crew_agents,
            "tasks": tasks,
            "process": crew_process,
        }
        
        # Add manager only for hierarchical
        if manager_agent:
            crew_config["manager_agent"] = manager_agent
            
        crew = Crew(**crew_config)

        # Run with animated progress and live time tracking
        start_time = time.time()
        
        # Create placeholders for dynamic updates
        progress_container = st.container()
        with progress_container:
            st.markdown("### 🚀 Crew Execution in Progress")
            progress_bar = st.progress(0, text="Initializing crew...")
            status_text = st.empty()
            time_display = st.empty()
        
        # Status messages for animation
        status_messages = [
            "🔍 Orchestrator analyzing project requirements...",
            "📋 Breaking down project into manageable tasks...",
            "🤝 Delegating work to specialized agents...",
            "⚙️ Agents processing their assignments...",
            "🔄 Coordinating agent outputs...",
            "✨ Synthesizing final deliverable...",
        ]
        
        # Start the crew execution and show animated progress
        try:
            import threading
            result_container = {"result": None, "error": None, "completed": False}
            
            # Run crew in separate thread to allow UI updates
            def run_crew():
                try:
                    result_container["result"] = crew.kickoff()
                except Exception as e:
                    result_container["error"] = e
                finally:
                    result_container["completed"] = True
            
            thread = threading.Thread(target=run_crew)
            thread.start()
            
            # Animate progress while crew is working
            progress = 0
            msg_index = 0
            while not result_container["completed"]:
                elapsed = int(time.time() - start_time)
                
                # Update progress bar (smoothly increase)
                progress = min(90, progress + 2)  # Cap at 90% until complete
                progress_bar.progress(progress, text=status_messages[msg_index % len(status_messages)])
                
                # Update status and time
                status_text.info(f"⏱️ **Elapsed Time:** {format_time(elapsed)}")
                
                # Rotate through messages
                if elapsed % 3 == 0 and elapsed > 0:
                    msg_index += 1
                
                time.sleep(0.5)
            
            thread.join()
            
            # Check for errors
            if result_container["error"]:
                progress_container.empty()
                st.error(f"❌ Crew execution failed: {result_container['error']}")
                return
            
            result = result_container["result"]
            
            # Complete progress
            progress_bar.progress(100, text="✅ Complete!")
            elapsed_time = int(time.time() - start_time)
            time_display.success(f"🎉 **Completed in {format_time(elapsed_time)}!**")
            time.sleep(1.5)
            progress_container.empty()
            
            # Store results in session state
            st.session_state.execution_result = result
            st.session_state.execution_metadata = {
                'elapsed_time': elapsed_time,
                'process_type': process_type,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'idea': idea.strip(),
                'num_files': len(files_data)
            }
            
        except Exception as e:
            progress_container.empty()
            st.error(f"❌ Crew execution failed: {e}")
            return
    
    # Display results (either from current execution or previous session state)
    if st.session_state.execution_result is not None:
        result = st.session_state.execution_result
        metadata = st.session_state.execution_metadata
        
        # Show execution info
        st.divider()
        info_cols = st.columns(4)
        with info_cols[0]:
            st.metric("⏱️ Duration", format_time(metadata.get('elapsed_time', 0)))
        with info_cols[1]:
            st.metric("🎯 Process", metadata.get('process_type', 'N/A'))
        with info_cols[2]:
            st.metric("📅 Executed", metadata.get('timestamp', 'N/A'))
        with info_cols[3]:
            st.metric("📁 Files Used", metadata.get('num_files', 0))
        
        st.subheader("📄 Final Report")
        
        # Debug: Show result type
        with st.expander("🔍 Debug Info", expanded=False):
            st.write(f"**Result Type:** {type(result)}")
            st.write(f"**Result Attributes:** {dir(result) if not isinstance(result, str) else 'N/A'}")
        
        # Handle different result types from CrewAI
        if isinstance(result, str):
            # Simple string result
            st.markdown(result)
            main_output = result
        else:
            # CrewOutput object (newer CrewAI versions)
            # Try to get the main output in order of preference
            main_output = None
            
            # Try different attributes to extract content
            if hasattr(result, 'raw'):
                main_output = str(result.raw) if result.raw else None
            
            if not main_output and hasattr(result, 'output'):
                main_output = str(result.output) if result.output else None
            
            if not main_output and hasattr(result, 'json'):
                try:
                    main_output = str(result.json) if result.json else None
                except:
                    pass
            
            if not main_output and hasattr(result, 'pydantic'):
                try:
                    main_output = str(result.pydantic) if result.pydantic else None
                except:
                    pass
            
            # Last resort: convert entire result to string
            if not main_output:
                main_output = str(result)
            
        # Display the main output prominently
        if main_output and len(str(main_output).strip()) > 50:
            st.markdown(main_output)
            
            # Add export button with full content
            report_text = str(main_output)
            
            # Create downloadable versions
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    label="📥 Download Report (Markdown)",
                    data=report_text,
                    file_name=f"ai_factory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with col_dl2:
                st.download_button(
                    label="📄 Download Report (Text)",
                    data=report_text,
                    file_name=f"ai_factory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
        else:
            # If main output is short/empty, check task outputs
            if not isinstance(result, str) and hasattr(result, 'tasks_output') and result.tasks_output:
                for idx, task_output in enumerate(result.tasks_output, 1):
                    st.markdown(f"### 📋 Task {idx} Output")
                    # Try multiple attributes for actual output
                    task_result = None
                    if hasattr(task_output, 'raw') and task_output.raw:
                        task_result = task_output.raw
                    elif hasattr(task_output, 'output') and task_output.output:
                        task_result = task_output.output
                    elif hasattr(task_output, 'result') and task_output.result:
                        task_result = task_output.result
                    
                    if task_result:
                        st.markdown(task_result)
                    else:
                        st.info("No detailed output captured for this task.")
                    
                    if idx < len(result.tasks_output):
                        st.divider()
                
                # Add download button for combined task outputs
                combined_output = "\n\n---\n\n".join([
                    f"## Task {i+1} Output\n\n{getattr(t, 'raw', getattr(t, 'output', str(t)))}"
                    for i, t in enumerate(result.tasks_output)
                ])
                st.download_button(
                    label="📥 Download All Task Outputs (Markdown)",
                    data=combined_output,
                    file_name=f"ai_factory_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            else:
                # Ultimate fallback
                result_text = str(result)
                st.markdown(result_text)
                st.download_button(
                    label="📥 Download Report",
                    data=result_text,
                    file_name=f"ai_factory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
        
        # ------------------------------------------------------------------------------
        # Deployment Section
        # ------------------------------------------------------------------------------
        st.divider()
        st.header("🚀 Deploy Your App")
        
        # Get the full result text
        if isinstance(result, str):
            result_text = result
        else:
            result_text = str(main_output) if main_output else str(result)
        
        # Analyze project and detect secrets
        project_analysis = analyze_project_type(result_text)
        detected_secrets = detect_required_secrets(result_text)
        
        # Show project analysis
        with st.expander("📊 Project Analysis", expanded=True):
            tech_cols = st.columns(4)
            detected_techs = [k.title() for k, v in project_analysis["tech_stack"].items() if v]
            
            if detected_techs:
                tech_cols[0].metric("Technologies Detected", len(detected_techs))
                tech_cols[1].info("**Stack:** " + ", ".join(detected_techs[:3]))
            else:
                tech_cols[0].info("General application detected")
            
            if detected_secrets:
                tech_cols[2].metric("API Keys Needed", len(detected_secrets))
                tech_cols[3].warning("⚠️ Requires configuration")
            else:
                tech_cols[2].success("✅ No API keys needed")
        
        # Platform Recommendations
        st.subheader("💡 Recommended Platforms")
        st.caption("Based on your project's technology stack and requirements")
        
        # Display platform options in cards
        for idx, platform in enumerate(project_analysis["platforms"]):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"### {platform['name']}")
                    st.caption(f"**Best for:** {platform['best_for']}")
                    
                    # Pros and cons
                    pros_cons = st.columns(2)
                    with pros_cons[0]:
                        st.markdown("**✅ Pros:**")
                        for pro in platform["pros"][:2]:  # Show first 2
                            st.markdown(f"• {pro}")
                    with pros_cons[1]:
                        st.markdown("**⚠️ Cons:**")
                        for con in platform["cons"][:2]:  # Show first 2
                            st.markdown(f"• {con}")
                
                with col2:
                    st.metric("Cost", platform["cost"])
                    st.caption(platform["tier_details"])
                
                with col3:
                    st.metric("Difficulty", platform["difficulty"])
                    if idx == 0:
                        st.success("Recommended")
                
                st.divider()
        
        # Environment Variables Section
        if detected_secrets:
            st.subheader("🔐 Required Environment Variables")
            st.warning(f"This app requires **{len(detected_secrets)} environment variable(s)** to function.")
            
            with st.expander("💡 Why do I need these?", expanded=False):
                st.info(
                    "Environment variables store sensitive information like API keys securely. "
                    "They keep your secrets out of code and allow different values for development vs production."
                )
            
            # Collect secrets from user
            st.markdown("#### Enter Your API Keys")
            st.caption("These will be used to generate deployment configuration files. Never share these publicly!")
            
            user_secrets = {}
            for secret in detected_secrets:
                col1, col2 = st.columns([3, 1])
                with col1:
                    user_secrets[secret] = st.text_input(
                        f"🔑 {secret}",
                        type="password",
                        help=get_secret_description(secret),
                        key=f"secret_{secret}",
                    )
                with col2:
                    st.caption("")  # Spacing
                    st.caption("")  # Spacing
                    if user_secrets[secret]:
                        st.success("✓")
                    else:
                        st.error("Required")
            
            # Secret validation
            all_secrets_provided = all(user_secrets.values())
            
            if not all_secrets_provided:
                st.info("💡 **Tip:** You can deploy without entering keys now, but you'll need to add them to your deployment platform later.")
        else:
            st.success("✅ No API keys or environment variables detected in your app!")
            user_secrets = {}
            all_secrets_provided = True
        
        # Deployment Instructions
        st.subheader("📋 Deployment Instructions")
        
        # Platform selection
        selected_platform = st.selectbox(
            "Choose your deployment platform:",
            options=[p["name"] for p in project_analysis["platforms"]],
            help="Select where you want to deploy your app"
        )
        
        # Find selected platform details
        platform_details = next(
            (p for p in project_analysis["platforms"] if p["name"] == selected_platform),
            project_analysis["platforms"][0]
        )
        
        # Generate deployment guide
        with st.expander(f"📖 How to Deploy to {selected_platform}", expanded=True):
            st.markdown(f"**Cost:** {platform_details['cost']} - {platform_details['tier_details']}")
            st.markdown(f"**Difficulty:** {platform_details['difficulty']}")
            
            st.markdown("---")
            
            # Platform-specific instructions
            if "Streamlit" in selected_platform:
                st.markdown("""
                ### Step 1: Push to GitHub
                1. Create a new repository on GitHub
                2. Save all generated code files to your project folder
                3. Create `requirements.txt` with dependencies
                4. Push to GitHub:
                ```bash
                git init
                git add .
                git commit -m "Initial commit"
                git branch -M main
                git remote add origin <your-repo-url>
                git push -u origin main
                ```
                
                ### Step 2: Deploy on Streamlit Cloud
                1. Go to [share.streamlit.io](https://share.streamlit.io)
                2. Click "New app"
                3. Select your repository
                4. Set main file path (e.g., `app.py`)
                5. Click "Advanced settings"
                """)
                
                if detected_secrets and user_secrets:
                    st.markdown("### Step 3: Add Secrets")
                    st.markdown("In Advanced Settings → Secrets, paste this TOML:")
                    
                    secrets_toml = "\n".join([
                        f'{k} = "{v}"' if v else f'# {k} = "your-key-here"'
                        for k, v in user_secrets.items()
                    ])
                    
                    st.code(secrets_toml, language="toml")
                    
                    st.download_button(
                        "📥 Download secrets.toml",
                        data=secrets_toml,
                        file_name="secrets.toml",
                        mime="text/plain",
                    )
                
                st.markdown("### Step 4: Deploy!")
                st.success("Click 'Deploy' and your app will be live in minutes! 🎉")
            
            elif "Netlify" in selected_platform or "Vercel" in selected_platform:
                st.markdown(f"""
                ### Step 1: Push to GitHub
                1. Create a new repository on GitHub
                2. Save all code to your project folder
                3. Create `.gitignore` file:
                ```
                .env
                .env.local
                node_modules/
                .next/
                dist/
                ```
                4. Push to GitHub
                
                ### Step 2: Connect to {selected_platform}
                1. Go to [{selected_platform.lower()}.com](https://{selected_platform.lower()}.com)
                2. Sign in with GitHub
                3. Click "New Project" or "Add New Site"
                4. Select your repository
                5. Configure build settings (usually auto-detected)
                """)
                
                if detected_secrets and user_secrets:
                    st.markdown("### Step 3: Add Environment Variables")
                    st.markdown("In your project settings → Environment Variables, add:")
                    
                    env_vars_table = "\n".join([
                        f"- **{k}**: `{v if v else 'your-key-here'}`"
                        for k, v in user_secrets.items()
                    ])
                    st.markdown(env_vars_table)
                    
                    # Create .env.example file
                    env_example = "\n".join([f"{k}=" for k in detected_secrets])
                    st.code(env_example, language="bash")
                    
                    st.download_button(
                        "📥 Download .env.example",
                        data=env_example,
                        file_name=".env.example",
                        mime="text/plain",
                    )
                
                st.markdown("### Step 4: Deploy!")
                st.success(f"Click 'Deploy' and {selected_platform} will build and host your app! 🚀")
            
            else:  # Railway, Render, etc.
                st.markdown(f"""
                ### Step 1: Push to GitHub
                1. Create repository and push your code
                2. Include necessary config files (Dockerfile, requirements.txt, etc.)
                
                ### Step 2: Connect to {selected_platform}
                1. Go to [{selected_platform.lower()}.com](https://{selected_platform.lower()}.com)
                2. Create new project
                3. Connect your GitHub repository
                4. {selected_platform} will auto-detect your app type
                """)
                
                if detected_secrets and user_secrets:
                    st.markdown("### Step 3: Configure Environment Variables")
                    st.markdown(f"In {selected_platform} dashboard → Variables, add:")
                    
                    for k, v in user_secrets.items():
                        st.code(f"{k}={v if v else 'your-value-here'}", language="bash")
                
                st.markdown("### Step 4: Deploy!")
                st.success(f"{selected_platform} will automatically deploy your app! 🎉")
        
        # Additional Resources
        with st.expander("📚 Additional Resources"):
            st.markdown(f"""
            ### Helpful Links for {selected_platform}:
            
            - Official Documentation
            - Community Forum
            - Pricing Details
            - Status Page
            
            ### General Deployment Tips:
            
            1. **Test locally first** - Make sure your app runs on your machine
            2. **Use .gitignore** - Never commit secrets or sensitive files
            3. **Monitor your app** - Check logs after deployment
            4. **Start with free tier** - Scale up as needed
            5. **Set up custom domain** - Most platforms offer free SSL
            
            ### Security Best Practices:
            
            - ✅ Use environment variables for all secrets
            - ✅ Enable 2FA on your accounts
            - ✅ Regularly rotate API keys
            - ✅ Use different keys for development/production
            - ✅ Monitor API usage and costs
            """)

# ------------------------------------------------------------------------------
# Main Router
# ------------------------------------------------------------------------------
if page == "Agent Management":
    agent_management_page()
else:
    project_execution_page()

