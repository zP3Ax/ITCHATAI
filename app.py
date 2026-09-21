import streamlit as st
from groq import Groq
import pandas as pd
from dotenv import load_dotenv
import os
import hashlib
from datetime import datetime

# ─── โหลด API Key ─────────────────────────────────────────
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ─── ตั้งค่าหน้าเว็บ ───────────────────────────────────────
st.set_page_config(
    page_title="IT Chat AI",
    page_icon="💻",
    layout="centered"
)

# ─── CSS ปรับหน้าตาแชทให้เหมือนภาพต้นแบบ ──────────────────
CHAT_UI_CSS = """
<style>
:root{
    --itc-purple:#8B7FE3;
    --itc-orange:#F4954A;
    --itc-bg:#FBF4EC;
    --itc-avatar:#4FA8E0;
}

.stApp{ background-color: var(--itc-bg); }
div[data-testid="stAppViewBlockContainer"]{ padding-bottom: 120px; }

/* ── แถบบนสุด ── */
.itc-topbar{
    display:flex; align-items:center; gap:14px;
    margin: 4px 0 22px 0;
}
.itc-topbar .itc-icon{ font-size:22px; color:#2b2b2b; }
.itc-topbar .itc-pill{
    flex:1; background:#fff; border:2px solid var(--itc-orange);
    border-radius:999px; padding:10px 20px; text-align:center;
    font-weight:600; color:#3a3a3a; font-size:15px;
}

/* ── ฟองแชท ── */
.itc-row{ display:flex; margin: 30px 0; position:relative; }
.itc-row.assistant{ justify-content:flex-start; padding-left:22px; }
.itc-row.user{ justify-content:flex-end; padding-right:22px; }

.itc-bubble{
    max-width:72%; padding:16px 20px; font-size:15px; line-height:1.55;
    color:#fff; white-space:pre-wrap; word-wrap:break-word;
}
.itc-bubble.assistant{ background:var(--itc-purple); border-radius:22px 22px 22px 4px; }
.itc-bubble.user{ background:var(--itc-orange); border-radius:22px 22px 4px 22px; }

.itc-avatar{
    width:38px; height:38px; border-radius:50%; background:var(--itc-avatar);
    display:flex; align-items:center; justify-content:center;
    color:#fff; font-size:18px; position:absolute;
}
.itc-row.assistant .itc-avatar{ left:-18px; bottom:-8px; }
.itc-row.user .itc-avatar{ right:-18px; top:-8px; }

/* ── แถบล่าง (พิมพ์ข้อความ) ── */
.st-key-bottombar{
    position:fixed; left:0; right:0; bottom:0; z-index:999;
    background:var(--itc-bg);
    padding:10px 0 18px 0;
    box-shadow: 0 -6px 16px rgba(0,0,0,0.05);
}
.st-key-bottombar > div{ max-width:700px; margin:0 auto; padding:0 18px; }

.st-key-bottombar [data-testid="column"]:nth-of-type(1) button{
    border-radius:50% !important; width:48px; height:48px; min-width:48px;
    border:none !important;
    background: conic-gradient(from 180deg,#7B68EE,#4FA8E0,#F472B6,#7B68EE) !important;
    color:#fff !important; font-size:20px !important; font-weight:700;
}
.st-key-bottombar [data-testid="column"]:nth-of-type(3) button{
    border-radius:50% !important; width:48px; height:48px; min-width:48px;
    border:none !important; background:#fff !important; color:#2b2b2b !important;
    font-size:18px !important; box-shadow:0 2px 6px rgba(0,0,0,0.08);
}
.st-key-bottombar [data-testid="column"]:nth-of-type(2){ position:relative; }
.st-key-bottombar [data-testid="column"]:nth-of-type(2)::before{
    content:"✨"; position:absolute; left:30px; top:50%;
    transform:translateY(-50%); z-index:3; font-size:15px;
}
.st-key-bottombar [data-testid="column"]:nth-of-type(2) input{
    border-radius:999px !important; border:none !important;
    background:#fff !important; padding:12px 18px 12px 42px !important;
    box-shadow:0 2px 8px rgba(0,0,0,0.06);
}
</style>
"""
st.markdown(CHAT_UI_CSS, unsafe_allow_html=True)

# ─── ฟังก์ชันโหลด/บันทึกคำถาม-คำตอบ (FAQ) ────────────────
DATA_FILE = "data.csv"

def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        return df
    except:
        return pd.DataFrame(columns=["question", "answer"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# ─── ฟังก์ชันจัดการบัญชีผู้ใช้ ────────────────────────────
USERS_FILE = "users.csv"

def load_users():
    try:
        return pd.read_csv(USERS_FILE)
    except:
        return pd.DataFrame(columns=["username", "password_hash"])

def save_users(df):
    df.to_csv(USERS_FILE, index=False, encoding="utf-8-sig")

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

# ─── ฟังก์ชันบันทึก/อ่านประวัติแชทของผู้ใช้ ───────────────
HISTORY_FILE = "chat_history.csv"

def load_history():
    try:
        return pd.read_csv(HISTORY_FILE)
    except:
        return pd.DataFrame(columns=["username", "role", "content", "timestamp"])

def save_message(username, role, content):
    df = load_history()
    new_row = pd.DataFrame({
        "username": [username],
        "role": [role],
        "content": [content],
        "timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
    })
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")

# ─── สร้าง Context จาก CSV ส่งให้โมเดล ────────────────────
def get_context(df):
    context = (
        "คุณคือผู้ช่วย IT ที่เชี่ยวชาญ ชื่อว่า 'IT Chat AI' "
        "ตอบคำถามเกี่ยวกับปัญหา IT เบื้องต้นเป็นภาษาไทย "
        "ตอบให้กระชับ ชัดเจน และเป็นขั้นตอน\n\n"
        "ข้อมูลที่คุณรู้:\n"
    )
    for _, row in df.iterrows():
        context += f"Q: {row['question']}\nA: {row['answer']}\n\n"
    return context

# ─── ถามโมเดล ───────────────────────────────────────────
def ask_gemini(question, context):
    prompt = (
        f"{context}\n\n"
        f"คำถามของผู้ใช้: {question}\n\n"
        "ตอบคำถามนี้โดยอ้างอิงจากข้อมูลที่มี "
        "ถ้าไม่มีข้อมูลที่ตรงกันให้บอกว่าไม่ทราบและแนะนำให้ติดต่อ IT Support"
    )
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# ─── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/technical-support.png", width=64)
    st.title("IT Chat AI")
    st.caption("ระบบตอบปัญหา IT เบื้องต้น")
    st.divider()
    page = st.radio("เมนู", ["🤖 แชทบอท", "🔐 Admin Panel"])

# ══════════════════════════════════════════════════════════
# หน้า USER — แชทบอท (ต้อง login ก่อน)
# ══════════════════════════════════════════════════════════
if page == "🤖 แชทบอท":

    if "user" not in st.session_state:
        st.session_state.user = None

    # ── ยังไม่ได้ login ──
    if st.session_state.user is None:
        st.markdown(
            """
            <div class="itc-topbar">
                <span class="itc-icon">☰</span>
                <div class="itc-pill">IT Chat AI 💻</div>
                <span class="itc-icon">🔍</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_login, tab_signup = st.tabs(["🔑 เข้าสู่ระบบ", "📝 สมัครสมาชิก"])

        with tab_login:
            login_u = st.text_input("ชื่อผู้ใช้", key="login_u")
            login_p = st.text_input("รหัสผ่าน", type="password", key="login_p")
            if st.button("เข้าสู่ระบบ", key="login_btn"):
                if not login_u or not login_p:
                    st.warning("⚠️ กรุณากรอกให้ครบ")
                else:
                    users = load_users()
                    match = users[users["username"] == login_u]
                    if not match.empty and match.iloc[0]["password_hash"] == hash_password(login_p):
                        st.session_state.user = login_u
                        hist = load_history()
                        hist = hist[hist["username"] == login_u]
                        st.session_state.messages = [
                            {"role": r["role"], "content": r["content"]} for _, r in hist.iterrows()
                        ]
                        st.session_state.pending_question = None
                        st.rerun()
                    else:
                        st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

        with tab_signup:
            signup_u = st.text_input("ตั้งชื่อผู้ใช้", key="signup_u")
            signup_p = st.text_input("ตั้งรหัสผ่าน", type="password", key="signup_p")
            if st.button("สมัครสมาชิก", key="signup_btn"):
                if not signup_u or not signup_p:
                    st.warning("⚠️ กรุณากรอกให้ครบ")
                else:
                    users = load_users()
                    if (users["username"] == signup_u).any():
                        st.error("❌ มีชื่อผู้ใช้นี้แล้ว กรุณาเลือกชื่ออื่น")
                    else:
                        new_row = pd.DataFrame({
                            "username": [signup_u],
                            "password_hash": [hash_password(signup_p)],
                        })
                        users = pd.concat([users, new_row], ignore_index=True)
                        save_users(users)
                        st.success("✅ สมัครสำเร็จ! ไปที่แท็บ 'เข้าสู่ระบบ' เพื่อเข้าใช้งานได้เลย")

    # ── login แล้ว: หน้าแชท ──
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "pending_question" not in st.session_state:
            st.session_state.pending_question = None

        top_col1, top_col2 = st.columns([5, 1])
        with top_col1:
            st.markdown(
                f"""
                <div class="itc-topbar">
                    <span class="itc-icon">☰</span>
                    <div class="itc-pill">👋 {st.session_state.user}</div>
                    <span class="itc-icon">🔍</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with top_col2:
            if st.button("🚪 ออก", key="user_logout"):
                st.session_state.user = None
                st.session_state.messages = []
                st.session_state.pending_question = None
                st.rerun()

        # ── พื้นที่แสดงข้อความ ──
        if not st.session_state.messages:
            st.markdown(
                """
                <div class="itc-row assistant">
                    <div class="itc-bubble assistant">สวัสดีครับ พิมพ์ปัญหา IT ที่ด้านล่างได้เลย 👇</div>
                    <div class="itc-avatar">🤖</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "assistant"
            icon = "🧑" if role == "user" else "🤖"
            text = str(msg["content"]).replace("<", "&lt;").replace(">", "&gt;")
            st.markdown(
                f"""
                <div class="itc-row {role}">
                    <div class="itc-bubble {role}">{text}</div>
                    <div class="itc-avatar">{icon}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── ประมวลผลคำถามที่ค้างอยู่ ──
        if st.session_state.pending_question:
            question = st.session_state.pending_question
            st.session_state.pending_question = None
            with st.spinner("กำลังคิด..."):
                df = load_data()
                context = get_context(df)
                answer = ask_gemini(question, context)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                save_message(st.session_state.user, "assistant", answer)
            st.rerun()

        # ── callback ตอนกดส่ง (Enter) ในช่องพิมพ์ ──
        def _submit_question():
            text = st.session_state.get("itc_input", "").strip()
            if text:
                st.session_state.messages.append({"role": "user", "content": text})
                save_message(st.session_state.user, "user", text)
                st.session_state.pending_question = text
            st.session_state.itc_input = ""

        def _clear_chat():
            st.session_state.messages = []
            st.session_state.pending_question = None

        # ── แถบล่าง: ปุ่มเพิ่ม / ช่องพิมพ์ / ไมค์ ──
        with st.container(key="bottombar"):
            col_plus, col_input, col_mic = st.columns([1, 6, 1])
            with col_plus:
                st.button("＋", key="itc_new_chat", on_click=_clear_chat, help="เริ่มแชทใหม่ (หน้าจอ)")
            with col_input:
                st.text_input(
                    "ถามอะไรก็ได้",
                    key="itc_input",
                    placeholder="ถามอะไรก็ได้",
                    label_visibility="collapsed",
                    on_change=_submit_question,
                )
            with col_mic:
                if st.button("🎤", key="itc_mic"):
                    st.toast("ฟีเจอร์พูดถามจะมาเร็ว ๆ นี้ 🎙️")

# ══════════════════════════════════════════════════════════
# หน้า ADMIN — จัดการข้อมูล + ดูประวัติแชท
# ══════════════════════════════════════════════════════════
elif page == "🔐 Admin Panel":
    st.title("🔐 Admin Panel")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        st.subheader("เข้าสู่ระบบ Admin")
        password = st.text_input("รหัสผ่าน", type="password")
        if st.button("เข้าสู่ระบบ"):
            if password == "admin1234":  # ← เปลี่ยนรหัสผ่านตรงนี้ได้
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("❌ รหัสผ่านไม่ถูกต้อง")

    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success("✅ เข้าสู่ระบบสำเร็จ")
        with col2:
            if st.button("ออกจากระบบ"):
                st.session_state.admin_logged_in = False
                st.rerun()

        st.divider()

        tab_qa, tab_history = st.tabs(["📋 จัดการคำถาม-คำตอบ", "📜 ประวัติแชทผู้ใช้"])

        # ── แท็บ 1: จัดการ FAQ (เดิม) ──
        with tab_qa:
            df = load_data()

            st.subheader("➕ เพิ่มคำถาม-คำตอบใหม่")
            new_q = st.text_input("คำถาม IT")
            new_a = st.text_area("คำตอบ")
            if st.button("➕ เพิ่ม"):
                if new_q and new_a:
                    new_row = pd.DataFrame({"question": [new_q], "answer": [new_a]})
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success("✅ เพิ่มข้อมูลสำเร็จ!")
                    st.rerun()
                else:
                    st.warning("⚠️ กรุณากรอกทั้งคำถามและคำตอบ")

            st.divider()

            st.subheader(f"📋 ข้อมูลทั้งหมด ({len(df)} รายการ)")
            if df.empty:
                st.info("ยังไม่มีข้อมูล กรุณาเพิ่มคำถาม-คำตอบก่อน")
            else:
                for i, row in df.iterrows():
                    with st.expander(f"❓ {row['question']}"):
                        st.write(f"**คำตอบ:** {row['answer']}")
                        if st.button("🗑️ ลบรายการนี้", key=f"del_{i}"):
                            df = df.drop(i).reset_index(drop=True)
                            save_data(df)
                            st.success("ลบสำเร็จ!")
                            st.rerun()

        # ── แท็บ 2: ประวัติแชทของผู้ใช้ (ใหม่) ──
        with tab_history:
            st.subheader("📜 ประวัติการแชทของผู้ใช้")
            hist = load_history()

            if hist.empty:
                st.info("ยังไม่มีประวัติการแชทของผู้ใช้")
            else:
                usernames = sorted(hist["username"].dropna().unique().tolist())
                selected_user = st.selectbox("เลือกผู้ใช้", usernames)

                user_hist = hist[hist["username"] == selected_user].sort_values("timestamp")
                st.caption(f"ทั้งหมด {len(user_hist)} ข้อความ")

                for _, row in user_hist.iterrows():
                    role_label = "🧑 ผู้ใช้" if row["role"] == "user" else "🤖 บอท"
                    st.markdown(f"**{role_label}** · _{row['timestamp']}_")
                    st.write(row["content"])
                    st.divider()

                st.download_button(
                    "⬇️ ดาวน์โหลดประวัติแชททั้งหมด (CSV)",
                    data=hist.to_csv(index=False).encode("utf-8-sig"),
                    file_name="chat_history.csv",
                    mime="text/csv",
                )
