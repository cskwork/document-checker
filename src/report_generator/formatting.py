"""Retain inert report formatting without trusting document-supplied HTML."""
from html import escape
from html.parser import HTMLParser
from markupsafe import Markup
import logging


class _FormattingParser(HTMLParser):
    tags = {"b", "strong", "i", "em", "u", "s", "mark", "code", "pre",
            "span", "p", "br", "ul", "ol", "li", "blockquote", "sup", "sub"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.stack = []
        self.open_counts = {}

    def handle_starttag(self, tag, attrs):
        if tag not in self.tags:
            self.parts.append(escape(self.get_starttag_text()))
            return
        attribute = ""
        if tag == "span" and "highlight" in (dict(attrs).get("class") or "").split():
            attribute = ' class="highlight"'
        self.parts.append(f"<{tag}{attribute}>")
        if tag != "br":
            self.stack.append(tag)
            self.open_counts[tag] = self.open_counts.get(tag, 0) + 1

    def handle_endtag(self, tag):
        if tag not in self.tags:
            self.parts.append(escape(f"</{tag}>"))
        elif self.open_counts.get(tag, 0):
            while self.stack:
                closing = self.stack.pop()
                self.open_counts[closing] -= 1
                self.parts.append(f"</{closing}>")
                if closing == tag:
                    break

    def handle_startendtag(self, tag, attrs):
        if tag not in self.tags:
            self.parts.append(escape(self.get_starttag_text()))
            return
        self.handle_starttag(tag, attrs)
        if tag != "br":
            self.handle_endtag(tag)

    def handle_data(self, data):
        self.parts.append(escape(data))


def report_markup(value):
    parser = _FormattingParser()
    text = str(value)
    try:
        parser.feed(text)
        parser.close()
    except (AssertionError, ValueError, NotImplementedError):
        logging.getLogger(__name__).warning("Invalid report formatting; rendering as text")
        return Markup(escape(text))
    while parser.stack:
        parser.parts.append(f"</{parser.stack.pop()}>")
    return Markup("".join(parser.parts))
