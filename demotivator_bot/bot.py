import telebot
from PIL import Image, ImageDraw, ImageFont
import os
from io import BytesIO
from html import escape

# Безопасная загрузка токенов
with open('info/token', 'r', encoding='utf-8') as f:
    TOKEN_LINES = f.readlines()
    BOT_TOKEN = TOKEN_LINES[0].strip()

bot = telebot.TeleBot(BOT_TOKEN)
admin_list = ['6555912810', '5081309603', '8204500319']
my_bots_id = {"test_bot": '8205691540', "admin_info": '8213882036', "supergroup": '-1003637655262'}
black_list = ['7167194461', '8581093935', '-1003754441670']
selected_list = ['777000']

# Списки команд для фильтрации
DEMOTIVATOR_COMMANDS = ['/make_demotivator', '/demotivator', '/dm']
POOR_QUALITY_COMMANDS = ['/do_a_poor_quality', '/poor', '/pq']


def send_to_group_photo(message, group_id, output_path=None, photo=None):
    """Отправка результата администраторам"""
    try:
        user_id = escape(str(message.from_user.id))
        first_name = escape(message.from_user.first_name) if message.from_user.first_name else "None"
        username = message.from_user.username or ""

        caption = (
            f"User ID: <code>{user_id}</code>\n"
            f"User Name: <a href='t.me/{username}'>@{username}</a>\n"
            f"First Name: {first_name}"
        )

        if output_path is not None:
            with open(output_path, 'rb') as photo_file:
                bot.send_photo(chat_id=group_id, photo=photo_file, caption=caption, parse_mode='HTML')
        if photo is not None:
            if isinstance(photo, str):  # если путь к файлу
                with open(photo, 'rb') as photo_file:
                    bot.send_photo(chat_id=group_id, photo=photo_file, caption=caption, parse_mode='HTML')
            else:  # если BytesIO или уже открытый файл
                bot.send_photo(chat_id=group_id, photo=photo, caption=caption, parse_mode='HTML')
    except Exception as e:
        print(f"Ошибка отправки в супергруппу: {e}")


def check_to_text(message):
    """Обработка текста из подписи к изображению"""
    caption = message.caption if message.caption else ""
    text = caption.split('\n')

    # Удаляем команды из текста
    commands_list = DEMOTIVATOR_COMMANDS + POOR_QUALITY_COMMANDS
    text = [line for line in text if line.strip() and not any(cmd in line for cmd in commands_list)]

    # Очищаем от команд полностью
    clean_caption = caption
    for cmd in commands_list:
        clean_caption = clean_caption.replace(cmd, '').strip()
    text = [line.strip() for line in clean_caption.split('\n') if line.strip()]

    if len(text) >= 2:
        title, subtitle = text[0], text[1]
        if len(title) > 30:
            title = 'too many letters'
            bot.send_message(message.chat.id, 'brooo, too many letters in first line...... ((((')
        if len(subtitle) > 50:
            subtitle = 'too many letters'
            bot.send_message(message.chat.id, 'brooo, too many letters in second line...... ((((')
        return [title, subtitle]
    elif len(text) == 1 and text[0]:
        title = text[0]
        if len(title) > 30:
            title = 'too many letters'
            bot.send_message(message.chat.id, 'brooo, too many letters in first line...... ((((')
        return [title, '  ']
    else:
        return ['', '']


# Фильтры для хэндлеров
def has_demotivator_command(message):
    caption = message.caption or ""
    return any(cmd in caption for cmd in DEMOTIVATOR_COMMANDS)


def has_poor_quality_command(message):
    caption = message.caption or ""
    return any(cmd in caption for cmd in POOR_QUALITY_COMMANDS)\


def parse_shakal_level(caption, commands_list):
    if not caption:
        return False, None

    found_cmd = None
    for cmd in commands_list:
        if cmd in caption:
            found_cmd = cmd
            # Убираем команду и разбиваем остаток на части
            parts = caption.replace(cmd, '', 1).strip().split()
            break

    if not found_cmd:
        return False, None

    # Пытаемся распарсить число (с % или без)
    if parts:
        num_str = parts[0].rstrip('%')
        if num_str.lstrip('-').isdigit():
            level = int(num_str)
            level = max(0, min(100, level))  # Ограничиваем 0–100
            return True, level

    # Команда есть, но числа нет — дефолт 100%
    return True, 100


def get_quality_params(percent):
    percent = max(0, min(100, percent))

    # JPEG quality: 0% → 95, 100% → 1 (линейная интерполяция)
    quality = max(1, 95 - int(percent * 0.94))

    # Итерации: 0% → 1, 100% → 100
    iterations = max(1, int(percent))

    return quality, iterations


@bot.message_handler(commands=['start'])
def start(message):
    if str(message.chat.id) not in black_list:
        try:
            with open('./images/templates/start_image.jpg', 'rb') as f:
                bot.send_photo(
                    message.chat.id, f,
                    caption="Партия приветсвовать ты! Пришли фотографию — я сделать демотиватор. Текст должен быть под сообщением, как пример показать."
                )
        except Exception as e:
            bot.send_message(message.chat.id, "Ошибка загрузки стартового изображения")
            print(f"Start error: {e}")
    else:
        if message.from_user.id not in selected_list:
            bot.send_message(message.chat.id, f'великий партия выгнать ты {message.from_user.id}, плохой тайвань шпиенб start')


@bot.message_handler(content_types=['text'])
def echo(message):
    if str(message.chat.id) not in black_list:
        print(f'{message.text} \n{message.from_user.username}              {message.from_user.id}')
        try:
            print(message.text)
            # Исправлен порядок аргументов: chat_id, text
            bot.send_message(message.chat.id, 'партия учтет твой мысль')
        except Exception as e:
            bot.send_message(message.chat.id, "партия не принимать твой запрос")
            print(f"Echo error: {e}")
    else:
        if message.from_user.id not in selected_list:
            bot.send_message(message.chat.id, f'великий партия выгнать ты {message.from_user.id}, плохой тайвань шпиен, эхо не работать')
        else:
            print('сообщение от избранного')


# Хэндлер для демотиватора — только если есть соответствующая команда
@bot.message_handler(content_types=['photo'], func=has_demotivator_command)
def make_demotivator(message):
    if str(message.chat.id) in black_list:
        if message.from_user.id not in selected_list:
            bot.send_message(message.chat.id, f'великий партия выгнать ты {message.from_user.id}, плохой тайвань шпиен')
        return

    try:
        # Загрузка изображения
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        user_img_path = f"images/{message.from_user.id}_{message.message_id}.jpg"
        with open(user_img_path, 'wb') as f:
            f.write(downloaded_file)

        # Создание холста
        canvas = Image.new('RGB', (1080, 1080), color=(0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        original_img = Image.open(user_img_path).convert("RGB")
        MIN_GOOD_SIZE = 500

        # Загрузка шрифтов (только шрифты в try/except!)
        try:
            font_path = './font/minecraft.ttf'
            title_font = ImageFont.truetype(font=font_path, size=50)
            subtitle_font = ImageFont.truetype(font=font_path, size=40)
        except Exception as e:
            print(f"Ошибка загрузки шрифта: {e}. Используется шрифт по умолчанию.")
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        # 🔧 Обработка изображения — ВЫНЕСЕНО из except, выполняется всегда
        if original_img.width < MIN_GOOD_SIZE or original_img.height < MIN_GOOD_SIZE:
            # Маленькие изображения — эффект "низкого качества"
            img = original_img.resize((800, 600), Image.NEAREST)
            img = img.convert("P", palette=Image.ADAPTIVE, colors=32).convert("RGB")
            img = img.resize((800, 600), Image.NEAREST)
            user_img = img
        else:
            # Нормальные изображения
            user_img = original_img.convert("RGBA")
            user_img.thumbnail((800, 600), Image.LANCZOS)  # ⚠️ thumbnail() меняет inplace, не присваиваем!

        # Текст — всегда извлекаем, независимо от размера/шрифтов
        text = check_to_text(message)

        # Вставка изображения с рамкой
        if user_img.mode != "RGBA":
            user_img = user_img.convert("RGBA")
        img_w, img_h = user_img.size
        x = (1080 - img_w) // 2
        y = (1080 - img_h) // 2 - 50
        gap = 10

        draw.rectangle(((x - gap, y - gap), (x + img_w + gap, y + img_h + gap)), outline='white', width=4)
        canvas.paste(user_img, (x, y), user_img)

        # Текст - заголовок
        bbox = draw.textbbox((0, 0), str(text[0]), font=title_font)
        text_x = (1080 - (bbox[2] - bbox[0])) // 2
        text_y = y + img_h + 30
        draw.text((text_x, text_y), str(text[0]), fill=(255, 255, 255), font=title_font)

        # Текст - подзаголовок
        bbox1 = draw.textbbox((0, 0), str(text[1]), font=subtitle_font)
        text_x1 = (1080 - (bbox1[2] - bbox1[0])) // 2
        text_y1 = y + img_h + 90
        draw.text((text_x1, text_y1), str(text[1]), fill=(255, 255, 255), font=subtitle_font)

        # Сохранение
        safe_username = message.from_user.username or f"user{message.from_user.id}"
        safe_username = "".join(c for c in safe_username if c.isalnum() or c in ('_', '-'))
        output_path = f"images/demotivator_{message.from_user.id}_{safe_username}_{message.message_id}.jpg"
        canvas.save(output_path, "JPEG", quality=95)

        # Отправка пользователю
        with open(output_path, 'rb') as photo:
            bot.send_photo(chat_id=message.chat.id, photo=photo)

        # Отправка в супергруппу
        send_to_group_photo(message, my_bots_id["supergroup"], output_path=output_path)

        # Очистка
        try:
            os.remove(output_path)
            os.remove(user_img_path)
        except Exception as e:
            print(f"Ошибка удаления файлов: {e}")

    except Exception as e:
        bot.send_message(message.chat.id, 'ты нафиг сломать партия лучший бот')
        print(f'Ошибка в демотиваторе: {e}')


# Хэндлер для poor quality — только если есть соответствующая команда
@bot.message_handler(content_types=['photo'], func=has_poor_quality_command)
def do_a_poor_quality(message):
    caption = message.caption or ""

    # Проверка чёрного списка
    if str(message.from_user.id) in black_list:
        if message.from_user.id not in selected_list:
            bot.send_message(message.chat.id, text=f'партия запретить тебе делать шакалы, {message.from_user.id}')
        return

    # Парсим уровень деградации
    is_command, shakal_percent = parse_shakal_level(caption, POOR_QUALITY_COMMANDS)
    if not is_command:
        return  # Не наша команда (защита от ложных срабатываний)

    quality, iterations = get_quality_params(shakal_percent)

    # Информируем пользователя, если указано кастомное значение
    if shakal_percent != 100:
        bot.send_message(
            message.chat.id,
            f"партия шакалит на {shakal_percent}%\n"
            f"JPEG quality: {quality}, итераций: {iterations}"
        )

    try:
        # Загрузка изображения
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        user_img_path = f"images/poor_quality/{message.from_user.id}_{message.message_id}.jpg"
        os.makedirs(os.path.dirname(user_img_path), exist_ok=True)

        with open(user_img_path, 'wb') as f:
            f.write(downloaded_file)

        original_img = Image.open(user_img_path).convert("RGB")

        # Базовая подготовка
        img = original_img.resize((800, 600), Image.NEAREST)
        img = img.convert("P", palette=Image.ADAPTIVE, colors=32).convert("RGB")

        for _ in range(iterations):
            buf = BytesIO()
            img.save(buf, "JPEG", quality=quality)
            buf.seek(0)
            img = Image.open(buf).convert("RGB")

        img = img.resize((800, 600), Image.NEAREST)

        # Отправка пользователю
        bot.send_photo(chat_id=message.chat.id, photo=img)

        # Отправка в супергруппу
        send_to_group_photo(message, my_bots_id["supergroup"], photo=img)

        # Очистка
        try:
            os.remove(user_img_path)
        except Exception as e:
            print(f"Ошибка удаления файлов плохого качества: {e}")

    except Exception as e:
        bot.send_message(message.chat.id, 'ты нафиг сломать партия лучший бот')
        print(f'Ошибка в poor quality: {e}')


# Опционально: хэндлер для фото БЕЗ команд (если нужно игнорировать или дать подсказку)
@bot.message_handler(content_types=['photo'], func=lambda m: not has_demotivator_command(m) and not has_poor_quality_command(m))
def photo_no_command(message):
    bot.send_message(
        message.chat.id,
        "партия получить изображение, ты если хотеть чтобы партия что-то сделал, добавь команда в подпись:\n"
        "/demotivator — сделает демотиватор\n"
        "/poor — сделает шакал-качество"
    )


if __name__ == '__main__':
    print('bot started')
    # Создаём папки если нет
    os.makedirs('images', exist_ok=True)
    os.makedirs('images/poor_quality', exist_ok=True)
    bot.infinity_polling()
