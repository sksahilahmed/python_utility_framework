import pandas as pd

df = pd.read_excel('output.xlsx', sheet_name='Sheet1')
unique_months = df['Closed Month'].nunique()

print("=== DEBUGGING AUTOMATION ARRAY ===\n")

# Filter 1: L1.5
l15_df = df[df['L1/L2'] == 'L1.5']
print(f"Step 1 - L1.5 only: {len(l15_df)} rows")

# Filter 2: Automation = Feasible
auto_l15 = l15_df[l15_df['Automation'] == 'Feasible']
print(f"Step 2 - L1.5 + Automation=Feasible: {len(auto_l15)} rows")

# Filter 3: Std/Agentic = "Standard" or "Standard/Agentic AI"
std_agentic_auto = auto_l15[
    (auto_l15['Std/Agentic'] == 'Standard') | 
    (auto_l15['Std/Agentic'] == 'Standard/Agentic AI')
]
print(f"Step 3 - L1.5 + Automation=Feasible + (Standard OR Standard/Agentic AI): {len(std_agentic_auto)} rows")

# Get usecases
usecases = std_agentic_auto['Usecase'].nunique()
print(f"\nUsecases: {usecases}")

# Ticket volume calculation
ticket_volume = len(std_agentic_auto) / unique_months
fte = ticket_volume / 140

print(f"\nTicket volume calculation:")
print(f"  {len(std_agentic_auto)} rows ÷ {unique_months} months = {ticket_volume:.4f}")
print(f"  FTE: {ticket_volume:.4f} ÷ 140 = {fte:.4f}")

print(f"\nCorrect automation_array should be:")
print(f"[{usecases}, {len(std_agentic_auto)}, {len(std_agentic_auto)}, {round(fte, 4)}]")
