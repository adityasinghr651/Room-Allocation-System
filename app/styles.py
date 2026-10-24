"""Vercel and Render inspired design system:
Minimalist monochrome palette, sharp typography, subtle 1px borders, generous whitespace,
quiet animations, and strict absence of emojis or decorative clutter.
"""
import streamlit as st


def apply_styles():
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg-root: #000000;
        --bg-subtle: #08080a;
        --bg-card: #0c0c0e;
        --bg-card-hover: #121216;
        --border-subtle: #1c1c21;
        --border-hover: #2e2e36;
        --border-focus: #52525b;
        
        --text-primary: #ededed;
        --text-secondary: #a1a1aa;
        --text-muted: #52525b;
        --text-faint: #3f3f46;

        --accent-white: #ffffff;
        --accent-emerald: #10b981;
        --accent-emerald-bg: rgba(16, 185, 129, 0.08);
        --accent-emerald-border: rgba(16, 185, 129, 0.22);

        --accent-rose: #ef4444;
        --accent-rose-bg: rgba(239, 68, 68, 0.08);
        --accent-rose-border: rgba(239, 68, 68, 0.22);

        --accent-blue: #3b82f6;
        --accent-blue-bg: rgba(59, 130, 246, 0.08);
        --accent-blue-border: rgba(59, 130, 246, 0.22);
    }

    /* Core Reset */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        letter-spacing: -0.015em;
        color: var(--text-primary);
        background-color: var(--bg-root);
    }

    .stApp {
        background-color: var(--bg-root);
        background-image: radial-gradient(circle at 50% 0%, #111116 0%, #000000 65%);
        color: var(--text-primary);
    }

    /* Streamlit Defaults Cleanup */
    header[data-testid="stHeader"] {
        background: rgba(0, 0, 0, 0.6) !important;
        backdrop-filter: blur(12px) !important;
        border-bottom: 1px solid var(--border-subtle);
    }
    footer {
        display: none !important;
    }
    [data-testid="stToolbar"] {
        right: 1.5rem !important;
    }

    /* Sidebar - Vercel / Render Console Style */
    [data-testid="stSidebar"] {
        background-color: #050507 !important;
        border-right: 1px solid var(--border-subtle) !important;
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] * {
        color: var(--text-primary);
    }
    [data-testid="stSidebar"] hr {
        border-color: var(--border-subtle) !important;
        margin: 1.25rem 0 !important;
    }

    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.035em;
        font-weight: 600;
        color: #ffffff;
        margin-top: 0;
    }
    h1 {
        font-size: 2.1rem;
        line-height: 1.15;
    }
    h2 {
        font-size: 1.45rem;
        line-height: 1.25;
    }
    h3 {
        font-size: 1.15rem;
        line-height: 1.35;
    }

    .mono {
        font-family: 'Geist Mono', monospace;
    }
    .eyebrow {
        font-family: 'Geist Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--text-muted);
        font-weight: 500;
        margin-bottom: 0.35rem;
    }

    /* Cards & Containers - Render/Vercel Style */
    .card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 1.25rem;
        transition: border-color 0.15s ease, background-color 0.15s ease;
        margin-bottom: 1rem;
    }
    .card:hover {
        border-color: var(--border-hover);
        background: var(--bg-card-hover);
    }

    /* Metric Tiles */
    .stat-tile {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 1.1rem 1.25rem;
        transition: border-color 0.15s ease;
    }
    .stat-tile:hover {
        border-color: var(--border-hover);
    }
    .stat-tile .label {
        font-family: 'Geist Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-muted);
        font-weight: 500;
        margin-bottom: 0.35rem;
    }
    .stat-tile .value {
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.04em;
        color: #ffffff;
        line-height: 1.1;
    }
    .stat-tile .meta {
        font-size: 0.78rem;
        color: var(--text-secondary);
        margin-top: 0.35rem;
    }

    /* Minimal Status Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-family: 'Geist Mono', monospace;
        font-size: 0.68rem;
        font-weight: 500;
        padding: 3px 8px;
        border-radius: 4px;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-neutral {
        background: #141418;
        border: 1px solid #27272e;
        color: #a1a1aa;
    }
    .badge-success {
        background: var(--accent-emerald-bg);
        border: 1px solid var(--accent-emerald-border);
        color: #34d399;
    }
    .badge-error {
        background: var(--accent-rose-bg);
        border: 1px solid var(--accent-rose-border);
        color: #f87171;
    }
    .badge-active {
        background: var(--accent-blue-bg);
        border: 1px solid var(--accent-blue-border);
        color: #60a5fa;
    }

    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;
    }
    .status-dot.green { background-color: var(--accent-emerald); }
    .status-dot.red { background-color: var(--accent-rose); }
    .status-dot.blue { background-color: var(--accent-blue); }
    .status-dot.muted { background-color: var(--text-muted); }

    /* Button System - Vercel High Contrast Buttons */
    div.stButton > button {
        border-radius: 6px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        letter-spacing: -0.01em !important;
        padding: 0.45rem 1rem !important;
        transition: all 0.15s ease !important;
        border: 1px solid #27272a !important;
        background: #0e0e11 !important;
        color: #f4f4f5 !important;
    }
    div.stButton > button:hover {
        border-color: #52525b !important;
        background: #18181b !important;
        color: #ffffff !important;
    }
    div.stButton > button:active {
        transform: scale(0.985);
    }

    div.stButton > button[kind="primary"] {
        background: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #ffffff !important;
        font-weight: 600 !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: #e4e4e7 !important;
        border-color: #e4e4e7 !important;
    }

    /* Streamlit Inputs & Forms */
    input[type="text"], input[type="password"], [data-baseweb="input"] input {
        background: #09090b !important;
        border: 1px solid #27272a !important;
        border-radius: 6px !important;
        color: #f4f4f5 !important;
        font-size: 0.88rem !important;
        transition: border-color 0.15s ease !important;
    }
    input[type="text"]:focus, input[type="password"]:focus, [data-baseweb="input"] input:focus {
        border-color: #71717a !important;
        box-shadow: none !important;
    }
    [data-baseweb="select"] {
        background: #09090b !important;
        border-radius: 6px !important;
    }

    /* Dataframes & Tables */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border-subtle) !important;
        border-radius: 6px !important;
        background: #08080a !important;
    }

    /* Radio & Navigation in Sidebar */
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding: 6px 10px !important;
        border-radius: 6px !important;
        margin-bottom: 2px !important;
        font-size: 0.85rem !important;
        transition: background-color 0.12s ease !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background-color: #121216 !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid var(--border-subtle) !important;
        gap: 1.5rem !important;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.6rem 0.2rem !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: var(--text-muted) !important;
        border-bottom: 2px solid transparent !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-primary) !important;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        border-bottom-color: #ffffff !important;
        background-color: transparent !important;
    }

    /* Blueprint Seating Arrangement Layout */
    .blueprint-room {
        background: #060608;
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 2rem;
    }
    .blueprint-board {
        text-align: center;
        background: #09090c;
        border: 1px solid #1a1a20;
        border-radius: 4px;
        padding: 7px;
        color: #71717a;
        font-family: 'Geist Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
    }
    .blueprint-grid {
        display: grid;
        gap: 10px;
        justify-content: center;
    }
    .blueprint-desk {
        background: #0c0c0f;
        border: 1px solid #202026;
        border-radius: 6px;
        padding: 10px 8px;
        text-align: center;
        min-width: 105px;
        transition: border-color 0.15s ease, transform 0.15s ease;
    }
    .blueprint-desk:hover {
        border-color: #52525b;
        transform: translateY(-1px);
    }
    .blueprint-desk.occupied {
        background: #0f0f13;
        border-color: #272730;
    }
    .blueprint-desk.empty {
        background: #060608;
        border: 1px dashed #1a1a20;
        opacity: 0.55;
    }
    .blueprint-desk.accessible {
        border-color: #10b981 !important;
    }
    .blueprint-desk.target-seat {
        background: #141419 !important;
        border: 2px solid #ffffff !important;
        box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.08) !important;
    }

    .desk-coord {
        font-family: 'Geist Mono', monospace;
        font-size: 0.65rem;
        color: #71717a;
        margin-bottom: 3px;
    }
    .desk-id {
        font-family: 'Geist Mono', monospace;
        font-size: 0.88rem;
        font-weight: 600;
        color: #ffffff;
    }
    .desk-name {
        font-size: 0.72rem;
        color: #a1a1aa;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin: 2px 0;
    }
    .desk-group-tag {
        display: inline-block;
        font-family: 'Geist Mono', monospace;
        font-size: 0.62rem;
        padding: 1px 5px;
        border-radius: 3px;
        background: #18181c;
        border: 1px solid #282830;
        color: #d4d4d8;
        margin-top: 3px;
    }

    /* Print View */
    @media print {
        body, .stApp {
            background: #ffffff !important;
            color: #000000 !important;
        }
        [data-testid="stSidebar"], header, footer, .stButton, div.stDownloadButton {
            display: none !important;
        }
        .blueprint-room {
            border: 1px solid #000 !important;
            page-break-after: always;
            background: #fff !important;
            color: #000 !important;
        }
        .blueprint-desk {
            background: #fff !important;
            border: 1px solid #000 !important;
            color: #000 !important;
        }
        .desk-coord, .desk-id, .desk-name {
            color: #000 !important;
        }
    }
    </style>""", unsafe_allow_html=True)
