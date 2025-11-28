import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
import pandas as pd
import threading

_lock = threading.Lock()

# Constants for colors and fonts
TEAL_START = "#2E8CA8"
TEAL_END = "#1F6C86"
TEAL = "#2E8CA8"
LIGHT_TEAL = "#BFE2EA"
GRID_LINE_COLOR = "#D9D9D9"
FONT_FAMILY = "Segoe UI, Calibri, sans-serif"

# Helper functions

def set_page_config():
    st.set_page_config(
        page_title="Dashboard",
        layout="wide",
    )

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
    # Medium outer ring thickness: width=0.3 (as before) is okay; can increase if needed, but 0.3 looks medium
    wedges, _ = ax.pie(sizes,
                       colors=colors,
                       startangle=90,
                       wedgeprops=dict(width=0.3, edgecolor='white'))

    # Draw circle in center to make it donut
    centre_circle = Circle((0, 0), 0.70, fc='white')
    ax.add_artist(centre_circle)

    # Center label with specified font weight and font family; matplotlib expects fontweight and fontfamily
    ax.text(
        0, 0, f"{value}%",
        ha='center',
        va='center',
        fontsize=12,
        fontweight='bold',
        fontfamily='Segoe UI'  # Using explicit font per user spec
    )

    # Label below chart, centered, with font family and size
    plt.text(
        0, -1.2, label,
        ha='center',
        va='center',
        fontsize=10,
        fontfamily='Segoe UI'
    )

    ax.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.
    plt.tight_layout()

    # Add alt text for accessibility in Streamlit: Streamlit does not support alt text in pyplot directly,
    # but we can add descriptive text below the chart for screen readers or visually
    st.pyplot(fig)
    plt.close(fig)

def render_donut_section():
    gradient_header("Utilization Graphs")
    cols = st.columns(3, gap="medium")
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
    # Define styling function
    def style_header(s):
        return [
            f'background: linear-gradient(90deg, {TEAL_START}, {TEAL_END});'
            'color: white;'
            'font-weight: bold;'
            f'font-family: {FONT_FAMILY};'
            'text-align: center;'
            'padding: 8px 12px;'
            'border: 1px solid '+GRID_LINE_COLOR+';'
            'height: 24px;'
            for v in s
        ]
    def style_cells(s):
        return [
            'padding: 8px 12px;'
            'border: 1px solid '+GRID_LINE_COLOR+';'
            f'font-family: {FONT_FAMILY};'
            'font-size: 10pt;'
            for v in s
        ]

    def style_remarks(s):
        return [
            'text-align: ' + remark_align + ';'
            'padding: 8px 12px;'
            'border: 1px solid '+GRID_LINE_COLOR+';'
            f'font-family: {FONT_FAMILY};'
            'font-size: 10pt;'
            for _ in s
        ]

    # Apply styles
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

    # Apply text align to remarks column if specified
    if 'Remarks/information icon' in df.columns:
        styled = styled.set_properties(subset=['Remarks/information icon'], **{'text-align': remark_align})

    # Set column widths with CSS
    # Note: pandas Styler does not support col widths in px or %. Might need to inject CSS manually, but streamlit may ignore.
    # So let’s proceed with default and try to use st.markdown CSS for width if applicable.

    return styled

def render_overall_rl_section():
    gradient_header("Overall RL")
    # Data as specified
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
    # Set column widths: 15%, 10%, 75% - approximate
    styled = styled_table(df, col_widths=[0.15, 0.10, 0.75], remark_align='left')
    st.dataframe(styled)

def render_optimization_summary_section():
    gradient_header("Optimization Summary")
    data = {
        "Lever": [
            "Elimination",
            "Automation",
            "Standard Automation",
            "Agentic AI",
            "Left Shift"
        ],
        "# of Usecases": ["", "", "", "", ""],
        "FTE": ["", "", "", "", ""]
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
    }]).set_properties(subset=['Lever'], **{'font-weight':'bold', 'padding': '8px 12px', 'font-family': FONT_FAMILY, 'font-size':'10pt'})
    )

def render_other_tools_section():
    gradient_header("Other Recommended Tools")
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

    # prepare rows where last row only contains "ServiceNow Performance Analytics" spanning across narrative if needed
    # Build dataframe for left and right columns - last row right column is only tool, left is empty or merged

    # We'll create a DataFrame with two columns, last row left: "ServiceNow Performance Analytics" and right blank (or could invert)
    left_col = criteria + ["ServiceNow Performance Analytics"]
    right_col = tools + [""]

    df = pd.DataFrame({
        "Criteria/Recommendation": left_col,
        "Tool/Action": right_col
    })

    # Use styled_table for consistent styling
    styled = styled_table(df, col_widths=[0.6, 0.4], remark_align='left')
    st.dataframe(styled)


def render_gradewise_mnm_rl_section():
    gradient_header("GradeWise MnM RL")
    # Header row columns top:
    columns = ["", "M1", "M2", "M3", "M4", "M5", "M6", "M7",
               "M8", "M9", "M10", "11", "M12", "M13", "M14",
               "M15", "M16", "M17", "M18"]
    rows = [
        "Grade", "PAT/PT", "PA/P", "A", "SA", "M", "SM"
    ]
    # Create empty dataframe with columns and rows
    data = {col: [""] * len(rows) for col in columns}
    data[columns[0]] = rows
    df = pd.DataFrame(data)

    # Style header row with teal bar and white text, center aligned
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

    # Use styled_table for consistent styling including row heights and cell padding
    styled = styled_table(df, col_widths=None, remark_align='center', row_heights=24)

    # Override header style explicitly to ensure teal gradient for header cells
    styled = styled.set_table_styles(header_style + [
        {'selector': 'td', 'props': [
            ('border', f'1px solid {GRID_LINE_COLOR}'),
            ('height', '24px'),
            ('padding', '8px 12px'),
            ('font-family', FONT_FAMILY),
            ('font-size', '10pt')
        ]}
    ], overwrite=False)

    # Additional alignment for first column (rows) to bold and center
    styled = styled.set_properties(subset=[columns[0]], **{'font-weight': 'bold', 'text-align': 'center'})

    st.dataframe(styled)


def populate_dashboard(results_df, show_on_streamlit: bool = True):
    """
    Render dashboard charts and KPIs from results_df (DataFrame with Lever rows).
    If show_on_streamlit=False, returns a dict of figures/data instead of rendering.
    """
    # Expecting results_df to have columns: 'Lever', '# of UseCases', 'Volume', 'FTE'
    if results_df is None or len(results_df) == 0:
        if show_on_streamlit:
            st.warning("No results to display in dashboard.")
        return None

    # Compute totals
    total_usecases = int(results_df['# of UseCases'].sum()) if '# of UseCases' in results_df.columns else 0
    total_fte = float(results_df['FTE'].sum()) if 'FTE' in results_df.columns else 0.0

    if show_on_streamlit:
        set_page_config()
        st.markdown("### Calculation Results")
        cols = st.columns(3)
        cols[0].metric("Total Usecases", f"{total_usecases}")
        cols[1].metric("Total FTE", f"{total_fte:.4f}")
        cols[2].metric("Distinct Levers", f"{len(results_df)}")

        # Bar chart for ticket volumes or FTE per lever
        st.markdown("### Lever breakdown")
        chart_df = results_df.set_index('Lever')[["# of UseCases", 'FTE']].fillna(0)
        st.bar_chart(chart_df['# of UseCases'])

        st.markdown("### Detailed table")
        st.dataframe(results_df)
        return None
    else:
        return {
            'total_usecases': total_usecases,
            'total_fte': total_fte,
            'results_df': results_df
        }

def main():
    set_page_config()
    # Apply global CSS for font, background and spacing per user specs
    st.markdown(f"""
    <style>
        /* Global container styles */
        .block-container {{
            padding: 0.5in 0.5in 0.5in 0.5in; /* page margins 0.5 inch all sides */
            background-color: white;
            font-family: 'Segoe UI', Calibri, sans-serif;
            font-size: 10pt;
            color: black;
        }}

        /* Section spacing: about 12-16px between blocks */
        .section-spacing {{
            margin-top: 14px;
            margin-bottom: 14px;
        }}

        /* Header bar text styling */
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

        /* Dataframe containers */
        .stDataFrame, .stTable {{
            max-width: 100%;
            /* Padding inside table containers is controlled by pandas style */
        }}
    </style>
    """, unsafe_allow_html=True)

    # Layout with left and right columns for first 4 sections
    left_col, right_col = st.columns([1,1], gap="large")
    with left_col:
        render_donut_section()
        st.write("")  # spacing about 12-16 px
        render_overall_rl_section()
    with right_col:
        render_optimization_summary_section()
        st.write("")  # spacing about 12-16 px
        render_other_tools_section()

    # Span full width for GradeWise MnM RL at bottom
    st.write("")  # spacing about 16 px
    render_gradewise_mnm_rl_section()

if __name__ == "__main__":
    main()
