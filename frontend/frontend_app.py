import streamlit as st
import requests
import pandas as pd
import os
# This tells it: "If you are in Docker, use the Docker URL. If you are local, use 127.0.0.1"
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
st.set_page_config(page_title="AI Resume Matcher", page_icon="🔮", layout="wide")

# ==========================================
# REAL-TIME API HELPERS
# ==========================================
def fetch_active_jobs():
    """Fetches jobs in real-time. Local DBs are so fast that caching causes stale UI issues."""
    try:
        res = requests.get(f"{BACKEND_URL}/api/jobs/", timeout=5)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []

# ==========================================
# CUSTOM CSS INJECTION (Premium SaaS Theme)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        /* Global Theme */
        .stApp {
            background-color: #0E1117;
            color: #E0E6ED;
        }
        
        /* Glassmorphism Cards for Candidate Outputs */
        .glass-card {
            background: rgba(26, 28, 35, 0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 10px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .glass-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px 0 rgba(0, 229, 255, 0.1);
        }

        /* Custom Glowing Score Badge */
        .score-badge {
            background: linear-gradient(135deg, #00E676 0%, #1DE9B6 100%);
            color: #000000;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 800;
            font-size: 1.1em;
            box-shadow: 0 0 15px rgba(0, 230, 118, 0.4);
            display: inline-block;
            float: right;
        }
        
        /* Neutral Score Badge */
        .score-badge-low {
            background: linear-gradient(135deg, #FF9100 0%, #FF3D00 100%);
            color: #FFFFFF;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 800;
            font-size: 1.1em;
            box-shadow: 0 0 15px rgba(255, 61, 0, 0.4);
            display: inline-block;
            float: right;
        }

        /* Streamlit Button Primary Override */
        div[data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, #651FFF 0%, #00E5FF 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            box-shadow: 0 6px 20px rgba(0, 229, 255, 0.4);
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==========================================
# HEADER SECTION
# ==========================================
st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>🔮 Nexus AI Matchmaker</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8B949E; margin-bottom: 40px;'>Semantic vector intelligence for precision talent acquisition.</p>", unsafe_allow_html=True)

# Create two clean columns
col1, col2 = st.columns([1, 1.8], gap="large")

# ==========================================
# COLUMN 1: UPLOADS & CONFIGURATION
# ==========================================
with col1:
    st.markdown("### 📥 Ingest Center")
    
    # --- 1. Resume Upload Component ---
    with st.container(border=True): 
        st.markdown("#### 📄 Add Candidate Resume")
        uploaded_file = st.file_uploader("Drop PDF resume here", type=["pdf"], label_visibility="collapsed")
        
        if st.button("Extract & Vectorize ⚡", type="primary", use_container_width=True):
            if uploaded_file is not None:
                with st.spinner("Extracting text and saving to database..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    try:
                        res = requests.post(f"{BACKEND_URL}/api/resumes/upload", files=files, timeout=30)
                        if res.status_code == 201 or res.status_code == 200:
                            st.success(f"Successfully vectorized {uploaded_file.name}!")
                        else:
                            st.error(f"Error: {res.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.RequestException:
                        st.error("Backend offline or request timed out.")
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
                            res = requests.post(f"{BACKEND_URL}/api/jobs/", json=payload, timeout=30)
                            if res.status_code == 201 or res.status_code == 200:
                                st.success("Target profile locked and saved.")
                                st.rerun()  # Forces UI to instantly update dropdown!
                            else:
                                st.error(f"Server error: {res.text}")
                        except requests.exceptions.RequestException:
                            st.error("Backend offline or request timed out.")
                else:
                    st.warning("Title and Requirements are mandatory.")

# ==========================================
# COLUMN 2: MATCHER & LEADERBOARD VIEW
# ==========================================
with col2:
    st.markdown("### 📊 Semantic Ranking Engine")
    
    jobs_list = fetch_active_jobs()

    if jobs_list:
        job_options = {j["title"]: j["id"] for j in jobs_list}
        selected_job_title = st.selectbox("Select Target Profile", options=list(job_options.keys()), label_visibility="collapsed")
        selected_job_id = job_options[selected_job_title]
        
        if st.button("Run Semantic Match 🚀", type="primary", use_container_width=True):
            with st.spinner("Calculating cosine distances and AI proficiency scores..."):
                try:
                    rank_res = requests.get(f"{BACKEND_URL}/api/jobs/{selected_job_id}/match", timeout=60)
                    
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
                                    score = item.get('score', item.get('match_score', 0))
                                    name = item.get('name', 'Unknown Candidate')
                                    email = item.get('email', 'No Email Provided')
                                    skills = item.get('breakdown', item.get('matched_skills', []))
                                    
                                    badge_class = "score-badge" if score >= 75 else "score-badge-low"
                                    
                                    # Render the high-level card
                                    card_html = f"""
                                    <div class="glass-card">
                                        <h3 style="margin-top: 0;">#{i} {name} <span class="{badge_class}">{score}%</span></h3>
                                        <p style="color: #A0AAB5; font-size: 0.9em; margin-bottom: 0px;">📧 {email}</p>
                                    </div>
                                    """
                                    st.markdown(card_html, unsafe_allow_html=True)
                                    
                                    # Streamlit Native Expander for Deep Dive
                                    with st.expander(f"🔍 View Match Analysis for {name}"):
                                        st.markdown(f"**Overall Semantic Match:**")
                                        st.progress(int(score) / 100)
                                        
                                        st.markdown("---")
                                        
                                        # Split skills into Matches and Gaps with DEDUPLICATION
                                        matched_skills = []
                                        missing_skills = []
                                        seen_matched_skills = set() # Track duplicates
                                        seen_missing_skills = set() # Track duplicates
                                        
                                        for s in skills:
                                            if isinstance(s, dict):
                                                jd_skill_name = s.get("jd_skill", "").title()
                                                
                                                if s.get("candidate_skill") == "MISSING":
                                                    if jd_skill_name not in seen_missing_skills:
                                                        missing_skills.append(jd_skill_name)
                                                        seen_missing_skills.add(jd_skill_name)
                                                else:
                                                    cand_skill = s.get("candidate_skill", "").title()
                                                    # Deduplicate based on the extracted candidate skill
                                                    if cand_skill not in seen_matched_skills:
                                                        matched_skills.append((cand_skill, s.get("proficiency", 0)))
                                                        seen_matched_skills.add(cand_skill)
                                            else:
                                                if s not in seen_matched_skills:
                                                    matched_skills.append((s, "N/A"))
                                                    seen_matched_skills.add(s)

                                        # Display side-by-side analysis
                                        skill_col1, skill_col2 = st.columns(2)
                                        with skill_col1:
                                            st.markdown("#### ✅ Verified Matches")
                                            if matched_skills:
                                                for skill, prof in matched_skills:
                                                    st.markdown(f"- **{skill}** *(Proficiency: {prof}/5)*")
                                            else:
                                                st.caption("No direct skills verified.")
                                                
                                        with skill_col2:
                                            st.markdown("#### ❌ Skill Gaps")
                                            if missing_skills:
                                                for missing in missing_skills:
                                                    st.markdown(f"- {missing}")
                                            else:
                                                st.caption("No major skill gaps detected!")
                                    
                                    st.write("") # Spacer between candidates
                                    
                            # --- TAB 2: ANALYTICS & INSIGHTS ---
                            with tab2:
                                st.write("")
                                with st.container(border=True):
                                    st.subheader("Cohort Analysis")
                                    
                                    scores = [c.get('score', c.get('match_score', 0)) for c in rankings_data]
                                    avg_score = sum(scores) / len(scores) if scores else 0
                                    
                                    m1, m2, m3 = st.columns(3)
                                    m1.metric("Total Candidates Scanned", len(rankings_data))
                                    m2.metric("Average Match Score", f"{avg_score:.1f}%")
                                    m3.metric("Top Score", f"{scores[0]}%" if scores else "0%")
                                    
                                    st.markdown("---")
                                    st.markdown("#### Score Distribution")
                                    
                                    # Create a simple DataFrame for the bar chart
                                    df_scores = pd.DataFrame({
                                        "Candidate": [c.get('name', f"Candidate {i+1}") for i, c in enumerate(rankings_data)],
                                        "Match %": scores
                                    }).set_index("Candidate")
                                    
                                    # Streamlit native bar chart
                                    st.bar_chart(df_scores, color="#00E5FF", height=300)
                                    
                    else:
                        st.error(f"Ranking endpoint failed: {rank_res.text}")
                except requests.exceptions.RequestException:
                    st.error("Error triggering ranking execution path: Backend offline or timed out.")
    else:
        st.info("Awaiting Job Profiles. Create one in the Ingest Center to begin.")