#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import time
import json
import random
from datetime import datetime
from typing import Tuple
from threading import Semaphore

from TelegramUtils import TelegramHttpsAPI, Message


class DBAPI:
    sql_create_stats_table = """CREATE TABLE IF NOT EXISTS drinkstats (
                                        id integer PRIMARY KEY,
                                        telegram_id integer NOT NULL,
                                        telegram_username text,
                                        telegram_name text,
                                        date integer NOT NULL,
                                        drink_type text
                                    ); """

    sql_insert_drink = """ INSERT INTO drinkstats (telegram_id, telegram_username, telegram_name, date, drink_type)
              values (?,?,?,?,?) """

    sql_get_drinks = "select count(*) from drinkstats where telegram_id like ? and drink_type like ?"

    sql_get_drinks_today = """ 
                            select count(*) from drinkstats where 
                            telegram_id like ? 
                            and drink_type like ? 
                            and date between ? and ? 
                            """

    def __init__(self, db_file):
        """
        Initializes the database api to work on given file
        :param db_file: database file
        """
        self.db_sem = Semaphore(1)
        try:
            self.conn = sqlite3.connect(db_file, check_same_thread=False)
            self.__init_tables()
        except sqlite3.Error as e:
            print("Database connection failed")
            print(e)

    def __str__(self):
        return str(self.__execute("select * from drinkstats").fetchall())

    def __execute(self, cmd, *args):
        """
        Execute SQL command
        :param cmd: command to run
        :param args: arguments to sqlite3.dbapi2.Cursor.execute()
        :return: Cursor if command succeeds, False if not
        """
        with self.db_sem:
            c = self.conn.cursor()
            try:
                with self.conn:
                    c.execute(cmd, args)
                return c
            except sqlite3.Error as e:
                print("Error running DB command")
                print(e)
                return False

            except Exception as e:
                print("Unknown error when running DB command")
                print(e)
                return False

    def __init_tables(self):
        """
        Initializes tables
        :return: None
        """
        if not self.__execute(DBAPI.sql_create_stats_table):
            print("Table init failed")

    def add_drink(self,
                  telegram_id,
                  telegram_username,
                  date,
                  drink_type,
                  telegram_name=None):
        """
        Adds one drink record to the database
        :param telegram_id: telegram user ID (always present)
        :param telegram_username: telegram username (not always present but required)
        :param date: timestamp (UNIX seconds)
        :param drink_type: drink type
        :param telegram_name: real name, optional
        :return: None
        """

        if not self.__execute(DBAPI.sql_insert_drink,
                              telegram_id, telegram_username, telegram_name, date, drink_type):
            print("Drink insertion failed")

    def get_total_drinks(self, telegram_id, drink_type, time_range: Tuple[float, float] = None):
        """
        Get total amount of drinks consumed with constraining SQL parameters
        :param telegram_id: Drinkers telegram id for the query
        :param drink_type: Drink type for the query
        :param time_range: Time range for the query. Defaults to all timeframes (None)
        :return: Number of drinks or None in case of error
        """
        try:
            if time_range is None:
                return self.__execute(DBAPI.sql_get_drinks,
                                      telegram_id, drink_type).fetchone()[0]
            else:
                return self.__execute(DBAPI.sql_get_drinks_today,
                                      telegram_id, drink_type, time_range[0], time_range[1]).fetchone()[0]
        except sqlite3.Error as e:
            print("Error getting total drinks!")
            print(e)


class DrinkTracker:
    def __init__(self):
        self.db = DBAPI("./drinkstats.db")
        with open("assets/drink_replies", "r") as f:
            self.replies = json.load(f)
            print(self.replies)

    def get_drink_cmds(self):
        cmds = {}
        for drink in self.replies.keys():
            cmds[drink] = "/" + drink

        return cmds

    def add_drink(self,
                  telegram_id,
                  telegram_username,
                  drink_type,
                  telegram_name=None):
        """
        Adds a drink record for given user
        :param telegram_id: Drinkers telegram id
        :param telegram_username: Username
        :param drink_type: Drink type
        :param telegram_name: Drinkers telegram name if available
        :return: None
        """
        print("Adding drink record for user: " + telegram_username)
        self.db.add_drink(telegram_id, telegram_username, time.time(), drink_type, telegram_name)

    def get_total_drinks(self, telegram_id="%", drink_type="%"):
        """
        Get total amount of drinks consumed
        :param telegram_id: Drinker id. Defaults to all drinkers.
        :param drink_type: Drink type. Defaults to all drinks.
        :return: Amount of drinks consumed according to the given parameters
        """
        return self.db.get_total_drinks(telegram_id, drink_type)

    def get_total_drinks_today(self, telegram_id="%", drink_type="%"):
        """
        Get total amount of drinks consumed during the ongoing day
        :param telegram_id: Drinker id. Defaults to all drinkers.
        :param drink_type: Drink type. Defaults to all drinks.
        :return: Amount of drinks consumed during the day according to given parameters.
        """
        today = datetime.today()
        daystart = datetime(year=today.year, month=today.month,
                            day=today.day, hour=0, second=0).timestamp()
        dayend = datetime(year=today.year, month=today.month,
                          day=today.day, hour=23, minute=59, second=59).timestamp()

        return self.db.get_total_drinks(telegram_id, drink_type, time_range=(daystart, dayend))

    def send_special_reply(self, api: TelegramHttpsAPI, message: Message, drink_type):
        """
        Sends a randomized special reply to the target if a reply is defined
        :param api: Telegram api
        :param message: Received message to reply to
        :param drink_type: Drink type
        :return: True if a special message was found
        """
        reply_found = False
        total_amount = str(self.get_total_drinks(telegram_id=message.user_id, drink_type=drink_type))
        daily_amount = str(self.get_total_drinks_today(telegram_id=message.user_id, drink_type=drink_type))

        print(total_amount)
        print(daily_amount)

        drink_daily_replies = self.replies[drink_type]["daily"]
        drink_total_replies = self.replies[drink_type]["total"]

        if daily_amount in drink_daily_replies:
            reply_found = True
            reply = random.choice(drink_daily_replies[daily_amount])
            api.send_message(Message(chat_id=message.chat_id,
                                     reply_to=message.message_id,
                                     parse_mode="Markdown",
                                     text=reply))

        if total_amount in drink_total_replies:
            reply_found = True
            reply = random.choice(drink_total_replies[total_amount])
            api.send_message(Message(chat_id=message.chat_id,
                                     reply_to=message.message_id,
                                     parse_mode="Markdown",
                                     text=reply))

        return reply_found


if __name__ == "__main__":
    tracker = DrinkTracker()
    tracker.add_drink(123, "123", "testi")

