import pandas as pd
import os
from datetime import datetime

print("🔍 TESTING PYTHON EXCEL CAPABILITIES")
print("=" * 50)

# Test 1: Check if libraries are available
try:
    import openpyxl
    print("✅ openpyxl library: AVAILABLE")
    print(f"   Version: {openpyxl.__version__}")
except ImportError:
    print("❌ openpyxl library: NOT AVAILABLE")

try:
    import pandas as pd
    print("✅ pandas library: AVAILABLE") 
    print(f"   Version: {pd.__version__}")
except ImportError:
    print("❌ pandas library: NOT AVAILABLE")

print("\n📊 EXCEL FILE OPERATIONS TEST")
print("-" * 30)

# Test 2: Create a new Excel file
test_file = "test_excel_operations.xlsx"

# Create sample data
data = {
    'Status': ['Waiting', 'Applied', 'Interview'],
    'Company': ['Google', 'Microsoft', 'Apple'], 
    'Position': ['Software Engineer', 'Data Scientist', 'Product Manager'],
    'Location': ['Mountain View', 'Seattle', 'Cupertino'],
    'Date Added': [datetime.now().strftime('%Y-%m-%d')] * 3
}

df = pd.DataFrame(data)

# Test writing to Excel
try:
    df.to_excel(test_file, index=False)
    print(f"✅ CREATE: Successfully created '{test_file}'")
    print(f"   Rows: {len(df)}, Columns: {len(df.columns)}")
except Exception as e:
    print(f"❌ CREATE failed: {e}")

# Test reading from Excel
try:
    df_read = pd.read_excel(test_file)
    print(f"✅ READ: Successfully read '{test_file}'")
    print(f"   Rows: {len(df_read)}, Columns: {len(df_read.columns)}")
    print(f"   Columns: {df_read.columns.tolist()}")
except Exception as e:
    print(f"❌ READ failed: {e}")

# Test appending to Excel
try:
    # Add new row
    new_row = {
        'Status': 'Waiting',
        'Company': 'Amazon', 
        'Position': 'DevOps Engineer',
        'Location': 'Austin',
        'Date Added': datetime.now().strftime('%Y-%m-%d')
    }
    
    # Read existing data
    df_existing = pd.read_excel(test_file)
    
    # Append new row
    df_updated = pd.concat([df_existing, pd.DataFrame([new_row])], ignore_index=True)
    
    # Write back to Excel
    df_updated.to_excel(test_file, index=False)
    
    print(f"✅ APPEND: Successfully added new row")
    print(f"   New total rows: {len(df_updated)}")
    
except Exception as e:
    print(f"❌ APPEND failed: {e}")

# Test editing existing data
try:
    df_edit = pd.read_excel(test_file)
    
    # Change status of first row
    df_edit.loc[0, 'Status'] = 'Accepted'
    
    # Save changes
    df_edit.to_excel(test_file, index=False)
    
    print(f"✅ EDIT: Successfully modified existing data")
    print(f"   Changed first row status to 'Accepted'")
    
except Exception as e:
    print(f"❌ EDIT failed: {e}")

# Test viewing final result
try:
    final_df = pd.read_excel(test_file)
    print(f"\n📋 FINAL EXCEL CONTENT:")
    print(final_df.to_string(index=False))
    
except Exception as e:
    print(f"❌ VIEW failed: {e}")

# Test with your actual files
print(f"\n🔍 CHECKING YOUR ACTUAL FILES")
print("-" * 30)

files_to_check = [
    "Summer2026_Applications.xlsx",
    "Internships Applied.xlsx"
]

for filename in files_to_check:
    if os.path.exists(filename):
        try:
            df = pd.read_excel(filename)
            print(f"✅ {filename}: Found and readable")
            print(f"   Shape: {df.shape} (rows, columns)")
            print(f"   Columns: {df.columns.tolist()}")
        except Exception as e:
            print(f"❌ {filename}: Found but error reading - {e}")
    else:
        print(f"⚠️ {filename}: File not found")

# Cleanup test file
try:
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"\n🧹 Cleaned up test file: {test_file}")
except:
    pass

print(f"\n💡 SUMMARY:")
print("Python can fully work with Excel files using pandas + openpyxl")
print("Supported operations: CREATE, READ, WRITE, APPEND, EDIT, DELETE")
print("File formats: .xlsx, .xls (older format)")
