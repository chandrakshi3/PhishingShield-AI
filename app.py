import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from analyzer import analyze_message
from transcriber import transcribe_audio, SUPPORTED_FORMATS
from utils import (
    SAMPLE_MESSAGES, RISK_COLORS, RISK_EMOJI,
    highlight_text_html, format_file_size
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PhishingShield AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif;
    background-color: #0d1117;
    color: #e6edf3;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #161b22 !important;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] .stMarkdown, 
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption {
    color: #8b949e !important;
}
[data-testid="stSidebar"] h3 {
    color: #58a6ff !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 12px 16px !important;
}
[data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 12px !important; }
[data-testid="stMetricValue"] { color: #e6edf3 !important; font-size: 22px !important; font-weight: 700 !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #161b22;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid #30363d;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    font-size: 14px;
    color: #8b949e;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: #1f6feb !important;
    color: white !important;
}

/* Buttons */
.stButton > button {
    background: #1f6feb;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 14px;
    padding: 10px 28px;
    transition: all 0.2s;
    letter-spacing: 0.02em;
}
.stButton > button:hover {
    background: #388bfd;
    border: none;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(31,111,235,0.4);
}

/* Secondary button (Clear) */
.stButton > button[kind="secondary"] {
    background: #21262d;
    color: #8b949e;
    border: 1px solid #30363d;
}

/* Text area */
.stTextArea textarea {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 10px !important;
    color: #e6edf3 !important;
    font-size: 14px !important;
    line-height: 1.7 !important;
}
.stTextArea textarea:focus {
    border-color: #1f6feb !important;
    box-shadow: 0 0 0 3px rgba(31,111,235,0.15) !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: #161b22;
    border: 2px dashed #30363d;
    border-radius: 12px;
    padding: 20px;
}
[data-testid="stFileUploader"]:hover {
    border-color: #1f6feb;
}

/* Expander */
details {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 10px !important;
}

/* Progress bar */
.stProgress > div > div {
    background: #1f6feb !important;
    border-radius: 999px !important;
}

/* Alerts */
.stAlert {
    border-radius: 10px !important;
    border-left-width: 4px !important;
    font-weight: 500;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #30363d;
    border-radius: 10px;
    overflow: hidden;
}

/* Divider */
hr { border-color: #30363d !important; }

/* Caption */
.stCaption { color: #6e7681 !important; }

/* Plotly charts background */
.js-plotly-plot .plotly .bg { fill: transparent !important; }

/* Flag badges */
.flag-badge {
    display: inline-block;
    background: rgba(248,81,73,0.1);
    color: #ff7b72;
    border: 1px solid rgba(248,81,73,0.3);
    border-radius: 6px;
    padding: 4px 12px;
    margin: 3px;
    font-size: 13px;
    font-weight: 500;
}

/* Section headers */
.section-header {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #8b949e;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #30363d;
}

/* Stat card in sidebar */
.stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: #0d1117;
    border-radius: 8px;
    margin: 4px 0;
    border: 1px solid #21262d;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def hex_to_rgba(hex_color: str, alpha: float = 0.2) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#8b949e", size=12),
)


# ── Session state ─────────────────────────────────────────────────────────────
if "stats" not in st.session_state:
    st.session_state.stats = {"total": 0, "safe": 0, "suspicious": 0, "high_risk": 0}


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:20px 0 12px 0">
      <div style="font-size:18px;font-weight:700;color:#e6edf3">🛡️ PhishingShield</div>
      <div style="font-size:11px;color:#6e7681;margin-top:3px">AI-Powered Scam Detection</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### ⚙️ Settings")
    language_hint = st.selectbox(
        "Audio language hint",
        ["Auto-detect", "Hindi", "Marathi", "Tamil", "Telugu", "Bengali", "Gujarati", "English"],
        help="Helps Whisper transcribe regional languages more accurately"
    )

    st.divider()
    st.markdown("### 📊 Session Stats")

    s = st.session_state.stats
    stats_html = f"""
    <div class="stat-row">
      <span style="color:#8b949e;font-size:13px">Total Scans</span>
      <span style="color:#e6edf3;font-weight:700;font-size:15px">{s['total']}</span>
    </div>
    <div class="stat-row">
      <span style="color:#ff7b72;font-size:13px">🚨 High Risk</span>
      <span style="color:#ff7b72;font-weight:700;font-size:15px">{s['high_risk']}</span>
    </div>
    <div class="stat-row">
      <span style="color:#e3b341;font-size:13px">⚠️ Suspicious</span>
      <span style="color:#e3b341;font-weight:700;font-size:15px">{s['suspicious']}</span>
    </div>
    <div class="stat-row">
      <span style="color:#3fb950;font-size:13px">✅ Safe</span>
      <span style="color:#3fb950;font-weight:700;font-size:15px">{s['safe']}</span>
    </div>
    """
    st.markdown(stats_html, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🧪 Test Samples")
    for label in SAMPLE_MESSAGES:
        if st.button(label, key=f"s_{label}", use_container_width=True):
            st.session_state["load_sample"] = SAMPLE_MESSAGES[label]

    st.divider()
    st.markdown("""
    <div style="font-size:11px;color:#6e7681;line-height:1.8">
      Groq LLaMA 3.3 · Whisper Large v3<br>
      Multilingual · Real-time Analysis
    </div>
    """, unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#161b22 0%,#0d1117 100%);
            border:1px solid #30363d;border-radius:16px;
            padding:32px 36px;margin-bottom:28px;
            box-shadow:0 4px 24px rgba(0,0,0,0.4)">
  <div style="display:flex;align-items:center;gap:16px">
    <div style="font-size:42px;line-height:1">🛡️</div>
    <div>
      <div style="font-size:28px;font-weight:700;color:#e6edf3;letter-spacing:-0.5px">
        PhishingShield AI
      </div>
      <div style="font-size:13px;color:#8b949e;margin-top:5px;line-height:1.6">
        Enterprise-grade multilingual scam &amp; phishing detection &nbsp;·&nbsp;
        <span style="color:#58a6ff">Hindi</span> &nbsp;·&nbsp;
        <span style="color:#58a6ff">Marathi</span> &nbsp;·&nbsp;
        <span style="color:#58a6ff">Tamil</span> &nbsp;·&nbsp;
        <span style="color:#58a6ff">Telugu</span> &nbsp;·&nbsp;
        <span style="color:#58a6ff">English</span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Render result ─────────────────────────────────────────────────────────────
def render_result(result: dict):
    risk  = result.get("risk_level", "suspicious")
    prob  = result.get("scam_probability", 0)
    color = RISK_COLORS[risk]
    emoji = RISK_EMOJI[risk]
    rec   = result.get("recommendation", "")

    # Update stats
    st.session_state.stats["total"] += 1
    st.session_state.stats[risk] = st.session_state.stats.get(risk, 0) + 1

    # ── Risk banner ──
    BANNER = {
        "high_risk":  ("rgba(248,81,73,0.1)",  "#ff7b72", "#ff7b72", "30363d",
                       "🚨 HIGH RISK DETECTED", "This message exhibits strong scam indicators. Do not respond or share any information."),
        "suspicious": ("rgba(227,179,65,0.1)",  "#e3b341", "#e3b341", "30363d",
                       "⚠️ SUSPICIOUS CONTENT", "This message has potential red flags. Verify through official channels before taking action."),
        "safe":       ("rgba(63,185,80,0.1)",   "#3fb950", "#3fb950", "30363d",
                       "✅ MESSAGE APPEARS SAFE", "No significant scam indicators detected in this message."),
    }
    bg, border_c, text_c, _, title, subtitle = BANNER[risk]
    st.markdown(f"""
    <div style="background:{bg};border:1px solid {border_c};border-left:4px solid {border_c};
                border-radius:10px;padding:16px 20px;margin:16px 0">
      <div style="font-size:15px;font-weight:700;color:{text_c};margin-bottom:4px">{title}</div>
      <div style="font-size:13px;color:#8b949e">{subtitle}</div>
      <div style="font-size:13px;color:{text_c};margin-top:6px;font-weight:500">→ {rec}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── 4 metric cards ──
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Risk Level",       f"{emoji} {risk.replace('_',' ').title()}")
    c2.metric("Scam Probability", f"{prob}%")
    c3.metric("Language",         result.get("language_detected", "Unknown"))
    c4.metric("Source",           "🎙 Audio" if result.get("_source_type") == "audio_transcript" else "📝 Text")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Charts row ──
    ch1, ch2 = st.columns([1, 1])

    with ch1:
        gauge_color = {"high_risk": "#ff7b72", "suspicious": "#e3b341", "safe": "#3fb950"}[risk]
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=prob,
            delta={"reference": 50, "valueformat": ".0f"},
            title={"text": "Scam Probability Score", "font": {"size": 13, "color": "#8b949e"}},
            number={"suffix": "%", "font": {"size": 36, "color": "#e6edf3"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#30363d",
                         "tickfont": {"color": "#6e7681", "size": 10}},
                "bar":  {"color": gauge_color, "thickness": 0.25},
                "bgcolor": "#161b22",
                "bordercolor": "#30363d",
                "steps": [
                    {"range": [0,  35], "color": "rgba(63,185,80,0.12)"},
                    {"range": [35, 65], "color": "rgba(227,179,65,0.12)"},
                    {"range": [65,100], "color": "rgba(248,81,73,0.12)"},
                ],
                "threshold": {
                    "line": {"color": gauge_color, "width": 3},
                    "thickness": 0.8,
                    "value": prob
                }
            }
        ))
        fig_g.update_layout(
            **PLOT_LAYOUT,
            height=240,
            margin=dict(l=20, r=20, t=50, b=10),
        )
        st.plotly_chart(fig_g, use_container_width=True)

    with ch2:
        tactics = result.get("tactics", {})
        if tactics:
            labels = list(tactics.keys())
            values = list(tactics.values())
            radar_color = {"high_risk": "#ff7b72", "suspicious": "#e3b341", "safe": "#3fb950"}[risk]
            fig_r = go.Figure(go.Scatterpolar(
                r=values + [values[0]],
                theta=labels + [labels[0]],
                fill="toself",
                fillcolor=hex_to_rgba(radar_color, 0.15),
                line=dict(color=radar_color, width=2),
                marker=dict(color=radar_color, size=5),
            ))
            fig_r.update_layout(
                **PLOT_LAYOUT,
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(
                        visible=True, range=[0, 10],
                        tickfont=dict(size=8, color="#6e7681"),
                        gridcolor="#21262d", linecolor="#30363d",
                    ),
                    angularaxis=dict(
                        tickfont=dict(size=9, color="#8b949e"),
                        gridcolor="#21262d", linecolor="#30363d",
                    ),
                ),
                showlegend=False,
                height=240,
                margin=dict(l=50, r=50, t=30, b=20),
                title=dict(text="Manipulation Tactics", font=dict(size=13, color="#8b949e")),
            )
            st.plotly_chart(fig_r, use_container_width=True)

    # ── Summary ──
    st.markdown(f"""
    <div style="background:#161b22;border:1px solid #30363d;border-left:4px solid {color['hex']};
                border-radius:10px;padding:16px 20px;margin:8px 0">
      <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;
                  color:#8b949e;margin-bottom:8px">Analysis Summary</div>
      <div style="font-size:14px;color:#c9d1d9;line-height:1.8">{result.get('summary','')}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Bottom two columns ──
    left, right = st.columns([1.2, 1])

    with left:
        # Highlighted message
        st.markdown("""<div class="section-header">📌 Message Analysis</div>""", unsafe_allow_html=True)
        html = highlight_text_html(result.get("_raw_text", ""), result.get("highlights", []))
        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #30363d;border-radius:10px;
                    padding:16px;min-height:80px;color:#c9d1d9">{html}</div>
        """, unsafe_allow_html=True)
        if result.get("highlights"):
            st.markdown(
                "<div style='font-size:12px;color:#6e7681;margin-top:6px'>"
                "💡 Hover over highlighted phrases to see the reason</div>",
                unsafe_allow_html=True
            )

        # Red flags
        if result.get("red_flags"):
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.markdown("""<div class="section-header">🚩 Red Flags Detected</div>""", unsafe_allow_html=True)
            badges = "".join(
                f'<span class="flag-badge">⚑ {f}</span>'
                for f in result["red_flags"]
            )
            st.markdown(f'<div style="margin:4px 0">{badges}</div>', unsafe_allow_html=True)

        # Suspicious links
        if result.get("suspicious_links"):
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.markdown("""<div class="section-header">🔗 Suspicious Links</div>""", unsafe_allow_html=True)
            for lnk in result["suspicious_links"]:
                st.markdown(
                    f'<div style="background:#161b22;border:1px solid rgba(248,81,73,0.3);'
                    f'border-radius:6px;padding:6px 12px;font-family:monospace;'
                    f'font-size:12px;color:#ff7b72;margin:3px 0">{lnk}</div>',
                    unsafe_allow_html=True
                )

    with right:
        tactics = result.get("tactics", {})
        if tactics:
            tdf = pd.DataFrame({
                "Tactic": list(tactics.keys()),
                "Score":  list(tactics.values())
            })
            tdf = tdf[tdf["Score"] > 0].sort_values("Score", ascending=True)
            if not tdf.empty:
                st.markdown("""<div class="section-header">📊 Tactic Intensity</div>""", unsafe_allow_html=True)
                fig_b = go.Figure(go.Bar(
                    x=tdf["Score"],
                    y=tdf["Tactic"],
                    orientation="h",
                    marker=dict(
                        color=tdf["Score"],
                        colorscale=[[0, "#3fb950"], [0.5, "#e3b341"], [1, "#ff7b72"]],
                        cmin=0, cmax=10,
                        line=dict(width=0),
                    ),
                    text=tdf["Score"].astype(str),
                    textposition="inside",
                    textfont=dict(color="white", size=11, family="Inter"),
                ))
                fig_b.update_layout(
                    **PLOT_LAYOUT,
                    height=280,
                    margin=dict(l=0, r=20, t=10, b=30),
                    xaxis=dict(range=[0, 10], title="Score (0–10)",
                               gridcolor="#21262d", tickfont=dict(color="#6e7681")),
                    yaxis=dict(tickfont=dict(size=11, color="#c9d1d9")),
                    bargap=0.3,
                )
                st.plotly_chart(fig_b, use_container_width=True)
            else:
                st.markdown("""
                <div style="background:#161b22;border:1px solid #30363d;border-radius:10px;
                            padding:40px 20px;text-align:center;margin-top:24px">
                  <div style="font-size:28px">✅</div>
                  <div style="font-size:13px;color:#3fb950;margin-top:8px;font-weight:600">
                    No manipulation tactics detected
                  </div>
                </div>
                """, unsafe_allow_html=True)


# ── Batch dashboard ───────────────────────────────────────────────────────────
def render_batch_dashboard(results: list):
    st.markdown("""
    <div style="height:24px"></div>
    <div style="font-size:18px;font-weight:700;color:#e6edf3;
                border-bottom:1px solid #30363d;padding-bottom:12px;margin-bottom:20px">
      📊 Batch Analysis Dashboard
    </div>
    """, unsafe_allow_html=True)

    df = pd.DataFrame([{
        "File":             r.get("_name", f"File {i+1}"),
        "Risk":             r.get("risk_level", "unknown").replace("_", " ").title(),
        "Scam Probability": r.get("scam_probability", 0),
        "Language":         r.get("language_detected", "Unknown"),
    } for i, r in enumerate(results)])

    c1, c2, c3 = st.columns(3)

    # Pie
    risk_counts = df["Risk"].value_counts().reset_index()
    risk_counts.columns = ["Risk", "Count"]
    fig_pie = go.Figure(go.Pie(
        labels=risk_counts["Risk"],
        values=risk_counts["Count"],
        hole=0.55,
        marker=dict(
            colors=["#ff7b72" if r == "High Risk" else "#e3b341" if r == "Suspicious" else "#3fb950"
                    for r in risk_counts["Risk"]],
            line=dict(color="#0d1117", width=2)
        ),
        textfont=dict(color="#e6edf3"),
    ))
    fig_pie.update_layout(
        **PLOT_LAYOUT, height=240,
        margin=dict(l=0, r=0, t=30, b=0),
        title=dict(text="Risk Distribution", font=dict(size=13, color="#8b949e")),
        legend=dict(font=dict(color="#8b949e")),
    )
    c1.plotly_chart(fig_pie, use_container_width=True)

    # Bar — probability
    fig_prob = go.Figure(go.Bar(
        x=df["File"], y=df["Scam Probability"],
        marker=dict(
            color=df["Scam Probability"],
            colorscale=[[0, "#3fb950"], [0.5, "#e3b341"], [1, "#ff7b72"]],
            cmin=0, cmax=100,
            line=dict(width=0),
        ),
        text=df["Scam Probability"].astype(str) + "%",
        textposition="outside",
        textfont=dict(color="#8b949e", size=11),
    ))
    fig_prob.update_layout(
        **PLOT_LAYOUT, height=240,
        margin=dict(l=0, r=0, t=30, b=40),
        title=dict(text="Scam Probability per File", font=dict(size=13, color="#8b949e")),
        xaxis=dict(tickfont=dict(color="#8b949e"), gridcolor="#21262d"),
        yaxis=dict(range=[0, 115], tickfont=dict(color="#8b949e"), gridcolor="#21262d"),
        bargap=0.4,
    )
    c2.plotly_chart(fig_prob, use_container_width=True)

    # Language bar
    lang_counts = df["Language"].value_counts().reset_index()
    lang_counts.columns = ["Language", "Count"]
    fig_lang = go.Figure(go.Bar(
        x=lang_counts["Language"], y=lang_counts["Count"],
        marker=dict(color="#58a6ff", line=dict(width=0)),
        text=lang_counts["Count"],
        textposition="outside",
        textfont=dict(color="#8b949e", size=11),
    ))
    fig_lang.update_layout(
        **PLOT_LAYOUT, height=240,
        margin=dict(l=0, r=0, t=30, b=40),
        title=dict(text="Languages Detected", font=dict(size=13, color="#8b949e")),
        xaxis=dict(tickfont=dict(color="#8b949e"), gridcolor="#21262d"),
        yaxis=dict(tickfont=dict(color="#8b949e"), gridcolor="#21262d"),
        bargap=0.4,
    )
    c3.plotly_chart(fig_lang, use_container_width=True)

    # Table
    st.markdown("""<div class="section-header" style="margin-top:8px">Summary Table</div>""",
                unsafe_allow_html=True)
    st.dataframe(
        df, use_container_width=True, hide_index=True,
        column_config={
            "Scam Probability": st.column_config.ProgressColumn(
                "Scam Probability", min_value=0, max_value=100, format="%d%%"
            ),
        }
    )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_text, tab_audio = st.tabs(["📝  Text Message Analysis", "🎙️  Audio Analysis"])


# ── TEXT TAB ──────────────────────────────────────────────────────────────────
with tab_text:
    st.markdown("""
    <div style="margin:20px 0 12px 0">
      <div style="font-size:16px;font-weight:600;color:#e6edf3">Paste a suspicious message</div>
      <div style="font-size:13px;color:#8b949e;margin-top:3px">
        Supports Hindi · Marathi · Tamil · Telugu · Bengali · Gujarati · English
      </div>
    </div>
    """, unsafe_allow_html=True)

    default = st.session_state.pop("load_sample", "")
    text_input = st.text_area(
        "Message",
        value=default,
        height=160,
        placeholder="Paste SMS, WhatsApp message, email or any suspicious text here…\n\nExample: आपका बैंक खाता बंद हो जाएगा। अभी OTP शेयर करें।",
        label_visibility="collapsed",
    )

    col1, col2, col3 = st.columns([1, 1, 3])
    run = col1.button("🔍 Analyze", key="run_text")
    if col2.button("🗑 Clear", key="clear_text"):
        st.rerun()

    if run:
        if not text_input.strip():
            st.warning("Please enter a message to analyze.")
        else:
            with st.spinner("Analyzing with LLaMA 3.3…"):
                try:
                    result = analyze_message(text_input.strip(), "text")
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    render_result(result)
                except Exception as e:
                    st.error(f"Analysis error: {e}")


# ── AUDIO TAB ─────────────────────────────────────────────────────────────────
with tab_audio:
    st.markdown("""
    <div style="margin:20px 0 12px 0">
      <div style="font-size:16px;font-weight:600;color:#e6edf3">Upload audio files for analysis</div>
      <div style="font-size:13px;color:#8b949e;margin-top:3px">
        MP3 · WAV · M4A · OGG · WebM · Multiple files supported
      </div>
    </div>
    """, unsafe_allow_html=True)

    files = st.file_uploader(
        "Audio files",
        type=["mp3", "wav", "m4a", "mp4", "ogg", "webm", "mpeg", "mpga"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if files:
        chips = " ".join(
            f'<span style="background:rgba(31,111,235,0.1);color:#58a6ff;'
            f'border:1px solid rgba(31,111,235,0.3);border-radius:6px;'
            f'padding:4px 12px;font-size:12px;font-weight:500">'
            f'🎵 {f.name} <span style="opacity:0.6">({format_file_size(f.size)})</span></span>'
            for f in files
        )
        st.markdown(f'<div style="margin:8px 0 16px 0">{chips}</div>', unsafe_allow_html=True)

    if st.button("🔍 Transcribe & Analyze", key="run_audio"):
        if not files:
            st.warning("Please upload at least one audio file.")
        else:
            all_results = []
            progress = st.progress(0, text="Initializing…")

            for i, f in enumerate(files):
                pct = int((i / len(files)) * 80)
                progress.progress(pct, text=f"Processing {f.name}…")

                with st.expander(f"📄 {f.name}", expanded=True):
                    with st.spinner("Transcribing with Whisper Large v3…"):
                        trans = transcribe_audio(f.read(), f.name, language_hint)

                    if not trans["success"]:
                        st.error(f"Transcription failed: {trans.get('error', 'Unknown error')}")
                        continue

                    st.markdown("""<div class="section-header">📝 Transcript</div>""",
                                unsafe_allow_html=True)
                    st.markdown(
                        f'<div style="background:#161b22;border:1px solid #30363d;'
                        f'border-radius:8px;padding:14px;font-size:14px;'
                        f'line-height:1.8;color:#c9d1d9">{trans["transcript"]}</div>',
                        unsafe_allow_html=True
                    )

                    ic1, ic2, ic3 = st.columns(3)
                    ic1.metric("Language",  trans["language"].title())
                    ic2.metric("Duration",  trans["duration"])
                    ic3.metric("Segments",  trans["segment_count"])

                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

                    with st.spinner("Analyzing with LLaMA 3.3…"):
                        result = analyze_message(trans["transcript"], "audio_transcript")
                        result["_name"] = f.name
                        all_results.append(result)

                    render_result(result)

            progress.progress(100, text="Analysis complete.")

            if len(all_results) > 1:
                render_batch_dashboard(all_results)