import streamlit as st
import pandas as pd
import io
import json
from pathlib import Path

st.set_page_config(
    page_title="Dashboard - Home",
    layout="wide",
)

st.markdown("""
<style>
    .header-title {
        text-align: center;
        font-size: 28pt;
        font-weight: bold;
        color: #2E8CA8;
        margin-bottom: 20px;
    }
    .upload-section {
        background-color: #f0f8ff;
        padding: 20px;
        border-radius: 5px;
        border: 2px solid #2E8CA8;
        margin-bottom: 20px;
    }
    .info-box {
        background-color: #e8f4f8;
        padding: 15px;
        border-left: 4px solid #2E8CA8;
        margin-bottom: 15px;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-title">📊 Automation Dashboard</div>', unsafe_allow_html=True)

st.markdown("---")

# Initialize session state
if 'df_uploaded' not in st.session_state:
    st.session_state.df_uploaded = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'summary_data' not in st.session_state:
    st.session_state.summary_data = None

def normalize_value(val):
    """Normalize a cell value for comparison."""
    if pd.isna(val):
        return None
    return str(val).strip().lower()

def find_column(df, search_terms):
    """Find a column by searching for any of the search terms (case-insensitive, trimmed)."""
    normalized_cols = {normalize_value(col): col for col in df.columns}
    search_terms_lower = [normalize_value(term) for term in search_terms]
    
    for term in search_terms_lower:
        if term in normalized_cols:
            return normalized_cols[term]
    return None

def process_excel_file(df):
    """Process Excel file and generate optimization summary."""
    try:
        # Find required columns (case-insensitive, trimmed search)
        col_l1l2 = find_column(df, ["L1/L2", "L1/l2"])
        if not col_l1l2:
            raise ValueError("Column 'L1/L2' not found")

        col_elim = find_column(df, ["Elimination"])
        if not col_elim:
            raise ValueError("Column 'Elimination' not found")

        col_usecase = find_column(df, ["Usecase", "Use Case"])
        if not col_usecase:
            raise ValueError("Column 'Usecase' not found")

        col_closed_month = find_column(df, ["Closed Month", "ClosedMonth"])
        if not col_closed_month:
            raise ValueError("Column 'Closed Month' not found")

        col_automation = find_column(df, ["Automation"])
        if not col_automation:
            raise ValueError("Column 'Automation' not found")

        col_std_agentic = find_column(df, ["Std/Agentic", "Std/agentic", "Standard/Agentic"])
        if not col_std_agentic:
            raise ValueError("Column 'Std/Agentic' not found")

        col_left_shift = find_column(df, ["Left Shift", "LeftShift", "left shift"])
        if not col_left_shift:
            raise ValueError("Column 'Left Shift' not found")

        # Get number of unique months
        unique_months = df[col_closed_month].dropna().unique()
        num_months = len(unique_months)
        
        if num_months == 0:
            raise ValueError("No valid months found in 'Closed Month' column")

        # Total counts for L1.5 and L2 (entire sheet)
        total_count_ofL1_5 = df[col_l1l2].apply(normalize_value).eq("l1.5").sum()
        total_count_ofL2 = df[col_l1l2].apply(normalize_value).eq("l2").sum()

        # ===== Elimination array =====
        elim_df = df[(df[col_elim].apply(normalize_value).eq("feasible")) & 
                     (df[col_l1l2].apply(normalize_value).eq("l1.5"))]
        
        elim_usecases = int(elim_df[col_usecase].nunique())
        elim_ticket_volume = len(elim_df) / num_months if num_months > 0 else 0
        elim_fte = elim_ticket_volume / 140
        elimination_array = [elim_usecases, round(elim_ticket_volume, 4), round(elim_fte, 4)]

        # ===== Automation array =====
        auto_df = df[(df[col_automation].apply(normalize_value).eq("feasible")) & 
                     (df[col_l1l2].apply(normalize_value).eq("l1.5"))]
        
        std_agentic_normalized = auto_df[col_std_agentic].apply(normalize_value)
        auto_std_df = auto_df[std_agentic_normalized.eq("standard") | std_agentic_normalized.eq("standard/agentic ai")]
        
        auto_usecases = int(auto_std_df[col_usecase].nunique())
        auto_ticket_volume = len(auto_std_df) / num_months if num_months > 0 else 0
        auto_fte = auto_ticket_volume / 140
        automation_array = [auto_usecases, round(auto_ticket_volume, 4), round(auto_fte, 4)]

        # ===== Automation agent array =====
        agentic_df = df[(df[col_automation].apply(normalize_value).eq("feasible")) & 
                        (df[col_std_agentic].apply(normalize_value).eq("agentic ai")) &
                        (df[col_l1l2].apply(normalize_value).eq("l1.5"))]
        
        agentic_usecases = int(agentic_df[col_usecase].nunique())
        agentic_ticket_volume = len(agentic_df) / num_months if num_months > 0 else 0
        agentic_fte = agentic_ticket_volume / 140
        automation_agent_array = [agentic_usecases, round(agentic_ticket_volume, 4), round(agentic_fte, 4)]

        # ===== Left shift array =====
        left_df = df[(df[col_left_shift].apply(normalize_value).eq("feasible")) & 
                     (df[col_l1l2].apply(normalize_value).eq("l1.5"))]
        
        left_usecases = int(left_df[col_usecase].nunique())
        left_ticket_volume = len(left_df) / num_months if num_months > 0 else 0
        left_fte = left_ticket_volume / 140
        left_shift_array = [left_usecases, round(left_ticket_volume, 4), round(left_fte, 4)]

        # ===== Generate output JSON =====
        output = {
            "total_count_ofL1.5": int(total_count_ofL1_5),
            "total_count_ofL2": int(total_count_ofL2),
            "elimination_array": elimination_array,
            "automation_array": automation_array,
            "automation_agent_array": automation_agent_array,
            "left_shift_array": left_shift_array
        }

        # Save to file
        with open("summary_output.json", "w") as f:
            json.dump(output, f, indent=4)
        
        return output, None
    except Exception as e:
        return None, str(e)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("📁 Upload Excel File")
    
    uploaded_file = st.file_uploader(
        "Choose an Excel file (.xlsx, .xls)",
        type=["xlsx", "xls"],
        help="Upload your data in Excel format. The file should contain data for the dashboard."
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("**📋 File Requirements:**")
    st.markdown("- Excel format (.xlsx or .xls)")
    st.markdown("- Structured data with headers")
    st.markdown("- Compatible with dashboard fields")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# File preview section
if uploaded_file is not None:
    st.subheader("📋 File Preview")
    
    try:
        # Read the Excel file
        excel_file = pd.ExcelFile(uploaded_file)
        
        # Show sheet names
        st.write(f"**Sheet Names:** {', '.join(excel_file.sheet_names)}")
        
        # Create tabs for each sheet
        sheet_tabs = st.tabs(excel_file.sheet_names)
        
        sheet_data = {}
        for idx, sheet_name in enumerate(excel_file.sheet_names):
            with sheet_tabs[idx]:
                df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                sheet_data[sheet_name] = df
                st.dataframe(df, use_container_width=True)
                st.write(f"**Rows:** {len(df)} | **Columns:** {len(df.columns)}")
        
        # Store in session state
        st.session_state.df_uploaded = sheet_data
        st.session_state.file_name = uploaded_file.name
        
    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")
        st.session_state.df_uploaded = None

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col2:
    st.markdown("")

with col2:
    if uploaded_file is not None and st.session_state.df_uploaded is not None:
        if st.button("✅ Process & Go to Dashboard", key="process_btn", use_container_width=True):
            # Get the sheet data (assuming first sheet for processing)
            sheet_names = list(st.session_state.df_uploaded.keys())
            df_to_process = st.session_state.df_uploaded[sheet_names[0]]
            
            # Process the file
            output, error = process_excel_file(df_to_process)
            
            if error:
                st.error(f"❌ Processing Error: {error}")
            else:
                st.session_state.processed = True
                st.session_state.summary_data = output
                st.success("✓ File processed successfully!")
                st.info("👉 Navigate to 'Dashboard' page to view your data")
                st.balloons()
    else:
        st.button("✅ Process & Go to Dashboard", disabled=True, use_container_width=True, 
                 help="Please upload a file first")

with col3:
    st.markdown("")

# Display status
if uploaded_file is not None:
    st.markdown("---")
    st.success(f"✓ File loaded: **{uploaded_file.name}**")
    if 'processed' in st.session_state and st.session_state.processed:
        st.info("✓ Ready to view dashboard. Use the sidebar to navigate to Dashboard page.")

# Instructions section
st.markdown("---")
st.subheader("📖 Instructions")

with st.expander("How to Use", expanded=False):
    st.markdown("""
    1. **Upload File**: Click the upload button above and select your Excel file
    2. **Preview Data**: Review the data in the preview section to ensure it's correct
    3. **Process**: Click the "Process & Go to Dashboard" button
    4. **View Dashboard**: Navigate to the Dashboard page using the sidebar
    5. **Analyze**: Review all dashboard sections with your data
    
    ### Expected Excel Format:
    - Sheet 1: Main data with columns matching dashboard fields
    - Ensure headers are in the first row
    - Data should be structured and clean
    """)
