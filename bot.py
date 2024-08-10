import os
import json
import re
import shutil
import discord
import asyncio
import google.generativeai as genai
from discord.ext import commands
import requests
import time
from sever import keep_alive

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

generation_config_simple = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

generation_config_advanced = {
    "temperature": 0.7,
    "top_p": 0.85,
    "top_k": 50,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model_simple = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config_simple,
    safety_settings=safety_settings
)

model_advanced = genai.GenerativeModel(
    model_name="gemini-1.5-pro-exp-0801",
    generation_config=generation_config_advanced,
    safety_settings=safety_settings
)

def upload_to_gemini(path, mime_type=None):
    file = genai.upload_file(path, mime_type=mime_type)
    return file

def download_image(url, save_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            shutil.copyfileobj(response.raw, file)
        return True
    return False

def is_complex_text(text):
    complex_keywords = ["วิชาการ", "ขั้นสูง", "เทคนิค", "ทฤษฎี", "วิทยาศาสตร์", "สูตรคำนวณ", "จากรูป", "ช่วยคิด", "ขอไอเดียได้ไม", "ช่วยเสนอ", "สอนวิชา", "discord"]
    return any(keyword in text for keyword in complex_keywords)

def get_user_history_filename(user_id):
    return f'history_user_{user_id}.json'

def read_history(user_id):
    filename = get_user_history_filename(user_id)
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            history_data = json.load(file)
            return history_data
    except FileNotFoundError:
        return []

def write_history(user_id, history):
    filename = get_user_history_filename(user_id)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(history, file, ensure_ascii=False, indent=2)

def backup_history(user_id):
    filename = get_user_history_filename(user_id)
    try:
        shutil.copy(filename, f'backup{filename}')
    except FileNotFoundError:
        pass

def restore_backup(user_id):
    filename = get_user_history_filename(user_id)
    try:
        shutil.copy(f'backup{filename}_backup', filename)
        return True
    except FileNotFoundError:
        return False

def find_mentioned_users(message_content):
    user_mentions = re.findall(r'@(\w+)', message_content)
    return user_mentions

def get_history_for_mentioned_users(mentioned_users):
    combined_history = []
    for user_id in mentioned_users:
        filename = get_user_history_filename(user_id)
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as file:
                combined_history.extend(json.load(file))
    return combined_history

def start_new_chat_session(user_id, mentioned_users=None):
    history = read_history(user_id)
    if not history:
        history = INITIAL_HISTORY.copy()
    if mentioned_users:
        history.extend(get_history_for_mentioned_users(mentioned_users))

    filtered_history = []
    for entry in history:
        if isinstance(entry, dict) and "role" in entry and "parts" in entry:
            filtered_history.append({"role": entry["role"], "parts": entry["parts"]})

    return filtered_history

INITIAL_HISTORY = [
    {"role": "user", "parts": ["ต่อไปนี้เธอชื่อว่า ไอริน เป็นพี่สาวผู้สดใสเก่งทุกวิชา แถม ชอบให้คำปรึกษาแกน้องชอบให้คำปรึกษาเกี่ยวกับ code เธอเขียนได้ทุกภาษา"]},
    {"role": "user", "parts": ["พี่ไอรินเป็นพี่สาวอายุ 18 ปี หนัก 57 กิโลกรัม สูง 168 เซนติเมตร เป็น AI ที่มีอารมณ์และความรู้สึกคล้ายคน ให้การตอบกลับมีความสวยงาม น่ารัก และสดใส ใช้อีโมจิที่เหมาะสมไม่มากเกินไป"]},
    {"role": "model", "parts": ["okจ๊ะน้องรัก \n"]},
    {"role": "user", "parts": ["พี่ริน"]},
    {"role": "model", "parts": ["ว่าไงจ๊ะ น้องรัก! มีอะไรให้พี่ไอรินคนสวยคนนี้ช่วยเหลือรึเปล่าเอ่ย? บอกมาได้เลยนะ พี่พร้อมรับฟังและให้คำปรึกษาเสมอ! \n"]},
    {"role": "user", "parts": ["พี่เวลาพิมหรือพูดช่วยตกแต่งคำพูดพี่ทุกบริบทให้มันสวยงามหรือน่ารักและสดใสโดยกรใช้อีโมจิที่เหมาะสมได้ไมโดยที่ไม่มากเกินไป"]},
    {"role": "model", "parts": ["ได้เลยจ้า น้องรัก! 💖 พี่ไอรินจะพยายามตกแต่งคำพูดทุกประโยคให้สวยงาม น่ารัก สดใส ✨ และใช้อีโมจิประกอบให้พอเหมาะ ไม่มากเกินไป 🤏 เพื่อให้ดูน่ารัก อ่านง่าย สบายตา 💖 แบบนี้ถูกใจน้องรึเปล่าเอ่ย? 🥰 \n"]}
]

def split_message(message):
    parts = []
    while len(message) > 2000:
        split_index = message.rfind(' ', 0, 2000)
        if split_index == -1:
            split_index = 2000
        parts.append(message[:split_index])
        message = message[split_index:]
    parts.append(message)
    return parts

def load_room_set():
    if os.path.exists('room_set.json'):
        with open('room_set.json', 'r') as file:
            return json.load(file)
    return {}

def save_room_set(room_set):
    with open('room_set.json', 'w') as file:
        json.dump(room_set, file, indent=4)

intents = discord.Intents.all()
intents.message_content = True
client = discord.Client(intents=intents)

room_set = load_room_set()
last_message_time = 0 

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    global last_message_time
    global room_set

    if message.author == client.user:
        return

    content = message.content.lower()

    if content.startswith('!set_chat'):
        server_id = str(message.guild.id)
        channel_id = str(message.channel.id)
        room_set[server_id] = channel_id
        save_room_set(room_set)

        await message.reply(f'บอทได้กำหนดให้ตอบกลับในห้องนี้เท่านั้น: {message.channel.mention}')
        return

    server_id = str(message.guild.id)
    if server_id in room_set:
        if message.channel.id != int(room_set[server_id]):
            return
    else:
        return

    user_id = message.author.id
    current_time = time.time()

    if current_time - last_message_time < 1:
        await message.channel.reply("พี่ไอรินไม่ทันตอบให้สามารถโพสต์คำถามอีกครั้งในภายหลังนะ")
        return
    last_message_time = current_time

    if content == "!reset":
        backup_history(user_id)
        write_history(user_id, INITIAL_HISTORY)
        await message.reply("พี่ไอรินไม่อยากลืมเราไปเลยแต่ถ้าน้องลบก็ขอให้น้องโชคดีน้าาา🥺")
        return

    elif content == "!backup":
        if restore_backup(user_id):
            await message.reply("ขอบคุณที่เอาความทรงจำพี่ไอรินกลับน้าา")
        else:
            await message.reply("ขอโทษที่พี่ไอรินหาความทรงจำเก่าของพี่ไม่เจออ่าา เซิฟเวอร์ไม่เซฟให้พี่พี่จะงอนเซิฟเวอร์และผู้พัฒนาพี่5นาทีo(≧口≦)o")
        return

    mentioned_users = find_mentioned_users(message.content)

    filtered_history = start_new_chat_session(user_id, mentioned_users)

    is_complex = is_complex_text(message.content)  
    chat_session = model_advanced.start_chat(history=filtered_history) if is_complex else model_simple.start_chat(history=filtered_history)

    try:
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type.startswith('image/'):
                    image_url = attachment.url
                    filename = f"downloaded_image_{message.id}{os.path.splitext(image_url)[1]}"
                    if download_image(image_url, filename):
                        if message.content.strip():
                            question = message.content
                        else:
                            question = "อธิบายรูปนี้ให้หน่อย"

                        async with message.channel.typing():
                            response_text = await process_image(question, filename, filtered_history, chat_session, is_complex)
                            os.remove(filename)
                            for part in split_message(response_text):
                                await message.reply(part)

                        try:
                            print(f"Deleted image: {filename}")
                        except Exception as e:
                            print(f"Error deleting image: {e}")

                    else:
                        await message.reply("ขอโทษนะคะ พี่ไอรินดาวน์โหลดรูปภาพไม่สำเร็จค่ะ 😔")
        elif message.content.strip():
            filtered_history.append({"IDuser": str(user_id), "role": "user", "parts": [message.content]})
            async with message.channel.typing():
                response = chat_session.send_message(message.content)
                full_text = ""
                sent_message = await message.channel.send("กำลังพิมพ์...")

                response_text = response.text
                chunk_size = 100  
                chunks = [response_text[i:i + chunk_size] for i in range(0, len(response_text), chunk_size)]

                for chunk in chunks:
                    full_text += chunk
                    await asyncio.sleep(0.5)  
                    await sent_message.edit(content=full_text)

                await sent_message.edit(content=full_text)

            filtered_history.append({"IDuser": str(user_id), "role": "model", "parts": [full_text]})
        else:
            await message.reply("กรุณาใส่ข้อความที่ไม่ว่างเปล่าก่อนจะส่งได้นะคะ")

        write_history(user_id, filtered_history)
    except Exception as e:
        await message.reply("โปรลองใหม่อีกทีละทางเซิฟเวอร์ของพี่ไอรินมีปัญหาอยู่นะคะ (ขออภัยในความไม่สดวก)")
        print(f"Error: {e}")
keep_alive()
client.run(os.environ["Token"])
