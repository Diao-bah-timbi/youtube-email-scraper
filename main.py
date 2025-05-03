#!/usr/bin/env python3
"""
YouTube Channel Email Scraper - Main Module

This is the main entry point for the YouTube email scraper program.
It coordinates the overall scraping process, connecting the modules for
sheets access, browser control, and email extraction.

Usage:
    python main.py
"""

import os
import time
import logging
import argparse
from typing import Optional
from colorama import Fore, Style, init

# Import utility modules
from browser_utils import setup_chrome_driver
from sheets_utils import connect_to_sheet, get_pending_urls, update_result, create_spreadsheet_if_not_exists
from email_extractor import extract_email, validate_youtube_url
from captcha_handler import is_captcha_present

# Initialize colorama for colored terminal output
init(autoreset=True)

# Default constants
DEFAULT_SPREADSHEET_NAME = "1sYDM1KNT1MmJXL1eHdcLeDuDu7Wncfcl2p3WNS6Bw60"

DEFAULT_BATCH_SIZE = 500
DEFAULT_WAIT_TIME = 10
LOG_FILE = "email_scraper.log"

def setup_logging() -> None:
    """Configure console and file logging."""
    # Configure logging to file
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def process_youtube_urls(spreadsheet_name: str, batch_size: int = DEFAULT_BATCH_SIZE, 
                         wait_time: int = DEFAULT_WAIT_TIME, resume: bool = True) -> None:
    """
    Process YouTube URLs from Google Sheet and extract email addresses.
    
    Args:
        spreadsheet_name: Name of the Google Spreadsheet
        batch_size: Number of URLs to process in one run
        wait_time: Maximum wait time in seconds for elements to load
        resume: Whether to skip URLs that already have data in column B
    """
    client = None
    sheet = None
    driver = None
    
    try:
        # Connect to Google Sheets
        client, sheet = connect_to_sheet(spreadsheet_name)
        
        # Select the first worksheet
        worksheet = sheet.get_worksheet(0)
        if not worksheet:
            logging.error("No worksheet found in the spreadsheet.")
            print(f"{Fore.RED}✗ No worksheet found in the spreadsheet.")
            return
        
        # Get URLs to process
        if resume:
            print("✓ Google Sheet connecté avec succès")

            urls_to_process = get_pending_urls(worksheet)
        else:
            # Get all values (including those already processed)
            data = worksheet.get_all_values()
            if not data or len(data) <= 1:
                logging.error("No data found in the spreadsheet or only headers present.")
                print(f"{Fore.RED}✗ No data found in the spreadsheet.")
                return
            
            # Skip header row
            urls_to_process = [(i+2, row[0]) for i, row in enumerate(data[1:])]
        
        
        print(f"{Fore.CYAN}ℹ Found {len(urls_to_process)} URLs to process")
        logging.info(f"Found {len(urls_to_process)} URLs to process")
        
        # Setup Chrome WebDriver
        print(f"{Fore.BLUE}➜ Setting up Chrome WebDriver...")
        driver = setup_chrome_driver()
        
        # Process URLs in batches
        total_to_process = len(urls_to_process)
        processed_count = 0
        
        for batch_start in range(0, total_to_process, batch_size):
            batch_end = min(batch_start + batch_size, total_to_process)
            current_batch = urls_to_process[batch_start:batch_end]
            
            print(f"{Fore.CYAN}ℹ Processing batch {batch_start//batch_size + 1} ({batch_end - batch_start} URLs)")
            logging.info(f"Processing batch {batch_start//batch_size + 1} ({batch_end - batch_start} URLs)")
            
            for row_idx, url in current_batch:
                try:
                    # Skip empty URLs
                    if not url or not url.strip():
                        update_result(worksheet, row_idx, 2, "EMPTY URL")
                        logging.warning(f"Empty URL in row {row_idx}")
                        print(f"{Fore.YELLOW}⚠ Row {row_idx}: Empty URL")
                        processed_count += 1
                        continue
                    
                    # Validate URL format
                    valid_url = validate_youtube_url(url)
                    if not valid_url:
                        update_result(worksheet, row_idx, 2, "INVALID URL")
                        logging.warning(f"Invalid URL format in row {row_idx}: {url}")
                        print(f"{Fore.YELLOW}⚠ Row {row_idx}: Invalid URL format")
                        processed_count += 1
                        continue
                    
                    # Process URL (use valid_url in case it was modified to add /about)
                    result = extract_email(driver, valid_url, wait_time)
                    
                    # Update Google Sheet
                    update_result(worksheet, row_idx, 2, result or "NOT FOUND")
                    
                    # Print progress
                    processed_count += 1
                    progress = (processed_count / total_to_process) * 100
                    print(f"{Fore.CYAN}ℹ Progress: {progress:.1f}% ({processed_count}/{total_to_process})")
                    
                    # Add a delay between requests (adjusted for batch boundaries)
                    if processed_count < total_to_process:
                        time.sleep(random.uniform(3.0, 6.0))
                    
                except Exception as e:
                    logging.error(f"Error processing row {row_idx}: {str(e)}")
                    print(f"{Fore.RED}✗ Error processing row {row_idx}: {str(e)}")
                    try:
                        update_result(worksheet, row_idx, 2, "ERROR")
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
    finally:
        # Clean up resources
        if driver:
            driver.quit()
            logging.info("WebDriver closed")
            print(f"{Fore.BLUE}➜ Chrome WebDriver closed")

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="YouTube Channel Email Scraper")
    
    parser.add_argument(
        "--spreadsheet", "-s",
        type=str,
        default=DEFAULT_SPREADSHEET_NAME,
        help=f"Name of the Google Spreadsheet (default: {DEFAULT_SPREADSHEET_NAME})"
    )
    
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Number of URLs to process in one batch (default: {DEFAULT_BATCH_SIZE})"
    )
    
    parser.add_argument(
        "--wait-time", "-w",
        type=int,
        default=DEFAULT_WAIT_TIME,
        help=f"Maximum wait time in seconds for elements to load (default: {DEFAULT_WAIT_TIME})"
    )
    
    parser.add_argument(
        "--no-resume", "-n",
        action="store_true",
        help="Process all URLs, including those already processed (default: only process URLs without data in column B)"
    )
    
    parser.add_argument(
        "--create", "-c",
        action="store_true",
        help="Create spreadsheet if it doesn't exist"
    )
    
    return parser.parse_args()

def main() -> None:
    """Main function to run the YouTube email scraper."""
    # Set up logging
    setup_logging()
    logging.info("Starting YouTube email scraper")
    print(f"{Fore.CYAN}YouTube Channel Email Scraper{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*40}{Style.RESET_ALL}")
    
    # Parse command-line arguments
    args = parse_arguments()
    spreadsheet_name = args.spreadsheet
    batch_size = args.batch_size
    wait_time = args.wait_time
    resume = not args.no_resume
    
    try:
        # Check if we need to create the spreadsheet
        if args.create:
            client = gspread.authorize(Credentials.from_service_account_file(
                'credentials.json', scopes=SCOPES
            ))
            create_spreadsheet_if_not_exists(client, spreadsheet_name)
        
        # Process URLs
        process_youtube_urls(
            spreadsheet_name=spreadsheet_name,
            batch_size=batch_size,
            wait_time=wait_time,
            resume=resume
        )
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        print(f"{Fore.RED}✗ An error occurred: {str(e)}")
    finally:
        logging.info("YouTube email scraper finished")
        print(f"{Fore.CYAN}{'='*40}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}YouTube email scraper finished{Style.RESET_ALL}")

if __name__ == "__main__":
    import random
    from google.oauth2.service_account import Credentials
    import gspread
    
    # Constants for direct import
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    
    main()