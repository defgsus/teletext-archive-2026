import html
from typing import Dict, Generator, Tuple, Union, Optional, Any

import bs4

from ..scraper import Scraper
from ..teletext import Teletext, TeletextPage


class ORFBase(Scraper):

    ABSTRACT = True
    CHANNEL: Optional[str] = None
    HOST = "https://text.orf.at"
    BASE_URL = "/channel/{}/page/100/1.html"

    COLOR_CLASS_MAPPING = {
        "black": "b",
        "red": "r",
        "green": "g",
        "yellow": "y",
        "blue": "l",
        "magenta": "m",
        "cyan": "c",
        "white": "w",
    }

    def iter_pages(self) -> Generator[Tuple[int, int, bs4.BeautifulSoup], None, None]:
        url = self.BASE_URL.format(self.CHANNEL)

        while True:
            soup = self.get_soup(f"{self.HOST}{url}")

            menu = soup.find("div", {"class": "menu"})
            current_page_text = menu.find("span", {"class": "currentpage"})
            current_page_text = current_page_text.text.split()[-1]
            page, sub_page = current_page_text.split(".")
            yield int(page), int(sub_page), soup

            next_sub_page = menu.find("a", {"class": "ns"})
            if u := next_sub_page.attrs["href"]:
                url = u
                continue

            next_page = menu.find("a", {"class": "np"})
            if u := next_page.attrs["href"]:
                url = u
                continue
            else:
                break

    def to_teletext(self, soup: bs4.BeautifulSoup) -> TeletextPage:
        page = soup.find("div", {"id": "pagewrapper"})
        tt = TeletextPage()
        for line in page.find_all("div", {"class": "line"}):
            tt.new_line()
            for div in line.find_all("div", {"class": "run"}):
                length = int(div.attrs["data-length"])
                if not length:
                    continue

                text: str = html.unescape(div.text)
                # skip long aria text
                if div.find("span", {"class": "sr-only"}):
                    text = div.find("span", {"aria-hidden": "true"}).text
                # pad to data-length
                if length > len(text):
                    text = text.rjust(length)
                # use g1 code from data-charcode
                if cc := div.attrs.get("data-charcode"):
                    text = chr(TeletextPage.g1_to_unicode(int(cc[:2], 16)))

                try:
                    link = int(div.attrs["data-link"])
                except (ValueError, TypeError, KeyError):
                    link = None

                tt.add_block(TeletextPage.Block(
                    text=text,
                    color=self.COLOR_CLASS_MAPPING[div.attrs["data-fg"].lstrip("G")],
                    bg_color=self.COLOR_CLASS_MAPPING[div.attrs["data-bg"].lstrip("G")],
                    link=link,
                ))
        #print(tt.to_ndjson()); exit()
        return tt


class ORF1(ORFBase):
    NAME = "orf1"
    CHANNEL = "orf1"
    ABSTRACT = False


class ORF2(ORFBase):
    NAME = "orf2"
    CHANNEL = "orf2"
    ABSTRACT = False


class ORF3(ORFBase):
    NAME = "orf3"
    CHANNEL = "orfiii"
    ABSTRACT = False


class ORFSportPlus(ORFBase):
    NAME = "orfsportplus"
    CHANNEL = "sportplus"
    ABSTRACT = False
