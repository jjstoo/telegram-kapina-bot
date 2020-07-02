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
                 brewery,
                 abv,
                 rating,
                 ratings,
                 style,
                 img):
        self.name = name
        self.brewery = brewery
        self.abv = abv
        self.rating = rating
        self.ratings = ratings
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

        beers = []
        raw_beer_list = []
        beer_futures = []

        data = https_get(self.beer_lists[list][0], headers=common_header).text
        soup = BeautifulSoup(data)
        print(soup)
        raw_beer_list = soup.find(id=self.beer_lists[list][1])
        for beer in raw_beer_list.find_all("li"):
            beer_futures.append(tpe.submit(self.get_beer, UntappdCrawler.BASE_URL + beer.find("a", href=True)["href"]))

        for future in beer_futures:
            result = future.result()
            if result:
                beers.append(result)

    def get_beer(self, url: str):
        try:
            data = https_get(url, headers=common_header).text
            soup = BeautifulSoup(data)

            basic_info = soup.find("div", {"class": "name"})
            name = basic_info.find("h1").text
            brewery = basic_info.find("p", {"class": "brewery"}).find("a").text
            style = basic_info.find("p", {"class": "style"}).text
            img = soup.find("a", {"class": "label"}).find("img")["src"]

            details = soup.find("div", {"class": "details"})
            abv = details.find("p", {"class": "abv"}).text
            rating = details.find("div", {"class": "caps"})["data-rating"]
            ratings = details.find("p", {"class": "raters"}).text

            return Beer(name=name,
                        brewery=brewery,
                        rating=float(rating),
                        ratings=ratings,
                        abv=abv,
                        style=style,
                        img=img)
        except Exception as e:
            return None
