from bs4 import BeautifulSoup

import feedgenerator

from to_rss import session

BASE_URL = 'https://www.theplayerstribune.com'

VALID_SPORTS = {
    'soccer': 'Soccer',
    'basketball': 'Basketball',
    'hockey': 'Hockey',
    'baseball': 'Baseball',
    'football': 'Football',
    'more': 'More Sports',
}


def sports_news(sport):
    # Get the HTML page.
    page_url = BASE_URL + '/global/sports/' + sport
    response = session.get(page_url)

    # Process the HTML using BeautifulSoup!
    soup = BeautifulSoup(response.content, 'html.parser')

    # Get the human name.
    name = VALID_SPORTS[sport]

    feed = feedgenerator.Rss201rev2Feed(name, page_url, name)

    # Iterate over each article.
    for article in soup.find_all('article'):
        children = list(article.children)

        # Most of the info we need is in the 3rd element.
        elements = list(children[2].children)

        # Get the author element, and pull out the name (and maybe a link).
        authors = list(elements[0].find_all('a'))
        # There's one or more authors. If there are multiple, don't provide a link.
        if len(authors) > 1:
            author_name = ', '.join(a.contents[0] for a in authors)
            author_link = None
        else:
            author_name = str(authors[0].contents[0])
            author_link = BASE_URL + authors[0]['href']

        # Get the article title (and URL).
        title = elements[1]

        # Get the brief description.
        excerpt = elements[2]

        feed.add_item(title=str(title.contents[0]),
                      link=BASE_URL + title['href'],
                      description=str(excerpt.contents[0]),
                      author_name=author_name,
                      author_link=author_link)

    return feed.writeString('utf-8')
