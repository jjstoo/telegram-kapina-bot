#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
from concurrent.futures import ThreadPoolExecutor
import sys
import re

from TelegramUtils import TelegramHttpsAPI, Message
from KapinaCam import KapinaCam
from UntappdCrawler import Untappd

"""
User configuration happens here
"""
# Snapshot filename
snapshot_output_file = "snapshot.jpg"

# Command triggers
triggers = {"image": "/kapina",
            "help": "/help",
            "beers": "/hana"}

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
    help_text = "Get a snapshot by sending %s" % triggers["image"]

    api.send_message(Message(chat_id=message.chat_id,
                             reply_to=message.message_id,
                             text=help_text))


def handle_beers(message: Message):
    beers = untappd.get_beers_on_list("hana")
    msg = ""

    for beer in beers:
        msg += str(beer) + "\n"
        msg += "   \n"

    if msg == "":
        msg = "Beer data not yet updated"

    api.send_message(Message(chat_id=message.chat_id,
                             reply_to=message.message_id,
                             parse_mode="Markdown",
                             text=msg))


def build_beer_lists():
    untappd.set_beer_lists({"hana": "https://untappd.com/v/pub-kultainen-apina/17995?ng_menu_id=5035026b-1470-48c7-b82a-bf1df18f5889"})


def main():
    build_beer_lists()
    untappd.start()
    while True:
        try:
            messages = api.get_messages()
            for message in messages:
                text = message.text.lower()
                cmd_arr = re.split(r"[@ ]", text)
                if triggers["image"] in cmd_arr:
                    tpe.submit(handle_image_request, message)
                elif triggers["help"] in cmd_arr:
                    tpe.submit(handle_help, message)
                elif triggers["beers"] in cmd_arr:
                    tpe.submit(handle_beers, message)
        except Exception as e:
            print(e)
            continue


main()
