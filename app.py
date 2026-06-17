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
    st.title("💻 IT Chat AI")
    st.caption("ถามปัญหา IT ได้เลย เช่น wifi ไม่ติด, ลืมรหัสผ่าน, เครื่องช้า")
    st.divider()

    # เก็บประวัติแชทใน session
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # แสดงประวัติแชท
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # ช่องพิมพ์คำถาม
    if question := st.chat_input("พิมพ์ปัญหา IT ของคุณ..."):

        # แสดงคำถามผู้ใช้
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        # ดึงข้อมูลจาก CSV แล้วถาม Gemini
        with st.chat_message("assistant"):
            with st.spinner("กำลังคิด..."):
                df = load_data()
                context = get_context(df)
                answer = ask_gemini(question, context)
                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

    # ปุ่มล้างประวัติแชท
    if st.session_state.messages:
        if st.button("🗑️ ล้างประวัติแชท"):
            st.session_state.messages = []
            st.rerun()

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