import streamlit as st
import pandas as pd
import os
from PIL import Image
import plotly.express as px
import base64
from io import BytesIO

# Page Config
st.set_page_config(page_title="ReSet Dashboard", page_icon="kent_icon.ico", layout="wide")

# Sidebar
with st.sidebar:
    st.markdown("### 📁 Upload & Filters")
    uploaded_file = st.file_uploader("📄 Upload your .xlsm, .xlsx or .csv file", type=["xlsm", "xlsx", "csv"])
    st.markdown("---")
    st.markdown(
        '''
        <div style='
            background: linear-gradient(145deg, #2E8B57, #3fa76c);
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            color: white;
            text-align: center;
            font-size: 15px;
            line-height: 1.6;
            margin-top: 20px;
        '>
            <div style="font-size: 22px; margin-bottom: 8px;">✨ Team</div>
            <div>📝 <strong>Designed by</strong><br>Gabriela Reis</div>
            <div style="margin-top: 8px;">💻 <strong>Developed by</strong><br>Sidney Rodrigues</div>
        </div>
        ''',
        unsafe_allow_html=True
    )

# Helpers
def image_to_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def pil_image_to_base64(img):
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode()

@st.cache_data(show_spinner="📥 Reading file...")
def read_file(file):
    filename = file.name.lower()
    if filename.endswith(".csv"):
        return pd.read_csv(file), pd.DataFrame(), pd.DataFrame()
    else:
        xls = pd.ExcelFile(file, engine="openpyxl")
        return (
            pd.read_excel(xls, sheet_name="Data"),
            pd.read_excel(xls, sheet_name="Summary"),
            pd.read_excel(xls, sheet_name="Reset_Update"),
        )

# Header
logo_base64 = image_to_base64("assets/logo_kent.jpeg")
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    st.markdown(
        f'''
        <div style='
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
            margin-bottom: 10px;
            margin-top: 10px;
        '>
            <img src='data:image/jpeg;base64,{logo_base64}' width='80' style='border-radius: 10px;' />
            <h1 style='color: #2E8B57; font-weight: 700; font-size: 2.4em; margin: 0;'>Reset Supported Programs</h1>
        </div>
        <hr style='border: 1px solid #2E8B57; margin-top: 10px; width: 100%;'>
        ''',
        unsafe_allow_html=True
    )

# Period analyzed - center aligned after header
if uploaded_file:
    data_df, summary_df, reset_df = read_file(uploaded_file)

    if 'FinishTime' in data_df.columns:
        data_df['FinishTime'] = pd.to_datetime(data_df['FinishTime'], errors='coerce', dayfirst=True)

    for col in ['bay number', 'Vendor', 'Program', 'Store']:
        if col in data_df.columns:
            data_df[col] = data_df[col].astype(str).str.upper().str.strip()

    default_vendor = data_df['Vendor'].dropna().unique()[0]
    default_program = data_df[data_df['Vendor'] == default_vendor]['Program'].dropna().unique()[0]
    filtered_temp = data_df[(data_df['Vendor'] == default_vendor) & (data_df['Program'] == default_program)]

    if 'FinishTime' in filtered_temp.columns:
        valid_dates_df = filtered_temp[filtered_temp['FinishTime'].notna()]
        if not valid_dates_df.empty:
            start_date = valid_dates_df['FinishTime'].min().date()
            end_date = valid_dates_df['FinishTime'].max().date()
            st.markdown(f"""
                <div style='
                    display: flex;
                    justify-content: center;
                    margin-bottom: 20px;
                    margin-top: -10px;
                '>
                    <div style='
                        width: 60%;
                        text-align: center;
                        font-size: 16px;
                        font-weight: 500;
                        color: white;
                        background-color: #2e8b57;
                        padding: 10px 18px;
                        border-radius: 12px;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
                    '>
                        📅 Period analyzed: <strong>{start_date.strftime('%b %d, %Y')}</strong> to <strong>{end_date.strftime('%b %d, %Y')}</strong>
                    </div>
                </div>
""", unsafe_allow_html=True)

    st.markdown("""
        <style>
            .label-style {
                font-weight: 600;
                color: white;
                font-size: 15px;
                margin-bottom: 4px;
                display: block;
            }
            div[data-baseweb="select"] {
                font-size: 15px;
            }
            .full-width-box > div {
                width: 100% !important;
            }
        </style>
    """, unsafe_allow_html=True)

    col_v1, col_v2 = st.columns([1, 1])
    with col_v1:
        st.markdown("<span class='label-style'>🔎 Select a Vendor</span>", unsafe_allow_html=True)
        selected_vendor = st.selectbox(
            "", sorted(data_df['Vendor'].dropna().unique()),
            key="vendor", label_visibility="collapsed"
        )

    with col_v2:
        vendor_programs = sorted(data_df[data_df['Vendor'] == selected_vendor]['Program'].dropna().unique())
        st.markdown("<span class='label-style'>🎯 Select a Program</span>", unsafe_allow_html=True)
        selected_program = st.selectbox(
            "", vendor_programs, key="program", label_visibility="collapsed"
        )

    filtered_df = data_df[
        (data_df['Vendor'] == selected_vendor) & (data_df['Program'] == selected_program)
    ]

    # KPIs
    num_stores = filtered_df['Store'].nunique() if 'Store' in filtered_df.columns else 0
    if 'Bay' in filtered_df.columns and filtered_df['Bay'].notna().sum() > 0:
        num_bays = filtered_df['Bay'].nunique()
    elif 'Location' in filtered_df.columns:
        num_bays = filtered_df['Location'].nunique()
    elif 'bay number' in filtered_df.columns:
        num_bays = filtered_df['bay number'].nunique()
    else:
        num_bays = 0
    num_maint = len(filtered_df)
    avg_maint_per_bay = round(num_maint / num_bays, 2) if num_bays else 0
    num_resets = len(reset_df[
        (reset_df['Vendor'].str.upper().str.strip() == selected_vendor) &
        (reset_df['Program'].str.upper().str.strip() == selected_program)
    ]) if not reset_df.empty else 0

    st.markdown("### 📊 Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🏪 Stores", num_stores)
    col2.metric("📦 Bays", num_bays)
    col3.metric("🛠️ Maintenances", num_maint)
    col4.metric("📉 Avg. per Bay", avg_maint_per_bay)
    col5.metric("🔁 Resets / Updates", num_resets)

    # Image
    st.markdown("---")
    st.markdown("### 🖼️ Bay Image")
    image = None
    image_caption = ""
    if os.path.exists("images"):
        for file in os.listdir("images"):
            if file.lower().startswith(selected_program.lower()) and file.lower().endswith((".jpg", ".png", ".jpeg")):
                image_path = os.path.join("images", file)
                image = Image.open(image_path)
                image_caption = f"{file}"
                break

    if image:
        encoded_img = pil_image_to_base64(image)
        st.markdown(f"""
            <style>
                .zoom-img {{
                    max-height: 80vh;
                    max-width: 100%;
                    width: auto;
                    border-radius: 15px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
                    transition: transform 0.3s ease;
                    cursor: zoom-in;
                }}
                .zoom-img:hover {{
                    transform: scale(1.03);
                }}
                .modal {{
                    display: none;
                    position: fixed;
                    z-index: 9999;
                    left: 0;
                    top: 0;
                    width: 100%;
                    height: 100%;
                    overflow: auto;
                    background-color: rgba(0,0,0,0.9);
                }}
                .modal-content {{
                    display: block;
                    margin: 5% auto;
                    max-width: 90%;
                    max-height: 90vh;
                    border-radius: 15px;
                }}
                .close {{
                    position: absolute;
                    top: 20px;
                    right: 35px;
                    color: #fff;
                    font-size: 40px;
                    font-weight: bold;
                    cursor: pointer;
                }}
            </style>
            <div style='text-align: center;'>
                <img src='data:image/jpeg;base64,{encoded_img}' class='zoom-img' onclick="document.getElementById('imgModal').style.display='block'" title='{image_caption}' />
            </div>
            <div id='imgModal' class='modal' onclick="this.style.display='none'">
                <span class='close' onclick="document.getElementById('imgModal').style.display='none'">&times;</span>
                <img class='modal-content' src='data:image/jpeg;base64,{encoded_img}' />
            </div>
        """, unsafe_allow_html=True)
        st.caption(image_caption)
    else:
        st.info(f"No image found for program '{selected_program}'.")

else:
    st.markdown("""
        <div style='
            display: flex;
            justify-content: center;
            align-items: center;
            margin-top: 30px;
            margin-bottom: 30px;
        '>
            <div style='
                background-color: #0f2c3f;
                color: white;
                padding: 20px 30px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 500;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            '>
                📄 Please upload a valid <strong>.xlsm</strong>, <strong>.xlsx</strong>, or <strong>.csv</strong> file in the sidebar to get started.
            </div>
        </div>
    """, unsafe_allow_html=True)
