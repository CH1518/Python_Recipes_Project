from url_scraper import run as url_run
from recipe_scraper import run as recipe_run
from base_logger import logger

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

logger.info("START")
logger.info("start url_run")
url_run(base_url, recipe_types)
logger.info("start recipe_run")
recipe_run()
logger.info("DONE")