# telegram-kapina-bot

Telegram bot for getting live snapshots and beer info from Pub Kultainen Apina in Tampere, Finland.
Webcam functionality is built around OpenCV and a super lightweight telegram bot API has been built from scratch.

Untappd uses many methods to block web scraping. Due to these measures, this program utilizes a pool of
random proxies to avoid being IP blocked from the site. This considerably slows down the update process, so Untappd updates are run
periodically in the background.

Telegram auth token must be placed in a file called "token" in the same working directory as the source files
