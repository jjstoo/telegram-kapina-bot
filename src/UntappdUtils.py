#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
README

Untappd uses many methods to block web scraping. Due to these measures, this class program utilizes a pool of
random proxies to avoid being IP blocked from the site. This considerably slows down the update process, so updates are run
periodically in the background.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Semaphore, Thread
from time import sleep
from typing import Dict, List
from bs4 import BeautifulSoup
import requests

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
                 img=None,
                 url=None):
        self.name = name
        self.brewery = brewery
        self.abv = abv
        self.rating = rating
        self.ratings = ratings
        self.style = style
        self.img = img
        self.url = url

    def __bool__(self):
        return all([self.name,
                    self.brewery,
                    self.abv,
                    self.rating,
                    self.ratings,
                    self.style])

    def __str__(self):
        return "[{}]({}) ({}) - {}, {}\n*{:.2f}/5*".format(self.name, self.url, self.style, self.brewery, self.abv, self.rating)


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
        :param lists: Dict["List name": "List URL"]
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

    def get_beers_on_list(self, list: str = None, tries=3):
        """
        Returns the updated beers on a given list
        :param list: List name
        :param tries: Download attempts
        :return: None if failed
        """

        if tries == 0:
            return None

        beers = []
        beer_futures = []
        try:
            data = self.net.https_get(self.beer_lists[list], headers=common_header).text
            soup = BeautifulSoup(data, features="html5lib")
            raw_beer_list = soup.find("ul", {"class": "menu-section-list"})
            for beer in raw_beer_list.find_all("li"):
                beer_futures.append(
                    tpe.submit(self.get_beer, UntappdCrawler.BASE_URL + beer.find("a", href=True)["href"]))

            for i, future in enumerate(beer_futures):
                result = future.result()
                if result is not None:
                    beers.append(result)

            return beers

        except requests.exceptions.ProxyError:
            print("Proxy connection error when getting menu! Retrying")
            self.net.set_random_proxy()
            return self.get_beers_on_list(list, tries - 1)

        except Exception as e:
            print(str(e) + "while getting venue data! Retrying")
            return self.get_beers_on_list(list, tries - 1)

    def get_beer(self, url: str, tries=3):
        """
        Constructs a beer object from given Untappd beer URL
        :param url: Ber URL
        :param tries: Max attempts
        :return: None if failed
        """

        if tries == 0:
            return None

        try:
            data = self.net.https_get(url, headers=common_header).text
            soup = BeautifulSoup(data, features="html5lib")

            basic_info = soup.find("div", {"class": "name"})
            name = basic_info.find("h1").text
            brewery = basic_info.find("p", {"class": "brewery"}).find("a").text
            style = basic_info.find("p", {"class": "style"}).text
            img = soup.find("a", {"class": "label"}).find("img")["src"]

            details = soup.find("div", {"class": "details"})
            abv = details.find("p", {"class": "abv"}).text.strip()
            rating = details.find("div", {"class": "caps"})["data-rating"]
            ratings = details.find("p", {"class": "raters"}).text

            return Beer(name=name,
                        brewery=brewery,
                        rating=float(rating),
                        ratings=ratings,
                        abv=abv,
                        style=style,
                        img=img,
                        url=url)

        except requests.exceptions.ConnectTimeout:
            print("Connection timed out! Trying again")
            return self.get_beer(url, tries - 1)

        except requests.exceptions.ProxyError:
            print("Proxy connection error when getting beer data! Finding another one")
            self.net.set_random_proxy()
            return self.get_beer(url, tries - 1)

        except Exception as e:
            print("Error getting beer data" + e)
            return None


class Untappd:
    def __init__(self,
                 poll_interval):
        """
        Initializes the class for specific poll interval
        :param poll_interval: Poll interval
        """
        self.poll_interval = poll_interval
        self.stopped = False

        self.crawler = UntappdCrawler()
        self.lists = []
        self.beer_model = {}
        self.beer_model_sem = Semaphore(1)

    def set_beer_lists(self, lists: Dict):
        """
        Setup beer lists
        :param lists: Dictionary containing the list names and URL's
        :return: None
        """
        self.crawler.set_beer_lists(lists)
        for key in lists:
            self.lists.append(key)

    def update(self):
        """
        Updates all beer lists
        :return: None
        """
        print("Updating beer model")
        failure = False
        for list in self.lists:
            new_model = self.crawler.get_beers_on_list(list)
            if new_model is not None:
                with self.beer_model_sem:
                    self.beer_model[list] = new_model
            else:
                failure = True

        print("Beer model update complete with errors!" if failure else "Beer model update complete!")

    def get_beers_on_list(self, list) -> List[Beer]:
        """
        Returns beers on given list
        :param list: Beer list
        :return: List of beers, empty list if not found
        """
        with self.beer_model_sem:
            if list in self.beer_model:
                return self.beer_model[list]
            else:
                return []

    def poll(self):
        """
        Updates the lists periodically
        :return: None
        """
        self.stopped = False
        while not self.stopped:
            self.update()
            sleep(60 * self.poll_interval)

    def start(self):
        """
        Starts polling
        :return: None
        """
        Thread(target=self.poll).start()

    def stop(self):
        """
        Stops polling
        :return: None
        """
        self.stopped = True


if __name__ == "__main__":
    untappd = Untappd(5)
    untappd.set_beer_lists(
        {"hana": "https://untappd.com/v/pub-kultainen-apina/17995?ng_menu_id=5035026b-1470-48c7-b82a-bf1df18f5889"})
    untappd.start()
    beers = untappd.get_beers_on_list("hana")

    for beer in beers:
        if beer:
            print(beer.name)
