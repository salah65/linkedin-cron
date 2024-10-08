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
    # Uncomment to run headless
    chrome_options.add_argument("--headless=new")
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

def get_profile_link(uri, label=None):
    if label is None: 
        label = uri
    parameters = ''

    # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST 
    escape_mask = '\033]8;{};{}\033\\{}\033]8;;\033\\'

    return escape_mask.format(parameters, uri, label)

def load_or_create_csv(file_name):
    """Load an existing CSV file or create a new one if not found or corrupted."""
    try:
        df_existing = pd.read_csv(file_name)
        return df_existing
    except (FileNotFoundError, EmptyDataError, ParserError) as e:
        effect_blink("Creating a new CSV file...",BgColor.GREEN)
        return pd.DataFrame(columns=['Name', 'URL', 'Title', 'Location', 'Timestamp'])

def search_linkedin_connections(driver, base_search_url, connections_count=3):
    """Search for LinkedIn connections based on search URL and extract connection details."""
    data = []
    new_entries_count = 0
    page_num = 1
    got_it_click_count = 0  # Counter for "Got it" button clicks


    effect_blink("Searching for new connections...",BgColor.GREEN)
    
    while new_entries_count < connections_count:
        search_url = base_search_url.format(page_num=page_num)
        driver.get(search_url)
        time.sleep(5)  # Wait for the page to load
        
        li_elements = driver.find_elements(By.CSS_SELECTOR, 'ul[class^="reusable-search__entity-result-list"] li')
        for li in li_elements:
            try:
                connect_button = li.find_element(By.CSS_SELECTOR, 'button[aria-label^="Invite"]')
                if connect_button:
                    name_link = li.find_element(By.CSS_SELECTOR, 'span.entity-result__title-text a')
                    name = name_link.text.strip()
                    url = name_link.get_attribute('href').strip()

                    # Split the name before the "View" text if needed
                    split_index = name.find('View')
                    name = name[:split_index].strip() if split_index != -1 else name

                    primary_subtitle = li.find_element(By.CSS_SELECTOR, 'div[class^="entity-result__primary-subtitle"]')
                    secondary_subtitle = li.find_element(By.CSS_SELECTOR, 'div[class^="entity-result__secondary-subtitle"]')

                    time.sleep(5)  # Pause between requests to avoid detection
                    connect_button.click()
                    time.sleep(2)
                    send_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Send without a note']"))
                    )
                    send_button.click()
                    
                    # Handle the "Got it" button if it appears
                    try:
                        got_it_button = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Got it']"))
                        )
                        got_it_button.click()
                        got_it_click_count += 1  # Increment the counter for "Got it" clicks
                        if got_it_click_count >= 2:
                            yellow("You have reached the connection limits. Exiting the script.")
                            return data  # Exit the function
                    except Exception:
                        got_it_click_count = 0  # Reset the counter if the button doesn't appear
                         # Create and append the entry
                        entry = {
                        'Name': name,
                        'URL': url,
                        'Title': primary_subtitle.text.strip(),
                        'Location': secondary_subtitle.text.strip(),
                        'Timestamp': datetime.now().strftime('%d/%m/%Y %I:%M %p')
                        }
                        data.append(entry)
                        new_entries_count += 1
                        entry=f"{name}, {primary_subtitle.text.strip()}, {secondary_subtitle.text.strip()}"
                        green(f"{new_entries_count}/{connections_count} added: {get_profile_link(url,entry)} ")

                    if new_entries_count >= connections_count:
                        break
            except Exception:
                continue

        # Move to the next page if needed
        if new_entries_count < connections_count:
            page_num += 1
            time.sleep(5)

    return data

def save_to_csv(file_name, df_existing, data):
    if not data:
        yellow(f"No new data to save in ./{file_name}")
        return
    """Append new connection data to the existing CSV file."""
    df_new = pd.DataFrame(data)
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined.to_csv(file_name, index=False)
    green(f"Data saved to ./{file_name}")

def main():
    # File name for the CSV
    file_name = 'linkedin_connections.csv'
    
    # Initialize WebDriver
    driver = initialize_webdriver()
    
    try:
        # Login to LinkedIn
        login_to_linkedin(driver)
        
        # Load or create the CSV file
        df_existing = load_or_create_csv(file_name)
        
        # Define the search URL
        base_search_url = "https://www.linkedin.com/search/results/people/?geoUrn=%5B%22100517351%22%2C%22102748797%22%2C%22102095887%22%2C%22103644278%22%5D&industry=%5B%22104%22%5D&keywords=recruiter&network=%5B%22S%22%2C%22O%22%5D&origin=FACETED_SEARCH&page={page_num}&sid=V2L"

        # Ask for Desired new connection number
        while True:
            try:
                green("How many connections do you want to send? ")
                send_count = int(input().strip())
                break  # If input is valid, exit the loop
            except ValueError:
                red("Invalid input. Please enter a valid integer.")  # Ask again if input is not an integer

       
        # Search for LinkedIn connections
        data = search_linkedin_connections(driver, base_search_url, connections_count=send_count)
        
        # Save the extracted data to the CSV
        save_to_csv(file_name, df_existing, data)
        
    finally:
        # Close the WebDriver
        driver.quit()

if __name__ == "__main__":    
    main()
