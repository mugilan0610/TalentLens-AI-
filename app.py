import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import requests
from streamlit_lottie import st_lottie
import io
from docx import Document

def generate_docx_report(candidates):
    doc = Document()
    doc.add_heading('TalentLens AI™ - Candidate Evaluation Report', 0)
    
    for candidate in candidates:
        doc.add_heading(f"{candidate.get('rank')}. {candidate.get('name', 'Unknown')}", level=1)
        doc.add_paragraph(f"ATS Score: {candidate.get('score')}%")
        doc.add_paragraph(f"Experience Level: {candidate.get('experience_label', 'N/A')}")
        doc.add_paragraph(f"Email: {candidate.get('email', 'N/A')} | Phone: {candidate.get('phone', 'N/A')}")
        doc.add_paragraph(f"Location: {candidate.get('location', 'N/A')} | Passed Out: {candidate.get('passed_out_year', 'N/A')}")
        
        skills = candidate.get('skills_found', [])
        skills_str = ", ".join(skills) if isinstance(skills, list) else skills
        doc.add_paragraph(f"Key Skills Found: {skills_str}")
        doc.add_paragraph(f"Evaluation Summary: {candidate.get('summary', 'No summary provided.')}")
        doc.add_paragraph("\n")
        
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

@st.cache_resource
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        return None

from modules.resume_parser import extract_text_from_file
from modules.ai_evaluator import evaluate_candidate

st.set_page_config(page_title="TalentLens AI™", layout="wide", initial_sidebar_state="expanded")

def load_css():
    try:
        with open("assets/styles.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Could not load CSS: {e}")

load_css()

# Session State Initialization
if 'candidates' not in st.session_state:
    st.session_state['candidates'] = []
if 'jd_text' not in st.session_state:
    st.session_state['jd_text'] = ""

# Sidebar Navigation & Setup
with st.sidebar:
    st.markdown(f'<img src="https://res.cloudinary.com/dlde5yjzk/image/upload/v1777479026/Upload_Analysis_Icon_hj9qim.png" class="sidebar-logo">', unsafe_allow_html=True)
    
    api_key = st.text_input("Gemini API Key", type="password", help="Enter your Google Gemini API key.")
    
    st.markdown("---")
    if st.button("🔄 Reset Evaluation State", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    st.markdown("### Navigation")
    nav_selection = st.radio("Go to", ["Upload & Analyze", "Candidates", "Dashboard"], label_visibility="collapsed")

# Native Streamlit Navigation (prevents full page refresh)
st.markdown("""
    <style>
    /* Futuristic Sidebar Toggles */
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="collapsedControl"] button {
        background: rgba(10, 10, 15, 0.7) !important;
        border: 1px solid rgba(0, 212, 255, 0.5) !important;
        border-radius: 12px !important;
        color: #00d4ff !important;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.3) !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 40px !important;
        height: 40px !important;
    }
    
    [data-testid="stSidebarCollapseButton"] button:hover,
    [data-testid="collapsedControl"] button:hover {
        background: rgba(0, 212, 255, 0.2) !important;
        border-color: #00d4ff !important;
        box-shadow: 0 0 25px rgba(0, 212, 255, 0.6) !important;
        transform: scale(1.1) !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 999991 !important;
    }
    
    [data-testid="collapsedControl"] {
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999992 !important;
        left: 20px !important;
        top: 20px !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stTextInput"] input[type="password"] {
        background: rgba(10, 10, 15, 0.5) !important;
        border: 2px solid #8a2be2 !important;
        color: #e2b3ff !important;
        box-shadow: 0 0 15px rgba(138, 43, 226, 0.4) !important;
        animation: rgb-pulse 2s infinite alternate !important;
        transition: all 0.3s ease;
        border-radius: 8px !important;
    }
    
    @keyframes rgb-pulse {
        0% { border-color: rgba(138, 43, 226, 0.6); box-shadow: 0 0 15px rgba(138, 43, 226, 0.4); }
        50% { border-color: rgba(0, 212, 255, 0.8); box-shadow: 0 0 25px rgba(0, 212, 255, 0.6); }
        100% { border-color: rgba(255, 0, 170, 0.6); box-shadow: 0 0 15px rgba(255, 0, 170, 0.4); }
    }
    
    /* Style Sidebar Radio Buttons as Glowing Floating Image Buttons */
    [data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 15px;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: rgba(20, 20, 30, 0.6);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 15px;
        padding: 15px 20px;
        transition: all 0.3s ease;
        cursor: pointer;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5), inset 0 0 10px rgba(0, 212, 255, 0.1);
        display: flex;
        align-items: center;
        width: 100%;
    }
    /* Hide the default radio circle */
    [data-testid="stSidebar"] div[role="radiogroup"] > label div:first-child:not([data-testid="stMarkdownContainer"]) {
        display: none;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] {
        display: flex;
        align-items: center;
        width: 100%;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p {
        font-weight: bold;
        color: #f0f6fc;
        font-size: 1.1rem;
        display: flex;
        align-items: center;
        margin: 0;
    }
    /* Hover and Active states */
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        box-shadow: 0 10px 25px rgba(0, 212, 255, 0.5), inset 0 0 20px rgba(0, 212, 255, 0.3);
        transform: translateY(-3px);
        border-color: #00d4ff;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background: rgba(0, 212, 255, 0.15);
        border-color: #00d4ff;
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.8), inset 0 0 20px rgba(0, 212, 255, 0.4);
    }
    
    /* Add Images to Radio Buttons as Background Fills */
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        width: 100%;
        height: 80px;
        border-radius: 15px;
        border: 2px solid rgba(0, 212, 255, 0.4);
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
        background-color: rgba(10, 10, 15, 0.8);
        background-size: cover;
        background-position: center;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }
    /* Dark overlay for readability */
    [data-testid="stSidebar"] div[role="radiogroup"] > label::after {
        content: "";
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(10, 10, 15, 0.7);
        z-index: 1;
        transition: all 0.3s ease;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover::after {
        background: rgba(0, 212, 255, 0.2);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked)::after {
        background: rgba(0, 212, 255, 0.4);
    }
    /* Text styling */
    [data-testid="stSidebar"] div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p {
        position: relative;
        z-index: 2;
        font-weight: 900;
        color: #fff;
        font-size: 1.3rem;
        text-shadow: 0 0 10px #00d4ff, 0 0 20px #000;
        margin: 0;
    }
    
    [data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(1) {
        background-image: url('https://res.cloudinary.com/dlde5yjzk/image/upload/v1777479017/Dashboard_Icon_s7zg3u.png');
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(2) {
        background-image: url('https://res.cloudinary.com/dlde5yjzk/image/upload/v1777479017/Candidates_Icon_rybyx0.png');
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(3) {
        background-image: url('https://res.cloudinary.com/dlde5yjzk/image/upload/v1777479017/Report_Export_Icon_moomuw.png');
    }
    
    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }
    
    
    /* Upload Layout Styling */
    .stApp { font-family: 'Outfit', sans-serif !important; }
    .page-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 3rem;
        color: #f0f6fc;
        text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
        margin-bottom: 0.5rem;
    }
    .glass-card {
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        border: 1px solid rgba(0, 212, 255, 0.4);
        border-radius: 20px;
    }
    .glow-heading {
        font-weight: 800;
        margin-bottom: 1.5rem;
    }
    .jd-glow { color: #fca311; text-shadow: 0 0 15px rgba(252, 163, 17, 0.6); }
    .resume-glow { color: #00d4ff; text-shadow: 0 0 15px rgba(0, 212, 255, 0.6); }

    /* Document Laser Scanner CSS */
    .document-scanner {
        width: 120px;
        height: 160px;
        background: rgba(255, 255, 255, 0.05);
        border: 2px solid rgba(0, 212, 255, 0.5);
        border-radius: 10px;
        position: relative;
        overflow: hidden;
        margin: 0 auto;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.2), inset 0 0 15px rgba(0, 212, 255, 0.1);
    }
    .document-scanner::before {
        content: '📄';
        font-size: 60px;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        opacity: 0.3;
        filter: drop-shadow(0 0 10px #00d4ff);
    }
    .scanner-laser {
        width: 100%;
        height: 4px;
        background: #00d4ff;
        box-shadow: 0 0 20px 8px rgba(0, 212, 255, 0.8);
        position: absolute;
        top: 0;
        left: 0;
        animation: scan-laser 1.5s ease-in-out infinite alternate;
        z-index: 2;
    }
    @keyframes scan-laser {
        0% { top: 0; }
        100% { top: calc(100% - 4px); }
    }
    </style>
    """, unsafe_allow_html=True)

def page_upload():
    st.markdown('<h1 class="page-title">Upload & Analyze</h1>', unsafe_allow_html=True)
    st.markdown("Configure your target job description and upload candidate resumes for holographic evaluation.")
    
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            st.markdown("<h3 class='glow-heading jd-glow'>🎯 Requirement Engine</h3>", unsafe_allow_html=True)
            jd_input_method = st.radio("Input Method", ["Manual Entry", "Upload Document"], horizontal=True, label_visibility="collapsed")
            
            jd_input = st.session_state.get('jd_text', '')
            jd_file = None
            if jd_input_method == "Manual Entry":
                jd_input = st.text_area("Paste the Job Description here:", height=200, value=jd_input)
            else:
                jd_file = st.file_uploader("Upload JD (PDF, DOCX, TXT)", type=['pdf', 'docx', 'txt'], key="jd_upload")
        
        with col2:
            st.markdown("<h3 class='glow-heading resume-glow'>📄 Talent Stream</h3>", unsafe_allow_html=True)
            uploaded_files = st.file_uploader("Upload Resumes (PDF, DOCX, TXT)", accept_multiple_files=True, type=['pdf', 'docx', 'txt'])
            
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 Initialize Holographic Scan", use_container_width=True):
        if not api_key:
            st.warning("⚠️ Please enter your Gemini API Key in the sidebar.")
            return
            
        final_jd = jd_input
        if jd_input_method == "Upload Document":
            if jd_file:
                jd_file.seek(0)
                final_jd = extract_text_from_file(jd_file.read(), jd_file.name)
            else:
                st.warning("⚠️ Please upload a Job Description document.")
                return
                
        if not final_jd:
            st.warning("⚠️ Please provide a Target Job Description.")
            return
            
        if not uploaded_files:
            st.warning("⚠️ Please upload at least one candidate resume.")
            return
            
        st.session_state['jd_text'] = final_jd
        st.session_state['candidates'] = [] # Clear previous run
        seen_candidates = set()
        
        # Inject Sci-Fi Scanning CSS Animation
        scan_ui = st.empty()
        with scan_ui.container():
            st.markdown("""
            <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 2rem 0;'>
                <div class='document-scanner'>
                    <div class='scanner-laser'></div>
                </div>
                <h3 style='text-align: center; color: #00d4ff; margin-top: 1rem;'>AI Agent is verifying document authenticity...</h3>
            </div>
            """, unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        import concurrent.futures
        
        # 1. Extract text synchronously to avoid st.cache_data thread exception
        file_data_list = []
        for file in uploaded_files:
            file.seek(0)
            raw_text = extract_text_from_file(file.read(), file.name)
            file_data_list.append((raw_text, file.name))
        
        def process_api(raw_text, file_name, api_key, final_jd):
            if not raw_text or raw_text.startswith("ERROR"):
                return {"error": f"Could not read {file_name}. Let's try a standard PDF.", "filename": file_name, "is_resume": False}
                
            evaluation = evaluate_candidate(api_key, final_jd, raw_text)
            evaluation["filename"] = file_name
            return evaluation

        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_api, fd[0], fd[1], api_key, final_jd) for fd in file_data_list]
            
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                result = future.result()
                results.append(result)
                progress_bar.progress((i + 1) / len(uploaded_files))
                status_text.text(f"Processed {result.get('filename', 'file')}...")
                
        # Handle results synchronously for UI
        for evaluation in results:
            file_name = evaluation.get("filename", "Unknown")
            
            if "error" in evaluation and not evaluation.get("is_resume", True):
                st.error(evaluation["error"])
                continue
            elif "error" in evaluation:
                st.error(f"Error evaluating {file_name}: {evaluation['error']}")
                continue
                
            # STRICT GATEKEEPER VALIDATION
            if evaluation.get("is_resume") is False:
                st.error(f"Invalid Document ({file_name}): Please upload a valid professional resume.")
                continue
                
            cand_name = evaluation.get("candidate_name", file_name.split('.')[0])
            cand_email = evaluation.get("email", "Unknown")
            cand_phone = evaluation.get("phone_number", "Unknown")
            
            # Duplicate Rejection Logic
            identifier1 = file_name.lower()
            identifier2 = (cand_name.lower(), cand_email.lower())
            if identifier1 in seen_candidates or (identifier2 in seen_candidates and cand_email != "Unknown"):
                st.info(f"⏭️ Skipped Duplicate Resume: {cand_name}")
                continue
            seen_candidates.add(identifier1)
            seen_candidates.add(identifier2)
                
            candidate_data = {
                "name": cand_name,
                "filename": file_name,
                "score": evaluation.get("score", 0),
                "experience_label": evaluation.get("experience_label", "Unknown"),
                "email": cand_email,
                "phone": cand_phone,
                "location": evaluation.get("location", "Unknown"),
                "passed_out_year": evaluation.get("passed_out_year", "Unknown"),
                "skills_found": evaluation.get("skills_found", []),
                "missing_skills": evaluation.get("missing_skills", []),
                "summary": evaluation.get("summary", ""),
                "interview_questions": evaluation.get("interview_questions", [])
            }
            st.session_state['candidates'].append(candidate_data)
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        # Remove scanning beam when done
        scan_ui.empty()
        
        # Sort and Rank
        if st.session_state['candidates']:
            st.session_state['candidates'] = sorted(st.session_state['candidates'], key=lambda x: x['score'], reverse=True)
            for rank, cand in enumerate(st.session_state['candidates']):
                cand['rank'] = rank + 1
                
            status_text.text("Analysis Complete! Navigate to 'Candidates' to view scorecards.")
            st.success("Analysis Complete!")
        else:
            status_text.text("Analysis Complete! No valid resumes were found.")

def page_candidates():
    st.markdown('<h1 class="page-title">Candidate Scorecards</h1>', unsafe_allow_html=True)
    
    if not st.session_state['candidates']:
        st.info("No candidates analyzed yet. Go to 'Upload & Analyze' to start.")
        return
        
    for cand in st.session_state['candidates']:
        pulse_class = "top-1-pulse" if cand['rank'] == 1 and cand['score'] > 75 else ""
        high_score_class = "high-score-glow" if cand['score'] > 75 else ""
        anim_class = "floating-anim"
        
        # Gold Ribbon logic
        ribbon_html = ""
        if cand['score'] > 75:
            ribbon_html = '<div class="gold-ribbon">Shortlisted</div>'
            
        skills_html = "".join([f'<span class="badge-green">{skill}</span>' for skill in cand['skills_found']])
        missing_skills_html = "".join([f'<span class="badge-red">{skill}</span>' for skill in cand['missing_skills']])
        
        card_html = f"""<div class="antigravity-card {pulse_class} {high_score_class} {anim_class}">
    {ribbon_html}
    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div>
            <div class="card-title">#{cand['rank']} {cand['name']}</div>
            <div class="card-email">{cand['email']}</div>
            <div class="experience-label">{cand['experience_label']}</div>
        </div>
        <div class="circular-score-container">
            <div class="circular-score" style="background: conic-gradient(#00d4ff {cand['score']}%, #161b22 0);">
                <span class="score-text">{cand['score']}%</span>
            </div>
        </div>
    </div>
    <div>
        <div class="section-title">✨ Strong Key Skills</div>
        <div>{skills_html}</div>
    </div>
    <div>
        <div class="section-title">⚠️ Missing Skills</div>
        <div>{missing_skills_html}</div>
    </div>
    <div class="verdict-text">"{cand['summary']}"</div>
</div>"""
        
        # Streamlit markdown breaks on newlines inside HTML, so we strip them
        st.markdown(card_html.replace('\n', ' '), unsafe_allow_html=True)
        
        # Download individual report button
        summary_json = json.dumps(cand, indent=4)
        st.download_button(
            label=f"⬇️ Download {cand['name']} Summary",
            data=summary_json,
            file_name=f"{cand['name']}_summary.json",
            mime="application/json",
            key=f"dl_{cand['rank']}"
        )

def page_dashboard():
    st.markdown('<h1 class="page-title">Advanced Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    if not st.session_state['candidates']:
        st.info("No data available. Go to 'Upload & Analyze' to evaluate candidates.")
        return
        
    candidates = st.session_state['candidates']
    df = pd.DataFrame(candidates)
    
    st.markdown("### Top Candidates Match Scores")
    top_5 = df.head(5)
    fig_bar = px.bar(top_5, x='name', y='score', text='score', 
                     color='score', color_continuous_scale=['#161b22', '#00d4ff'],
                     title="Candidate Comparison")
    fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#f0f6fc")
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("### Talent Pool Skill Distribution")
    all_skills = []
    for skills in df['skills_found']:
        all_skills.extend(skills)
    if all_skills:
        skill_counts = pd.Series(all_skills).value_counts().reset_index()
        skill_counts.columns = ['Skill', 'Count']
        fig_pie = px.pie(skill_counts.head(10), values='Count', names='Skill', 
                         color_discrete_sequence=px.colors.sequential.Teal, hole=0.4)
        fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#f0f6fc")
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No skills extracted to display pie chart.")
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("### 🏆 Shortlisted Candidates (Score > 75%)")
    shortlisted = df[df['score'] > 75]
    
    if not shortlisted.empty:
        # Display Dynamic Table
        display_df = shortlisted[['rank', 'name', 'filename', 'score', 'experience_label']].copy()
        display_df.columns = ['Rank', 'Name', 'File', 'Match %', 'Experience']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        csv = shortlisted.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Shortlisted Candidates as CSV",
            data=csv,
            file_name="shortlisted_candidates.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.warning("No candidates scored above 75%.")
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("### 📑 All Candidates Report")
    display_all_df = df[['rank', 'name', 'email', 'phone', 'location', 'skills_found', 'passed_out_year', 'experience_label', 'score']].copy()
    display_all_df.columns = ['S.No', 'Name', 'Email', 'Mobile Num', 'Location', 'Skills', 'Passed Out Year', 'Experience of Work', 'Score ATS']
    
    # Skills list to string
    display_all_df['Skills'] = display_all_df['Skills'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    
    st.dataframe(display_all_df, use_container_width=True, hide_index=True)
    
    csv_all = display_all_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download ALL Candidates as CSV",
        data=csv_all,
        file_name="all_candidates.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    word_data = generate_docx_report(st.session_state['candidates'])
    st.download_button(
        label="📄 Download Candidates Summary as Word (.docx)",
        data=word_data,
        file_name="talentlens_evaluation_summary.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

# Custom Animated Header
st.markdown("""
<style>
@keyframes header-glow {
    0% { text-shadow: 0 0 15px rgba(0, 212, 255, 0.6); }
    100% { text-shadow: 0 0 30px rgba(0, 212, 255, 0.9); }
}
.header-container {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 20px;
    margin-bottom: 2.5rem;
    padding: 15px 25px;
    background: rgba(10, 10, 15, 0.5);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    border: 1px solid rgba(0, 212, 255, 0.2);
}
.header-logo {
    height: 100px;
    width: 100px;
    object-fit: contain;
    filter: drop-shadow(0 0 15px rgba(0, 212, 255, 0.8));
}
.animated-header {
    color: #00d4ff;
    font-weight: 900;
    font-size: 2.5rem;
    margin: 0;
    animation: header-glow 2s ease-in-out infinite alternate;
    font-family: 'Outfit', sans-serif;
    letter-spacing: 2px;
}
</style>
<div class="header-container">
    <img src="https://res.cloudinary.com/dlde5yjzk/image/upload/v1777479026/Upload_Analysis_Icon_hj9qim.png" class="header-logo">
    <div class="animated-header">TalentLens AI™</div>
</div>
""", unsafe_allow_html=True)

# Routing via Sidebar Selection
if nav_selection == "Upload & Analyze":
    page_upload()
elif nav_selection == "Candidates":
    page_candidates()
elif nav_selection == "Dashboard":
    page_dashboard()

# Custom Footer
st.markdown("""
<br><br>
<div style="text-align: center; color: rgba(255, 255, 255, 0.5); font-size: 0.9rem; padding: 1rem 0; border-top: 1px solid rgba(0, 212, 255, 0.2);">
    © 2026 TalentLens AI™ | Developed with ✨ by <strong>Mugilan M</strong>
</div>
""", unsafe_allow_html=True)
