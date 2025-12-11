Here's the latest update for the code:
import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(page_title="EdgeFinder AIS 8.0 (Phoenix)", layout="wide", page_icon="🔥")

# Load API Key
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    # ⚠️ SECURITY WARNING: Only use this for local testing.
    API_KEY = "PASTE_YOUR_API_KEY_HERE"

client = genai.Client(api_key=API_KEY)

# --- 2. DATABASE CONNECTION (GOOGLE SHEETS) ---
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def get_database_connection():
    try:
        creds_dict = dict(st.secrets["service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
        client_gs = gspread.authorize(creds)
        sheet = client_gs.open("EdgeFinder_Database").sheet1
        return sheet
    except Exception as e:
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
    except:
        return "Error reading history."

# --- AIS 8.0 MASTER PROMPT ---
# Incorporates Logic from:
# - AIS 7.0 Master Protocol (The Kill Switch Laws) 
# - The Traffic Light Protocol (Green/Yellow/Red Zones)
# - The Phoenix Slip Structure

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
* **The "Blowout" Law (NBA):** If Spread > 10, DO NOT bet "Over Points" on Starters (Rotation Risk). [cite: 177]
* **The "Rotation" Law (Football):** If a "B-Team" lineup is confirmed, DELETE "Handicap/Spread" bets. Use "Win to Nil" or "Unders".
* **The "Correlation" Ban:** Never combine "Match Winner" + "Player Prop" in the same slip (Red Card/Injury Risk). [cite: 189]

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
    /* Orange/Red Phoenix Gradient Button */
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
    
    # 2025 Simulation Toggle
    sim_mode = st.checkbox("🔮 Enable 2025 Simulation Data Stream (For Paper Trading)")

    if st.button("🚀 RUN TRAFFIC LIGHT AUDIT", use_container_width=True):
        if not home_team or not away_team:
            st.error("Enter both teams.")
        else:
            with st.spinner("Connecting to AIS 8.0... Scanning Traffic Lights... Applying Kill Switches..."):
                # 1. Get Memory Context
                history_context = get_learning_context()
                
                # 2. Build Dynamic Prompt
                # We inject the "Simulation Mode" instruction if checked
                sim_instruction = ""
                if sim_mode:
                    sim_instruction = "IMPORTANT: The user is in a 2025 Simulation Timeline. Assume verified roster changes (e.g., Mbappe at Real Madrid, etc.) if found in recent search context, or prioritize 2025-specific queries."

                final_system_instruction = f"{SYSTEM_INSTRUCTION_BASE}\n\nCURRENT LEARNING CONTEXT: {history_context}\n{sim_instruction}"
                
                google_search_tool = types.Tool(google_search=types.GoogleSearch())
                
                # AIS 8.0 Specific Prompting
                prompt = f"""
                Run a full PHOENIX AUDIT on {home_team} vs {away_team} ({sport}).
                
                STEP 1: USE GOOGLE SEARCH to find the *latest* lineups, injuries, and form.
                STEP 2: Classify both teams as GREEN, YELLOW, or RED ZONE.
                STEP 3: Check against the KILL SWITCH LAWS.
                STEP 4: Generate the PHOENIX SLIP based on {history_context}.
                """
                
                try:
                    # 3. Generate Prediction
                    response = client.models.generate_content(
                        model='gemini-2.0-flash-exp', # Updated to latest model
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            tools=[google_search_tool],
                            system_instruction=final_system_instruction
                        )
                    )
                    
                    # 4. Display
                    st.markdown("---")
                    st.markdown(f"**🧠 NEURAL CONTEXT:** `{history_context}`")
                    st.markdown(response.text)
                    
                    # 5. Save Button
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
                    num_rows="dynamic"
                )
                
                if st.button("🔄 Update Database"):
                    updated_data = [edited_df.columns.values.tolist()] + edited_df.values.tolist()
                    db.clear()
                    db.update(updated_data)
                    st.success("Database Updated! AIS will learn from this.")
            else:
                st.info("No bets saved yet.")
        except Exception as e:
            st.error(f"Error loading database: {e}")
    else:
        st.info("Connect Google Sheets to unlock History Tracking.")