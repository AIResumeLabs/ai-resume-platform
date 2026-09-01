import streamlit as st
import requests
import pandas as pd
import os

# This tells it: "If you are in Docker, use the Docker URL. If you are local, use 127.0.0.1"
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
st.set_page_config(page_title="AI Resume Matcher", page_icon="🔮", layout="wide")

# Acronyms that should stay fully uppercase instead of Python's .title()
# turning them into "Sql", "Aws", "Api" etc.
SKILL_ACRONYMS = {
    "sql", "aws", "api", "rest", "orm", "jwt", "oauth", "ci", "cd",
    "ui", "ux", "css", "html", "js", "ts", "ml", "nlp", "k8s", "gcp",
    "llm", "s3", "ec2", "cpp", "csharp",
}


def display_skill_name(skill: str) -> str:
    """Title-cases a skill name while keeping known acronyms fully uppercase."""
    skill = (skill or "").strip()
    if not skill:
        return skill
    words = []
    for w in skill.split():
        words.append(w.upper() if w.lower() in SKILL_ACRONYMS else w.capitalize())
    return " ".join(words)


# ==========================================
# REAL-TIME API HELPERS
# ==========================================
@st.cache_data(ttl=5)
def fetch_active_jobs():
    """Fetches jobs in real-time and reports backend connectivity.

    Returns (jobs_list, error_message). error_message is None when the
    backend responded successfully — this is what lets the UI distinguish
    "no jobs created yet" from "backend is unreachable", which the
    original version could not do (both looked identical: an empty list).

    Cached briefly (ttl=5s) so that switching the job dropdown or other
    unrelated reruns don't re-pay a full request/timeout every time. Right
    after creating a job, the code below explicitly calls
    fetch_active_jobs.clear() before rerunning, so the new job still shows
    up immediately — the original no-cache behavior is preserved exactly
    where it actually matters.
    """
    try:
        res = requests.get(f"{BACKEND_URL}/api/jobs/", timeout=5)
        if res.status_code == 200:
            return res.json(), None
        return [], f"Backend returned HTTP {res.status_code}."
    except requests.exceptions.ConnectionError:
        return [], f"Cannot reach backend at {BACKEND_URL}. Is it running?"
    except requests.exceptions.Timeout:
        return [], "Backend request timed out."
    except Exception as e:
        return [], f"Unexpected error contacting backend: {e}"


# ==========================================
# CUSTOM CSS INJECTION (Monochrome Blue/Purple Theme)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Sora', sans-serif !important;
            letter-spacing: -0.01em;
        }

        /* Global Theme — a slow-moving ambient gradient, blue/purple/indigo
           only (no green). Fixed so it doesn't scroll with content, and
           sits behind everything via a negative z-index. */
        .stApp {
            background-color: #06070B;
            color: #E6E9F0;
        }
        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            z-index: 0;
            background:
                radial-gradient(circle at 12% 18%, rgba(124, 58, 237, 0.18) 0%, transparent 45%),
                radial-gradient(circle at 88% 12%, rgba(0, 200, 255, 0.14) 0%, transparent 45%),
                radial-gradient(circle at 50% 95%, rgba(79, 70, 229, 0.12) 0%, transparent 55%);
            background-size: 200% 200%;
            animation: aurora-drift 24s ease-in-out infinite;
            pointer-events: none;
        }
        @keyframes aurora-drift {
            0%   { background-position: 0% 0%; }
            50%  { background-position: 100% 60%; }
            100% { background-position: 0% 0%; }
        }
        .stApp > header, .stApp [data-testid="stAppViewContainer"] {
            position: relative;
            z-index: 1;
        }

        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover { background: rgba(124, 58, 237, 0.4); }

        /* Glassmorphism cards for candidate results */
        .glass-card {
            position: relative;
            background: linear-gradient(160deg, rgba(30, 32, 46, 0.55) 0%, rgba(14, 15, 22, 0.55) 100%);
            backdrop-filter: blur(20px) saturate(140%);
            -webkit-backdrop-filter: blur(20px) saturate(140%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 12px;
            box-shadow:
                0 8px 32px 0 rgba(0, 0, 0, 0.35),
                inset 0 1px 0 0 rgba(255, 255, 255, 0.06);
            transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                        box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                        border-color 0.25s ease;
            animation: card-fade-in 0.4s ease-out;
        }
        .glass-card::before {
            content: "";
            position: absolute;
            top: 0; left: 16px; right: 16px;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        }
        .glass-card:hover {
            transform: translateY(-3px);
            border-color: rgba(124, 58, 237, 0.35);
            box-shadow:
                0 16px 48px 0 rgba(0, 0, 0, 0.4),
                0 0 32px 0 rgba(124, 58, 237, 0.15),
                inset 0 1px 0 0 rgba(255, 255, 255, 0.08);
        }
        @keyframes card-fade-in {
            from { opacity: 0; transform: translateY(6px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* Score badges — blue/purple = strong, amber = caution, red = critical.
           Green removed entirely to stay on-theme. */
        .score-badge, .score-badge-low, .score-badge-critical {
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 800;
            font-size: 1.1em;
            display: inline-block;
            float: right;
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        .score-badge {
            background: linear-gradient(135deg, #7C3AED 0%, #00C8FF 100%);
            color: #FFFFFF;
            box-shadow: 0 0 20px rgba(124, 58, 237, 0.45);
        }
        .score-badge-low {
            background: linear-gradient(135deg, #FF9100 0%, #FF3D00 100%);
            color: #FFFFFF;
            box-shadow: 0 0 20px rgba(255, 61, 0, 0.4);
        }
        .score-badge-critical {
            background: linear-gradient(135deg, #D50000 0%, #6A0000 100%);
            color: #FFFFFF;
            box-shadow: 0 0 20px rgba(213, 0, 0, 0.5);
        }

        /* Insight callout — blue accent instead of green */
        .insight-callout {
            border-radius: 10px;
            padding: 12px 18px;
            margin-bottom: 18px;
            font-size: 0.95em;
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border-left: 3px solid transparent;
        }
        .insight-good {
            background: rgba(0, 200, 255, 0.07);
            border: 1px solid rgba(0, 200, 255, 0.25);
            border-left: 3px solid #00C8FF;
        }
        .insight-warning {
            background: rgba(255, 145, 0, 0.07);
            border: 1px solid rgba(255, 145, 0, 0.25);
            border-left: 3px solid #FF9100;
        }
        .insight-neutral {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-left: 3px solid rgba(255, 255, 255, 0.3);
        }

        .status-banner-error {
            background: rgba(58, 18, 18, 0.55);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 82, 82, 0.4);
            border-radius: 10px;
            padding: 12px 18px;
            margin-bottom: 20px;
            color: #ffb4b4;
            box-shadow: 0 0 20px rgba(255, 82, 82, 0.12);
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(160deg, rgba(30, 32, 46, 0.45) 0%, rgba(14, 15, 22, 0.45) 100%);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 28px 0 rgba(0, 0, 0, 0.3), inset 0 1px 0 0 rgba(255, 255, 255, 0.05);
        }

        div[data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
        }
        div[data-testid="stTabs"] button[role="tab"] {
            border-radius: 8px 8px 0 0;
            transition: color 0.2s ease;
        }
        div[data-baseweb="select"] > div {
            background: rgba(255, 255, 255, 0.04) !important;
            border-radius: 10px !important;
            border-color: rgba(255, 255, 255, 0.12) !important;
        }

        /* Primary buttons — blue/purple sheen, no green anywhere */
        div[data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, #5B21B6 0%, #00C8FF 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 24px rgba(0, 200, 255, 0.35);
            color: white;
        }
        div[data-testid="stButton"] > button[kind="primary"]:active {
            transform: translateY(0px);
        }

        div[data-testid="stMetricValue"] {
            font-family: 'Sora', sans-serif;
        }

        /* KPI tiles for the three breakdown scores — bordered cards with a
           colored value instead of bare floating numbers. Tier color is
           chosen in Python (kpi_tier_color) and passed in via the style
           attribute, so this class only defines the shared box shape. */
        .kpi-tile {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.09);
            border-radius: 14px;
            padding: 16px 18px;
            text-align: center;
        }
        .kpi-tile .kpi-label {
            font-size: 0.8em;
            color: #9AA4B2;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 6px;
        }
        .kpi-tile .kpi-value {
            font-family: 'Sora', sans-serif;
            font-weight: 700;
            font-size: 1.9em;
        }

        /* Skill chips — replace bullet lists with pill badges */
        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 4px;
        }
        .chip-match {
            background: rgba(0, 200, 255, 0.10);
            border: 1px solid rgba(0, 200, 255, 0.35);
            color: #BEEFFF;
            border-radius: 999px;
            padding: 5px 12px;
            font-size: 0.85em;
            font-weight: 500;
            white-space: nowrap;
        }
        .chip-match .prof {
            color: #7FD8FF;
            opacity: 0.85;
            font-size: 0.9em;
        }
        .chip-gap {
            background: rgba(255, 61, 0, 0.08);
            border: 1px solid rgba(255, 61, 0, 0.3);
            color: #FFC9B8;
            border-radius: 999px;
            padding: 5px 12px;
            font-size: 0.85em;
            font-weight: 500;
            white-space: nowrap;
        }
    </style>
    """, unsafe_allow_html=True)


inject_custom_css()


def badge_class_for(insight: str, score) -> str:
    """Picks the badge tier from the backend's own semantic insight rather
    than an arbitrary score cutoff, so the badge agrees with the text
    underneath it instead of potentially contradicting it."""
    insight = insight or ""
    if insight.startswith("⚠️") and "Missing required" in insight:
        return "score-badge-critical"
    if insight.startswith("⚠️"):
        return "score-badge-low"
    if insight.startswith("⭐"):
        return "score-badge"
    return "score-badge" if score >= 75 else "score-badge-low"


def insight_css_class(insight: str) -> str:
    insight = insight or ""
    if insight.startswith("⭐"):
        return "insight-good"
    if insight.startswith("⚠️"):
        return "insight-warning"
    return "insight-neutral"


def kpi_value_color(pct: float) -> str:
    """Tier color for a 0-100 KPI value. Blue/cyan = strong, amber = mid,
    red = weak. No green, to match the rest of the theme."""
    if pct >= 80:
        return "#00C8FF"
    if pct >= 60:
        return "#FF9100"
    return "#FF5252"


# ==========================================
# HEADER SECTION
# ==========================================
st.markdown(
    """<h1 style='text-align: center; margin-bottom: 0; font-size: 2.8em; font-weight: 800;
    background: linear-gradient(135deg, #A78BFA 0%, #00C8FF 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent;'>
    🔮 Nexus AI Matchmaker</h1>""",
    unsafe_allow_html=True,
)
st.markdown("<p style='text-align: center; color: #9AA4B2; margin-bottom: 20px; font-size: 1.05em;'>Semantic vector intelligence for precision talent acquisition.</p>", unsafe_allow_html=True)

# Fetch jobs ONCE here and reuse the result below — the original code called
# this again inside column 2, doubling the network cost on every render.
jobs_list, backend_error = fetch_active_jobs()

if backend_error:
    col_banner, col_retry = st.columns([5, 1])
    with col_banner:
        st.markdown(
            f"""<div class="status-banner-error">
            🔴 <strong>Backend Unreachable</strong> — {backend_error}
            </div>""",
            unsafe_allow_html=True,
        )
    with col_retry:
        if st.button("🔄 Retry", use_container_width=True):
            fetch_active_jobs.clear()
            st.rerun()

st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# Create two clean columns
col1, col2 = st.columns([1, 1.8], gap="large")

# ==========================================
# COLUMN 1: UPLOADS & CONFIGURATION
# ==========================================
with col1:
    st.markdown("### 📥 Ingest Center")

    # Session-state counter used to reset the file_uploader widget after a
    # successful upload — otherwise the same file stays "loaded" in the
    # widget and a user could accidentally resubmit it.
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    # --- 1. Resume Upload Component ---
    with st.container(border=True):
        st.markdown("#### 📄 Add Candidate Resume")
        uploaded_file = st.file_uploader(
            "Drop PDF resume here",
            type=["pdf"],
            label_visibility="collapsed",
            key=f"resume_uploader_{st.session_state.uploader_key}",
        )

        if st.button("Extract & Vectorize ⚡", type="primary", use_container_width=True):
            if uploaded_file is not None:
                with st.spinner("Extracting text and saving to database..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    try:
                        res = requests.post(f"{BACKEND_URL}/api/resumes/upload", files=files, timeout=120)
                        if res.status_code in (200, 201):
                            st.success(f"Successfully vectorized {uploaded_file.name}!")
                            st.session_state.uploader_key += 1  # reset the widget
                            st.rerun()
                        else:
                            st.error(f"Error: {res.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.ConnectionError:
                        st.error(f"Cannot reach backend at {BACKEND_URL}.")
                    except requests.exceptions.Timeout:
                        st.error("Upload timed out — the backend may be overloaded.")
                    except requests.exceptions.RequestException:
                        st.error("Backend offline or request failed.")
            else:
                st.warning("Please select a PDF file first.")

    # --- 2. Job Description Creation Component ---
    with st.container(border=True):
        st.markdown("#### 🎯 Create Target Profile")
        with st.form("job_creation_form", clear_on_submit=True):
            job_title = st.text_input("Job Title", placeholder="e.g. Senior FastAPI Engineer")
            job_text = st.text_area("Job Requirements", placeholder="Paste the technical requirements here...", height=120)

            submitted = st.form_submit_button("Save Target Profile", type="primary", use_container_width=True)

            if submitted:
                if job_title.strip() and job_text.strip():
                    with st.spinner("Generating job embeddings..."):
                        payload = {"title": job_title, "raw_text": job_text}
                        try:
                            res = requests.post(f"{BACKEND_URL}/api/jobs/", json=payload, timeout=120)
                            if res.status_code in (200, 201):
                                st.success("Target profile locked and saved.")
                                fetch_active_jobs.clear()  # invalidate cache so it shows up immediately
                                st.rerun()
                            else:
                                st.error(f"Server error: {res.text}")
                        except requests.exceptions.ConnectionError:
                            st.error(f"Cannot reach backend at {BACKEND_URL}.")
                        except requests.exceptions.Timeout:
                            st.error("Request timed out — the backend may be overloaded.")
                        except requests.exceptions.RequestException:
                            st.error("Backend offline or request failed.")
                else:
                    st.warning("Title and Requirements are mandatory.")

    # --- Empty-space filler: quick usage tips so column 1 doesn't feel
    # like it trails off into blank space below the two panels. Purely
    # cosmetic — no data dependency. ---
    with st.container(border=True):
        st.markdown("#### 💡 Quick Tips")
        st.markdown(
            "<div style='color:#9AA4B2; font-size:0.88em; line-height:1.6;'>"
            "• Upload resumes first, then create a target profile<br>"
            "• Match scores update instantly — no page reload needed<br>"
            "• Use specific job requirements for tighter semantic matches"
            "</div>",
            unsafe_allow_html=True,
        )

# ==========================================
# COLUMN 2: MATCHER & LEADERBOARD VIEW
# ==========================================
with col2:
    st.markdown("### 📊 Semantic Ranking Engine")

    if jobs_list:
        job_options = {j["title"]: j["id"] for j in jobs_list}
        selected_job_title = st.selectbox("Select Target Profile", options=list(job_options.keys()), label_visibility="collapsed")
        selected_job_id = job_options[selected_job_title]

        if st.button("Run Semantic Match 🚀", type="primary", use_container_width=True):
            with st.spinner("Calculating cosine distances and AI proficiency scores..."):
                try:
                    rank_res = requests.get(f"{BACKEND_URL}/api/jobs/{selected_job_id}/match", timeout=120)

                    if rank_res.status_code == 200:
                        response_json = rank_res.json()
                        rankings_data = response_json.get("matches", [])

                        if not rankings_data:
                            st.info("No candidates found in the vector database.")
                        else:
                            tab1, tab2 = st.tabs(["🏆 Global Leaderboard", "📈 Analytics Insights"])

                            # --- TAB 1: LEADERBOARD & DEEP DIVES ---
                            with tab1:
                                st.write("")
                                for i, item in enumerate(rankings_data, start=1):
                                    # Backend keys are 'match_score' and 'matched_skills' —
                                    # reading them directly instead of the previous
                                    # dual-key fallback (item.get('score', item.get('match_score', 0)))
                                    # which only ever worked because 'score' never existed.
                                    score = item.get('match_score', 0)
                                    name = item.get('name', 'Unknown Candidate')
                                    email = item.get('email', 'No Email Provided')
                                    skills = item.get('matched_skills', [])
                                    insight = item.get('insights', '')
                                    breakdown = item.get('detailed_breakdown', {})

                                    badge_class = badge_class_for(insight, score)

                                    card_html = f"""
                                    <div class="glass-card">
                                        <h3 style="margin-top: 0;">#{i} {name} <span class="{badge_class}">{score}%</span></h3>
                                        <p style="color: #A0AAB5; font-size: 0.9em; margin-bottom: 0px;">📧 {email}</p>
                                    </div>
                                    """
                                    st.markdown(card_html, unsafe_allow_html=True)

                                    with st.expander(f"🔍 View Match Analysis for {name}"):
                                        # Surface the backend's own qualitative insight —
                                        # this was computed but never shown before.
                                        if insight:
                                            st.markdown(
                                                f'<div class="insight-callout {insight_css_class(insight)}">{insight}</div>',
                                                unsafe_allow_html=True,
                                            )

                                        st.markdown("**Overall Semantic Match:**")
                                        st.progress(min(1.0, max(0.0, score / 100)))

                                        # Score breakdown — rendered as three KPI tiles with
                                        # tier-colored values instead of bare st.metric numbers.
                                        if breakdown:
                                            skill_pct = breakdown.get('impact_weighted_match', 0) * 100
                                            affinity_pct = breakdown.get('vector_affinity', 0) * 100
                                            critical_pct = breakdown.get('critical_skill_ratio', 0) * 100

                                            kpi_html = f"""
                                            <div style="display:flex; gap:14px; margin-bottom: 8px;">
                                                <div class="kpi-tile" style="flex:1;">
                                                    <div class="kpi-label">Skill Match</div>
                                                    <div class="kpi-value" style="color:{kpi_value_color(skill_pct)};">{skill_pct:.0f}%</div>
                                                </div>
                                                <div class="kpi-tile" style="flex:1;">
                                                    <div class="kpi-label">Semantic Affinity</div>
                                                    <div class="kpi-value" style="color:{kpi_value_color(affinity_pct)};">{affinity_pct:.0f}%</div>
                                                </div>
                                                <div class="kpi-tile" style="flex:1;">
                                                    <div class="kpi-label">Critical Coverage</div>
                                                    <div class="kpi-value" style="color:{kpi_value_color(critical_pct)};">{critical_pct:.0f}%</div>
                                                </div>
                                            </div>
                                            """
                                            st.markdown(kpi_html, unsafe_allow_html=True)

                                        st.markdown("---")

                                        # Split skills into Matches and Gaps with deduplication
                                        matched_skills = []
                                        missing_skills = []
                                        seen_matched_skills = set()
                                        seen_missing_skills = set()

                                        for s in skills:
                                            if isinstance(s, dict):
                                                jd_skill_name = display_skill_name(s.get("jd_skill", ""))

                                                if s.get("candidate_skill") == "MISSING":
                                                    if jd_skill_name not in seen_missing_skills:
                                                        missing_skills.append(jd_skill_name)
                                                        seen_missing_skills.add(jd_skill_name)
                                                else:
                                                    cand_skill = display_skill_name(s.get("candidate_skill", ""))
                                                    if cand_skill not in seen_matched_skills:
                                                        matched_skills.append((cand_skill, s.get("proficiency", 0)))
                                                        seen_matched_skills.add(cand_skill)
                                            else:
                                                # Legacy defensive path in case matched_skills
                                                # is ever a flat list of strings instead of dicts.
                                                if s not in seen_matched_skills:
                                                    matched_skills.append((s, "N/A"))
                                                    seen_matched_skills.add(s)

                                        skill_col1, skill_col2 = st.columns(2)
                                        with skill_col1:
                                            st.markdown("#### ✅ Verified Matches")
                                            if matched_skills:
                                                chips = "".join(
                                                    f'<span class="chip-match">{skill} <span class="prof">· {prof}/5</span></span>'
                                                    for skill, prof in matched_skills
                                                )
                                                st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)
                                            else:
                                                st.caption("No direct skills verified.")

                                        with skill_col2:
                                            st.markdown("#### ❌ Skill Gaps")
                                            if missing_skills:
                                                chips = "".join(
                                                    f'<span class="chip-gap">{missing}</span>'
                                                    for missing in missing_skills
                                                )
                                                st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)
                                            else:
                                                st.caption("No major skill gaps detected!")

                                    st.write("")

                            # --- TAB 2: ANALYTICS & INSIGHTS ---
                            with tab2:
                                st.write("")
                                with st.container(border=True):
                                    st.subheader("Cohort Analysis")

                                    scores = [c.get('match_score', 0) for c in rankings_data]
                                    avg_score = sum(scores) / len(scores) if scores else 0

                                    m1, m2, m3 = st.columns(3)
                                    m1.metric("Total Candidates Scanned", len(rankings_data))
                                    m2.metric("Average Match Score", f"{avg_score:.1f}%")
                                    # max() instead of scores[0] — don't silently assume
                                    # the API response is sorted descending.
                                    m3.metric("Top Score", f"{max(scores):.1f}%" if scores else "0%")

                                    st.markdown("---")
                                    st.markdown("#### Score Distribution")

                                    df_scores = pd.DataFrame({
                                        "Candidate": [c.get('name', f"Candidate {i+1}") for i, c in enumerate(rankings_data)],
                                        "Match %": scores,
                                    }).set_index("Candidate")

                                    st.bar_chart(df_scores, color="#7C3AED", height=300)

                    else:
                        st.error(f"Ranking endpoint failed: {rank_res.text}")
                except requests.exceptions.ConnectionError:
                    st.error(f"Cannot reach backend at {BACKEND_URL}.")
                except requests.exceptions.Timeout:
                    st.error("Ranking request timed out — try again or check backend load.")
                except requests.exceptions.RequestException:
                    st.error("Error triggering ranking execution path: Backend offline or timed out.")
    elif backend_error:
        # Distinct from the "no jobs yet" case below — the banner above
        # already explains this, so keep this secondary message short.
        st.caption("Ranking engine is unavailable until the backend connection is restored.")
    else:
        st.info("Awaiting Job Profiles. Create one in the Ingest Center to begin.")