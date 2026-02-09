import telebot
from PIL import Image, ImageDraw, ImageFont
import os
from io import BytesIO
import time

# токен бота

TOKEN = open('info/token', 'r').readlines()
bot = telebot.TeleBot(TOKEN[0].strip())
admin_bot = telebot.TeleBot(TOKEN[1].strip())

admins_list = open('info/admins_list').readlines()


def check_to_text(message):
    text = str(message.caption).split('\n')
    if len(text) == 2:
        print('изображение c подписью')
        if len(text[0]) > 30:
            text[0] = 'too many letters'
            bot.send_message(message.chat.id, 'brooo, too many letters in first line...... ((((')
        if len(text[1]) > 50:
            text[1] = 'too many letters'
            bot.send_message(message.chat.id, 'brooo, too many letters in second line...... ((((')

    if len(text) == 1 and text[0] != 'None':
        text = [str(text[0]), '  ']
        if len(text[0]) > 30:
            text[0] = 'too many letters'
            bot.send_message(message.chat.id, 'brooo, too many letters in first line...... ((((')
    if len(text) == 0 or text[0] == 'None':
        text = ['', '']
    print(text, len(text))
    return text



def send_to_admins_photo(message, admin_id, output_path):
    admin_bot.send_photo(chat_id=admin_id, photo=open(output_path, 'rb'),
                         caption=f'User ID: {message.from_user.id}\nUser Name: {message.from_user.username}\nFirst Name: {message.from_user.first_name}')



#   DEMOTIVATOR BOT CODE
#   DEMOTIVATOR BOT CODE
#   DEMOTIVATOR BOT CODE
#   DEMOTIVATOR BOT CODE
#   DEMOTIVATOR BOT CODE

@bot.message_handler(commands=['start'])
def start(message):
    with open('./images/templates/start_image.jpg', 'rb') as f:
        bot.send_photo(message.chat.id, f,
                       caption="Партия приветсвовать ты! Пришли фотографию — я сделать демотиватор. Текст должен быть под сообщением, как пример показать.")



@bot.message_handler(content_types=['text'])
def echo(message):
    print(f'{message.text} \n{message.from_user.username}              {message.from_user.id}')
    response = input('./: ')
    # response = message.text
    print(message.text)
    bot.send_message(message.chat.id, response)




@bot.message_handler(content_types=['photo'])
def make_demotivator(message):
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)


        user_img_path = f"images/{message.from_user.id}_{message.message_id}.jpg"
        with open(user_img_path, 'wb') as f:
            f.write(downloaded_file)

        canvas = Image.new('RGB', (1080, 1080), color=(0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        original_img = Image.open(user_img_path).convert("RGB")
        MIN_GOOD_SIZE = 500

        if original_img.width < MIN_GOOD_SIZE or original_img.height < MIN_GOOD_SIZE:
            img = original_img.resize((800, 600), Image.Resampling.NEAREST)
            img = img.convert("P", palette=Image.ADAPTIVE, colors=32).convert("RGB")
            for _ in range(100):
                buf = BytesIO()
                img.save(buf, "JPEG", quality=5)
                buf.seek(0)
                img = Image.open(buf).convert("RGB")
            img = img.resize((800, 600), Image.Resampling.NEAREST)
            user_img = img
            text = check_to_text(message)




        else:
            user_img = original_img.convert("RGBA")
            user_img.thumbnail((800, 600), Image.Resampling.LANCZOS)
            text = check_to_text(message)

        # Вставка на холст
        if user_img.mode != "RGBA":
            user_img = user_img.convert("RGBA")
        img_w, img_h = user_img.size
        x = (1080 - img_w) // 2
        y = (1080 - img_h) // 2 - 50
        gap = 10
        x1 = x-gap
        y1=y-gap
        x2=x+img_w+gap
        y2=y+img_h+gap
        draw.rectangle(((x1, y1), (x2, y2)), outline='white', fill=None, width=4)
        canvas.paste(user_img, (x, y), user_img)


        # Текст
        try:
            font = './font/minecraft.ttf'
        except:
            font = ImageFont.load_default()


        bbox = draw.textbbox((0, 0), str(text[0]), font=(ImageFont.truetype(font=font, size=50)))
        text_x = (1080 // 2) - ((bbox[2] - bbox[0]) // 2)
        text_y = y + img_h + 30
        draw.text((text_x, text_y), str(text[0]), fill=(255, 255, 255), font=(ImageFont.truetype(font=font, size=50)))
        bbox1 = draw.textbbox((0, 0), str(text[1]), font=(ImageFont.truetype(font=font, size=40)))
        text_x1 = (1080 // 2) - ((bbox1[2] - bbox1[0]) // 2)
        text_y1 = y + img_h + 90
        draw.text((text_x1, text_y1), str(text[1]), fill=(255, 255, 255), font=(ImageFont.truetype(font=font, size=40)))

        output_path = f"images/demotivator_{message.from_user.id}_{message.from_user.username}_{message.message_id}.jpg"
        canvas.save(output_path, "JPEG", quality=95)

        bot.send_photo(chat_id=message.chat.id, photo=open(output_path, 'rb'))

        [send_to_admins_photo(message, admin_id, output_path) for admin_id in admins_list] # send to admin photo in one line


        os.remove(f"images/demotivator_{message.from_user.id}_{message.from_user.username}_{message.message_id}.jpg")
        os.remove(f"images/{message.from_user.id}_{message.message_id}.jpg")

    except Exception as e:
            bot.reply_to(message, "Что-то сломалось... Попробуй другое фото.")
            print("Ошибка:", e)

bot.infinity_polling()

# DEMOTIVATOR BOT CODE END
# DEMOTIVATOR BOT CODE END
# DEMOTIVATOR BOT CODE END
# DEMOTIVATOR BOT CODE END
# DEMOTIVATOR BOT CODE END
