import re
import time
import os
import requests
import pandas as pd
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logger = logging.getLogger(__name__)
logger.info("Scraping started for UGC") 

def get_full_date(day_number):
    """Convert day number to format (DD/MM/YYYY)."""
    today = datetime.today()
    day_number = int(day_number)

    if day_number < today.day:
        full_date = datetime(today.year, today.month + 1, day_number)
    else:
        full_date = datetime(today.year, today.month, day_number)

    return full_date.strftime("%d/%m/%Y")


def get_film_links(url):
    """Extract links of all films showing."""
    logging.info(f"Requesting film page: {url}")
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'html.parser')
    film_elements = soup.find_all('a', class_='vignette')
    links = [film['href'] for film in film_elements if 'href' in film.attrs]
    logging.info(f"Extracted {len(links)} film links.")
    return links


def scrape_film_details(driver, films_link):
    """Scrape title, genre, dates, and showtimes from each film page."""
    all_films_VOX = pd.DataFrame()

    day_mapping = {
        "Lun.": "Lundi", "Mar.": "Mardi", "Mer.": "Mercredi",
        "Jeu.": "Jeudi", "Ven.": "Vendredi", "Sam.": "Samedi", "Dim.": "Dimanche"
    }

    for i, link in enumerate(films_link[:10]):
        logging.info(f"[{i+1}/{len(films_link)}] Visiting film link: {link}")
        driver.get(link)

        # Close popups only once
        if i == 0:
            try:
                driver.find_element(By.CLASS_NAME, "didomi-continue-without-agreeing").click()
                driver.find_element(By.ID, "close").click()
                logging.info("Pop-up fermé avec succès.")
            except Exception as e:
                logging.warning("Pop-up not found or already closed.")

        try:
            titre = driver.find_element(By.CLASS_NAME, "ff_titre").text
        except:
            titre = "Not yet revealed"
            logging.warning("Titre not found.")

        try:
            raw_genre = driver.find_element(By.CLASS_NAME, "ff_genre").text.lower()
            genre = raw_genre.split(':', 1)[1].strip().upper() if ':' in raw_genre else raw_genre
        except:
            genre = "Unknown"
            logging.warning("Genre not found.")

        jour, date = [], []
        for elem in driver.find_elements(By.CLASS_NAME, "hr_jour"):
            text = elem.text.strip()
            if text:
                jour_short = text[:4]
                jour_full = day_mapping.get(jour_short, jour_short)
                jour.append(jour_full)

                date_number = re.sub(r"\D", "", text)
                date_full = get_full_date(date_number)
                date.append(date_full)

        lst = []
        for j in range(len(date)):
            try:
                driver.find_element(By.XPATH, f'//*[@id="horaires"]/div/div[1]/div/div[{j+1}]').click()
                horaires = [hor.text for hor in driver.find_elements(By.CLASS_NAME, "hor") if hor.text]
            except:
                horaires = []
                logging.warning(f"No horaires found for date {date[j]}.")

            lst.append({
                "titre": titre,
                "genre": genre,
                "date": date[j],
                "jour": jour[j],
                "horaire": horaires
            })

        if lst:
            df = pd.DataFrame(lst).explode("horaire")
            all_films_VOX = pd.concat([all_films_VOX, df], ignore_index=True)
            logging.info(f"Scraped {len(df)} showtimes for '{titre}'.")

        time.sleep(2)

    return all_films_VOX


def Scrap_VOX():
    start_time = time.time()
    logging.info("Scraping started.")

    data_folder = "data_movies"
    os.makedirs(data_folder, exist_ok=True)
    logging.info(f"Data folder ready: {data_folder}")


    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # For headless environment
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)

    url = 'https://www.cine-vox.com/films-a-l-affiche/'
    logging.info("Fetching film links...")
    films_link = get_film_links(url)

    logging.info("Starting film detail scraping...")
    films_data = scrape_film_details(driver, films_link)

    driver.quit()
    logging.info("Browser session ended.")

    # Save results
    save_path = os.path.join(data_folder, "UGC.csv")
    films_data.to_csv(save_path, index=False)
    logging.info(f"Saved scraped data to {save_path}")

    duration = round((time.time() - start_time) / 60, 2)
    logging.info(f"Scraping completed in {duration} minutes.")

    




