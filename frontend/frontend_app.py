import streamlit as st
import requests
import pandas as pd

# Set up backend API URL base
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Resume Matcher", page_icon="🔮", layout="wide")

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
        
        /* Glassmorphism Cards */
        .glass-card {
            background: rgba(26, 28, 35, 0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .glass-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px 0 rgba(0, 229, 255, 0.1);
        }

        /* Typography */
        h1, h2, h3 {
            color: #FFFFFF !important;
            font-weight: 600 !important;
            letter-spacing: -0.5px;
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
        
        /* Neutral Score Badge for lower matches */
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

        /* Skill Pills/Badges */
        .skill-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }
        .skill-pill {
            background: rgba(0, 229, 255, 0.1);
            border: 1px solid rgba(0, 229, 255, 0.3);
            color: #00E5FF;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.85em;
            font-weight: 500;
            letter-spacing: 0.3px;
        }

        /* Streamlit Button Overrides */
        div.stButton > button {
            background: linear-gradient(135deg, #651FFF 0%, #00E5FF 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 229, 255, 0.2);
        }
        div.stButton > button:hover {
            box-shadow: 0 6px 20px rgba(0, 229, 255, 0.4);
            border: none;
            color: white;
        }

        /* Expander/Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==========================================
# HEADER SECTION
# ==========================================
st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>🔮 Nexus AI Matchmaker</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8B949E; margin-bottom: 40px;'>Semantic vector intelligence for precision talent acquisition.</p>", unsafe_allow_html=True)

# Create two clean columns on the screen
col1, col2 = st.columns([1, 1.8], gap="large")

# ==========================================
# COLUMN 1: UPLOADS & CONFIGURATION
# ==========================================
with col1:
    st.markdown("### 📥 Ingest Center")
    
    # --- 1. Resume Upload Component ---
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 📄 Add Candidate Resume")
        uploaded_file = st.file_uploader("Drop PDF resume here", type=["pdf"], label_visibility="collapsed")
        
        if st.button("Extract & Vectorize ⚡", key="upload_btn", use_container_width=True):
            if uploaded_file is not None:
                with st.spinner("Extracting text and saving to database..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    try:
                        res = requests.post(f"{BACKEND_URL}/api/resumes/upload", files=files)
                        if res.status_code == 200:
                            st.success(f"Successfully vectorized {uploaded_file.name}!")
                        else:
                            st.error(f"Error: {res.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Backend offline: {e}")
            else:
                st.warning("Please select a PDF file first.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 2. Job Description Creation Component ---
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 🎯 Create Job Profile")
        job_title = st.text_input("Job Title", placeholder="e.g. Senior FastAPI Engineer")
        job_text = st.text_area("Job Requirements", placeholder="Paste the technical requirements here...", height=120)
        
        if st.button("Save Target Profile", key="save_job_btn", use_container_width=True):
            if job_title.strip() and job_text.strip():
                with st.spinner("Generating job embeddings..."):
                    payload = {"title": job_title, "raw_text": job_text}
                    try:
                        res = requests.post(f"{BACKEND_URL}/api/jobs/", json=payload)
                        if res.status_code == 200:
                            st.success("Target profile locked and saved.")
                        else:
                            st.error(f"Server error: {res.text}")
                    except Exception as e:
                        st.error(f"Backend offline: {e}")
            else:
                st.warning("Title and Requirements are mandatory.")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# COLUMN 2: MATCHER & LEADERBOARD VIEW
# ==========================================
with col2:
    st.markdown("### 📊 Semantic Ranking Engine")
    
    # Fetch active jobs
    jobs_list = []
    try:
        jobs_res = requests.get(f"{BACKEND_URL}/api/jobs/")
        if jobs_res.status_code == 200:
            jobs_list = jobs_res.json()
    except Exception:
        st.error("Cannot reach the backend server.")

    if jobs_list:
        job_options = {j["title"]: j["id"] for j in jobs_list}
        selected_job_title = st.selectbox("Select Target Profile", options=list(job_options.keys()), label_visibility="collapsed")
        selected_job_id = job_options[selected_job_title]
        
        if st.button("Run Semantic Match 🚀", use_container_width=True):
            with st.spinner("Calculating cosine distances..."):
                try:
                    # FIXED: Using the correct /match endpoint
                    rank_res = requests.get(f"{BACKEND_URL}/api/jobs/{selected_job_id}/match")
                    
                    if rank_res.status_code == 200:
                        response_json = rank_res.json()
                        # FIXED: Extracting from the 'matches' key
                        rankings_data = response_json.get("matches", [])
                        
                        if not rankings_data:
                            st.info("No candidates found in the vector database.")
                        else:
                            # --- UX: TABS ---
                            tab1, tab2 = st.tabs(["🏆 Global Leaderboard", "📈 Analytics Insights"])
                            
                            with tab1:
                                st.markdown("<br>", unsafe_allow_html=True)
                                # Render Custom HTML Cards for each candidate
                                for i, item in enumerate(rankings_data, start=1):
                                    score = item.get('match_score', 0)
                                    name = item.get('name', 'Unknown Candidate')
                                    email = item.get('email', 'No Email Provided')
                                    skills = item.get('matched_skills', [])
                                    
                                    # Logic for badge color based on score
                                    badge_class = "score-badge" if score >= 75 else "score-badge-low"
                                    
                                    # Build HTML for skills pills
                                    skills_html = "".join([f'<span class="skill-pill">{s}</span>' for s in skills])
                                    
                                    card_html = f"""
                                    <div class="glass-card">
                                        <h3 style="margin-top: 0;">#{i} {name} <span class="{badge_class}">{score}%</span></h3>
                                        <p style="color: #A0AAB5; font-size: 0.9em; margin-bottom: 8px;">📧 {email}</p>
                                        <div class="skill-container">
                                            {skills_html}
                                        </div>
                                    </div>
                                    """
                                    st.markdown(card_html, unsafe_allow_html=True)
                                    
                            with tab2:
                                st.markdown("<br>", unsafe_allow_html=True)
                                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                                st.subheader("Cohort Analysis")
                                
                                avg_score = sum([c.get('match_score', 0) for c in rankings_data]) / len(rankings_data)
                                
                                m1, m2, m3 = st.columns(3)
                                m1.metric("Total Candidates Scanned", len(rankings_data))
                                m2.metric("Average Match Score", f"{avg_score:.1f}%")
                                m3.metric("Top Score", f"{rankings_data[0].get('match_score', 0)}%")
                                st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.error(f"Ranking endpoint failed: {rank_res.text}")
                except Exception as e:
                    st.error(f"Error triggering ranking execution path: {e}")
    else:
        st.info("Awaiting Job Profiles. Create one in the Ingest Center to begin.")