import re
import time
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


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
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'html.parser')
    film_elements = soup.find_all('a', class_='vignette')
    return [film['href'] for film in film_elements if 'href' in film.attrs]


def scrape_film_details(driver, films_link):
    """Scrape title, genre, dates, and showtimes from each film page."""
    all_films_VOX = pd.DataFrame()

    day_mapping = {
        "Lun.": "Lundi", "Mar.": "Mardi", "Mer.": "Mercredi",
        "Jeu.": "Jeudi", "Ven.": "Vendredi", "Sam.": "Samedi", "Dim.": "Dimanche"
    }

    for i, link in enumerate(films_link):
        driver.get(link)

        # Close popups only once
        if i == 0:
            try:
                driver.find_element(By.CLASS_NAME, "didomi-continue-without-agreeing").click()
                driver.find_element(By.ID, "close").click()
                print("Pop-up fermé avec succès.")
            except:
                pass

        try:
            titre = driver.find_element(By.CLASS_NAME, "ff_titre").text
        except:
            titre = "Not yet revealed"

        try:
            raw_genre = driver.find_element(By.CLASS_NAME, "ff_genre").text.lower()
            genre = raw_genre.split(':', 1)[1].strip().upper() if ':' in raw_genre else raw_genre
        except:
            genre = "Unknown"


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

        time.sleep(2)

    return all_films_VOX


def main():
    start_time = time.time()

    # Set up data folder
    data_folder = "data_movies"
    os.makedirs(data_folder, exist_ok=True)

    # Init driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    url = 'https://www.cine-vox.com/films-a-l-affiche/'
    print("Getting film links...")
    films_link = get_film_links(url)
    print(f"Found {len(films_link)} film links.")

    print("Scraping film details...")
    films_data = scrape_film_details(driver, films_link)

    driver.quit()

    # Save to CSV to Data Movies
    csv_path = os.path.join(data_folder, "data_movies/VOX.csv")
    films_data.to_csv(csv_path, index=False)

    duration = round((time.time() - start_time) / 60, 2)
    print(f"Finished scraping. Duration: {duration} minutes.")
    print(f"Data saved to '{csv_path}'.")


if __name__ == "__main__":
    main()
