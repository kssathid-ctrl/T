import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from pydantic import BaseModel, Field
from typing import Literal

st.set_page_config(page_title="Auto Graph & AI Chatbot", layout="wide")
st.title("📊 ระบบพล็อตกราฟอัตโนมัติ & AI Chatbot")

tab1, tab2 = st.tabs(["📋 พล็อตจากตาราง/CSV (ไม่ต้องใช้ Key)", "🤖 แชทบอท AI พล็อตกราฟ"])

# --- แท็บที่ 1: พล็อตจากตาราง ---
with tab1:
    st.subheader("กรอกข้อมูลในตารางเพื่อสร้างกราฟทันที")
    default_data = pd.DataFrame({
        "หมวดหมู่": ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค."],
        "ยอดขาย": [12000, 15000, 13500, 18000, 22000],
        "กำไร": [3000, 4200, 3500, 5000, 6800]
    })
    df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

    if not df.empty and len(df.columns) >= 2:
        col1, col2, col3 = st.columns(3)
        with col1:
            x_col = st.selectbox("แกน X", df.columns, index=0)
        with col2:
            y_col = st.selectbox("แกน Y", df.columns, index=1)
        with col3:
            chart_type = st.selectbox("รูปแบบกราฟ", ["Bar (กราฟแท่ง)", "Line (กราฟเส้น)", "Pie (กราฟวงกลม)", "Scatter (กราฟจุด)"])

        if "Bar" in chart_type:
            fig = px.bar(df, x=x_col, y=y_col, color=x_col, text_auto=True)
        elif "Line" in chart_type:
            fig = px.line(df, x=x_col, y=y_col, markers=True)
        elif "Pie" in chart_type:
            fig = px.pie(df, names=x_col, values=y_col, hole=0.3)
        else:
            fig = px.scatter(df, x=x_col, y=y_col, size=y_col, color=x_col)

        st.plotly_chart(fig, use_container_width=True)

# --- แท็บที่ 2: แชทบอท AI ---
with tab2:
    st.subheader("พิมพ์บอกข้อมูล แล้วให้ AI เลือกกราฟที่เหมาะสมให้")
    api_key = st.text_input("ใส่ Gemini API Key (รับฟรีที่ aistudio.google.com)", type="password")
    
    class ChartSchema(BaseModel):
        chart_type: Literal["bar", "line", "pie", "scatter"]
        title: str
        x_label: str
        y_label: str
        labels: list[str]
        values: list[float]
        explanation: str

    user_prompt = st.chat_input("พิมพ์ข้อมูลที่นี่ เช่น ยอดขายกาแฟ จันทร์ 50, อังคาร 80, พุธ 65")
    if user_prompt:
        if not api_key:
            st.error("กรุณาใส่ Gemini API Key ด้านบนก่อนพิมพ์แชทครับ")
        else:
            with st.spinner("AI กำลังวาดกราฟ..."):
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"วิเคราะห์ข้อมูลและเลือกกราฟที่เหมาะสม: {user_prompt}",
                    config={"response_mime_type": "application/json", "response_schema": ChartSchema},
                )
                res: ChartSchema = response.parsed
                df_ai = pd.DataFrame({res.x_label: res.labels, res.y_label: res.values})
                st.write(f"**คำแนะนำ AI:** {res.explanation}")
                
                if res.chart_type == "bar":
                    fig2 = px.bar(df_ai, x=res.x_label, y=res.y_label, color=res.x_label, text_auto=True, title=res.title)
                elif res.chart_type == "line":
                    fig2 = px.line(df_ai, x=res.x_label, y=res.y_label, markers=True, title=res.title)
                elif res.chart_type == "pie":
                    fig2 = px.pie(df_ai, names=res.x_label, values=res.y_label, hole=0.3, title=res.title)
                else:
                    fig2 = px.scatter(df_ai, x=res.x_label, y=res.y_label, size=res.y_label, title=res.title)
                st.plotly_chart(fig2, use_container_width=True)
