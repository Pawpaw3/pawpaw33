import os
import telebot
from flask import Flask, request
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, concatenate_videoclips
import time

TOKEN = '6875281030:AAHfvPNS8LQ0nr7baA1oaFaRcqxyYqB290w'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Максимальные ширина и высота видео-сообщения
MAX_WIDTH = 640
MAX_HEIGHT = 640

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне видео, и я преобразую его в круглое видео на белом фоне.")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    try:
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        input_path = 'temp_video.mp4'
        with open(input_path, 'wb') as video_file:
            video_file.write(downloaded_file)

        output_path = process_video_to_circle(input_path)

        if output_path:
            # Изменяем размер видео
            resized_output_path = resize_video(output_path, MAX_WIDTH, MAX_HEIGHT)
            # Объединяем аудио из оригинального видео и измененного видео
            final_output_path = merge_audio(input_path, resized_output_path)
            with open(final_output_path, 'rb') as video_note:
                bot.send_video_note(message.chat.id, video_note, reply_to_message_id=message.message_id)

            # Удаляем временные файлы
            safe_delete_file(input_path)
            safe_delete_file(output_path)
            safe_delete_file(resized_output_path)
            safe_delete_file(final_output_path)

    except Exception as e:
        bot.reply_to(message, f'Произошла ошибка: {e}')

def process_video_to_circle(input_path):
    clip = VideoFileClip(input_path)
    min_dimension = min(clip.size)
    clip_cropped = clip.crop(width=min_dimension, height=min_dimension, x_center=clip.size[0] // 2,
                             y_center=clip.size[1] // 2)
    circle_clip = clip_cropped.fl_image(make_frame_circle_with_border)
    output_path = 'output_circle_video.mp4'
    circle_clip.write_videofile(output_path, codec='libx264')
    return output_path

def make_frame_circle_with_border(frame):
    h, w = frame.shape[:2]
    center = (w // 2, h // 2)
    radius = min(center[0], center[1])  # Максимальный радиус в пределах видео
    mask = np.zeros((h, w), np.uint8)
    cv2.circle(mask, center, radius, 255, thickness=-1)
    circular_frame = cv2.bitwise_and(frame, frame, mask=mask)
    white_background = np.ones_like(frame) * 255  # Белый фон
    circular_frame_with_border = cv2.bitwise_and(white_background, white_background, mask=~mask)
    circular_frame_with_border += circular_frame
    return circular_frame_with_border

def resize_video(input_path, target_width, target_height):
    clip = VideoFileClip(input_path)
    resized_clip = clip.resize((target_width, target_height))
    resized_output_path = 'resized_video.mp4'
    resized_clip.write_videofile(resized_output_path, codec='libx264', audio=False)
    return resized_output_path

def merge_audio(original_video_path, resized_video_path):
    original_clip = VideoFileClip(original_video_path)
    resized_clip = VideoFileClip(resized_video_path)
    final_clip = resized_clip.set_audio(original_clip.audio)
    final_output_path = 'final_video.mp4'
    final_clip.write_videofile(final_output_path, codec='libx264')
    return final_output_path

def safe_delete_file(file_path):
    """Пытается безопасно удалить файл, повторяя попытку при необходимости."""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                break
        except Exception as e:
            print(f"Не удалось удалить файл {file_path}: {e}, попытка {attempt + 1}")
            time.sleep(1)  # Задержка перед следующей попыткой

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://<your-domain>/' + TOKEN)
    return "!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
