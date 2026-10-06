import logging
import sys
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from to_rss import get_session
from to_rss.rss import ImageEnclosure, RssFeed

logger = logging.getLogger(__name__)

BASE_URL = "https://www.nhl.com"

# NHL files game previews under a topic page rather than in the news feed.
# They are excluded from /news/ but still published at this URL.
PREVIEWS_URL = f"{BASE_URL}/news/topic/game-previews/"

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
    "kings": "Los Angeles Kings",
    "sharks": "San Jose Sharks",
    "kraken": "Seattle Kraken",
    "canucks": "Vancouver Canucks",
    "goldenknights": "Vegas Golden Knights",
}


def _team_slug(name: str) -> str:
    """Generate a team slug from the name."""
    # Special cases for Montréal, St. Louis, and French.
    return (
        name.lower()
        .replace("é", "e")
        .replace(".", "")
        .replace(" (fr)", "")
        .replace(" ", "-")
    )


# Team name to the slug used in game preview article URLs. They are slugified
# versions of VALID_TEAMS with an override for fr-canadiens.
TEAM_SLUGS = {team: _team_slug(name) for team, name in VALID_TEAMS.items()}


def _fetch_items(page_url: str) -> list[dict]:
    """Fetch a listing page and return one dict per article on it."""
    # Get the HTML page.
    response = get_session().get(page_url)

    # Process the HTML using BeautifulSoup!
    soup = BeautifulSoup(response.content, "html.parser")

    items = []

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

        # RSS requires absolute links; NHL serves these as site-relative paths.
        assert isinstance(link, str)
        link = urljoin(BASE_URL, link)

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

        # Some cards have neither a heading nor an image to title them.
        if header and header.string:
            title = header.string
        elif image and image.get("alt"):
            title = str(image["alt"])
        else:
            logger.error(f"No article title found for {link}")
            continue

        time = article.find("time")
        if time:
            pubdate = datetime.fromisoformat(str(time["datetime"]))
        else:
            pubdate = None

        items.append(
            {
                "title": title,
                "link": link,
                "description": description,
                "pubdate": pubdate,
                "enclosure": enclosure,
            }
        )

    if len(items) == 0:
        logger.error(f"Found no articles on {page_url}")

    return items


def _build_feed(name: str, page_url: str, items: list[dict]) -> str:
    feed = RssFeed(name, page_url, name)

    # Interleave the items from both pages.
    for item in sorted(
        items, key=lambda item: item.get("pubdate", datetime.min), reverse=True
    ):
        feed.add_item(**item)

    if len(feed.items) == 0:
        logger.error(f"Created empty feed for {page_url}")

    return feed.writeString("utf-8")


def nhl_news() -> str:
    page_url = f"{BASE_URL}/news/"
    items = _fetch_items(page_url)
    previews = _fetch_items(PREVIEWS_URL)

    return _build_feed("NHL Headlines", page_url, items + previews)


def team_news(team: str) -> str:
    if team == "fr-canadiens":
        url = "fr/canadiens"
    else:
        url = team

    page_url = f"{BASE_URL}/{url}/news/"
    items = _fetch_items(page_url)
    previews = _fetch_items(PREVIEWS_URL)

    # Filter the game previews to only this team.
    slug = TEAM_SLUGS[team]
    previews = [item for item in previews if slug in item["link"]]

    return _build_feed(f"{VALID_TEAMS[team]} News", page_url, items + previews)


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
