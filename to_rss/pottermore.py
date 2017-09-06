from datetime import datetime

from bs4 import BeautifulSoup

import feedgenerator

import requests

BASE_URL = 'https://www.pottermore.com'

def parse_date(date_str):
    """Parse a date string of the format 06 September 2017 to a datetime."""

    return datetime.strptime(date_str, '%d %B %Y')


def get_description(soup):
    """Return the meta description."""
    # Get the description.
    meta = soup.find('meta', attrs={'name': 'description'})
    return meta.attrs['content']


def add_item(feed, news_item):
    """All the news items follow the same format, parse the individual fields from the BeautifulSoup element and create a feed item."""
    feed.add_item(
        title=news_item.find('h2').text,
        link=BASE_URL + news_item.find('a').attrs['href'],
        description='',  # Unfortunately there's no additional text.
        pubdate=parse_date(news_item.find('time').text),
    )


def pottermore_news():
    """Parse the Pottermore news page into articles."""
    response = requests.get(BASE_URL + '/news')

    # Process the HTML using BeautifulSoup!
    soup = BeautifulSoup(response.content, 'html.parser')

    # Create the output feed.
    feed = feedgenerator.Rss201rev2Feed('Pottermore News',
                                        BASE_URL + '/news',
                                        get_description(soup))

    # There's 3 levels of articles, featured, other-featured, and other.

    # Add the featured article.
    featured_item = soup.find(id='featured-item')
    add_item(feed, featured_item)

    # Add the other featured items.
    for other_featured in soup.find_all(class_='hub-item l-hub-grid__item'):
        add_item(feed, other_featured)

    # Finally, add any other news items.
    for item in soup.find_all(class_='hub-item l-hub-grid__item l-hub-grid__item--three hub-item--compact News'):
        add_item(feed, item)

    return feed.writeString('utf-8')


def pottermore_features():
    """Parse the Pottermore featured page into articles."""
    response = requests.get(BASE_URL + '/features')

    # Process the HTML using BeautifulSoup!
    soup = BeautifulSoup(response.content, 'html.parser')

    # Create the output feed.
    feed = feedgenerator.Rss201rev2Feed('Pottermore Features',
                                        BASE_URL + '/features',
                                        get_description(soup))

    # There's 3 levels of articles, featured, other-featured, and other.

    # Add the featured article.
    featured_item = soup.find(id='featured-item')
    add_item(feed, featured_item)

    # Add the other featured items.
    for other_featured in soup.find_all(class_='hub-item l-hub-grid__item'):
        add_item(feed, other_featured)

    # Finally, add any other news items.
    for item in soup.select('.hub-item.l-hub-grid__item.l-hub-grid__item--three.hub-item--compact'):
        add_item(feed, item)

    return feed.writeString('utf-8')
