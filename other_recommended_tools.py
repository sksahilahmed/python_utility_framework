import pandas as pd
import json


def normalize_column_name(col_name):
    """Normalize column name for comparison."""
    return str(col_name).strip().lower()


def find_column(df, search_terms):
    """Find a column by searching for any of the search terms (case-insensitive, trimmed)."""
    normalized_cols = {normalize_column_name(col): col for col in df.columns}
    search_terms_lower = [normalize_column_name(term) for term in search_terms]

    for term in search_terms_lower:
        if term in normalized_cols:
            return normalized_cols[term]
    return None


def normalize_value(val):
    """Normalize a cell value for comparison."""
    if pd.isna(val):
        return None
    return str(val).strip().lower()


def calculate_other_recommended_tools(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate 'Other Recommended Tools' table with 5 rows.
    
    Row 1 (P1/P2): Total priority count / total number of months
    Row 2 (FLR): (L1.5 count / months) / (total all tickets / months)
    Row 3 (Triaging Effort): (L2 count / months) / 1300
    Rows 4-5: Placeholder rows (left as they are now)
    
    2nd column shows values only if conditions are met:
    - P1/P2 >= 10
    - FLR < 30% (0.30)
    - Triaging Effort > 1 FTE
    """
    
    # Find required columns
    col_l1l2 = find_column(df, ["L1_L2", "L1/L2", "L1/l2", "L1_l2"])
    if not col_l1l2:
        raise ValueError("Column 'L1_L2' not found in merged DataFrame")
    
    col_priority = find_column(df, ["Priority", "priority"])
    if not col_priority:
        raise ValueError("Column 'Priority' not found in merged DataFrame")
    
    col_closed_month = find_column(df, ["Closed Month", "ClosedMonth"])
    num_months = 1
    if col_closed_month:
        unique_months = df[col_closed_month].dropna().unique()
        num_months = len(unique_months) or 1
    
    # Calculate totals
    total_l1_5 = df[col_l1l2].apply(normalize_value).eq("l1.5").sum()
    total_l2 = df[col_l1l2].apply(normalize_value).eq("l2").sum()
    total_all_tickets = len(df)
    
    # Count P1 and P2 rows (count rows where Priority contains "P1" or "P2")
    priority_col_normalized = df[col_priority].apply(normalize_value)
    total_p1_p2 = priority_col_normalized.isin(["p1", "p2"]).sum()
    
    # Row 1: P1/P2 = total P1/P2 count / total number of months
    p1_p2_value = total_p1_p2 / num_months if num_months > 0 else 0
    
    # Row 2: FLR = (total L1.5 / months) / (total all tickets / months)
    l1_5_per_month = total_l1_5 / num_months if num_months > 0 else 0
    all_tickets_per_month = total_all_tickets / num_months if num_months > 0 else 0
    flr_value = (l1_5_per_month / all_tickets_per_month * 100) if all_tickets_per_month > 0 else 0  # as percentage
    
    # Row 3: Triaging Effort = (total L2 / months) / 1300
    l2_per_month = total_l2 / num_months if num_months > 0 else 0
    triaging_effort_value = l2_per_month / 1300 if 1300 > 0 else 0
    
    # Determine if values should be shown based on conditions
    show_p1_p2 = p1_p2_value >= 10
    show_flr = flr_value < 30
    show_triaging_effort = triaging_effort_value > 1
    
    # Build summary rows with values and conditions for tooltips
    summary_rows = [
        {
            "Tool": "P1/P2",
            "Current": round(p1_p2_value, 4),
            "Condition": ">=10",
            "Met": "✓" if show_p1_p2 else "✗"
        },
        {
            "Tool": "FLR",
            "Current": f"{round(flr_value, 2)}%",
            "Condition": "<30%",
            "Met": "✓" if show_flr else "✗"
        },
        {
            "Tool": "Triaging Effort",
            "Current": round(triaging_effort_value, 4),
            "Condition": ">1 FTE",
            "Met": "✓" if show_triaging_effort else "✗"
        },
        {
            "Tool": "Placeholder 1",
            "Current": "-",
            "Condition": "-",
            "Met": "-"
        },
        {
            "Tool": "Placeholder 2",
            "Current": "-",
            "Condition": "-",
            "Met": "-"
        },
    ]
    
    results_df = pd.DataFrame(summary_rows)
    
    # Store raw values for reference
    raw_data = {
        "p1_p2": round(p1_p2_value, 4),
        "flr_percentage": round(flr_value, 2),
        "triaging_effort": round(triaging_effort_value, 4),
        "total_p1_p2": int(total_p1_p2),
        "total_l1_5": int(total_l1_5),
        "total_l2": int(total_l2),
        "total_all_tickets": int(total_all_tickets),
        "num_months": int(num_months),
        "conditions_met": {
            "p1_p2_show": bool(show_p1_p2),
            "flr_show": bool(show_flr),
            "triaging_effort_show": bool(show_triaging_effort)
        }
    }
    
    return results_df, raw_data


def main(file_path):
    df = pd.read_excel(file_path, sheet_name=0)
    print(f"Loaded {len(df)} rows from {file_path}")
    results_df, raw_data = calculate_other_recommended_tools(df)
    print("\n=== Other Recommended Tools ===")
    print(results_df.to_string(index=False))
    print("\n=== Raw Calculation Data ===")
    print(json.dumps(raw_data, indent=2))


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python other_recommended_tools.py <excel_file_path>")
        sys.exit(1)
    main(sys.argv[1])
