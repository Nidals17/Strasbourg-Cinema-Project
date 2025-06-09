import subprocess
from Scraping_VOX import Scrap_VOX
from Scraping_UGC import Scrap_UGC  # Replace with your actual module
import logging
import os

print("Starting scrapping")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create handlers
file_handler = logging.FileHandler('Scraper.log', mode='w')
console_handler = logging.StreamHandler()

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

DATA_FOLDER = "data_movies"
os.makedirs(DATA_FOLDER, exist_ok=True)

print("🔄 Scraping fresh UGC data...")
ugc_df = Scrap_UGC()

print("✅ UGC data saved.")

print("🔄 Scraping fresh VOX data...")
vox_df = Scrap_VOX()
print("✅ VOX data saved.")

print("🚀 Launching Streamlit app...")
# Only launch Streamlit locally
if os.environ.get("GITHUB_ACTIONS") != "true":
    print("🚀 Launching Streamlit app...")
    subprocess.run(["streamlit", "run", "Streamlit.py"])
