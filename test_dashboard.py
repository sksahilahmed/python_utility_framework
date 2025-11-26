import json

# Load and display the summary output
with open('summary_output.json', 'r') as f:
    data = json.load(f)

print("\n=== OPTIMIZATION SUMMARY FOR DASHBOARD ===\n")
print("Elimination:")
print(f"  Usecases: {data['elimination_array'][0]}")
print(f"  Ticket Volume: {data['elimination_array'][1]}")
print(f"  FTE: {data['elimination_array'][2]}")

print("\nAutomation:")
print(f"  Usecases: {data['automation_array'][0]}")
print(f"  Ticket Volume: {data['automation_array'][1]}")
print(f"  FTE: {data['automation_array'][2]}")

print("\nAutomation-Agentic AI:")
print(f"  Usecases: {data['automation_agent_array'][0]}")
print(f"  Ticket Volume: {data['automation_agent_array'][1]}")
print(f"  FTE: {data['automation_agent_array'][2]}")

print("\nLeft Shift:")
print(f"  Usecases: {data['left_shift_array'][0]}")
print(f"  Ticket Volume: {data['left_shift_array'][1]}")
print(f"  FTE: {data['left_shift_array'][2]}")

print("\n=== TABLE FOR DASHBOARD ===\n")
print("Lever | # of Usecases | Ticket Volume | FTE")
print("-" * 50)
print(f"Elimination | {data['elimination_array'][0]} | {data['elimination_array'][1]} | {data['elimination_array'][2]}")
print(f"Automation | {data['automation_array'][0]} | {data['automation_array'][1]} | {data['automation_array'][2]}")
print(f"Automation-Agentic AI | {data['automation_agent_array'][0]} | {data['automation_agent_array'][1]} | {data['automation_agent_array'][2]}")
print(f"Left Shift | {data['left_shift_array'][0]} | {data['left_shift_array'][1]} | {data['left_shift_array'][2]}")
