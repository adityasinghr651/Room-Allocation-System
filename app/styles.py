"""Global visual design system: premium dark console aesthetics, glassmorphic cards,
responsive CSS grid room geometry, and print-ready seating chart styles.
"""
import streamlit as st


def apply_styles():
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,400;0,500;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    
    :root {
        --bg-root: #06090f;
        --bg-panel: rgba(13, 20, 36, 0.85);
        --bg-panel-hover: rgba(18, 28, 50, 0.95);
        --border-subtle: #1e293b;
        --border-focus: #3b82f6;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --accent-blue: #3b82f6;
        --accent-purple: #8b5cf6;
        --accent-emerald: #10b981;
        --accent-amber: #f59e0b;
        --accent-rose: #f43f5e;
        --accent-cyan: #06b6d4;
    }

    /* Core Page Reset */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 85% -5%, rgba(59, 130, 246, 0.15) 0%, transparent 45%),
                    radial-gradient(circle at 10% 40%, rgba(139, 92, 246, 0.08) 0%, transparent 40%),
                    var(--bg-root);
        color: var(--text-primary);
    }

    /* Streamlit Top Header & Footer adjustments */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    footer {
        visibility: hidden !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #090e1a 0%, #05080e 100%) !important;
        border-right: 1px solid var(--border-subtle) !important;
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] * {
        color: var(--text-primary);
    }

    /* Typography & Hierarchy */
    h1, h2, h3, h4 {
        letter-spacing: -0.03em;
        font-weight: 700;
        color: #ffffff;
    }
    .eyebrow {
        color: #60a5fa;
        font-family: 'DM Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 0.35rem;
    }
    .mono {
        font-family: 'DM Mono', monospace;
    }

    /* Modern Glassmorphic Panels */
    .panel {
        background: var(--bg-panel);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 1.25rem;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
        transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1),
                    border-color 0.2s ease,
                    box-shadow 0.2s ease;
        margin-bottom: 1rem;
    }
    .panel:hover {
        border-color: #334155;
        box-shadow: 0 16px 36px -12px rgba(30, 58, 138, 0.25);
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(10, 15, 30, 0.8) 100%);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 1.1rem 1.25rem;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: var(--accent-blue);
    }
    .metric-card.emerald::before { background: var(--accent-emerald); }
    .metric-card.purple::before { background: var(--accent-purple); }
    .metric-card.amber::before { background: var(--accent-amber); }
    .metric-card.cyan::before { background: var(--accent-cyan); }

    .metric-label {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-family: 'DM Mono', monospace;
        font-weight: 500;
    }
    .metric-value {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        color: #ffffff;
        margin: 0.2rem 0;
        line-height: 1.1;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: var(--text-secondary);
    }

    /* Badge Pills */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-family: 'DM Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 9999px;
        text-transform: uppercase;
    }
    .badge.blue { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.35); }
    .badge.emerald { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.35); }
    .badge.amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.35); }
    .badge.purple { background: rgba(139, 92, 246, 0.15); color: #a78bfa; border: 1px solid rgba(139, 92, 246, 0.35); }
    .badge.rose { background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.35); }

    /* Physical Seating Arrangement Layout */
    .room-container {
        background: #090e18;
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 2rem;
    }
    .board-indicator {
        text-align: center;
        background: #111827;
        border: 1px dashed #374151;
        border-radius: 6px;
        padding: 6px;
        color: #9ca3af;
        font-family: 'DM Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        margin-bottom: 1.5rem;
    }
    .grid-bench {
        display: grid;
        gap: 12px;
        justify-content: center;
    }
    .desk-cell {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 10px 8px;
        text-align: center;
        min-width: 100px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        transition: all 0.18s ease;
        position: relative;
    }
    .desk-cell:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
        border-color: #3b82f6;
    }
    .desk-cell.occupied {
        background: #131c31;
        border-color: #2b3956;
    }
    .desk-cell.empty {
        background: #0a0f1d;
        border: 1px dashed #202b40;
        opacity: 0.65;
    }
    .desk-cell.accessible {
        border-color: #0d9488 !important;
        box-shadow: inset 0 0 12px rgba(13, 148, 136, 0.2);
    }
    .desk-cell.my-seat {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(139, 92, 246, 0.3) 100%) !important;
        border: 2px solid #60a5fa !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.6) !important;
        animation: pulse-border 2s infinite ease-in-out;
    }
    @keyframes pulse-border {
        0%, 100% { box-shadow: 0 0 14px rgba(59, 130, 246, 0.4); }
        50% { box-shadow: 0 0 26px rgba(59, 130, 246, 0.85); }
    }

    .seat-title {
        font-size: 0.68rem;
        font-family: 'DM Mono', monospace;
        color: #94a3b8;
    }
    .seat-student-id {
        font-size: 0.88rem;
        font-weight: 700;
        color: #ffffff;
        margin: 2px 0;
    }
    .seat-group {
        display: inline-block;
        font-size: 0.65rem;
        font-weight: 700;
        border-radius: 4px;
        padding: 1px 6px;
        font-family: 'DM Mono', monospace;
    }

    /* Group Color Themes */
    .grp-A { background: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); }
    .grp-B { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.4); }
    .grp-C { background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.4); }
    .grp-D { background: rgba(139, 92, 246, 0.2); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.4); }
    .grp-E { background: rgba(244, 63, 94, 0.2); color: #fda4af; border: 1px solid rgba(244, 63, 94, 0.4); }
    .grp-default { background: rgba(148, 163, 184, 0.2); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.4); }

    /* Buttons */
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
        transition: all 0.16s ease !important;
        border: 1px solid #334155 !important;
        background: #0f172a !important;
        color: #f8fafc !important;
    }
    div.stButton > button:hover {
        border-color: #60a5fa !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25) !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        border: 1px solid #3b82f6 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5) !important;
    }

    /* Printable Chart Styles (Targeted for printing/PDF saving) */
    @media print {
        body, .stApp {
            background: #ffffff !important;
            color: #000000 !important;
        }
        [data-testid="stSidebar"], header, footer, .stButton, div.stDownloadButton {
            display: none !important;
        }
        .room-container {
            border: 2px solid #000 !important;
            page-break-after: always;
            background: #fff !important;
            color: #000 !important;
            padding: 10px !important;
        }
        .desk-cell {
            background: #fff !important;
            border: 1px solid #000 !important;
            color: #000 !important;
            box-shadow: none !important;
        }
        .seat-student-id, .seat-title {
            color: #000 !important;
        }
        .board-indicator {
            background: #eee !important;
            border: 1px solid #000 !important;
            color: #000 !important;
        }
    }
    </style>""", unsafe_allow_html=True)
