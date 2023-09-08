from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from deep_translator import GoogleTranslator

import urllib.request
import pandas as pd
import os

SEARCH_ENTRY_XPATH = "//*[@class='h-full min-w-[228px] shrink-0 cursor-pointer']"
IMAGE_CLASS_NAME = "media-viewer-overview__section-image"
DESCRIPTION_CLASS_NAME = "object-description-body"
DESCRIPTION_OPEN_BUTTON_CLASS = "object-description-open-button"
DATA_CLASS_NAME = "object-kenmerken-list"

MAX_TRANSLATION_LENGTH = 5000

WEB_DRIVER_OPTIONS = Options()
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
WEB_DRIVER_OPTIONS.add_argument(f'user-agent={user_agent}')
WEB_DRIVER_OPTIONS.add_argument('--headless')
WEB_DRIVER_OPTIONS.add_argument('--no-sandbox')
WEB_DRIVER_OPTIONS.add_argument('--disable-dev-shm-usage')
WEB_DRIVER_SERVICE = Service(ChromeDriverManager().install())

ENTRIES_CSV_NAME = 'entries.csv'

DATA_DIRECTORY = 'data'
if not os.path.exists(DATA_DIRECTORY):
    os.mkdir(DATA_DIRECTORY)


def get_address_name(url):
    """
    Returns the address name, extracted from the url
    """
    address_part = url.split('/')[-1]
    # Address part has the form: { huis | appartement }-{id}-streetname-number
    return '_'.join(address_part.split('-')[2:])

def create_directory(directory_name):
    """
    Creates the ouput directory named after the address
    returns the address name
    """
    directory_name = get_address_name(url)
    print(f"Address: {directory_name}")
    if not os.path.exists(f'{DATA_DIRECTORY}/{directory_name}'):
        os.mkdir(f'{DATA_DIRECTORY}/{directory_name}')
    return directory_name

def download_photos(url, directory_name):
    """
    Downloads all the photos in the media library
    """
    print("Downloading photos...")

    driver = webdriver.Chrome(service=WEB_DRIVER_SERVICE, options=WEB_DRIVER_OPTIONS)
    media_url = f"{url}/#overzicht"

    driver.get(media_url)

    images = driver.find_elements(By.CLASS_NAME, IMAGE_CLASS_NAME)
    # preserve the order of downloaded images with a prefix
    for i, img in enumerate(images):
        source = img.get_attribute("src")
        name = f"{i+1:02d}_{source.split('/')[-1]}"
        urllib.request.urlretrieve(source, f"{DATA_DIRECTORY}/{directory_name}/{name}")
    driver.close()
    print(f"{len(images)} photos have been downloaded!")

def clean_string(info_string):
    """
    Remove unnecessary information from the string
    """
    return (info_string.replace("€ ", "")  # in monetary fields
                       .replace(".", "")  # in monetary fields
                       .replace(" m²", "")  # in area fields
                       .replace(" kosten koper", "")  # in asking price field
                       .replace(" Wat betekent dit?", ""))  # in energy label field

def get_info(url, address_name, data):
    """
    Gets data like
    * url
    * asking price, asking price per sqm,
    * construction year
    * living area, plot area
    * number of rooms
    * energy label
    """
    USEFUL_INFO = [
        'Vraagprijs',
        'Vraagprijs per m²',
        'Bouwjaar',
        'Wonen',
        'Perceel',
        'Aantal kamers',
        'Energielabel'
    ]
    info = {
        'url': url,
        'address': address_name,
    }
    for section in data:
        lines = section.get_attribute("innerText").split('\n')
        for field, value in zip(lines, lines[1:]):
            if field in USEFUL_INFO:
                field = '_'.join(field.lower().split())
                info[field] = clean_string(value)
    return info

def get_data(url, address_name):
    """
    Gets data like
    * asking price, asking price per sqm,
    * construction year
    * living area, plot area
    * number of rooms
    * energy label
    Finally gets the description and translates it to English
    """
    driver = webdriver.Chrome(service=WEB_DRIVER_SERVICE, options=WEB_DRIVER_OPTIONS)
    driver.get(url)
    print("Retrieving data...")
    data = driver.find_elements(By.CLASS_NAME, DATA_CLASS_NAME)

    info = get_info(url, address_name, data)

    print("Extracting/Translating the description...")
    # Expand the description
    open_button = driver.find_element(By.CLASS_NAME, DESCRIPTION_OPEN_BUTTON_CLASS)
    driver.execute_script("arguments[0].click();", open_button) 

    description = driver.find_elements(By.CLASS_NAME, DESCRIPTION_CLASS_NAME)[0].get_attribute("innerText")

    driver.close()
    save_and_translate_description(description, address_name)

    return info

def save_and_translate_description(description, address_name):
    """
    Save the original description and then a translation to english
    """
    with open(f'{DATA_DIRECTORY}/{address_name}/description.txt', 'w') as f:
        f.write(description)

    # Translation has a max of 5000 chars
    if len(description) > MAX_TRANSLATION_LENGTH:
        description = description[:MAX_TRANSLATION_LENGTH -1]

    description_en = GoogleTranslator(source='nl', target='en').translate(description)

    with open(f'{DATA_DIRECTORY}/{address_name}/description_en.txt', 'w') as f:
        f.write(description_en)

def get_all_href_urls(search_url):
    """
    Extract all the href links from the search url
    TODO: Deal with paginated results
    """
    print(search_url)

    driver = webdriver.Chrome(service=WEB_DRIVER_SERVICE, options=WEB_DRIVER_OPTIONS)

    driver.get(search_url)

    links = driver.find_elements(By.XPATH, SEARCH_ENTRY_XPATH)

    for link in links:
        print(link.get_attribute("href"))

    urls = [
        link.get_attribute("href")
        for link in links
    ]

    driver.close()

    return urls

def generate_search_url(price_min=None, price_max=None, bedrooms_min=None, area_min=None, city=None, within_distance=None):
    """
    Given the passed parameters, return the funda search url
    """
    basic_search_url = "https://www.funda.nl/zoeken/koop?"
    # TODO: Dynamically construct it based on the parameters
    return f"{basic_search_url}?price=%22{price_min}-{price_max}%22&bedrooms=%22{bedrooms_min}-%22&floor_area=%22{area_min}-%22&publication_date=%225%22&selected_area=%5B%22{city},{within_distance}%22%5D"

price_min = 400000
price_max = 700000
bedrooms_min = 3
area_min = 100
city = 'amsterdam'
within_distance = '2km'

search_url = generate_search_url(price_min, price_max, bedrooms_min, area_min, city, within_distance)

urls = get_all_href_urls(search_url)

# Read already saved entries
try:
    entries_df = pd.read_csv(ENTRIES_CSV_NAME)
except FileNotFoundError:
    entries_df = pd.DataFrame()

print(entries_df)
entries = []

for url in urls[:2]:
    # Remove the trailing '/' if it exists
    if url[-1] == '/':
        url = url[:-1]

    address_name = create_directory(url)
    # download_photos(url, address_name)
    info = get_data(url, address_name)
    entries.append(info)
    # TODO: if entry already exists, compare the data and check if there are differences
# TODO: Generate excel file with the data

entries_df = pd.DataFrame.from_records(entries)

entries_df.to_csv(ENTRIES_CSV_NAME, index=False)

print("Done!")