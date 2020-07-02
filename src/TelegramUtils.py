#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Dict
import requests

from Networking import NetworkHandler


class Message:
    """
    Represents a single outgoing or inbound message
    """

    def __init__(self,
                 chat_id=None,
                 reply_to=None,
                 photo=None,
                 text=None):
        """
        Initialization
        """
        self.message_id = None
        self.from_user_id = None
        self.chat_id = chat_id
        self.reply_to = reply_to
        self.photo = photo
        self.text: str = text

    def load_from_json(self, json):
        """
        Load object from JSON data
        :param json: JSON message data from telegram API
        :return: None
        """
        try:
            # Mandatory content
            self.message_id = json["message_id"]
            self.from_user_id = json["from"]["id"]
            self.chat_id = json["chat"]["id"]
            # Optional content
            if "text" in json: self.text = json["text"]
        except KeyError as ke:
            print("Message construction failed:" + str(ke))

    def __str__(self):
        return "Chat:" + str(self.chat_id) + " Sender: " + str(self.from_user_id) + " Text: " + self.text

    def __eq__(self, other):
        if self.message_id == other.message_id and isinstance(other, Message):
            return True
        else:
            return False


class TelegramHttpsAPI:
    """
    Python abstraction for telegram HTTPS API.
    Currently only handling incoming messages with text content, incoming files not handled.
    Capable of sending text and image media.
    """

    BASE_URL = "https://api.telegram.org/bot"

    # Method endpoints
    GETUPDATES = "/getUpdates"
    SENDMESSAGE = "/sendMessage"
    SENDPHOTO = "/sendPhoto"

    def __init__(self, token):
        """
        Initialize the API to given bot token
        :param token: bot token
        """
        self.token = token
        self.url = TelegramHttpsAPI.BASE_URL + self.token
        self.update_id = None
        self.net = NetworkHandler()

    def get_updates(self):
        """
        Get unhandled updates
        :return: JSON update data as a dict
        """
        request_url = self.url + TelegramHttpsAPI.GETUPDATES
        data = self.net.https_get(request_url, {"offset": self.update_id})
        try:
            return data.json()["result"]
        except ValueError:
            return None

    def get_messages(self) -> List[Message]:
        """
        Get unhandled message updates
        :return: List of unhandled message objects
        """
        messages = []
        updates = self.get_updates()

        # Iterate through the updates
        for update in updates:
            self.update_id = update["update_id"] + 1
            raw_message = update["message"]
            if raw_message:
                # We are only interested in updates with text content
                if "text" in raw_message:
                    message_obj = Message()
                    message_obj.load_from_json(raw_message)
                    messages.append(message_obj)

        return messages

    def send_message(self, message: Message):
        """
        Sends given message. Message type (photo, text, etc.) depends on the contents of the message object
        :param message: Message object. Optional photo attribute must be a path to a local file.
        :return: None
        """

        if message.photo:
            post_url = self.url + TelegramHttpsAPI.SENDPHOTO
            parameters = {"chat_id": message.chat_id,
                          "caption": message.text,
                          "reply_to_message_id": message.reply_to}
            files = {"photo": open(message.photo, "rb")}

            self.net.https_post(post_url, parameters, files)

        elif message.text:
            post_url = self.url + TelegramHttpsAPI.SENDMESSAGE
            parameters = {"chat_id": message.chat_id,
                          "text": message.text,
                          "reply_to_message_id": message.reply_to}

            self.net.https_post(post_url, parameters)

        else:
            print("No message content available")
