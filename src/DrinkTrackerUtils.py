#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import time


class DBAPI:
    sql_create_stats_table = """ CREATE TABLE IF NOT EXISTS drinkstats (
                                        id integer PRIMARY KEY,
                                        telegram_id text NOT NULL,
                                        telegram_username text,
                                        telegram_name text,
                                        date integer NOT NULL,
                                        drink_type text
                                    ); """

    sql_insert_drink = """ INSERT INTO drinkstats (telegram_id, telegram_username, telegram_name, date, drink_type)
              values (?,?,?,?,?) """

    def __init__(self, db_file):
        """
        Initializes the database api to work on given file
        :param db_file: database file
        """
        try:
            self.conn = sqlite3.connect(db_file)
            self.__init_tables()
        except sqlite3.Error as e:
            print("Database connection failed")
            print(e)

    def __str__(self):
        c = self.conn.cursor()
        c.execute("select * from drinkstats")
        return str(c.fetchall())

    def __execute(self, cmd, *args):
        """
        Execute SQL command
        :param cmd: command to run
        :param args: arguments to sqlite3.dbapi2.Cursor.execute()
        :return: True if command succeeds
        """
        c = self.conn.cursor()
        try:
            c.execute(cmd, args)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print("Error running DB command")
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

        if all((telegram_id, telegram_username, date, drink_type)):
            if not self.__execute(DBAPI.sql_insert_drink,
                                  telegram_id, telegram_username, telegram_name, date, drink_type):
                print("Drink insertion failed")
        else:
            print("Insufficient data for drink insertion")


class DrinkTracker:

    BEER = "beer"
    BOOZE = "viina"
    WINE = "viini"

    def __init__(self):
        self.db = DBAPI("./drinkstats.db")


if __name__ == "__main__":
    tracker = DrinkTracker()
