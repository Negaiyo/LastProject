import telebot
import moviepy.editor as mp
import os
from config import BOT_TOKEN
import time

bot = telebot.TeleBot(BOT_TOKEN)

users_data = {}


def clean_up(*file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)

@bot.message_handler(commands=['help'])
def send_help(message):
    user_name = message.from_user.first_name if message.from_user.first_name else "пользователь"
    help_text = (
        f"Привет, {user_name}! 🙌\n"
        "Здесь ты можешь преобразовать свои видео в видеокружки! 🎥➡️🔵\n\n"
        "Отправляй мне любое видео, и я создам из него кружок. Но видео должно быть не более минуты.  "
        "Видеокружок Не будет создан, из-за ограничений Telegram ⏱\n\n"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name if message.from_user.first_name else "пользователь"
    if message.from_user.id not in users_data:
        users_data[message.from_user.id] = {'username': message.from_user.username}
    bot.reply_to(message, f'Привет, {user_name}! Отправь мне видео, и я конвертирую его в видеокружок.')

@bot.message_handler(content_types=['video'])
def handle_video(message):
    start_message_time = time.time()  # Время начала отправки сообщения
    if message.video.duration > 60:
        bot.reply_to(message, "Видео не должно длиться более 60 секунд!")
        return

    file_id = message.video.file_id
    video_file_path = f'video_{file_id}.mp4'
    video_note_path = f'video_note_{file_id}.mp4'
    
    try:
        msg_download = bot.send_message(message.chat.id, 'Скачиваю видео... ⏳')
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open(video_file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.delete_message(chat_id=message.chat.id, message_id=msg_download.message_id)
        upload_time = round(time.time() - start_message_time, 2)  # Вычисляем время загрузки видео на сервер

        msg_convert = bot.send_message(message.chat.id, 'Конвертирую видео в кружок... 🔄')
        
        start_time = time.time()  # Время начала обработки видео
        
        input_video = mp.VideoFileClip(video_file_path)
        w, h = input_video.size
        circle_size = 360
        aspect_ratio = float(w) / float(h)
        
        if w > h:
            new_w = int(circle_size * aspect_ratio)
            new_h = circle_size
        else:
            new_w = circle_size
            new_h = int(circle_size / aspect_ratio)
            
        resized_video = input_video.resize((new_w, new_h))
        output_video = resized_video.crop(x_center=resized_video.w/2, y_center=resized_video.h/2, width=circle_size, height=circle_size)
        output_video.write_videofile(video_note_path, codec='libx264', audio_codec='aac', bitrate='5M')
        
        processing_time = round(time.time() - start_time, 2)  # Вычисляем время обработки видео
        bot.delete_message(chat_id=message.chat.id, message_id=msg_convert.message_id)
        send_time = round(time.time() - start_message_time - processing_time, 2)  # Время отправки с пк

        with open(video_note_path, 'rb') as video:
            sent_message = bot.send_video_note(message.chat.id, video, duration=message.video.duration)
        
        processing_message = f'Время загрузки: {upload_time} сек. ⏳\nВремя обработки: {processing_time} сек. ⏱\nВремя отправки: {send_time} сек. 📤'
        bot.send_message(message.chat.id, processing_message, reply_to_message_id=sent_message.message_id)
        
    except Exception as e:
        bot.reply_to(message, 'Произошла ошибка при обработке вашего видео 😥. Возможно вес видео большой.Пришлите пожалуйста другое видео, или пришлите это видео с соотношением 1:1')
        print(e)
    finally:
        clean_up(video_file_path, video_note_path)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "Извините, Вы прислали фотографию, пожалуйста пришлите видео для конвертации. 😕")


bot.infinity_polling()
