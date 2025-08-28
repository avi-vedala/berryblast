import pandas as pd

# Test with your actual Excel file
print("Reading Summer2026_Applications.xlsx...")
df = pd.read_excel('Summer2026_Applications.xlsx')
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print("\nFirst few rows:")
print(df.head())
