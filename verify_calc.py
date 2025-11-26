import pandas as pd

df = pd.read_excel('output.xlsx', sheet_name='Sheet1')

# Verify calculations
print("=== VERIFICATION ===")
print(f"Total rows: {len(df)}")
print(f"L1.5 count: {(df['L1/L2'] == 'L1.5').sum()}")
print(f"L2 count: {(df['L1/L2'] == 'L2').sum()}")

# Unique months
unique_months = df['Closed Month'].nunique()
print(f"\nUnique months: {unique_months}")

# Elimination feasible
elim_feasible = df[df['Elimination'] == 'Feasible']
print(f"\nElimination Feasible rows: {len(elim_feasible)}")
print(f"Elimination usecases: {elim_feasible['Usecase'].nunique()}")
print(f"Elimination avg tickets: {len(elim_feasible) / unique_months:.4f}")

# Automation feasible
auto_feasible = df[df['Automation'] == 'Feasible']
print(f"\nAutomation Feasible rows: {len(auto_feasible)}")
print(f"Automation usecases: {auto_feasible['Usecase'].nunique()}")
print(f"Automation L1.5 count: {(auto_feasible['L1/L2'] == 'L1.5').sum()}")
std_agentic_count = ((auto_feasible['Std/Agentic'] == 'Standard') | (auto_feasible['Std/Agentic'] == 'Agentic AI')).sum()
print(f"Automation Std/Agentic count: {std_agentic_count}")
print(f"Automation avg tickets: {len(auto_feasible) / unique_months:.4f}")

# Left shift
left_feasible = df[(df['Left Shift'] == 'Feasible') & (df['L1/L2'] == 'L1.5')]
print(f"\nLeft Shift Feasible & L1.5 rows: {len(left_feasible)}")
print(f"Left Shift usecases: {left_feasible['Usecase'].nunique()}")
print(f"Left Shift avg tickets: {len(left_feasible) / unique_months:.4f}")
