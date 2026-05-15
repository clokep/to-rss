import logging

from bs4 import BeautifulSoup, Tag

from to_rss import get_session
from to_rss.rss import ImageEnclosure, RssFeed

logger = logging.getLogger(__name__)

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
        if link is None:
            logger.error("No URL found")
            continue
        assert isinstance(link, Tag)

        # The image is in the first element, within a noscript tag.
        noscript = article.find("noscript")
        if noscript is None:
            logger.error("No noscript found")
            continue
        picture = noscript.contents[0]
        if picture is None:
            logger.error("No picture found")
            continue
        assert isinstance(picture, Tag)
        img = picture.contents[3]
        assert isinstance(img, Tag)
        image = ImageEnclosure(url=str(img["src"]), mime_type="image/jpg")

        # Most of the info we need is in the 3rd element.
        temp_elements = link.contents[2]
        assert isinstance(temp_elements, Tag)
        elements = temp_elements.contents
        assert isinstance(elements[0], Tag)

        # Get the article title.
        title_el = elements[0].contents[0]
        assert isinstance(title_el, Tag)
        title = title_el.string

        # Get the brief description.
        excerpt_el = elements[0].contents[1]
        assert isinstance(excerpt_el, Tag)
        excerpt = excerpt_el.string

        # Get the author element, and pull out the name (and maybe a link).
        if len(elements) > 1:
            assert isinstance(elements[1], Tag)
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
