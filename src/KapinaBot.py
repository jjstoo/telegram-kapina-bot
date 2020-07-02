#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import sys
import re

from TelegramUtils import TelegramHttpsAPI, Message
from KapinaCam import KapinaCam

"""
User configuration happens here
"""
# Snapshot filename
snapshot_output_file = "snapshot.jpg"

# Replace with your own command trigger for sending an image
triggers = {"image": "/kapina",
            "help": "/help"}

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
    help_text = "Get a snapshot by sending %s" % triggers["image"]

    api.send_message(Message(chat_id=message.chat_id,
                             reply_to=message.message_id,
                             text=help_text))


def main():
    while True:
        messages = api.get_messages()
        for message in messages:
            text = message.text.lower()
            cmd_arr = re.split(r"[@ ]", text)
            if triggers["image"] in cmd_arr:
                threading.Thread(target=handle_image_request, args=(message,)).start()
            elif triggers["help"] in cmd_arr:
                threading.Thread(target=handle_help, args=(message,)).start()


main()
