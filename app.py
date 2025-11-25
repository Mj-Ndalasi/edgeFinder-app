import streamlit as st
from google import genai
from google.genai import types

# --- 1. CONFIGURATION ---
# PASTE YOUR API KEY HERE
# OLD WAY (Unsafe for Cloud):
# API_KEY = "AIzaSy..."

# NEW WAY (Safe for Cloud):
API_KEY = st.secrets["GOOGLE_API_KEY"]

# Initialize Client
client = genai.Client(api_key=API_KEY)

# --- 2. THE BRAIN (AIS 5.0) ---
SYSTEM_INSTRUCTION = """
You are EdgeFinder (formerly AIS 5.0).
Your Goal: Identify "Game States" and "Systemic Mismatches" using LIVE DATA.

MANDATORY PROTOCOL:
1. You HAVE access to Google Search. You MUST use it to find the LATEST lineups, injuries, and stats for the SPECIFIC teams asked.
2. Do NOT hallucinate data. If you cannot find specific xG, state "Data not found" rather than guessing.
3. IGNORE generic training data; prioritize the search results you find right now.

OUTPUT FORMAT:
**MATCH:** [Team A] vs [Team B]
**SYSTEMIC READ:** [Short Headline]

**1. THE EXPLOIT (Player Prop)**
* **Target:** [Name]
* **Bet:** [Selection]
* **Evidence:** [Real stats found via search]

**2. THE GAME STATE (Main Bet)**
* **Target:** [Selection]
* **Protocol:** [A/B/C]
* **Reason:** [Tactical reason based on today's search]

**3. LIVE WATCHLIST**
* [Trigger A]
* [Trigger B]
"""

# --- 3. UI CONFIGURATION (THE GLOW UP) ---
st.set_page_config(page_title="EdgeFinder AI", layout="wide", page_icon="⚡")

# Custom Cyberpunk CSS
st.markdown("""
<style>
    /* MAIN BACKGROUND & TEXT */
    .stApp {
        background-color: #0b0f19;
        color: #e0e0e0;
    }
    
    /* INPUT FIELDS (Dark & Clean) */
    .stTextInput > div > div > input {
        background-color: #1a1f2e;
        color: #ffffff;
        border: 1px solid #30364d;
        border-radius: 8px;
    }
    
    /* BUTTONS (Neon Green Glow) */
    div.stButton > button {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        color: #000000;
        font-weight: bold;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(0, 201, 255, 0.5);
    }
    
    /* CARDS (Containers) */
    .metric-card {
        background-color: #131722;
        border: 1px solid #2a2e39;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* HEADERS */
    h1 { color: #ffffff; font-weight: 800; letter-spacing: -1px; }
    h2, h3 { color: #92FE9D !important; }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #0b0f19;
        border-right: 1px solid #2a2e39;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR CONFIG ---
with st.sidebar:
    st.title("⚡ EdgeFinder")
    st.caption("v1.0 // Anti-Fragile Protocol")
    
    st.divider()
    
    active_sport = st.selectbox("🎯 Active Sport", ["Soccer ⚽", "Basketball 🏀", "NFL 🏈"])
    
    st.divider()
    
    col1, col2 = st.columns(2)
    home_odds = col1.number_input("Home Odds", value=1.90)
    away_odds = col2.number_input("Away Odds", value=3.50)
    
    st.success("● SYSTEM ONLINE")

# --- 5. MAIN INTERFACE ---
# Title Section
st.markdown("<h1>🔎 MATCH INTELLIGENCE</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #888; margin-bottom: 30px;'>Enter match details below to initiate the Systemic Mismatch Scan.</p>", unsafe_allow_html=True)

# Input Section (Side-by-Side Cards)
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown("### 🏠 HOME TEAM")
    home_team = st.text_input("Home Team Input", placeholder="e.g. Dortmund", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown("### ✈️ AWAY TEAM")
    away_team = st.text_input("Away Team Input", placeholder="e.g. Villarreal", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 6. ACTION BUTTON & LOGIC ---
if st.button("🚀 RUN EDGEFINDER PROTOCOL", use_container_width=True):
    if not home_team or not away_team:
        st.warning("⚠️ Please define both targets before scanning.")
    else:
        with st.spinner(f"📡 SEARCHING LIVE DATA: {home_team.upper()} vs {away_team.upper()}..."):
            try:
                # 1. Define Search Tool
                google_search_tool = types.Tool(
                    google_search=types.GoogleSearch()
                )

                # 2. Prompt
                prompt = f"""
                Analyze the match: {home_team} vs {away_team} ({active_sport}).
                Odds: Home {home_odds} | Away {away_odds}.
                
                STEP 1: GOOGLE SEARCH for today's lineups, injuries, and form.
                STEP 2: Apply the EdgeFinder (AIS 5.0) Logic.
                """

                # 3. Generate
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[google_search_tool],
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.7
                    )
                )

                # 4. Display Results in a "Card"
                st.markdown("---")
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown("## 📊 ANALYSIS REPORT")
                st.markdown(response.text)
                st.markdown('</div>', unsafe_allow_html=True)

                # 5. Show Sources
                if response.candidates[0].grounding_metadata.search_entry_point:
                     st.markdown("### 🔗 Verified Sources")
                     st.markdown(response.candidates[0].grounding_metadata.search_entry_point.rendered_content, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ SYSTEM ERROR: {e}")
