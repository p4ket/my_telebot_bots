import telebot
from PIL import Image, ImageDraw, ImageFont
import os
from io import BytesIO

# токен бота

TOKEN = open('token', 'r').readline()
bot = telebot.TeleBot(TOKEN)

# папки для картинок
os.makedirs('images/user_images', exist_ok=True)
os.makedirs('images/bot_images', exist_ok=True)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Привет! Пришли фото — сделаю демотиватор.')


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

        user_img_path = f"images/user_images/{message.from_user.id}_{message.message_id}.jpg"
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
            text = str(message.caption).split('\n')
            print(text, len(text))
            if len(text) == 2:
                print('изображение c подписью')
                if len(text[0]) > 30:
                    text[0] = 'too many letters'
                    bot.send_message(message.chat.id, 'brooo, too many letters in first line...... ((((')
                if len(text[1]) > 60:
                    text[1] = 'too many letters'
                    bot.send_message(message.chat.id, 'brooo, too many letters in second line...... ((((')

            if len(text) == 1 and text[0] != 'None':
                text = [str(text[0]), '  ']
            else:
                text = ['','']


        else:
            user_img = original_img.convert("RGBA")
            user_img.thumbnail((800, 600), Image.Resampling.LANCZOS)
            text = str(message.caption).split('\n')
            print(text, len(text))
            if len(text) == 2:
                print('изображение c подписью')
                if len(text[0]) > 30:
                    text[0] = 'too many letters'
                    bot.send_message(message.chat.id, 'brooo, too many letters in first line...... ((((')
                if len(text[1]) > 60:
                    text[1] = 'too many letters'
                    bot.send_message(message.chat.id, 'brooo, too many letters in second line...... ((((')

            if len(text) == 1 and text[0] != 'None':
                text = [str(text[0]), '  ']
            else:
                text = ['', '']

        # Вставка на холст
        if user_img.mode != "RGBA":
            user_img = user_img.convert("RGBA")
        img_w, img_h = user_img.size
        x = (1080 - img_w) // 2
        y = (1080 - img_h) // 2 - 50
        canvas.paste(user_img, (x, y), user_img)

        # Текст
        try:
            font = './font/minecraft.ttf'
        except:
            font = ImageFont.load_default()


        bbox = draw.textbbox((0, 0), str(text[0]), font=(ImageFont.truetype(font=font, size=50)))
        text_x = (1080 - (bbox[2] - bbox[0])) // 2
        text_y = y + img_h + 30
        draw.text((text_x, text_y), str(text[0]), fill=(255, 255, 255), font=(ImageFont.truetype(font=font, size=40)))
        bbox1 = draw.textbbox((0, 0), str(text[1]), font=(ImageFont.truetype(font=font, size=40)))
        text_x = ((1080 - (bbox1[2] - bbox1[0])) // 2)
        text_y = y + img_h + 90
        draw.text((text_x, text_y), str(text[1]), fill=(255, 255, 255), font=(ImageFont.truetype(font=font, size=30)))



        output_path = f"images/bot_images/demotivator_{message.from_user.id}_{message.from_user.username}_{message.message_id}.jpg"
        canvas.save(output_path, "JPEG", quality=95)

        with open(output_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo)

    except Exception as e:
        bot.reply_to(message, "Что-то сломалось... Попробуй другое фото.")
        print("Ошибка:", e)

bot.infinity_polling()