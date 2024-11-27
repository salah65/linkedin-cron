from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from dotenv import load_dotenv
import os
import pandas as pd
from pandas.errors import EmptyDataError, ParserError
from datetime import datetime
from colorist import *


# Load environment variables from .env file
load_dotenv()

# LinkedIn credentials
username = os.getenv('EMAIL')
password = os.getenv('PASSWORD')

def initialize_webdriver():
    """Initialize the Selenium WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Run headless
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--mute-audio")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def login_to_linkedin(driver):
    """Login to LinkedIn using the provided credentials."""
    effect_blink("Logging into LinkedIn...",BgColor.GREEN)
    driver.get("https://www.linkedin.com/login")
    
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    
    # Wait for login to complete
    time.sleep(10)






def search_linkedin_connections(driver, base_search_url, connections_count=3):
    """Search for LinkedIn connections based on search URL and extract connection details."""
    new_entries_count = 0
    page_num = 101
    got_it_click_count = 0  # Counter for "Got it" button clicks


    effect_blink("Searching for new connections...",BgColor.GREEN)

    try:
        while new_entries_count < connections_count:
            search_url = base_search_url.format(page_num=page_num)
            driver.get(search_url)
            time.sleep(5)  # Wait for the page to load

             # Check if the "No results found" button exists
            try:
                no_results_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label^="No results found"]')
                if no_results_button:
                    yellow("No more results. Exiting the search.")
                    return
            except Exception:
                # No such button found; continue the process
                pass

            # Locate all <li> elements
            list_elements = driver.find_elements(By.CSS_SELECTOR, '[role^="list"] li')

            # Iterate over each <li> element
            for index, li in enumerate(list_elements, start=1):
                try:
                    # Locate the button within the current <li> element
                    button = li.find_element(By.CSS_SELECTOR, 'button[aria-label^="Invite"]')
                    button.click()
                    send_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label^="Send"]'))
                    )
                    send_button.click()
                    #  Handle the "Got it" button if it appears
                    try:
                        got_it_button = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Got it']"))
                        )
                        got_it_button.click()
                        got_it_click_count += 1  # Increment the counter for "Got it" clicks
                        if got_it_click_count >= 2:
                            yellow("You have reached the connection limits. Exiting the script.")
                            return
                    except Exception as e:
                        got_it_click_count = 0  # Reset the counter if the button doesn't appear
                    time.sleep(2)
                    new_entries_count+=1
                    if new_entries_count >= connections_count:
                            break


                except Exception as e:
                    continue
            
            if new_entries_count < connections_count:
                page_num += 1

    except KeyboardInterrupt:
        yellow("Script interrupted by the user. Saving current progress...")

    except Exception as e:
        red(f"An error occurred: {e}. Saving current progress...")




def main():
    # File name for the CSV
    file_name = 'linkedin_connections.csv'
    
    # Initialize WebDriver
    driver = initialize_webdriver()
    
    try:
        # Login to LinkedIn
        login_to_linkedin(driver)
        
        
        # Define the search URL
        base_search_url = "https://www.linkedin.com/search/results/people/?geoUrn=%5B%22103644278%22%5D&industry=%5B%22104%22%2C%2296%22%2C%221594%22%5D&keywords=recruiter&network=%5B%22S%22%5D&origin=FACETED_SEARCH&sid=iED&page={page_num}"        # Ask for Desired new connection number
        while True:
            try:
                green("How many connections do you want to send? ")
                send_count = int(input().strip())
                break  # If input is valid, exit the loop
            except ValueError:
                red("Invalid input. Please enter a valid integer.")  # Ask again if input is not an integer

        # Search for LinkedIn connections
        search_linkedin_connections(driver, base_search_url, connections_count=send_count)

    finally:
        # Close the WebDriver
        driver.quit()


if __name__ == "__main__":
    main()