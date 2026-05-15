import logging
import os
import sys
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


def _get_news(name: str, page_url: str) -> str:
    # Get the HTML page.
    response = get_session().get(page_url)

    # Process the HTML using BeautifulSoup!
    soup = BeautifulSoup(response.content, "html.parser")

    feed = RssFeed(name, page_url, name)

    # Iterate over each article.
    for article in soup.find_all(class_="nhl-c-card-wrap"):
        header = article.find("h3")

        if article.name == "a":
            link = article["href"]
        else:
            anchor = article.find("a")
            if anchor is None:
                logger.error("No article URL found")
                continue
            link = anchor["href"]

        # The content is split into two pieces that must be re-assembled.
        preview = article.find("div", class_="fa-text__body")
        if preview is not None:
            description = preview.get_text()
        else:
            description = ""

        # Find an image from the video preview.
        image = article.find("img")
        if image:
            enclosure = ImageEnclosure(url=str(image["src"]), mime_type="image/jpg")
        else:
            enclosure = None

        if header:
            title = header.string
        elif image:
            title = image["alt"]

        time = article.find("time")
        if time:
            pubdate = datetime.fromisoformat(str(time["datetime"]))
        else:
            pubdate = None

        feed.add_item(
            title=title,
            link=link,
            description=description,
            pubdate=pubdate,
            enclosure=enclosure,
        )

    if len(feed.items) == 0:
        logger.error(f"Created empty feed for {page_url}")

    return feed.writeString("utf-8")


def nhl_news() -> str:
    return _get_news("NHL Headlines", f"{BASE_URL}/news/")


def team_news(team: str) -> str:
    if team == "fr-canadiens":
        url = "fr/canadiens"
    else:
        url = team

    return _get_news(f"{VALID_TEAMS[team]} News", f"{BASE_URL}/{url}/news/")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        team = "nhl"
    else:
        team = sys.argv[1]

    import to_rss

    to_rss.DISABLE_CACHED_SESSION = True

    if team == "nhl":
        print(nhl_news())

    elif team not in VALID_TEAMS:
        print(f"Invalid team name: {team}")
        exit(1)

    else:
        print(team_news(team))
