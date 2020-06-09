import csv
import datetime
import locale
import logging
import re
import os
import requests
import pytz

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

MENU, HOUSE, RATES, STOVEADD, STOVE = range(5)

reply_keyboard = [["Коммуналка", "Данные с счётчиков"], ["Плита помыта",
                   "Когда мыли плиту"]]
markup = ReplyKeyboardMarkup(
    reply_keyboard, resize_keyboard=True, one_time_keyboard=True
)

emoji = {
    "angry_face": "\U0001F620",
    "rofl": "\U0001F602",
    "fire": "\U0001F525",
    "frost": "\U00002744",
    "droplet": "\U0001F4A7",
    "energy": "\U000026A1",
}

timezone_local = pytz.timezone("Europe/Moscow")
timezone_offset = "+0300"

with open("local/token", "r") as tmp:
    TOKEN = tmp.read().replace("\n", "")


def get_today():
    today = datetime.datetime.now(timezone_local)
    return today


def get_today_rus(args):
    locale.setlocale(locale.LC_ALL, "ru_RU.utf8")
    today = get_today().strftime(args)
    return today


def print_csv(update, context):
    locale.setlocale(locale.LC_ALL, "en_US.utf8")
    e_coldw = emoji['frost'] + emoji['droplet']
    e_hotw = emoji['fire'] + emoji['droplet']
    e_elec = emoji['energy']
    with open("local/house.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        text = "```\n"
        text += f"{'Date':10}| {e_coldw:7}| {e_hotw:7}| {e_elec:8}\n"
        text += '-' * 35 + '\n'
        for row in reader:
            datefinal = datetime.datetime.strptime(row["date"],
                                                    "%Y-%m-%d").strftime("%y %b %-d")
            hot, cold, elec = row["hot_water"], row["cold_water"], row["electricity"]
            text += f"{datefinal:10}| {cold:7}| {hot:7}| {elec:8}\n"
        text += '```\n'
        update.message.reply_text(text=text, parse_mode="MarkdownV2")

    return MENU


def house_payment(update, context):
    locale.setlocale(locale.LC_ALL, "ru_RU.utf8")
    with open("local/house.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = [row for row in reader]
    with open("local/rates.json") as rates_file:
        rates = eval(rates_file.read())
    current, last = rows[-1], rows[-2]
    delta = {}
    for key in ["hot_water", "cold_water", "electricity"]:
        delta[key] = float(current[key]) - float(last[key])
    delta['drain'] = delta['cold_water'] + delta['hot_water']

    total_sum = rates['gas'] + rates['door']
    total_sum += rates['electricity'] * delta['electricity']
    total_sum += (rates['cold_water'] + rates['drain']) * delta['cold_water']
    total_sum += (rates['hot_water'] + rates['drain']) * delta['hot_water']

    output = "```\n"
    for name, key in zip(["Gas", "Door"], ['gas', 'door']):
        output += f"{name:7}: {rates[key]:21.2f}\n"

    names = ["Electr", "Cwater", "Hwater", "Drain"]
    keys = ["electricity", "cold_water", "hot_water", "drain"]
    #keys = [x.lower().replace(' ', '_') for x in names]
    for name, key in zip(names, keys):
        output += f"{name:7}: {rates[key]:6.2f} * {delta[key]:3.0f}"
        output += f" = {(rates[key] * delta[key]):6.2f}\n"
    output += '-' * 30 + '\n'
    output += f"{'Total':7}: {total_sum:21.2f}\n"
    output += "```"
    update.message.reply_text(text=output, parse_mode="MarkdownV2")

    return MENU


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


def start(update, context):
    rofl = emoji['rofl']
    reply_text = (rofl + " Слава героям Донбасса! " + rofl)
    update.message.reply_text(reply_text, reply_markup=markup)

    return MENU


def check_name(name):
    if (name == "Taika"):
        return "Денис"
    else:
        return name


def stove_last(update, context):
    directory = "local"
    filename = "stove.csv"
    if filename not in os.listdir(directory):
        text = "Записей нет. Самое время помыть плиту!"
    else:
        with open(directory + '/' + filename) as csvfile:
            reader = csv.DictReader(csvfile)
            rows = [row for row in reader]
            text = ' '.join(rows[-1])
    update.message.reply_text(text)

    return MENU

def stove_add(update, context):
    reply_text = "Помыл плиту? (Да/Нет/Затрудняюсь ответить)"
    update.message.reply_text(reply_text)

    return STOVEADD

def stove_add_answer(update, context):
    directory = "local"
    filename = "stove.csv"
    path = os.path.join(directory, filename)
    if filename not in os.listdir(directory):
        mode = 'w'
    else:
        mode = 'a'
    answer = update.message.text
    if (answer == "Да" or answer == "да"):
        user = check_name(update.message.from_user.first_name)
        with open(path, mode) as csvfile:
            date = get_today().isoformat()
            csvfile.write(date + ',' + user + '\n')
        reply_text = "Умница!"
    elif (answer == "Нет" or answer == "нет"):
        reply_text = "Ну ка пошёл мыть плиту " + emoji['angry_face']
    else:
        reply_text = "Так Да или Нет? Давай снова :^)"
    update.message.reply_text(reply_text)

    return MENU

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    MENU_PAR = [
        MessageHandler(Filters.regex("^Коммуналка$"), house_payment),
        MessageHandler(Filters.regex("^Данные с счётчиков$"), print_csv),
        MessageHandler(Filters.regex("^Плита помыта$"), stove_add),
        MessageHandler(Filters.regex("^Когда мыли плиту$"), stove_last),
    ]

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: MENU_PAR,
            STOVEADD: MENU_PAR + [MessageHandler(Filters.text, stove_add_answer)],
            HOUSE: MENU_PAR,
            STOVE: MENU_PAR,
            RATES: MENU_PAR
            # CommandHandler('skip', skip_commentary)]
        },
        fallbacks=[ConversationHandler.END],
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
