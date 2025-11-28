"""
merge_by_subgroup_final.py - stable DataFrame API implementation

Provides `merge_file(df_input, source_filename=None)`.
"""

import os
import json
import traceback
import sys
from typing import List, Tuple, Optional
from datetime import datetime

import pandas as pd


def find_column_case_insensitive(df: pd.DataFrame, names: List[str]) -> Optional[str]:
    lower_map = {str(col).strip().lower(): col for col in df.columns}
    for n in names:
        key = str(n).strip().lower()
        if key in lower_map:
            return lower_map[key]
    return None


def load_excel_file(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found.")
    return pd.read_excel(path, sheet_name=0)


def match_keyword_in_text(text: str, keyword: str) -> Tuple[bool, float]:
    if not text or not keyword:
        return False, 0.0
    text_lower = text.lower()
    kw_lower = keyword.lower()
    if kw_lower in text_lower:
        return True, 1.0
    kw_tokens = [t for t in kw_lower.split() if t]
    text_tokens = set(text_lower.split())
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'and', 'or', 'of', 'to', 'for', 'in', 'on', 'at', 'by', 'with', 'from', 'not', 'no', 'can', 'could', 'should', 'would', 'user', 'request', 'issue'}
    kw_tokens_meaningful = [t for t in kw_tokens if t not in stop_words]
    if not kw_tokens_meaningful:
        return False, 0.0
    matching_tokens = sum(1 for kt in kw_tokens_meaningful if kt in text_tokens)
    match_ratio = matching_tokens / len(kw_tokens_meaningful)
    if match_ratio == 1.0:
        return True, 0.85
    elif match_ratio >= 0.60:
        score = 0.60 + (match_ratio * 0.20)
        return True, score
    elif match_ratio >= 0.33:
        score = 0.50 + (match_ratio * 0.15)
        return True, score
    else:
        return False, 0.0


def find_best_keyword_match(text: str, keywords: List[str]) -> Optional[Tuple[str, float]]:
    if not text or not keywords:
        return None
    for keyword in keywords:
        is_match, score = match_keyword_in_text(text, keyword)
        if is_match and score >= 0.50:
            return keyword, score
    return None


def merge_file(df_input: pd.DataFrame, source_filename: str = None) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Process input DataFrame by matching subgroup keywords.

    Returns: (merged_df, unmatched_df, log_info)
    """
    lookup_path = "lookup.xlsx"
    if not os.path.exists(lookup_path):
        raise FileNotFoundError("lookup.xlsx not found in working directory")
    df_lookup = load_excel_file(lookup_path)

    df_input = df_input.copy()
    total_input_rows = len(df_input)
    input_cols = list(df_input.columns)

    desc_col = find_column_case_insensitive(df_input, ["description"])
    if desc_col is None:
        raise ValueError("Input DataFrame missing 'description' column")

    subgroup_col = find_column_case_insensitive(df_lookup, ["subgroup"])
    if subgroup_col is None:
        raise ValueError("Lookup file missing 'subgroup' column")

    # Enrichment lookup columns (best-effort)
    usecase_col = find_column_case_insensitive(df_lookup, ["usecase", "use case"])
    automation_col = find_column_case_insensitive(df_lookup, ["automation feasibility"])
    approach_col = find_column_case_insensitive(df_lookup, ["automation approach"])
    leftshift_col = find_column_case_insensitive(df_lookup, ["left shift feasibility"])
    elimination_col = find_column_case_insensitive(df_lookup, ["elimination feasibility"])
    l1l2_col = find_column_case_insensitive(df_lookup, ["l1/l2", "l1", "l2"])

    lookup_cols = {
        'usecase': usecase_col,
        'automation': automation_col,
        'approach': approach_col,
        'leftshift': leftshift_col,
        'elimination': elimination_col,
        'l1l2': l1l2_col
    }

    lookup_subgroups_raw = df_lookup[subgroup_col].fillna("").astype(str).map(lambda s: s.strip()).tolist()
    keywords_unique = list(dict.fromkeys([s.strip().lower() for s in lookup_subgroups_raw if s.strip() != ""]))

    keyword_to_row = {}
    for idx in df_lookup.index:
        raw = str(df_lookup.at[idx, subgroup_col]).strip()
        norm = raw.lower()
        if norm == "":
            continue
        if norm not in keyword_to_row:
            keyword_to_row[norm] = {
                "lookup_index": int(idx),
                "lookup_row": df_lookup.loc[idx],
                "original_keyword": raw
            }

    all_results = []
    for in_idx in df_input.index:
        row = df_input.loc[in_idx]
        desc = row.get(desc_col, "")
        if pd.isna(desc):
            desc = ""
        desc_str = str(desc).strip()

        match = find_best_keyword_match(desc_str, keywords_unique)

        result = {
            "input_index": int(in_idx),
            "description": desc_str,
            "matched": match is not None,
            "keyword": None,
            "score": 0.0,
            "lookup_data": {}
        }

        if match:
            keyword_norm, score = match
            result["keyword"] = keyword_norm
            result["score"] = score
            lookup_entry = keyword_to_row.get(keyword_norm)
            if lookup_entry:
                result["lookup_data"] = {
                    "lookup_index": lookup_entry["lookup_index"],
                    "lookup_row": lookup_entry["lookup_row"],
                    "original_keyword": lookup_entry["original_keyword"]
                }

        all_results.append(result)

    matched_count = sum(1 for r in all_results if r["matched"])
    unmatched_count = len(all_results) - matched_count

    output_rows = []
    unmatched_rows = []
    first_matches = []
    for result in all_results:
        in_idx = result["input_index"]
        input_row = df_input.loc[in_idx]
        enriched = {}
        for col in input_cols:
            enriched[col] = input_row.get(col)

        if result["matched"] and result["lookup_data"]:
            lookup_row = result["lookup_data"]["lookup_row"]
            enriched["Matched_Keyword"] = result["lookup_data"].get("original_keyword", result["keyword"])
            enriched["Match_Score"] = round(result["score"], 2)
            enriched["UseCase"] = lookup_row.get(lookup_cols['usecase']) if lookup_cols['usecase'] else ""
            enriched["Automation_Feasibility"] = lookup_row.get(lookup_cols['automation']) if lookup_cols['automation'] else ""
            enriched["Automation_Approach"] = lookup_row.get(lookup_cols['approach']) if lookup_cols['approach'] else ""
            enriched["Left_Shift_Feasibility"] = lookup_row.get(lookup_cols['leftshift']) if lookup_cols['leftshift'] else ""
            enriched["Elimination_Feasibility"] = lookup_row.get(lookup_cols['elimination']) if lookup_cols['elimination'] else ""
            enriched["L1_L2"] = lookup_row.get(lookup_cols['l1l2']) if lookup_cols['l1l2'] else ""
            first_matches.append({
                "input_index": in_idx,
                "matched_subgroup": enriched.get("Matched_Keyword"),
                "match_score": enriched.get("Match_Score"),
                "lookup_row_id": result["lookup_data"].get("lookup_index")
            })
        else:
            enriched["Matched_Keyword"] = ""
            enriched["Match_Score"] = 0.0
            enriched["UseCase"] = "Others"
            enriched["Automation_Feasibility"] = "Unknown"
            enriched["Automation_Approach"] = "Unknown"
            enriched["Left_Shift_Feasibility"] = "Unknown"
            enriched["Elimination_Feasibility"] = "Unknown"
            enriched["L1_L2"] = "Unknown"
            unmatched_rows.append(enriched)

        output_rows.append(enriched)

    enriched_df = pd.DataFrame(output_rows)
    unmatched_df = pd.DataFrame(unmatched_rows)

    log_info = {
        "total_rows": total_input_rows,
        "matched_count": matched_count,
        "unmatched_count": unmatched_count,
        "distinct_subgroups": len(keywords_unique),
        "first_matches": first_matches[:10]
    }

    return enriched_df, unmatched_df, log_info


def main():
    try:
        input_path = "input.xlsx"
        print("=" * 80)
        print("TICKET PROCESSING & OPTIMIZATION ANALYSIS (CLI)")
        print("=" * 80)

        df_input = load_excel_file(input_path)
        enriched_df, unmatched_df, log_info = merge_file(df_input, source_filename=input_path)

        total_input_rows = log_info.get("total_rows", len(df_input))
        matched_count = log_info.get("matched_count", enriched_df.shape[0] - unmatched_df.shape[0])
        unmatched_count = log_info.get("unmatched_count", unmatched_df.shape[0])

        summary_data = []
        elimination_count = sum(1 for _, row in enriched_df.iterrows() if str(row.get("Elimination_Feasibility", "")).strip().lower() == "feasible")
        summary_data.append({"Lever": "Elimination", "# of UseCases": elimination_count, "Volume": total_input_rows, "FTE": round(elimination_count / 140, 2)})

        automation_count = sum(1 for _, row in enriched_df.iterrows() if str(row.get("Automation_Feasibility", "")).strip().lower() == "feasible")
        summary_data.append({"Lever": "Automation", "# of UseCases": automation_count, "Volume": total_input_rows, "FTE": round(automation_count / 140, 2)})

        standard_count = sum(1 for _, row in enriched_df.iterrows() if str(row.get("Automation_Approach", "")).strip().lower() == "standard")
        summary_data.append({"Lever": "Standard Automation", "# of UseCases": standard_count, "Volume": total_input_rows, "FTE": round(standard_count / 140, 2)})

        agentic_count = sum(1 for _, row in enriched_df.iterrows() if "agentic" in str(row.get("Automation_Approach", "")).strip().lower())
        summary_data.append({"Lever": "Agentic AI", "# of UseCases": agentic_count, "Volume": total_input_rows, "FTE": round(agentic_count / 140, 2)})

        leftshift_count = sum(1 for _, row in enriched_df.iterrows() if str(row.get("Left_Shift_Feasibility", "")).strip().lower() == "feasible")
        summary_data.append({"Lever": "Left Shift", "# of UseCases": leftshift_count, "Volume": total_input_rows, "FTE": round(leftshift_count / 140, 2)})

        summary_df = pd.DataFrame(summary_data)

        output_filename = f"processed_tickets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            enriched_df.to_excel(writer, sheet_name='Enriched Data', index=False)
            summary_df.to_excel(writer, sheet_name='Optimization Summary', index=False)

        summary_json = {
            "generated_at": datetime.now().isoformat(),
            "total_tickets": total_input_rows,
            "matched": matched_count,
            "unmatched": unmatched_count,
            "match_rate": f"{(matched_count/total_input_rows*100):.1f}%",
            "summary": summary_data
        }
        with open("summary.json", "w") as f:
            json.dump(summary_json, f, indent=2)

        print(f"Saved: {output_filename} and summary.json")
        print("Processing complete.")

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
