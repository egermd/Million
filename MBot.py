import telebot
import requests
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import json
import os

token = os.environ['TELEGRAM_TOKEN']
api_url = 'https://stepik.akentev.com/api/millionaire'

bot = telebot.TeleBot(token)

try:
    data = json.load(open("data.json", 'r', encoding='utf-8'))

except FileNotFoundError:
    data = {
"count": {},
"states": {},
"answers": {},
"params": {},
"right_answer": {},
"greetings": {},
}


def change_data(key, user_id, value):
    data[key][user_id] = value
    json.dump(data, open("data.json", 'w',
                         encoding='utf-8'), indent=2, ensure_ascii=False)


MAIN = 'main'
QUIZ = 'question'
LEVEL = "level"
SECOND_CHANCE = 'chance'


@bot.message_handler(func=lambda message: True)
def dispatcher(message):
    user_id = str(message.from_user.id)
    if user_id not in data["count"]:
        data["count"][user_id] = {}
        data["count"][user_id]['victories'] = 0
        data["count"][user_id]['defeats'] = 0
    json.dump(data, open("data.json", 'w',
                         encoding='utf-8'), indent=2, ensure_ascii=False)
    state = data["states"].get(user_id, MAIN)
    if state == MAIN:
        main_handler(message)
    elif state == QUIZ:
        question(message)
    elif state == LEVEL:
        level(message)
    elif state == SECOND_CHANCE:
        chance(message)


def main_handler(message):
    user_id = str(message.from_user.id)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.row("Привет", "Вопрос", "Сложность", "Счёт")
    if message.text == '/start':
        bot.send_message(message.chat.id, "Это бот-игра в \"Кто хочет стать миллионером\"", reply_markup=markup)
    elif message.text == "Привет" and user_id in data["greetings"]:
        bot.send_message(message.chat.id, 'Мы уже здоровались))', reply_markup=markup)
    elif message.text == "Привет":
        change_data("greetings", user_id, True)
        bot.send_message(message.chat.id, 'Ну привет!', reply_markup=markup)
    elif message.text == "Сложность":
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.row("Легко", "Средне", "Сложно")
        bot.send_message(message.chat.id, "Выбери сложность вопросов", reply_markup=markup)
        change_data("states", user_id, LEVEL)

    elif message.text in ('Спроси меня вопрос', 'Вопрос', 'Ещё вопрос'):
        if user_id in data["params"]:
            quiz_bank = requests.get(api_url, params={"complexity": data["params"][user_id]})
        else:
            quiz_bank = requests.get(api_url, )
        res = quiz_bank.json()
        change_data("right_answer", user_id, res["answers"][0])
        change_data("answers", user_id, res["answers"])
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.row(*data["answers"][user_id])
        bot.send_message(message.chat.id, "{} {}".format(res["question"], " ".join(set(data["answers"][user_id]))),
                         reply_markup=markup)
        change_data("states",user_id, QUIZ)
    elif message.text in ("Покажи счёт", "Счёт"):
        bot.send_message(message.chat.id, ('Побед: {} Поражений: {}'.format(data["count"][user_id]['victories'],
                                                                            data["count"][user_id]['defeats'])))

    else:
        bot.send_message(message.chat.id, 'Я тебя не понял')


def question(message):
    user_id = str(message.from_user.id)
    if message.text == data["right_answer"][user_id]:
        bot.send_message(message.chat.id, 'Правильно!')
        data["count"][user_id]['victories'] += 1
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.row("Привет", "Вопрос", "Сложность", "Счёт")
        bot.send_message(message.chat.id, "Что делаем дальше?", reply_markup=markup)
        data["states"][user_id] = MAIN
        json.dump(data, open("data.json", 'w',
                             encoding='utf-8'), indent=2, ensure_ascii=False)
    elif message.text in list(data["answers"][user_id]) and message.text != data["right_answer"][user_id]:
        bot.send_message(message.chat.id, 'Неправильно :( Попробуй еще раз')
        change_data("states", user_id, SECOND_CHANCE)
    else:
        bot.send_message(message.chat.id, 'Я тебя не понял')


def chance(message):
    user_id = str(message.from_user.id)
    if message.text == data["right_answer"][user_id]:
        bot.send_message(message.chat.id, 'Правильно!')
        data["count"][user_id]['victories'] += 1
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.row("Привет", "Вопрос", "Сложность", "Счёт")
        bot.send_message(message.chat.id, "Что делаем дальше?", reply_markup=markup)
        data["states"][user_id] = MAIN
        json.dump(data, open("data.json", 'w',
                             encoding='utf-8'), indent=2, ensure_ascii=False)
    elif message.text in list(data["answers"][user_id]) and message.text != data["right_answer"][user_id]:
        bot.send_message(message.chat.id, 'Неправильно :( ')
        data["count"][user_id]['defeats'] += 1
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.row("Привет", "Вопрос", "Сложность", "Счёт")
        bot.send_message(message.chat.id, "Что делаем дальше?", reply_markup=markup)
        data["states"][user_id] = MAIN
        json.dump(data, open("data.json", 'w',
                             encoding='utf-8'), indent=2, ensure_ascii=False)
    else:
        bot.send_message(message.chat.id, 'Я тебя не понял')


def level(message):
    user_id = str(message.from_user.id)

    if message.text == 'Легко':
        change_data("params", user_id, '1')
    elif message.text == 'Средне':
        change_data("params", user_id, '2')
    elif message.text == 'Сложно':
        change_data("params", user_id, '3')
    else:
        bot.send_message(message.chat.id, 'Я тебя не понял')
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.row("Привет", "Вопрос", "Сложность", "Счёт")
    bot.send_message(message.chat.id, "Что делаем дальше?", reply_markup=markup)
    change_data("states", user_id, MAIN)


bot.polling()
