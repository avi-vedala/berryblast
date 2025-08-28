import pandas as pd
import os

# Check if file exists
filename = "Summer2026_Applications.xlsx"
if os.path.exists(filename):
    print(f"File found: {filename}")
    
    # Read the Excel file
    df = pd.read_excel(filename)
    
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nData types:")
    print(df.dtypes)
else:
    print(f"File not found: {filename}")
    print("Files in current directory:")
    print(os.listdir("."))
