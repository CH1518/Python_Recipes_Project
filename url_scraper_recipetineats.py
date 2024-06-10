import requests
from bs4 import BeautifulSoup as bs
from base_logger import logger
import db
import sqlalchemy

def run(base_url, recipe_types):
    known_urls = set([row.url for row in db.session.query(db.URL.url).all()])
    new_url_counter = 0
    for recipe_type in recipe_types:
        #logger.info(recipe_type)
        counter = 1
        while True:
            endpoint = base_url+recipe_type
            if counter > 1:
                endpoint += f'/?fwp_paged={counter}'
            result = requests.get(endpoint, headers = headers)
            if "Sorry, no content matched your criteria." in result.text:
                break            
            new_url_counter += get_urls(result, known_urls)
            counter += 1
        db.session.commit()
    #logger.info(f"saved {new_url_counter} new urls")

def get_urls(result, known_urls):    
    soup = bs(result.text,'html.parser')  
    post_items = soup.find_all("header", "entry-header")
    new_records = []
    for post_item in post_items:
        try:
            url = post_item.find("a").get("href")
            if url in known_urls:
                continue
        except Exception as e:
            #logger.debug(f"url not found in post-item on page {result.url}")
            continue
        try:  
            recipe_name = post_item.find("a", "entry-title-link").text  
        except Exception as e:
            recipe_name = sqlalchemy.sql.null()
        try:
            image = post_item.find("img").get("src") 
        except Exception as e:
            image = sqlalchemy.sql.null()
        #logger.info(recipe_name)        
        new_record = db.URL(
            url = url,
            recipe_name = recipe_name,
            image = image
        )
        new_records.append(new_record)
        known_urls.add(url)
    db.session.add_all(new_records)
    return len(new_records)

if __name__ == '__main2__':
    headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
    base_url = "https://www.recipetineats.com/category/"
    recipe_types = [
        "main-dishes",
        "soup-recipes",
        "pasta-recipes",
        "dessert-recipes",
        "breads",
        "dip-recipes",
        "baking-recipes",
        "asian-recipes",
        "beef-recipes",
        "chicken-recipes",
        "lamb-recipes",
        "breakfast-recipes",
        "muffin-recipes",
        "egg-recipes"
    ]

run(base_url, recipe_types)