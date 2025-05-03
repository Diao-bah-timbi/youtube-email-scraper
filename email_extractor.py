"""
Module for email extraction functionality in the YouTube email scraper.

This module provides functions to extract email addresses from YouTube channel "About" pages.
"""

import re
import logging
import time
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)
from colorama import Fore

from captcha_handler import is_captcha_present

def random_delay(min_seconds: float = 3.0, max_seconds: float = 6.0) -> None:
    """
    Wait for a random amount of time between actions to avoid detection.
    
    Args:
        min_seconds: Minimum wait time in seconds
        max_seconds: Maximum wait time in seconds
    """
    import random
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def validate_email(email: str) -> bool:
    """
    Validate if a string looks like an email address.
    
    Args:
        email: String to validate as an email
        
    Returns:
        True if the string appears to be a valid email address
    """
    # Basic email validation regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def extract_email_from_element(element) -> Optional[str]:
    """
    Extract email address from an element's text or href attribute.
    
    Args:
        element: WebElement that might contain an email
        
    Returns:
        Extracted email address or None
    """
    # Try to get text content
    text = element.text
    
    # If no text, try href attribute (for mailto links)
    if not text:
        href = element.get_attribute("href")
        if href and "mailto:" in href:
            # Extract email from mailto link
            email = href.split("mailto:")[1].split("?")[0].strip()
            if validate_email(email):
                return email
    else:
        # Look for email pattern in text
        match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        if match:
            email = match.group(0)
            if validate_email(email):
                return email
    
    return None

def find_email_elements(driver: webdriver.Chrome) -> List:
    """
    Find elements that might contain email addresses.
    
    Args:
        driver: Chrome WebDriver instance
        
    Returns:
        List of WebElements that might contain email addresses
    """
    # Try various selectors that might contain emails
    selectors = [
        "//a[contains(@href, 'mailto:')]",
        "//span[contains(text(), '@')]",
        "//div[contains(text(), '@')]",
        "//p[contains(text(), '@')]"
    ]
    
    elements = []
    for selector in selectors:
        elements.extend(driver.find_elements(By.XPATH, selector))
    
    return elements

def extract_email(driver: webdriver.Chrome, url: str, wait_time: int = 10) -> Optional[str]:
    """
    Extract email address from a YouTube channel About page.
    
    Args:
        driver: Chrome WebDriver instance
        url: URL of the YouTube channel About page
        wait_time: Maximum wait time in seconds for elements to load
        
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
            WebDriverWait(driver, wait_time).until(
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
            
            # Try to find the email address
            email_elements = find_email_elements(driver)
            
            for element in email_elements:
                email = extract_email_from_element(element)
                if email:
                    logging.info(f"Email found: {email}")
                    print(f"{Fore.GREEN}✓ Email found: {email}")
                    return email
            
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

def validate_youtube_url(url: str) -> bool:
    """
    Validate if a URL is a YouTube channel URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if the URL appears to be a valid YouTube channel URL
    """
    if not url or not isinstance(url, str):
        return False
    
    # Pattern for YouTube channel URLs
    patterns = [
        r'^https?://(?:www\.)?youtube\.com/channel/[A-Za-z0-9_-]+(?:/about)?$',
        r'^https?://(?:www\.)?youtube\.com/c/[A-Za-z0-9_-]+(?:/about)?$',
        r'^https?://(?:www\.)?youtube\.com/user/[A-Za-z0-9_-]+(?:/about)?$',
        r'^https?://(?:www\.)?youtube\.com/@[A-Za-z0-9_-]+(?:/about)?$'
    ]
    
    # Check if URL matches any of the patterns
    for pattern in patterns:
        if re.match(pattern, url):
            # If URL doesn't end with /about, add it
            if not url.endswith('/about'):
                return url + '/about'
            return url
    
    return False