import streamlit as st
import pandas as pd
import io
import json
from pathlib import Path
import traceback

# Try importing the new APIs if present
try:
    from merge_by_subgroup_final import merge_file
except Exception:
    merge_file = None

try:
    from process_excel import process_dataframe
except Exception:
    process_dataframe = None

try:
    from dashboard import populate_dashboard
except Exception:
    populate_dashboard = None

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

# Initialize session state with all necessary variables
if 'df_uploaded' not in st.session_state:
    st.session_state.df_uploaded = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'summary_data' not in st.session_state:
    st.session_state.summary_data = None
if 'merged_df' not in st.session_state:
    st.session_state.merged_df = None
if 'unmatched_df' not in st.session_state:
    st.session_state.unmatched_df = None
if 'results_df' not in st.session_state:
    st.session_state.results_df = None
if 'log_info' not in st.session_state:
    st.session_state.log_info = None

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
        # If new merge/process APIs exist, prefer using them (but here df is already the uploaded sheet)
        if process_dataframe is not None:
            # process_dataframe expects merged/enriched DF. If the uploaded sheet is already merged, call directly.
            output = process_dataframe(df)
            return output, None

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
# Support two scenarios:
# 1) A fresh `uploaded_file` from the uploader in this run; read it and store into session_state.
# 2) No fresh upload but previous upload present in `st.session_state.df_uploaded`; show that instead.
sheet_data = None
file_display_name = None
if uploaded_file is not None:
    st.subheader("📋 File Preview")
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        st.write(f"**Sheet Names:** {', '.join(excel_file.sheet_names)}")
        sheet_tabs = st.tabs(excel_file.sheet_names)
        sheet_data = {}
        for idx, sheet_name in enumerate(excel_file.sheet_names):
            with sheet_tabs[idx]:
                # read each sheet
                df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                sheet_data[sheet_name] = df
                st.dataframe(df, use_container_width=True)
                st.write(f"**Rows:** {len(df)} | **Columns:** {len(df.columns)}")
        # persist
        st.session_state.df_uploaded = sheet_data
        st.session_state.file_name = uploaded_file.name
        file_display_name = uploaded_file.name
    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")
        st.session_state.df_uploaded = None
else:
    # No fresh upload — check session_state for previous upload
    if 'df_uploaded' in st.session_state and st.session_state.df_uploaded:
        sheet_data = st.session_state.df_uploaded
        file_display_name = st.session_state.get('file_name', None)
        st.subheader("📋 File Preview (from previous upload)")
        try:
            sheet_names = list(sheet_data.keys())
            st.write(f"**Sheet Names:** {', '.join(sheet_names)}")
            sheet_tabs = st.tabs(sheet_names)
            for idx, sheet_name in enumerate(sheet_names):
                with sheet_tabs[idx]:
                    df = sheet_data[sheet_name]
                    st.dataframe(df, use_container_width=True)
                    st.write(f"**Rows:** {len(df)} | **Columns:** {len(df.columns)}")
        except Exception as e:
            st.error(f"❌ Error displaying stored file: {e}")
            st.session_state.df_uploaded = None
            sheet_data = None

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col2:
    st.markdown("")

with col2:
    # Allow processing when either a fresh upload exists or a stored upload is present in session_state
    has_uploaded = (uploaded_file is not None) or ('df_uploaded' in st.session_state and st.session_state.df_uploaded)
    if has_uploaded:
        if st.button("✅ Process & Go to Dashboard", key="process_btn", use_container_width=True):
            # Determine df to process: prefer persisted session data
            if 'df_uploaded' in st.session_state and st.session_state.df_uploaded:
                sheet_names = list(st.session_state.df_uploaded.keys())
                df_to_process = st.session_state.df_uploaded[sheet_names[0]]
            else:
                # fallback to reading the freshly uploaded file
                try:
                    excel_file = pd.ExcelFile(uploaded_file)
                    df_to_process = pd.read_excel(uploaded_file, sheet_name=excel_file.sheet_names[0])
                except Exception as e:
                    st.error(f"❌ Unable to read uploaded file for processing: {e}")
                    st.stop()

            # If merge API available, run merge -> process -> dashboard
            if merge_file is not None:
                try:
                    with st.spinner("Matching records using lookup keywords..."):
                        merged_df, unmatched_df, log_info = merge_file(df_to_process, source_filename=st.session_state.file_name)
                    st.session_state.merged_df = merged_df
                    st.session_state.unmatched_df = unmatched_df
                    st.session_state.log_info = log_info

                    # Show merged download
                    st.success(f"✓ Merge complete — Matched: {log_info.get('matched_count',0)}, Unmatched: {log_info.get('unmatched_count',0)}")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        buf = io.BytesIO()
                        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                            merged_df.to_excel(writer, index=False, sheet_name='Merged')
                        buf.seek(0)
                        st.download_button("Download merged.xlsx", data=buf.getvalue(), file_name='merged.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    with col_b:
                        buf2 = io.BytesIO()
                        with pd.ExcelWriter(buf2, engine='openpyxl') as writer:
                            unmatched_df.to_excel(writer, index=False, sheet_name='Unmatched')
                        buf2.seek(0)
                        st.download_button("Download unmatched.xlsx", data=buf2.getvalue(), file_name='unmatched.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

                except Exception as e:
                    st.error(f"❌ Merge failed: {e}")
                    st.exception(traceback.format_exc())
                    st.session_state.processed = False
                    st.stop()

                # After merge, run calculations if available
                if process_dataframe is not None:
                    try:
                        with st.spinner("Running calculations..."):
                            results_df = process_dataframe(merged_df)
                        st.session_state.results_df = results_df
                        st.session_state.processed = True
                        st.success("✓ Calculations complete")
                        # Show results download
                        buf3 = io.BytesIO()
                        with pd.ExcelWriter(buf3, engine='openpyxl') as writer:
                            results_df.to_excel(writer, index=False, sheet_name='Results')
                        buf3.seek(0)
                        st.download_button("Download calculated_output.xlsx", data=buf3.getvalue(), file_name='calculated_output.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                        # Render dashboard inline if function available
                        if populate_dashboard is not None:
                            try:
                                populate_dashboard(results_df, show_on_streamlit=True)
                            except Exception as e:
                                st.warning(f"Dashboard render failed: {e}")
                    except Exception as e:
                        st.error(f"❌ Processing Error: {e}")
                        st.exception(traceback.format_exc())
                        st.session_state.processed = False
                else:
                    # Fallback to older process function
                    output, error = process_excel_file(merged_df if 'merged_df' in st.session_state and st.session_state.merged_df is not None else df_to_process)
                    if error:
                        st.error(f"❌ Processing Error: {error}")
                    else:
                        st.session_state.processed = True
                        st.session_state.summary_data = output
                        st.success("✓ File processed successfully (fallback)!")
                        st.info("👉 Navigate to 'Dashboard' page to view your data")
                        st.balloons()
            else:
                # No merge API — fall back to processing the uploaded sheet directly
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

# Display status — show persisted info even when `uploaded_file` is None
st.markdown("---")
if 'file_name' in st.session_state and st.session_state.file_name:
    st.success(f"✓ File loaded: **{st.session_state.file_name}**")
elif uploaded_file is not None:
    st.success(f"✓ File loaded: **{uploaded_file.name}**")

if 'processed' in st.session_state and st.session_state.processed:
    st.info("✓ Ready to view dashboard. Use the sidebar to navigate to Dashboard page.")

# Persistent outputs: if processing has been done earlier, keep download buttons and summary visible
if 'merged_df' in st.session_state and st.session_state.merged_df is not None:
    st.markdown("---")
    st.subheader("📦 Processed Outputs (persistent)")
    log_info = st.session_state.get('log_info', {}) or {}
    matched = log_info.get('matched_count', None)
    unmatched = log_info.get('unmatched_count', None)
    if matched is not None and unmatched is not None:
        st.write(f"**Matched:** {matched} | **Unmatched:** {unmatched}")

    col_a, col_b, col_c = st.columns(3)
    merged_df = st.session_state.merged_df
    unmatched_df = st.session_state.unmatched_df
    results_df = st.session_state.results_df

    with col_a:
        try:
            buf_m = io.BytesIO()
            with pd.ExcelWriter(buf_m, engine='openpyxl') as writer:
                merged_df.to_excel(writer, index=False, sheet_name='Merged')
            buf_m.seek(0)
            st.download_button("Download merged.xlsx", data=buf_m.getvalue(), file_name='merged.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', key="merged-download")
        except Exception as e:
            st.warning(f"Could not prepare merged download: {e}")

    with col_b:
        try:
            buf_u = io.BytesIO()
            with pd.ExcelWriter(buf_u, engine='openpyxl') as writer:
                if unmatched_df is not None:
                    unmatched_df.to_excel(writer, index=False, sheet_name='Unmatched')
            buf_u.seek(0)
            st.download_button("Download unmatched.xlsx", data=buf_u.getvalue(), file_name='unmatched.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', key="unmatched-download")
        except Exception as e:
            st.warning(f"Could not prepare unmatched download: {e}")

    with col_c:
        try:
            if results_df is not None:
                buf_r = io.BytesIO()
                with pd.ExcelWriter(buf_r, engine='openpyxl') as writer:
                    results_df.to_excel(writer, index=False, sheet_name='Results')
                buf_r.seek(0)
                st.download_button("Download calculated_output.xlsx", data=buf_r.getvalue(), file_name='calculated_output.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', key="results-download")
            else:
                st.info("Calculations not yet run — click Process to compute results.")
        except Exception as e:
            st.warning(f"Could not prepare results download: {e}")


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
