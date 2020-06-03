import csv
import datetime
import locale
import logging
import re

from telegram.ext import CommandHandler, Updater

import requests

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Openweathermap Weather codes and corressponding emojis
rofl = u"\U0001F602"  # Code: 200's, 900, 901, 902, 905
with open("local/token", "r") as tmp:
    TOKEN = tmp.read().replace("\n", "")

def get_date():
    today = datetime.date.today()
    return today


def print_csv(bot, update):
    locale.setlocale(locale.LC_ALL, "ru_RU.utf8")
    with open("local/house.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            daterus = datetime.date.fromisoformat(row["Date"])
            datefinal = daterus.strftime(" %B %Y ")
            hot = " Горячая вода : " + row["Hot Water"] + " кубов "
            cold = " Холодная вода : " + row["Cold Water"] + " кубов "
            elec = " Электричество : " + row["Electricity"] + " кВт "
            chat_id = update.message.chat_id
            text = datefinal + cold + hot + elec
            bot.send_message(chat_id=chat_id, text=text)


def get_url():
    contents = requests.get("https://random.dog/woof.json").json()
    url = contents["url"]
    return url


def get_image_url():
    allowed_extension = ["jpg", "jpeg", "png"]
    file_extension = ""
    while file_extension not in allowed_extension:
        url = get_url()
        file_extension = re.search("([^.]*)$", url).group(1).lower()
    return url


def bop(bot, update):
    url = get_image_url()
    chat_id = update.message.chat_id
    bot.send_photo(chat_id=chat_id, photo=url)


def start(bot, update):
    chat_id = update.message.chat_id
    date = get_date().isoformat()
    text = rofl + " Пора чинить стиральную машину! " + rofl + date
    bot.send_message(chat_id=chat_id, text=text)


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("bop", bop))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("house", print_csv))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
