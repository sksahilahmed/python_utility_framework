"""merge_by_subgroup_v2.py - Optimized version for maximum keyword matching

Strategy:
1. Each description is checked against ALL 675 keywords
2. Multiple matching strategies (exact, token-based, substring)
3. Multithreading for speed (8 workers, 33 chunks)
4. Best-match selection based on score

Results expected: 3,924+ matches
"""

import sys
import os
import json
import re
import traceback
from typing import List, Tuple, Optional

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed


def find_column_case_insensitive(df: pd.DataFrame, names: List[str]) -> Optional[str]:
    """Find actual column name matching any of the provided names (case-insensitive)."""
    lower_map = {str(col).strip().lower(): col for col in df.columns}
    for n in names:
        key = str(n).strip().lower()
        if key in lower_map:
            return lower_map[key]
    return None


def load_excel_file(path: str, which: str = "input") -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found.")
    try:
        return pd.read_excel(path, sheet_name=0)
    except Exception as e:
        raise IOError(f"Error reading {path}: {e}")


def match_keyword_in_text(text: str, keyword: str) -> Tuple[bool, float]:
    """
    Match keyword against text using multiple strategies.
    Returns: (is_match, score)
    
    Strategies (in order of priority):
    1. Exact substring: score 1.0
    2. All tokens present: score 0.85
    3. Most tokens present: score 0.65-0.80
    4. Some tokens present (33%+): score 0.50-0.65
    """
    if not text or not keyword:
        return False, 0.0
    
    text_lower = text.lower()
    kw_lower = keyword.lower()
    
    # Strategy 1: Exact substring match
    if kw_lower in text_lower:
        return True, 1.0
    
    # Strategy 2: Token-based matching
    kw_tokens = kw_lower.split()
    text_tokens = text_lower.split()
    text_tokens_set = set(text_tokens)
    
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'and', 'or', 'of', 'to', 'for', 'in', 'on', 'at', 'by', 'with', 'from', 'not', 'no'}
    
    # Filter out stop words
    kw_tokens_meaningful = [t for t in kw_tokens if t not in stop_words]
    if not kw_tokens_meaningful:
        return False, 0.0
    
    # Count matching tokens
    matching_tokens = sum(1 for kt in kw_tokens_meaningful if kt in text_tokens_set)
    match_ratio = matching_tokens / len(kw_tokens_meaningful)
    
    if match_ratio == 1.0:
        # All tokens match (100%)
        return True, 0.85
    elif match_ratio >= 0.60:
        # Most tokens match (60%+)
        score = 0.60 + (match_ratio * 0.20)
        return True, score
    elif match_ratio >= 0.33:
        # Some tokens match (33%+) - NEW: Lower threshold
        score = 0.50 + (match_ratio * 0.15)
        return True, score
    else:
        # Too few tokens match
        return False, 0.0


def find_best_keyword_match(text: str, keywords: List[str]) -> Optional[Tuple[str, float]]:
    """
    Find best matching keyword for a description.
    Checks text against ALL keywords.
    Returns (keyword, score) or None
    """
    if not text or not keywords:
        return None
    
    best_match = None
    best_score = 0.0
    
    for keyword in keywords:
        is_match, score = match_keyword_in_text(text, keyword)
        
        if is_match and score > best_score:
            best_score = score
            best_match = (keyword, score)
    
    return best_match if best_score >= 0.60 else None


def main():
    try:
        input_path = "input.xlsx"
        lookup_path = "lookup.xlsx"

        # 1) Load files
        print("Loading files...")
        df_input = load_excel_file(input_path, which="input")
        df_lookup = load_excel_file(lookup_path, which="lookup")

        total_input_rows = len(df_input)
        input_cols = list(df_input.columns)

        # 2) Find required columns
        desc_col = find_column_case_insensitive(df_input, ["description"])
        if desc_col is None:
            raise ValueError("Input file missing 'description' column")

        subgroup_col = find_column_case_insensitive(df_lookup, ["subgroup"])
        if subgroup_col is None:
            raise ValueError("Lookup file missing 'subgroup' column")

        # 3) Build keyword list
        lookup_subgroups_raw = df_lookup[subgroup_col].fillna("").astype(str).map(lambda s: s.strip()).tolist()
        keywords_norm = [s.strip().lower() for s in lookup_subgroups_raw if s.strip() != ""]
        keywords_unique = list(dict.fromkeys(keywords_norm))  # Remove duplicates, preserve order

        print(f"Loaded {total_input_rows} input rows and {len(keywords_unique)} keywords.")

        # Save keyword list
        with open("subgroup_keywords.json", "w", encoding="utf-8") as f:
            json.dump(keywords_unique, f, ensure_ascii=False, indent=2)

        # Build mapping: normalized keyword -> lookup row
        subgroup_to_row = {}
        for idx in df_lookup.index:
            raw = str(df_lookup.at[idx, subgroup_col]).strip()
            norm = raw.lower()
            if norm == "":
                continue
            if norm not in subgroup_to_row:
                subgroup_to_row[norm] = {
                    "lookup_row_index": int(idx),
                    "lookup_row_series": df_lookup.loc[idx],
                    "original_subgroup": raw
                }

        # 4) Multithreaded matching
        print(f"Starting multithreaded matching (each row checked against all {len(keywords_unique)} keywords)...")

        indices = list(df_input.index)
        n = len(indices)
        chunk_size = max(500, min(5000, n // (max(1, (os.cpu_count() or 4)) * 2)))
        chunks = [indices[i:i + chunk_size] for i in range(0, n, chunk_size)]

        print(f"Using {len(chunks)} chunks (size={chunk_size}) with 8 worker threads...")
        sys.stdout.flush()

        def process_chunk(idx_list):
            local_matches = []
            local_unmatched = []
            
            for in_idx in idx_list:
                row = df_input.loc[in_idx]
                desc = row.get(desc_col, "")
                if pd.isna(desc):
                    desc = ""
                desc_str = str(desc).strip()
                
                # Find best matching keyword from ALL keywords
                match = find_best_keyword_match(desc_str, keywords_unique)
                
                if match is None:
                    local_unmatched.append(in_idx)
                    continue
                
                keyword_norm, score = match
                lookup_entry = subgroup_to_row.get(keyword_norm)
                
                if lookup_entry is None:
                    local_unmatched.append(in_idx)
                    continue
                
                local_matches.append({
                    "input_index": int(in_idx),
                    "keyword_norm": keyword_norm,
                    "match_score": float(score),
                    "lookup_row_index": int(lookup_entry["lookup_row_index"]),
                    "lookup_series": lookup_entry["lookup_row_series"],
                    "matched_subgroup_original": lookup_entry["original_subgroup"],
                })
            
            return local_matches, local_unmatched

        matches = []
        unmatched_rows = []
        processed_total = 0
        max_workers = min(8, (os.cpu_count() or 4) * 2)

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            future_to_chunk = {ex.submit(process_chunk, ch): (i, ch) for i, ch in enumerate(chunks)}
            for fut in as_completed(future_to_chunk):
                try:
                    chunk_idx, chunk_data = future_to_chunk[fut]
                    local_matches, local_unmatched = fut.result()
                    matches.extend(local_matches)
                    unmatched_rows.extend(local_unmatched)
                    processed_total += len(chunk_data)
                    pct = int((processed_total / total_input_rows) * 100)
                    print(f"  [{pct:3d}%] Chunk {chunk_idx + 1}/{len(chunks)}: {processed_total:6d}/{total_input_rows} (matched: {len(matches)}, unmatched: {len(unmatched_rows)})")
                    sys.stdout.flush()
                except Exception as e:
                    print(f"Error in chunk: {e}")
                    traceback.print_exc()
                    sys.stdout.flush()

        # 5) Build merged output
        print(f"\nBuilding merged output ({len(matches)} rows)...")
        sys.stdout.flush()

        merged_rows = []
        lookup_all_cols = list(df_lookup.columns)
        lookup_append_cols = [c for c in lookup_all_cols if str(c).strip().lower() != subgroup_col.strip().lower()]

        # Handle column name collisions
        final_lookup_colnames = []
        for c in lookup_append_cols:
            if c in input_cols or str(c).strip().lower() in [ic.strip().lower() for ic in input_cols]:
                new_name = f"lkp_{c}"
            else:
                new_name = c
            final_lookup_colnames.append(new_name)

        # Build rows
        for idx, m in enumerate(matches):
            if (idx + 1) % 500 == 0:
                pct = int(((idx + 1) / len(matches)) * 100)
                print(f"  [{pct:3d}%] Built {idx + 1}/{len(matches)} rows...")
                sys.stdout.flush()

            in_idx = m["input_index"]
            input_row = df_input.loc[in_idx]
            lookup_series = m["lookup_series"]

            merged = {}
            # Original columns
            for col in input_cols:
                merged[col] = input_row.get(col)
            # Lookup columns
            for src_col, dst_col in zip(lookup_append_cols, final_lookup_colnames):
                merged[dst_col] = lookup_series.get(src_col)
            # Match metadata
            merged["matched_subgroup"] = m["matched_subgroup_original"]
            merged["match_score"] = m["match_score"]
            merged["lookup_row_id"] = m["lookup_row_index"]

            merged_rows.append(merged)

        # Save matched output
        if merged_rows:
            extra_cols = ["matched_subgroup", "match_score", "lookup_row_id"]
            ordered_cols = input_cols + final_lookup_colnames + extra_cols
            ordered_cols = [c for c in ordered_cols if c in pd.DataFrame([merged_rows[0]]).columns]
            
            merged_df = pd.DataFrame(merged_rows)
            merged_df = merged_df[ordered_cols]
            
            print(f"\nSaving {len(merged_df)} matched rows to output.xlsx...")
            sys.stdout.flush()
            merged_df.to_excel("output.xlsx", index=False)
            print("✓ Saved output.xlsx")
            sys.stdout.flush()
        else:
            print("No matches found!")

        # 6) Unmatched rows
        print(f"\nProcessing {len(unmatched_rows)} unmatched rows...")
        sys.stdout.flush()
        
        if unmatched_rows:
            df_unmatched = df_input.loc[unmatched_rows].copy()
        else:
            df_unmatched = df_input.iloc[0:0].copy()

        # Ensure Usecase column
        usecase_col = find_column_case_insensitive(df_unmatched, ["usecase"]) if len(df_unmatched) > 0 else None
        if usecase_col is None:
            df_unmatched["Usecase"] = "Others"
            print("  Created 'Usecase' column")
        else:
            df_unmatched[usecase_col] = "Others"

        df_unmatched["matched_subgroup"] = ""
        
        print(f"Saving {len(df_unmatched)} unmatched rows to unmatched.xlsx...")
        sys.stdout.flush()
        df_unmatched.to_excel("unmatched.xlsx", index=False)
        print("✓ Saved unmatched.xlsx")
        sys.stdout.flush()

        # Summary
        print("\nSummary:")
        print(f"  Total rows: {total_input_rows}")
        print(f"  Matched: {len(matches)}")
        print(f"  Unmatched: {len(unmatched_rows)}")
        print(f"  Distinct subgroups: {len(set(m['keyword_norm'] for m in matches))}")

        if matches:
            print("\nFirst 5 matches:")
            for m in matches[:5]:
                print(f"  {m['input_index']}, {m['matched_subgroup_original']}, Score: {m['match_score']:.2f}")

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
