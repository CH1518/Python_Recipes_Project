import time
import requests
from bs4 import BeautifulSoup as bs
import sqlalchemy
import db
from base_logger import logger

headers = {"User-Agent" :"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}

def run():
    visited_urls = set()
    select = "select id, url, recipe_name from url where id not in (select url_id from recipe) and skip is null"
    with db.engine.connect() as conn:
        urls = [row for row in db.engine.execute(sqlalchemy.text(select))]
    new_records = []
    for i, row in enumerate(urls):
        try:
            scrapeRecipe(row, new_records, visited_urls)
            logger.info(f"scraping - {row.recipe_name}")
        except Exception as e:
            logger.warning(f"{row.url} caused scrape function exception - {e}")
        if (i+1) % 50 == 0:
            time.sleep(30)
    
    db.session.add_all(new_records)
    db.session.commit()
    flag_unscrapable_urls()
    
def flag_unscrapable_urls(): 
    select = "select id, url, recipe_name from url where id not in (select url_id from recipe) and skip is null"   
    with db.engine.connect() as conn:
        rows = [row for row in db.engine.execute(sqlalchemy.text(select))]   
    for row in rows:
        #db.session.query(db.URL).filter(db.URL.id == row.id) #update skip column to be true
        to_update = db.session.query(db.URL).filter(db.URL.id == row.id)
        to_update.skip = True
        logger.info(f"{row.recipe_name} flagged to skip from URL table\n{row.url}")
    db.session.commit()

def scrapeRecipe(row, new_records, visited_urls):
    url = row.url
    soup = _make_soup(url)

    if row.id in visited_urls:
        logger.info(f"Skipping duplicate url_id: {row.id}")
        return
    
    try:
        author = soup.find('p', 'not-prose').find('a').text.replace("\xa0", '')
    except:
        logger.debug("Didn't find author")
        author = sqlalchemy.sql.null()
    try:
        description = description_helper(soup)
    except:
        logger.debug("Didn't find description")
        description = sqlalchemy.sql.null()

    ### Fill JSON
    recipe = {}
    try:
        ingredients = [li.text for li in soup.find('div', 'mb-8').find_all('li')]
        recipe['ingredients'] = ingredients
    except Exception as e:
        logger.info("Didn't find ingredients")
        logger.info(e)
        pass
    try:
        instructions = [li.text for li in soup.find('ul', 'font-serif leading-7 text-fok-navy-500 list-decimal text-lg').find_all('li')]
        recipe['instructions'] = instructions
    except Exception as e:
        logger.info("Didn't find instructions")
        logger.info(e)
        pass
    try:
        tags = [li.text for li in soup.find('div', 'not-prose my-8 flex flex-col items-baseline text-sm uppercase md:mb-0').find_all('li')]
        recipe['tags'] = tags
    except Exception as e:
        logger.info("Didn't find tags")
        logger.info(e)
        pass
    try:
        recipe = _prep_cook_ready_yield(soup, recipe)
    except Exception as e:
        logger.info("Didn't find prep, cook, ready, yield")
        logger.info(e)
        pass

    if 'instructions' in recipe\
    or 'ingredients' in recipe:
        new_record = db.Recipe(
            url_id = row.id,
            author = author,
            description = description,
            recipe = recipe
        )
        new_records.append(new_record)
        visited_urls.add(row.id)

def _prep_cook_ready_yield(soup, recipe):
    P, C, R, M = 'Prep-time:', 'Cook Time:', 'Ready In:', 'Makes'
    spans = [span.text for span in soup.find('div','box-post-control mb-6').find_all('span')]
    for span in spans[1:]:
        if R in span: ## Maybe span.text?
            recipe['ready in'] = span.text.split(R)[1].strip()
        elif P in span:
            recipe['prep time'] = span.text.split(R)[1].replace("/", "").strip()
        elif "Cook Time:" in span:
            recipe['cook-time'] = span.text.split(C)[1].strip()
        elif M in span:
            recipe['yields'] = span.text.split(M)[1].strip()
    return recipe


def _make_soup(url):
    return bs(requests.get(url, headers = headers).text, 'html.parser')


def description_helper(soup):
    description = ''
    div_tags = soup.find_all('div', class_='core-paragraph')
    for div_tag in div_tags:
        p_tags = div_tag.find_all('p')
        for p_tag in p_tags:
            if len(p_tag.text) > 0 and 'not-prose' not in p_tag.find_parent().attrs['class']:
                description += f" {p_tag.text}"
    description = description.replace("\n", '').replace("\xa0", '').strip()
    return description

if __name__ == "__main__":
    headers = {"User-Agent" :"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}
    run()
