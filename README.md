<<<<<<< HEAD
# YouTube Channel Email Scraper

A Python script to automate the extraction of email addresses from YouTube channel "About" pages.

## Features

- Reads YouTube channel "About" page URLs from a Google Sheet
- Automatically navigates to each URL using Selenium
- Extracts email addresses from the "For Business Inquiries" section
- Writes results back to the Google Sheet
- Handles errors, CAPTCHA detection, and implements anti-detection measures
- Processes URLs in configurable batches
- Provides detailed logging and progress tracking

## Requirements

- Python 3.8+
- Google Sheets API credentials
- Chrome browser installed

## Installation

1. Install the required Python packages:

```bash
pip install selenium gspread google-auth webdriver-manager colorama
```

2. Set up Google Sheets API credentials:
   - Follow the instructions at https://docs.gspread.org/en/latest/oauth2.html to create a service account
   - Download the credentials JSON file and save it as `credentials.json` in the same directory as the script

3. Create a Google Sheet with the following structure:
   - Column A: YouTube channel "About" page URLs (one per row)
   - Column B: Will contain the extracted email addresses

## Configuration

Edit the `youtube_email_scraper.py` file to update the following settings:

- `SPREADSHEET_NAME`: Name of your Google Sheet
- `BATCH_SIZE`: Number of URLs to process in one run (default: 500)
- `WAIT_TIME`: Maximum wait time in seconds for elements to load (default: 10)

## Usage

Run the script:

```bash
python youtube_email_scraper.py
```

## How It Works

1. The script connects to your Google Sheet using the provided credentials
2. It reads URLs from column A, skipping any rows that already have data in column B
3. For each URL, it:
   - Opens the URL in a Selenium-controlled Chrome browser
   - Waits for the page to load and scrolls to the "For Business Inquiries" section
   - Clicks the "View Email Address" button
   - Extracts the revealed email address
   - Writes the email (or appropriate status message) to column B
4. Status messages in column B include:
   - Email address (if found)
   - "NOT FOUND" (if no email is found)
   - "CAPTCHA" (if a CAPTCHA is detected)
   - "ERROR" (if the page fails to load or another error occurs)
   - "INVALID URL" (if the URL format is incorrect)
   - "EMPTY URL" (if the URL cell is empty)

## Handling CAPTCHAs

If a CAPTCHA is detected, the script will mark the row with "CAPTCHA" and move on to the next URL. You can later filter your sheet for "CAPTCHA" entries and process them manually or with a different approach.

## Anti-Detection Measures

The script implements several measures to avoid detection:
- Random delays between actions
- Realistic browser window sizes
- Randomized user-agent strings
- WebDriver stealth techniques

## Logging

The script logs all operations to:
- Console (with color-coded status indicators)
- Log file (`email_scraper.log`)

## Notes

- Processing a large number of URLs may trigger YouTube's anti-bot measures
- The script performance depends on your internet connection speed
- For best results, run the script during periods of low activity

>>>>>>> f4f35b4cb95c575b5ca8c72969b1364d562465dc
