import pandas as pd

df = pd.read_excel('output.xlsx', sheet_name='Sheet1')
unique_months = df['Closed Month'].nunique()

print("=== DEBUGGING AUTOMATION ARRAYS ===\n")

# Automation feasible rows
auto_feasible = df[df['Automation'] == 'Feasible']
print(f"Total Automation Feasible rows: {len(auto_feasible)}")
print(f"Unique months: {unique_months}")

# Check Std/Agentic values
print(f"\nStd/Agentic unique values: {auto_feasible['Std/Agentic'].unique()}")

# Count "Standard" only
standard_only = (auto_feasible['Std/Agentic'] == 'Standard').sum()
print(f"\nStandard only: {standard_only}")

# Count "Agentic AI" only
agentic_ai_only = (auto_feasible['Std/Agentic'] == 'Agentic AI').sum()
print(f"Agentic AI only: {agentic_ai_only}")

# Standard OR Agentic AI
standard_or_agentic = ((auto_feasible['Std/Agentic'] == 'Standard') | (auto_feasible['Std/Agentic'] == 'Agentic AI')).sum()
print(f"Standard OR Agentic AI: {standard_or_agentic}")

# L1.5 count in automation feasible
l1_5_count = (auto_feasible['L1/L2'] == 'L1.5').sum()
print(f"\nL1.5 count in Automation Feasible: {l1_5_count}")

# Usecases
print(f"Usecases in Automation Feasible: {auto_feasible['Usecase'].nunique()}")

# Correct ticket volume for automation array
print(f"\n=== AUTOMATION ARRAY CALCULATION ===")
print(f"Total tickets: {len(auto_feasible)}")
print(f"Divided by {unique_months} months: {len(auto_feasible) / unique_months:.4f}")
print(f"FTE: {(len(auto_feasible) / unique_months) / 140:.4f}")

# Should be: [no_of_usecase, only_L1.5_count, std_and_agentic_count, FTE]
# But wait - what's the 3rd value? Let me check the requirement again
print(f"\nAutomation Array should be:")
print(f"[{auto_feasible['Usecase'].nunique()}, {l1_5_count}, {standard_or_agentic}, {round((len(auto_feasible) / unique_months) / 140, 4)}]")

print(f"\n=== AUTOMATION AGENT ARRAY CALCULATION ===")
# Only count rows where Std/Agentic == "Agentic AI"
agentic_rows = auto_feasible[auto_feasible['Std/Agentic'] == 'Agentic AI']
print(f"Rows with Agentic AI only: {len(agentic_rows)}")
print(f"Usecases in Agentic AI rows: {agentic_rows['Usecase'].nunique()}")
l1_5_in_agentic = (agentic_rows['L1/L2'] == 'L1.5').sum()
print(f"L1.5 count in Agentic AI rows: {l1_5_in_agentic}")
print(f"Ticket volume: {len(agentic_rows) / unique_months:.4f}")
print(f"FTE: {(len(agentic_rows) / unique_months) / 140:.4f}")

print(f"\nAutomation Agent Array should be:")
print(f"[{agentic_rows['Usecase'].nunique()}, {l1_5_in_agentic}, {len(agentic_rows)}, {round((len(agentic_rows) / unique_months) / 140, 4)}]")
