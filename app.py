import streamlit as st
from groq import Groq
import pandas as pd
from dotenv import load_dotenv
import os

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

# ─── ฟังก์ชันโหลด/บันทึก CSV ──────────────────────────────
def load_data():
    try:
        df = pd.read_csv("data.csv")
        return df
    except:
        return pd.DataFrame(columns=["question", "answer"])

def save_data(df):
    df.to_csv("data.csv", index=False, encoding="utf-8-sig")

# ─── สร้าง Context จาก CSV ส่งให้ Gemini ─────────────────
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

# ─── ถาม Gemini ───────────────────────────────────────────
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
# หน้า USER — แชทบอท
# ══════════════════════════════════════════════════════════
if page == "🤖 แชทบอท":

    # เก็บประวัติแชทใน session
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None

    # ── แถบบนสุด ──
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

    # ── ประมวลผลคำถามที่ค้างอยู่ (มาจากช่องพิมพ์ด้านล่าง) ──
    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None
        with st.spinner("กำลังคิด..."):
            df = load_data()
            context = get_context(df)
            answer = ask_gemini(question, context)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

    # ── callback ตอนกดส่ง (Enter) ในช่องพิมพ์ ──
    def _submit_question():
        text = st.session_state.get("itc_input", "").strip()
        if text:
            st.session_state.messages.append({"role": "user", "content": text})
            st.session_state.pending_question = text
        st.session_state.itc_input = ""

    def _clear_chat():
        st.session_state.messages = []
        st.session_state.pending_question = None

    # ── แถบล่าง: ปุ่มเพิ่ม / ช่องพิมพ์ / ไมค์ ──
    with st.container(key="bottombar"):
        col_plus, col_input, col_mic = st.columns([1, 6, 1])
        with col_plus:
            st.button("＋", key="itc_new_chat", on_click=_clear_chat, help="เริ่มแชทใหม่")
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
# หน้า ADMIN — จัดการข้อมูล
# ══════════════════════════════════════════════════════════
elif page == "🔐 Admin Panel":
    st.title("🔐 Admin Panel")

    # ── Login ──
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
        # ── เข้าสู่ระบบแล้ว ──
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success("✅ เข้าสู่ระบบสำเร็จ")
        with col2:
            if st.button("ออกจากระบบ"):
                st.session_state.admin_logged_in = False
                st.rerun()

        df = load_data()
        st.divider()

        # ── เพิ่มข้อมูลใหม่ ──
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

        # ── แสดงข้อมูลทั้งหมด ──
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
