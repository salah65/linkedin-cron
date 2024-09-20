from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from dotenv import load_dotenv
import os
import pandas as pd
from openpyxl import load_workbook
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# LinkedIn credentials
username = os.getenv('EMAIL')
password = os.getenv('PASSWORD')

# Set up Chrome options to run headless (without opening a browser window)
chrome_options = Options()
# Uncomment if you want to run in headless mode
# chrome_options.add_argument("--headless")  
# chrome_options.add_argument("--disable-gpu")  
# chrome_options.add_argument("--no-sandbox")  
# chrome_options.add_argument("--disable-dev-shm-usage")  

# Set up the WebDriver with headless Chrome
driver = webdriver.Chrome(options=chrome_options)

# Open LinkedIn login page
driver.get("https://www.linkedin.com/login")

# Wait for the page to load and enter credentials
wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
driver.find_element(By.ID, "password").send_keys(password)

# Click login
driver.find_element(By.XPATH, "//button[@type='submit']").click()

# Wait for login to complete
time.sleep(10)

# Define the base search URL with pagination
base_search_url = "https://www.linkedin.com/search/results/people/?geoUrn=%5B%22100517351%22%2C%22102748797%22%2C%22102095887%22%2C%22103644278%22%5D&industry=%5B%22104%22%5D&keywords=recruiter&network=%5B%22S%22%2C%22O%22%5D&origin=FACETED_SEARCH&page={page_num}&sid=V2L"

# Load or create Excel file
file_name = 'linkedin_connections.xlsx'
try:
    # Try to load the existing workbook
    book = load_workbook(file_name)
    writer = pd.ExcelWriter(file_name, engine='openpyxl', mode='a')  # Open the file in append mode
    # writer.book = book  # No need to set this if you're already in append mode, but we'll keep it
    
    # Load existing data
    df_existing = pd.read_excel(file_name, sheet_name='Connections')
    existing_count = len(df_existing)
except FileNotFoundError:
    # If file does not exist, create a new workbook
    writer = pd.ExcelWriter(file_name, engine='openpyxl')
    existing_count = 0

# List to store new data
data = []

# Counter for new entries
new_entries_count = 0
page_num = 1

while new_entries_count < 3:
    search_url = base_search_url.format(page_num=page_num)
    
    # Open the LinkedIn search URL
    driver.get(search_url)
    
    # Wait for the search results to load
    time.sleep(5)

    # Find all the "li" elements containing the search results
    li_elements = driver.find_elements(By.CSS_SELECTOR, 'ul[class^="reusable-search__entity-result-list"] li')

    for li in li_elements:
        try:
            # Check if the li contains the specific button
            connect_button = li.find_element(By.CSS_SELECTOR, 'button[aria-label^="Invite"]')
            if connect_button:
                # Extract the name and URL from the a tag within the correct span
                name_link = li.find_element(By.CSS_SELECTOR, 'span.entity-result__title-text a')
                name = name_link.text.strip()
                url = name_link.get_attribute('href').strip()

                # Split the name before the "View" text if needed
                split_index = name.find('View')
                name = name[:split_index].strip() if split_index != -1 else name

                # Extract primary and secondary subtitles
                primary_subtitle = li.find_element(By.CSS_SELECTOR, 'div[class^="entity-result__primary-subtitle"]')
                secondary_subtitle = li.find_element(By.CSS_SELECTOR, 'div[class^="entity-result__secondary-subtitle"]')

                # Append the extracted data to the list
                data.append({
                    'Name': name,
                    'URL': url,
                    'Primary Subtitle': primary_subtitle.text.strip(),
                    'Secondary Subtitle': secondary_subtitle.text.strip(),
                    'Timestamp': datetime.now().strftime('%d/%m/%Y %I:%M %p')
                })

                new_entries_count += 1

                # Click the connect button
                time.sleep(5)  # Pause between requests to avoid detection
                connect_button.click()
                time.sleep(2)
                
                # Handle the connection request dialog
                send_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Send without a note']")))
                send_button.click()
                WebDriverWait(driver, 10).until(EC.invisibility_of_element((By.XPATH, "//button[@aria-label='Send without a note']")))

                # Wait for the "Connect" button to reappear (in case you're iterating for the next connection)
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button//span[text()='Connect']")))

                if new_entries_count >= 20:
                    break

        except Exception as e:
            print(f"Error processing element: {e}")
            continue

    # Pause before moving to the next page
    if new_entries_count < 20:
        page_num += 1
        time.sleep(5)

# Close the browser after task completion
driver.quit()

# Convert the data to a DataFrame and append it to the Excel file
df_new = pd.DataFrame(data)

if existing_count > 0:
    df_existing = pd.read_excel(file_name, sheet_name='Connections')
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
else:
    df_combined = df_new

# Write the combined data to the Excel file with 'replace' if the sheet already exists
with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    df_combined.to_excel(writer, sheet_name='Connections', index=False)

print(f"{new_entries_count} new entries saved to linkedin_connections.xlsx")
