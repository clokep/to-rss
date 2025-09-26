import logging
from datetime import datetime

from bs4 import BeautifulSoup

from to_rss import get_session
from to_rss.rss import ImageEnclosure, RssFeed

logger = logging.getLogger(__name__)

BASE_URL = "https://www.nhl.com"

# See https://www.nhl.com/info/teams
VALID_TEAMS = {
    # Metropolitan division.
    "hurricanes": "Carolina Hurricanes",
    "bluejackets": "Columbus Blue Jackets",
    "devils": "New Jersey Devils",
    "islanders": "New York Islanders",
    "rangers": "New York Rangers",
    "flyers": "Philadelphia Flyers",
    "penguins": "Pittsburgh Penguins",
    "capitals": "Washington Capitals",
    # Atlantic division.
    "bruins": "Boston Bruins",
    "sabres": "Buffalo Sabres",
    "redwings": "Detroit Red Wings",
    "panthers": "Florida Panthers",
    "canadiens": "Montréal Canadiens",
    "fr-canadiens": "Montréal Canadiens (FR)",
    "senators": "Ottawa Senators",
    "lightning": "Tampa Bay Lightning",
    "mapleleafs": "Toronto Maple Leafs",
    # Central division.
    "blackhawks": "Chicago Blackhawks",
    "avalanche": "Colorado Avalanche",
    "stars": "Dallas Stars",
    "wild": "Minnesota Wild",
    "predators": "Nashville Predators",
    "blues": "St. Louis Blues",
    "utah": "Utah Mammoth",
    "jets": "Winnipeg Jets",
    # Pacific division.
    "ducks": "Anaheim Ducks",
    "flames": "Calgary Flames",
    "oilers": "Edmonton Oilers",
    "kings": "Las Angeles Kings",
    "sharks": "San Jose Sharks",
    "kraken": "Seattle Kraken",
    "canucks": "Vancouver Canucks",
    "goldenknights": "Vegas Golden Knights",
}


def _get_news(name, page_url):
    # Get the HTML page.
    response = get_session().get(page_url)

    # Process the HTML using BeautifulSoup!
    soup = BeautifulSoup(response.content, "html.parser")

    feed = RssFeed(name, page_url, name)

    # Iterate over each article.
    for article in soup.find_all(class_="nhl-c-card-wrap"):
        title = article.find("h3")

        if article.name == "a":
            link = article["href"]
        else:
            link = article.find("a")["href"]

        # The content is split into two pieces that must be re-assembled.
        preview = article.find("div", class_="fa-text__body")
        if preview is not None:
            description = preview.get_text()
        else:
            description = ""

        # Find an image from the video preview.
        image = article.find("img")

        time = article.find("time")
        if time:
            pubdate = datetime.fromisoformat(time["datetime"])
        else:
            pubdate = None

        feed.add_item(
            title=title.string,
            link=link,
            description=description,
            pubdate=pubdate,
            enclosure=ImageEnclosure(url=image["src"], mime_type="image/jpg"),
        )

    if len(feed.items) == 0:
        logger.error(f"Created empty feed for {page_url}")

    return feed.writeString("utf-8")


def nhl_news():
    return _get_news("NHL Headlines", f"{BASE_URL}/news/")


def team_news(team):
    if team == "fr-canadiens":
        url = "fr/canadiens"
    else:
        url = team

    return _get_news(f"{VALID_TEAMS[team]} News", f"{BASE_URL}/{url}/news/")
