import pandas as pd

df = pd.read_excel('output.xlsx', sheet_name='Sheet1')
print('All columns:')
for col in df.columns:
    print(f'  {col}: {df[col].dtype}')
print('\nNumeric columns:')
numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
print(numeric_cols if numeric_cols else 'None found')
