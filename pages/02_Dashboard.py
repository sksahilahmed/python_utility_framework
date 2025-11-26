import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
import pandas as pd
import threading
import json
import os

_lock = threading.Lock()

# Constants for colors and fonts
TEAL_START = "#2E8CA8"
TEAL_END = "#1F6C86"
TEAL = "#2E8CA8"
LIGHT_TEAL = "#BFE2EA"
GRID_LINE_COLOR = "#D9D9D9"
FONT_FAMILY = "Segoe UI, Calibri, sans-serif"

st.set_page_config(
    page_title="Dashboard - Analytics",
    layout="wide",
)

# Check if data is uploaded
if 'df_uploaded' not in st.session_state or st.session_state.df_uploaded is None:
    st.warning("⚠️ No data uploaded yet. Please go to Home page and upload an Excel file first.")
    st.info("Navigate using the sidebar: Home → Upload Excel → Process → View Dashboard")
    st.stop()

# Helper functions

def gradient_header(title):
    """Render a header bar with gradient teal background and white centered title text."""
    header_style = f'''
    <style>
        .header-bar {{
            background: linear-gradient(90deg, {TEAL_START}, {TEAL_END});
            color: white;
            font-weight: bold;
            font-size: 14pt;
            height: 24px;
            line-height: 24px;
            text-align: center;
            font-family: {FONT_FAMILY};
            margin-bottom: 12px;
            border-radius: 2px;
        }}
    </style>
    '''
    st.markdown(header_style, unsafe_allow_html=True)
    st.markdown(f'<div class="header-bar">{title}</div>', unsafe_allow_html=True)

def donut_chart(label, value, alt_text):
    """Create a donut chart with the specified parameters and render it in Streamlit."""
    remainder = 100 - value
    sizes = [value, remainder]
    colors = [TEAL, LIGHT_TEAL]

    fig, ax = plt.subplots(figsize=(2, 2), dpi=80, subplot_kw=dict(aspect="equal"))
    wedges, _ = ax.pie(sizes,
                       colors=colors,
                       startangle=90,
                       wedgeprops=dict(width=0.3, edgecolor='white'))

    centre_circle = Circle((0, 0), 0.70, fc='white')
    ax.add_artist(centre_circle)

    ax.text(
        0, 0, f"{value}%",
        ha='center',
        va='center',
        fontsize=12,
        fontweight='bold',
        fontfamily='Segoe UI'
    )

    plt.text(
        0, -1.2, label,
        ha='center',
        va='center',
        fontsize=10,
        fontfamily='Segoe UI'
    )

    ax.axis('equal')
    plt.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

def render_donut_section(donut_data=None):
    """Render donut charts section with option to use custom data."""
    gradient_header("Utilization Graphs")
    cols = st.columns(3, gap="medium")
    
    # Use provided data or default
    if donut_data is None:
        donut_data = [
            ("Triaging", 7, "Triaging donut 7%"),
            ("Non-Ticketed", 54, "Non-Ticketed donut 54%"),
            ("Ticketed", 39, "Ticketed donut 39%"),
        ]
    
    for col, (label, value, alttext) in zip(cols, donut_data):
        with col:
            donut_chart(label, value, alttext)

def styled_table(df, col_widths, remark_align='left', row_heights=None):
    """Render a styled table with specific column widths, colors, and spacing."""
    styled = df.style.set_table_styles([
        {'selector': 'th', 'props': [
            ('background', f'linear-gradient(90deg, {TEAL_START}, {TEAL_END})'),
            ('color', 'white'),
            ('font-weight', 'bold'),
            ('font-family', FONT_FAMILY),
            ('text-align', 'center'),
            ('padding', '8px 12px'),
            ('border', f'1px solid {GRID_LINE_COLOR}'),
            ('height', '24px')
        ]},
        {'selector': 'td', 'props': [
            ('padding', '8px 12px'),
            ('border', f'1px solid {GRID_LINE_COLOR}'),
            ('font-family', FONT_FAMILY),
            ('font-size', '10pt')
        ]}
    ])

    if 'Remarks/information icon' in df.columns:
        styled = styled.set_properties(subset=['Remarks/information icon'], **{'text-align': remark_align})

    return styled

def render_overall_rl_section(data=None):
    """Render Overall RL section with option to use custom data."""
    gradient_header("Overall RL")
    
    if data is None:
        data = {
            "Period": ["H1Y1", "H2Y1", "H1Y2"],
            "RL": ["", "", ""],
            "Remarks/information icon": [
                "140 Tickets productivity No automation",
                "160 Tickets productivity 50% automation",
                "160 Tickets productivity, 100% Automation + Left Shift"
            ]
        }
    
    df = pd.DataFrame(data)
    styled = styled_table(df, col_widths=[0.15, 0.10, 0.75], remark_align='left')
    st.dataframe(styled, use_container_width=True)

def render_optimization_summary_section(data=None):
    """Render Optimization Summary with option to use custom data."""
    gradient_header("Optimization Summary")
    
    if data is None:
        # Try to load from session state first
        if 'summary_data' in st.session_state and st.session_state.summary_data:
            summary_data = st.session_state.summary_data
        # Otherwise try to load from summary_output.json
        elif os.path.exists("summary_output.json"):
            try:
                with open("summary_output.json", "r") as f:
                    summary_data = json.load(f)
            except Exception as e:
                st.error(f"Error loading summary data: {e}")
                summary_data = None
        else:
            summary_data = None
        
        if summary_data:
            data = {
                "Lever": [
                    "Elimination",
                    "Automation",
                    "Automation-Agentic AI",
                    "Left Shift"
                ],
                "# of Usecases": [
                    summary_data.get("elimination_array", [0, 0, 0])[0],
                    summary_data.get("automation_array", [0, 0, 0])[0],
                    summary_data.get("automation_agent_array", [0, 0, 0])[0],
                    summary_data.get("left_shift_array", [0, 0, 0])[0]
                ],
                "Ticket Volume": [
                    summary_data.get("elimination_array", [0, 0, 0])[1],
                    summary_data.get("automation_array", [0, 0, 0])[1],
                    summary_data.get("automation_agent_array", [0, 0, 0])[1],
                    summary_data.get("left_shift_array", [0, 0, 0])[1]
                ],
                "FTE": [
                    summary_data.get("elimination_array", [0, 0, 0])[2],
                    summary_data.get("automation_array", [0, 0, 0])[2],
                    summary_data.get("automation_agent_array", [0, 0, 0])[2],
                    summary_data.get("left_shift_array", [0, 0, 0])[2]
                ]
            }
        else:
            data = {
                "Lever": [
                    "Elimination",
                    "Automation",
                    "Automation-Agentic AI",
                    "Left Shift"
                ],
                "# of Usecases": ["", "", "", ""],
                "Ticket Volume": ["", "", "", ""],
                "FTE": ["", "", "", ""]
            }
    
    df = pd.DataFrame(data)
    st.dataframe(df.style.set_table_styles([{
        'selector': 'th',
        'props': [
            ('background', f'linear-gradient(90deg, {TEAL_START}, {TEAL_END})'),
            ('color', 'white'),
            ('font-weight', 'bold'),
            ('font-family', FONT_FAMILY),
            ('text-align', 'center'),
            ('padding', '8px 12px'),
            ('border', f'1px solid {GRID_LINE_COLOR}'),
            ('height', '24px')
        ]
    }]).set_properties(subset=['Lever'], **{'font-weight':'bold', 'padding': '8px 12px', 'font-family': FONT_FAMILY, 'font-size':'10pt'}),
    use_container_width=True)

def render_other_tools_section(data=None):
    """Render Other Recommended Tools with option to use custom data."""
    gradient_header("Other Recommended Tools")
    
    if data is None:
        criteria = [
            "P1/P2 >= 10",
            "FLR <30%",
            "Triaging Effort >1 FTE",
            "Service Improvement Recommendation"
        ]
        tools = [
            "CRTSIT Assist",
            "SOP Genius Recommended",
            "Auto Ticket Triaging",
            "Ticket Quality Audit Tool",
        ]
        left_col = criteria + ["ServiceNow Performance Analytics"]
        right_col = tools + [""]
        
        data = {
            "Criteria/Recommendation": left_col,
            "Tool/Action": right_col
        }
    
    df = pd.DataFrame(data)
    styled = styled_table(df, col_widths=[0.6, 0.4], remark_align='left')
    st.dataframe(styled, use_container_width=True)

def render_gradewise_mnm_rl_section(data=None):
    """Render GradeWise MnM RL section with option to use custom data."""
    gradient_header("GradeWise MnM RL")
    
    if data is None:
        columns = ["", "M1", "M2", "M3", "M4", "M5", "M6", "M7",
                   "M8", "M9", "M10", "11", "M12", "M13", "M14",
                   "M15", "M16", "M17", "M18"]
        rows = [
            "Grade", "PAT/PT", "PA/P", "A", "SA", "M", "SM"
        ]
        data_dict = {col: [""] * len(rows) for col in columns}
        data_dict[columns[0]] = rows
        data = pd.DataFrame(data_dict)
    
    header_style = [{
        'selector': 'th',
        'props': [
            ('background', f'linear-gradient(90deg, {TEAL_START}, {TEAL_END})'),
            ('color', 'white'),
            ('font-weight', 'bold'),
            ('font-family', FONT_FAMILY),
            ('text-align', 'center'),
            ('padding', '8px 12px'),
            ('border', f'1px solid {GRID_LINE_COLOR}'),
            ('height', '24px'),
            ('min-width', '50px')
        ]
    }]

    styled = data.style.set_table_styles(header_style + [
        {'selector': 'td', 'props': [
            ('border', f'1px solid {GRID_LINE_COLOR}'),
            ('height', '24px'),
            ('padding', '8px 12px'),
            ('font-family', FONT_FAMILY),
            ('font-size', '10pt')
        ]}
    ], overwrite=False)

    st.dataframe(styled, use_container_width=True)

def main():
    # Apply global CSS
    st.markdown(f"""
    <style>
        .block-container {{
            padding: 0.5in 0.5in 0.5in 0.5in;
            background-color: white;
            font-family: 'Segoe UI', Calibri, sans-serif;
            font-size: 10pt;
            color: black;
        }}

        .section-spacing {{
            margin-top: 14px;
            margin-bottom: 14px;
        }}

        .header-bar {{
            height: 24px;
            line-height: 24px;
            font-weight: bold;
            font-size: 14pt;
            color: white;
            text-align: center;
            font-family: 'Segoe UI', Calibri, sans-serif;
            border-radius: 2px;
            margin-bottom: 12px;
        }}

        .stDataFrame, .stTable {{
            max-width: 100%;
        }}
    </style>
    """, unsafe_allow_html=True)

    # Header with file info
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 Dashboard Analytics")
    with col2:
        if st.session_state.file_name:
            st.info(f"📁 File: {st.session_state.file_name}")
    st.markdown("---")

    # Layout with left and right columns for first 4 sections
    left_col, right_col = st.columns([1,1], gap="large")
    with left_col:
        render_donut_section()
        st.write("")
        render_overall_rl_section()
    with right_col:
        render_optimization_summary_section()
        st.write("")
        render_other_tools_section()

    # Full width section
    st.write("")
    render_gradewise_mnm_rl_section()
    
    st.markdown("---")
    st.info("💡 To update the data, go back to Home page and upload a new Excel file.")

if __name__ == "__main__":
    main()
