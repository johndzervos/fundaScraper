from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from deep_translator import GoogleTranslator

import urllib.request

import os

IMAGE_CLASS_NAME = "media-viewer-overview__section-image"
DESCRIPTION_CLASS_NAME = "object-description-body"
DESCRIPTION_OPEN_BUTTON_CLASS = "object-description-open-button"

MAX_TRANSLATION_LENGTH = 5000

def get_address_name(url):
    """
    Returns the address name, etracted from the url
    """
    address_part = url.split('/')[-1]
    # Address part has the form: huis-{id}-streetname-number
    return '_'.join(address_part.split('-')[2:])

def create_folder(directory_name):
    """
    Creates the ouput directory named after the address
    """
    directory_name = get_address_name(url)
    print(f"Address: {directory_name}")
    if not os.path.exists(directory_name):
        os.mkdir(directory_name)

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
    # TODO preserve the order of downloaded images, maybe with a prefix
    for img in images:
        source = img.get_attribute("src")
        name = source.split('/')[-1]
        urllib.request.urlretrieve(source, f"{directory_name}/{name}")
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

    with open(f'{directory_name}/description.txt', 'w') as f:
        f.write(description)

    # Translation has a max of 5000 chars
    if len(description) > MAX_TRANSLATION_LENGTH:
        description = description[:MAX_TRANSLATION_LENGTH -1]

    description_en = GoogleTranslator(source='nl', target='en').translate(description)

    with open(f'{directory_name}/description_en.txt', 'w') as f:
        f.write(description_en)


url = 'https://www.funda.nl/koop/amsterdam/huis-42202810-wolbrantskerkweg-9/'

# Remove the trailing '/' if it exists
if url[-1] == '/':
    url = url[:-1]

create_folder(url)
download_photos(url)
get_description(url)

print("Done!")