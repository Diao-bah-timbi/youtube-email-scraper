#!/usr/bin/env python3
"""
YouTube Channel Email Scraper

This script automates the extraction of email addresses from YouTube channel "About" pages.
It reads URLs from a Google Sheet, processes them using Selenium, and writes the results back.

Requirements:
    - Python 3.8+
    - Google Sheets API credentials (credentials.json)
    - ChromeDriver installed and in PATH

Usage:
    1. Install required packages:
       pip install selenium gspread google-auth webdriver-manager colorama

    2. Place your Google API credentials file (credentials.json) in the same directory
       (Instructions to create: https://docs.gspread.org/en/latest/oauth2.html)

    3. Update the SPREADSHEET_NAME constant with your Google Sheet name

    4. Run the script:
       python youtube_email_scraper.py
"""

import os
import time
import random
import logging
from typing import Optional, Tuple, List
import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init(autoreset=True)

# Constants
SPREADSHEET_NAME = "YouTube Channel Emails"  # Update with your sheet name
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
CREDS_FILE = "credentials.json"
BATCH_SIZE = 500
LOG_FILE = "email_scraper.log"
WAIT_TIME = 10  # Maximum wait time in seconds for elements to load

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def setup_logging() -> None:
    """Configure console and file logging."""
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def random_delay(min_seconds: float = 3.0, max_seconds: float = 6.0) -> None:
    """
    Wait for a random amount of time between actions to avoid detection.
    
    Args:
        min_seconds: Minimum wait time in seconds
        max_seconds: Maximum wait time in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def connect_to_sheet() -> Tuple[gspread.Client, gspread.Spreadsheet]:
    """
    Connect to Google Sheets using credentials.
    
    Returns:
        Tuple containing the authorized client and the spreadsheet
    
    Raises:
        FileNotFoundError: If credentials file is not found
        Exception: For other authentication or connection issues
    """
    try:
        if not os.path.exists(CREDS_FILE):
            raise FileNotFoundError(f"Credentials file '{CREDS_FILE}' not found")
        
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet = client.open(SPREADSHEET_NAME)
        logging.info(f"Successfully connected to spreadsheet: {SPREADSHEET_NAME}")
        print(f"{Fore.GREEN}✓ Connected to Google Sheet: {SPREADSHEET_NAME}")
        return client, sheet
    except FileNotFoundError as e:
        logging.error(f"Credentials file not found: {str(e)}")
        print(f"{Fore.RED}✗ Error: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Failed to connect to Google Sheets: {str(e)}")
        print(f"{Fore.RED}✗ Error connecting to Google Sheets: {str(e)}")
        raise

def setup_chrome_driver() -> webdriver.Chrome:
    """
    Configure and initialize ChromeDriver with settings to avoid detection.
    
    Returns:
        Configured Chrome WebDriver instance
    """
    chrome_options = Options()
    
    # Add options to make the browser less detectable
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Set a realistic window size
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Set a realistic user agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]
    chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # Disable automation flags
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Use webdriver-manager to handle ChromeDriver installation
    service = Service(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Execute CDP commands to prevent detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
    })
    
    return driver

def is_captcha_present(driver: webdriver.Chrome) -> bool:
    """
    Check if a CAPTCHA is present on the page.
    
    Args:
        driver: Chrome WebDriver instance
        
    Returns:
        True if CAPTCHA is detected, False otherwise
    """
    captcha_indicators = [
        "//iframe[contains(@src, 'recaptcha')]",
        "//div[contains(@class, 'recaptcha')]",
        "//*[contains(text(), 'captcha')]",
        "//*[contains(text(), 'CAPTCHA')]",
        "//div[@id='captcha']"
    ]
    
    for indicator in captcha_indicators:
        try:
            if driver.find_elements(By.XPATH, indicator):
                logging.warning("CAPTCHA detected on the page")
                print(f"{Fore.YELLOW}⚠ CAPTCHA detected!")
                return True
        except WebDriverException:
            pass
    
    return False

def extract_email(driver: webdriver.Chrome, url: str) -> Optional[str]:
    """
    Extract email address from a YouTube channel About page.
    
    Args:
        driver: Chrome WebDriver instance
        url: URL of the YouTube channel About page
        
    Returns:
        Extracted email address or status message
    """
    try:
        logging.info(f"Processing URL: {url}")
        print(f"{Fore.BLUE}➜ Processing: {url}")
        
        driver.get(url)
        random_delay(2, 4)
        
        # Check if we need to scroll to view the business inquiries section
        try:
            # Wait for the page to load
            WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check for CAPTCHA
            if is_captcha_present(driver):
                return "CAPTCHA"
            
            # Scroll down to make sure the email button is visible
            driver.execute_script("window.scrollBy(0, 500);")
            random_delay(1, 2)
            
            # Look for the "View email address" button in the "For business inquiries" section
            email_button_xpaths = [
                "//span[contains(text(), 'View email address')]/..",
                "//button[contains(text(), 'View email address')]",
                "//div[contains(text(), 'For business inquiries')]//following::span[contains(text(), 'View email address')]/.."
            ]
            
            email_button = None
            for xpath in email_button_xpaths:
                try:
                    email_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if not email_button:
                logging.warning(f"Email button not found for URL: {url}")
                print(f"{Fore.YELLOW}⚠ Email button not found")
                return "NOT FOUND"
            
            # Click the button to reveal the email
            email_button.click()
            random_delay(1, 2)
            
            # Check for CAPTCHA again after clicking
            if is_captcha_present(driver):
                return "CAPTCHA"
            
            # Try to find the email address with different approaches
            email_xpaths = [
                "//a[contains(@href, 'mailto:')]",
                "//span[contains(text(), '@')]",
                "//div[contains(text(), '@')]"
            ]
            
            for xpath in email_xpaths:
                try:
                    elements = driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        text = element.text or element.get_attribute("href")
                        if text:
                            # Look for mailto: links
                            if "mailto:" in text:
                                email = text.split("mailto:")[1].split("?")[0].strip()
                                logging.info(f"Email found: {email}")
                                print(f"{Fore.GREEN}✓ Email found: {email}")
                                return email
                            
                            # Look for text containing @
                            if "@" in text and "." in text.split("@")[1]:
                                # Simple validation to ensure it looks like an email
                                email = text.strip()
                                logging.info(f"Email found: {email}")
                                print(f"{Fore.GREEN}✓ Email found: {email}")
                                return email
                except Exception as e:
                    logging.error(f"Error finding email element: {str(e)}")
            
            return "NOT FOUND"
            
        except TimeoutException:
            logging.error(f"Page load timeout for URL: {url}")
            print(f"{Fore.RED}✗ Page load timeout")
            return "ERROR"
            
    except WebDriverException as e:
        logging.error(f"WebDriver error for URL {url}: {str(e)}")
        print(f"{Fore.RED}✗ Browser error: {str(e)}")
        return "ERROR"
    except Exception as e:
        logging.error(f"Unexpected error for URL {url}: {str(e)}")
        print(f"{Fore.RED}✗ Error: {str(e)}")
        return "ERROR"

def process_youtube_urls(sheet: gspread.Spreadsheet, driver: webdriver.Chrome, batch_size: int = BATCH_SIZE) -> None:
    """
    Process YouTube URLs from Google Sheet and extract email addresses.
    
    Args:
        sheet: Google Spreadsheet to read from and write to
        driver: Chrome WebDriver instance
        batch_size: Number of URLs to process in one run
    """
    try:
        # Select the first worksheet
        worksheet = sheet.get_worksheet(0)
        if not worksheet:
            logging.error("No worksheet found in the spreadsheet.")
            print(f"{Fore.RED}✗ No worksheet found in the spreadsheet.")
            return
        
        # Get all values from the first two columns
        data = worksheet.get_all_values()
        if not data or len(data) <= 1:  # Check if data exists and is more than just headers
            logging.error("No data found in the spreadsheet or only headers present.")
            print(f"{Fore.RED}✗ No data found in the spreadsheet.")
            return
        
        # Assuming first row is headers
        headers = data[0]
        rows = data[1:]
        
        # Check if we have at least 2 columns
        if len(headers) < 2:
            logging.error("Spreadsheet must have at least 2 columns.")
            print(f"{Fore.RED}✗ Spreadsheet must have at least 2 columns.")
            return
        
        print(f"{Fore.CYAN}ℹ Found {len(rows)} URLs to process")
        logging.info(f"Found {len(rows)} URLs to process")
        
        # Track URLs to process (skip those that already have data in column B)
        urls_to_process = [(i+2, row[0]) for i, row in enumerate(rows) if len(row) < 2 or not row[1]]
        
        if not urls_to_process:
            print(f"{Fore.GREEN}✓ All URLs have already been processed!")
            logging.info("All URLs have already been processed.")
            return
        
        print(f"{Fore.CYAN}ℹ {len(urls_to_process)} URLs need processing")
        logging.info(f"{len(urls_to_process)} URLs need processing")
        
        # Process URLs in batches
        total_to_process = len(urls_to_process)
        processed_count = 0
        
        for batch_start in range(0, total_to_process, batch_size):
            batch_end = min(batch_start + batch_size, total_to_process)
            batch = urls_to_process[batch_start:batch_end]
            
            print(f"{Fore.CYAN}ℹ Processing batch {batch_start//batch_size + 1} ({batch_end - batch_start} URLs)")
            logging.info(f"Processing batch {batch_start//batch_size + 1} ({batch_end - batch_start} URLs)")
            
            for row_idx, url in batch:
                try:
                    # Skip empty URLs
                    if not url or not url.strip():
                        worksheet.update_cell(row_idx, 2, "EMPTY URL")
                        logging.warning(f"Empty URL in row {row_idx}")
                        print(f"{Fore.YELLOW}⚠ Row {row_idx}: Empty URL")
                        processed_count += 1
                        continue
                    
                    # Validate URL format
                    if not url.startswith("https://www.youtube.com/"):
                        worksheet.update_cell(row_idx, 2, "INVALID URL")
                        logging.warning(f"Invalid URL format in row {row_idx}: {url}")
                        print(f"{Fore.YELLOW}⚠ Row {row_idx}: Invalid URL format")
                        processed_count += 1
                        continue
                    
                    # Extract email
                    result = extract_email(driver, url)
                    
                    # Update Google Sheet
                    worksheet.update_cell(row_idx, 2, result or "NOT FOUND")
                    
                    # Print progress
                    processed_count += 1
                    progress = (processed_count / total_to_process) * 100
                    print(f"{Fore.CYAN}ℹ Progress: {progress:.1f}% ({processed_count}/{total_to_process})")
                    
                    # Add a random delay between requests
                    random_delay()
                    
                except Exception as e:
                    logging.error(f"Error processing row {row_idx}: {str(e)}")
                    print(f"{Fore.RED}✗ Error processing row {row_idx}: {str(e)}")
                    try:
                        worksheet.update_cell(row_idx, 2, "ERROR")
                    except:
                        logging.error(f"Failed to update error status for row {row_idx}")
                    processed_count += 1
                    
            print(f"{Fore.GREEN}✓ Batch {batch_start//batch_size + 1} completed!")
            logging.info(f"Batch {batch_start//batch_size + 1} completed!")
            
        print(f"{Fore.GREEN}✓ All {total_to_process} URLs have been processed!")
        logging.info(f"All {total_to_process} URLs have been processed!")
        
    except Exception as e:
        logging.error(f"Error processing URLs: {str(e)}")
        print(f"{Fore.RED}✗ Error processing URLs: {str(e)}")

def main() -> None:
    """Main function to run the YouTube email scraper."""
    setup_logging()
    logging.info("Starting YouTube email scraper")
    print(f"{Fore.CYAN}YouTube Channel Email Scraper{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*40}{Style.RESET_ALL}")
    
    client = None
    sheet = None
    driver = None
    
    try:
        # Connect to Google Sheets
        client, sheet = connect_to_sheet()
        
        # Setup Chrome WebDriver
        print(f"{Fore.BLUE}➜ Setting up Chrome WebDriver...")
        driver = setup_chrome_driver()
        print(f"{Fore.GREEN}✓ Chrome WebDriver initialized")
        
        # Process URLs
        process_youtube_urls(sheet, driver, BATCH_SIZE)
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        print(f"{Fore.RED}✗ An error occurred: {str(e)}")
    finally:
        # Clean up resources
        if driver:
            driver.quit()
            logging.info("WebDriver closed")
            print(f"{Fore.BLUE}➜ Chrome WebDriver closed")
        
        logging.info("YouTube email scraper finished")
        print(f"{Fore.CYAN}{'='*40}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}YouTube email scraper finished{Style.RESET_ALL}")

if __name__ == "__main__":
    main()