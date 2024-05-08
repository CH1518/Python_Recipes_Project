import requests
from bs4 import BeautifulSoup as bs
import db
import sqlalchemy
from base_logger import logger

headers = {"User-Agent" :"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}
base = "https://www.forksoverknives.com"

def run(base_url, recipe_types):
    known_urls = set([row.url for row in db.session.query(db.URL.url).all()])
    new_url_counter = 0
    for recipe_type in recipe_types:
        logger.info(recipe_type)
        counter = 1
        while True:
            endpoint = base_url+recipe_type
            if counter > 1:
                endpoint += f'/page/{counter}'
            result = requests.get(endpoint, headers = headers)
            if result.status_code != 200:
                break
            new_url_counter += get_urls(result, known_urls)
            counter += 1
        db.session.commit()
    logger.info(f"saved {new_url_counter} new urls")

def get_urls(result, known_urls):    
    soup = bs(result.text)   
    post_items = soup.find_all("li", "list-none")
    new_records = []
    for post_item in post_items:
        try:
            url = base+post_item.find("a").get("href")
            if url in known_urls:
                continue
        except Exception as e:
            logger.debug(f"url not found in post-item on page {result.url}")
            continue
        try:  
            recipe_name = post_item.find("h3").text  
        except Exception as e:
            recipe_name = sqlalchemy.sql.null()
        try:
            image = post_item.find("img").get("src")  
        except Exception as e:
            image = sqlalchemy.sql.null()
        logger.info(recipe_name)        
        new_record = db.URL(
            url = url,
            recipe_name = recipe_name,
            image = image
        )
        new_records.append(new_record)
        known_urls.add(url)
    db.session.add_all(new_records)
    return len(new_records)
    
if __name__ == '__main__':
    headers = {"User-Agent" :"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}
    base_url = "https://www.forksoverknives.com/recipes/"
    base = "https://www.forksoverknives.com"
    recipe_types = [
            "amazing-grains",
            "vegan-baked-stuffed",
            "vegan-breakfast",
            "vegan-burgers-wraps",
            "vegan-desserts",
            "vegan-pasta-noodles",
            "vegan-salads-sides",
            "vegan-sauces-condiments",
            "vegan-snacks-appetizers",
            "vegan-soups-stews"
        ]
