#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import sys

from TelegramUtils import TelegramHttpsAPI, Message
from ImageCapture import ImageCapture

try:
    with open("token", "r") as file:
        TOKEN = file.read().replace("\n", "")
except OSError:
    print("Token file not found")
    sys.exit(1)

OUTPUTFILE = "snapshot.jpg"
snapshot_sem = threading.Semaphore(1)
api = TelegramHttpsAPI(TOKEN)
cam = ImageCapture(snapshot_sem, OUTPUTFILE)


def handle_image_request(message: Message):
    cam.snapshot()
    with snapshot_sem:
        api.send_message(Message(chat_id=message.chat_id,
                                 reply_to=message.message_id,
                                 photo=OUTPUTFILE))


def main():
    while True:
        messages = api.get_messages()
        for message in messages:
            text = message.text.lower()
            if text.split()[0] == "/kapina":
                threading.Thread(target=handle_image_request, args=(message,)).start()


main()
