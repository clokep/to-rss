import iso8601
from bs4 import BeautifulSoup

from to_rss import get_session
from to_rss.rss import ImageEnclosure, RssFeed

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
    "coyotes": "Arizona Coyotes",
    "blackhawks": "Chicago Blackhawks",
    "avalanche": "Colorado Avalanche",
    "stars": "Dallas Stars",
    "wild": "Minnesota Wild",
    "predators": "Nashville Predators",
    "blues": "St. Louis Blues",
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


def _size_from_url(image_url):
    """Returns the width and height of the image, parsed from the URL."""
    # The URL is like https://.../.../640x360/foo.jpg
    try:
        return image_url.split("/")[-2].split("x")
    except ValueError:
        return None, None


def _get_news(name, page_url):
    # Get the HTML page.
    response = get_session().get(page_url)

    # Process the HTML using BeautifulSoup!
    soup = BeautifulSoup(response.content, "html.parser")

    feed = RssFeed(name, page_url, name)

    # Iterate over each article.
    for article in soup.find_all("article", class_="article-item"):
        # Get the author element, and pull out the name (and maybe a link).
        author = article.find_all(class_="article-item__contributor")[0]
        author_name = author.contents[0].strip().lstrip("by").strip()
        if author.a:
            author_link = author.a["href"]
        else:
            author_link = None

        # Get the date element and parse it to a datetime.
        date = article.find_all(class_="article-item__date")[0]

        # The content is split into two pieces that must be re-assembled.
        preview = article.find_all("div", class_="article-item__preview")[0]
        # Note that the full body isn't available, it could be grabbed from the
        # data-url though!

        # Find an image from the video preview.
        image_container = article.find_all("div", class_="article-item__img-container")
        image = None
        if len(image_container) > 0:
            image = image_container[0].find_all("img")[0]
            image_url = image.get("data-srcset")
            if image_url:
                image_url = image_url.split(" ")[0]
            else:
                image_url = image.get("data-src")
                if not image_url:
                    image_url = image["src"]
            width, height = _size_from_url(image_url)
            if image_url.startswith("//"):
                image_url = "https:" + image_url

            image = ImageEnclosure(
                url=image_url, mime_type="image/jpg", width=width, height=height
            )

        feed.add_item(
            title=str(article.h1.string),
            link=BASE_URL + article["data-url"],
            description=str(preview),
            author_name=author_name,
            author_link=author_link,
            pubdate=iso8601.parse_date(date["data-date"]),
            enclosure=image,
        )

    return feed.writeString("utf-8")


def nhl_news():
    return _get_news("NHL Headlines", f"{BASE_URL}/news/")


def team_news(team):
    if team == "fr-canadiens":
        url = "fr/canadiens"
    else:
        url = team

    return _get_news(f"{VALID_TEAMS[team]} News", f"{BASE_URL}/{url}/news/")
