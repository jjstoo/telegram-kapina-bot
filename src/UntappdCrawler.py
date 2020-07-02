from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from bs4 import BeautifulSoup

from Networking import https_get

# We'll have to fake being a real user, otherwise Untappd blocks the requests
common_header = {
    'User-Agent': 'Mozilla/5.0'
}

tpe = ThreadPoolExecutor(max_workers=10)


class Beer:
    def __init__(self,
                 name,
                 abv,
                 rating,
                 style,
                 img):
        self.name = name
        self.abv = abv
        self.rating = rating
        self.style = style
        self.img = img


class UntappdCrawler:
    BASE_URL = "https://untappd.com"

    def __init__(self):
        self.beer_lists = {}
        self.default_beer_list = None

    def set_beer_lists(self, lists: Dict):
        """
        Sets the available beers lists
        :param lists: Dict["List name": ["List URL", "List HTML element ID"]]
        :return: None
        """
        self.beer_lists = lists

    def set_default_beer_list(self, list: str) -> bool:
        """
        Sets the default beer list for queries
        :param list: Default list name
        :return: True if the list is found from the available beer lists
        """
        if list in self.beer_lists:
            self.default_beer_list = list
            return True
        else:
            return False

    def get_beers_on_list(self, list: str = None):

        raw_beer_entries = []

        data = https_get(self.beer_lists[list][0], headers=common_header).text
        soup = BeautifulSoup(data)
        raw_beer_list = soup.find(id=self.beer_lists[list][1])
        for beer in raw_beer_list.find_all("li"):
            tpe.submit(self.get_beer, UntappdCrawler.BASE_URL + beer.find("a", href=True)["href"])

    def get_beer(self, url: str):
        data = https_get(url, headers=common_header).text
        soup = BeautifulSoup(data)

        basic_info = soup.find("div", {"class": "name"})
        name = basic_info.find("h1").text
        print(name)
