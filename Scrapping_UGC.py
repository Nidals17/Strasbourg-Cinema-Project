import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_film_links(driver, url):
    links = []
    driver.get(url)

    # Close cookie pop-up only here
    try:
        cookie_button = driver.find_element(By.CSS_SELECTOR, ".hagreed__continue.hagreed-validate")
        cookie_button.click()
        print("Pop-up closed successfully.")
    except Exception as e:
        print("Could not find the cookie pop-up:", e)

    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    dates_contents_div = soup.find('div', class_='dates-content')

    if not dates_contents_div:
        print("Could not find the div with class 'dates-content'.")
        return links

    movie_blocks = dates_contents_div.find_all('div', class_='block--title text-uppercase')
    base_url = 'https://www.ugc.fr/'

    for block in movie_blocks:
        a_tag = block.find('a', href=True)
        if a_tag:
            links.append(base_url + a_tag['href'])

    return links


def scrape_film_details(driver, films_link):
    all_films_UGC = pd.DataFrame()

    jour_translation = {
        'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
        'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
    }

    wait = WebDriverWait(driver, 4)

    for link in films_link:
        driver.get(link)
        time.sleep(2)

        # Title
        try:
            titre = driver.find_element(By.XPATH, '//*[@id="film-presentation"]/div[1]/div/div/div/div[2]/h1').text.strip()
        except:    
            continue

        # Genre
        try:
            group_info = driver.find_element(By.CSS_SELECTOR, "div.group-info.d-none.d-md-block p.color--dark-blue").text
            genre = group_info.split('·')[0].strip().upper()
            if re.search(r'\d', genre) or 'Sortie' in genre or 'Avec' in genre:
                continue
        except:
            genre = "Unknown"

        try:
            dates_nav = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dates-nav")))
            slider_items = dates_nav.find_elements(By.XPATH, './/div[starts-with(@class, "slider-item")]')
        except Exception:
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

            except Exception:
                continue

        if lst:
            df = pd.DataFrame(lst)
            all_films_UGC = pd.concat([all_films_UGC, df], ignore_index=True)

        time.sleep(0.2)

    return all_films_UGC


def main():

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    url = 'https://www.ugc.fr/cinema-ugc-cine-cite-strasbourg.html'

    print("Getting film links...")
    films = get_film_links(driver, url)
    print(f"Found {len(films)} film links.")

    print("Scraping film details...")
    films_data_UGC = scrape_film_details(driver, films)

    driver.quit()
    films_data_UGC.to_csv("data_movies/UGC.csv", index=False)
    print(films_data_UGC)



if __name__ == "__main__":
    main()



