import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s', datefmt = '%m/%d/%Y %I:%M:%S %p')

ch = logging.StreamHandler()
ch.setFormatter(formatter)

fh = logging.FileHandler('log/scraper.log')
fh.setFormatter(formatter)

logger.addHandler(ch)
logger.addHandler(fh)