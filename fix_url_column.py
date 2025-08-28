import pandas as pd
import os

print("=== Fixing URL Column in Excel File ===")

excel_file = "Summer2026_Applications.xlsx"

if os.path.exists(excel_file):
    # Read existing data
    df = pd.read_excel(excel_file)
    print(f"Current columns: {list(df.columns)}")
    print(f"Current data shape: {df.shape}")
    
    # Check if URL column exists
    if 'URL' not in df.columns:
        print("Adding URL column...")
        df['URL'] = ""  # Add empty URL column
        
        # Save back to Excel
        df.to_excel(excel_file, index=False)
        print("✅ URL column added successfully!")
    else:
        print("URL column already exists")
        
        # Check for NaN values
        nan_count = df['URL'].isna().sum()
        print(f"NaN values in URL column: {nan_count}")
        
        if nan_count > 0:
            print("Replacing NaN values with empty strings...")
            df['URL'] = df['URL'].fillna("")
            df.to_excel(excel_file, index=False)
            print("✅ NaN values replaced!")
    
    # Show final structure
    df = pd.read_excel(excel_file)
    print(f"\nFinal columns: {list(df.columns)}")
    print(f"Final data shape: {df.shape}")
    print("\nSample data:")
    for i in range(min(3, len(df))):
        print(f"Row {i+1}: URL = '{df.iloc[i]['URL']}'")

else:
    print("Excel file not found!")

print("=== Fix Complete ===")
