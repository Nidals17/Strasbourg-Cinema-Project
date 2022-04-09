Vox-Cinema-project

from selenium import webdriver
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

url='https://www.cine-vox.com/films-a-l-affiche/'
url

req= requests.get(url)
soup= BeautifulSoup(req.text,'html.parser')
str(soup)
films = soup.find_all('a' ,class_= 'vignette')
films =re.findall('<a class="vignette url"(.*?)/></a>', str(soup))
len(films)
films2 ='https://www.cine-vox.*?"'
films_link = re.findall(films2, str(films))
films_link

PATH = "C:\Program Files (x86)\chromedriver.exe"

driver = webdriver.Chrome(PATH)
all_films = pd.DataFrame()

for i in range(len(films_link)):
    if i == 0:
        wo_agreeing = True
    else:
        wo_agreeing = False
        
    driver.get(films_link[i])
    if wo_agreeing:
        driver.find_element_by_class_name("didomi-continue-without-agreeing").click()
        driver.find_element_by_id("close").click()

    titre=(driver.find_element_by_class_name('ff_titre').text)
    genre=(driver.find_element_by_class_name('ff_genre').text)
    
    jour=[]
    date=[]
    for i in range(0,len(driver.find_elements_by_class_name('hr_jour'))):
         if (driver.find_elements_by_class_name('hr_jour')[i].text) !='':
            jour.append(driver.find_elements_by_class_name('hr_jour')[i].text[:4])
            dates=driver.find_elements_by_class_name('hr_jour')[i].text
            dates=re.sub('\D', '', dates)
            date.append(dates)
    n=len(date)
    
    lst = []
    for i in range(1,n+1):
        driver.find_element_by_xpath('//*[@id="horaires"]/div/div[1]/div/div[{}]'.format(str(i))).click()
        lst.append({
        'titre' : titre,
        'genre' : genre.lower(),
        'jour' : jour[i-1],
        'date' : date[i-1],
        'hor' : [hor.text for hor in driver.find_elements_by_class_name('hor') if hor.text != '']
        })
    if lst:
        df = pd.DataFrame(lst).explode('hor')
        all_films = pd.concat([all_films,df])
        
    time.sleep(2)
    

def jouer():
    
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    
    print("Bienvenue sur CineVox \n")
    quit = "2"
    while quit== "2":
        type = input('Retrouvez vos films par : \n 1) Genre\n 2) Nom\n 3) Jour \n Pour quitter, tapez "4" \n ')
        if type == '1':
            list_genre=['thriller','action','comédie','famille','aventure','drame','animation']
            dict_genre = {}
            for i in range(len(list_genre)):
                dict_genre[i] = list_genre[i]
                print(str(i) + ')' + list_genre[i])
            genre=int(input('\n  \n Veuillez faire votre choix de genre parmi cette liste \n '))
            def pargenre(genre):
                if genre in range(len(list_genre)):
                    return pd.DataFrame(all_films[all_films.genre.str.contains(dict_genre[genre])])
                else:
                    return("Choix incorrect")
            display(pargenre(genre))

        elif type == '2':

            dict_titre = {}
            for i in range(len(list(set(all_films.titre)))):
                dict_titre[i] = list(set(all_films.titre))[i]

                print(str(i) + ") " + list(set(all_films.titre))[i])
            parnom=int(input("Veuillez faire votre choix de film parmi cette liste \n"))

            def prnom(parnom):
                if parnom in range(len(list(set(all_films.titre)))):
                    return pd.DataFrame(all_films[all_films.titre.str.contains(dict_titre[parnom])])
                else:
                    return("Choix incorrect")
            display(prnom(parnom))

        elif type == '3':
            dict_jour = {}
            for i in range(len(list(set(all_films.jour)))):
                dict_jour[i] = list(set(all_films.jour))[i]

                print(str(i) + ") " + list(set(all_films.jour))[i])
            jour=int(input(" Veuillez faire choix d'un jour \n")) 
            def parjour(jour):
                if jour in range(len(list(set(all_films.jour)))):
                    return pd.DataFrame(all_films.loc[all_films["jour"]==dict_jour[jour]])
                else:
                    return("Choix incorrect")

            display(parjour(jour))

        elif type == '4':
            return("Au revoir \n Au plaisir de vous revoir bientôt")
            break

        else:
            print("Choix incorrect")
        
        quit = input('Pour quitter : 1 \nPour choisir à nouveau : 2\n').upper()
        if quit == '1':
            return("Merci d'avoir choisi CineVox \nAu plaisir de vous accueillir prochainement dans nos locaux")
        
        
print(jouer())
