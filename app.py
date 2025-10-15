# app.py
# ──────────────────────────────────────────────────────────────────────────────
# AI Factory — Streamlit + CrewAI starter app
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
# ──────────────────────────────────────────────────────────────────────────────

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4

import streamlit as st

# CrewAI imports (kept minimal and version-friendly)
from crewai import Agent, Task, Crew, Process

# ------------------------------------------------------------------------------
# App & Security Setup
# ------------------------------------------------------------------------------
st.set_page_config(page_title="AI Factory", page_icon="🏭", layout="wide")

# Ensure API key comes from Streamlit secrets; never hard-code.
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", "")
if not OPENAI_KEY:
    st.warning(
        "🔐 OpenAI API key not found in Streamlit secrets. "
        "Add it to `.streamlit/secrets.toml` as `OPENAI_API_KEY = \"...\"`."
    )
# CrewAI and the OpenAI SDK pick up the key from environment variables
os.environ["OPENAI_API_KEY"] = OPENAI_KEY

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
        # Fallback to empty list if structure is wrong
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

    # List agents with delete buttons
    for a in agents:
        with st.expander(f"🧩 {a.get('role', 'Unknown Role')}"):
            st.write(f"**Goal:** {a.get('goal','')}")
            st.write(f"**Backstory:** {a.get('backstory','')}")
            st.write(f"**Allow Delegation:** {'Yes' if a.get('allow_delegation') else 'No'}")
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
    # Pick a sensible default model (change if you prefer another)
    default_model = "gpt-4o-mini"

    return Agent(
        role=profile.get("role", "Agent"),
        goal=profile.get("goal", ""),
        backstory=profile.get("backstory", ""),
        allow_delegation=bool(profile.get("allow_delegation", True)),
        model=default_model,           # CrewAI will route this to OpenAI
        verbose=True,                  # Helpful while you're getting started
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
    )

    st.divider()
    colL, colR = st.columns([1, 1])
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
            "Crew Process",
            options=["hierarchical"],
            index=0,
            help="This app uses a hierarchical process where the orchestrator leads and delegates."
        )

    launch = st.button("🧩 Launch Crew", type="primary", use_container_width=True, disabled=not bool(idea.strip()))
    if launch:
        if not OPENAI_KEY:
            st.error("OpenAI API key missing. Add it to `.streamlit/secrets.toml` and reload the app.")
            return

        saved_agents = load_agents()
        if not saved_agents:
            st.error("No agents are configured. Please add agents in **Agent Management**.")
            return

        orchestrator_profile = find_orchestrator(saved_agents)
        if not orchestrator_profile:
            st.error("No Orchestrator Agent found. Create an agent with role name including 'Orchestrator'.")
            return

        # Convert profiles to CrewAI Agent instances
        try:
            crew_agents: List[Agent] = [build_crewai_agent(p) for p in saved_agents]
            # Orchestrator will naturally lead with hierarchical process if present.
            # (CrewAI internally coordinates based on process=Process.hierarchical)
        except Exception as e:
            st.error(f"Failed to initialize agents: {e}")
            return

        # Create a single high-level orchestration task
        task_description = (
            "You are the Orchestrator for this project. Analyze the user's idea, "
            "develop a clear execution plan, break it into tasks, and coordinate the work. "
            "Delegate to other available agents as needed. "
            "Deliver a final, cohesive result, including the plan, key decisions, artifacts, and next steps.\n\n"
            f"User's idea:\n{idea.strip()}"
        )
        orchestrator_task = Task(
            description=task_description,
            expected_output=(
                "A comprehensive final deliverable that includes: "
                "(1) a concise project summary, "
                "(2) a prioritized plan with milestones, "
                "(3) delegated tasks and outcomes, "
                "(4) final recommendations or artifacts, and "
                "(5) clear next steps."
            ),
            agent=build_crewai_agent(orchestrator_profile),  # Assign the task explicitly to the Orchestrator
        )

        # Assemble the crew
        crew_process = Process.hierarchical  # future extension point if you add more process types
        crew = Crew(
            agents=crew_agents,
            tasks=[orchestrator_task],
            process=crew_process,
            verbose=True,
        )

        # Run with a spinner and display results
        with st.spinner("🧪 The crew is working... orchestrating, delegating, and synthesizing results."):
            try:
                result = crew.kickoff()
            except Exception as e:
                st.error(f"❌ Crew execution failed: {e}")
                return

        st.success("✅ Crew execution complete!")
        # CrewAI often returns a rich object or a string; handle both
        if hasattr(result, "raw") and isinstance(result.raw, str):
            st.markdown(result.raw)
        else:
            st.markdown(str(result))

# ------------------------------------------------------------------------------
# Main Router
# ------------------------------------------------------------------------------
if page == "Agent Management":
    agent_management_page()
else:
    project_execution_page()

