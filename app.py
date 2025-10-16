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

/* Dropdown Menu Container */
[data-baseweb="menu"],
[data-baseweb="popover"],
ul[role="listbox"] {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: var(--shadow-lg) !important;
  padding: var(--spacing-sm) !important;
}

/* Dropdown Options */
[role="option"],
li[role="option"],
[data-baseweb="menu-item"] {
  background: transparent !important;
  color: var(--text-primary) !important;
  padding: var(--spacing-md) var(--spacing-lg) !important;
  border-radius: var(--radius-sm) !important;
  margin: var(--spacing-xs) 0 !important;
  transition: all var(--transition-fast) !important;
}

[role="option"]:hover,
li[role="option"]:hover,
[data-baseweb="menu-item"]:hover {
  background: var(--bg-tertiary) !important;
  color: var(--text-primary) !important;
}

/* Selected Option */
[role="option"][aria-selected="true"],
li[role="option"][aria-selected="true"] {
  background: var(--bg-tertiary) !important;
  color: var(--accent-primary) !important;
  font-weight: 600 !important;
}

/* Selectbox Label */
.stSelectbox label {
  color: var(--text-primary) !important;
  font-weight: 500 !important;
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
}
[data-testid="stMetricValue"],
[data-testid="stMetric"] [data-testid="stMarkdownContainer"] {
  color: var(--text) !important;
}
[data-testid="stMetricDelta"] {
  color: var(--text) !important;
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
            if st.button("← Back to Idea", help="Go back to edit your project idea", key="back_to_idea_btn"):
                st.session_state.phase = 'idea_input'
                st.rerun()
        
        with col_nav3:
            if st.button("Continue →", type="primary", help="Proceed to gather API keys", key="continue_from_strategy_btn"):
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
        
        # Detect required API keys based on chosen strategy
        chosen_strategy_lower = str(st.session_state.chosen_strategy).lower()
        strategy_options_lower = str(st.session_state.strategy_options).lower()
        
        required_keys = {}
        optional_keys = {}
        
        # Deployment platforms
        if "netlify" in chosen_strategy_lower or "netlify" in strategy_options_lower:
            optional_keys["Netlify API Token"] = "Get from: app.netlify.com → User Settings → Applications → Personal access tokens"
        if "vercel" in chosen_strategy_lower or "vercel" in strategy_options_lower:
            optional_keys["Vercel Token"] = "Get from: vercel.com/account/tokens"
        if "railway" in chosen_strategy_lower or "railway" in strategy_options_lower:
            optional_keys["Railway Token"] = "Get from: railway.app/account/tokens"
        if "render" in chosen_strategy_lower or "render" in strategy_options_lower:
            optional_keys["Render API Key"] = "Get from: dashboard.render.com → Account Settings → API Keys"
        if "heroku" in chosen_strategy_lower or "heroku" in strategy_options_lower:
            optional_keys["Heroku API Key"] = "Get from: dashboard.heroku.com/account → API Key"
        
        # Databases
        if "supabase" in chosen_strategy_lower:
            required_keys["Supabase URL"] = "Your Supabase project URL"
            required_keys["Supabase Anon Key"] = "Your Supabase anon/public key"
        if "firebase" in chosen_strategy_lower:
            required_keys["Firebase Config"] = "Your Firebase configuration object (JSON)"
        if "mongodb" in chosen_strategy_lower and "atlas" in chosen_strategy_lower:
            optional_keys["MongoDB Atlas URI"] = "Your MongoDB connection string"
        if "postgres" in chosen_strategy_lower or "postgresql" in chosen_strategy_lower:
            optional_keys["Database URL"] = "PostgreSQL connection string (e.g., postgresql://user:pass@host:5432/db)"
        
        # Services
        if "openai" in chosen_strategy_lower or "gpt" in chosen_strategy_lower:
            optional_keys["OpenAI API Key"] = "Get from: platform.openai.com/api-keys"
        if "stripe" in chosen_strategy_lower:
            optional_keys["Stripe API Key"] = "Get from: dashboard.stripe.com/apikeys"
            optional_keys["Stripe Webhook Secret"] = "For webhook verification"
        if "sendgrid" in chosen_strategy_lower or "email" in chosen_strategy_lower:
            optional_keys["SendGrid API Key"] = "For email sending functionality"
        if "twilio" in chosen_strategy_lower:
            optional_keys["Twilio Account SID"] = "Your Twilio account SID"
            optional_keys["Twilio Auth Token"] = "Your Twilio auth token"
        
        # Always useful
        optional_keys["GitHub Token"] = "For automated deployment and CI/CD (get from: github.com/settings/tokens)"
        
        st.info("💡 **Tip:** You can skip this step and add API keys later during deployment. These are optional for the code generation phase.")
        
        # API Keys Form
        with st.form("api_keys_form", clear_on_submit=False):
            st.markdown("### 🔑 Required API Keys")
            if required_keys:
                required_values = {}
                for key_name, key_help in required_keys.items():
                    required_values[key_name] = st.text_input(
                        f"🔴 {key_name} (Required)",
                        type="password",
                        help=key_help,
                        key=f"required_{key_name.replace(' ', '_').lower()}"
                    )
            else:
                st.success("✅ No required API keys detected for your chosen stack!")
            
            st.markdown("### 🔓 Optional API Keys")
            if optional_keys:
                optional_values = {}
                for key_name, key_help in optional_keys.items():
                    optional_values[key_name] = st.text_input(
                        f"⚪ {key_name} (Optional)",
                        type="password",
                        help=key_help,
                        key=f"optional_{key_name.replace(' ', '_').lower()}"
                    )
            
            st.divider()
            
            # Form buttons
            col_form1, col_form2, col_form3 = st.columns([1, 1, 1])
            
            with col_form1:
                back_button = st.form_submit_button("← Back", help="Return to package selection")
            
            with col_form3:
                submit_button = st.form_submit_button("Continue to Build →", type="primary", help="Proceed with building")
            
            # Handle form submission
            if back_button:
                st.session_state.phase = 'strategy_selection'
                st.rerun()
            
            if submit_button:
                # Validate required keys
                if required_keys:
                    all_required_filled = all(required_values.get(k, "").strip() for k in required_keys.keys())
                    if not all_required_filled:
                        st.error("❌ Please fill in all required API keys before continuing.")
                        st.stop()
                
                # Store all API keys
                api_keys = {}
                
                if required_keys:
                    for key_name, value in required_values.items():
                        if value.strip():
                            api_keys[key_name] = value.strip()
                
                if optional_keys:
                    for key_name, value in optional_values.items():
                        if value.strip():
                            api_keys[key_name] = value.strip()
                
                st.session_state.api_keys = api_keys
                
                # Move to building phase
                st.session_state.phase = 'building'
                st.success(f"✅ Configured {len(api_keys)} API key(s). Proceeding to build...")
                st.rerun()
        
        st.divider()
        
        # Skip option outside the form
        col_skip1, col_skip2, col_skip3 = st.columns([1, 1, 1])
        with col_skip2:
            if st.button("⏭️ Skip & Build", help="Skip API key configuration and proceed", key="skip_api_keys_btn"):
                st.session_state.api_keys = {}
                st.session_state.phase = 'building'
                st.info("Skipped API key configuration. You can add them during deployment.")
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
        if st.session_state.get('api_keys'):
            api_keys_context = "\n\n## 🔑 Provided API Keys & Configuration\n\n"
            api_keys_context += "The user has provided the following API keys/configuration:\n\n"
            for key_name, key_value in st.session_state.api_keys.items():
                # Show key name and masked value for security
                masked_value = key_value[:4] + "..." + key_value[-4:] if len(key_value) > 8 else "***"
                api_keys_context += f"- **{key_name}**: `{masked_value}` (available for use)\n"
            api_keys_context += "\n⚠️ **IMPORTANT**: Include setup instructions for these API keys in your deployment guide.\n"
            api_keys_context += "Create environment variable templates and configuration examples.\n"
        else:
            api_keys_context = "\n\n## 🔑 API Keys\n\nNo API keys provided. Include placeholder configuration in your deployment guide.\n"
        
        # Format additional requirements
        additional_context = ""
        if st.session_state.user_selections.get('additional_features'):
            additional_context += f"\n\n## ✨ Additional Features Requested\n\n{st.session_state.user_selections['additional_features']}\n"
        if st.session_state.user_selections.get('special_requirements'):
            additional_context += f"\n\n## ⚙️ Special Requirements\n\n{st.session_state.user_selections['special_requirements']}\n"
        
        # Build the comprehensive task description
        orchestrator_task_desc = f"""
# 🎯 PROJECT EXECUTION MISSION

You are the Orchestrator leading a team of specialist agents to build a complete, production-ready application.

## 📝 USER'S PROJECT IDEA

{st.session_state.project_idea}

## 🏗️ CHOSEN TECHNOLOGY STRATEGY

{st.session_state.chosen_strategy}

**You MUST implement the project using this exact technology stack.** Do not deviate from the chosen strategy unless technically impossible.
{api_keys_context}
{additional_context}
{file_context}

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

## 📊 EXPECTED OUTPUT STRUCTURE

Format your response EXACTLY like this:

```markdown
# 🏭 [PROJECT NAME] - Deployment Kit

## 📖 Project Overview
[2-3 paragraph description of what was built]

## 🏗️ Technology Stack
[List the exact technologies used, matching the chosen strategy]

## 📁 Project Structure
```
/project-root
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── backend/
│   ├── routes/
│   ├── models/
│   └── server.js
├── .gitignore
├── README.md
└── .env.example
```

## 💻 Source Code Files

### File: .gitignore
```
[Complete .gitignore content]
```

### File: package.json (or requirements.txt)
```json
[Complete dependency file with all packages and versions]
```

### File: frontend/src/App.js (or equivalent)
```javascript
[Complete, working code]
```

[Include ALL necessary files - frontend, backend, config, etc.]

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

## ✅ QUALITY CHECKLIST

Before submitting, verify:
- [ ] All source code files are included and complete
- [ ] Dependencies are listed with specific versions
- [ ] .gitignore is properly configured
- [ ] Environment variables are documented
- [ ] Deployment guide is step-by-step and clear
- [ ] Code follows best practices for the chosen stack
- [ ] README is comprehensive
- [ ] Local development instructions are included

---

**Remember**: The user is counting on you to deliver a COMPLETE, WORKING, DEPLOYABLE application. This is not a mockup or proof-of-concept - it's the real thing.
"""

        try:
            # Create Orchestrator agent
            orchestrator_agent = build_crewai_agent(orchestrator_profile)
            
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
            
            # Create crew (Orchestrator can delegate to other agents)
            build_crew = Crew(
                agents=[orchestrator_agent],
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
            cols = st.columns(5)
            with cols[0]:
                st.metric("⏱️ Build Time", format_time(st.session_state.execution_metadata.get('elapsed_time', 0)))
            with cols[1]:
                st.metric("📦 Strategy", st.session_state.execution_metadata.get('strategy', 'N/A')[:20] + "...")
            with cols[2]:
                st.metric("🔑 API Keys", st.session_state.execution_metadata.get('api_keys_count', 0))
            with cols[3]:
                st.metric("📁 Ref Files", st.session_state.execution_metadata.get('files_count', 0))
            with cols[4]:
                st.metric("📅 Completed", st.session_state.execution_metadata.get('timestamp', 'N/A').split(' ')[1])
        
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
                st.session_state.execution_result = None
                st.session_state.execution_metadata = {}
                st.success("🔄 Session reset! Starting fresh...")
                st.rerun()
    
    # ============================================================================
    # FALLBACK: Legacy code for backward compatibility
    # ============================================================================
    else:
        # This should not be reached with proper phase management
        st.warning(f"⚠️ Unknown phase: {st.session_state.phase}")
        if st.button("🔄 Reset to Start"):
            st.session_state.phase = 'idea_input'
            st.rerun()
    
    # Legacy code below - kept for backward compatibility with building phase
    # This section runs for all phases (including else fallback)
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
    
    st.divider()
    
    # Smart button based on workflow phase
    col1, col2, col3 = st.columns([2, 1, 2])
    
    # Determine button text and action
    if not st.session_state.consultation_result:
        # Phase 1: Get consultation
        button_text = "💡 Get Consultation"
        button_help = "Orchestrator will analyze your idea and present options"
        workflow_action = "consultation"
    else:
        # Phase 2: Build with selections
        button_text = "🚀 Build Project"
        button_help = "Full crew will build code based on your selections"
        workflow_action = "building"
    
    with col2:
        launch = st.button(
            button_text,
            type="primary",
            use_container_width=True,
            disabled=not bool(idea.strip()),
            help=button_help if idea.strip() else "Enter a project idea to enable"
        )
    
    # Action buttons
    if st.session_state.consultation_result:
        with col1:
            if st.button("🔄 Start Over", help="Clear consultation and start fresh"):
                st.session_state.consultation_result = None
                st.session_state.user_selections = {}
                st.session_state.workflow_phase = None
                st.rerun()
    
    # Clear results button
    if st.session_state.execution_result is not None:
        with col3:
            if st.button("🗑️ Clear Results", help="Clear previous execution results"):
                st.session_state.execution_result = None
                st.session_state.execution_metadata = {}
                st.rerun()
    
    if launch:
        if not OPENAI_KEY:
            st.error("OpenAI API key missing. Add it to `.streamlit/secrets.toml` and reload the app.")
            return

        saved_agents = load_agents()
        if not saved_agents:
            st.error("No agents are configured. Please add agents in **Agent Management**.")
            return
        
        # Determine which workflow phase we're in
        st.session_state.workflow_phase = workflow_action
        
        # PHASE 1: CONSULTATION - Just Orchestrator presents options
        if workflow_action == "consultation":
            # Find orchestrator
            orchestrator_profile = find_orchestrator(saved_agents)
            if not orchestrator_profile:
                st.error("Consultation mode requires an Orchestrator Agent. Create an agent with 'Orchestrator' in the role name.")
                return
            
            file_context = build_context_from_files(files_data)
            
            # Consultation task - analyze and present options
            consultation_task_desc = (
                "You are the Orchestrator consulting with the user BEFORE the project build begins.\n\n"
                "🎯 YOUR ROLE:\n"
                "Analyze the user's project idea and present 2-3 SPECIFIC OPTIONS for them to choose from.\n\n"
                "⚠️ CRITICAL UNDERSTANDING:\n"
                "- If user says 'app' or 'application' → They want a WEB APPLICATION (React, Vue, Flask, etc.)\n"
                "- NOT notebooks, NOT Jupyter, NOT Google Colab unless specifically requested\n"
                "- Focus on deployable, user-facing applications\n\n"
                "📋 PROVIDE EXACTLY THIS FORMAT:\n\n"
                "## Technology Stack Options\n\n"
                "**Option A: [Stack Name]**\n"
                "- Stack: [e.g., React + Node.js + PostgreSQL]\n"
                "- Pros: [2-3 key benefits]\n"
                "- Cons: [1-2 limitations]\n"
                "- Best for: [ideal use case]\n"
                "- Platform: [Recommended deployment platform]\n"
                "- Version Control: Git + GitHub\n\n"
                "(Repeat for Options B and C)\n\n"
                "## Quick Recommendations\n\n"
                "**Recommended:** Option [A/B/C] because [brief reason]\n"
                "**Fastest to build:** Option [X]\n"
                "**Most cost-effective:** Option [Y]\n"
                "**Estimated time:** [X] weeks\n\n"
                "## GitHub & Version Control Setup\n\n"
                "For all options, you'll get:\n"
                "- `.gitignore` file (configured for your tech stack)\n"
                "- Git initialization commands\n"
                "- GitHub repository creation guide\n"
                "- Push commands to upload your code\n"
                "- Branch strategy recommendations\n\n"
                "## Complete Deliverables\n\n"
                "Full application including:\n"
                "- **Frontend**: Complete UI components and pages\n"
                "- **Backend**: API endpoints, database models, auth (if needed)\n"
                "- **Config**: All necessary config files (package.json, etc.)\n"
                "- **Deployment**: Platform-specific deploy instructions\n"
                "- **Documentation**: README, setup guide, API docs\n"
                "- **Git Setup**: .gitignore + commands to push to GitHub\n\n"
                f"💡 USER'S PROJECT IDEA:\n{idea.strip()}\n"
                f"{file_context}\n\n"
                "⚠️ REMEMBER: Present 2-3 clear options. User will SELECT one, then the team builds it.\n"
                "Keep it concise - user needs to make a quick decision, not read an essay."
            )
            
            try:
                orch_agent = build_crewai_agent(orchestrator_profile)
                consult_task = Task(
                    description=consultation_task_desc,
                    expected_output=(
                        "Concise consultation with 2-3 technology stack options, each including:\n"
                        "- Tech stack details\n"
                        "- Pros and cons\n"
                        "- Recommended deployment platform\n"
                        "- Version control (Git/GitHub) mention\n"
                        "Plus quick recommendations and what deliverables user will receive (including Git setup, .gitignore, push commands)."
                    ),
                    agent=orch_agent
                )
                
                consult_crew = Crew(
                    agents=[orch_agent],
                    tasks=[consult_task],
                    process=Process.sequential,
                    verbose=True
                )
                
                with st.spinner("🤔 Orchestrator is analyzing your project..."):
                    consultation_result = consult_crew.kickoff()
                
                # Store consultation result
                if hasattr(consultation_result, 'raw'):
                    st.session_state.consultation_result = str(consultation_result.raw)
                elif hasattr(consultation_result, 'output'):
                    st.session_state.consultation_result = str(consultation_result.output)
                else:
                    st.session_state.consultation_result = str(consultation_result)
                
                st.success("✅ Consultation complete! Review the options above and make your selections.")
                st.rerun()
                return
                
            except Exception as e:
                st.error(f"❌ Consultation failed: {e}")
                return
        
        # PHASE 2: BUILDING - Full crew builds code based on user selections
        
        # Get selected platform from user selections or use default
        selected_platform = st.session_state.user_selections.get('platform', 'As recommended')

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
            
            # Add user selections to context
            user_selections_context = ""
            if st.session_state.user_selections and st.session_state.user_selections.get('tech'):
                sels = st.session_state.user_selections
                user_selections_context = (
                    "\n\n" + "="*80 + "\n"
                    "🎯 USER'S SELECTED PREFERENCES (MUST BE FOLLOWED)\n"
                    "="*80 + "\n"
                    f"Technology Stack: {sels.get('tech', 'Not specified')}\n"
                    f"Deployment Platform: {sels.get('platform', 'As recommended')}\n"
                    f"Additional Requirements: {sels.get('additional', 'None')}\n"
                    "="*80 + "\n\n"
                    "⚠️⚠️⚠️ CRITICAL REQUIREMENT ⚠️⚠️⚠️\n"
                    "You MUST use the technology stack the user selected above.\n"
                    "If user selected 'Option A: MEAN Stack' → Use MongoDB, Express, React, Node.js\n"
                    "If user selected 'Option B: Python Flask' → Use Python, Flask\n"
                    "If user selected 'Option C: Vue + Firebase' → Use Vue.js, Firebase\n\n"
                    "DO NOT use Python/Pandas/Jupyter/ML libraries unless that's what the user selected!\n"
                    "DO NOT ignore the user's selection!\n"
                    "DO NOT substitute with a different tech stack!\n\n"
                    "The user already made their choice. Your job is to implement THAT choice.\n"
                    "="*80 + "\n\n"
                )
            
            # Build deliverables requirements
            deliverables_req = []
            if include_code:
                deliverables_req.append("- Complete, ready-to-use source code files with proper structure")
                deliverables_req.append("- .gitignore file (properly configured for the tech stack)")
            if include_deployment:
                deliverables_req.append("- Deployment configuration files (package.json, requirements.txt, Dockerfile, etc.)")
                deliverables_req.append(f"- Platform-specific deployment guide for {selected_platform}")
                deliverables_req.append("- Git repository setup instructions")
                deliverables_req.append("- Commands to initialize Git and push to GitHub")
            if include_docs:
                deliverables_req.append("- README.md with setup instructions AND Git/GitHub workflow")
                deliverables_req.append("- API documentation if applicable")
                deliverables_req.append("- Architecture documentation")
            if include_tests:
                deliverables_req.append("- Unit test files")
                deliverables_req.append("- Testing documentation")
            
            deliverables_section = "\n".join(deliverables_req) if deliverables_req else "- High-level plan and recommendations"
            
            # Single high-level task for orchestrator
            task_description = (
                "You are the Orchestrator for this project. Your job is to coordinate the team to build ACTUAL, WORKING CODE and deliverables.\n\n"
                "🎯 PRIMARY OBJECTIVE:\n"
                "Analyze the user's idea, create an execution plan, delegate tasks, and ensure the team delivers CONCRETE ARTIFACTS.\n\n"
                "⚠️ CRITICAL: This is NOT about writing reports or documentation about what could be built. "
                "The team must produce ACTUAL SOURCE CODE FILES that can be immediately used.\n\n"
                f"📦 REQUIRED DELIVERABLES:\n{deliverables_section}\n\n"
                f"🚀 TARGET DEPLOYMENT PLATFORM: {selected_platform}\n"
                "Ensure all code, configurations, and instructions are optimized for this platform.\n\n"
                "📋 DELIVERABLE FORMAT:\n"
                "Present each code file clearly with:\n"
                "1. Filename (e.g., `src/App.js`, `requirements.txt`)\n"
                "2. Complete file contents in properly formatted code blocks\n"
                "3. Brief explanation of what the file does\n\n"
                f"💡 USER'S PROJECT IDEA:\n{idea.strip()}\n"
                f"{file_context}"
                f"{user_selections_context}\n\n"
                "🔧 EXECUTION GUIDELINES:\n"
                "1. Build a COMPLETE, PRODUCTION-READY web application\n"
                "2. Include ALL layers: Frontend UI + Backend API + Database (if needed)\n"
                "3. Generate EVERY file needed to run the app locally\n"
                "4. Include .gitignore configured for the tech stack\n"
                f"5. Provide Git setup + GitHub push commands\n"
                f"6. Include deployment instructions for {selected_platform}\n"
                "7. Make it immediately runnable - no missing pieces!\n\n"
                "⚠️ COMPLETENESS CHECKLIST:\n"
                "✅ Frontend: Pages, components, styles, routing\n"
                "✅ Backend: API routes, controllers, models, middleware\n"
                "✅ Config: package.json/requirements.txt with ALL dependencies\n"
                "✅ Git: .gitignore + init commands + GitHub push guide\n"
                "✅ Deploy: Step-by-step deployment instructions\n"
                "✅ Docs: README with setup, run, and deploy instructions\n\n"
                "📊 FINAL OUTPUT STRUCTURE:\n"
                "## Project Overview\n"
                "[Brief description]\n\n"
                "## Architecture\n"
                "[System design]\n\n"
                "## Source Code Files\n"
                "### File: .gitignore\n"
                "```\n"
                "[Complete .gitignore]\n"
                "```\n\n"
                "### File: [config file]\n"
                "```\n"
                "[Complete config]\n"
                "```\n\n"
                "[ALL frontend + backend files]\n\n"
                "## Git & GitHub Setup\n"
                "```bash\n"
                "git init\n"
                "git add .\n"
                "git commit -m \"Initial commit\"\n"
                "# Create repo on GitHub, then:\n"
                "git remote add origin https://github.com/username/repo.git\n"
                "git push -u origin main\n"
                "```\n\n"
                "## Deployment Guide\n"
                f"[Complete {selected_platform} deployment steps]\n\n"
                "## Running Locally\n"
                "[Commands to install dependencies and run]"
            )
            # Build tech-specific expected output
            if st.session_state.user_selections.get('tech'):
                tech_hint = f"\n\nREMINDER: User selected {st.session_state.user_selections.get('tech')}. All code MUST match this selection!"
            else:
                tech_hint = ""
            
            tasks.append(Task(
                description=task_description,
                expected_output=(
                    "Complete source code files and deployment artifacts in this format:\n\n"
                    "## Project Overview\n"
                    "[2-3 sentence description]\n\n"
                    "## Tech Stack Used\n"
                    "[MUST match user's selected option]\n\n"
                    "## Source Code Files\n\n"
                    "### File: [appropriate config file for tech stack]\n"
                    "```[language]\n"
                    "[COMPLETE file contents]\n"
                    "```\n\n"
                    "### File: [main application files]\n"
                    "```[language]\n"
                    "[COMPLETE working code]\n"
                    "```\n\n"
                    "[Include ALL necessary files for the SELECTED tech stack]\n\n"
                    "## Git Setup\n"
                    "[.gitignore and Git commands]\n\n"
                    "## Deployment Instructions\n"
                    f"[Step-by-step guide for {selected_platform}]\n\n"
                    "## Setup & Run\n"
                    "[Commands to install and run locally]"
                    f"{tech_hint}"
                ),
                agent=build_crewai_agent(orchestrator_profile),
            ))
            crew_process = Process.hierarchical
            manager_agent = build_crewai_agent(orchestrator_profile)
            
        elif process_type == "Sequential":
            # Build context from uploaded files
            file_context = build_context_from_files(files_data)
            
            # Build deliverables requirements
            deliverables_req = []
            if include_code:
                deliverables_req.append("- Complete source code files")
            if include_deployment:
                deliverables_req.append(f"- Deployment configs for {selected_platform}")
            if include_docs:
                deliverables_req.append("- Documentation files")
            if include_tests:
                deliverables_req.append("- Test files")
            
            deliverables_section = "\n".join(deliverables_req) if deliverables_req else "- Analysis and recommendations"
            
            # Sequential: Create a task for each agent in order
            crew_process = Process.sequential
            for agent_profile in saved_agents:
                task_desc = (
                    f"As the {agent_profile.get('role', 'Agent')}, contribute your specialized expertise to build ACTUAL WORKING CODE.\n\n"
                    f"⚠️ CRITICAL: Generate concrete code files, not just descriptions or plans.\n\n"
                    f"📦 REQUIRED DELIVERABLES:\n{deliverables_section}\n\n"
                    f"🚀 TARGET PLATFORM: {selected_platform}\n\n"
                    f"💡 PROJECT IDEA: {idea.strip()}\n\n"
                    f"🎯 YOUR GOAL: {agent_profile.get('goal', 'Contribute to the project')}\n\n"
                    f"Build upon previous work if available. Provide actual code in properly formatted code blocks with filenames.\n"
                    f"{file_context}"
                )
                tasks.append(Task(
                    description=task_desc,
                    expected_output=(
                        f"Concrete code files and configurations from {agent_profile.get('role', 'Agent')}. "
                        "Must include actual source code in properly formatted code blocks with filenames, "
                        "NOT descriptions or plans. Format: ### File: filename.ext\n```language\n[code]\n```"
                    ),
                    agent=build_crewai_agent(agent_profile),
                ))
                
        else:  # Consensus
            # Build context from uploaded files
            file_context = build_context_from_files(files_data)
            
            # Build deliverables requirements
            deliverables_req = []
            if include_code:
                deliverables_req.append("- Source code files")
            if include_deployment:
                deliverables_req.append(f"- Deployment setup for {selected_platform}")
            if include_docs:
                deliverables_req.append("- Documentation")
            if include_tests:
                deliverables_req.append("- Tests")
            
            deliverables_section = "\n".join(deliverables_req) if deliverables_req else "- Collaborative solution"
            
            # Consensus: Each agent contributes to collaborative solution
            crew_process = Process.sequential
            for agent_profile in saved_agents:
                task_desc = (
                    f"As the {agent_profile.get('role', 'Agent')}, collaborate to build REAL, WORKING CODE.\n\n"
                    f"⚠️ IMPORTANT: Generate actual code files with proper structure, not just plans.\n\n"
                    f"📦 DELIVERABLES NEEDED:\n{deliverables_section}\n\n"
                    f"🚀 PLATFORM: {selected_platform}\n\n"
                    f"💡 PROJECT: {idea.strip()}\n\n"
                    f"🎯 GOAL: {agent_profile.get('goal', 'Contribute collaboratively')}\n\n"
                    f"Review previous contributions, add your perspective, and work toward a consensus solution with concrete code.\n"
                    f"{file_context}"
                )
                tasks.append(Task(
                    description=task_desc,
                    expected_output=(
                        f"Working code files from {agent_profile.get('role', 'Agent')} contributing to consensus. "
                        "Must provide actual source code in code blocks with filenames, NOT analysis or recommendations. "
                        "Format: ### File: filename.ext\n```language\n[complete code]\n```"
                    ),
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
                'num_files': len(files_data),
                'platform': selected_platform,
                'deliverables': {
                    'code': include_code,
                    'deployment': include_deployment,
                    'docs': include_docs,
                    'tests': include_tests
                }
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
        info_cols = st.columns(5)
        with info_cols[0]:
            st.metric("⏱️ Duration", format_time(metadata.get('elapsed_time', 0)))
        with info_cols[1]:
            st.metric("🎯 Process", metadata.get('process_type', 'N/A'))
        with info_cols[2]:
            st.metric("🚀 Platform", metadata.get('platform', 'N/A').split(' ')[0])
        with info_cols[3]:
            st.metric("📅 Executed", metadata.get('timestamp', 'N/A'))
        with info_cols[4]:
            st.metric("📁 Files Used", metadata.get('num_files', 0))
        
        # Show deliverables checkboxes
        delivs = metadata.get('deliverables', {})
        if delivs:
            deliv_info = []
            if delivs.get('code'): deliv_info.append("✅ Code")
            if delivs.get('deployment'): deliv_info.append("📋 Deploy")
            if delivs.get('docs'): deliv_info.append("📚 Docs")
            if delivs.get('tests'): deliv_info.append("🧪 Tests")
            if deliv_info:
                st.caption(f"**Requested:** {' • '.join(deliv_info)}")
        
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
            
            # Extract code files from result
            code_files = extract_code_files_from_result(report_text)
            
            st.subheader("💾 Export Options")
            
            # Download buttons
            col_dl1, col_dl2, col_dl3 = st.columns(3)
            with col_dl1:
                st.download_button(
                    label="📄 Download Report (MD)",
                    data=report_text,
                    file_name=f"ai_factory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with col_dl2:
                if code_files:
                    project_name = metadata.get('idea', 'project')[:30].replace(' ', '_')
                    zip_data = create_project_zip(code_files, project_name)
                    st.download_button(
                        label=f"📦 Download ZIP ({len(code_files)} files)",
                        data=zip_data,
                        file_name=f"{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )
                else:
                    st.button("📦 No Files Detected", disabled=True, use_container_width=True)
            
            with col_dl3:
                st.download_button(
                    label="📝 Download Text",
                    data=report_text,
                    file_name=f"ai_factory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
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
                        label_visibility="collapsed"
                    )
                
                with col_save:
                    if st.button("💾 Save Files", disabled=not folder_path, use_container_width=True):
                        success, result_data = write_files_to_directory(code_files, folder_path)
                        if success:
                            st.success(f"✅ Saved {len(result_data)} files to {folder_path}!")
                            with st.expander("📁 Files created"):
                                for file in result_data:
                                    st.code(file)
                        else:
                            st.error(f"❌ Failed to save files: {result_data}")
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
        
        # Display platform options in consistent, compact cards
        for idx, platform in enumerate(project_analysis["platforms"]):
            with st.container():
                col_platform, col_info = st.columns([5, 3])
                
                with col_platform:
                    # Platform name with top pick badge
                    if idx == 0:
                        st.markdown(f"**{platform['name']}** ⭐ _Top Pick_")
                    else:
                        st.markdown(f"**{platform['name']}**")
                    
                    st.caption(f"{platform['best_for']}")
                    
                    # Compact pros/cons on same line
                    pros_text = " • ".join(platform["pros"][:2])
                    cons_text = " • ".join(platform["cons"][:1])
                    st.caption(f"✅ {pros_text}")
                    if cons_text:
                        st.caption(f"⚠️ {cons_text}")
                
                with col_info:
                    # Compact info display without large metric cards
                    st.caption("**Cost**")
                    st.write(f"{platform['cost']}")
                    st.caption(f"_{platform['tier_details']}_")
                    
                    st.caption("**Difficulty**")
                    st.write(f"{platform['difficulty']}")
                
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

