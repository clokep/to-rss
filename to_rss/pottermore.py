import json
import logging

import iso8601
import markdown

from to_rss import get_session
from to_rss.rss import ImageEnclosure, RssFeed

logger = logging.getLogger(__name__)

BASE_URL = "https://www.wizardingworld.com"
API_URL = "https://api.wizardingworld.com/v3"


def get_items(tag):
    """Use the Wizarding World API to get recent news posts."""
    body = {
        "operationName": "ContentQuery",
        "variables": {
            "tags": tag,
            "count": 15,
            "excludeTags": ["hide-from-web"],
        },
        "query": "query ContentQuery($contentTypes: [String!], $count: Int, $offset: Int, $tags: [String!], $excludeTags: [String!], $externalId: String) {\n  content(contentTypes: $contentTypes, count: $count, offset: $offset, tags: $tags, excludeTags: $excludeTags, externalId: $externalId) {\n    results {\n      id\n      body\n      contentTypeId\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa: E501
    }

    response = get_session().post(
        API_URL,
        json=body,
        headers={
            "Authorization": "none",
            "Content-Type": "application/json",
        },
    )
    response.raise_for_status()

    return response.json()


def pottermore_page(tag, url, name, description):
    """Get a list of articles for a section of the Wizarding World site."""
    # Create the output feed.
    feed = RssFeed(name, BASE_URL + "/" + tag, description)

    # Get all of the items, then reach into the JSON to get each post.
    data = get_items(tag)
    for post in data["data"]["content"]["results"]:
        body = json.loads(post["body"])
        title = body["displayTitle"]

        # The actual text must be rebuilt from the multiple sections.
        description = body.get("intro", "")
        for section in body["section"]:
            section_type = section["contentTypeId"]

            if section_type == "textSection":
                description += section["text"]

            elif section_type == "image":
                # Add the image on a separate line.
                image = section["image"]
                alt = image.get("description") or image["title"]
                description += (
                    f'<img src="https:{image["file"]["url"]}" alt="{alt}"></a>'
                )

            elif section_type == "video":
                # Add the preview image.
                image = section["mainImage"]["image"]
                alt = section["displayTitle"]
                description += (
                    f'<img src="https:{image["file"]["url"]}" alt="{alt}"></a>'
                )

            elif section_type == "excerpt":
                description += (
                    f'**{section["excerptURLTitle"]}**\n> {section["excerptText"]}'
                )

            elif section_type == "quote":
                section_title = section.get("quoteAttributionTitle") or section.get(
                    "quoteAttribution"
                )
                if section_title:
                    description += f'**{section_title}**\n> {section["quoteText"]}'
                else:
                    description += f'\n> {section["quoteText"]}'
            else:
                logger.error(
                    "Unknown section type: %s via %s / %s",
                    section_type,
                    url,
                    title,
                )

            description += "\n\n"

        # The image at the top of the page.
        main_image = body["mainImage"]
        image_file = main_image["image"]["file"]
        image_details = image_file["details"]["image"]
        description = main_image.get("imageAltText") or main_image["image"]["title"]

        feed.add_item(
            title=title,
            link=BASE_URL + "/" + url + "/" + body["externalId"],
            author_name=body["author"]["title"],
            description=markdown.markdown(description),
            pubdate=iso8601.parse_date(body["publishDate"]),
            unique_id=post["id"],
            categories=[t["name"] for t in body["tags"]],
            updateddate=iso8601.parse_date(body["_updatedAt"]),
            enclosure=ImageEnclosure(
                url="https:" + image_file["url"],
                mime_type=image_file["contentType"],
                width=image_details["width"],
                height=image_details["height"],
                description=description,
            ),
        )

    return feed.writeString("utf-8")
