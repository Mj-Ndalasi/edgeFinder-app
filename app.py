import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time  # Added for retry logic

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

@st.cache_resource(ttl=600)  # Caching for stability and speed
def get_database_connection():
    try:
        if "service_account" in st.secrets:
            creds_dict = dict(st.secrets["service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
            client_gs = gspread.authorize(creds)
            # FIXED: Used get_worksheet(0) instead of .sheet1 for reliability
            sheet = client_gs.open("EdgeFinder_Database").get_worksheet(0)
            return sheet
        return None
    except Exception as e:
        # Silently fail here to avoid messy errors on startup, handled in UI
        return None

db = get_database_connection()

# --- 3. THE BRAIN (AIS 8.0 PHOENIX PROTOCOL) ---
def get_learning_context():
    """Reads past performance to adjust the AI's risk profile."""
    if db is None:
        return "System Status: New Database. No historical data available."
    
    try:
        data = db.get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            return "History: Clean Slate."
        
        # Ensure 'Result' column exists to avoid crash
        if 'Result' not in df.columns:
            return "History: Database columns structure error."

        wins = df[df['Result'] == 'WON'].shape[0]
        total_graded = df[df['Result'].isin(['WON', 'LOST'])].shape[0]
        
        if total_graded == 0:
            return "History: No graded bets yet."
            
        win_rate = (wins / total_graded) * 100
        
        insight = f"Current Win Rate: {win_rate:.1f}%. "
        if win_rate < 45:
            insight += "⚠️ CRITICAL ADJUSTMENT: Performance is low. ACTIVATE 'PROTOCOL C' (Safety First). No Moonshots."
        elif win_rate > 60:
            insight += "🔥 STATUS: Green Zone. Authorized for 'PROTOCOL B' (Variance/High Upside)."
        return insight
    except Exception as e:
        return f"Error reading history: {str(e)}"

# --- RETRY LOGIC FUNCTION ---
def generate_safe_content(model_name, contents, config):
    """Retries the API call if it hits a 503 Overloaded error."""
    max_retries = 4
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
        except Exception as e:
            error_msg = str(e)
            # Retry only on server errors (503) or rate limits (429)
            if "503" in error_msg or "429" in error_msg:
                wait_time = 2 ** (attempt + 1) # Exponential backoff: 2s, 4s, 8s...
                st.toast(f"⚠️ AI Busy. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})", icon="⏳")
                time.sleep(wait_time)
            else:
                raise e # If it's another error (like Auth), fail immediately
    return None

# --- AIS 8.0 MASTER PROMPT ---
SYSTEM_INSTRUCTION_BASE = """
You are EdgeFinder (AIS 8.0 Phoenix).
Your Goal: Identify Structural Mismatches and Variance Traps using the "Traffic Light" system.

THE GOLDEN RULE: We do not bet on "potential." We bet on Systemic Flaws.

### 🚦 1. THE TRAFFIC LIGHT PROTOCOL (Mandatory Scan)
For every team/game, assign a Status:
* **🟢 GREEN ZONE (System):** Teams with elite structural control (e.g., Man City, OKC Thunder). Safe for "Straight Wins".
* **🟡 YELLOW ZONE (Fortress):** Teams reliable ONLY at home. FADE them away.
* **🔴 RED ZONE (Chaos):** Volatile teams (e.g., Chelsea, Mid-table NBA). KILL SWITCH: Never bet them to win straight up.

### 💀 2. THE KILL SWITCH LAWS (AIS 7.0)
If these conditions are met, you MUST reject the specific bet type:
* **The "Blowout" Law (NBA):** If Spread > 10, DO NOT bet "Over Points" on Starters (Rotation Risk).
* **The "Rotation" Law (Football):** If a "B-Team" lineup is confirmed, DELETE "Handicap/Spread" bets. Use "Win to Nil" or "Unders".
* **The "Correlation" Ban:** Never combine "Match Winner" + "Player Prop" in the same slip (Red Card/Injury Risk).

### 📋 3. OUTPUT FORMAT (The Phoenix Diagnostic)
You must output your analysis in this EXACT format:

**MATCH:** [Team A] vs [Team B]
**AUDIT:** [Green/Yellow/Red Zone Verdicts]

**1. THE TRAFFIC LIGHT AUDIT**
* **Home Status:** [Color] - [Reason]
* **Away Status:** [Color] - [Reason]
* **VERDICT:** [PLAYABLE / SKIP / TRAP]

**2. THE PHOENIX SLIP (Max 3 Legs)**
* **Leg 1 (Anchor):** [Selection] (The safest structural play)
* **Leg 2 (Pivot):** [Selection] (The tactical mismatch)
* **Leg 3 (Moonshot):** [Selection] (Optional - High variance prop)

**3. KILL SWITCH CHECK**
* [ ] Lineups Verified?
* [ ] No Red Zone Win Bets?
"""

# --- 4. CUSTOM CSS (Cyberpunk/Phoenix UI) ---
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e0e0e0; }
    .stTextInput > div > div > input { background-color: #1a1f2e; color: white; border: 1px solid #30364d; }
    .metric-card { background-color: #131722; border: 1px solid #2a2e39; padding: 20px; border-radius: 12px; margin-bottom: 15px;}
    .stButton > button { background: linear-gradient(90deg, #FF416C 0%, #FF4B2B 100%); color: white; font-weight: bold; border: none; }
    div[data-testid="stDataFrame"] { background-color: #1a1f2e; }
</style>
""", unsafe_allow_html=True)

# --- 5. MAIN INTERFACE TABS ---
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
    
    sim_mode = st.checkbox("🔮 Enable 2025 Simulation Data Stream (For Paper Trading)")

    if st.button("🚀 RUN TRAFFIC LIGHT AUDIT", use_container_width=True):
        if not home_team or not away_team:
            st.error("Enter both teams.")
        else:
            with st.spinner("Connecting to AIS 8.0... Scanning Traffic Lights... Applying Kill Switches..."):
                history_context = get_learning_context()
                
                sim_instruction = ""
                if sim_mode:
                    sim_instruction = "IMPORTANT: The user is in a 2025 Simulation Timeline. Assume verified roster changes (e.g., Mbappe at Real Madrid, etc.) if found in recent search context, or prioritize 2025-specific queries."

                final_system_instruction = f"{SYSTEM_INSTRUCTION_BASE}\n\nCURRENT LEARNING CONTEXT: {history_context}\n{sim_instruction}"
                
                google_search_tool = types.Tool(google_search=types.GoogleSearch())
                
                prompt = f"""
                Run a full PHOENIX AUDIT on {home_team} vs {away_team} ({sport}).
                
                STEP 1: USE GOOGLE SEARCH to find the *latest* lineups, injuries, and form.
                STEP 2: Classify both teams as GREEN, YELLOW, or RED ZONE.
                STEP 3: Check against the KILL SWITCH LAWS.
                STEP 4: Generate the PHOENIX SLIP based on {history_context}.
                """
                
                # --- EXECUTION WITH RETRY LOOP ---
                try:
                    # UPDATED: Using 'gemini-1.5-pro' for higher stability than flash
                    response = generate_safe_content(
                        model_name='gemini-1.5-pro',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            tools=[google_search_tool],
                            system_instruction=final_system_instruction
                        )
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
                    else:
                        st.error("❌ ERROR: The AI models are currently overloaded. Please try again in 2-3 minutes.")
                        
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
                        # Convert to list of lists with headers
                        updated_data = [edited_df.columns.values.tolist()] + edited_df.values.tolist()
                        
                        # SAFE UPDATE: Overwrite cells instead of deleting the sheet
                        db.update(updated_data, "A1") 
                        
                        st.success("Database Updated! The AI will learn from this next time.")
                        st.rerun()
            else:
                st.info("No bets saved yet. Go to Scanner to add one.")
        except Exception as e:
            st.error(f"Error loading database: {e}")
    else:
        st.info("Connect Google Sheets to unlock History Tracking.")
