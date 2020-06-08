import csv
import datetime
import locale
import logging
import re
import os

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
            hot = " Горячая вода : " + row["hot_water"] + " кубов "
            cold = " Холодная вода : " + row["cold_water"] + " кубов "
            elec = " Электричество : " + row["electricity"] + " кВт "
            chat_id = update.message.chat_id
            text = datefinal + cold + hot + elec
            bot.send_message(chat_id=chat_id, text=text)

def house_payment(bot, update):
    locale.setlocale(locale.LC_ALL, "ru_RU.utf8")
    with open("local/house.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = [row for row in reader]
    with open("rates.json") as rates_file:
        rates = eval(rates_file.read())
    current, last = rows[-1], rows[-2]
    delta = {}
    for key in ["hot_water", "cold_water", "electricity"]:
        delta[key] = float(current[key]) - float(last[key])
    delta['drain'] = delta['cold_water'] + delta['hot_water'] 
    
    total_sum = 0
    total_sum += rates['gas']
    total_sum += rates['door']
    total_sum += rates['electricity'] * delta['electricity']
    total_sum += (rates['cold_water'] + rates['drain']) * delta['cold_water']
    total_sum += (rates['hot_water'] + rates['drain']) * delta['hot_water']
    
    output = ""
    for name, key in zip(["Gas", "Door"], ['gas', 'door']):
        output += f"{name:12}: {rates[key]:24.2f}"
        output += '\n'
    
    names = ["Electricity", "Cold water", "Hot water", "Drain"]
    keys = [x.lower().replace(' ', '_') for x in names]
    for name, key in zip(names, keys):
        output += f"{name:12}: {rates[key]:6.2f} * {delta[key]:6.2f}"
        output += f" = {(rates[key] * delta[key]):6.2f}"
        output += '\n'
    output += '-' * 38
    output += '\n'
    output += f"{'Total':12}: {total_sum:24.2f}"
    bot.send_message(chat_id=chat_id, text=output)

    

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

def stove_last(bot, update):
    directory = "local"
    filename = "stove.csv"
    path = os.path.join(directory, filename)
    if filename not in os.listdir(directory):
        text = "Записей нет. Самое время помыть плиту!"
    else:
        with open(path) as csvfile:
            reader = csv.DictReader(csvfile)
            row = reader[-1]
            daterus = datetime.date.fromisoformat(row["Date"])
            text = f"{daterus} {row[person]}"
    bot.send_message(chat_id=chat_id, text=text)

def stove_add(bot, update, context):
    directory = "local"
    filename = "stove.csv"
    path = os.path.join(directory, filename)
    if filename not in os.listdir(directory):
        mode = 'w'
    else:
        mode = 'a'
    with open(path, mode) as csvfile:
        csvfile.write(','.join(context.args))




def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("bop", bop))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("house", print_csv))
    dp.add_handler(CommandHandler("stove_last", stove_last))
    dp.add_handler(CommandHandler("stove_add", stove_add))
    dp.add_handler(CommandHandler("house_payment", house_payment))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
