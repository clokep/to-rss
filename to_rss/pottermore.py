import json

import feedgenerator

import iso8601

import requests

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

    response = requests.post(
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
    feed = feedgenerator.Rss201rev2Feed(name, BASE_URL + "/" + tag, description)

    # Get all of the items, then reach into the JSON to get each post.
    data = get_items(tag)
    for post in data["data"]["content"]["results"]:
        body = json.loads(post["body"])

        # The actual text must be rebuilt from the multiple sections.
        description = body.get("intro", "")
        for section in body["section"]:
            if section["contentTypeId"] == "textSection":
                # TODO This seems to be reStructuredText.
                description += section["text"]

            elif section["contentTypeId"] == "image":
                # TODO Add a link to the image.
                # Useful properties: imageAltText,
                # section['image']['file']['details'] has height/width and size.
                # section['image']['file']['url']
                pass

        # The image at the top of the page.
        main_image = body["mainImage"]["image"]["file"]

        feed.add_item(
            title=body["displayTitle"],
            link=BASE_URL + "/" + url + "/" + body["externalId"],
            author_name=body["author"]["title"],
            description=description,
            pubdate=iso8601.parse_date(body["publishDate"]),
            unique_id=post["id"],
            categories=[t["name"] for t in body["tags"]],
            updateddate=iso8601.parse_date(body["_updatedAt"]),
            enclosures=[
                feedgenerator.Enclosure(
                    "https:" + main_image["url"],
                    main_image["details"]["size"],
                    main_image["contentType"],
                ),
            ],
        )

    return feed.writeString("utf-8")
