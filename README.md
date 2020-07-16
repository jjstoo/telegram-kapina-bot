# telegram-kapina-bot

This is a Telegram bot created for our squads personal entertainment. 
However, most of the modules have been made in a reusable manner.

#### Main features
* Super lightweight Telegram bot API :: [TelegramUtils][1]
* Live webcam snapshots from our favorite bar, Kultainen Apina (kapina) in Tampere, Finland :: [KapinaCam][2]
* Beer menu scraping from Untappd to get the current beer offering :: [UntappdUtils][3]
* Beer (and other beverages) consumption logging :: [DrinkTrackerUtils][4]

#### Untappd menu scraping

Untappd uses many methods to block any web scraping attempts. Due to these restrictions, the module is configured to use a random proxy for each query.
Proxying makes the connection slow and thus updates are run periodically in the background.

[1]: https://github.com/jjstoo/telegram-kapina-bot/blob/master/src/TelegramUtils.py
[2]: https://github.com/jjstoo/telegram-kapina-bot/blob/master/src/KapinaCam.py
[3]: https://github.com/jjstoo/telegram-kapina-bot/blob/master/src/UntappdUtils.py
[4]: https://github.com/jjstoo/telegram-kapina-bot/blob/master/src/DrinkTrackerUtils.py
