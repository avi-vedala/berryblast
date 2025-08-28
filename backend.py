# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
import pandas as pd
import requests
from datetime import datetime
from google import genai
from google.genai import types
from typing import Dict, Any
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default API key - Replace this with your actual Google Gemini API key
DEFAULT_API_KEY = "AIzaSyCfqqqu8YXmngWwzXkJLSzYcIBoWzYjBps"

class JobExtractor:
    def __init__(self, api_key: str = None):
        """
        Initialize the JobExtractor with Google Gemini API
        
        Args:
            api_key (str): Google Gemini API key. If None, will try default key, then environment variables
        """
        # Priority: passed parameter > default key > environment variables
        if api_key:
            self.api_key = api_key
        elif DEFAULT_API_KEY and DEFAULT_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
            self.api_key = DEFAULT_API_KEY
        else:
            self.api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        
        if not self.api_key:
            raise ValueError("Google API key not provided. Please set DEFAULT_API_KEY in backend.py, set GEMINI_API_KEY environment variable, or pass api_key parameter")
        
        # Configure new Gemini client
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-flash"
        
        # Excel file path
        self.excel_file = "Summer2026_Applications.xlsx"
        
        # Load the prompt template
        self.load_prompt_template()
    
    def load_prompt_template(self):
        """Load the prompt template from prompt.txt"""
        try:
            with open('prompt.txt', 'r', encoding='utf-8') as file:
                self.prompt_template = file.read().strip()
        except FileNotFoundError:
            self.prompt_template = """Use the provided link to extract the following information from the job listing:
1. Company
2. Job Title
3. Location
4. Job Functions

Do not paraphrase any information or data. Be as accurate as possible. Match the appropriate information with the respective columns in the Excel file.
Add along today's date, and the same url as pasted.
Also make the first column arbitrarily "Waiting"."""
    
    def fetch_webpage_content(self, url: str) -> str:
        """
        Fetch content from a webpage URL
        
        Args:
            url (str): The URL to fetch content from
            
        Returns:
            str: The webpage content
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching webpage: {e}")
            raise
    
    def extract_job_info(self, url: str, custom_prompt: str = None) -> Dict[str, Any]:
        """
        Extract job information from URL using Gemini AI
        
        Args:
            url (str): The job listing URL
            custom_prompt (str): Optional custom prompt to override template
            
        Returns:
            Dict[str, Any]: Extracted job information
        """
        try:
            # Fetch webpage content
            logger.info(f"Fetching content from: {url}")
            webpage_content = self.fetch_webpage_content(url)
            
            # Prepare prompt
            prompt = custom_prompt or self.prompt_template
            full_prompt = f"""
{prompt}

URL: {url}

Webpage Content:
{webpage_content[:10000]}  # Limit content to avoid token limits

Please extract the information in the following JSON format:
{{
    "status": "Applied",
    "company_name": "Company",
    "position_title": "Job Title", 
    "location": "Location",
    "job_functions": "Job Functions",
    "date_applied": "{datetime.now().strftime('%Y-%m-%d')}"
}}

Only return the JSON, no additional text.
"""
            
            # Get response from Gemini using new API
            logger.info("Sending request to Gemini API...")
            
            # Create content using new API structure
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=full_prompt),
                    ],
                ),
            ]
            
            # Configure generation with tools (including Google Search for better results)
            tools = [
                types.Tool(googleSearch=types.GoogleSearch()),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                tools=tools,
            )
            
            # Generate content using the new API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=generate_content_config,
            )
            
            # Parse JSON response
            try:
                # Clean the response text (remove markdown formatting if present)
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                job_info = json.loads(response_text)
                logger.info("Successfully extracted job information")
                return job_info
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response text: {response.text}")
                
                # Fallback: create manual extraction
                return self.fallback_extraction(url, response.text)
                
        except Exception as e:
            logger.error(f"Error extracting job info: {e}")
            raise
    
    def fallback_extraction(self, url: str, response_text: str) -> Dict[str, Any]:
        """
        Fallback method to extract information if JSON parsing fails
        
        Args:
            url (str): The job URL
            response_text (str): The raw response from Gemini
            
        Returns:
            Dict[str, Any]: Extracted information with fallback values
        """
        return {
            "status": "Applied",
            "company_name": "Could not extract",
            "position_title": "Could not extract",
            "location": "Could not extract", 
            "job_functions": "Could not extract",
            "date_applied": datetime.now().strftime('%Y-%m-%d')
        }
    
    def is_file_locked(self, filepath: str) -> bool:
        """
        Check if file is locked (e.g., open in Excel)
        
        Args:
            filepath (str): Path to the file to check
            
        Returns:
            bool: True if file is locked, False otherwise
        """
        try:
            # Try to open the file in write mode
            with open(filepath, 'a'):
                return False
        except (PermissionError, IOError):
            return True
    
    def wait_for_file_unlock(self, filepath: str, max_wait: int = 30) -> bool:
        """
        Wait for file to be unlocked
        
        Args:
            filepath (str): Path to the file
            max_wait (int): Maximum seconds to wait
            
        Returns:
            bool: True if file became available, False if timeout
        """
        import time
        
        wait_time = 0
        while wait_time < max_wait:
            if not self.is_file_locked(filepath):
                return True
            
            logger.info(f"File is locked, waiting... ({wait_time}s/{max_wait}s)")
            time.sleep(2)
            wait_time += 2
        
        return False
    
    def load_or_create_excel(self) -> pd.DataFrame:
        """
        Load existing Excel file or create new one with proper columns
        
        Returns:
            pd.DataFrame: The Excel data
        """
        # Check if file is locked
        if os.path.exists(self.excel_file) and self.is_file_locked(self.excel_file):
            logger.warning(f"Excel file '{self.excel_file}' is currently open/locked")
            logger.info("Please close the Excel file and try again, or wait for auto-unlock...")
            
            if not self.wait_for_file_unlock(self.excel_file):
                raise PermissionError(f"Excel file '{self.excel_file}' is locked. Please close it in Excel and try again.")
        
        if os.path.exists(self.excel_file):
            try:
                df = pd.read_excel(self.excel_file)
                logger.info(f"Loaded existing Excel file with {len(df)} rows")
                
                # Check if URL column exists, add if missing (migration)
                if 'URL' not in df.columns:
                    logger.info("Adding URL column to existing Excel file")
                    df['URL'] = ""  # Add empty URL column
                    # Save the updated structure
                    df.to_excel(self.excel_file, index=False)
                    logger.info("Excel file updated with URL column")
                
                return df
            except PermissionError as e:
                raise PermissionError(f"Cannot access Excel file. Please close '{self.excel_file}' in Excel and try again.")
            except Exception as e:
                logger.warning(f"Error reading Excel file, creating new one: {e}")
        
        # Create new DataFrame with expected columns
        columns = ["Status", "Company", "Job Title", "Location", "Job Functions", "Date Applied", "URL"]
        df = pd.DataFrame(columns=columns)
        logger.info("Created new Excel file structure")
        return df
    
    def append_to_excel(self, job_info: Dict[str, Any]) -> bool:
        """
        Append job information to Excel file
        
        Args:
            job_info (Dict[str, Any]): Job information to append
            
        Returns:
            bool: Success status
        """
        try:
            # Check if file is locked before proceeding
            if os.path.exists(self.excel_file) and self.is_file_locked(self.excel_file):
                logger.warning(f"Excel file '{self.excel_file}' is currently open/locked")
                
                if not self.wait_for_file_unlock(self.excel_file):
                    raise PermissionError(f"Cannot write to Excel file. Please close '{self.excel_file}' in Excel and try again.")
            
            # Load existing data
            df = self.load_or_create_excel()
            
            # Create new row
            new_row = {
                "Status": job_info.get("status", "Applied"),
                "Company": job_info.get("company_name", ""),
                "Job Title": job_info.get("position_title", ""),
                "Location": job_info.get("location", ""),
                "Job Functions": job_info.get("job_functions", ""),
                "Date Applied": job_info.get("date_applied", datetime.now().strftime('%Y-%m-%d')),
                "URL": job_info.get("url", "")
            }
            
            # Check if URL already exists (check against internal URL tracking, not Excel column)
            if not df.empty and 'Company' in df.columns and 'Job Title' in df.columns:
                # Check for duplicate based on company and position to avoid re-adding same job
                duplicate_check = df[
                    (df['Company'] == job_info.get("company_name", "")) & 
                    (df['Job Title'] == job_info.get("position_title", ""))
                ]
                if not duplicate_check.empty:
                    logger.warning(f"Similar job already exists: {job_info.get('company_name')} - {job_info.get('position_title')}")
                    return False
            
            # Append new row
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save to Excel with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    df.to_excel(self.excel_file, index=False)
                    logger.info(f"Successfully added job to Excel file. Total rows: {len(df)}")
                    return True
                except PermissionError:
                    if attempt < max_retries - 1:
                        logger.warning(f"Permission denied on attempt {attempt + 1}, retrying...")
                        if not self.wait_for_file_unlock(self.excel_file, max_wait=10):
                            continue
                    else:
                        raise PermissionError(f"Cannot save to Excel file after {max_retries} attempts. Please close '{self.excel_file}' in Excel.")
            
            return True
            
        except PermissionError:
            raise  # Re-raise permission errors
        except Exception as e:
            logger.error(f"Error appending to Excel: {e}")
            raise
    
    def process_job_url(self, url: str, custom_prompt: str = None) -> Dict[str, Any]:
        """
        Complete pipeline: extract job info and append to Excel
        
        Args:
            url (str): Job listing URL
            custom_prompt (str): Optional custom prompt
            
        Returns:
            Dict[str, Any]: Processing results
        """
        try:
            # Extract job information
            job_info = self.extract_job_info(url, custom_prompt)
            
            # Add the URL to the job_info (ensure it's not empty)
            job_info["url"] = url if url else ""
            
            # Append to Excel
            success = self.append_to_excel(job_info)
            
            return {
                "success": success,
                "job_info": job_info,
                "message": "Job information extracted and added to spreadsheet" if success else "URL already exists in spreadsheet"
            }
            
        except Exception as e:
            logger.error(f"Error processing job URL: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process job URL"
            }

    def update_row_status(self, row_number: int, new_status: str) -> Dict[str, Any]:
        """
        Update the status of a specific row in the Excel file
        
        Args:
            row_number (int): 1-based row number to update
            new_status (str): New status value ("Applied", "Rejected", "Interviewed", "Accepted")
            
        Returns:
            Dict[str, Any]: Update results
        """
        try:
            # Check if file is locked
            if self.is_file_locked(self.excel_file):
                if not self.wait_for_file_unlock(self.excel_file):
                    return {"success": False, "message": "Excel file is locked. Please close it and try again."}
            
            # Load current data
            df = self.load_or_create_excel()
            
            if df.empty:
                return {"success": False, "message": "No data found in Excel file."}
            
            if row_number < 1 or row_number > len(df):
                return {"success": False, "message": f"Row number {row_number} is out of range. Valid range: 1-{len(df)}"}
            
            # Update the status (row_number - 1 because pandas uses 0-based indexing)
            df.iloc[row_number - 1, df.columns.get_loc('Status')] = new_status
            
            # Save back to Excel
            df.to_excel(self.excel_file, index=False)
            logger.info(f"Updated row {row_number} status to {new_status}")
            
            return {
                "success": True, 
                "message": f"Row {row_number} status updated to '{new_status}'"
            }
            
        except Exception as e:
            logger.error(f"Error updating row status: {e}")
            return {
                "success": False,
                "message": f"Failed to update row status: {str(e)}"
            }
    
    def delete_row(self, row_number: int) -> Dict[str, Any]:
        """
        Delete a specific row from the Excel file
        
        Args:
            row_number (int): 1-based row number to delete
            
        Returns:
            Dict[str, Any]: Delete results
        """
        try:
            # Check if file is locked
            if self.is_file_locked(self.excel_file):
                if not self.wait_for_file_unlock(self.excel_file):
                    return {"success": False, "message": "Excel file is locked. Please close it and try again."}
            
            # Load current data
            df = self.load_or_create_excel()
            
            if df.empty:
                return {"success": False, "message": "No data found in Excel file."}
            
            if row_number < 1 or row_number > len(df):
                return {"success": False, "message": f"Row number {row_number} is out of range. Valid range: 1-{len(df)}"}
            
            # Get row info for confirmation message
            row_info = df.iloc[row_number - 1]
            company = row_info.get('Company', row_info.get('Company Name', 'Unknown'))
            job_title = row_info.get('Job Title', row_info.get('Position Title', 'Unknown'))
            
            # Delete the row (row_number - 1 because pandas uses 0-based indexing)
            df = df.drop(df.index[row_number - 1]).reset_index(drop=True)
            
            # Save back to Excel
            df.to_excel(self.excel_file, index=False)
            logger.info(f"Deleted row {row_number}: {company} - {job_title}")
            
            return {
                "success": True, 
                "message": f"Deleted row {row_number}: {company} - {job_title}"
            }
            
        except Exception as e:
            logger.error(f"Error deleting row: {e}")
            return {
                "success": False,
                "message": f"Failed to delete row: {str(e)}"
            }


# Example usage and testing functions
def test_webpage_fetch(url: str):
    """Test webpage fetching functionality"""
    print(f"\n🌐 Testing webpage fetch for: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.text[:500]  # First 500 characters
        print(f"✅ Successfully fetched content (first 500 chars):")
        print(f"Status Code: {response.status_code}")
        print(f"Content Preview: {content}...")
        return True
    except Exception as e:
        print(f"❌ Error fetching webpage: {e}")
        return False

def test_excel_permissions():
    """Test Excel file permissions and locking"""
    print(f"\n📊 Testing Excel permissions...")
    
    try:
        # Use a temporary API key for testing (will fail API calls but test file operations)
        test_extractor = JobExtractor(api_key="test-key-for-file-operations-only")
        excel_file = test_extractor.excel_file
        
        print(f"Excel file: {excel_file}")
        
        # Check if file exists
        if not os.path.exists(excel_file):
            print(f"⚠️ Excel file doesn't exist, will create new one")
        else:
            print(f"✅ Excel file exists")
        
        # Test file locking
        is_locked = test_extractor.is_file_locked(excel_file)
        if is_locked:
            print(f"🔒 File is LOCKED (probably open in Excel)")
            print(f"❌ Cannot write to file - please close Excel first")
            return False
        else:
            print(f"🔓 File is UNLOCKED (ready for writing)")
        
        # Test loading
        df = test_extractor.load_or_create_excel()
        print(f"✅ Successfully loaded/created Excel file")
        print(f"   Columns: {df.columns.tolist()}")
        print(f"   Current rows: {len(df)}")
        
        # Test writing (add a test row)
        test_job = {
            "status": "Test",
            "company_name": "Permission Test Company",
            "position_title": "Test Position",
            "location": "Test Location",
            "job_functions": "Testing permissions",
            "date_applied": datetime.now().strftime('%Y-%m-%d')
        }
        
        print(f"📝 Testing write permissions...")
        success = test_extractor.append_to_excel(test_job)
        
        if success:
            print(f"✅ Successfully wrote test data to Excel")
            print(f"💡 Permissions are working correctly!")
        else:
            print(f"⚠️ Write test completed but row might be duplicate")
            
        return True
        
    except PermissionError as e:
        print(f"🔒 PERMISSION DENIED: {e}")
        print(f"")
        print(f"🚨 SOLUTIONS:")
        print(f"1. Close the Excel file if it's open")
        print(f"2. Check if file is read-only (right-click → Properties)")
        print(f"3. Run terminal as administrator")
        print(f"4. Move Excel file to a different location")
        return False
        
    except Exception as e:
        print(f"❌ Error testing Excel permissions: {e}")
        return False

def test_excel_operations():
    """Test Excel file operations"""
    print(f"\n📊 Testing Excel operations...")
    
    try:
        extractor = JobExtractor()
        df = extractor.load_or_create_excel()
        print(f"✅ Excel file loaded/created successfully")
        print(f"Columns: {df.columns.tolist()}")
        print(f"Current rows: {len(df)}")
        
        # Test adding a sample row
        sample_job = {
            "status": "Applied",
            "company_name": "Test Company",
            "position_title": "Test Position",
            "location": "Test Location",
            "job_functions": "Test Functions",
            "date_applied": datetime.now().strftime('%Y-%m-%d')
        }
        
        print(f"📝 Testing row addition...")
        success = extractor.append_to_excel(sample_job)
        if success:
            print(f"✅ Successfully added test row to Excel")
        else:
            print(f"⚠️ Row not added (likely duplicate URL)")
            
        return True
    except Exception as e:
        print(f"❌ Error with Excel operations: {e}")
        return False

def debug_gemini_connection(api_key: str = None):
    """Test Gemini API connection"""
    print(f"\n🤖 Testing Gemini API connection...")
    
    try:
        # Use same priority as JobExtractor
        if api_key:
            test_key = api_key
        elif DEFAULT_API_KEY and DEFAULT_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
            test_key = DEFAULT_API_KEY
        else:
            test_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            
        if not test_key:
            print(f"❌ No API key provided")
            print(f"Options to set API key:")
            print(f"1. Set DEFAULT_API_KEY in backend.py")
            print(f"2. Set environment variable: $env:GEMINI_API_KEY = 'your_key_here'")
            print(f"3. Set environment variable: $env:GOOGLE_API_KEY = 'your_key_here'")
            return False
        
        # Use new API structure
        client = genai.Client(api_key=test_key)
        
        # Test simple query
        test_prompt = "Hello! Please respond with 'API connection successful'"
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=test_prompt),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig()
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=generate_content_config,
        )
        
        print(f"✅ Gemini API connected successfully")
        print(f"Test Response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Gemini API: {e}")
        print(f"💡 Make sure you have the latest google-genai package installed:")
        print(f"   pip install --upgrade google-genai")
        return False

def main():
    """Main function with debugging options"""
    import sys
    
    print("=" * 60)
    print("🚀 JOB EXTRACTOR BACKEND - DEBUG MODE")
    print("=" * 60)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test-web" and len(sys.argv) > 2:
            url = sys.argv[2]
            test_webpage_fetch(url)
            return
            
        elif command == "test-permissions":
            test_excel_permissions()
            return
            
        elif command == "test-excel":
            test_excel_operations()
            return
            
        elif command == "test-api":
            api_key = sys.argv[2] if len(sys.argv) > 2 else None
            debug_gemini_connection(api_key)
            return
            
        elif command == "process" and len(sys.argv) > 2:
            url = sys.argv[2]
            api_key = sys.argv[3] if len(sys.argv) > 3 else None
            
            try:
                if api_key:
                    extractor = JobExtractor(api_key=api_key)
                else:
                    extractor = JobExtractor()
                
                print(f"\n🔄 Processing job URL: {url}")
                result = extractor.process_job_url(url)
                
                print(f"\n📋 RESULT:")
                print(f"Success: {result.get('success', False)}")
                print(f"Message: {result.get('message', 'No message')}")
                
                if 'job_info' in result:
                    print(f"\n📝 EXTRACTED JOB INFO:")
                    for key, value in result['job_info'].items():
                        print(f"  {key}: {value}")
                
                if 'error' in result:
                    print(f"\n❌ ERROR: {result['error']}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
            return
    
    # Interactive mode
    print("\n🔧 AVAILABLE COMMANDS:")
    print("1. Test webpage fetching: python backend.py test-web <url>")
    print("2. Test Excel permissions: python backend.py test-permissions")
    print("3. Test Excel operations: python backend.py test-excel")
    print("4. Test Gemini API: python backend.py test-api [api_key]")
    print("5. Process job URL: python backend.py process <url> [api_key]")
    print("6. Run all tests: python backend.py test-all")
    print("\n" + "="*60)
    
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1].lower() == "test-all"):
        print("\n🧪 RUNNING ALL TESTS...")
        
        # Test 1: Excel operations
        excel_ok = test_excel_operations()
        
        # Test 2: API connection
        api_ok = debug_gemini_connection()
        
        # Test 3: Webpage fetch (using a reliable test URL)
        web_ok = test_webpage_fetch("https://httpbin.org/html")
        
        print(f"\n📊 TEST SUMMARY:")
        print(f"Excel Operations: {'✅' if excel_ok else '❌'}")
        print(f"Gemini API: {'✅' if api_ok else '❌'}")  
        print(f"Web Fetching: {'✅' if web_ok else '❌'}")
        
        if all([excel_ok, api_ok, web_ok]):
            print(f"\n🎉 All tests passed! System is ready.")
        else:
            print(f"\n⚠️ Some tests failed. Check the issues above.")
    
    print(f"\n💡 TIPS:")
    print(f"• Set your API key: $env:GOOGLE_API_KEY = 'your_key_here'")
    print(f"• Test with a real job URL: python backend.py process 'https://example.com/job'")
    print(f"• Check Excel file: {os.path.abspath('Summer2026_Applications.xlsx')}")


if __name__ == "__main__":
    main()
