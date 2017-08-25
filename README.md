## To RSS

This project aims to provide RSS feeds for platforms that should just provide
RSS feeds. It supports a few different endpoints:

Information is pulled on demand on each refresh of the page (and is always
current).

### Wikipedia Current Event

The last 7 days of
[Wikipedia Current Events](https://en.wikipedia.org/wiki/Portal:Current_events)
is served as an RSS feed.

It pulls data from the last 7 days of current events from Wikipedia, e.g. a page
like https://en.wikipedia.org/wiki/Portal:Current_events/2017_May_8. The
Wikicode is parsed using
[mwparserfromhell](http://mwparserfromhell.readthedocs.org/) to an AST which is
then cleaned-up slightly and converted back into HTML. Each day is served as an
individual article in RSS.

### NHL News

To my knowledge, [NHL.com](https://www.nhl.com/) does not provide an
RSS feed for their [news feed](https://www.nhl.com/news/). This is a simple
proxy that loads the NHL.com news site and serves it back as an RSS feed. You
can get an RSS feed for NHL news (at `/nhl/news/`) or for a specific team (e.g.
the New York Islanders news at `/nhl/islanders/`). The root (at `/nhl/`) lists
all possible feeds. Note that currently only article summaries are supported.

### Patreon

Patreon doesn't seem to provide an RSS feed for an individual user's posts, it
only emails out updates. This provides a way to see those over RSS.

### About

It is a Flask application that serves RSS feeds generated using
[FeedGenerator](https://github.com/getpelican/feedgenerator). Generally
information is pulled using requests and parsed with BeautifulSoup4.
