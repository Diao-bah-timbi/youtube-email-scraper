"""
Module for browser-related utilities for the YouTube email scraper.

This module provides functions for setting up and controlling the browser
for web scraping operations.
"""

import random
import logging
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from colorama import Fore

def get_random_user_agent() -> str:
    """
    Get a random user agent string to avoid detection.
    
    Returns:
        Random user agent string
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.84",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(user_agents)

def get_random_screen_resolution() -> str:
    """
    Get a random screen resolution to appear more human-like.
    
    Returns:
        Random screen resolution in the format 'widthxheight'
    """
    resolutions = [
        "1920,1080",
        "1366,768",
        "1440,900",
        "1536,864",
        "1280,720",
        "1600,900"
    ]
    return random.choice(resolutions)

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
    window_size = get_random_screen_resolution()
    chrome_options.add_argument(f"--window-size={window_size}")
    
    # Set a realistic user agent
    user_agent = get_random_user_agent()
    chrome_options.add_argument(f"--user-agent={user_agent}")
    
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
    
    logging.info("Chrome WebDriver initialized with anti-detection measures")
    print(f"{Fore.GREEN}✓ Chrome WebDriver initialized with anti-detection measures")
    
    return driver

def get_scroll_positions(page_height: int) -> List[int]:
    """
    Get a list of scroll positions to navigate a page naturally.
    
    Args:
        page_height: Total height of the page in pixels
        
    Returns:
        List of scroll positions
    """
    # Create a more human-like scrolling pattern
    # First scroll quickly through the first part then slow down
    positions = []
    
    # Fast scrolling for the first 70% of the page
    step = page_height // 5
    for pos in range(0, int(page_height * 0.7), step):
        positions.append(pos)
    
    # Slower, more precise scrolling for the last 30%
    step = page_height // 10
    for pos in range(int(page_height * 0.7), page_height, step):
        positions.append(pos)
    
    return positions