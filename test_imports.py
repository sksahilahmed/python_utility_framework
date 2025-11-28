import pandas as pd

print('Starting import test...')

# Import functions
try:
    from merge_by_subgroup_final import merge_file
    print('merge_file imported')
except Exception as e:
    print('merge_file import failed:', e)

try:
    from process_excel import process_dataframe
    print('process_dataframe imported')
except Exception as e:
    print('process_dataframe import failed:', e)

# Build a tiny sample DataFrame for process_dataframe
sample = pd.DataFrame([
    {
        'L1/L2': 'L1.5',
        'Elimination_Feasibility': 'Feasible',
        'UseCase': 'UC1',
        'Closed Month': '2025-10',
        'Automation_Feasibility': 'Feasible',
        'Automation_Approach': 'Standard',
        'Left_Shift_Feasibility': 'Feasible'
    },
    {
        'L1/L2': 'L1.5',
        'Elimination_Feasibility': 'Not Feasible',
        'UseCase': 'UC2',
        'Closed Month': '2025-10',
        'Automation_Feasibility': 'Feasible',
        'Automation_Approach': 'Agentic AI',
        'Left_Shift_Feasibility': 'Not Feasible'
    }
])

try:
    res = process_dataframe(sample)
    print('process_dataframe output:')
    print(res)
except Exception as e:
    print('process_dataframe failed:', e)

# Test calculate_other_recommended_tools
try:
    from other_recommended_tools import calculate_other_recommended_tools
    print('\ncalculate_other_recommended_tools imported')
    
    # Add Priority column to sample
    sample['Priority'] = ['P1', 'P2']
    
    results_df, raw_data = calculate_other_recommended_tools(sample)
    print('Other Recommended Tools output:')
    print(results_df)
    print('\nRaw calculation data:')
    import json
    print(json.dumps(raw_data, indent=2))
except Exception as e:
    print('calculate_other_recommended_tools failed:', e)

print('\nDone')
