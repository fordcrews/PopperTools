import os
import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Configuration
download_dir = "C:\\vPinball\\PinUPSystem"
url = "https://virtual-pinball-spreadsheet.web.app/csvexport"
os.makedirs(download_dir, exist_ok=True)

# Backup existing puplookup.csv if it exists
puplookup_path = os.path.join(download_dir, "puplookup.csv")
backup_path = os.path.join(download_dir, "puplookup.bak")
if os.path.exists(puplookup_path):
    if os.path.exists(backup_path):
        os.remove(backup_path)
    os.rename(puplookup_path, backup_path)

# Set up Selenium with Chrome in headless mode
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)
driver.get(url)

# Wait for the page to load and the button to become clickable
time.sleep(5)

# Click the "Pinup Popper" button to trigger the CSV download
button = driver.find_element(By.XPATH, "//button[contains(text(), 'Pinup Popper')]")
button.click()

# Wait for the download to complete
time.sleep(10)

# Extract the CSV data URL
links = driver.find_elements(By.XPATH, "//a[@href]")
csv_data_url = None
for link in links:
    href = link.get_attribute("href")
    if href.startswith("data:text/csv"):
        csv_data_url = href
        break

if csv_data_url:
    # Extract the CSV content from the data URL
    csv_content = csv_data_url.split(',', 1)[1]

    # Decode the percent-encoded CSV content
    decoded_csv_content = urllib.parse.unquote(csv_content)

    file_name = os.path.join(download_dir, "puplookup.csv")

    # Save the CSV content to a file
    with open(file_name, "w", encoding="utf-8") as csv_file:
        csv_file.write(decoded_csv_content)
    print(f"Saved {file_name}")
else:
    print("CSV data URL not found.")

driver.quit()
