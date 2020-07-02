from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from bs4 import BeautifulSoup

from Networking import NetworkHandler

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
        self.net = NetworkHandler()
        self.net.set_random_proxy()

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
        beer_futures = []
        try:
            data = self.net.https_get(self.beer_lists[list][0], headers=common_header).text
            soup = BeautifulSoup(data, features="html5lib")
            raw_beer_list = soup.find("ul", {"class": "menu-section-list"})
            for beer in raw_beer_list.find_all("li"):
                beer_futures.append(
                    tpe.submit(self.get_beer, UntappdCrawler.BASE_URL + beer.find("a", href=True)["href"]))

            for future in beer_futures:
                result = future.result()
                if result is not None:
                    beers.append(result)

            return beers

        except Exception as e:
            print("Connection to untappd failed, resetting proxy")
            self.net.set_random_proxy()
            return None

    def get_beer(self, url: str):
        try:
            data = self.net.https_get(url, headers=common_header).text
            soup = BeautifulSoup(data, features="html5lib")

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
        except Exception:
            raise ConnectionError


if __name__ == "__main__":
    untappd = UntappdCrawler()
    untappd.set_beer_lists({"hana":
        [
            "https://untappd.com/v/pub-kultainen-apina/17995?ng_menu_id=5035026b-1470-48c7-b82a-bf1df18f5889",
            "section-menu-list-146318694"]})

    untappd.set_default_beer_list("hana")
    beers = untappd.get_beers_on_list("hana")

    for beer in beers:
        print(beer.name)
