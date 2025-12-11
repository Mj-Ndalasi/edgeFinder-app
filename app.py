import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time 

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(page_title="EdgeFinder AIS 8.0 (Phoenix)", layout="wide", page_icon="🔥")

# Load API Key
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    API_KEY = "PASTE_YOUR_API_KEY_HERE"

client = genai.Client(api_key=API_KEY)

# --- 2. DATABASE CONNECTION (GOOGLE SHEETS) ---
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource(ttl=600)
def get_database_connection():
    try:
        if "service_account" in st.secrets:
            creds_dict = dict(st.secrets["service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
            client_gs = gspread.authorize(creds)
            sheet = client_gs.open("EdgeFinder_Database").get_worksheet(0)
            return sheet
        return None
    except Exception as e:
        return None

db = get_database_connection()

# --- 3. THE BRAIN (AIS 8.0 PHOENIX PROTOCOL) ---
def get_learning_context():
    if db is None:
        return "System Status: New Database. No historical data available."
    try:
        data = db.get_all_records()
        df = pd.DataFrame(data)
        if df.empty: return "History: Clean Slate."
        if 'Result' not in df.columns: return "History: Database columns structure error."

        wins = df[df['Result'] == 'WON'].shape[0]
        total_graded = df[df['Result'].isin(['WON', 'LOST'])].shape[0]
        
        if total_graded == 0: return "History: No graded bets yet."
            
        win_rate = (wins / total_graded) * 100
        insight = f"Current Win Rate: {win_rate:.1f}%. "
        if win_rate < 45:
            insight += "⚠️ CRITICAL ADJUSTMENT: Performance is low. ACTIVATE 'PROTOCOL C' (Safety First)."
        elif win_rate > 60:
            insight += "🔥 STATUS: Green Zone. Authorized for 'PROTOCOL B' (Variance/High Upside)."
        return insight
    except Exception as e:
        return f"Error reading history: {str(e)}"

# --- 🔥 THE HYBRID GENERATOR ---
def generate_hybrid(contents, use_search_tool, config):
    # Model Priority List
    model_candidates = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-001',
        'gemini-1.5-pro',
        'gemini-2.0-flash-exp'
    ]
    
    # If using search, we need a tool object
    tools_list = [types.Tool(google_search=types.GoogleSearch())] if use_search_tool else None
    
    last_error = None
    
    for model_name in model_candidates:
        try:
            # Update config with specific tools for this run
            run_config = types.GenerateContentConfig(
                tools=tools_list,
                system_instruction=config.system_instruction,
                temperature=0.3
            )
            
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=run_config
            )
        except Exception as e:
            error_msg = str(e)
            last_error = e
            
            # If Quota Error (429) and we are using Search, we must STOP and warn user.
            if ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg) and use_search_tool:
                st.error("🚨 DAILY SEARCH QUOTA REACHED! Please switch to 'Manual Mode' to continue.")
                return None
            
            # If just a model name error (404), try next model
            if "404" in error_msg or "NOT_FOUND" in error_msg:
                continue
                
            # If Overloaded (503), wait brief moment
            if "503" in error_msg:
                time.sleep(2)
                continue
                
    if last_error:
        st.error(f"❌ System Error: {last_error}")
    return None

# --- AIS 8.0 MASTER PROMPT ---
SYSTEM_INSTRUCTION_BASE = """
You are EdgeFinder (AIS 8.0 Phoenix).
Your Goal: Identify Structural Mismatches and Variance Traps using the "Traffic Light" system.

THE GOLDEN RULE: We do not bet on "potential." We bet on Systemic Flaws.

### 🚦 1. THE TRAFFIC LIGHT PROTOCOL (Mandatory Scan)
For every team/game, assign a Status:
* **🟢 GREEN ZONE (System):** Teams with elite structural control. Safe for "Straight Wins".
* **🟡 YELLOW ZONE (Fortress):** Teams reliable ONLY at home. FADE them away.
* **🔴 RED ZONE (Chaos):** Volatile teams. KILL SWITCH: Never bet them to win straight up.

### 💀 2. THE KILL SWITCH LAWS
* **The "Blowout" Law (NBA):** If Spread > 10, DO NOT bet "Over Points" on Starters.
* **The "Rotation" Law (Football):** If a "B-Team" lineup is confirmed, DELETE "Handicap/Spread" bets.
* **The "Correlation" Ban:** Never combine "Match Winner" + "Player Prop".

### 📋 3. OUTPUT FORMAT
You must output your analysis in this EXACT format:

**MATCH:** [Team A] vs [Team B]
**AUDIT:** [Green/Yellow/Red Zone Verdicts]

**1. THE TRAFFIC LIGHT AUDIT**
* **Home Status:** [Color] - [Reason (Cite Form/Fatigue if available)]
* **Away Status:** [Color] - [Reason (Cite Form/Fatigue if available)]
* **VERDICT:** [PLAYABLE / SKIP / TRAP]

**2. THE PHOENIX SLIP (Max 3 Legs)**
* **Leg 1 (Anchor):** [Selection] (The safest structural play)
* **Leg 2 (Pivot):** [Selection] (The tactical mismatch)
* **Leg 3 (Moonshot):** [Selection] (Optional - High variance prop)

**3. KILL SWITCH CHECK**
* [ ] Lineups Verified?
* [ ] No Red Zone Win Bets?
"""

# --- 4. CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e0e0e0; }
    .stTextInput > div > div > input { background-color: #1a1f2e; color: white; border: 1px solid #30364d; }
    .stTextArea > div > div > textarea { background-color: #1a1f2e; color: #00ffcc; border: 1px solid #30364d; font-family: monospace; }
    .metric-card { background-color: #131722; border: 1px solid #2a2e39; padding: 20px; border-radius: 12px; margin-bottom: 15px;}
    .stButton > button { background: linear-gradient(90deg, #FF416C 0%, #FF4B2B 100%); color: white; font-weight: bold; border: none; }
    div[data-testid="stDataFrame"] { background-color: #1a1f2e; }
</style>
""", unsafe_allow_html=True)

# --- 5. MAIN INTERFACE ---
st.title("🔥 EdgeFinder AIS 8.0 (Phoenix Protocol)")

if db is None:
    st.warning("⚠️ OFFLINE MODE: Google Sheets not connected. (Check Secrets)")

tab1, tab2 = st.tabs(["🔎 PHOENIX SCANNER", "📂 LOCKER ROOM (History)"])

# === TAB 1: THE SCANNER ===
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("### 🏠 HOME TEAM")
        home_team = st.text_input("Home Input", placeholder="e.g. Fiorentina", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("### ✈️ AWAY TEAM")
        away_team = st.text_input("Away Input", placeholder="e.g. Dynamo Kyiv", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    sport = st.selectbox("Sport", ["Football ⚽ (UEFA/Leagues)", "NBA 🏀", "NFL 🏈"])

    # --- 🎛️ CONTROL CENTER ---
    st.markdown("### 📡 DATA SOURCE")
    mode = st.radio("Select Intelligence Source:", 
             ["🟢 Auto-Pilot (Google Search)", "🟠 Manual Intel (Paste Data - Unlimited)"],
             horizontal=True)

    user_context = ""
    if "Manual" in mode:
        st.info("💡 **SCOUT INSTRUCTION:** Go to Flashscore/SofaScore. Copy the 'Match Summary', 'Lineups', or 'Last 5 Matches' and paste it below. The AI will extract the Fatigue & Form data for you.")
        user_context = st.text_area("📋 Intel Stream (Paste Text Here)", height=150, placeholder="Example: \n- Liverpool played 3 days ago (Fatigue High)\n- Salah is benched\n- Last 5 games: W W L D W")

    if st.button("🚀 RUN TRAFFIC LIGHT AUDIT", use_container_width=True):
        if not home_team or not away_team:
            st.error("Enter both teams.")
        else:
            with st.spinner("Connecting to AIS 8.0... Running Structural Diagnostics..."):
                history_context = get_learning_context()
                
                # Determine source logic
                use_search = "Auto" in mode
                
                final_system_instruction = f"{SYSTEM_INSTRUCTION_BASE}\n\nCURRENT LEARNING CONTEXT: {history_context}"
                
                prompt = f"""
                Run a full PHOENIX AUDIT on {home_team} vs {away_team} ({sport}).
                
                SOURCE DATA: {"GOOGLE SEARCH (LIVE)" if use_search else "USER PROVIDED INTEL (BELOW)"}
                
                {f'🚨 USER INTEL:\n{user_context}' if not use_search else 'STEP 1: Search for LATEST Lineups, Injuries, and Schedule (Fatigue).'}
                
                CRITICAL INSTRUCTION: 
                If using User Intel, extract FATIGUE (days since last game) and FORM (last 5 results) from the text to determine the Traffic Light Status.
                
                STEP 2: Classify both teams as GREEN, YELLOW, or RED ZONE.
                STEP 3: Check against the KILL SWITCH LAWS.
                STEP 4: Generate the PHOENIX SLIP based on {history_context}.
                """
                
                try:
                    # Pass the mock config object simply to carry instructions
                    # The function 'generate_hybrid' handles the messy API logic
                    class MockConfig:
                        system_instruction = final_system_instruction
                        
                    response = generate_hybrid(
                        contents=prompt,
                        use_search_tool=use_search,
                        config=MockConfig()
                    )
                    
                    if response:
                        st.markdown("---")
                        st.markdown(f"**🧠 NEURAL CONTEXT:** `{history_context}`")
                        st.markdown(response.text)
                        
                        if db:
                            st.markdown("---")
                            if st.button("💾 Save Phoenix Slip"):
                                current_time = datetime.now().strftime("%Y-%m-%d")
                                db.append_row([current_time, sport, f"{home_team} vs {away_team}", "Pending", "0", "Pending"])
                                st.toast("Bet Saved to Locker Room!")
                except Exception as e:
                    st.error(f"AIS Core Error: {e}")

# === TAB 2: LOCKER ROOM (HISTORY) ===
with tab2:
    st.header("📂 Betting History")
    if db:
        try:
            data = db.get_all_records()
            df = pd.DataFrame(data)
            
            if not df.empty:
                edited_df = st.data_editor(
                    df,
                    column_config={
                        "Result": st.column_config.SelectboxColumn(
                            "Result",
                            options=["Pending", "WON", "LOST", "PUSH"],
                            required=True,
                        )
                    },
                    num_rows="dynamic",
                    use_container_width=True
                )
                
                if st.button("🔄 Update Database"):
                    with st.spinner("Syncing to Cloud..."):
                        updated_data = [edited_df.columns.values.tolist()] + edited_df.values.tolist()
                        db.update(updated_data, "A1") 
                        st.success("Database Updated!")
                        st.rerun()
            else:
                st.info("No bets saved yet.")
        except Exception as e:
            st.error(f"Error loading database: {e}")
    else:
        st.info("Connect Google Sheets to unlock History Tracking.")
