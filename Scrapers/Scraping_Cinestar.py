import os
import re
import time
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# URL of Ciné Star cinema
URL = 'https://www.cinema-star.com/horaires/'

# Mapping of short to full day names
day_map = {
    "Lu.": "Lundi", "Ma.": "Mardi", "Me.": "Mercredi",
    "Je.": "Jeudi", "Ve.": "Vendredi", "Sa.": "Samedi", "Di.": "Dimanche",
    "Aujourd’hui": "Aujourd’hui"
}

def remove_surrounding_quotes(text):
    if not isinstance(text, str):
        return text
    # Remove surrounding double or single quotes, if present
    return re.sub(r'^["\'](.*)["\']$', r'\1', text).strip()


def is_future_date(date_str):
    """Check if date is today or in the future."""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date() >= datetime.today().date()
    except:
        return False


def get_film_data_from_cinestar():
    logger.info("Requesting Ciné Star website...")
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    movie_divs = soup.find_all("div", class_="wrap-fiche-film")

    films_list = []

    logger.info(f"Found {len(movie_divs)} films.")

    for div in movie_divs:
        try:
            # --- Title ---
            h2_tag = div.find("h2")
            if not h2_tag:
                continue
            a_tag = h2_tag.find("a", title=True)
            if not a_tag or "Voir la fiche du film " not in a_tag['title']:
                continue
            movie_title = a_tag['title'].split("Voir la fiche du film ", 1)[-1].strip()
            if "QUINZAINE EN SALLE :" in movie_title:
                movie_title = movie_title.split("QUINZAINE EN SALLE : ", 1)[-1].strip()

            # --- Genre ---
            try:
                genre_span = div.find("span", class_="horaires-genre")
                genre = genre_span.find("strong", class_="hi").text.strip().upper() if genre_span else "UNKNOWN"
            except:
                genre = "UNKNOWN"

            # --- Horaires by day ---
            horaires_divs = div.select("div.tablehorairein table td")
            for td in horaires_divs:
                day_tag = td.select_one("span.fchead")
                if not day_tag:
                    continue

                raw_day = day_tag.get_text(strip=True)
                if raw_day == "Aujourd’hui":
                    full_day = "Aujourd’hui"
                    date_obj = datetime.today()
                else:
                    abbr = raw_day[:3]
                    num = re.sub(r'\D', '', raw_day)
                    if not num:
                        continue
                    full_day = day_map.get(abbr, abbr)
                    day_number = int(num)
                    today = datetime.today()

                    # If date has passed, assume it's for next month
                    if day_number < today.day:
                        try:
                            date_obj = datetime(today.year, today.month + 1, day_number)
                        except:
                            # handle December
                            date_obj = datetime(today.year + 1,
                                                 1, day_number)
                    else:
                        date_obj = datetime(today.year, today.month, day_number)

                date_str = date_obj.strftime("%d/%m/%Y")

                # Filter out past dates
                if not is_future_date(date_str):
                    continue

                times = [t.get_text(strip=True) for t in td.select("div.fc") if t.get_text(strip=True)]

                if not times:
                    continue

                for time_show in times:
                    films_list.append({
                        "titre": movie_title,
                        "genre": genre,
                        "date": date_str,
                        "jour": full_day,
                        "horaire": time_show
                    })

        except Exception as e:
            logger.warning(f"Error while processing a movie block: {e}")
            continue

    return pd.DataFrame(films_list)


def Scrap_CineStar():
    start_time = time.time()
    logger.info("Scraping Ciné Star started.")

    # Create folder
    data_folder = "data_movies"
    os.makedirs(data_folder, exist_ok=True)

    # Get data
    df = get_film_data_from_cinestar()
    df['titre'] = df['titre'].apply(remove_surrounding_quotes)

    # Save to CSV
    save_path = os.path.join(data_folder, "CineStar.csv")
    df.to_csv(save_path, index=False)
    logger.info(f"Saved data to {save_path}")
    duration = round((time.time() - start_time) / 60, 2)
    logger.info(f"Scraping Ciné Star completed in {duration} minutes.")

    return df