"""
Module for handling CAPTCHA detection and processing in the YouTube email scraper.

This module provides utilities for detecting and handling CAPTCHAs that may
appear during the scraping process.
"""

import logging
import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from colorama import Fore

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

def handle_captcha(driver: webdriver.Chrome, url: str) -> Optional[str]:
    """
    Handle CAPTCHA detection during scraping.
    
    Args:
        driver: Chrome WebDriver instance
        url: URL where CAPTCHA was detected
        
    Returns:
        "CAPTCHA" status message or None if handling was successful
    """
    logging.warning(f"CAPTCHA detected at URL: {url}")
    print(f"{Fore.YELLOW}⚠ CAPTCHA detected at URL: {url}")
    
    # You could implement manual solving prompts here
    # For now, we'll just return the CAPTCHA status
    return "CAPTCHA"

def wait_for_captcha_solution(driver: webdriver.Chrome, timeout: int = 120) -> bool:
    """
    Wait for the user to manually solve a CAPTCHA. (Optional implementation)
    This function could be used if you want to implement a manual solving workflow.
    
    Args:
        driver: Chrome WebDriver instance
        timeout: Maximum time to wait for CAPTCHA solution in seconds
        
    Returns:
        True if CAPTCHA appears to be solved, False if timeout occurred
    """
    print(f"{Fore.YELLOW}⚠ Please solve the CAPTCHA manually in the browser window")
    print(f"{Fore.YELLOW}⚠ You have {timeout} seconds to solve it")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not is_captcha_present(driver):
            print(f"{Fore.GREEN}✓ CAPTCHA appears to be solved")
            return True
        time.sleep(2)
    
    print(f"{Fore.RED}✗ CAPTCHA solving timeout")
    return False