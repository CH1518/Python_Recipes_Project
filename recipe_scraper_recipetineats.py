import time
import requests
from bs4 import BeautifulSoup as bs
import sqlalchemy
import db
from base_logger import logger

headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
url = "https://www.recipetineats.com/"

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

    if row.id in visited_urls:
        logger.info(f"Skipping duplicate url_id: {row.id}")
        return

    soup = _make_soup(url)

    try:
        author = soup.find('span', 'entry-author-name').text
    except:
        logger.debug("Didn't find author")
        author = None  # Set author to None if not found

    try:
        description = description_helper(soup)
    except:
        logger.debug("Didn't find description")
        description = None  # Set description to None if not found

    recipe = {}
    try:
        ingredients = [li.text for li in soup.find('div', 'mb-8').find('ol').find_all('li')]
        if ingredients:
            ingredients_list = []
            for ingredient_group in ingredients:
                ul_elements = ingredient_group.find_all('ul')
                for ul_element in ul_elements:
                    h4_element = ul_element.find_previous_sibling('h4')
                    if h4_element:
                         ingredients_list.append(h4_element.text + ':')
                    li_items = ul_element.find_all('li')
                    for li_item in li_items:
                         ingredients_list.append(li_item.text)
            recipe['ingredients'] = ingredients_list
    except Exception as e:
        logger.info("Didn't find ingredients")
        logger.info(e)
        pass
    
    try:
        instructions = soup.find_all('div', class_='wprm-recipe-instruction-group')
        if instructions:
            instructions_list = []
            for instruction_group in instructions:
                ul_elements = instruction_group.find_all('ul')
                for ul_element in ul_elements:
                    h4_element = ul_element.find_previous_sibling('h4')
                    if h4_element:
                        instructions_list.append(h4_element.text + ':')
                    li_items = ul_element.find_all('li')
                    for li_item in li_items:
                        instructions_list.append(li_item.text)
            recipe['instructions'] = instructions_list
    except Exception as e:
        logger.info("Didn't find instructions")
        logger.info(e)
        pass
    
    try:
        tags = [span.text for span in soup.find('div', 'wprm-recipe-block-container wprm-recipe-block-container-separate wprm-block-text-normal wprm-recipe-tag-container wprm-recipe-keyword-container').find_all('span')]
        recipe['tags'] = tags
    except Exception as e:
        logger.info("Didn't find tags")
        logger.info(e)
        pass

    try:
        recipe = _prep_cook_ready_yield(soup, recipe)
    except Exception as e:
        logger.info("Didn't find prep, cook, total")
        logger.info(e)
        pass

    if 'instructions' in recipe or 'ingredients' in recipe:
        new_record = db.Recipe(
            url_id=row.id,
            author=author,
            description=description,
            recipe=recipe
        )
        new_records.append(new_record)
        visited_urls.add(row.id)

def _prep_cook_ready_yield(soup, recipe):
    P, T, C = 'Prep-time:', 'Total:', 'Cook:'
    spans = soup.find('div', 'wprm-entry-info').find_all('span')
    for i in range(len(spans) - 1):
        span = spans[i]
        next_span = spans[i + 1]
        if C in span: ## Maybe span.text?
            recipe['Cook'] = f"{span.text}: {next_span.text}"
        elif P in span:
            recipe['Prep'] = f"{span.text}: {next_span.text}"
        elif T in span:
            recipe['Total'] = f"{span.text}: {next_span.text}"

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
    headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
    run()

run()