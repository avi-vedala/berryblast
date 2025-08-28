import streamlit as st
import pandas as pd
import os
from backend import JobExtractor
from datetime import datetime

# Configure the page
st.set_page_config(
    page_title="Job Application Tracker",
    page_icon="💼",
    layout="wide"
)

# Initialize job extractor globally
@st.cache_resource
def get_job_extractor():
    """Get a cached JobExtractor instance"""
    return JobExtractor()

job_extractor = get_job_extractor()

# Title of the app
st.title("💼 Job Application Tracker")
st.markdown("*Extract job information from URLs and manage your applications*")

# Check API key availability automatically
def check_api_key():
    """Check if API key is available from various sources"""
    from backend import DEFAULT_API_KEY
    
    # Check if default API key is set
    if DEFAULT_API_KEY and DEFAULT_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
        return DEFAULT_API_KEY, "default"
    
    # Check environment variables
    env_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if env_key:
        return env_key, "environment"
    
    return None, None

# Get API key automatically
api_key, key_source = check_api_key()

# Sidebar for API configuration (simplified)
with st.sidebar:
    st.header("🔧 Configuration")
    
    # API Key status
    if api_key:
        if key_source == "default":
            st.success("✅ Using default API Key from backend.py")
        elif key_source == "environment":
            st.success("✅ Using API Key from environment variable")
        
        # Option to override with manual input
        with st.expander("🔧 Override API Key"):
            manual_key = st.text_input(
                "Custom API Key:",
                type="password",
                help="Override the default API key if needed"
            )
            if manual_key:
                api_key = manual_key
                st.info("Using custom API key")
    else:
        st.warning("⚠️ No API Key configured")
        st.error("**Setup Required:** Please configure your API key")
        
        # Manual API key input when no default is available
        manual_key = st.text_input(
            "Gemini API Key:",
            type="password",
            help="Enter your Google Gemini API key"
        )
        if manual_key:
            api_key = manual_key
            st.success("✅ API Key entered")
        else:
            st.info("💡 **Quick Setup:**")
            st.code("1. Edit backend.py\n2. Replace 'YOUR_GEMINI_API_KEY_HERE'\n3. Restart the app", language="text")
            st.info("Or get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)")

# Main content area with tabs
tab1, tab2, tab3 = st.tabs(["🚀 Extract Job Info", "📊 View Applications", "🔍 Row Details"])

with tab1:
    st.header("🌐 Job Information Extractor")
    
    # URL Input
    url = st.text_input("🔗 Enter Job Listing URL:", placeholder="https://company.com/careers/job-listing")
    
    # Custom prompt option
    use_custom_prompt = st.checkbox("Use custom prompt", help="Override the default extraction prompt")
    
    custom_prompt = None
    if use_custom_prompt:
        custom_prompt = st.text_area(
            "Custom Prompt:",
            height=150,
            placeholder="Enter your custom prompt for job extraction..."
        )
    else:
        # Show default prompt for reference
        with st.expander("View Default Prompt"):
            try:
                with open('prompt.txt', 'r', encoding='utf-8') as file:
                    default_prompt = file.read()
                st.code(default_prompt, language="text")
            except FileNotFoundError:
                st.warning("prompt.txt file not found")
    
    # Extract button
    col1, col2 = st.columns([1, 3])
    with col1:
        extract_button = st.button("🚀 Extract Job Info", type="primary", disabled=not api_key or not url)
    
    with col2:
        if not api_key:
            st.error("❌ API Key required - configure in sidebar")
        elif not url:
            st.warning("⚠️ Please enter a job URL")
        else:
            st.success("✅ Ready to extract")
    
    # Processing and results
    if extract_button and api_key and url:
        try:
            with st.spinner("🔄 Extracting job information..."):
                # Process the job URL using global extractor
                result = job_extractor.process_job_url(url, custom_prompt)
            
            # Display results
            if result.get('success'):
                st.success(f"✅ {result.get('message', 'Job information extracted successfully!')}")
                
                # Show extracted job info
                job_info = result.get('job_info', {})
                if job_info:
                    st.subheader("📋 Extracted Information:")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**🏢 Company:** {job_info.get('company_name', 'N/A')}")
                        st.write(f"**💼 Position:** {job_info.get('position_title', 'N/A')}")
                        st.write(f"**📍 Location:** {job_info.get('location', 'N/A')}")
                    
                    with col2:
                        st.write(f"**⚡ Functions:** {job_info.get('job_functions', 'N/A')}")
                        st.write(f"**📅 Date Applied:** {job_info.get('date_applied', 'N/A')}")
                        st.write(f"**📊 Status:** {job_info.get('status', 'Applied')}")
                
            else:
                st.error(f"❌ {result.get('message', 'Failed to extract job information')}")
                if 'error' in result:
                    st.error(f"Error details: {result['error']}")
                    
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Make sure your API key is valid and the URL is accessible")

with tab2:
    st.header("📊 Your Job Applications")
    
    # Load the Excel file directly from the repository
    excel_file = "Summer2026_Applications.xlsx"
    
    try:
        if os.path.exists(excel_file):
            # Always read fresh data from Excel file (no caching)
            df = pd.read_excel(excel_file)
            
            # Handle empty dataframe
            if df.empty:
                st.info("📄 No applications found. The Excel file exists but is empty.")
                st.info("Start by extracting job information in the first tab!")
            else:
                # Show total applications first
                st.info(f"📊 **Total Applications:** {len(df)}")
                
                # Display basic info about the file
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    applied_count = len(df[df.get('Status', '') == 'Applied']) if 'Status' in df.columns else 0
                    st.metric("✅ Applied", applied_count)
                with col2:
                    rejected_count = len(df[df.get('Status', '') == 'Rejected']) if 'Status' in df.columns else 0
                    st.metric("❌ Rejected", rejected_count)
                with col3:
                    interviewed_count = len(df[df.get('Status', '') == 'Interviewed']) if 'Status' in df.columns else 0
                    st.metric("🎤 Interviewed", interviewed_count)
                with col4:
                    accepted_count = len(df[df.get('Status', '') == 'Accepted']) if 'Status' in df.columns else 0
                    st.metric("🎉 Accepted", accepted_count)
                
                # Display column names
                st.write("**Columns:**", ", ".join(df.columns.tolist()))
                
                # Filter and search options
                st.subheader("🔍 Filter Applications")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Status filter
                    if 'Status' in df.columns:
                        status_options = ['All'] + df['Status'].dropna().unique().tolist()
                        selected_status = st.selectbox("Filter by Status:", status_options)
                    else:
                        selected_status = 'All'
                
                with col2:
                    # Company search
                    company_search = st.text_input("🔍 Search Company:", placeholder="Enter company name...")
                
                # Apply filters
                filtered_df = df.copy()
                if selected_status != 'All':
                    filtered_df = filtered_df[filtered_df['Status'] == selected_status]
                
                if company_search:
                    company_col = 'Company' if 'Company' in df.columns else 'Company Name'
                    if company_col in df.columns:
                        filtered_df = filtered_df[
                            filtered_df[company_col].str.contains(company_search, case=False, na=False)
                        ]
                
                # Display filtered results
                st.subheader("📋 Applications")
                
                # Handle slider values for small datasets
                total_rows = len(filtered_df)
                if total_rows <= 5:
                    # For small datasets, just show all rows without slider
                    rows_to_show = total_rows
                    st.info(f"Showing all {total_rows} applications")
                else:
                    # For larger datasets, use slider
                    min_rows = min(5, total_rows)
                    max_rows = min(50, total_rows)
                    default_rows = min(20, total_rows)
                    
                    rows_to_show = st.slider(
                        "Rows to display", 
                        min_value=min_rows, 
                        max_value=max_rows, 
                        value=default_rows
                    )
                
                # Display the dataframe with custom height and 1-based row numbering
                display_df = filtered_df.head(rows_to_show).copy()
                display_df.index = range(1, len(display_df) + 1)  # Start row numbers from 1
                st.dataframe(display_df, use_container_width=True, height=400)
                
                # Summary statistics
                if len(filtered_df) != len(df):
                    st.info(f"Showing {len(filtered_df)} of {len(df)} applications")
        
        else:
            st.warning(f"📁 Excel file '{excel_file}' not found.")
            st.info("The file will be created automatically when you extract your first job.")

    except Exception as e:
        st.error(f"❌ Error reading Excel file: {str(e)}")
        st.info("Please check if the file is a valid Excel file and not corrupted.")

with tab3:
    st.header("🔍 Row Details")
    
    # Row number input
    # Check max rows if Excel file exists
    max_row = 1
    if os.path.exists(excel_file):
        try:
            temp_df = pd.read_excel(excel_file)
            max_row = len(temp_df) if not temp_df.empty else 1
        except:
            max_row = 1
    
    row_number = st.number_input("Enter row number:", min_value=1, max_value=max_row, value=1)
    
    try:
        if os.path.exists(excel_file):
            # Always load fresh data from Excel (no caching)
            df = pd.read_excel(excel_file)
            
            if not df.empty and row_number <= len(df):
                st.subheader(f"📋 Row {row_number} Details:")
                selected_row = df.iloc[row_number - 1]
                
                # Display row data in a nice format with icons
                for col, value in selected_row.items():
                    # Add appropriate icons based on column names
                    icon = "🏢" if "company" in col.lower() else \
                           "💼" if "position" in col.lower() or "title" in col.lower() else \
                           "📍" if "location" in col.lower() else \
                           "⚡" if "function" in col.lower() else \
                           "📅" if "date" in col.lower() else \
                           "🔗" if "url" in col.lower() else \
                           "📊" if "status" in col.lower() else \
                           "📝"
                    
                    st.write(f"**{icon} {col}:** {value}")
                
                # Action buttons for the row
                st.subheader("⚡ Actions")
                
                # Status update buttons
                st.write("**Update Status:**")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("✅ Applied", key=f"applied_{row_number}"):
                        result = job_extractor.update_row_status(row_number, "Applied")
                        if result["success"]:
                            st.success(result["message"])
                            st.rerun()
                        else:
                            st.error(result["message"])
                
                with col2:
                    if st.button("📞 Interviewed", key=f"interviewed_{row_number}"):
                        result = job_extractor.update_row_status(row_number, "Interviewed")
                        if result["success"]:
                            st.success(result["message"])
                            st.rerun()
                        else:
                            st.error(result["message"])
                
                with col3:
                    if st.button("🎉 Accepted", key=f"accepted_{row_number}"):
                        result = job_extractor.update_row_status(row_number, "Accepted")
                        if result["success"]:
                            st.success(result["message"])
                            st.rerun()
                        else:
                            st.error(result["message"])
                
                with col4:
                    if st.button("❌ Rejected", key=f"rejected_{row_number}"):
                        result = job_extractor.update_row_status(row_number, "Rejected")
                        if result["success"]:
                            st.success(result["message"])
                            st.rerun()
                        else:
                            st.error(result["message"])
                
                # Other actions
                st.write("**Other Actions:**")
                col5, col6 = st.columns(2)
                
                with col5:
                    if st.button("📋 Copy Details", key=f"copy_{row_number}"):
                        details = "\n".join([f"{col}: {value}" for col, value in selected_row.items()])
                        st.text_area("Row Details (copy this):", details, height=200, key=f"details_{row_number}")
                
                with col6:
                    # Delete button with confirmation
                    if st.button("🗑️ Delete Row", key=f"delete_{row_number}", type="secondary"):
                        # Use session state to handle confirmation
                        st.session_state[f"confirm_delete_{row_number}"] = True
                
                # Confirmation dialog for delete
                if st.session_state.get(f"confirm_delete_{row_number}", False):
                    st.warning("⚠️ Are you sure you want to delete this row? This action cannot be undone!")
                    col_confirm, col_cancel = st.columns(2)
                    
                    with col_confirm:
                        if st.button("✅ Yes, Delete", key=f"confirm_yes_{row_number}", type="primary"):
                            result = job_extractor.delete_row(row_number)
                            if result["success"]:
                                st.success(result["message"])
                                st.session_state[f"confirm_delete_{row_number}"] = False
                                st.rerun()
                            else:
                                st.error(result["message"])
                    
                    with col_cancel:
                        if st.button("❌ Cancel", key=f"confirm_no_{row_number}"):
                            st.session_state[f"confirm_delete_{row_number}"] = False
                            st.rerun()
                
                # Row info
                st.info(f"Row {row_number} of {len(df)}")
            
            elif not df.empty:
                st.warning(f"⚠️ Row number {row_number} exceeds the number of rows in the data ({len(df)} rows).")
            else:
                st.info("📄 No data available. Extract some job information first!")
        else:
            st.warning(f"📁 Excel file '{excel_file}' not found.")
            
    except Exception as e:
        st.error(f"❌ Error accessing row details: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        💼 Job Application Tracker | Built with Streamlit & Google Gemini AI
    </div>
    """, 
    unsafe_allow_html=True
)