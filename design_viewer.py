import os
import pandas as pd
import streamlit as st
import json
from PIL import Image
from fpdf import FPDF
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

st.set_page_config(
    page_title="Design Viewer",
    page_icon="🎨",
    layout="wide"
)

# Initialize login state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Login Page
if not st.session_state.logged_in:
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        margin-top: 5rem;
    }
    .login-title {
        text-align: center;
        color: white;
        font-size: 2.5rem;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .stTextInput > div > div > input {
        background-color: rgba(255,255,255,0.9);
        border: none;
        border-radius: 10px;
        padding: 12px;
        font-size: 16px;
    }
    .stButton > button {
        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 30px;
        font-size: 16px;
        font-weight: bold;
        width: 100%;
        margin-top: 1rem;
    }
    .stButton > button:hover {
        background: linear-gradient(45deg, #ee5a24, #ff6b6b);
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="login-title">🎨 Design Viewer</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: white; margin-bottom: 2rem;">Please login to continue</p>', unsafe_allow_html=True)
    
    email = st.text_input("📧 Email", placeholder="Enter your email")
    password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
    
    if st.button("🚀 Login"):
        if email == "sagar@gmail.com" and password == "123456":
            st.session_state.logged_in = True
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("❌ Invalid email or password")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Main App (only loads after login)
st.title("🎨 Design Viewer - Excel-like Table with Image Mapping")

# Logout button
col1, col2 = st.columns([4, 1])
with col2:
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()

# Data persistence functions
def save_data():
    data = {
        "df": st.session_state.df.to_dict(),
        "image_folder": st.session_state.image_folder
    }
    with open("design_viewer_data.json", "w") as f:
        json.dump(data, f)

def load_data():
    try:
        with open("design_viewer_data.json", "r") as f:
            data = json.load(f)
        return pd.DataFrame(data["df"]), data["image_folder"]
    except:
        return None, ""

# --- Initialize DataFrame ---
if "df" not in st.session_state:
    # Try to load saved data
    saved_df, saved_folder = load_data()
    if saved_df is not None:
        st.session_state.df = saved_df
        st.session_state.image_folder = saved_folder
    else:
        # Create DataFrame with 3 empty rows
        st.session_state.df = pd.DataFrame({
            "No": [1, 2, 3],
            "Design Name": ["", "", ""],
            "Design Image": ["", "", ""]
        })
        st.session_state.image_folder = ""

# --- Editable AG-Grid Table ---
st.write("### ✍️ Editable Table")
st.info("Use this table like Excel. Type once and it works smoothly.")

# Add row button
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("➕ Add Row"):
        next_no = len(st.session_state.df) + 1
        new_row = pd.DataFrame({"No": [next_no], "Design Name": [""], "Design Image": [""]})
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        save_data()  # Save data after adding row
        st.rerun()

gb = GridOptionsBuilder.from_dataframe(st.session_state.df)
gb.configure_default_column(editable=True, resizable=True, wrapText=True, autoHeight=True)
gb.configure_column("No", width=80, editable=False)
gb.configure_column("Design Name", width=200)
gb.configure_column("Design Image", width=300, editable=False)
gb.configure_selection("single")
gb.configure_grid_options(
    domLayout='normal',
    suppressHorizontalScroll=False,
    alwaysShowHorizontalScroll=True,
    rowHeight=40
)
grid_options = gb.build()

grid_response = AgGrid(
    st.session_state.df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=True,
    height=300
)

# Safely update session_state.df and auto-map images
if "data" in grid_response:
    if isinstance(grid_response["data"], pd.DataFrame):
        new_df = grid_response["data"]
    else:
        new_df = pd.DataFrame(grid_response["data"])
    
    # Auto-map images if folder is set and design names changed
    if st.session_state.image_folder and os.path.exists(st.session_state.image_folder):
        images = []
        for val in new_df["Design Name"]:
            img_path = ""
            if pd.notna(val) and str(val).strip():
                for ext in [".png", ".jpg", ".jpeg", ".bmp"]:
                    possible = os.path.join(st.session_state.image_folder, str(val).strip() + ext)
                    if os.path.exists(possible):
                        img_path = possible
                        break
            images.append(img_path)
        new_df["Design Image"] = images
    
    st.session_state.df = new_df
    save_data()  # Save data after changes

# --- Path Binding Section ---
st.write("### 🔗 Set Images Folder")
folder_input = st.text_input("📂 Enter folder path:", value=st.session_state.image_folder)

if folder_input != st.session_state.image_folder:
    folder = folder_input.strip()
    if folder and os.path.exists(folder):
        st.session_state.image_folder = folder
        save_data()  # Save data after folder change
        st.success(f"✅ Path set to: {folder}")
        st.rerun()
    elif folder:
        st.error("❌ Invalid folder path.")

# --- Show Images Preview ---
if not st.session_state.df.empty and any(st.session_state.df["Design Image"]):
    st.write("### 📋 Images Preview")
    
    # Filter rows with images
    rows_with_images = st.session_state.df[st.session_state.df["Design Image"] != ""]
    
    if not rows_with_images.empty:
        cols = st.columns(min(3, len(rows_with_images)))
        for idx, (_, row) in enumerate(rows_with_images.iterrows()):
            if idx < len(cols) and row["Design Image"]:
                try:
                    img = Image.open(row["Design Image"])
                    img = img.resize((200, 150))
                    cols[idx].image(img, caption=f"{row['No']}. {row['Design Name']}")
                except:
                    cols[idx].write(f"❌ {row['Design Name']} - Image not found")

# --- PDF Generation Function ---
def generate_pdf(df):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)

    # Ensure we only use the 3 main columns
    df_clean = df[["No", "Design Name", "Design Image"]].copy()
    
    page_width = pdf.w - 2 * pdf.l_margin
    col_widths = [0.1 * page_width, 0.35 * page_width, 0.55 * page_width]
    pdf.set_fill_color(200, 200, 200)

    # Header
    for i, col_name in enumerate(df_clean.columns):
        pdf.cell(col_widths[i], 12, col_name, border=1, align='C', fill=True)
    pdf.ln()

    # Rows
    for _, row in df_clean.iterrows():
        img_path = row["Design Image"]
        max_img_height = 50
        img_height = max_img_height
        img_width = col_widths[2] - 4

        if img_path and os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                w, h = img.size
                aspect = h / w
                img_height = min(max_img_height, aspect * img_width)
            except:
                img_path = None

        row_height = max(12, img_height + 4)

        pdf.cell(col_widths[0], row_height, str(row["No"]), border=1, align='C')
        pdf.cell(col_widths[1], row_height, str(row["Design Name"]), border=1, align='C')

        x = pdf.get_x()
        y = pdf.get_y()
        pdf.cell(col_widths[2], row_height, '', border=1)
        if img_path:
            try:
                pdf.image(img_path, x + 2, y + 2, w=img_width, h=img_height)
            except:
                pdf.set_xy(x, y)
                pdf.multi_cell(col_widths[2], row_height, "Image Error", border=0, align='C')
        pdf.ln(row_height)
    return pdf

# --- Download as PDF ---
if st.button("📥 Download as PDF"):
    if not st.session_state.df.empty:
        pdf = generate_pdf(st.session_state.df)
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name="Designs_Table.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("No data available to generate PDF.")
