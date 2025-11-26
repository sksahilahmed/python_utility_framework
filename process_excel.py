import pandas as pd
import json
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

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

def main(file_path):
    # Read Excel file
    df = pd.read_excel(file_path, sheet_name="Sheet1")
    logging.info(f"Loaded {len(df)} rows from Sheet1")
    
    # Find required columns (case-insensitive, trimmed search)
    col_l1l2 = find_column(df, ["L1/L2", "L1/l2"])
    if not col_l1l2:
        raise ValueError("Column 'L1/L2' not found")
    logging.info(f"Found L1/L2 column: '{col_l1l2}'")

    col_elim = find_column(df, ["Elimination"])
    if not col_elim:
        raise ValueError("Column 'Elimination' not found")
    logging.info(f"Found Elimination column: '{col_elim}'")

    col_usecase = find_column(df, ["Usecase", "Use Case"])
    if not col_usecase:
        raise ValueError("Column 'Usecase' not found")
    logging.info(f"Found Usecase column: '{col_usecase}'")

    col_closed_month = find_column(df, ["Closed Month", "ClosedMonth"])
    if not col_closed_month:
        raise ValueError("Column 'Closed Month' not found")
    logging.info(f"Found Closed Month column: '{col_closed_month}'")

    col_automation = find_column(df, ["Automation"])
    if not col_automation:
        raise ValueError("Column 'Automation' not found")
    logging.info(f"Found Automation column: '{col_automation}'")

    col_std_agentic = find_column(df, ["Std/Agentic", "Std/agentic", "Standard/Agentic"])
    if not col_std_agentic:
        raise ValueError("Column 'Std/Agentic' not found")
    logging.info(f"Found Std/Agentic column: '{col_std_agentic}'")

    col_left_shift = find_column(df, ["Left Shift", "LeftShift", "left shift"])
    if not col_left_shift:
        raise ValueError("Column 'Left Shift' not found")
    logging.info(f"Found Left Shift column: '{col_left_shift}'")

    # Get number of unique months
    unique_months = df[col_closed_month].dropna().unique()
    num_months = len(unique_months)
    logging.info(f"Number of unique months: {num_months}")
    
    # Since there's no explicit "Ticket Count" column, each row represents 1 ticket
    # For average monthly tickets: total_tickets / num_months
    
    # Total counts for L1.5 and L2 (entire sheet)
    total_count_ofL1_5 = df[col_l1l2].apply(normalize_value).eq("l1.5").sum()
    total_count_ofL2 = df[col_l1l2].apply(normalize_value).eq("l2").sum()
    logging.info(f"Total L1.5 rows: {total_count_ofL1_5}, Total L2 rows: {total_count_ofL2}")

    # ===== Elimination array =====
    # Filter for Elimination == "Feasible" AND L1/L2 == "L1.5"
    elim_df = df[(df[col_elim].apply(normalize_value).eq("feasible")) & 
                 (df[col_l1l2].apply(normalize_value).eq("l1.5"))]
    logging.info(f"Rows for elimination (Feasible & L1.5): {len(elim_df)}")
    
    elim_usecases = int(elim_df[col_usecase].nunique())
    elim_ticket_volume = len(elim_df) / num_months if num_months > 0 else 0
    elim_fte = elim_ticket_volume / 140
    elimination_array = [elim_usecases, round(elim_ticket_volume, 4), round(elim_fte, 4)]
    logging.info(f"Elimination: {elim_usecases} usecases, {round(elim_ticket_volume, 4)} ticket volume, {round(elim_fte, 4)} FTE")

    # ===== Automation array =====
    # Filter for Automation == "Feasible" AND L1/L2 == "L1.5"
    auto_df = df[(df[col_automation].apply(normalize_value).eq("feasible")) & 
                 (df[col_l1l2].apply(normalize_value).eq("l1.5"))]
    logging.info(f"Rows for automation (Feasible & L1.5): {len(auto_df)}")
    
    # Further filter for Std/Agentic == "Standard" OR "Standard/Agentic AI"
    std_agentic_normalized = auto_df[col_std_agentic].apply(normalize_value)
    auto_std_df = auto_df[std_agentic_normalized.eq("standard") | std_agentic_normalized.eq("standard/agentic ai")]
    logging.info(f"Rows for automation with Standard or Standard/Agentic AI: {len(auto_std_df)}")
    
    auto_usecases = int(auto_std_df[col_usecase].nunique())
    auto_ticket_volume = len(auto_std_df) / num_months if num_months > 0 else 0
    auto_fte = auto_ticket_volume / 140
    automation_array = [auto_usecases, round(auto_ticket_volume, 4), round(auto_fte, 4)]
    logging.info(f"Automation: {auto_usecases} usecases, {round(auto_ticket_volume, 4)} ticket volume, {round(auto_fte, 4)} FTE")

    # ===== Automation agent array =====
    # Filter for Automation == "Feasible" AND Std/Agentic == "Agentic AI" AND L1/L2 == "L1.5"
    agentic_df = df[(df[col_automation].apply(normalize_value).eq("feasible")) & 
                    (df[col_std_agentic].apply(normalize_value).eq("agentic ai")) &
                    (df[col_l1l2].apply(normalize_value).eq("l1.5"))]
    logging.info(f"Rows for automation agent (Feasible & Agentic AI & L1.5): {len(agentic_df)}")
    
    agentic_usecases = int(agentic_df[col_usecase].nunique())
    agentic_ticket_volume = len(agentic_df) / num_months if num_months > 0 else 0
    agentic_fte = agentic_ticket_volume / 140
    automation_agent_array = [agentic_usecases, round(agentic_ticket_volume, 4), round(agentic_fte, 4)]
    logging.info(f"Automation Agent: {agentic_usecases} usecases, {round(agentic_ticket_volume, 4)} ticket volume, {round(agentic_fte, 4)} FTE")

    # ===== Left shift array =====
    left_df = df[(df[col_left_shift].apply(normalize_value).eq("feasible")) & 
                 (df[col_l1l2].apply(normalize_value).eq("l1.5"))]
    logging.info(f"Rows for left shift (Feasible & L1.5): {len(left_df)}")
    
    left_usecases = int(left_df[col_usecase].nunique())
    left_ticket_volume = len(left_df) / num_months if num_months > 0 else 0
    left_fte = left_ticket_volume / 140
    left_shift_array = [left_usecases, round(left_ticket_volume, 4), round(left_fte, 4)]
    logging.info(f"Left Shift: {left_usecases} usecases, {round(left_ticket_volume, 4)} ticket volume, {round(left_fte, 4)} FTE")

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
    
    logging.info("Output saved to summary_output.json")
    
    # Print to stdout
    print("\n" + json.dumps(output, indent=4))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_excel.py <excel_file_path>")
        sys.exit(1)
    main(sys.argv[1])
