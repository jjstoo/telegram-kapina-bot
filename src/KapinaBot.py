#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
import sys
import re

from conf import *
from TelegramUtils import TelegramHttpsAPI, Message
from KapinaCam import KapinaCam
from UntappdUtils import Untappd
from DrinkTrackerUtils import DrinkTracker

"""
Initialization
"""
try:
    with open("assets/token", "r") as file:
        TOKEN = file.read().replace("\n", "")
except OSError:
    print("Token file not found")
    sys.exit(1)

snapshot_sem = threading.Semaphore(1)
api = TelegramHttpsAPI(TOKEN)
cam = KapinaCam(snapshot_sem, snapshot_output_file)
stats = DrinkTracker()
drink_triggers = stats.get_drink_cmds()
untappd = Untappd(5)
tpe = ThreadPoolExecutor(max_workers=pool_size)


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


def handle_help_request(message: Message):
    """
    Replies to the given message with a help text
    :param message: Message to reply to
    :return: None
    """
    help_text = "*Get a snapshot of kapina:*\n" \
                "{}\n" \
                "*Log your drinks by sending:*\n" \
                "{}\n" \
                "*List your drinking records with:* \n" \
                "{} (+ \"total\" for group records)\n" \
                "*Currently available kapina beer infos:* \n" \
                "{} \n" \
        .format(triggers["image"],
                "\n".join(drink_triggers.values()),
                triggers["drink_records"],
                "\n".join(beer_tap_triggers))

    api.send_message(Message(chat_id=message.chat_id,
                             reply_to=message.message_id,
                             parse_mode="Markdown",
                             text=help_text))


def handle_beer_tap_request(message: Message, list_name: str):
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


def handle_drink_request(message: Message, cmd_arr):
    print("Handling drink addition")
    special_message_sent = False
    username = message.username
    user_id = message.user_id

    if username is not None and user_id is not None:
        for trigger in drink_triggers:
            if drink_triggers[trigger] in cmd_arr:
                stats.add_drink(user_id, username, trigger)
                if stats.send_special_reply(api, message, trigger): special_message_sent = True

        if not special_message_sent:
            reply = "*Kippis!* Juomia pudoteltu {} kpl, joista {} on nautittu tänään".format(
                stats.get_total_drinks(telegram_id=user_id), stats.get_total_drinks_today(telegram_id=user_id))

            api.send_message(Message(chat_id=message.chat_id,
                                     reply_to=message.message_id,
                                     parse_mode="Markdown",
                                     text=reply))
    else:
        print("Username or id missing from drink command!")


def handle_drinking_records_request(message: Message, cmd_arr):
    print("Getting drink stats")

    total = False
    extra_argument_idx = cmd_arr.index(triggers["drink_records"]) + 1
    if len(cmd_arr) > extra_argument_idx:
        if cmd_arr[extra_argument_idx].lower() == "total":
            total = True

    records = {}

    if total:
        total = stats.get_total_drinks()
        for drink in drink_triggers:
            records[drink] = stats.get_total_drinks(drink_type=drink)
    else:
        total = stats.get_total_drinks(telegram_id=message.user_id)
        for drink in drink_triggers:
            records[drink] = stats.get_total_drinks(drink_type=drink, telegram_id=message.user_id)

    reply = [f"Yhteensä *{total}* kpl juomia juotu:"]

    print(reply)

    for drink in records:
        if records[drink] > 0:
            reply.append(f"- {drink}: {records[drink]} kpl")

    print(reply)

    api.send_message(Message(chat_id=message.chat_id,
                             reply_to=message.message_id,
                             parse_mode="Markdown",
                             text="\n".join(reply)))


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
                    tpe.submit(handle_help_request, message)
                if drink_cmd_found:
                    tpe.submit(handle_drink_request, message, cmd_arr)
                if triggers["drink_records"] in cmd_arr:
                    tpe.submit(handle_drinking_records_request, message, cmd_arr)
                if len(beer_list_cmds) > 0:
                    tpe.submit(handle_beer_tap_request, message, beer_list_cmds[0][1:])
        except Exception as e:
            print("Major oops")
            print(e)
            continue


main()
