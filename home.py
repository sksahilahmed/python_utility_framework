"""
Streamlit app entrypoint for uploading an Excel/CSV and running merge -> calculations -> dashboard.
Run with: `streamlit run home.py`
"""

import io
import traceback
import pandas as pd
import streamlit as st

# Import the project's processing functions
try:
    from merge_by_subgroup_final import merge_file
except Exception:
    merge_file = None

try:
    from process_excel import process_dataframe
except Exception:
    process_dataframe = None

try:
    import dashboard
except Exception:
    dashboard = None


st.set_page_config(page_title="Merge & Dashboard", layout="wide")

st.title("Merge by Subgroup — Upload and Analyze")
st.markdown("Upload an `.xlsx`, `.xls` or `.csv` file. The app will match tickets to lookup keywords and show merged results. Then run calculations and render the dashboard.")

uploader = st.file_uploader("Upload Excel or CSV", type=["xlsx", "xls", "csv"])
show_raw = st.checkbox("Show raw uploaded file", value=False)

# session state for persistence
if 'merged_df' not in st.session_state:
    st.session_state['merged_df'] = None
if 'unmatched_df' not in st.session_state:
    st.session_state['unmatched_df'] = None
if 'log_info' not in st.session_state:
    st.session_state['log_info'] = None
if 'results_df' not in st.session_state:
    st.session_state['results_df'] = None


def read_uploaded_file(uploaded) -> pd.DataFrame:
    """Read UploadedFile into pandas DataFrame using BytesIO/StringIO."""
    if uploaded.type == 'text/csv' or uploaded.name.lower().endswith('.csv'):
        try:
            content = uploaded.getvalue().decode('utf-8')
        except Exception:
            content = uploaded.getvalue().decode('latin-1')
        return pd.read_csv(io.StringIO(content))
    else:
        # Excel
        return pd.read_excel(io.BytesIO(uploaded.getvalue()), sheet_name=0)


if uploader is not None:
    try:
        df_input = read_uploaded_file(uploader)
    except Exception as e:
        st.error(f"Failed to read uploaded file: {e}")
        st.stop()

    if show_raw:
        st.subheader("Raw uploaded file (first 100 rows)")
        st.dataframe(df_input.head(100))

    if merge_file is None:
        st.error("Merge function not available. Ensure `merge_by_subgroup_final.py` is present and importable.")
        st.stop()

    # Perform merge with spinner
    with st.spinner("Matching uploaded data against lookup keywords..."):
        try:
            merged_df, unmatched_df, log_info = merge_file(df_input, source_filename=uploader.name)
            st.session_state['merged_df'] = merged_df
            st.session_state['unmatched_df'] = unmatched_df
            st.session_state['log_info'] = log_info
        except Exception as e:
            st.error(f"Merge failed: {e}")
            st.exception(traceback.format_exc())
            st.stop()

    # Summary
    total = log_info.get('total_rows', len(df_input))
    matched = log_info.get('matched_count', 0)
    unmatched = log_info.get('unmatched_count', 0)
    distinct = log_info.get('distinct_subgroups', 0)

    st.success(f"Merge complete — Total: {total}, Matched: {matched}, Unmatched: {unmatched}, Distinct subgroups: {distinct}")

    # Show first matches (if available)
    if log_info.get('first_matches'):
        st.subheader("First matches (sample)")
        st.table(pd.DataFrame(log_info.get('first_matches')))

    # Expanders for merged and unmatched
    with st.expander("Merged Results (first 100 rows)", expanded=True):
        st.dataframe(merged_df.head(100))
        # Download button
        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine='openpyxl') as writer:
            merged_df.to_excel(writer, index=False, sheet_name='Merged')
        towrite.seek(0)
        st.download_button("Download merged.xlsx", data=towrite.getvalue(), file_name='merged.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    with st.expander("Unmatched Rows (first 100 rows)"):
        st.dataframe(unmatched_df.head(100))
        # Download unmatched
        towrite2 = io.BytesIO()
        with pd.ExcelWriter(towrite2, engine='openpyxl') as writer:
            unmatched_df.to_excel(writer, index=False, sheet_name='Unmatched')
        towrite2.seek(0)
        st.download_button("Download unmatched.xlsx", data=towrite2.getvalue(), file_name='unmatched.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # Button to run calculations
    run_calc = st.button("Run calculations")
    if run_calc:
        if process_dataframe is None:
            st.error("Calculation function not available. Ensure `process_excel.py` is present and importable.")
            st.stop()

        with st.spinner("Running calculations..."):
            try:
                results_df = process_dataframe(merged_df)
                st.session_state['results_df'] = results_df
            except Exception as e:
                st.error(f"Processing failed: {e}")
                st.exception(traceback.format_exc())
                st.stop()

        # Show KPIs and table
        st.success("Calculations complete")
        st.subheader("Calculation Results")
        # Show numeric KPIs
        try:
            total_usecases = int(results_df['# of UseCases'].sum()) if '# of UseCases' in results_df.columns else 0
            total_fte = float(results_df['FTE'].sum()) if 'FTE' in results_df.columns else 0.0
            c1, c2 = st.columns(2)
            c1.metric("Total Usecases", f"{total_usecases}")
            c2.metric("Total FTE", f"{total_fte:.4f}")
        except Exception:
            pass

        st.dataframe(results_df)

        # Download calculated output
        towrite3 = io.BytesIO()
        with pd.ExcelWriter(towrite3, engine='openpyxl') as writer:
            results_df.to_excel(writer, index=False, sheet_name='Results')
        towrite3.seek(0)
        st.download_button("Download calculated_output.xlsx", data=towrite3.getvalue(), file_name='calculated_output.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        # Populate dashboard
        if dashboard is None:
            st.warning("Dashboard module not available. Ensure `dashboard.py` is present.")
        else:
            try:
                dashboard.populate_dashboard(results_df, show_on_streamlit=True)
            except Exception as e:
                st.error(f"Dashboard rendering failed: {e}")
                st.exception(traceback.format_exc())

    # Persist in session_state
    st.info("You can re-run calculations or download outputs. Data is stored in this session.")
else:
    st.info("Upload a file to begin. You can also generate a sample with the 'Sample' button below.")

    if st.button("Generate sample input"):
        # Create a tiny sample DataFrame
        sample = pd.DataFrame({
            'description': [
                'Reset user password for HR system',
                'Unable to access VPN from home',
                'Request to change email signature template'
            ],
            'Closed Month': ['2025-10', '2025-10', '2025-10']
        })
        st.dataframe(sample)
        st.write("Download this sample and adapt it to your data model.")
        b = io.BytesIO()
        with pd.ExcelWriter(b, engine='openpyxl') as writer:
            sample.to_excel(writer, index=False, sheet_name='Sheet1')
        b.seek(0)
        st.download_button("Download sample.xlsx", data=b.getvalue(), file_name='sample_input.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# End of home.py
