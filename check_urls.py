import pandas as pd
import os

print("=== Checking URL Column Implementation ===")

# Check if Excel file exists
if os.path.exists('Summer2026_Applications.xlsx'):
    print("✅ Excel file exists")
    
    # Read the Excel file
    df = pd.read_excel('Summer2026_Applications.xlsx')
    
    print(f"📊 Data shape: {df.shape}")
    print(f"📋 Columns: {list(df.columns)}")
    
    # Check if URL column exists
    if 'URL' in df.columns:
        print("✅ URL column is present!")
        
        # Check if URLs are being captured
        urls = df['URL'].tolist()
        print(f"📎 URLs found: {len([url for url in urls if url and str(url) != 'nan'])}")
        
        # Show sample data
        print("\n📄 Sample data:")
        for i, row in df.iterrows():
            print(f"Row {i+1}:")
            print(f"  Company: {row.get('Company', 'N/A')}")
            print(f"  Job Title: {row.get('Job Title', 'N/A')}")
            print(f"  URL: {row.get('URL', 'N/A')}")
            print()
    else:
        print("❌ URL column is missing!")
        print("Available columns:", list(df.columns))
else:
    print("❌ Excel file not found")

print("=== URL Check Complete ===")
