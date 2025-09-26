from typing import Any

from feedgenerator import Rss201rev2Feed
from feedgenerator.django.utils.encoding import iri_to_uri
from feedgenerator.django.utils.xmlutils import SimplerXMLGenerator


class ImageEnclosure:
    """Represents an RSS image enclosure."""

    def __init__(
        self,
        url: str,
        mime_type: str,
        width: int | None = None,
        height: int | None = None,
        description: str | None = None,
    ):
        self.mime_type = mime_type
        self.url = iri_to_uri(url)
        self.width = width
        self.height = height
        self.description = description


class RssFeed(Rss201rev2Feed):
    """
    Fixes some oddities in the standard feedgenerator.Rss201rev2Feed.
    """

    def add_item_elements(self, handler: SimplerXMLGenerator, item: Any) -> None:
        enclosure = item["enclosure"]

        # Remove the enclosure, it will be added manually.
        item["enclosure"] = None

        # Call the super method, more will be added afterward.
        super().add_item_elements(handler, item)

        # Enclosure without a length.
        if enclosure is not None:
            attrs = {"url": enclosure.url, "type": enclosure.mime_type}
            if enclosure.width and enclosure.height:
                attrs["width"] = str(enclosure.width)
                attrs["height"] = str(enclosure.height)
            if enclosure.description:
                attrs["description"] = enclosure.description
            handler.addQuickElement("enclosure", "", attrs)

        item["enclosure"] = enclosure
