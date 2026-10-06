from collections.abc import Generator
from xml.etree import ElementTree

import pytest

from tests import assert_items_exists
from to_rss.nhl import TEAM_SLUGS, VALID_TEAMS, nhl_news, team_news


def _get_links(contents: str) -> Generator[str]:
    items = ElementTree.fromstring(contents).findall(".//item")
    for item in items:
        link = item.find("link")
        if link is not None:
            yield link.text or ""


@pytest.mark.parametrize("team_name", VALID_TEAMS.keys())
def test_nhl_team(team_name):
    result = team_news(team_name)
    assert_items_exists(result)

    # Each team feeds picks up the previews of its own games.
    links = _get_links(team_news(team_name))
    assert any("game-preview" in link for link in links)

    # Each team feed only includes a preview for its own games.
    assert all(
        TEAM_SLUGS[team_name] in link for link in links if "game-preview" in link
    )


def test_nhl_news():
    result = nhl_news()
    assert_items_exists(result)

    # The game preview articles dropped from nhl.com's main feed are merged in.
    links = _get_links(result)
    assert any("game-preview" in link for link in links)
