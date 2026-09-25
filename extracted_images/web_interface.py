import streamlit as st
import os
import json
import pandas as pd
from rag_project_code import RAGSystem

# تهيئة الحالة
if "rag_system" not in st.session_state:
    st.session_state.rag_system = None

st.set_page_config(page_title="Corporate AI Assistant", layout="wide")
st.title("🏢 Corporate AI Assistant - s.j")

TASKS_FILE = 'tasks.json'

# --- دوال إدارة الملف ---
def load_tasks():
    if not os.path.exists(TASKS_FILE): return []
    with open(TASKS_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, 'w', encoding='utf-8') as f: json.dump(tasks, f, ensure_ascii=False, indent=4)

# --- إدارة الموظفين (إضافة وحذف) ---
with st.sidebar:
    st.header("⚙️ إدارة الموظفين")
    tasks = load_tasks()
    
    with st.expander("➕ إضافة موظف جديد"):
        with st.form("add_form", clear_on_submit=True):
            name = st.text_input("اسم الموظف")
            task = st.text_input("المهمة")
            email = st.text_input("الإيميل")
            if st.form_submit_button("حفظ"):
                new_id = max([t['id'] for t in tasks], default=0) + 1
                tasks.append({"id": new_id, "employee_name": name, "task": task, "email": email, "status": "Pending"})
                save_tasks(tasks)
                st.rerun()

    st.header("🗑️ حذف موظف")
    del_name = st.selectbox("اختر لحذف:", [""] + [t['employee_name'] for t in tasks])
    if st.button("حذف المحدد"):
        tasks = [t for t in tasks if t['employee_name'] != del_name]
        save_tasks(tasks)
        st.rerun()

# --- جدول المهام المتكامل ---
st.subheader("📋 سجل المهام الكامل")
tasks = load_tasks()
df = pd.DataFrame(tasks)

# الجدول التفاعلي للتحرير المباشر
edited_df = st.data_editor(
    df,
    column_config={
        "status": st.column_config.SelectboxColumn("الحالة", options=["Pending", "Done"]),
        "task": st.column_config.TextColumn("المهمة", width="large"),
        "employee_name": st.column_config.TextColumn("الموظف"),
        "email": st.column_config.TextColumn("الإيميل")
    },
    hide_index=True,
    use_container_width=True
)

if st.button("💾 حفظ التعديلات في الجدول"):
    save_tasks(edited_df.to_dict(orient='records'))
    st.success("تم تحديث المهام بنجاح!")
    st.rerun()

# --- قسم التذكيرات  ---
st.subheader("🔔 إرسال تذكيرات للمهام الجارية")
for index, row in edited_df.iterrows():
    if row['status'] == "Pending":
        if st.button(f"إرسال تذكير لـ {row['employee_name']}", key=f"remind_{row['id']}"):
            if st.session_state.rag_system:
                msg = st.session_state.rag_system.send_task_reminder(row['employee_name'], row['task'], row['email'])
                st.success(msg)
            else:
                st.warning("يجب فهرسة المجلد أولاً!")

# --- قسم الفهرسة والدردشة ---
st.divider()
st.header("🧠 ذكاء الشركة الاصطناعي")
folder_path = st.text_input("أدخل مسار المجلد للفهرسة:", placeholder="C:/CompanyDocs")

if st.button("بدء فهرسة المجلد"):
    if os.path.exists(folder_path):
        with st.spinner("جاري الفهرسة..."):
            my_rag = RAGSystem(folder_path)
            my_rag.ingest_data(folder_path)
            st.session_state.rag_system = my_rag
            st.success("تم!")
    else:
        st.error("المسار غير صحيح.")

if st.session_state.rag_system:
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    
    if prompt := st.chat_input("ask Corporate AI ..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            answer = st.session_state.rag_system.ask(prompt)
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})