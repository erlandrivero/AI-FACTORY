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
button[data-testid="baseButton-primary"] {
  background: var(--accent) !important;
  color: #fff !important;
  border: 1px solid transparent !important;
  border-radius: 12px !important;
}
button[data-testid="baseButton-secondary"] {
  background: var(--surface-2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}
button[data-testid="baseButton-primary"]:hover {
  background: var(--accent-hover) !important;
}

/* Alerts */
div[data-testid="stAlert"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  color: var(--text) !important;
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
[data-testid="stTooltipHoverTarget"] + div {
  background-color: var(--surface) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
}

/* Ensure help icon and tooltip content are visible */
.stTooltipIcon svg,
[data-testid="stMarkdownContainer"] p,
[role="tooltip"] * {
  color: var(--text) !important;
}
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Constants & Storage Helpers
# ------------------------------------------------------------------------------
AGENTS_FILE = Path("agents.json")

def _ensure_agents_file() -> None:
    """Create the agents.json file if it doesn't exist."""
    if not AGENTS_FILE.exists():
        AGENTS_FILE.write_text(json.dumps([], indent=2), encoding="utf-8")

def load_agents() -> List[Dict[str, Any]]:
    """Load agent profiles from agents.json (auto-creates if missing)."""
    _ensure_agents_file()
    try:
        data = json.loads(AGENTS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []

def save_agents(all_agents: List[Dict[str, Any]]) -> None:
    """Persist the full agent list to agents.json."""
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
    all_agents = load_agents()
    all_agents.append(agent)
    save_agents(all_agents)
    return agent

def delete_agent(agent_id: str) -> None:
    """Delete an agent by id."""
    all_agents = load_agents()
    filtered = [a for a in all_agents if a.get("id") != agent_id]
    save_agents(filtered)

def find_orchestrator(agents: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    """Find the orchestrator agent (by role containing 'orchestrator')."""
    for a in agents:
        if "orchestrator" in a.get("role", "").lower():
            return a
    return None

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
                value=True,
                help="If enabled, the agent can delegate work to others."
            )
        with col2:
            goal = st.text_input("Goal*", placeholder="e.g., Coordinate and deliver projects end-to-end")

        backstory = st.text_area(
            "Backstory*",
            placeholder="Brief background/personality to guide how this agent behaves."
        )

        submitted = st.form_submit_button("💾 Save Agent")
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
                    st.experimental_rerun()

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
    st.write("Describe your project idea and launch a hierarchical crew.")

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
    
    # Launch button right below the text area for better UX
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        launch = st.button(
            "🚀 Launch Crew",
            type="primary",
            use_container_width=True,
            disabled=not bool(idea.strip()),
            help="Click to start the crew with your project idea" if idea.strip() else "Enter a project idea to enable"
        )

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
            
            # Single high-level task for orchestrator
            task_description = (
                "You are the Orchestrator for this project. Analyze the user's idea, "
                "develop a clear execution plan, break it into tasks, and coordinate the work. "
                "Delegate to other available agents as needed. "
                "Deliver a final, cohesive result, including the plan, key decisions, artifacts, and next steps.\n\n"
                f"User's idea:\n{idea.strip()}"
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
            # Sequential: Create a task for each agent in order
            crew_process = Process.sequential
            for agent_profile in saved_agents:
                task_desc = (
                    f"As the {agent_profile.get('role', 'Agent')}, analyze the user's project idea and contribute your specialized expertise. "
                    f"Build upon previous work if available.\n\n"
                    f"Project idea: {idea.strip()}\n\n"
                    f"Your goal: {agent_profile.get('goal', 'Contribute to the project')}"
                )
                tasks.append(Task(
                    description=task_desc,
                    expected_output=f"Detailed analysis and contribution from the {agent_profile.get('role', 'Agent')} perspective.",
                    agent=build_crewai_agent(agent_profile),
                ))
                
        else:  # Consensus
            # Consensus: Each agent contributes to collaborative solution
            crew_process = Process.sequential
            for agent_profile in saved_agents:
                task_desc = (
                    f"As the {agent_profile.get('role', 'Agent')}, collaborate on the user's project idea. "
                    f"Review previous contributions and add your unique perspective. "
                    f"Work toward a consensus solution that incorporates all viewpoints.\n\n"
                    f"Project idea: {idea.strip()}\n\n"
                    f"Your goal: {agent_profile.get('goal', 'Contribute collaboratively')}"
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
                status_text.info(f"⏱️ **Elapsed Time:** {elapsed} seconds")
                
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
            time_display.success(f"🎉 **Completed in {elapsed_time} seconds!**")
            time.sleep(1.5)
            progress_container.empty()
            
        except Exception as e:
            progress_container.empty()
            st.error(f"❌ Crew execution failed: {e}")
            return
        
        st.success(f"✅ Crew execution complete! (Total time: {elapsed_time}s)")
        
        st.subheader("📄 Final Report")
        
        # Handle different result types from CrewAI
        if isinstance(result, str):
            # Simple string result
            st.markdown(result)
        else:
            # CrewOutput object (newer CrewAI versions)
            # Try to get the main output first
            main_output = None
            if hasattr(result, 'raw') and result.raw:
                main_output = result.raw
            elif hasattr(result, 'output') and result.output:
                main_output = result.output
            elif hasattr(result, 'pydantic') and hasattr(result.pydantic, 'raw'):
                main_output = result.pydantic.raw
            
            # Display the main output prominently
            if main_output and len(str(main_output).strip()) > 50:
                st.markdown(main_output)
                
                # Add export button
                report_text = str(main_output)
                st.download_button(
                    label="📥 Download Report (Markdown)",
                    data=report_text,
                    file_name=f"ai_factory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            else:
                # If main output is short/empty, check task outputs
                if hasattr(result, 'tasks_output') and result.tasks_output:
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
# Main Router
# ------------------------------------------------------------------------------
if page == "Agent Management":
    agent_management_page()
else:
    project_execution_page()

