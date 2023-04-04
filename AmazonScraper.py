import time
import argparse
from bs4 import BeautifulSoup
from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions


def get_driver():
    service = ChromeService(executable_path='/path/to/chromedriver')
    options = ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_reviews(url):
    retry_strategy = Retry(
        total=3,
        status_forcelist=[502, 503],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    response = session.get(url)
    if response.status_code != 200:
        raise ValueError(f'Request failed with status code {response.status_code}')
    soup = BeautifulSoup(response.content, 'html.parser')
    reviews_section = soup.find(id='cm-cr-dp-review-list')
    if reviews_section is None:
        raise ValueError('Could not find reviews section on page')
    review_containers = reviews_section.find_all('div', {'data-hook': 'review'})
    reviews = []
    for container in review_containers:
        review_text = container.find('span', {'data-hook': 'review-body'}).text.strip()
        review_text = review_text.replace('Read more', '')
        star_rating = container.find('span', {'class': 'a-icon-alt'}).text.split()[0]
        reviews.append({'review_text': review_text, 'star_rating': star_rating})

    driver = get_driver()
    driver.get(url)
    time.sleep(5)  # wait for page to load
    while True:
        try:
            show_more_button = driver.find_element_by_id('cm_cr-show-more-link')
            show_more_button.click()
            time.sleep(2)
        except:
            break
    response = driver.page_source
    soup = BeautifulSoup(response, 'html.parser')
    reviews_section = soup.find(id='cm-cr-dp-review-list')
    if reviews_section is None:
        raise ValueError('Could not find reviews section on page')
    review_containers = reviews_section.find_all('div', {'data-hook': 'review'})
    for container in review_containers:
        review_text = container.find('span', {'data-hook': 'review-body'}).text.strip()
        review_text = review_text.replace('Read more', '')
        star_rating = container.find('span', {'class': 'a-icon-alt'}).text.split()[0]
        reviews.append({'review_text': review_text, 'star_rating': star_rating})
    driver.quit()
    return reviews


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape Amazon product reviews')
    parser.add_argument('url', metavar='URL', type=str, help='URL of the Amazon product page')
    args = parser.parse_args()
    url = args.url
    try:
        reviews = get_reviews(url)
        for review in reviews:
            print(f'Review: {review["review_text"]}')
            print(f'Star rating: {review["star_rating"]}')
            print('-------------------------------------')
        print(f'Total reviews: {len(reviews)}')
    except Exception as e:
        print(f'Error: {str(e)}')
