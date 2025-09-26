from bs4 import BeautifulSoup

from to_rss import get_session
from to_rss.rss import ImageEnclosure, RssFeed

BASE_URL = "https://www.theplayerstribune.com"

VALID_SPORTS = {
    "soccer": "Soccer",
    "basketball": "Basketball",
    "hockey": "Hockey",
    "baseball": "Baseball",
    "football": "Football",
    "more": "More Sports",
}


def sports_news(sport: str) -> str:
    # Get the HTML page.
    page_url = BASE_URL + "/sports/" + sport
    response = get_session().get(page_url)

    # Process the HTML using BeautifulSoup!
    soup = BeautifulSoup(response.content, "html.parser")

    # Get the human name.
    name = VALID_SPORTS[sport]

    feed = RssFeed(name, page_url, name)

    # Iterate over each article.
    for article in soup.find_all("article"):
        link = article.contents[0]

        # The image is in the first element, within a noscript tag.
        picture = article.find("noscript").contents[0]
        img = picture.contents[3]
        image = ImageEnclosure(url=img["src"], mime_type="image/jpg")

        # Most of the info we need is in the 3rd element.
        elements = link.contents[2].contents

        # Get the article title.
        title = elements[0].contents[0].string

        # Get the brief description.
        excerpt = elements[0].contents[1].string

        # Get the author element, and pull out the name (and maybe a link).
        if len(elements) > 1:
            authors = elements[1].string
        else:
            authors = None

        feed.add_item(
            title=title,
            link=link["href"],
            description=excerpt,
            author_name=authors,
            enclosure=image,
        )

    return feed.writeString("utf-8")
