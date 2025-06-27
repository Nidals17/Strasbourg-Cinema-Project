import re
import time
import logging
import os
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)
logger.info("Scraping started for UGC") 

def get_film_links(driver, url):
    links = []
    logging.info("Navigating to main cinema page.")
    driver.get(url)

    try:
        cookie_button = driver.find_element(By.CSS_SELECTOR, ".hagreed__continue.hagreed-validate")
        cookie_button.click()
        logging.info("Pop-up closed successfully.")
    except Exception as e:
        logging.warning(f"Could not find the cookie pop-up: {e}")

    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    dates_contents_div = soup.find('div', class_='dates-content')

    if not dates_contents_div:
        logging.warning("Could not find the div with class 'dates-content'.")
        return links

    movie_blocks = dates_contents_div.find_all('div', class_='block--title text-uppercase')
    base_url = 'https://www.ugc.fr/'

    for block in movie_blocks:
        a_tag = block.find('a', href=True)
        if a_tag:
            link = base_url + a_tag['href']
            links.append(link)
            logging.info(f"Film link found: {link}")

    logging.info(f"Total film links found: {len(links)}")
    return links


def scrape_film_details(driver, films_link):
    all_films_UGC = pd.DataFrame()
    jour_translation = {
        'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
        'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
    }

    wait = WebDriverWait(driver, 3)

    for link in films_link:
        logging.info(f"Scraping film page: {link}")
        driver.get(link)
        time.sleep(2)

        try:
            titre = driver.find_element(By.XPATH, '//*[@id="film-presentation"]/div[1]/div/div/div/div[2]/h1').text.strip()
            logging.info(f"Title found: {titre}")
        except Exception as e:
            logging.warning(f"Skipping film due to missing title: {e}")
            continue

        try:
            group_info = driver.find_element(By.CSS_SELECTOR, "div.group-info.d-none.d-md-block p.color--dark-blue").text
            genre = group_info.split('·')[0].strip().upper()
            if re.search(r'\d', genre) or 'Sortie' in genre or 'Avec' in genre:
                logging.warning(f"Irrelevant genre detected, skipping film: {genre}")
                continue
        except:
            genre = "Unknown"
            logging.info("Genre not found; defaulted to 'Unknown'.")

        try:
            dates_nav = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dates-nav")))
            slider_items = dates_nav.find_elements(By.XPATH, './/div[starts-with(@class, "slider-item")]')
        except Exception as e:
            logging.warning(f"Skipping film due to date navigation issue: {e}")
            continue

        lst = []

        for item in slider_items:
            try:
                item_id = item.get_attribute("id")
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', item_id)
                if not date_match:
                    continue

                date_text = date_match.group(1)
                date_obj = datetime.strptime(date_text, '%Y-%m-%d')
                jour = jour_translation.get(date_obj.strftime('%A'), date_obj.strftime('%A'))
                date_formatted = date_obj.strftime('%d/%m/%Y')

                driver.execute_script("arguments[0].scrollIntoView(true);", item)
                time.sleep(0.2)
                driver.execute_script("arguments[0].click();", item)

                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "screening-start")))
                horaires = [elem.text.strip() for elem in driver.find_elements(By.CLASS_NAME, "screening-start") if elem.text.strip()]

                for hor in horaires:
                    lst.append({
                        "titre": titre,
                        "genre": genre,
                        "date": date_formatted,
                        "jour": jour,
                        "horaire": hor
                    })

            except Exception as e:
                logging.warning(f"Failed to extract horaires for date {item_id}: {e}")
                continue

        if lst:
            df = pd.DataFrame(lst)
            all_films_UGC = pd.concat([all_films_UGC, df], ignore_index=True)
            logging.info(f"Added {len(lst)} showtimes for film: {titre}")

        time.sleep(0.2)
    print(all_films_UGC)
    return all_films_UGC


def Scrap_UGC():
    logging.info("Starting UGC cinema scraper.")

    try:

        is_github = os.environ.get("GITHUB_ACTIONS") == "true"

        if is_github:
            chrome_options = Options()
            chrome_options.add_argument("--headless") 
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920x1080")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

        logging.info("WebDriver initialized successfully.")
    except Exception as e:
        logging.critical(f"Failed to initialize WebDriver: {e}")
        return

    url = 'https://www.ugc.fr/cinema-ugc-cine-cite-strasbourg.html'
    logging.info("Starting film links extraction...")
    films = get_film_links(driver, url)
    logging.info(f"{len(films)} film links retrieved.")

    logging.info("Starting film details scraping...")
    films_data_UGC = scrape_film_details(driver, films)

    driver.quit()
    logging.info("WebDriver closed.")

    output_path = "data_movies/UGC.csv"
    if not films_data_UGC.empty:
        films_data_UGC.to_csv(output_path, index=False)
    else:
        logging.warning("No data scraped. File not saved.")    
    
    logging.info(f"Scraping finished. Data saved to {output_path}.")
    logging.info(f"Total records scraped: {len(films_data_UGC)}")


