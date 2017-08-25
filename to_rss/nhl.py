from datetime import datetime

import feedgenerator

from bs4 import BeautifulSoup

import requests

BASE_URL = 'https://www.nhl.com'

# See https://www.nhl.com/info/teams
VALID_TEAMS = {
    # Metropolitan division.
    'hurricanes': 'Carolina Hurricanes',
    'bluejackets': 'Columbus Blue Jackets',
    'devils': 'New Jersey Devils',
    'islanders': 'New York Islanders',
    'rangers': 'New York Rangers',
    'flyers': 'Philadelphia Flyers',
    'penguins': 'Pittsburgh Penguins',
    'capitals': 'Washington Capitals',
    # Atlantic division.
    'bruins': 'Boston Bruins',
    'sabres': 'Buffalo Sabres',
    'redwings': 'Detroit Red Wings',
    'panthers': 'Florida Panthers',
    'canadiens': 'Montréal Canadiens',
    'senators': 'Ottawa Senators',
    'lightning': 'Tampa Bay Lightning',
    'mapleleafs': 'Toronto Maple Leafs',
    # Central division.
    'blackhawks': 'Chicago Blackhawks',
    'avalanche': 'Colorado Avalanche',
    'stars': 'Dallas Stars',
    'wild': 'Minnesota Wild',
    'predators': 'Nashville Predators',
    'blues': 'St. Louis Blues',
    'jets': 'Winnipeg Jets',
    # Pacific division.
    'ducks': 'Anaheim Ducks',
    'coyotes': 'Arizona Coyotes',
    'flames': 'Calgary Flames',
    'oilers': 'Edmonton Oilers',
    'kings': 'Las Angeles Kings',
    'sharks': 'San Jose Sharks',
    'canucks': 'Vancouver Canucks',
    'goldenknights': 'Vegas Golden Knights',
}


def _get_news(name, page_url):
    # Get the HTML page.
    response = requests.get(page_url)

    # Process the HTML using BeautifulSoup!
    soup = BeautifulSoup(response.content, 'html.parser')

    feed = feedgenerator.Rss201rev2Feed(name, page_url, name)

    # Iterate over each article.
    for article in soup.find_all('article'):
        # Get the author element, and pull out the name (and maybe a link).
        author = article.find_all(class_='article-item__contributor')[0]
        author_name = author.contents[0].strip().lstrip('by').strip()
        if author.a:
            author_link = author.a['href']
        else:
            author_link = None
        
        # Get the date element and parse it to a datetime.
        date = article.find_all(class_='article-item__date')[0]

        # The content is split into two pieces that must be re-assembled.
        preview = article.find_all('div', class_='article-item__preview')[0]
        # Note that the full body isn't available, it could be grabbed from the
        # data-url though!

        feed.add_item(title=str(article.h1.string),
                      link=BASE_URL + article['data-url'],
                      description=str(preview),
                      author_name=author_name,
                      author_link=author_link,
                      pubdate=datetime.strptime(date['data-date'], "%Y-%m-%dT%H:%M:%S%z"))

    return feed.writeString('utf-8')


def nhl_news():
    return _get_news('NHL Headlines', '{}/news/'.format(BASE_URL))


def team_news(team):
    return _get_news('{} News'.format(VALID_TEAMS[team]),
                     '{}/{}/news/'.format(BASE_URL, team))


if __name__ == '__main__':
    team_news('islanders')
