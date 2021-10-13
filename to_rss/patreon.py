from contextlib import contextmanager
from datetime import datetime
from os import environ

import feedgenerator

import selenium
from selenium import webdriver

# This is lame.
if "Apple" not in environ.get("TERM_PROGRAM", ""):
    from pyvirtualdisplay import Display
else:

    @contextmanager
    def Display():
        yield


PATREON_URL = "https://www.patreon.com/{}"


def get_first_child(element, tag="div"):
    return element.find_elements_by_tag_name(tag)[0]


def patreon_posts(user):
    patreon_user_url = PATREON_URL.format(user)

    with Display():
        # Start Firefox and it will run inside the virtual display.
        driver = webdriver.Firefox()

        # Make sure we always clean up at the end.
        try:
            driver.get(patreon_user_url)

            element = driver.find_element_by_tag_name("h1")
            feed_title = element.text
            # Find a h1, followed by a span.
            feed_description = (
                feed_title
                + " "
                + driver.find_element_by_xpath("//h1/following-sibling::span").text
            )

            feed = feedgenerator.Rss201rev2Feed(
                title=feed_title, link=patreon_user_url, description=feed_description
            )

            posts = driver.find_elements_by_css_selector('div[data-tag="post-card"]')

            for post in posts:
                print(post)
                element = post.find_element_by_css_selector(
                    'a[data-tag="post-published-at"'
                )
                link = element.get_attribute("href")
                date = datetime.strptime(element.text, "%b %d, %Y AT %I:%M %p")

                title = post.find_element_by_css_selector(
                    'span[data-tag="post-title"]'
                ).text
                try:
                    container = post.find_element_by_css_selector(
                        'div[data-tag="post-content-collapse"]'
                    )
                    description_el = get_first_child(
                        get_first_child(get_first_child(get_first_child(container)))
                    )
                    description = description_el.get_attribute("innerHTML")
                except selenium.common.exceptions.NoSuchElementException:
                    # No description.
                    description = ""

                # TODO Handle media.

                feed.add_item(
                    title=title,
                    link=link,
                    description=description,
                    author_name=feed_title,
                    author_link=patreon_user_url,
                    pubdate=date,
                )

        finally:
            driver.quit()

    return feed.writeString("utf-8")
