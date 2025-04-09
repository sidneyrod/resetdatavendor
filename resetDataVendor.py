import streamlit as st
import pandas as pd
import os
from PIL import Image
import base64
from io import BytesIO
import zipfile
import tempfile

# --- Configuração da página ---
st.set_page_config(page_title="ReSet Dashboard", page_icon="kent_icon.ico", layout="wide")

# --- Variável de imagem temporária global ---
temp_img_dir = None

# --- Sidebar Upload ---
with st.sidebar:
    st.markdown("### 📁 Upload & Filters")
    uploaded_file = st.file_uploader("📄 Upload your .xlsm, .xlsx or .csv file", type=["xlsm", "xlsx", "csv"])
    uploaded_zip = st.file_uploader("🖼️ Upload .zip file with images", type=["zip"])
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

    # --- Extração do ZIP (se houver) ---
    if uploaded_zip is not None:
        temp_dir = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
            zip_ref.extractall(temp_dir.name)
        temp_img_dir = temp_dir.name

# --- Helpers ---
def image_to_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

@st.cache_data(show_spinner="🗓️ Reading file...")
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

# --- Logo e título ---
logo_base64 = ""
if os.path.exists("assets/logo_kent.jpeg"):
    logo_base64 = image_to_base64("assets/logo_kent.jpeg")

st.markdown(f"""
<div style='text-align: center; margin: 0; padding: 0;'>
    <img src='data:image/jpeg;base64,{logo_base64}' width='80' style='border-radius: 10px; margin-bottom: 5px;' />
    <h1 style='color: #2E8B57; font-weight: 700; font-size: 2.5em; margin: 0;'>Reset Supported Programs</h1>
    <hr style='border: 1px solid #2E8B57; margin: 6px auto 0 auto; width: 100%;'>
</div>
""", unsafe_allow_html=True)

if uploaded_file:
    data_df, summary_df, reset_df = read_file(uploaded_file)

    if 'FinishTime' in data_df.columns:
        data_df['FinishTime'] = pd.to_datetime(data_df['FinishTime'], errors='coerce', dayfirst=True)

    for col in ['bay number', 'Vendor', 'Program', 'Store']:
        if col in data_df.columns:
            data_df[col] = data_df[col].astype(str).str.upper().str.strip()

    default_vendor = data_df['Vendor'].dropna().unique()[0]
    default_program = data_df[data_df['Vendor'] == default_vendor]['Program'].dropna().unique()[0]

    # --- Filtros ---
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

    # --- Período Analisado ---
    valid_dates_df = filtered_df[filtered_df['FinishTime'].notna()]
    if not valid_dates_df.empty:
        start_date = valid_dates_df['FinishTime'].min().date()
        end_date = valid_dates_df['FinishTime'].max().date()
        st.markdown(f"""
        <div style='display: flex; justify-content: center; margin: 5px 0 30px 0;'>
            <div style='background-color: #2E8B57; color: white; padding: 10px 20px; border-radius: 12px; font-size: 15px; font-weight: 500; box-shadow: 0 4px 10px rgba(0,0,0,0.3);'>
                📅 Period analyzed: <strong>{start_date.strftime('%b %d, %Y')}</strong> to <strong>{end_date.strftime('%b %d, %Y')}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- KPIs ---
    num_stores = filtered_df['Store'].nunique()
    num_bays = filtered_df['bay number'].nunique()
    num_maint = len(filtered_df)
    avg_per_bay = round(num_maint / num_bays, 2) if num_bays else 0
    num_resets = len(reset_df[
        (reset_df['Vendor'].str.upper().str.strip() == selected_vendor) &
        (reset_df['Program'].str.upper().str.strip() == selected_program)
    ]) if not reset_df.empty else 0

    # --- Layout Principal ---
    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        st.markdown("### 📊 Overview")
        st.markdown("""
        <style>
        .kpi-box {
            background-color: #1E1E1E;
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.4);
        }
        .kpi-title {
            font-size: 18px;
            font-weight: 600;
            color: white;
            margin-bottom: 10px;
        }
        .kpi-value {
            font-size: 32px;
            font-weight: bold;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px;'>
            <div class='kpi-box'><div class='kpi-title'>🏪 Stores</div><div class='kpi-value'>{num_stores}</div></div>
            <div class='kpi-box'><div class='kpi-title'>📦 Bays</div><div class='kpi-value'>{num_bays}</div></div>
            <div class='kpi-box'><div class='kpi-title'>🛠️ Maintenances</div><div class='kpi-value'>{num_maint}</div></div>
            <div class='kpi-box'><div class='kpi-title'>🔁 Resets / Updates</div><div class='kpi-value'>{num_resets}</div></div>
            <div class='kpi-box' style='grid-column: span 2;'><div class='kpi-title'>📉 Avg. per Bay</div><div class='kpi-value'>{avg_per_bay}</div></div>
        </div>
        """, unsafe_allow_html=True)

        # --- Lista das Lojas ---
        store_list = sorted(filtered_df['Store'].unique())
        if store_list:
            st.markdown("""
            <div style='margin-top: 35px;'>
                <h3 style='margin-bottom: 12px; color: white; font-size: 24px;'>🏪 Store List</h3>
            </div>
            """, unsafe_allow_html=True)

            cards = []
            for store in store_list:
                cards.append(f"<div style='background-color: #333; color: white; padding: 6px 12px; border-radius: 8px; font-size: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);'>{store}</div>")

            stores_div = "<div style='display: flex; flex-wrap: wrap; gap: 10px;'>" + "".join(cards) + "</div>"
            st.markdown(stores_div, unsafe_allow_html=True)

    with col_right:
        st.markdown("### 🖼️ Bay Image")
        image = None
        image_caption = ""

        # 1. Verifica se há imagens no zip temporário
        if temp_img_dir and os.path.exists(temp_img_dir):
            for file in os.listdir(temp_img_dir):
                if file.lower().startswith(selected_program.lower()) and file.lower().endswith(('.jpg', '.png', '.jpeg')):
                    image_path = os.path.join(temp_img_dir, file)
                    image = Image.open(image_path)
                    image_caption = file
                    break

        # 2. Se não encontrou no zip, tenta pasta local padrão
        if image is None:
            image_dir = os.path.join(os.getcwd(), "images")
            if os.path.exists(image_dir):
                for file in os.listdir(image_dir):
                    if file.lower().startswith(selected_program.lower()) and file.lower().endswith(('.jpg', '.png', '.jpeg')):
                        image_path = os.path.join(image_dir, file)
                        image = Image.open(image_path)
                        image_caption = file
                        break

        if image:
            st.image(image, caption=image_caption, width=500, use_container_width=False)
        else:
            st.info(f"No image found for program '{selected_program}'.")
