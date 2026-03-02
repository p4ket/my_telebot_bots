import telebot
from PIL import Image, ImageDraw, ImageFont
import os
from io import BytesIO
from html import escape
import regex

# ==================== КОНФИГУРАЦИЯ ====================
with open('info/token', 'r', encoding='utf-8') as f:
    TOKEN_LINES = f.readlines()
    BOT_TOKEN = TOKEN_LINES[0].strip()

bot = telebot.TeleBot(BOT_TOKEN)

# Списки команд
DEMOTIVATOR_COMMANDS = ['/make_demotivator', '/demotivator', '/dm']
POOR_QUALITY_COMMANDS = ['/do_a_poor_quality', '/poor', '/pq']
STICKER_COMMANDS = ['/make_sticker', '/sticker', '/st']

# ID админов и чёрный список
ADMIN_LIST = ['6555912810', '5081309603', '8204500319']
BLACK_LIST = ['7167194461', '8581093935', '-1003754441670']
SELECTED_LIST = ['777000']

# ID для отправки в супергруппу
MY_BOTS_ID = {
    "test_bot": '8205691540',
    "admin_info": '8213882036',
    "supergroup": '-1003637655262'
}

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_user_info(message):
    """Безопасно получает данные о пользователе"""
    if message.from_user:
        uid = message.from_user.id
        uname = message.from_user.username or f"user_{uid}"
        fname = message.from_user.first_name or "User"
    else:
        uid = message.chat.id
        uname = message.chat.username or "channel"
        fname = message.chat.title or "Channel"
    return uid, uname, fname


def check_access(message):
    """Проверка на чёрный список"""
    uid, _, _ = get_user_info(message)
    if str(uid) in BLACK_LIST:
        if str(uid) not in SELECTED_LIST:
            return False
    return True


def is_private_chat(message):
    """Проверяет, является ли чат личным сообщением"""
    return message.chat.type == 'private'


def has_command(message, cmd_list):
    """Проверяет наличие команды в тексте или подписи"""
    caption = message.caption or ""
    text = message.text or ""
    return any(cmd in caption or cmd in text for cmd in cmd_list)


def cleanup_chat(message, bot_messages_to_delete=None):
    """
    Удаляет исходное сообщение пользователя и служебные сообщения бота.
    Бот должен быть администратором с правом удаления сообщений.
    """
    try:
        # Удаляем оригинальное сообщение пользователя
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

        # Удаляем служебные сообщения бота
        if bot_messages_to_delete:
            for msg_id in bot_messages_to_delete:
                try:
                    bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
                except Exception as e:
                    print(f"Не удалось удалить сообщение бота {msg_id}: {e}")
    except Exception as e:
        print(f"⚠️ Не удалось очистить чат (бот должен быть админом): {e}")


def send_to_group_photo(message, group_id, output_path=None, photo=None):
    """Отправка результата в супергруппу"""
    try:
        uid, uname, fname = get_user_info(message)
        user_id = escape(str(uid))
        username = uname or ""

        caption = (
            f"User ID: <code>{user_id}</code>\n"
            f"User Name: <a href='t.me/{username}'>{message.from_user.first_name}</a>"
        )

        if output_path is not None:
            with open(output_path, 'rb') as photo_file:
                bot.send_photo(chat_id=group_id, photo=photo_file, caption=caption, parse_mode='HTML')
        if photo is not None:
            if isinstance(photo, str):
                with open(photo, 'rb') as photo_file:
                    bot.send_photo(chat_id=group_id, photo=photo_file, caption=caption, parse_mode='HTML')
            else:
                bot.send_photo(chat_id=group_id, photo=photo, caption=caption, parse_mode='HTML')
    except Exception as e:
        print(f"Ошибка отправки в супергруппу: {e}")


def check_to_emoji(message, default="👍"):
    """Извлекает эмодзи из подписи"""
    try:
        caption = message.caption or ""
        emoji_pattern = regex.compile(r"\p{Emoji}")
        matches = emoji_pattern.findall(caption)
        return "".join(matches[:20]) if matches else default
    except:
        return default


def get_emojis_for_api(emojis_string, max_count=20):
    """Конвертирует строку эмодзи в список для Telegram API"""
    if not emojis_string:
        return ["👍"]
    emoji_pattern = regex.compile(r"\p{Emoji}")
    emoji_list = emoji_pattern.findall(emojis_string)
    result = emoji_list[:max_count]
    return result if result else ["👍"]


def prepare_static_sticker(in_path, out_path):
    """Конвертирует изображение в формат стикера Telegram"""
    with Image.open(in_path) as img:
        img = img.convert("RGBA")
        img.thumbnail((512, 512), Image.LANCZOS)
        bg = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        bg.paste(img, ((512 - img.width) // 2, (512 - img.height) // 2), img)
        bg.save(out_path, "PNG", optimize=True)

        # Сжатие если файл > 512 KB
        max_size_kb = 512
        if os.path.getsize(out_path) > max_size_kb * 1024:
            for quality in [95, 85, 75, 65]:
                bg.save(out_path, "PNG", optimize=True, compress_level=quality)
                if os.path.getsize(out_path) <= max_size_kb * 1024:
                    break


def check_to_text(message):
    """Обработка текста из подписи для демотиватора"""
    caption = message.caption if message.caption else ""
    commands_list = DEMOTIVATOR_COMMANDS + POOR_QUALITY_COMMANDS + STICKER_COMMANDS

    clean_caption = caption
    for cmd in commands_list:
        clean_caption = clean_caption.replace(cmd, '').strip()

    text = [line.strip() for line in clean_caption.split('\n') if line.strip()]

    if len(text) >= 2:
        title, subtitle = text[0], text[1]
        if len(title) > 30:
            title = 'too many letters'
            # Отправляем предупреждение только в ЛС
            if is_private_chat(message):
                bot.send_message(message.chat.id, 'brooo, too many letters in first line...... ((((')
        if len(subtitle) > 50:
            subtitle = 'too many letters'
            # Отправляем предупреждение только в ЛС
            if is_private_chat(message):
                bot.send_message(message.chat.id, 'brooo, too many letters in second line...... ((((')
        return [title, subtitle]
    elif len(text) == 1 and text[0]:
        title = text[0]
        if len(title) > 30:
            title = 'too many letters'
            # Отправляем предупреждение только в ЛС
            if is_private_chat(message):
                bot.send_message(message.chat.id, 'brooo, too many letters in first line...... ((((')
        return [title, '  ']
    else:
        return ['', '']


def parse_shakal_level(caption, commands_list):
    """Извлекает уровень деградации из подписи"""
    if not caption:
        return False, None

    found_cmd = None
    for cmd in commands_list:
        if cmd in caption:
            found_cmd = cmd
            parts = caption.replace(cmd, '', 1).strip().split()
            break

    if not found_cmd:
        return False, None

    if parts:
        num_str = parts[0].rstrip('%')
        if num_str.lstrip('-').isdigit():
            level = int(num_str)
            level = max(0, min(100, level))
            return True, level

    return True, 100


def get_quality_params(percent):
    """Конвертирует процент в параметры JPEG-деградации"""
    percent = max(0, min(100, percent))
    quality = max(1, 95 - int(percent * 0.94))
    iterations = max(1, int(percent))
    return quality, iterations





# ==================== ХЭНДЛЕРЫ ====================
# ==================== ХЭНДЛЕРЫ ====================
# ==================== ХЭНДЛЕРЫ ====================
# ==================== ХЭНДЛЕРЫ ====================
# ==================== ХЭНДЛЕРЫ ====================
# ==================== ХЭНДЛЕРЫ ====================




@bot.message_handler(commands=['start'])
def start(message):
    if check_access(message):
        try:
            try:
                if str(message.from_user.id) not in open('info/users.txt', 'r').readlines():
                    with open('info/users.txt', 'w') as users:
                        users.write(str(message.from_user.id))
                print("succesfully writed user's id to users.txt")
            except Exception as e:
                print(f'Error with write user id to file: {e}')


            uid, uname, fname = get_user_info(message)
            with open('./images/templates/start_image.png', 'rb') as f:
                if uname and uname != 'None':
                    caption = f"Партия приветсвовать тебя, @{uname}! Данный бот может много чего предложить. Напиши /help для подробностей.\n(партия будет доволен, если ты подаришь звезда и зайдешь в канал↓↓↓)\nhttps://t.me/+r2p3l1QPGMM0Nzcy"
                else:
                    caption = f"Партия приветсвовать тебя, незнакомец! Данный бот может много чего предложить. Напиши /help для подробностей.\n(↓↓↓партия будет доволен, если ты подаришь звезда и зайдешь в канал↓↓↓)\nhttps://t.me/+r2p3l1QPGMM0Nzcy"
                bot.send_photo(message.chat.id, f, caption=caption)
        except Exception as e:
            bot.send_message(message.chat.id, "Ошибка загрузки стартового изображения")
            print(f"Start error: {e}")
    else:
        if str(message.from_user.id) not in SELECTED_LIST:
            bot.send_message(message.chat.id, f'Великий партия выгнать ты {message.from_user.id}, плохой тайвань шпиен.')


@bot.message_handler(commands=['help', 'h', '?'])
def help_command(message):
    if not check_access(message):
        if str(message.from_user.id) not in SELECTED_LIST:
            bot.send_message(message.chat.id, 'Партия запретить тебе смотреть /help.')
        return

    help_text = (
        "📜 **Команды партии:**\n\n"
        "🖼️ **Демотиватор:**\n"
        "`/demotivator`, `/dm`, `/make_demotivator` — создать демотиватор\n"
        "Текст в подписи к фото (2 строки)\n\n"
        "🗑️ **Шакал-качество:**\n"
        "`/poor`, `/pq`, `/do_a_poor_quality` [0-100%] — зашакалить изображение\n"
        "Пример: `/poor 50` или `/poor 10%`\n\n"
        "🎨 **Стикеры:**\n"
        "`/sticker`, `/st`, `/make_sticker` — создать стикер\n"
        "Эмодзи в подписи будут привязаны к стикеру\n\n"
        "🧹 **Авто-очистка:**\n"
        "Бот удаляет исходное сообщение и оставляет только результат!\n\n"
        "💬 **Режимы работы:**\n"
        "• В ЛС — бот отвечает на все сообщения\n"
        "• В группах — бот реагирует только на команды"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['info'])
def info_command(message):
    try:
        caption = f'этот бот был создан давным-давно для того, чтобы радовать людей и создателя (задоньте пж, разраб тоже есть хочет)↓↓↓\nhttps://t.me/+r2p3l1QPGMM0Nzcy'
        with open('images/templates/info_image.jpg', 'rb') as image:
            bot.send_photo(message.chat.id, photo=image, caption=caption)
    except Exception as e:
        print(f'Error with info message: {e}')

# 🔧 ТЕКСТОВЫЕ СООБЩЕНИЯ — только в ЛС
@bot.message_handler(content_types=['text'])
def echo(message):
    # Проверяем, что это НЕ команда (команды обрабатываются отдельно)
    if message.text and message.text.startswith('/'):
        return  # Пропускаем команды, они обрабатываются хэндлерами commands

    # 🔧 ОТВЕЧАЕМ НА ТЕКСТ ТОЛЬКО В ЛИЧНЫХ СООБЩЕНИЯХ
    if is_private_chat(message):
        if check_access(message):
            print(f'[ЛС] {message.text} \n@{message.from_user.username} {message.from_user.id}')
            bot.send_message(message.chat.id, 'Партия учтет твой мысль.')
        else:
            if str(message.from_user.id) not in SELECTED_LIST:
                bot.send_message(message.chat.id, f'Великий партия выгнать ты {message.from_user.id}, эхо не работать.')
            else:
                print('Сообщение от избранного.')
    # В группах/каналах — игнорируем обычный текст (только команды работают)
    else:
        print(f'[Группа/Канал] ({message.from_user.id}, {message.from_user.username}, {message.from_user.first_name}): {message.text}  ')





# ==================== ДЕМОТИВАТОР ====================
# ==================== ДЕМОТИВАТОР ====================
# ==================== ДЕМОТИВАТОР ====================
# ==================== ДЕМОТИВАТОР ====================
# ==================== ДЕМОТИВАТОР ====================
# ==================== ДЕМОТИВАТОР ====================



@bot.message_handler(content_types=['photo'], func=lambda m: has_command(m, DEMOTIVATOR_COMMANDS))
def make_demotivator(message):
    if not check_access(message):
        if str(message.from_user.id) not in SELECTED_LIST:
            bot.send_message(message.chat.id, 'Великий партия выгнать ты, плохой тайвань шпиен.')
        return

    bot_messages_to_delete = []

    try:
        uid, uname, fname = get_user_info(message)

        # Уведомление об обработке (будет удалено)
        # Отправляем только в ЛС, в группах не спамим
        if is_private_chat(message):
            temp_msg = bot.send_message(message.chat.id, "🎨 Партия делает демотиватор...")
            bot_messages_to_delete.append(temp_msg.message_id)

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        os.makedirs("images", exist_ok=True)
        user_img_path = f"images/dm_{uid}_{message.message_id}.jpg"
        with open(user_img_path, 'wb') as f:
            f.write(downloaded_file)

        canvas = Image.new('RGB', (1080, 1080), color=(0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        original_img = Image.open(user_img_path).convert("RGB")

        try:
            font_path = './font/minecraft.ttf'
            title_font = ImageFont.truetype(font=font_path, size=50)
            subtitle_font = ImageFont.truetype(font=font_path, size=40)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        if original_img.width < 500 or original_img.height < 500:
            user_img = original_img.resize((800, 600), Image.NEAREST)
        else:
            user_img = original_img.convert("RGBA")
            user_img.thumbnail((800, 600), Image.LANCZOS)

        text = check_to_text(message)

        if user_img.mode != "RGBA":
            user_img = user_img.convert("RGBA")

        img_w, img_h = user_img.size
        x = (1080 - img_w) // 2
        y = (1080 - img_h) // 2 - 50
        gap = 10

        draw.rectangle(((x - gap, y - gap), (x + img_w + gap, y + img_h + gap)), outline='white', width=4)
        canvas.paste(user_img, (x, y), user_img)

        bbox = draw.textbbox((0, 0), str(text[0]), font=title_font)
        draw.text(((1080 - (bbox[2] - bbox[0])) // 2, y + img_h + 30), str(text[0]), fill=(255, 255, 255), font=title_font)

        bbox1 = draw.textbbox((0, 0), str(text[1]), font=subtitle_font)
        draw.text(((1080 - (bbox1[2] - bbox1[0])) // 2, y + img_h + 90), str(text[1]), fill=(255, 255, 255), font=subtitle_font)

        output_path = f"images/res_dm_{uid}_{message.message_id}.jpg"
        canvas.save(output_path, "JPEG", quality=95)

        # 🧹 ОЧИСТКА перед отправкой результата (только в группах)
        if not is_private_chat(message):
            cleanup_chat(message, bot_messages_to_delete)

        # Отправка результата
        with open(output_path, 'rb') as photo:
            bot.send_photo(chat_id=message.chat.id, photo=photo)

        # Отправка в супергруппу
        send_to_group_photo(message, MY_BOTS_ID["supergroup"], output_path=output_path)

        os.remove(output_path)
        os.remove(user_img_path)

    except Exception as e:
        print(f"Demotivator Error: {e}")
        if not is_private_chat(message):
            cleanup_chat(message, bot_messages_to_delete)
        bot.send_message(message.chat.id, "❌ Партия сломалась при создании демотиватора.")






# ==================== ПООР КВАЛИТИ ====================
# ==================== ПООР КВАЛИТИ ====================
# ==================== ПООР КВАЛИТИ ====================
# ==================== ПООР КВАЛИТИ ====================
# ==================== ПООР КВАЛИТИ ====================






@bot.message_handler(content_types=['photo'], func=lambda m: has_command(m, POOR_QUALITY_COMMANDS))
def do_a_poor_quality(message):
    if not check_access(message):
        if str(message.from_user.id) not in SELECTED_LIST:
            bot.send_message(message.chat.id, 'Партия запретить тебе делать шакалы.')
        return

    bot_messages_to_delete = []
    caption = message.caption or ""

    # Получение данных пользователя
    uid, uname, fname = get_user_info(message)

    is_command, shakal_percent = parse_shakal_level(caption, POOR_QUALITY_COMMANDS)
    if not is_command:
        return

    quality, iterations = get_quality_params(shakal_percent)

    # Уведомление только в ЛС
    if shakal_percent != 100 and is_private_chat(message):
        temp_msg = bot.send_message(
            message.chat.id,
            f"🔧 Партия шакалит на {shakal_percent}%\nJPEG quality: {quality}, итераций: {iterations}"
        )
        bot_messages_to_delete.append(temp_msg.message_id)

    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        os.makedirs("images/poor_quality", exist_ok=True)
        user_img_path = f"images/poor_quality/pq_{uid}_{message.message_id}.jpg"
        with open(user_img_path, 'wb') as f:
            f.write(downloaded_file)

        original_img = Image.open(user_img_path).convert("RGB")
        img = original_img.resize((800, 600), Image.NEAREST)
        img = img.convert("P", palette=Image.ADAPTIVE, colors=32).convert("RGB")

        for _ in range(iterations):
            buf = BytesIO()
            img.save(buf, "JPEG", quality=quality)
            buf.seek(0)
            img = Image.open(buf).convert("RGB")

        img = img.resize((800, 600), Image.NEAREST)

        # 🧹 ОЧИСТКА (только в группах)
        if not is_private_chat(message):
            cleanup_chat(message, bot_messages_to_delete)

        # Отправка результата
        bot.send_photo(chat_id=message.chat.id, photo=img)

        # Отправка в супергруппу
        send_to_group_photo(message, MY_BOTS_ID["supergroup"], photo=img)

        os.remove(user_img_path)

    except Exception as e:
        print(f"Poor Quality Error: {e}")
        if not is_private_chat(message):
            cleanup_chat(message, bot_messages_to_delete)
        bot.send_message(message.chat.id, "❌ Партия не смогла зашакалить фото.")





# ==================== СТИКЕРЫ ====================
# ==================== СТИКЕРЫ ====================
# ==================== СТИКЕРЫ ====================
# ==================== СТИКЕРЫ ====================
# ==================== СТИКЕРЫ ====================
# ==================== СТИКЕРЫ ====================





@bot.message_handler(content_types=['photo'], func=lambda m: has_command(m, STICKER_COMMANDS))
def made_sticker(message):
    if not check_access(message):
        if str(message.from_user.id) not in SELECTED_LIST:
            bot.send_message(message.chat.id, 'Партия запретить тебе делать стикеры.')
        return

    bot_messages_to_delete = []
    uid, uname, fname = get_user_info(message)

    all_emojis_str = check_to_emoji(message, default="👍")
    emojis_for_api = get_emojis_for_api(all_emojis_str, max_count=20)
    emojis_display = "".join(emojis_for_api)

    # Уведомление только в ЛС
    if is_private_chat(message):
        temp_msg = bot.send_message(message.chat.id, f"🎨 Партия делает стикер с эмодзи: {emojis_display}")
        bot_messages_to_delete.append(temp_msg.message_id)

    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)

        os.makedirs("tmp", exist_ok=True)
        raw_path = f"tmp/raw_{uid}_{message.message_id}.jpg"
        png_path = f"tmp/sticker_{uid}_{message.message_id}.png"

        with open(raw_path, "wb") as f:
            f.write(downloaded)

        prepare_static_sticker(raw_path, png_path)

        bot_username = bot.get_me().username
        pack_name = f"u{uid}_stickers_by_{bot_username}"
        pack_title = f"{fname}'s stickers"

        result_text = ""
        try:
            with open(png_path, "rb") as st:
                bot.add_sticker_to_set(user_id=uid, name=pack_name, emojis=emojis_for_api, png_sticker=st)
            result_text = f"✅ Стикёр добавлен!\n📦 https://t.me/addstickers/{pack_name}\n🎨 {emojis_display}"
        except telebot.apihelper.ApiException as e:
            if "STICKERSET_INVALID" in str(e) or "not found" in str(e).lower():
                with open(png_path, "rb") as st:
                    bot.create_new_sticker_set(
                        user_id=uid,
                        name=pack_name,
                        title=pack_title,
                        emojis=emojis_for_api,
                        png_sticker=st,
                        sticker_format="static"
                    )
                result_text = f"✨ Пак создан!\n📦 https://t.me/addstickers/{pack_name}\n🎨 {emojis_display}"
            elif "STICKERS_TOO_MUCH" in str(e):
                result_text = "📦 В паке максимум 120 стикеров! Удали старые или создай новый пак."
            else:
                result_text = f"❌ Ошибка: {e}"

        # 🧹 ОЧИСТКА (только в группах)
        if not is_private_chat(message):
            cleanup_chat(message, bot_messages_to_delete)

        # Отправка результата
        bot.send_message(message.chat.id, result_text)

        os.remove(raw_path)
        os.remove(png_path)

    except Exception as e:
        print(f"Sticker Error: {e}")
        if not is_private_chat(message):
            cleanup_chat(message, bot_messages_to_delete)
        bot.send_message(message.chat.id, "❌ Ошибка стикера.")



# ==================== ФОТО БЕЗ КОМАНД ====================
# ==================== ФОТО БЕЗ КОМАНД ====================
# ==================== ФОТО БЕЗ КОМАНД ====================
# ==================== ФОТО БЕЗ КОМАНД ====================



@bot.message_handler(
    content_types=['photo'],
    func=lambda m: not has_command(m, DEMOTIVATOR_COMMANDS) and
                   not has_command(m, POOR_QUALITY_COMMANDS) and
                   not has_command(m, STICKER_COMMANDS)
)
def photo_no_command(message):
    # Отвечаем на фото без команд ТОЛЬКО в ЛС
    if is_private_chat(message) and check_access(message):
        bot.send_message(
            message.chat.id,
            "📸 Партия получить изображение!\n\n"
            "Чтобы партия что-то сделал, добавь команду в подпись:\n"
            "/demotivator — сделает демотиватор\n"
            "/poor [0-100%] — сделает шакал-качество\n"
            "/sticker — сделает стикер"
        )
    # В группах игнорируем фото без команд


# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    print('@editor_theyablo4ko_bot запущен, лс-все, канал-ограниченные')
    os.makedirs('images', exist_ok=True)
    os.makedirs('images/poor_quality', exist_ok=True)
    os.makedirs('images/templates', exist_ok=True)
    os.makedirs('tmp', exist_ok=True)
    bot.infinity_polling()





