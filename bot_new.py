# -*- coding: utf-8 -*-
import config
import os
import telebot
import cherrypy
import requests
from PIL import Image, ImageDraw, ImageFont
from text_processing import process_text

WEBHOOK_HOST = '212.80.216.227'
WEBHOOK_PORT = 8443
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_SSL_CERT = './webhook_cert.pem'
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (config.token)

bot=telebot.TeleBot(config.token)

user_dict = {}
steps = ["name", "town", "occupation", "fact", "social", "country", "identity", "text"]

class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.clear_step_handler_by_chat_id(chat_id = message.chat.id)
    msg = bot.send_message(message.chat.id, config.messages[0])
    bot.register_next_step_handler(msg, process_step, 0)

@bot.message_handler(func=lambda message: True)
def process_all(message):
    if message.content_type == "text":
        if message.text == "Сначала":
            send_welcome(message)
        if message.text == "Поменять фото":
            msg = bot.send_message(message.chat.id, config.messages[8])
            bot.register_next_step_handler(msg, process_step, 8)

@bot.message_handler(content_types=['photo'])
def process_photos(message):
    existing_ids = tuple(user_dict.keys())
    if message.chat.id in existing_ids:
        handle_photo(message, {**user_dict[message.chat.id]})

def process_step(message, step):
    try:
        markup = telebot.types.ReplyKeyboardMarkup()
        markup.row("Пропустить")
        markup.row("Сначала", "Поменять фото")
        chat_id = message.chat.id
        if message.content_type == "text":
            if message.text == "Сначала" or message.text == "/start" or message.text == "/help":
                send_welcome(message)
                return()
            if message.text == "Поменять фото":
                msg = bot.send_message(message.chat.id, config.messages[8], reply_markup = markup)
                bot.register_next_step_handler(msg, process_step, 8)
                return()
        if step == 0:
            user = {"name" : message.text}
            user_dict[chat_id] = user
            msg = bot.send_message(message.chat.id, config.messages[step + 1], reply_markup = markup)
            bot.register_next_step_handler(msg, process_step, step + 1)
        elif step == 8:
            existing_ids = tuple(user_dict.keys())
            if chat_id in existing_ids:
                user = user_dict[chat_id]
            else:
                send_welcome(message)
            for step in steps:
                if step not in user:
                   user[step] = "Пропустить"
            handle_photo(message, {**user})
        else:
            user = user_dict[chat_id]
            user[steps[step]] = message.text
            msg = bot.send_message(message.chat.id, config.messages[step + 1], reply_markup = markup)
            bot.register_next_step_handler(msg, process_step, step + 1)
    except Exception as e:
        bot.reply_to(message, "Эх, ошибка...\nПопробуй ещё раз.")
        print(e)

def find_middle(text):
    if " " in text:
        pos1 = int(len(text) / 2) + text[int(len(text) / 2):].find(" ")
        pos2 = text[:int(len(text) / 2)].rfind(" ")
        if pos1 < int(len(text) / 2):
            pos1 = -1
        if pos1 > 0 and pos2 > 0:
            if min(len(text[pos1:]), len(text[:pos1])) / max(len(text[pos1:]), len(text[:pos1])) >= min(len(text[pos2:]), len(text[:pos2])) / max(len(text[pos2:]), len(text[:pos2])):
                return(pos1)
            else:
                return(pos2)
        elif pos2 < 0:
            return(pos1)
        else:
            return(pos2)
    else:
        return(-1)

def handle_photo(message, user):
    if message.content_type == "photo":
        file_info = bot.get_file(message.photo[-1].file_id)
        path = "tmp/" + str(message.chat.id) + file_info.file_path[-4:]
        file = bot.download_file(file_info.file_path)
        with open(path, 'wb') as new_photo:
            new_photo.write(file)
    else:
        path = config.flag
    base = Image.open(path)
    (width, height) = base.size
    if min(width, height) < 850:
        if width < height:
            new_width = 850
            new_height = new_width * height // width
        else:
            new_height = 850
            new_width = new_height * width // height
        base = base.resize((new_width, new_height), Image.ANTIALIAS)
        (width, height) = (new_width, new_height)
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    image.paste(base, (0, 0))
    tr1 = Image.open(config.tr1)
    tr2 = Image.open(config.tr2)
    qr = Image.open(config.qr)
    uniq = [user[i].strip() for i in steps[:-1] if user[i] != "Пропустить" and user[i].strip() != ""]
    text = "Я" + u"\u0020\u2013\u0020" + ("\nЯ" + u"\u0020\u2013\u0020").join(uniq)
    text_data = process_text(text, 500, 550, config.font, config.fontsize, ImageDraw.Draw(image), config.line_beg) 
    h = text_data["height"] + 100;
    tr1 = tr1.crop((0, 0, 600, h))
    image.paste(tr1, (0, 0, 600, h), mask = tr1)
    tr2y = height - 200 if height - 200 >= h + 50 else (height - h - 150) // 2 + h
    image.paste(tr2, ((width - 700) // 2, tr2y, (width - 700) // 2 + tr2.size[0], tr2y + tr2.size[1]), mask = tr2)
    image.paste(qr, (width - 160, 10, width - 10, 160))
    draw = ImageDraw.Draw(image)
    font = text_data["font"]
    draw.multiline_text((50, 50), text_data["text"], font = font, fill = config.color1)
    if user["text"] != "Пропустить":
        text = user["text"]
        text_data = process_text(text, 650, 130, config.font, 80, ImageDraw.Draw(image), "")
        draw.multiline_text(((width - text_data["width"]) // 2, tr2y + 10), text_data["text"], font = text_data["font"], fill = config.color2, align = "center")
    else:
        text = "Осенью власть может сделать меня\nчеловеком второго сорта.\nДавайте не допустим этого!"
        font = ImageFont.truetype(config.font, size = 38)
        draw.multiline_text(((width - draw.multiline_textsize(text, font = font)[0]) // 2, tr2y + 10), text, fill = config.color2, font = font, align = "center")
    path2 = "tmp/res" + str(message.chat.id) + ".png"
    image.save(path2)
    with open(path2, 'rb') as new_photo:
    	bot.send_photo(message.chat.id, new_photo)
    if path != config.flag:
        os.remove(path)
    os.remove(path2)

bot.enable_save_next_step_handlers(delay = 2)
bot.load_next_step_handlers()

bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH, certificate=open(WEBHOOK_SSL_CERT, 'r'))

cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
