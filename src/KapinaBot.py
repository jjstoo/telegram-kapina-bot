#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
import sys
import re

from TelegramUtils import TelegramHttpsAPI, Message
from KapinaCam import KapinaCam
from UntappdUtils import Untappd
from DrinkTrackerUtils import DrinkTracker

"""
User configuration happens here
"""
# Snapshot filename
snapshot_output_file = "snapshot.jpg"

# Command triggers
triggers = {"image": "/kapina",
            "help": "/help"}

drink_triggers = {"beer": "/kalja",
                  "booze": "/viina",
                  "wine": "/viini"}
beer_tap_triggers = []

# Thread pool size for smooth handling of multiple requests
pool_size = 10

"""
Initialization
"""
try:
    with open("token", "r") as file:
        TOKEN = file.read().replace("\n", "")
except OSError:
    print("Token file not found")
    sys.exit(1)

snapshot_sem = threading.Semaphore(1)
api = TelegramHttpsAPI(TOKEN)
cam = KapinaCam(snapshot_sem, snapshot_output_file)
stats = DrinkTracker()
tpe = ThreadPoolExecutor(max_workers=pool_size)
untappd = Untappd(5)


def handle_image_request(message: Message):
    """
    Replies to the given message with a snapshot
    :param message: Message to reply to
    :return: None
    """
    cam.snapshot()
    with snapshot_sem:
        api.send_message(Message(chat_id=message.chat_id,
                                 reply_to=message.message_id,
                                 photo=snapshot_output_file))


def handle_help(message: Message):
    """
    Replies to the given message with a help text
    :param message: Message to reply to
    :return: None
    """
    help_text = "Get a snapshot by sending {}\n" \
                "Currently available beer listings:\n" \
                "{}".format(triggers["image"], beer_tap_triggers)

    api.send_message(Message(chat_id=message.chat_id,
                             reply_to=message.message_id,
                             text=help_text))


def handle_beers(message: Message, list_name: str):
    """
    Replies to the given message with beer tap listing
    :param message: Mssage to reply to
    :param list_name: 
    :return: None
    """
    beers = untappd.get_beers_on_list(list_name)
    msg = ""

    for beer in beers:
        msg += str(beer) + "\n"
        msg += "   \n"

    if msg == "":
        msg = "Beer data not yet updated"

    api.send_message(Message(chat_id=message.chat_id,
                             reply_to=message.message_id,
                             parse_mode="Markdown",
                             disable_web_page_preview=True,
                             text=msg))


def handle_drink(message: Message, cmd_arr):

    print("Handling drink addition")

    username = message.username
    user_id = message.user_id

    if username is not None and user_id is not None:
        if drink_triggers["beer"] in cmd_arr:
            stats.add_drink(user_id, username, drink_triggers["beer"][1:])
        if drink_triggers["booze"] in cmd_arr:
            stats.add_drink(user_id, username, drink_triggers["booze"][1:])
        if drink_triggers["wine"] in cmd_arr:
            stats.add_drink(user_id, username, drink_triggers["wine"][1:])
    else:
        print("Username or id missing from drink command!")


def build_beer_lists(lists: Dict):
    """
    Initializes beer lists
    :return: None
    """
    untappd.set_beer_lists(lists)

    for list in lists:
        beer_tap_triggers.append("/" + list)


def main():
    build_beer_lists({"hana": "https://untappd.com/v/pub-kultainen-apina/17995?ng_menu_id=5035026b-1470-48c7"
                              "-b82a-bf1df18f5889"})
    untappd.start()
    while True:
        try:
            messages = api.get_messages()
            for message in messages:
                text = message.text.lower()
                cmd_arr = re.split(r"[@ ]", text)
                beer_list_cmds = [i for i in cmd_arr if i in beer_tap_triggers]
                drink_cmd_found = any([i for i in cmd_arr if i in drink_triggers.values()])
                if triggers["image"] in cmd_arr:
                    tpe.submit(handle_image_request, message)
                if triggers["help"] in cmd_arr:
                    tpe.submit(handle_help, message)
                if drink_cmd_found:
                    tpe.submit(handle_drink, message, cmd_arr)
                if len(beer_list_cmds) > 0:
                    tpe.submit(handle_beers, message, beer_list_cmds[0][1:])
        except Exception as e:
            print("Major oops")
            print(e)
            continue


main()
