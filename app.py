import streamlit as st
import time
import uuid
from backend import audit_request, run_main_ai, generate_dna_hash

st.set_page_config(page_title="Omni-Audit", page_icon="🧬", layout="wide")

# --- CSS STYLES ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Space+Mono&display=swap');
    .stApp { background-color: #0b0e14; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    header {visibility: hidden;}

    .glass-card {
        background: #12161d; border: 1px solid #30363d; border-radius: 12px;
        padding: 20px; height: 620px; display: flex; flex-direction: column; overflow: hidden;
    }

    .card-title { font-size: 11px; font-weight: 700; text-transform: uppercase; color: #8b949e; margin-bottom: 20px; }

    /* DNA HELIX */
    .dna-stage { height: 450px; display: flex; justify-content: center; align-items: center; perspective: 1000px; }
    .dna-container { position: relative; width: 100px; height: 380px; transform-style: preserve-3d; }
    .pair-row { position: absolute; width: 100%; height: 2px; transform-style: preserve-3d; animation: helix-rotate 4s infinite linear; }
    .strand-bar { position: absolute; height: 1px; width: 100%; background: rgba(255, 255, 255, 0.2); top: 50%; z-index: -1; }
    .dot { position: absolute; width: 12px; height: 12px; border-radius: 50%; top: -5px; }
    @keyframes helix-rotate { from { transform: rotateY(0deg); } to { transform: rotateY(360deg); } }
    .d-left { left: 0; background: #58a6ff; box-shadow: 0 0 12px #58a6ff; }
    .d-right { right: 0; background: #bc8cff; box-shadow: 0 0 12px #bc8cff; }
    .mutated .d-left, .mutated .d-right { background: #f85149 !important; box-shadow: 0 0 15px #f85149 !important; }

    /* LOGS */
    .t-item { 
        padding: 10px; margin-bottom: 8px; border-radius: 6px; 
        background: rgba(255,255,255,0.03); font-family: 'Space Mono', monospace; font-size: 11px;
    }
    .t-block { border-left: 3px solid #f85149; color: #ff7b72; }
    .t-allow { border-left: 3px solid #2ea043; color: #7ee787; }
    .t-bot { border-left: 3px solid #58a6ff; color: #c9d1d9; background: rgba(88, 166, 255, 0.05); }
</style>
""", unsafe_allow_html=True)

if "logs" not in st.session_state: st.session_state.logs = []
if "status" not in st.session_state: st.session_state.status = "SECURE"
if "voice_queue" not in st.session_state: st.session_state.voice_queue = None

# --- ENHANCED BROWSER VOICE ENGINE ---
def trigger_voice(text, is_alert=False):
    if text:
        # Clean text for JS
        safe_text = text.replace('"', '').replace("'", "")
        pitch = 1.4 if is_alert else 1.1
        rate = 0.9 if is_alert else 1.0
        
        st.markdown(f"""
            <img src="x" onerror='
                (function() {{
                    window.speechSynthesis.cancel();
                    var msg = new SpeechSynthesisUtterance("{safe_text}");
                    var voices = window.speechSynthesis.getVoices();
                    // Priority Female Voices
                    var target = voices.find(v => v.name.includes("Samantha") || v.name.includes("Female") || v.name.includes("Google UK English Female") || v.name.includes("Zira"));
                    if (target) msg.voice = target;
                    msg.pitch = {pitch}; 
                    msg.rate = {rate};
                    window.speechSynthesis.speak(msg);
                }})();
            ' style="display:none;">
        """, unsafe_allow_html=True)

def run_audit(cmd, force=False):
    ts = time.strftime("%H:%M:%S")
    
    if force:
        st.session_state.status = "SECURE"
        st.session_state.logs.append({"ts": ts, "type": "ALLOW", "text": f"OVERRIDE: {cmd}"})
        bot_res = run_main_ai(cmd)
        st.session_state.logs.append({"ts": ts, "type": "BOT", "text": f"AI RESPONSE: {bot_res}"})
        st.session_state.voice_queue = ("Override accepted.", False)
        return

    res = audit_request(cmd)
    parts = res.split("|")
    outcome = parts[0].strip()
    reason = parts[2].strip() if len(parts) > 2 else "Violation"

    if "BLOCK" in outcome:
        st.session_state.status = "BLOCKED"
        st.session_state.logs.append({"ts": ts, "type": "BLOCK", "text": f"BLOCKED: {reason}"})
        st.session_state.voice_queue = (f"Security Alert. {reason}", True)
    else:
        st.session_state.status = "SECURE"
        st.session_state.logs.append({"ts": ts, "type": "ALLOW", "text": f"USER: {cmd}"})
        bot_res = run_main_ai(cmd)
        st.session_state.logs.append({"ts": ts, "type": "BOT", "text": f"AI: {bot_res}"})
        # AI reads back a snippet of its response
        st.session_state.voice_queue = (f"Processing complete. {bot_res[:100]}", False)

# --- UI ---
st.title("🧬 Omni-Audit AI Oversight")

with st.sidebar:
    st.markdown("### Audio Interface")
    if st.button("🚀 INITIALIZE VOICE"):
        trigger_voice("Omni Audit browser voice engine activated. Systems are secure.")
        st.success("Voice Online")

# Trigger voice from queue if exists
if st.session_state.voice_queue:
    text, alert_status = st.session_state.voice_queue
    trigger_voice(text, is_alert=alert_status)
    st.session_state.voice_queue = None

cmd_in = st.text_input("Enter Protocol Command", key="cmd_input")
if cmd_in and cmd_in != st.session_state.get("prev_cmd"):
    st.session_state.prev_cmd = cmd_in
    run_audit(cmd_in)
    st.rerun()

c1, c2, c3 = st.columns([1.2, 1, 1])

with c1:
    log_html = ""
    for l in st.session_state.logs[-10:][::-1]:
        css_class = "t-block" if l["type"] == "BLOCK" else ("t-bot" if l["type"] == "BOT" else "t-allow")
        log_html += f'<div class="t-item {css_class}"><b>[{l["ts"]}]</b> {l["text"]}</div>'
    st.markdown(f'<div class="glass-card"><div class="card-title">Neural Logs</div>{log_html}</div>', unsafe_allow_html=True)

with c2:
    mut_class = "mutated" if st.session_state.status == "BLOCKED" else ""
    dna_inner = "".join([f'<div class="pair-row {mut_class}" style="top:{i*20}px; animation-delay:-{i*0.2}s;"><div class="strand-bar"></div><div class="dot d-left"></div><div class="dot d-right"></div></div>' for i in range(18)])
    st.markdown(f'<div class="glass-card"><div class="card-title">Genetic Helix</div><div class="dna-stage"><div class="dna-container">{dna_inner}</div></div></div>', unsafe_allow_html=True)

with c3:
    is_blocked = st.session_state.status == "BLOCKED"
    st.markdown(f"""
    <div class="glass-card">
        <div class="card-title">System Status</div>
        <div style="background:rgba(255,255,255,0.03); padding:40px 20px; border-radius:10px; border:1px solid #30363d; text-align:center;">
            <h1 style="color:{'#f85149' if is_blocked else '#2ea043'}; margin:0; font-size:32px;">{st.session_state.status}</h1>
            <p style="color:#8b949e; font-size:11px; margin-top:10px;">VOICE: {'AUTHORITATIVE' if is_blocked else 'NORMAL'}</p>
        </div>
        <div style="margin-top:auto; font-family:'Space Mono'; font-size:10px; color:#58a6ff; text-align:center;">
            HASH: {generate_dna_hash(cmd_in if cmd_in else "IDLE")}
        </div>
    </div>
    """, unsafe_allow_html=True)
    if is_blocked:
        if st.button("🔓 AUTHORIZE OVERRIDE", type="primary", use_container_width=True):
            run_audit(cmd_in, force=True)
            st.rerun()