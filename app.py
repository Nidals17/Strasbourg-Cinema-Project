import subprocess
from Scraping_VOX import Scrap_VOX
from Scraping_UGC import Scrap_UGC  # Replace with your actual module
import logging
import os

print("Starting scrapping")

logging.basicConfig(
    filename='Scraper.log',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DATA_FOLDER = "data_movies"
os.makedirs(DATA_FOLDER, exist_ok=True)

print("🔄 Scraping fresh UGC data...")
ugc_df = Scrap_UGC()

print("✅ UGC data saved.")

print("🔄 Scraping fresh VOX data...")
vox_df = Scrap_VOX()
print("✅ VOX data saved.")

print("🚀 Launching Streamlit app...")
subprocess.run(["Streamlit", "run", "Streamlit.py"])
