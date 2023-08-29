from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from deep_translator import GoogleTranslator

import urllib.request

import os

DATA_DIRECTORY = 'data'
if not os.path.exists(DATA_DIRECTORY):
    os.mkdir(DATA_DIRECTORY)

SEARCH_ENTRY_XPATH = "//*[@class='h-full min-w-[228px] shrink-0 cursor-pointer']"

IMAGE_CLASS_NAME = "media-viewer-overview__section-image"
DESCRIPTION_CLASS_NAME = "object-description-body"
DESCRIPTION_OPEN_BUTTON_CLASS = "object-description-open-button"

MAX_TRANSLATION_LENGTH = 5000

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
    """
    directory_name = get_address_name(url)
    print(f"Address: {directory_name}")
    if not os.path.exists(f'{DATA_DIRECTORY}/{directory_name}'):
        os.mkdir(f'{DATA_DIRECTORY}/{directory_name}')

def download_photos(url):
    """
    Downloads all the photos in the media library
    """
    print("Downloading photos...")
    directory_name = get_address_name(url)

    options = Options()
    # options.add_argument('--headless')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    media_url = f"{url}/#overzicht"

    driver.get(media_url)

    images = driver.find_elements(By.CLASS_NAME, IMAGE_CLASS_NAME)
    # TODO: preserve the order of downloaded images, maybe with a prefix
    for img in images:
        source = img.get_attribute("src")
        name = source.split('/')[-1]
        urllib.request.urlretrieve(source, f"{DATA_DIRECTORY}/{directory_name}/{name}")
    driver.close()
    print(f"{len(images)} photos have been downloaded!")

def get_description(url):
    """
    Gets the description and translates it to English
    """
    print("Extracting/Translating the description...")
    options = Options()
    # options.add_argument('--headless')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    # Expand the description
    open_button = driver.find_element(By.CLASS_NAME, DESCRIPTION_OPEN_BUTTON_CLASS)
    driver.execute_script("arguments[0].click();", open_button) 

    description = driver.find_elements(By.CLASS_NAME, DESCRIPTION_CLASS_NAME)[0].get_attribute("innerText")

    driver.close()

    directory_name = get_address_name(url)

    with open(f'{DATA_DIRECTORY}/{directory_name}/description.txt', 'w') as f:
        f.write(description)

    # Translation has a max of 5000 chars
    if len(description) > MAX_TRANSLATION_LENGTH:
        description = description[:MAX_TRANSLATION_LENGTH -1]

    description_en = GoogleTranslator(source='nl', target='en').translate(description)

    with open(f'{DATA_DIRECTORY}/{directory_name}/description_en.txt', 'w') as f:
        f.write(description_en)

def get_all_href_urls(search_url):
    """
    Extract all the href links from the search url
    TODO: Deal with paginated results
    """
    print(search_url)
    options = Options()
    # options.add_argument('--headless')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

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

price_min = 400000
price_max = 700000
bedrooms_min = 3
area_min = 100
city = 'amsterdam'
within_distance = '2km'

search_url = f"https://www.funda.nl/zoeken/koop?price=%22{price_min}-{price_max}%22&bedrooms=%22{bedrooms_min}-%22&floor_area=%22{area_min}-%22&publication_date=%225%22&selected_area=%5B%22{city},{within_distance}%22%5D"

urls = get_all_href_urls(search_url)

for url in urls:
    # Remove the trailing '/' if it exists
    if url[-1] == '/':
        url = url[:-1]

    create_directory(url)
    download_photos(url)
    get_description(url)
    # TODO: get other data as well
    # like asking price, area, energy label, number of bedrooms
    # TODO: if entry already exists, compare the data and check if there are differences

print("Done!")