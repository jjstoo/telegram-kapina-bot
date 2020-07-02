import requests
import random
import time
from typing import Dict


class NetworkHandler:

    def __init__(self):

        self.proxies = None
        self.proxy_update = False

    def https_post(self, url: str, parameters: Dict = None, files: Dict = None) -> requests.Response:
        """
        Raw https post with optional parameters
        :param url: POST URL
        :param parameters: Parameters
        :param files: Multipart file data to send
        :return: None
        """
        return requests.post(url, parameters, files=files)

    def https_get(self, url: str, parameters: Dict = None, headers: Dict = None) -> requests.Response:
        """
        Raw https get with optional parameters
        :param url: GET URL
        :param parameters: Parameters
        :param headers: Header attributes
        :return: Requests GET object with return code and payload
        """
        return requests.get(url, params=parameters, headers=headers, proxies=self.proxies)

    def set_random_proxy(self):
        """
        Sets or updates the instance to use a random proxy
        :return: None
        """

        # Behold the worlds dumbest spinlock
        if self.proxy_update:
            while self.proxy_update:
                time.sleep(1)
            return

        self.proxy_update = True
        proxy_list_url = "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
        test_url = 'https://httpbin.org/ip'
        data = requests.get(proxy_list_url).text.split("\n")
        random.shuffle(data)

        for ip in data:
            print("Connecting to proxy at " + ip, end=" ... ")
            proxies = {
                "http": "http://" + ip,
                "https": "https://" + ip
            }

            try:
                response = requests.get(test_url, proxies=proxies, timeout=5).status_code
                if response == 200:
                    print("SUCCESS")
                    self.proxies = proxies
                    self.proxy_update = False
                    return
            except Exception as e:
                print("FAILED")

        print("No working proxy found")
        self.proxy_update = False


if __name__ == "__main__":
    net = NetworkHandler()
    net.set_random_proxy()
