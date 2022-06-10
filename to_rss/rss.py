from feedgenerator import Rss201rev2Feed
from feedgenerator.django.utils.encoding import iri_to_uri


class ImageEnclosure:
    "Represents an RSS enclosure"

    def __init__(self, url, mime_type, width=None, height=None, description=None):
        self.mime_type = mime_type
        self.url = iri_to_uri(url)
        self.width = width
        self.height = height
        self.description = description


class RssFeed(Rss201rev2Feed):
    """
    Fixes some oddities in the standard feedgnerator.Rss201rev2Feed.
    """

    def add_item_elements(self, handler, item):
        enclosure = item["enclosure"]

        # Remove the enclosure, it will be added manually.
        item["enclosure"] = None

        #
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
