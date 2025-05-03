"""
Module for Google Sheets interaction in the YouTube email scraper.

This module provides functions for connecting to Google Sheets,
reading data, and writing results.
"""

import os
import logging
from typing import Tuple, List, Dict, Optional
import gspread
from google.oauth2.service_account import Credentials
from colorama import Fore

# Constants
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
CREDS_FILE = "credentials.json"

def connect_to_sheet(spreadsheet_id):
    credentials = Credentials.from_service_account_file(
        'credentials.json',
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(credentials)

    try:
        sheet = client.open_by_key(spreadsheet_id)
        return client, sheet
    except Exception as e:
        raise Exception(f"Could not open spreadsheet '{spreadsheet_id}': {e}")

def get_pending_urls(worksheet: gspread.Worksheet) -> List[Tuple[int, str]]:
    """
    Get URLs that need to be processed (no data in column B).

    Args:
        worksheet: Google Sheet worksheet to read from

    Returns:
        List of (row_index, url) tuples for URLs needing processing
    """
    # Get all values from the first two columns
    data = worksheet.get_all_values()
    if not data or len(data) <= 1:
        return []

    rows = data[1:]  # skip header

    urls_to_process = []

    for i, row in enumerate(rows):
        row_index = i + 2  # Adjust for 1-based index and header
        if len(row) >= 1 and (len(row) < 2 or not row[1]):
            raw_url = row[0].strip()
            # Auto-complete if missing scheme
            if not raw_url.startswith("http"):
                raw_url = "https://" + raw_url
            urls_to_process.append((row_index, raw_url))

    return urls_to_process

def update_result(worksheet: gspread.Worksheet, row: int, column: int, value: str) -> None:
    """
    Update a cell in the Google Sheet with the result.
    
    Args:
        worksheet: Google Sheet worksheet to update
        row: Row number (1-based)
        column: Column number (1-based)
        value: Value to write to the cell
    """
    try:
        worksheet.update_cell(row, column, value)
        logging.info(f"Updated cell ({row}, {column}) with value: {value}")
    except Exception as e:
        logging.error(f"Failed to update cell ({row}, {column}): {str(e)}")
        print(f"{Fore.RED}✗ Error updating Google Sheet: {str(e)}")

def batch_update_results(worksheet: gspread.Worksheet, updates: List[Dict[str, str]]) -> None:
    """
    Update multiple cells in the Google Sheet in a single batch request.
    
    Args:
        worksheet: Google Sheet worksheet to update
        updates: List of dictionaries with 'row', 'col', and 'value' keys
    """
    try:
        # Prepare cell list for batch update
        cell_list = []
        for update in updates:
            cell = worksheet.cell(update['row'], update['col'])
            cell.value = update['value']
            cell_list.append(cell)
        
        # Update in batch
        worksheet.update_cells(cell_list)
        logging.info(f"Batch updated {len(updates)} cells")
        print(f"{Fore.GREEN}✓ Batch updated {len(updates)} cells")
    except Exception as e:
        logging.error(f"Failed to perform batch update: {str(e)}")
        print(f"{Fore.RED}✗ Error performing batch update: {str(e)}")

def create_spreadsheet_if_not_exists(client: gspread.Client, spreadsheet_name: str) -> Optional[gspread.Spreadsheet]:
    """
    Create a new spreadsheet if it doesn't exist.
    
    Args:
        client: Authorized gspread client
        spreadsheet_name: Name of the spreadsheet to create
        
    Returns:
        The created or existing spreadsheet, or None if creation failed
    """
    try:
        # Try to open the spreadsheet
        try:
            sheet = client.open(spreadsheet_name)
            logging.info(f"Found existing spreadsheet: {spreadsheet_name}")
            print(f"{Fore.BLUE}ℹ Found existing spreadsheet: {spreadsheet_name}")
            return sheet
        except gspread.SpreadsheetNotFound:
            # Create a new spreadsheet
            sheet = client.create(spreadsheet_name)
            logging.info(f"Created new spreadsheet: {spreadsheet_name}")
            print(f"{Fore.GREEN}✓ Created new spreadsheet: {spreadsheet_name}")
            
            # Set up the header row
            worksheet = sheet.get_worksheet(0)
            worksheet.update_cell(1, 1, "YouTube Channel URL")
            worksheet.update_cell(1, 2, "Email Address")
            
            # Format header row
            worksheet.format("A1:B1", {
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                "horizontalAlignment": "CENTER",
                "textFormat": {"bold": True}
            })
            
            return sheet
    except Exception as e:
        logging.error(f"Failed to create spreadsheet: {str(e)}")
        print(f"{Fore.RED}✗ Error creating spreadsheet: {str(e)}")
        return None