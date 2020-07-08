#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import time
from threading import Semaphore


class DBAPI:
    sql_create_stats_table = """ CREATE TABLE IF NOT EXISTS drinkstats (
                                        id integer PRIMARY KEY,
                                        telegram_id integer NOT NULL,
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

    def get_total_drinks(self, telegram_id=None):
        if not telegram_id:
            return self.__execute("select count(*) from drinkstats").fetchone()[0]
        else:
            return self.__execute("select count(*) from drinkstats where telegram_id=?", telegram_id).fetchone()[0]


class DrinkTracker:

    def __init__(self):
        self.db = DBAPI("./drinkstats.db")

    def add_drink(self,
                  telegram_id,
                  telegram_username,
                  drink_type,
                  telegram_name=None):
        print("Adding drink record for user: " + telegram_username)
        self.db.add_drink(telegram_id, telegram_username, time.time(), drink_type, telegram_name)

    def get_total_drinks(self, telegram_id=None):
        return self.db.get_total_drinks(telegram_id)


if __name__ == "__main__":
    tracker = DrinkTracker()
    drinks = tracker.get_total_drinks()
    print(drinks)


