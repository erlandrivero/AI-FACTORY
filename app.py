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
import re
import zipfile
import io
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
# Professional UI/UX Design System with Enhanced Spacing
# ------------------------------------------------------------------------------
DARK_CSS = """
<style>
/* Import Professional Typography */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Design System - Professional Color Palette */
:root {
  /* Background System */
  --bg-primary: #0F1117;           /* Main app background - deeper, richer */
  --bg-secondary: #1A1D29;         /* Content areas background */
  --bg-tertiary: #252936;          /* Elevated surfaces (cards, panels) */
  --bg-elevated: #2D3142;          /* Highest elevation (modals, popovers) */
  
  /* Border & Divider System */
  --border-subtle: #2D3142;        /* Subtle borders */
  --border-default: #3D4357;       /* Default borders */
  --border-emphasis: #4D5367;      /* Emphasized borders */
  
  /* Accent & Brand Colors */
  --accent-primary: #7C5CFF;       /* Primary brand purple */
  --accent-primary-hover: #6B4CFA; /* Hover state */
  --accent-primary-active: #5A3BE9; /* Active/pressed state */
  --accent-gradient: linear-gradient(135deg, #7C5CFF 0%, #9D7FFF 100%);
  
  /* Text System */
  --text-primary: #F5F5F7;         /* Primary text - high contrast */
  --text-secondary: #C7C7CC;       /* Secondary text */
  --text-tertiary: #8E8E93;        /* Tertiary text - labels, captions */
  --text-disabled: #636366;        /* Disabled state */
  
  /* Semantic Colors */
  --success: #34D399;              /* Success green */
  --success-bg: rgba(52, 211, 153, 0.1);
  --error: #F87171;                /* Error red */
  --error-bg: rgba(248, 113, 113, 0.1);
  --warning: #FBBF24;              /* Warning amber */
  --warning-bg: rgba(251, 191, 36, 0.1);
  --info: #60A5FA;                 /* Info blue */
  --info-bg: rgba(96, 165, 250, 0.1);
  
  /* Spacing System - Professional Breathing Room */
  --spacing-xs: 0.25rem;    /* 4px */
  --spacing-sm: 0.5rem;     /* 8px */
  --spacing-md: 1rem;       /* 16px */
  --spacing-lg: 1.5rem;     /* 24px */
  --spacing-xl: 2rem;       /* 32px */
  --spacing-2xl: 3rem;      /* 48px */
  --spacing-3xl: 4rem;      /* 64px */
  
  /* Border Radius System */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 18px;
  --radius-full: 9999px;
  
  /* Shadow System */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
  
  /* Typography Scale */
  --font-size-xs: 0.75rem;   /* 12px */
  --font-size-sm: 0.875rem;  /* 14px */
  --font-size-base: 1rem;    /* 16px */
  --font-size-lg: 1.125rem;  /* 18px */
  --font-size-xl: 1.25rem;   /* 20px */
  --font-size-2xl: 1.5rem;   /* 24px */
  --font-size-3xl: 1.875rem; /* 30px */
  
  /* Line Heights */
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;
  
  /* Transitions */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ============================================================================
   BASE APPLICATION STYLES - Enhanced Typography & Spacing
   ============================================================================ */

/* Main App Container */
html, body, [data-testid="stAppViewContainer"], .stApp {
  background-color: var(--bg-primary) !important;
  color: var(--text-primary) !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif !important;
  font-size: var(--font-size-base) !important;
  line-height: var(--leading-normal) !important;
  font-weight: 400 !important;
  -webkit-font-smoothing: antialiased !important;
  -moz-osx-font-smoothing: grayscale !important;
}

/* Main Content Area - Add Generous Padding */
.block-container {
  padding-top: var(--spacing-2xl) !important;
  padding-bottom: var(--spacing-2xl) !important;
  padding-left: var(--spacing-xl) !important;
  padding-right: var(--spacing-xl) !important;
  max-width: 1400px !important;
}

/* Column Gap Enhancement - More Breathing Room */
[data-testid="column"] {
  padding-left: var(--spacing-md) !important;
  padding-right: var(--spacing-md) !important;
}

/* First column - remove left padding */
[data-testid="column"]:first-child {
  padding-left: 0 !important;
}

/* Last column - remove right padding */
[data-testid="column"]:last-child {
  padding-right: 0 !important;
}

/* Increase gap between columns */
.row-widget.stHorizontalBlock {
  gap: var(--spacing-xl) !important;
}

/* Header */
[data-testid="stHeader"] {
  background: linear-gradient(180deg, rgba(15, 17, 23, 0.95), rgba(15, 17, 23, 0)) !important;
  color: var(--text-primary) !important;
  border-bottom: 1px solid var(--border-subtle) !important;
  backdrop-filter: blur(10px) !important;
}

/* Sidebar - Enhanced with Better Contrast */
[data-testid="stSidebar"] {
  background-color: var(--bg-secondary) !important;
  color: var(--text-primary) !important;
  border-right: 1px solid var(--border-default) !important;
  padding-top: var(--spacing-xl) !important;
}

[data-testid="stSidebar"] * {
  color: var(--text-primary) !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
  font-size: var(--font-size-sm) !important;
  line-height: var(--leading-relaxed) !important;
}

/* ============================================================================
   CARDS, CONTAINERS & EXPANDERS - Enhanced Visual Hierarchy
   ============================================================================ */

/* Base Container Text */
.block-container, .stTabs, .stDataFrame, .stMarkdown, .stMetric {
  color: var(--text-primary) !important;
}

/* Expander - Professional Card Style */
div[data-testid="stExpander"] {
  background: var(--bg-tertiary) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius-lg) !important;
  margin-bottom: var(--spacing-md) !important;
  box-shadow: var(--shadow-sm) !important;
  transition: all var(--transition-base) !important;
}

div[data-testid="stExpander"]:hover {
  border-color: var(--border-emphasis) !important;
  box-shadow: var(--shadow-md) !important;
}

/* Expander Header */
div[data-testid="stExpander"] > details > summary {
  background: var(--bg-elevated) !important;
  border-bottom: 1px solid var(--border-subtle) !important;
  padding: var(--spacing-lg) var(--spacing-xl) !important;
  font-weight: 600 !important;
  font-size: var(--font-size-base) !important;
  color: var(--text-primary) !important;
  cursor: pointer !important;
  transition: background-color var(--transition-fast) !important;
}

div[data-testid="stExpander"] > details > summary:hover {
  background: var(--bg-tertiary) !important;
}

/* Expander Content */
div[data-testid="stExpander"] > details > div {
  padding: var(--spacing-xl) !important;
}

div[data-testid="stExpander"] p,
div[data-testid="stExpander"] .stMarkdown {
  color: var(--text-secondary) !important;
  line-height: var(--leading-relaxed) !important;
}

/* ============================================================================
   INPUT FIELDS - Enhanced Spacing & Focus States
   ============================================================================ */

/* Text Inputs */
textarea, 
input[type="text"], 
input[type="search"], 
input[type="email"], 
input[type="password"] {
  background: var(--bg-tertiary) !important;
  color: var(--text-primary) !important;
  border: 1.5px solid var(--border-default) !important;
  border-radius: var(--radius-md) !important;
  padding: var(--spacing-md) var(--spacing-lg) !important;
  font-size: var(--font-size-base) !important;
  line-height: var(--leading-normal) !important;
  transition: all var(--transition-base) !important;
}

textarea:hover, 
input[type="text"]:hover, 
input[type="search"]:hover, 
input[type="email"]:hover, 
input[type="password"]:hover {
  border-color: var(--border-emphasis) !important;
  background: var(--bg-elevated) !important;
}

textarea:focus, 
input[type="text"]:focus, 
input[type="search"]:focus, 
input[type="email"]:focus, 
input[type="password"]:focus {
  border-color: var(--accent-primary) !important;
  background: var(--bg-elevated) !important;
  box-shadow: 0 0 0 3px rgba(124, 92, 255, 0.1) !important;
  outline: none !important;
}

textarea::placeholder, input::placeholder {
  color: var(--text-tertiary) !important;
  opacity: 1 !important;
}

/* Text Areas - Extra Padding */
textarea {
  min-height: 120px !important;
  line-height: var(--leading-relaxed) !important;
}

/* ============================================================================
   SELECT & DROPDOWN MENUS - Fixed for Dark Mode
   ============================================================================ */

/* Selectbox Container */
div[data-baseweb="select"] > div,
.stSelectbox > div > div {
  background: var(--bg-tertiary) !important;
  border: 1.5px solid var(--border-default) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-primary) !important;
  padding: var(--spacing-sm) var(--spacing-md) !important;
  transition: all var(--transition-base) !important;
}

div[data-baseweb="select"] > div:hover,
.stSelectbox > div > div:hover {
  border-color: var(--border-emphasis) !important;
  background: var(--bg-elevated) !important;
}

/* Selectbox Selected Value Text */
div[data-baseweb="select"] > div > div,
div[data-baseweb="select"] span,
div[data-baseweb="select"] input,
.stSelectbox div[data-baseweb="select"] > div {
  color: var(--text-primary) !important;
  background: transparent !important;
}

/* Selectbox Arrow Icon */
div[data-baseweb="select"] svg,
.stSelectbox svg {
  fill: var(--text-secondary) !important;
}

/* Dropdown Menu Container - Multiple Selectors for Higher Specificity */
[data-baseweb="menu"],
[data-baseweb="popover"],
ul[role="listbox"],
.stSelectbox [data-baseweb="popover"],
[data-baseweb="popover"] [data-baseweb="menu"] {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: var(--shadow-lg) !important;
  padding: var(--spacing-sm) !important;
}

/* Dropdown Menu Inner Content */
[data-baseweb="menu"] > ul,
[data-baseweb="popover"] > div,
ul[role="listbox"] {
  background: var(--bg-elevated) !important;
}

/* Dropdown Options - High Specificity */
[role="option"],
li[role="option"],
[data-baseweb="menu-item"],
.stSelectbox [role="option"],
[data-baseweb="menu"] li {
  background: transparent !important;
  color: var(--text-primary) !important;
  padding: var(--spacing-md) var(--spacing-lg) !important;
  border-radius: var(--radius-sm) !important;
  margin: var(--spacing-xs) 0 !important;
  transition: all var(--transition-fast) !important;
}

/* Force text color in all dropdown children */
[role="option"] *,
li[role="option"] *,
[data-baseweb="menu-item"] * {
  color: var(--text-primary) !important;
}

/* Dropdown Option Hover State */
[role="option"]:hover,
li[role="option"]:hover,
[data-baseweb="menu-item"]:hover,
.stSelectbox [role="option"]:hover {
  background: var(--bg-tertiary) !important;
  color: var(--text-primary) !important;
}

/* Selected Option Highlight */
[role="option"][aria-selected="true"],
li[role="option"][aria-selected="true"],
.stSelectbox [role="option"][aria-selected="true"] {
  background: var(--bg-tertiary) !important;
  color: var(--accent-primary) !important;
  font-weight: 600 !important;
}

/* Selectbox Label */
.stSelectbox label {
  color: var(--text-primary) !important;
  font-weight: 500 !important;
}

/* Override any white backgrounds in dropdown */
[data-baseweb="popover"] [style*="background"],
[data-baseweb="menu"] [style*="background"] {
  background: var(--bg-elevated) !important;
}

/* ============================================================================
   BUTTONS - Professional Design with Elevation
   ============================================================================ */

/* Primary Buttons */
.stButton > button, 
button[kind="secondary"],
button[data-testid="baseButton-primary"],
button[kind="primary"] {
  background: var(--accent-gradient) !important;
  color: #FFFFFF !important;
  border: none !important;
  padding: var(--spacing-md) var(--spacing-xl) !important;
  border-radius: var(--radius-md) !important;
  font-weight: 600 !important;
  font-size: var(--font-size-base) !important;
  letter-spacing: 0.01em !important;
  box-shadow: var(--shadow-sm) !important;
  transition: all var(--transition-base) !important;
  cursor: pointer !important;
}

.stButton > button:hover, 
button[kind="secondary"]:hover,
button[data-testid="baseButton-primary"]:hover,
button[kind="primary"]:hover {
  transform: translateY(-2px) !important;
  box-shadow: var(--shadow-md) !important;
  background: linear-gradient(135deg, var(--accent-primary-hover) 0%, #8D6FFF 100%) !important;
}

.stButton > button:active,
button[kind="secondary"]:active,
button[data-testid="baseButton-primary"]:active,
button[kind="primary"]:active {
  transform: translateY(0) !important;
  box-shadow: var(--shadow-sm) !important;
}

.stButton > button:focus,
button[kind="secondary"]:focus,
button[data-testid="baseButton-primary"]:focus,
button[kind="primary"]:focus {
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(124, 92, 255, 0.3) !important;
}

/* Secondary Buttons */
button[data-testid="baseButton-secondary"] {
  background: var(--bg-tertiary) !important;
  color: var(--text-primary) !important;
  border: 1.5px solid var(--border-default) !important;
  border-radius: var(--radius-md) !important;
  padding: var(--spacing-md) var(--spacing-xl) !important;
  font-weight: 600 !important;
  font-size: var(--font-size-base) !important;
  transition: all var(--transition-base) !important;
}

button[data-testid="baseButton-secondary"]:hover {
  background: var(--bg-elevated) !important;
  border-color: var(--border-emphasis) !important;
  transform: translateY(-1px) !important;
  box-shadow: var(--shadow-sm) !important;
}

/* Disabled Button State */
.stButton > button:disabled,
button:disabled {
  opacity: 0.5 !important;
  cursor: not-allowed !important;
  transform: none !important;
  box-shadow: none !important;
}

/* ============================================================================
   ALERTS & NOTIFICATIONS - Enhanced Visual Communication
   ============================================================================ */

/* Info Messages */
.stInfo, 
[data-testid="stInfo"],
div[data-testid="stAlert"] {
  background: var(--info-bg) !important;
  border-left: 4px solid var(--info) !important;
  border-radius: var(--radius-md) !important;
  padding: var(--spacing-lg) var(--spacing-xl) !important;
  color: var(--text-primary) !important;
  margin: var(--spacing-md) 0 !important;
}

/* Success Messages */
.stSuccess, 
[data-testid="stSuccess"] {
  background: var(--success-bg) !important;
  border-left: 4px solid var(--success) !important;
  border-radius: var(--radius-md) !important;
  padding: var(--spacing-lg) var(--spacing-xl) !important;
  color: var(--text-primary) !important;
  margin: var(--spacing-md) 0 !important;
}

/* Warning Messages */
.stWarning, 
[data-testid="stWarning"] {
  background: var(--warning-bg) !important;
  border-left: 4px solid var(--warning) !important;
  border-radius: var(--radius-md) !important;
  padding: var(--spacing-lg) var(--spacing-xl) !important;
  color: var(--text-primary) !important;
  margin: var(--spacing-md) 0 !important;
}

/* Error Messages */
.stError, 
[data-testid="stError"] {
  background: var(--error-bg) !important;
  border-left: 4px solid var(--error) !important;
  border-radius: var(--radius-md) !important;
  padding: var(--spacing-lg) var(--spacing-xl) !important;
  color: var(--text-primary) !important;
  margin: var(--spacing-md) 0 !important;
}

/* Alert Content */
div[data-testid="stAlert"] *,
div[data-testid="stNotification"] *,
.stAlert *,
div[data-testid="stAlert"] p,
div[data-testid="stAlert"] strong {
  color: var(--text-primary) !important;
  background: transparent !important;
}

/* ============================================================================
   TYPOGRAPHY & TEXT ELEMENTS
   ============================================================================ */

/* Headings - Enhanced Hierarchy */
h1, h2, h3, h4, h5, h6 {
  color: var(--text-primary) !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em !important;
  line-height: var(--leading-tight) !important;
  margin-bottom: var(--spacing-md) !important;
}

h1 { font-size: var(--font-size-3xl) !important; }
h2 { font-size: var(--font-size-2xl) !important; }
h3 { font-size: var(--font-size-xl) !important; }

/* Paragraphs & Labels */
label, p, li, span {
  color: var(--text-secondary) !important;
  line-height: var(--leading-relaxed) !important;
}

/* Strong Text */
strong, b {
  color: var(--text-primary) !important;
  font-weight: 600 !important;
}

/* Captions */
[data-testid="stCaptionContainer"],
.stTextInput small,
.stTextArea small {
  color: var(--text-tertiary) !important;
  font-size: var(--font-size-sm) !important;
  line-height: var(--leading-normal) !important;
}

/* Form Labels */
.stCheckbox label span,
.stCheckbox [data-testid="stMarkdownContainer"] {
  color: var(--text-primary) !important;
  font-weight: 500 !important;
}

/* ============================================================================
   HELP ICONS & TOOLTIPS
   ============================================================================ */

/* Help Icons */
svg.info-icon,
.stCheckbox svg,
.stSelectbox svg[data-testid="stTooltipHoverTarget"],
.stTextInput svg[data-testid="stTooltipHoverTarget"],
.stTextArea svg[data-testid="stTooltipHoverTarget"],
[data-testid="stTooltipHoverTarget"] svg {
  fill: var(--text-secondary) !important;
  color: var(--text-secondary) !important;
  opacity: 0.8 !important;
  transition: opacity var(--transition-fast) !important;
}

[data-testid="stTooltipHoverTarget"]:hover svg {
  opacity: 1 !important;
}

/* Tooltip Container */
[data-testid="stTooltipHoverTarget"] {
  color: var(--text-secondary) !important;
  display: inline-flex !important;
  visibility: visible !important;
}

/* Tooltips */
[data-baseweb="tooltip"],
[role="tooltip"] {
  background-color: var(--bg-elevated) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius-md) !important;
  padding: var(--spacing-sm) var(--spacing-md) !important;
  box-shadow: var(--shadow-lg) !important;
  font-size: var(--font-size-sm) !important;
}

/* ============================================================================
   CODE BLOCKS & MARKDOWN
   ============================================================================ */

/* Inline Code */
code {
  background: var(--bg-tertiary) !important;
  color: var(--accent-primary) !important;
  padding: var(--spacing-xs) var(--spacing-sm) !important;
  border-radius: var(--radius-sm) !important;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Courier New', monospace !important;
  font-size: 0.9em !important;
}

/* Code Blocks */
pre {
  background: var(--bg-tertiary) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius-md) !important;
  padding: var(--spacing-lg) !important;
  overflow-x: auto !important;
  line-height: var(--leading-relaxed) !important;
}

pre code {
  background: transparent !important;
  padding: 0 !important;
}

/* ============================================================================
   LOADING STATES & PROGRESS
   ============================================================================ */

/* Spinner */
div[data-testid="stSpinner"] {
  background: var(--bg-tertiary) !important;
  color: var(--text-primary) !important;
  border-radius: var(--radius-md) !important;
  padding: var(--spacing-lg) var(--spacing-xl) !important;
  border: 1px solid var(--border-default) !important;
  box-shadow: var(--shadow-sm) !important;
}

/* Progress Bars */
.stProgress > div > div > div {
  background-color: var(--accent-gradient) !important;
  border-radius: var(--radius-full) !important;
}

[data-testid="stProgressBar"] {
  background-color: var(--bg-tertiary) !important;
  border-radius: var(--radius-full) !important;
  height: 8px !important;
}

/* ============================================================================
   DIVIDERS & SEPARATORS
   ============================================================================ */

hr, .stDivider {
  border-color: var(--border-default) !important;
  opacity: 0.5 !important;
  margin: var(--spacing-xl) 0 !important;
}

/* ============================================================================
   SCROLLBARS - Custom Styled
   ============================================================================ */

*::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

*::-webkit-scrollbar-track {
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
}

*::-webkit-scrollbar-thumb {
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  border: 2px solid var(--bg-primary);
  transition: background-color var(--transition-base);
}

*::-webkit-scrollbar-thumb:hover {
  background-color: var(--bg-elevated);
}

/* ============================================================================
   TEXTAREA INTERACTIONS & USABILITY
   ============================================================================ */

/* Text Area - Enhanced Interaction */
textarea {
  line-height: var(--leading-relaxed) !important;
  pointer-events: auto !important;
  cursor: text !important;
  user-select: text !important;
  resize: vertical !important;
}

.stTextArea textarea {
  pointer-events: auto !important;
  cursor: text !important;
  user-select: text !important;
}

/* Ensure text area container doesn't block clicks */
.stTextArea, 
[data-testid="stTextArea"] {
  pointer-events: auto !important;
}

.stTextArea > div, 
[data-testid="stTextArea"] > div {
  pointer-events: auto !important;
}

/* Hide Streamlit's default input instructions */
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

/* Metrics (st.metric) */
[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 0.75rem !important;
}
[data-testid="stMetricLabel"],
[data-testid="stMetric"] label {
  color: var(--text-muted) !important;
  font-size: 0.75rem !important;
}
[data-testid="stMetricValue"],
[data-testid="stMetric"] [data-testid="stMarkdownContainer"] {
  color: var(--text) !important;
  font-size: 1rem !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}
[data-testid="stMetricDelta"] {
  color: var(--text) !important;
  font-size: 0.875rem !important;
}

/* Download buttons */
.stDownloadButton > button {
  background: var(--surface-2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}
.stDownloadButton > button:hover {
  background: var(--surface) !important;
  border-color: var(--accent) !important;
}

/* Radio buttons and checkboxes */
.stRadio label,
.stCheckbox label {
  color: var(--text) !important;
}
.stRadio > div,
.stCheckbox > div {
  color: var(--text) !important;
}

/* Columns */
[data-testid="column"] {
  color: var(--text) !important;
}

/* Info, success, warning, error messages */
.stInfo, [data-testid="stInfo"] {
  background-color: rgba(124, 92, 255, 0.1) !important;
  border-left: 4px solid var(--accent) !important;
  color: var(--text) !important;
}
.stSuccess, [data-testid="stSuccess"] {
  background-color: rgba(34, 197, 94, 0.1) !important;
  border-left: 4px solid var(--success) !important;
  color: var(--text) !important;
}
.stWarning, [data-testid="stWarning"] {
  background-color: rgba(245, 158, 11, 0.1) !important;
  border-left: 4px solid var(--warning) !important;
  color: var(--text) !important;
}
.stError, [data-testid="stError"] {
  background-color: rgba(239, 68, 68, 0.1) !important;
  border-left: 4px solid var(--error) !important;
  color: var(--text) !important;
}

/* Progress bars */
.stProgress > div > div > div {
  background-color: var(--accent) !important;
}
[data-testid="stProgressBar"] {
  background-color: var(--surface-2) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background-color: var(--surface) !important;
  border-bottom: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  color: var(--text-muted) !important;
  background-color: transparent !important;
}
.stTabs [aria-selected="true"] {
  color: var(--accent) !important;
  border-bottom-color: var(--accent) !important;
}
.stTabs [data-baseweb="tab-panel"] {
  background-color: var(--surface) !important;
  color: var(--text) !important;
  padding: 1rem !important;
  border-radius: 0 0 10px 10px !important;
}

/* Links */
a, a:visited {
  color: var(--accent) !important;
}
a:hover {
  color: var(--accent-hover) !important;
  text-decoration: underline !important;
}

/* Markdown elements */
.stMarkdown a {
  color: var(--accent) !important;
}
.stMarkdown code {
  background: var(--surface-2) !important;
  color: var(--text) !important;
  padding: 2px 6px !important;
  border-radius: 4px !important;
}
.stMarkdown pre {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  padding: 1rem !important;
}
.stMarkdown blockquote {
  border-left: 4px solid var(--accent) !important;
  padding-left: 1rem !important;
  color: var(--text-muted) !important;
}
.stMarkdown table {
  color: var(--text) !important;
}
.stMarkdown th {
  background: var(--surface-2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}
.stMarkdown td {
  background: var(--surface) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}

/* DataFrames and Tables */
.stDataFrame, [data-testid="stDataFrame"] {
  background: var(--surface) !important;
  color: var(--text) !important;
}
.stDataFrame table {
  color: var(--text) !important;
}
.stDataFrame th {
  background: var(--surface-2) !important;
  color: var(--text) !important;
}
.stDataFrame td {
  color: var(--text) !important;
}

/* JSON display */
.stJson {
  background: var(--surface-2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}

/* Ensure all text is visible */
div, span, p, label, li {
  color: var(--text) !important;
}

/* Fix any potential white-on-white or black-on-black */
[style*="color: rgb(0, 0, 0)"],
[style*="color: #000"],
[style*="color: black"] {
  color: var(--text) !important;
}
[style*="color: rgb(255, 255, 255)"],
[style*="color: #fff"],
[style*="color: white"] {
  color: var(--text) !important;
}

/* ============================================================================
   AGENT MANAGEMENT - Custom Card Styling
   ============================================================================ */

/* Agent Card Container */
.agent-card {
  background: var(--bg-tertiary) !important;
  border: 1.5px solid var(--border-default) !important;
  border-radius: var(--radius-lg) !important;
  padding: var(--spacing-xl) !important;
  margin-bottom: var(--spacing-lg) !important;
  box-shadow: var(--shadow-sm) !important;
  transition: all var(--transition-base) !important;
  position: relative !important;
}

.agent-card:hover {
  border-color: var(--border-emphasis) !important;
  box-shadow: var(--shadow-md) !important;
  transform: translateY(-2px) !important;
}

/* Agent Card Header */
.agent-card-header {
  display: flex !important;
  justify-content: space-between !important;
  align-items: flex-start !important;
  margin-bottom: var(--spacing-md) !important;
}

/* Agent Role Title */
.agent-role {
  font-size: var(--font-size-xl) !important;
  font-weight: 700 !important;
  color: var(--text-primary) !important;
  margin-bottom: var(--spacing-sm) !important;
  letter-spacing: -0.01em !important;
}

/* Agent Goal Text */
.agent-goal {
  font-size: var(--font-size-base) !important;
  color: var(--text-secondary) !important;
  line-height: var(--leading-relaxed) !important;
  margin-bottom: var(--spacing-md) !important;
}

/* Agent Backstory */
.agent-backstory {
  font-size: var(--font-size-sm) !important;
  color: var(--text-tertiary) !important;
  line-height: var(--leading-relaxed) !important;
  font-style: italic !important;
  padding: var(--spacing-md) !important;
  background: var(--bg-secondary) !important;
  border-left: 3px solid var(--accent-primary) !important;
  border-radius: var(--radius-sm) !important;
  margin-top: var(--spacing-md) !important;
}

/* Agent Badge (delegation status) */
.agent-badge {
  display: inline-block !important;
  padding: var(--spacing-xs) var(--spacing-md) !important;
  background: var(--accent-primary) !important;
  color: #FFFFFF !important;
  font-size: var(--font-size-xs) !important;
  font-weight: 600 !important;
  border-radius: var(--radius-full) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}

.agent-badge.no-delegation {
  background: var(--bg-elevated) !important;
  color: var(--text-tertiary) !important;
}

/* Empty State */
.empty-agents-state {
  text-align: center !important;
  padding: var(--spacing-3xl) var(--spacing-xl) !important;
  background: var(--bg-secondary) !important;
  border: 2px dashed var(--border-default) !important;
  border-radius: var(--radius-lg) !important;
  color: var(--text-tertiary) !important;
}

.empty-agents-state-icon {
  font-size: 48px !important;
  margin-bottom: var(--spacing-lg) !important;
  opacity: 0.5 !important;
}

.empty-agents-state-text {
  font-size: var(--font-size-lg) !important;
  color: var(--text-secondary) !important;
  margin-bottom: var(--spacing-sm) !important;
}

.empty-agents-state-hint {
  font-size: var(--font-size-sm) !important;
  color: var(--text-tertiary) !important;
}

/* ============================================================================
   PROJECT EXECUTION - Enhanced Styling
   ============================================================================ */

/* Styled Section Titles */
.section-title {
  font-size: var(--font-size-2xl) !important;
  font-weight: 700 !important;
  color: var(--text-primary) !important;
  margin-bottom: var(--spacing-lg) !important;
  padding-bottom: var(--spacing-md) !important;
  border-bottom: 2px solid var(--border-emphasis) !important;
  letter-spacing: -0.02em !important;
  background: var(--accent-gradient) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
}

.section-subtitle {
  font-size: var(--font-size-lg) !important;
  font-weight: 600 !important;
  color: var(--text-primary) !important;
  margin-bottom: var(--spacing-md) !important;
  display: flex !important;
  align-items: center !important;
  gap: var(--spacing-sm) !important;
}

/* Enhanced Project Idea Text Area */
.project-idea-container {
  margin: var(--spacing-lg) 0 !important;
}

.project-idea-container textarea {
  background: var(--bg-elevated) !important;
  border: 2px solid var(--border-default) !important;
  border-radius: var(--radius-lg) !important;
  padding: var(--spacing-xl) !important;
  font-size: var(--font-size-base) !important;
  line-height: var(--leading-relaxed) !important;
  transition: all var(--transition-base) !important;
  min-height: 180px !important;
}

.project-idea-container textarea:hover {
  border-color: var(--border-emphasis) !important;
  background: var(--bg-tertiary) !important;
}

.project-idea-container textarea:focus {
  border-color: var(--accent-primary) !important;
  background: var(--bg-tertiary) !important;
  box-shadow: 0 0 0 4px rgba(124, 92, 255, 0.15) !important;
  outline: none !important;
}

/* Prominent Launch/Action Buttons */
.launch-button button,
.primary-action-button button {
  background: var(--accent-gradient) !important;
  color: #FFFFFF !important;
  border: none !important;
  padding: var(--spacing-lg) var(--spacing-2xl) !important;
  border-radius: var(--radius-lg) !important;
  font-size: var(--font-size-lg) !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em !important;
  text-transform: uppercase !important;
  box-shadow: 0 4px 12px rgba(124, 92, 255, 0.3) !important;
  transition: all var(--transition-base) !important;
  cursor: pointer !important;
  position: relative !important;
  overflow: hidden !important;
}

.launch-button button:hover,
.primary-action-button button:hover {
  transform: translateY(-3px) !important;
  box-shadow: 0 8px 20px rgba(124, 92, 255, 0.4) !important;
  background: linear-gradient(135deg, var(--accent-primary-hover) 0%, #9D7FFF 100%) !important;
}

.launch-button button:active,
.primary-action-button button:active {
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(124, 92, 255, 0.3) !important;
}

.launch-button button:disabled,
.primary-action-button button:disabled {
  opacity: 0.5 !important;
  cursor: not-allowed !important;
  transform: none !important;
  box-shadow: none !important;
}

/* Final Report Container */
.report-container {
  background: var(--bg-tertiary) !important;
  border: 2px solid var(--border-emphasis) !important;
  border-radius: var(--radius-xl) !important;
  padding: var(--spacing-2xl) !important;
  margin: var(--spacing-xl) 0 !important;
  box-shadow: var(--shadow-lg) !important;
  position: relative !important;
}

.report-container::before {
  content: '' !important;
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  height: 4px !important;
  background: var(--accent-gradient) !important;
  border-radius: var(--radius-xl) var(--radius-xl) 0 0 !important;
}

.report-header {
  font-size: var(--font-size-2xl) !important;
  font-weight: 700 !important;
  color: var(--text-primary) !important;
  margin-bottom: var(--spacing-xl) !important;
  padding-bottom: var(--spacing-md) !important;
  border-bottom: 1px solid var(--border-default) !important;
  display: flex !important;
  align-items: center !important;
  gap: var(--spacing-md) !important;
}

.report-content {
  color: var(--text-secondary) !important;
  line-height: var(--leading-relaxed) !important;
  font-size: var(--font-size-base) !important;
}

.report-content h1,
.report-content h2,
.report-content h3 {
  color: var(--text-primary) !important;
  margin-top: var(--spacing-xl) !important;
  margin-bottom: var(--spacing-md) !important;
}

.report-content code {
  background: var(--bg-secondary) !important;
  color: var(--accent-primary) !important;
  padding: var(--spacing-xs) var(--spacing-sm) !important;
  border-radius: var(--radius-sm) !important;
  font-size: 0.9em !important;
}

.report-content pre {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius-md) !important;
  padding: var(--spacing-lg) !important;
  overflow-x: auto !important;
  margin: var(--spacing-md) 0 !important;
}

/* Info Cards/Panels */
.info-panel {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius-lg) !important;
  padding: var(--spacing-lg) !important;
  margin: var(--spacing-md) 0 !important;
}

.info-panel-title {
  font-size: var(--font-size-base) !important;
  font-weight: 600 !important;
  color: var(--text-primary) !important;
  margin-bottom: var(--spacing-sm) !important;
}

.info-panel-content {
  font-size: var(--font-size-sm) !important;
  color: var(--text-secondary) !important;
  line-height: var(--leading-relaxed) !important;
}

/* Phase Progress Pills */
.phase-pill {
  display: inline-block !important;
  padding: var(--spacing-sm) var(--spacing-lg) !important;
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius-full) !important;
  font-size: var(--font-size-sm) !important;
  font-weight: 500 !important;
  color: var(--text-secondary) !important;
  margin: 0 var(--spacing-xs) !important;
}

.phase-pill.active {
  background: var(--accent-gradient) !important;
  border-color: var(--accent-primary) !important;
  color: #FFFFFF !important;
  font-weight: 600 !important;
  box-shadow: 0 2px 8px rgba(124, 92, 255, 0.3) !important;
}

.phase-pill.completed {
  background: var(--success-bg) !important;
  border-color: var(--success) !important;
  color: var(--success) !important;
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

def find_strategy_consultant(agents: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    """Find the strategy consultant agent (by role containing 'strategy consultant')."""
    for a in agents:
        if "strategy consultant" in a.get("role", "").lower():
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

def extract_code_files_from_result(result_text: str) -> Dict[str, str]:
    """Extract code files from markdown result."""
    files = {}
    
    # Pattern to match: ### File: filename.ext followed by ```language ... ```
    pattern = r'###\s+File:\s+([^\n]+)\n\s*```(\w+)?\n(.*?)```'
    matches = re.finditer(pattern, result_text, re.DOTALL)
    
    for match in matches:
        filename = match.group(1).strip()
        content = match.group(3).strip()
        files[filename] = content
    
    return files

def create_project_zip(files: Dict[str, str], project_name: str = "project") -> bytes:
    """Create a ZIP file from extracted code files."""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filepath, content in files.items():
            zip_file.writestr(filepath, content)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def write_files_to_directory(files: Dict[str, str], base_path: str) -> tuple:
    """Write extracted files to a local directory."""
    try:
        base_dir = Path(base_path)
        base_dir.mkdir(parents=True, exist_ok=True)
        
        written_files = []
        for filepath, content in files.items():
            full_path = base_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            written_files.append(str(full_path))
        
        return True, written_files
    except Exception as e:
        return False, str(e)

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
        "Create, view, and manage your AI agents. Build a team with specialized roles and skills."
    )
    
    st.divider()

    # Collapsible form for creating new agents
    with st.expander("➕ Create a New Agent", expanded=False):
        st.caption("Define a new agent with a specific role, goal, and personality.")
        
        with st.form("create_agent_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                role = st.text_input(
                    "Role*", 
                    placeholder="e.g., Orchestrator Agent, Strategy Consultant",
                    help="The agent's job title or primary function"
                )
            with col2:
                goal = st.text_input(
                    "Goal*", 
                    placeholder="e.g., Coordinate and deliver projects end-to-end",
                    help="What this agent aims to accomplish"
                )

            backstory = st.text_area(
                "Backstory*",
                placeholder="You are an expert in... Your specialty is... You have experience with...",
                help="The agent's background, expertise, and personality traits",
                height=120
            )
            
            allow_delegation = st.checkbox(
                "Allow Delegation",
                value=False,
                help="✨ Enable this for manager agents (like Orchestrator) who can delegate tasks to other agents"
            )

            col_submit1, col_submit2, col_submit3 = st.columns([1, 1, 1])
            with col_submit2:
                submitted = st.form_submit_button("💾 Save Agent", use_container_width=True, type="primary")
            
            if submitted:
                if not role.strip() or not goal.strip() or not backstory.strip():
                    st.error("⚠️ Please fill in all required fields (Role, Goal, and Backstory).")
                else:
                    agent = add_agent(role, goal, backstory, allow_delegation)
                    st.success(f"✅ Agent '{agent['role']}' created successfully!")
                    st.balloons()

    st.divider()
    
    # Display current agents as styled cards
    st.subheader("👥 Your Agent Team")
    agents = load_agents()
    
    if not agents:
        # Empty state with styled message
        st.markdown("""
        <div class="empty-agents-state">
            <div class="empty-agents-state-icon">🤖</div>
            <div class="empty-agents-state-text">No agents created yet</div>
            <div class="empty-agents-state-hint">Click "➕ Create a New Agent" above to build your first AI agent</div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.caption(f"Managing {len(agents)} agent{'s' if len(agents) != 1 else ''}")
    
    # Display each agent as a beautiful card
    for idx, agent in enumerate(agents):
        # Create card with custom HTML/CSS
        delegation_badge = ""
        if agent.get('allow_delegation'):
            delegation_badge = '<span class="agent-badge">Can Delegate</span>'
        else:
            delegation_badge = '<span class="agent-badge no-delegation">Individual</span>'
        
        # Card header with role and delete button
        col_card, col_delete = st.columns([5, 1])
        
        with col_card:
            st.markdown(f"""
            <div class="agent-card">
                <div class="agent-card-header">
                    <div>
                        <div class="agent-role">🧩 {agent.get('role', 'Unknown Role')}</div>
                        {delegation_badge}
                    </div>
                </div>
                <div class="agent-goal">
                    <strong>🎯 Goal:</strong> {agent.get('goal', 'No goal specified')}
                </div>
                <div class="agent-backstory">
                    <strong>📖 Backstory:</strong><br>{agent.get('backstory', 'No backstory provided')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_delete:
            st.write("")  # Spacer for alignment
            st.write("")  # Additional spacer
            if st.button("🗑️", key=f"del_{agent['id']}", help=f"Delete {agent.get('role')}", use_container_width=True):
                if st.session_state.get(f"confirm_delete_{agent['id']}", False):
                    delete_agent(agent["id"])
                    st.success(f"🗑️ Deleted '{agent.get('role')}'")
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_{agent['id']}"] = True
                    st.warning("⚠️ Click delete again to confirm")
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
# Helper: Intelligent API Key Detection
# ------------------------------------------------------------------------------
def detect_api_keys_for_stack(package_name: str, full_strategy_text: str, additional_features: str = "", special_requirements: str = "") -> tuple:
    """
    Intelligently detect required and optional API keys based on the selected package.
    Analyzes the package content to extract tech stack details.
    
    Args:
        package_name: The selected package name (e.g., "Package A")
        full_strategy_text: The content of the selected package
        additional_features: User's additional feature requests
        special_requirements: User's special requirements
    
    Returns: (required_keys_dict, optional_keys_dict)
    
    Note: User's additional features and requirements take priority over package defaults.
    """
    required_keys = {}
    optional_keys = {}
    
    # Combine all text for analysis - USER INPUT TAKES PRIORITY
    combined_text = f"{package_name.lower()} {full_strategy_text.lower()} {additional_features.lower()} {special_requirements.lower()}"
    
    # ========== TECH STACK SPECIFIC DETECTION ==========
    
    # MERN Stack (MongoDB, Express, React, Node.js)
    if "mern" in combined_text or ("mongodb" in combined_text and "react" in combined_text and "express" in combined_text):
        optional_keys["MongoDB Atlas URI"] = "MongoDB connection string (mongodb+srv://user:pass@cluster.mongodb.net/dbname)"
        optional_keys["JWT Secret"] = "Secret key for JWT token generation (authentication)"
        optional_keys["Port"] = "Server port (default: 5000 or 3000)"
    
    # MEAN Stack (MongoDB, Express, Angular, Node.js)
    if "mean" in combined_text or ("mongodb" in combined_text and "angular" in combined_text):
        optional_keys["MongoDB Atlas URI"] = "MongoDB connection string"
        optional_keys["JWT Secret"] = "Secret key for authentication tokens"
    
    # PERN Stack (PostgreSQL, Express, React, Node.js)
    if "pern" in combined_text or ("postgresql" in combined_text and "react" in combined_text):
        optional_keys["PostgreSQL Database URL"] = "PostgreSQL connection (postgresql://user:pass@host:5432/db)"
        optional_keys["JWT Secret"] = "Secret for JWT authentication"
    
    # Next.js
    if "next" in combined_text or "nextjs" in combined_text:
        optional_keys["NEXT_PUBLIC_API_URL"] = "Public API URL for client-side requests"
    
    # Django
    if "django" in combined_text:
        optional_keys["Django Secret Key"] = "Django SECRET_KEY for security"
        optional_keys["Database URL"] = "Database connection string"
    
    # Flask
    if "flask" in combined_text:
        optional_keys["Flask Secret Key"] = "Flask SECRET_KEY for sessions"
        optional_keys["Database URI"] = "SQLAlchemy database URI"
    
    # ========== DATABASE DETECTION ==========
    
    if "supabase" in combined_text:
        required_keys["Supabase Project URL"] = "Your Supabase project URL (https://xxxxx.supabase.co)"
        required_keys["Supabase Anon Key"] = "Your Supabase anonymous/public API key"
    
    if "firebase" in combined_text:
        required_keys["Firebase Config JSON"] = "Your Firebase configuration object"
    
    if "mongodb" in combined_text and "MongoDB Atlas URI" not in optional_keys:
        optional_keys["MongoDB Connection String"] = "MongoDB URI (mongodb+srv://...)"
    
    if ("postgres" in combined_text or "postgresql" in combined_text) and "PostgreSQL" not in str(optional_keys):
        optional_keys["PostgreSQL URL"] = "PostgreSQL connection (postgresql://...)"
    
    if "mysql" in combined_text:
        optional_keys["MySQL Connection String"] = "MySQL database connection"
    
    # ========== DEPLOYMENT PLATFORM ==========
    
    if "netlify" in combined_text:
        optional_keys["Netlify API Token"] = "For automated deployments (app.netlify.com → Personal access tokens)"
    
    if "vercel" in combined_text:
        optional_keys["Vercel Token"] = "For automated deployments (vercel.com/account/tokens)"
    
    if "railway" in combined_text:
        optional_keys["Railway Token"] = "For Railway deployments (railway.app/account/tokens)"
    
    if "render" in combined_text:
        optional_keys["Render API Key"] = "For Render deployments (dashboard.render.com)"
    
    if "heroku" in combined_text:
        optional_keys["Heroku API Key"] = "For Heroku deployments"
    
    if "aws" in combined_text or "amazon web services" in combined_text:
        optional_keys["AWS Access Key ID"] = "AWS access key for deployments"
        optional_keys["AWS Secret Access Key"] = "AWS secret key"
    
    if "digitalocean" in combined_text:
        optional_keys["DigitalOcean Token"] = "DigitalOcean API token"
    
    # ========== SERVICE INTEGRATIONS ==========
    
    if "openai" in combined_text or "gpt" in combined_text or "chatgpt" in combined_text:
        optional_keys["OpenAI API Key"] = "For AI features (platform.openai.com/api-keys)"
    
    if "stripe" in combined_text or "payment" in combined_text:
        optional_keys["Stripe API Key"] = "For payments (dashboard.stripe.com/apikeys)"
        optional_keys["Stripe Webhook Secret"] = "For webhook verification"
    
    if "sendgrid" in combined_text or ("email" in combined_text and "send" in combined_text):
        optional_keys["SendGrid API Key"] = "For email sending (sendgrid.com/api-keys)"
    
    if "twilio" in combined_text or "sms" in combined_text:
        optional_keys["Twilio Account SID"] = "Twilio account SID"
        optional_keys["Twilio Auth Token"] = "Twilio auth token"
    
    if "cloudinary" in combined_text or "image upload" in combined_text or "media upload" in combined_text:
        optional_keys["Cloudinary Cloud Name"] = "Cloudinary cloud name"
        optional_keys["Cloudinary API Key"] = "Cloudinary API key"
        optional_keys["Cloudinary API Secret"] = "Cloudinary API secret"
    
    if "google" in combined_text and "auth" in combined_text:
        optional_keys["Google OAuth Client ID"] = "For Google sign-in"
        optional_keys["Google OAuth Client Secret"] = "Google OAuth secret"
    
    if "github" in combined_text and "auth" in combined_text:
        optional_keys["GitHub OAuth Client ID"] = "For GitHub authentication"
        optional_keys["GitHub OAuth Client Secret"] = "GitHub OAuth secret"
    
    # ========== ALWAYS USEFUL (Only if CI/CD mentioned) ==========
    if "ci/cd" in combined_text or "github actions" in combined_text or "automation" in combined_text:
        optional_keys["GitHub Personal Access Token"] = "For CI/CD automation (github.com/settings/tokens)"
    
    return required_keys, optional_keys

# ------------------------------------------------------------------------------
# PAGE: Project Execution
# ------------------------------------------------------------------------------
def project_execution_page():
    st.header("🚀 Project Execution")
    st.write("Build complete applications with AI-powered agents.")

    # Initialize session state for phase-based workflow
    if 'phase' not in st.session_state:
        st.session_state.phase = 'idea_input'
    if 'execution_result' not in st.session_state:
        st.session_state.execution_result = None
    if 'execution_metadata' not in st.session_state:
        st.session_state.execution_metadata = {}
    if 'consultation_result' not in st.session_state:
        st.session_state.consultation_result = None
    if 'strategy_options' not in st.session_state:
        st.session_state.strategy_options = None
    if 'chosen_strategy' not in st.session_state:
        st.session_state.chosen_strategy = None
    if 'user_selections' not in st.session_state:
        st.session_state.user_selections = {}
    if 'project_idea' not in st.session_state:
        st.session_state.project_idea = ""
    if 'uploaded_files_data' not in st.session_state:
        st.session_state.uploaded_files_data = []
    if 'deliverables_config' not in st.session_state:
        st.session_state.deliverables_config = {
            'code': True,
            'deployment': True,
            'docs': True,
            'tests': False
        }
    if 'process_type' not in st.session_state:
        st.session_state.process_type = 'Hierarchical'
    if 'api_keys_collected' not in st.session_state:
        st.session_state.api_keys_collected = {}
    
    # Show phase progress indicator
    phases = ['idea_input', 'strategy_selection', 'info_gathering', 'building', 'complete']
    phase_names = ['💡 Idea', '🎯 Strategy', '🔐 Config', '🚀 Building', '✅ Complete']
    current_phase_idx = phases.index(st.session_state.phase) if st.session_state.phase in phases else 0
    
    cols = st.columns(len(phases))
    for idx, (col, phase_name) in enumerate(zip(cols, phase_names)):
        with col:
            if idx < current_phase_idx:
                st.success(f"✓ {phase_name}")
            elif idx == current_phase_idx:
                st.info(f"▶ {phase_name}")
            else:
                st.caption(phase_name)
    
    st.divider()
    
    # ============================================================================
    # PHASE 1: IDEA INPUT
    # ============================================================================
    if st.session_state.phase == 'idea_input':
        # Styled title with gradient
        st.markdown('<h2 class="section-title">💡 Step 1: Describe Your Project</h2>', unsafe_allow_html=True)
        st.write("Tell us what you want to build, and our Strategy Consultant will create solution packages for you.")
        
        st.divider()
        
        # Enhanced project idea text area with custom styling
        st.markdown('<div class="project-idea-container">', unsafe_allow_html=True)
        idea = st.text_area(
            "Project Idea",
            value=st.session_state.project_idea,
            height=220,
            placeholder=(
                "Describe what you want to build or accomplish. "
                "Our Strategy Consultant will analyze your idea and present solution packages with tech stack options."
            ),
            help="Type or paste your project idea here, then click Plan Strategy below.",
            key="project_idea_input",
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # File upload section
        st.subheader("📚 Background Materials (Optional)")
        st.caption("Upload reference files for context (notebooks, docs, datasets, code, etc.)")
        
        uploaded_files = st.file_uploader(
            "Upload files",
            type=['ipynb', 'md', 'markdown', 'csv', 'txt', 'py', 'json'],
            accept_multiple_files=True,
            help="Upload Jupyter notebooks, markdown files, datasets, or code for context",
            label_visibility="collapsed",
            key="file_uploader_phase1"
        )
        
        # Parse and display uploaded files
        files_data = []
        if uploaded_files:
            st.write(f"**{len(uploaded_files)} file(s) uploaded:**")
            cols_files = st.columns(min(len(uploaded_files), 3))
            for idx, uploaded_file in enumerate(uploaded_files):
                parsed = parse_uploaded_file(uploaded_file)
                files_data.append(parsed)
                with cols_files[idx % 3]:
                    st.info(f"{parsed['icon']} **{parsed['name']}**\n\n{parsed['type']}")
        
        st.divider()
        
        # Prominent action button
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            st.markdown('<div class="launch-button">', unsafe_allow_html=True)
            if st.button(
                "🎯 Plan Strategy",
                type="primary",
                use_container_width=True,
                disabled=not bool(idea.strip()),
                help="Strategy Consultant will analyze your idea and create solution packages" if idea.strip() else "Enter a project idea to enable",
                key="plan_strategy_btn"
            ):
                st.markdown('</div>', unsafe_allow_html=True)
                if not OPENAI_KEY:
                    st.error("OpenAI API key missing. Add it to `.streamlit/secrets.toml` and reload the app.")
                else:
                    # Save to session state
                    st.session_state.project_idea = idea.strip()
                    st.session_state.uploaded_files_data = files_data
                    
                    # Load agents and find Strategy Consultant
                    saved_agents = load_agents()
                    if not saved_agents:
                        st.error("No agents are configured. Please add agents in **Agent Management**.")
                    else:
                        strategy_consultant = find_strategy_consultant(saved_agents)
                        if not strategy_consultant:
                            st.error("⚠️ Strategy Consultant Agent not found. Please create an agent with 'Strategy Consultant' in the role name.")
                        else:
                            # Build context from uploaded files
                            file_context = build_context_from_files(files_data)
                            
                            # Strategy task - analyze and generate solution packages
                            strategy_task_desc = (
                                "You are the Strategy Consultant analyzing the user's project idea.\n\n"
                                "🎯 YOUR ROLE:\n"
                                "Analyze the project idea and generate 2-3 SOLUTION PACKAGES (technology stack options) "
                                "that the user can choose from.\n\n"
                                "⚠️ CRITICAL UNDERSTANDING:\n"
                                "- If user says 'app' or 'application' → They want a WEB APPLICATION (React, Vue, Next.js, Flask, Django, etc.)\n"
                                "- NOT notebooks, NOT Jupyter, NOT Google Colab unless specifically requested\n"
                                "- Focus on DEPLOYABLE, USER-FACING applications\n"
                                "- Think about the ENTIRE solution: frontend + backend + database + deployment\n\n"
                                "📋 PROVIDE EXACTLY THIS FORMAT:\n\n"
                                "## Solution Packages\n\n"
                                "### Package A: [Descriptive Name]\n"
                                "**Technology Stack:**\n"
                                "- Frontend: [e.g., React with TypeScript]\n"
                                "- Backend: [e.g., Node.js with Express]\n"
                                "- Database: [e.g., PostgreSQL]\n"
                                "- Deployment: [e.g., Vercel (frontend) + Railway (backend)]\n\n"
                                "**Pros:**\n"
                                "- [Benefit 1]\n"
                                "- [Benefit 2]\n"
                                "- [Benefit 3]\n\n"
                                "**Cons:**\n"
                                "- [Limitation 1]\n"
                                "- [Limitation 2]\n\n"
                                "**Best For:** [Ideal use case/scenario]\n"
                                "**Estimated Build Time:** [X weeks]\n"
                                "**Cost:** [Free tier available / $X per month]\n\n"
                                "---\n\n"
                                "(Repeat for Package B and Package C)\n\n"
                                "## Recommendations\n\n"
                                "**🏆 Best Overall:** Package [A/B/C] - [Brief reason]\n"
                                "**⚡ Fastest to Build:** Package [X] - [Brief reason]\n"
                                "**💰 Most Cost-Effective:** Package [Y] - [Brief reason]\n"
                                "**🚀 Most Scalable:** Package [Z] - [Brief reason]\n\n"
                                "## What You'll Get\n\n"
                                "Regardless of which package you choose, you'll receive:\n"
                                "- ✅ Complete source code files (frontend + backend)\n"
                                "- ✅ Database schema and models\n"
                                "- ✅ API endpoints and routing\n"
                                "- ✅ Configuration files (package.json, requirements.txt, etc.)\n"
                                "- ✅ .gitignore configured for your stack\n"
                                "- ✅ Git initialization commands\n"
                                "- ✅ GitHub repository setup guide\n"
                                "- ✅ Deployment instructions for your chosen platform\n"
                                "- ✅ README with setup, run, and deploy steps\n"
                                "- ✅ Environment variables template\n\n"
                                f"💡 USER'S PROJECT IDEA:\n{idea.strip()}\n"
                                f"{file_context}\n\n"
                                "⚠️ REMEMBER:\n"
                                "- Present 2-3 COMPLETE solution packages\n"
                                "- Each package should be a FULL-STACK solution (not just frontend or just backend)\n"
                                "- Be specific about technologies (don't just say 'JavaScript', say 'React with TypeScript')\n"
                                "- Consider the user's skill level and project complexity\n"
                                "- Keep it concise but informative - user needs to make a decision quickly\n"
                            )
                            
                            try:
                                # Create Strategy Consultant agent
                                strategy_agent = build_crewai_agent(strategy_consultant)
                                
                                # Create strategy task
                                strategy_task = Task(
                                    description=strategy_task_desc,
                                    expected_output=(
                                        "2-3 complete solution packages in the specified format, each including:\n"
                                        "- Full technology stack (frontend, backend, database, deployment)\n"
                                        "- Detailed pros and cons\n"
                                        "- Best use case\n"
                                        "- Time and cost estimates\n"
                                        "Plus clear recommendations and a complete deliverables list."
                                    ),
                                    agent=strategy_agent
                                )
                                
                                # Create crew with ONLY the Strategy Consultant
                                strategy_crew = Crew(
                                    agents=[strategy_agent],
                                    tasks=[strategy_task],
                                    process=Process.sequential,
                                    verbose=True
                                )
                                
                                # Run the strategy session
                                with st.spinner("🎯 Strategy Consultant is analyzing your project and creating solution packages..."):
                                    strategy_result = strategy_crew.kickoff()
                                
                                # Store the strategy options
                                if hasattr(strategy_result, 'raw'):
                                    st.session_state.strategy_options = str(strategy_result.raw)
                                elif hasattr(strategy_result, 'output'):
                                    st.session_state.strategy_options = str(strategy_result.output)
                                else:
                                    st.session_state.strategy_options = str(strategy_result)
                                
                                # Move to strategy selection phase
                                st.session_state.phase = 'strategy_selection'
                                st.success("✅ Solution packages created! Review your options.")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Strategy planning failed: {e}")
                                import traceback
                                with st.expander("🔍 Error Details"):
                                    st.code(traceback.format_exc())
    
    # ============================================================================
    # PHASE 2: STRATEGY SELECTION
    # ============================================================================
    elif st.session_state.phase == 'strategy_selection' and st.session_state.strategy_options:
        st.subheader("🎯 Step 2: Choose Your Solution Package")
        st.write("Review the solution packages and select the one that best fits your needs.")
        
        # Display strategy options in an expander
        with st.expander("📦 Solution Packages Analysis", expanded=True):
            st.markdown(st.session_state.strategy_options)
        
        st.divider()
        
        # Package selection
        st.subheader("✅ Select Your Package")
        
        package_choice = st.radio(
            "Which solution package would you like to use?",
            options=["Package A", "Package B", "Package C", "Custom Solution"],
            index=0,
            help="Choose the package that best matches your requirements and constraints",
            key="package_selection_radio"
        )
        
        # If custom, allow specification
        custom_details = ""
        if package_choice == "Custom Solution":
            custom_details = st.text_area(
                "Describe your custom solution",
                placeholder="e.g., Next.js + Supabase + Vercel, or Django + React + PostgreSQL + AWS",
                height=100,
                key="custom_solution_input"
            )
            if custom_details:
                package_choice = f"Custom: {custom_details}"
        
        # Additional configuration
        st.divider()
        st.subheader("⚙️ Additional Configuration")
        
        col_config1, col_config2 = st.columns(2)
        
        with col_config1:
            additional_features = st.text_area(
                "Additional Features (Optional)",
                placeholder="e.g., Real-time updates, Email notifications, Analytics dashboard...",
                height=100,
                key="additional_features_input"
            )
        
        with col_config2:
            special_requirements = st.text_area(
                "Special Requirements (Optional)",
                placeholder="e.g., GDPR compliance, Mobile-first design, Offline support...",
                height=100,
                key="special_requirements_input"
            )
        
        st.divider()
        
        # Navigation buttons
        col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])
        
        with col_nav1:
            if st.button(
                "← Back to Idea", 
                help="Go back to edit your project idea", 
                key="back_to_idea_btn",
                use_container_width=True
            ):
                st.session_state.phase = 'idea_input'
                st.rerun()
        
        with col_nav3:
            if st.button(
                "Continue →", 
                type="primary", 
                help="Proceed to configure API keys", 
                key="continue_from_strategy_btn",
                use_container_width=True
            ):
                # Store the chosen strategy
                st.session_state.chosen_strategy = package_choice
                st.session_state.user_selections = {
                    'package': package_choice,
                    'additional_features': additional_features,
                    'special_requirements': special_requirements
                }
                
                # Move to info_gathering phase
                st.session_state.phase = 'info_gathering'
                st.success(f"✅ Selected: {package_choice}")
                st.rerun()
    
    # ============================================================================
    # PHASE 3: INFO GATHERING (API Keys & Secrets)
    # ============================================================================
    elif st.session_state.phase == 'info_gathering':
        st.subheader("🔐 Step 3: Configure API Keys & Secrets")
        st.write("Provide the necessary API keys for your chosen technology stack.")
        
        # Show selected package
        with st.expander("📦 Your Selected Package", expanded=False):
            st.info(f"**Package:** {st.session_state.chosen_strategy}")
            if st.session_state.user_selections.get('additional_features'):
                st.write(f"**Additional Features:** {st.session_state.user_selections['additional_features']}")
            if st.session_state.user_selections.get('special_requirements'):
                st.write(f"**Special Requirements:** {st.session_state.user_selections['special_requirements']}")
        
        st.divider()
        
        # Extract only the chosen package's content from all strategy options
        chosen_package_content = ""
        if st.session_state.strategy_options and st.session_state.chosen_strategy:
            full_text = st.session_state.strategy_options
            # Try to extract the specific package section
            package_marker = st.session_state.chosen_strategy  # e.g., "Package A", "Package B"
            if package_marker in full_text:
                # Find the start of this package
                start_idx = full_text.find(package_marker)
                # Find the next package marker or end of text
                next_package_markers = ["## Package", "### Package", "**Package"]
                end_idx = len(full_text)
                for marker in next_package_markers:
                    next_idx = full_text.find(marker, start_idx + len(package_marker))
                    if next_idx != -1 and next_idx < end_idx:
                        end_idx = next_idx
                chosen_package_content = full_text[start_idx:end_idx]
            else:
                # Fallback: use the full text (less precise)
                chosen_package_content = full_text
        
        # Use intelligent API key detection with only the selected package
        # Include user's additional features and requirements for more accurate detection
        additional_features = st.session_state.user_selections.get('additional_features', '')
        special_requirements = st.session_state.user_selections.get('special_requirements', '')
        
        required_keys, optional_keys = detect_api_keys_for_stack(
            st.session_state.chosen_strategy,
            chosen_package_content,
            additional_features,
            special_requirements
        )
        
        st.info("💡 **Tip:** These API keys are detected based on your selected package. You can skip this step and add them later during deployment. The agents will use these to configure your application properly.")
        
        # API Keys Input (non-form for better styling)
        st.markdown("### 🔑 Required API Keys")
        if required_keys:
            if 'api_key_inputs' not in st.session_state:
                st.session_state.api_key_inputs = {}
            
            for key_name, key_help in required_keys.items():
                st.session_state.api_key_inputs[key_name] = st.text_input(
                    f"🔴 {key_name} (Required)",
                    value=st.session_state.api_key_inputs.get(key_name, ""),
                    type="password",
                    help=key_help,
                    key=f"required_{key_name.replace(' ', '_').replace('/', '_').lower()}"
                )
        else:
            st.success("✅ No required API keys detected for your chosen stack!")
        
        st.markdown("### 🔓 Optional API Keys")
        st.caption("💡 Fill in only the API keys you want to use. The agents will create placeholder configuration for any skipped keys.")
        
        if optional_keys:
            if 'api_key_inputs' not in st.session_state:
                st.session_state.api_key_inputs = {}
            
            for key_name, key_help in optional_keys.items():
                st.session_state.api_key_inputs[key_name] = st.text_input(
                    f"⚪ {key_name} (Optional)",
                    value=st.session_state.api_key_inputs.get(key_name, ""),
                    type="password",
                    help=key_help,
                    key=f"optional_{key_name.replace(' ', '_').replace('/', '_').lower()}"
                )
        
        st.divider()
        
        # Navigation buttons with matching Phase 2 styling
        col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])
        
        with col_nav1:
            if st.button(
                "← Back to Strategy", 
                help="Return to package selection",
                key="back_to_strategy_from_config_btn",
                use_container_width=True
            ):
                st.session_state.phase = 'strategy_selection'
                st.rerun()
        
        with col_nav3:
            if st.button(
                "Continue →", 
                type="primary", 
                help="Proceed with building",
                key="continue_from_config_btn",
                use_container_width=True
            ):
                # Validate required keys
                if required_keys:
                    missing_keys = [k for k in required_keys.keys() if not st.session_state.api_key_inputs.get(k, "").strip()]
                    if missing_keys:
                        st.error(f"❌ Please fill in all required API keys: {', '.join(missing_keys)}")
                        st.stop()
                
                # Store all API keys
                api_keys = {}
                for key_name, value in st.session_state.api_key_inputs.items():
                    if value and value.strip():
                        api_keys[key_name] = value.strip()
                
                st.session_state.api_keys = api_keys
                
                # Move to building phase
                st.session_state.phase = 'building'
                st.success(f"✅ Configured {len(api_keys)} API key(s). Proceeding to build...")
                time.sleep(0.5)
                st.rerun()
        
        st.divider()
        
        # Skip option with centered button
        col_skip1, col_skip2, col_skip3 = st.columns([1, 1, 1])
        with col_skip2:
            if st.button("⏭️ Skip & Build", help="Skip API key configuration and proceed", key="skip_api_keys_btn", use_container_width=True):
                st.session_state.api_keys = {}
                st.session_state.phase = 'building'
                st.info("⏭️ Skipped API key configuration. You can add them during deployment.")
                time.sleep(0.5)
                st.rerun()
    
    # ============================================================================
    # PHASE 4: BUILDING
    # ============================================================================
    elif st.session_state.phase == 'building':
        st.subheader("🚀 Step 4: Building Your Project")
        st.write("Our AI development crew is assembling your complete deployment kit...")
        
        # Show build configuration
        with st.expander("📋 Build Configuration", expanded=False):
            st.write(f"**Project Idea:** {st.session_state.project_idea[:200]}...")
            st.write(f"**Chosen Strategy:** {st.session_state.chosen_strategy}")
            if st.session_state.user_selections.get('additional_features'):
                st.write(f"**Additional Features:** {st.session_state.user_selections['additional_features']}")
            if st.session_state.user_selections.get('special_requirements'):
                st.write(f"**Special Requirements:** {st.session_state.user_selections['special_requirements']}")
            api_keys_count = len(st.session_state.get('api_keys', {}))
            st.write(f"**API Keys Configured:** {api_keys_count}")
            files_count = len(st.session_state.uploaded_files_data)
            st.write(f"**Reference Files:** {files_count}")
        
        st.divider()
        
        # Load agents
        saved_agents = load_agents()
        if not saved_agents:
            st.error("❌ No agents configured. Please add agents in **Agent Management**.")
            if st.button("← Back to Config", key="back_from_building_no_agents"):
                st.session_state.phase = 'info_gathering'
                st.rerun()
            return
        
        # Find Orchestrator
        orchestrator_profile = find_orchestrator(saved_agents)
        if not orchestrator_profile:
            st.error("❌ Orchestrator Agent not found. Create an agent with 'Orchestrator' in the role name.")
            if st.button("← Back to Config", key="back_from_building_no_orchestrator"):
                st.session_state.phase = 'info_gathering'
                st.rerun()
            return
        
        # Build comprehensive context
        file_context = build_context_from_files(st.session_state.uploaded_files_data)
        
        # Format API keys for the task
        api_keys_context = ""
        if st.session_state.get('api_keys') and len(st.session_state.api_keys) > 0:
            api_keys_context = "\n\n## 🔑 Provided API Keys & Configuration\n\n"
            api_keys_context += "The user has provided the following API keys/configuration that **MUST** be integrated into the application:\n\n"
            
            api_key_list = []
            env_variables = []
            
            for key_name, key_value in st.session_state.api_keys.items():
                # Show key name and masked value for security
                masked_value = key_value[:4] + "..." + key_value[-4:] if len(key_value) > 8 else "***"
                api_key_list.append(f"- **{key_name}**: `{masked_value}` (provided by user)")
                
                # Convert to environment variable format
                env_var_name = key_name.upper().replace(' ', '_').replace('-', '_')
                env_variables.append(f"{env_var_name}={key_value}")
            
            api_keys_context += "\n".join(api_key_list)
            api_keys_context += "\n\n### 🔧 Integration Instructions\n\n"
            api_keys_context += "1. **Create `.env.example`** file with placeholder values for all keys\n"
            api_keys_context += "2. **Show how to use these keys** in your application code (e.g., environment variables, config files)\n"
            api_keys_context += "3. **Document each key's purpose** in the README\n"
            api_keys_context += "4. **Include setup instructions** in the deployment guide\n"
            api_keys_context += "\n**Environment Variables Format:**\n```\n"
            api_keys_context += "\n".join(env_variables[:3])  # Show first 3 as example
            if len(env_variables) > 3:
                api_keys_context += f"\n# ... and {len(env_variables) - 3} more\n"
            api_keys_context += "```\n"
        else:
            api_keys_context = "\n\n## 🔑 API Keys & Configuration\n\n"
            api_keys_context += "No API keys were provided by the user. You should:\n"
            api_keys_context += "1. Include a `.env.example` file with placeholder values for common services\n"
            api_keys_context += "2. Document which API keys the application needs in the README\n"
            api_keys_context += "3. Show where to obtain these keys in the setup guide\n"
        
        # Format additional requirements
        additional_context = ""
        if st.session_state.user_selections.get('additional_features'):
            additional_context += f"\n\n## ✨ Additional Features Requested (HIGH PRIORITY)\n\n{st.session_state.user_selections['additional_features']}\n\n"
            additional_context += "⚠️ **IMPORTANT**: These additional features MODIFY the base package. If they mention different technologies (e.g., MongoDB instead of PostgreSQL), you MUST use the user's specified technology.\n"
        if st.session_state.user_selections.get('special_requirements'):
            additional_context += f"\n\n## ⚙️ Special Requirements (MUST IMPLEMENT)\n\n{st.session_state.user_selections['special_requirements']}\n\n"
            additional_context += "⚠️ **IMPORTANT**: These requirements OVERRIDE package defaults. If there's a conflict between the package and user requirements, ALWAYS follow the user's requirements.\n"
        
        # Build the comprehensive task description
        orchestrator_task_desc = f"""
# 🎯 PROJECT EXECUTION MISSION

You are the Orchestrator leading a team of specialist agents to build a complete, production-ready application.

## 📝 USER'S PROJECT IDEA

{st.session_state.project_idea}

## 🏗️ CHOSEN TECHNOLOGY STRATEGY (BASE PACKAGE)

{st.session_state.chosen_strategy}

**IMPORTANT**: This is the BASE package. However, if the user has specified additional features or special requirements below that mention different technologies, YOU MUST use the user's specified technologies instead.

**Example**: If the package suggests PostgreSQL but the user's additional features mention "MongoDB", you MUST use MongoDB, not PostgreSQL.
{api_keys_context}
{additional_context}
{file_context}

## 🎯 TECHNOLOGY PRIORITY RULES

When there's a conflict between the base package and user input:
1. **User's Additional Features** = HIGHEST PRIORITY (overrides package)
2. **User's Special Requirements** = HIGHEST PRIORITY (overrides package)
3. **Base Package Strategy** = Use only if no conflicts with user input

**Examples of User Overrides**:
- Package says "PostgreSQL" + User says "use MongoDB" → USE MONGODB ✅
- Package says "Railway" + User says "deploy to Vercel" → USE VERCEL ✅
- Package says "REST API" + User says "use GraphQL" → USE GRAPHQL ✅

## 🎯 YOUR MISSION

Your mission is to deliver a complete **Deployment Kit** that includes:

### 1️⃣ Complete Source Code
- **Frontend**: All UI components, pages, layouts, styles
- **Backend**: API routes, controllers, services, middleware
- **Database**: Schema definitions, models, migrations
- **Configuration**: All config files (package.json, requirements.txt, tsconfig.json, etc.)
- **Environment Setup**: .env.example with all required variables

### 2️⃣ Essential Files
- `.gitignore` (properly configured for the chosen tech stack)
- `README.md` (comprehensive setup and usage guide)
- `package.json` or `requirements.txt` (with ALL dependencies and versions)
- Configuration files for the chosen framework/platform

### 3️⃣ Deployment Guide
- **Step-by-step deployment instructions** for the chosen platform
- **Environment variable configuration** guide
- **Database setup** instructions (if applicable)
- **Domain and DNS** setup (if applicable)
- **Troubleshooting** common issues

### 4️⃣ Documentation
- **Project overview** and architecture
- **API documentation** (if applicable)
- **Component documentation** (for complex UIs)
- **Development workflow** (how to run locally, test, build)

## 📋 CRITICAL REQUIREMENTS

⚠️ **COMPLETENESS**: This must be a COMPLETE application, not a tutorial or example. Every file needed to deploy and run the application must be included.

⚠️ **PRODUCTION-READY**: Code must be clean, well-commented, follow best practices, and be ready for production deployment.

⚠️ **TECH STACK ADHERENCE**: You MUST use the chosen technology strategy. Do not substitute with different technologies.

⚠️ **DEPLOYMENT-FOCUSED**: Provide exact, copy-paste-ready deployment instructions. Assume the user has basic technical knowledge but needs clear guidance.

⚠️ **API KEY INTEGRATION**: If API keys were provided, show exactly where and how to use them in the code and deployment.

## 🚫 ABSOLUTELY FORBIDDEN

❌ **NO PLACEHOLDER CODE**: Never use comments like "// logic goes here" or "# TODO: implement this"
❌ **NO BROKEN IMPORTS**: Every import statement MUST reference a file you actually generate
❌ **NO MISSING ENTRY POINTS**: Include index.js, index.html, main.py, or whatever the tech stack requires
❌ **NO EMPTY FUNCTIONS**: Every function must have actual implementation
❌ **NO MISSING DEPENDENCIES**: Every imported package must be in package.json/requirements.txt
❌ **NO SKELETON CODE**: Generate complete, working implementations

## ✅ MANDATORY VALIDATION CHECKLIST

Before submitting your output, you MUST verify every item:

### Code Validation
- [ ] Every import statement references a file that exists in your output
- [ ] Every function has actual implementation (no placeholders)
- [ ] All dependencies are listed in package.json/requirements.txt
- [ ] Entry point files exist (index.js, index.html, main.py, etc.)
- [ ] No "TODO" or "implement this" comments remain

### Completeness Validation
- [ ] Frontend has ALL required files (components, pages, styles, assets)
- [ ] Backend has ALL routes, controllers, models, middleware
- [ ] Database schemas and connections are complete
- [ ] CORS and security middleware are implemented
- [ ] Error handling is implemented throughout

### Documentation Validation
- [ ] README.md exists with complete setup instructions
- [ ] .env.example has ALL required variables with descriptions
- [ ] Deployment guide has step-by-step instructions
- [ ] API documentation is included (if applicable)
- [ ] Troubleshooting section covers common issues

### Integration Validation
- [ ] Frontend can connect to backend (CORS configured)
- [ ] Environment variables are properly used
- [ ] File structure matches imports
- [ ] Build commands will work
- [ ] Deploy commands are accurate for chosen platform

## 📊 EXPECTED OUTPUT STRUCTURE

Format your response EXACTLY like this:

```markdown
# 🏭 [PROJECT NAME] - Deployment Kit

## 📖 Project Overview
[2-3 paragraph description of what was built]

## 🏗️ Technology Stack
[List the exact technologies used, matching the chosen strategy]

## 📋 FILE MANIFEST

**Total Files Generated:** [NUMBER]

This deployment kit includes the following files:

### Frontend Files ([X] files)
- `frontend/public/index.html` (52 lines) - Main HTML template
- `frontend/src/index.js` (15 lines) - React entry point
- `frontend/src/App.js` (120 lines) - Main application component
- `frontend/src/components/[Name].js` ([X] lines) - [Description]
- `frontend/src/styles.css` (85 lines) - Application styles
- `frontend/package.json` (25 lines) - Frontend dependencies
[List EVERY frontend file with line count and purpose]

### Backend Files ([X] files)
- `backend/server.js` (65 lines) - Express server setup
- `backend/routes/api.js` (110 lines) - API route definitions
- `backend/controllers/[name]Controller.js` ([X] lines) - [Description]
- `backend/models/[Name].js` ([X] lines) - Database model
- `backend/middleware/[name].js` ([X] lines) - [Description]
- `backend/package.json` (20 lines) - Backend dependencies
[List EVERY backend file with line count and purpose]

### Configuration & Documentation ([X] files)
- `README.md` (180 lines) - Complete setup and usage guide
- `.env.example` (15 lines) - Environment variable template
- `.gitignore` (25 lines) - Git ignore rules
- `DEPLOYMENT.md` (120 lines) - Step-by-step deployment guide
[List EVERY config/doc file]

## 📁 Project Structure
```
/project-root
├── frontend/
│   ├── public/
│   │   ├── index.html ✅
│   │   └── manifest.json ✅
│   ├── src/
│   │   ├── components/
│   │   │   └── [Component].js ✅
│   │   ├── App.js ✅
│   │   ├── index.js ✅
│   │   └── styles.css ✅
│   └── package.json ✅
├── backend/
│   ├── routes/
│   │   └── api.js ✅
│   ├── controllers/
│   │   └── [name]Controller.js ✅
│   ├── models/
│   │   └── [Name].js ✅
│   ├── middleware/
│   │   └── [name].js ✅
│   ├── server.js ✅
│   └── package.json ✅
├── .gitignore ✅
├── .env.example ✅
├── README.md ✅
└── DEPLOYMENT.md ✅
```

## ✅ VALIDATION REPORT

Before delivery, I verified:
- ✅ All [X] imports are valid (no broken references)
- ✅ All [X] functions have complete implementations
- ✅ All [X] dependencies are listed in package.json/requirements.txt
- ✅ Entry point files exist and are configured correctly
- ✅ CORS is configured for frontend-backend communication
- ✅ Error handling is implemented
- ✅ README includes complete setup instructions
- ✅ No placeholder code or TODOs remain

## 💻 Source Code Files

### File: README.md
```markdown
[Complete README with setup, usage, deployment instructions]
```

### File: .gitignore
```
[Complete .gitignore content for the tech stack]
```

### File: .env.example
```
[ALL required environment variables with descriptions]
```

### File: frontend/public/index.html
```html
[Complete HTML template]
```

### File: frontend/src/index.js
```javascript
[Complete entry point]
```

### File: frontend/src/App.js
```javascript
[Complete, working code with NO placeholders]
```

### File: frontend/src/components/[ComponentName].js
```javascript
[Complete component implementation]
```

### File: frontend/src/styles.css
```css
[Complete styling]
```

### File: frontend/package.json
```json
[Complete dependency file with ALL packages and exact versions]
```

### File: backend/server.js
```javascript
[Complete server setup with middleware, CORS, error handling]
```

### File: backend/routes/api.js
```javascript
[Complete API routes with actual implementations]
```

### File: backend/controllers/[name]Controller.js
```javascript
[Complete controller with full business logic - NO placeholders]
```

### File: backend/models/[Name].js
```javascript
[Complete database model]
```

### File: backend/middleware/[name].js
```javascript
[Complete middleware implementation]
```

### File: backend/package.json
```json
[Complete dependency file with ALL packages and exact versions]
```

[Include EVERY file needed for the application to run]

## 🔐 Environment Configuration

### File: .env.example
```
[All required environment variables with descriptions]
```

## 🚀 Deployment Guide

### Prerequisites
- [List what user needs installed]

### Step 1: Clone and Setup
```bash
[Exact commands]
```

### Step 2: Configure Environment
[How to set up .env file with API keys]

### Step 3: Database Setup (if applicable)
[Database initialization steps]

### Step 4: Deploy to [Platform Name]
[Platform-specific deployment steps]

### Step 5: Verify Deployment
[How to test that it's working]

## 🧪 Local Development

### Install Dependencies
```bash
[Commands to install]
```

### Run Development Server
```bash
[Commands to run]
```

### Build for Production
```bash
[Commands to build]
```

## 🔧 Troubleshooting

[Common issues and solutions]

## 📚 Additional Resources

[Helpful links and documentation]
```

## ⚡ EXECUTION STRATEGY

1. **Analyze** the project idea and chosen strategy
2. **Design** the complete architecture
3. **Delegate** specific tasks to specialist agents (Frontend Coder, Backend Coder, etc.)
4. **Coordinate** the outputs from all agents
5. **Integrate** everything into a cohesive deployment kit
6. **Verify** completeness against the requirements

## ✅ FINAL QUALITY CHECKLIST

Before submitting, verify EVERY item below. An incomplete submission is REJECTED:

### ✅ Code Completeness (MANDATORY)
- [ ] Every file referenced in imports exists in your output
- [ ] Every function has complete implementation (no "// TODO" or "// implement this")
- [ ] Entry points exist: index.js, index.html, main.py, etc.
- [ ] All components/modules used are actually generated
- [ ] No broken references or missing files

### ✅ Dependencies & Configuration (MANDATORY)
- [ ] package.json/requirements.txt includes ALL dependencies with versions
- [ ] .gitignore is complete for the tech stack
- [ ] .env.example has ALL environment variables with descriptions
- [ ] Config files are complete (tsconfig.json, webpack.config.js, etc.)

### ✅ Functionality (MANDATORY)
- [ ] Core features are FULLY IMPLEMENTED (not placeholders)
- [ ] CORS is configured for frontend-backend communication
- [ ] Error handling is implemented
- [ ] Database connections work
- [ ] API routes have actual logic

### ✅ Documentation (MANDATORY)
- [ ] README.md includes: overview, setup, run, deploy instructions
- [ ] Deployment guide has step-by-step platform-specific instructions
- [ ] API documentation included (if applicable)
- [ ] Troubleshooting section included

### ✅ File Manifest (MANDATORY)
- [ ] File manifest lists ALL files with line counts
- [ ] Total file count is realistic (15+ files minimum for full-stack apps)
- [ ] All files in manifest are actually generated

---

## 🎯 FINAL REMINDER

**STOP AND VERIFY** before submitting:
1. Can this code run with just `npm install && npm start` or equivalent?
2. Are ALL imports valid (no missing files)?
3. Are ALL functions implemented (no placeholders)?
4. Is the README complete enough for someone to deploy this?
5. Did you generate at LEAST 15-20 files for a full-stack app?

**If you answer NO to any question above, DO NOT SUBMIT. Fix it first.**

The user is counting on you to deliver a COMPLETE, WORKING, DEPLOYABLE application. This is not a mockup, tutorial, or proof-of-concept - it's the real thing that must work immediately.
"""

        try:
            # Create Orchestrator agent
            orchestrator_agent = build_crewai_agent(orchestrator_profile)
            
            # Create worker agents (all agents except orchestrator)
            worker_agents = []
            for agent_profile in saved_agents:
                if agent_profile['id'] != orchestrator_profile['id']:  # Exclude orchestrator
                    worker_agent = build_crewai_agent(agent_profile)
                    worker_agents.append(worker_agent)
            
            # Create comprehensive task
            build_task = Task(
                description=orchestrator_task_desc,
                expected_output=(
                    "A complete Deployment Kit in markdown format containing:\n"
                    "1. All source code files (frontend, backend, database, config)\n"
                    "2. .gitignore file\n"
                    "3. Complete dependency files (package.json, requirements.txt, etc.)\n"
                    "4. Environment configuration (.env.example)\n"
                    "5. Step-by-step deployment guide for the chosen platform\n"
                    "6. README with project overview and local development instructions\n"
                    "7. Troubleshooting section\n\n"
                    "Format: Each file must be in markdown code blocks with clear file paths.\n"
                    f"Tech Stack: MUST match {st.session_state.chosen_strategy}\n"
                    "Quality: Production-ready, complete, and immediately deployable."
                ),
                agent=orchestrator_agent
            )
            
            # Create crew with hierarchical process
            # In hierarchical mode: manager_agent is separate, agents list contains only workers
            build_crew = Crew(
                agents=worker_agents if worker_agents else [orchestrator_agent],  # Use workers, or orchestrator if no workers
                tasks=[build_task],
                process=Process.hierarchical,
                manager_agent=orchestrator_agent,
                verbose=True
            )
            
            # Execute with progress tracking
            start_time = time.time()
            
            progress_container = st.container()
            with progress_container:
                st.markdown("### 🏗️ Building Your Application")
                progress_bar = st.progress(0, text="Initializing development crew...")
                status_text = st.empty()
                time_display = st.empty()
            
            status_messages = [
                "🎯 Orchestrator analyzing project requirements...",
                "📋 Breaking down into development tasks...",
                "👥 Delegating to specialist agents...",
                "💻 Frontend team building UI components...",
                "⚙️ Backend team implementing API logic...",
                "🗄️ Database team creating schemas...",
                "🔧 DevOps team preparing deployment configs...",
                "📝 Documentation team writing guides...",
                "✨ Integration team assembling components...",
                "🔍 QA team reviewing code quality...",
                "📦 Packaging deployment kit...",
            ]
            
            # Run crew in thread for progress animation
            import threading
            result_container = {"result": None, "error": None, "completed": False}
            
            def run_crew():
                try:
                    result_container["result"] = build_crew.kickoff()
                except Exception as e:
                    result_container["error"] = e
                finally:
                    result_container["completed"] = True
            
            thread = threading.Thread(target=run_crew)
            thread.start()
            
            # Animate progress
            progress = 0
            msg_index = 0
            while not result_container["completed"]:
                elapsed = int(time.time() - start_time)
                
                progress = min(95, progress + 1)
                progress_bar.progress(progress, text=status_messages[msg_index % len(status_messages)])
                
                status_text.info(f"⏱️ **Elapsed Time:** {format_time(elapsed)}")
                
                if elapsed % 5 == 0 and elapsed > 0:
                    msg_index += 1
                
                time.sleep(1)
            
            thread.join()
            
            # Check for errors
            if result_container["error"]:
                progress_container.empty()
                st.error(f"❌ Build failed: {result_container['error']}")
                with st.expander("🔍 Error Details"):
                    st.code(str(result_container['error']))
                
                if st.button("← Back to Config", key="back_from_building_error"):
                    st.session_state.phase = 'info_gathering'
                    st.rerun()
                return
            
            result = result_container["result"]
            
            # Complete progress
            progress_bar.progress(100, text="✅ Build Complete!")
            elapsed_time = int(time.time() - start_time)
            time_display.success(f"🎉 **Completed in {format_time(elapsed_time)}!**")
            time.sleep(2)
            progress_container.empty()
            
            # Extract and store result
            if hasattr(result, 'raw'):
                final_output = str(result.raw)
            elif hasattr(result, 'output'):
                final_output = str(result.output)
            else:
                final_output = str(result)
            
            # Store results in session state
            st.session_state.execution_result = final_output
            st.session_state.execution_metadata = {
                'elapsed_time': elapsed_time,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'idea': st.session_state.project_idea,
                'strategy': st.session_state.chosen_strategy,
                'api_keys_count': len(st.session_state.get('api_keys', {})),
                'files_count': len(st.session_state.uploaded_files_data)
            }
            
            # Move to complete phase
            st.session_state.phase = 'complete'
            st.success("✅ Your deployment kit is ready!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Build execution failed: {e}")
            import traceback
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())
            
            if st.button("← Back to Config", key="back_from_building_exception"):
                st.session_state.phase = 'info_gathering'
                st.rerun()
    
    # ============================================================================
    # PHASE 5: COMPLETE
    # ============================================================================
    elif st.session_state.phase == 'complete':
        # Styled title with gradient
        st.markdown('<h2 class="section-title">✅ Step 5: Your Project is Ready!</h2>', unsafe_allow_html=True)
        st.write("Your complete deployment kit has been generated and is ready for download.")
        
        # Show execution summary
        if st.session_state.execution_metadata:
            st.divider()
            st.caption("📊 **Build Summary** (Server time displayed - may differ from your local timezone)")
            cols = st.columns(5)
            with cols[0]:
                st.metric("⏱️ Build Time", format_time(st.session_state.execution_metadata.get('elapsed_time', 0)))
            with cols[1]:
                strategy_name = st.session_state.execution_metadata.get('strategy', 'N/A')
                # Show first 15 chars if too long
                display_strategy = strategy_name if len(strategy_name) <= 15 else strategy_name[:12] + "..."
                st.metric("📦 Strategy", display_strategy)
            with cols[2]:
                st.metric("🔑 API Keys", st.session_state.execution_metadata.get('api_keys_count', 0))
            with cols[3]:
                st.metric("📁 Ref Files", st.session_state.execution_metadata.get('files_count', 0))
            with cols[4]:
                # Show time only (server time may differ from local time)
                timestamp_str = st.session_state.execution_metadata.get('timestamp', 'N/A')
                time_only = timestamp_str.split(' ')[1] if ' ' in timestamp_str else timestamp_str
                st.metric("📅 Completed", time_only)
        
        st.divider()
        
        # Display the deployment kit in styled report container
        if st.session_state.execution_result:
            result_text = st.session_state.execution_result
            
            # Professional report container with gradient accent
            st.markdown("""
            <div class="report-container">
                <div class="report-header">
                    📦 Your Deployment Kit
                </div>
                <div class="report-content">
            """, unsafe_allow_html=True)
            
            st.markdown(result_text)
            
            st.markdown("""
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # Export options
            st.subheader("💾 Download Options")
            
            col_dl1, col_dl2, col_dl3 = st.columns(3)
            
            with col_dl1:
                st.download_button(
                    label="📄 Download Markdown",
                    data=result_text,
                    file_name=f"deployment_kit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    help="Download the complete deployment kit as markdown"
                )
            
            with col_dl2:
                # Extract code files and create ZIP
                code_files = extract_code_files_from_result(result_text)
                if code_files:
                    project_name = st.session_state.project_idea[:30].replace(' ', '_')
                    zip_data = create_project_zip(code_files, project_name)
                    st.download_button(
                        label=f"📦 Download ZIP ({len(code_files)} files)",
                        data=zip_data,
                        file_name=f"{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        use_container_width=True,
                        help="Download all source code files as a ZIP archive"
                    )
                else:
                    st.button("📦 No Files Detected", disabled=True, use_container_width=True)
            
            with col_dl3:
                st.download_button(
                    label="📝 Download Text",
                    data=result_text,
                    file_name=f"deployment_kit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    help="Download as plain text file"
                )
            
            # Local folder save option
            if code_files:
                st.divider()
                st.caption("💻 **Save to Local Folder** (optional - works only when running locally)")
                
                col_path, col_save = st.columns([3, 1])
                with col_path:
                    folder_path = st.text_input(
                        "Folder Path",
                        placeholder="e.g., C:\\Projects\\my-app or /Users/name/projects/my-app",
                        help="Absolute path where project files should be saved",
                        label_visibility="collapsed",
                        key="local_folder_path_input"
                    )
                
                with col_save:
                    if st.button("💾 Save Files", disabled=not folder_path, use_container_width=True, key="save_to_local_btn"):
                        success, result_data = write_files_to_directory(code_files, folder_path)
                        if success:
                            st.success(f"✅ Saved {len(result_data)} files to {folder_path}!")
                            with st.expander("📁 Files created"):
                                for file in result_data:
                                    st.code(file)
                        else:
                            st.error(f"❌ Failed to save files: {result_data}")
        
        st.divider()
        
        # Action buttons
        col_action1, col_action2, col_action3 = st.columns([1, 1, 1])
        
        with col_action2:
            st.markdown('<div class="primary-action-button">', unsafe_allow_html=True)
            if st.button("🔄 Start New Project", type="primary", use_container_width=True, key="start_new_project_btn"):
                st.markdown('</div>', unsafe_allow_html=True)
                # Reset all session state
                st.session_state.phase = 'idea_input'
                st.session_state.project_idea = ""
                st.session_state.uploaded_files_data = []
                st.session_state.strategy_options = None
                st.session_state.chosen_strategy = None
                st.session_state.user_selections = {}
                st.session_state.api_keys = {}
                st.session_state.api_key_inputs = {}
                st.session_state.execution_result = None
                st.session_state.execution_metadata = {}
                st.success("🔄 Session reset! Starting fresh...")
                st.rerun()
    
    # ============================================================================
    # FALLBACK: Unknown Phase Handler
    # ============================================================================
    else:
        # This should not be reached with proper phase management
        st.warning(f"⚠️ Unknown phase: {st.session_state.phase}")
        if st.button("🔄 Reset to Start"):
            st.session_state.phase = 'idea_input'
            st.rerun()

# ------------------------------------------------------------------------------
# Main Router
# ------------------------------------------------------------------------------
if page == "Agent Management":
    agent_management_page()
else:
    project_execution_page()
