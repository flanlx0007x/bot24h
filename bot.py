import os
import shutil
import requests
import discord
import asyncio
import json
import random
import string
from PIL import Image
from discord.ext import commands, tasks
import google.generativeai as genai
from sever import keep_alive

# Configure API key
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# Function to generate random string
def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

# Function to upload image to Gemini
def upload_to_gemini(path, mime_type=None):
    file = genai.upload_file(path, mime_type=mime_type)
    return file

# Function to download image from URL
def download_image(url, save_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            shutil.copyfileobj(response.raw, file)
        return True
    return False

# Function to process image with AI model
async def process_image(question, file_path, conversation_history):
    try:
        # Upload image to Gemini
        files = [upload_to_gemini(file_path, mime_type="image/jpeg")]

        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config,
        )

        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        files[0],
                        f"{question}",
                    ],
                },
                {
                    "role": "model",
                    "parts": [
                        " \n",
                    ],
                },
            ]
        )

        response = chat_session.send_message(question)
        response_text = response.text
        conversation_history.append((question, response_text))
        return response_text
    except Exception as e:
        print(f"Error in process_image: {e}")
        return "An error occurred while processing the image."

# Function to show conversation history
def show_history(conversation_history, max_messages=None):
    history_output = "----- Conversation History -----\n"
    if max_messages is None:
        messages_to_show = conversation_history
    else:
        messages_to_show = conversation_history[-max_messages:]
    for index, (user_message, response) in enumerate(messages_to_show, start=1):
        history_output += f"{index}. User: {user_message}\n   Bot: {response}\n"
    history_output += "--------------------------------"
    return history_output

# Function to check if a question is a math question
def is_math_question(question):
    math_operators = ['+', '-', '*', '/', '**', '//', '%']
    words = question.split()
    return all(any(op in word for op in math_operators) for word in words)

# Function to evaluate a math expression
def eval_expression(expression):
    try:
        return eval(expression)
    except Exception as e:
        return f"Error: {e}"

# Function to get Gemini response
async def get_gemini_response(question, conversation_history):
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-latest",
            generation_config={
                "temperature": 1,
                "top_p": 0.99,
                "top_k": 0,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ],
        )
        convo = model.start_chat(history=conversation_history)
        user_message = question
        convo.send_message(user_message)
        response = convo.last.text
        conversation_history.append((user_message, response))
        return response
    except Exception as e:
        print(f"Error in get_gemini_response: {e}")
        return None

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
client = commands.Bot(command_prefix="!", intents=intents)

# Global variables
conversation_history = []

# Bot status messages
statuses = [
    "เหงา", "เบื่อหว่าา", "ขก.ทำต่อละ", "อยากกลับบ้าน", "ไม่อยากไปทำงาน",
    "กินไรดีน้า", "ติวไม่ทันแล้ว", "หลับไปเลยละกัน", "ตื่นแล้วนะ",
    "อยากกินหมูกระทะ", "ง่วงนอนจังเลย", "อยากไปเที่ยว", "บทจะเศร้าก็เศร้านะ",
    "ทำไมต้องมีวันจันทร์", "คิดถึงจังเลย", "เงินเดือนออกแล้ว", "หิวววว",
    "ร้อนจังเลยวันนี้", "วันนี้ฝนตกหนักจัง"
]

status_index = 0

# Bot status changing task
@tasks.loop(seconds=3)
async def change_status():
    global status_index
    await client.change_presence(activity=discord.Game(name=statuses[status_index]))
    status_index = (status_index + 1) % len(statuses)

# Chatbot room configuration
chatbot_rooms = {}
if os.path.exists('chatbot_rooms.json'):
    with open('chatbot_rooms.json', 'r') as file:
        chatbot_rooms = json.load(file)

@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    change_status.start()

@client.event
async def on_message(message):
    global chatbot_rooms
    global conversation_history

    if message.author == client.user:
        return

    if message.content.startswith('!ask'):
        question = message.content[len('!ask'):].strip()
        img_url = message.attachments[0].url if message.attachments else None

        temp_image_path = "temp_image.jpg"
        if img_url and download_image(img_url, temp_image_path):
            # Process image with AI model
            processed_response = await process_image(question, temp_image_path, conversation_history)
            await message.channel.send(f"{processed_response}")

            # Save the processed image as 'test.jpg'
            shutil.copy(temp_image_path, "test.jpg")

            # Clean up: Delete temporary image
            os.remove(temp_image_path)
        else:
            await message.channel.send(f"Failed to download image from {img_url}")

    elif message.content.startswith('!Gen'):
        try:
            _, count_str = message.content.split(maxsplit=1)
            count = int(count_str)
        except ValueError:
            await message.channel.send("Usage: !Gen <number>")
            return

        if count <= 0:
            await message.channel.send("Please specify a positive number.")
            return

        urls = []
        for _ in range(count):
            random_string = generate_random_string(32)
            new_url = f"https://gift.truemoney.com/campaign/?v={random_string}"
            urls.append(new_url)

        embed = discord.Embed(title=f"Generated อังเปา(มันแค่สุ่ม) {count} URLs", color=discord.Color.green())

        for index, url in enumerate(urls):
            embed.add_field(name=f"ลิงค์อังเปา {index + 1}", value=url, inline=False)

        try:
            await message.author.send(embed=embed)
            await message.reply(f"Successfully generated {count} URLs and sent them to your DMs.", mention_author=False)
            return
        except discord.errors.Forbidden:
            await message.reply("I couldn't send you a DM. Please make sure you allow DMs from server members.", mention_author=False)
            return

    elif message.content.startswith('Clear_history'):
        conversation_history = []
        await message.reply("ได้ทำการล้างประวัติการสอบถามและตอบกลับแล้ว:✅")
        return

    elif message.content.startswith('Show_history'):
        full_history_text = show_history(conversation_history)
        await message.channel.send(full_history_text)
        return  

    elif message.content.startswith('status'):
        if isinstance(message.channel, discord.TextChannel) and isinstance(message.guild, discord.Guild):
            guild = message.guild

            embed = discord.Embed(
                title="Status",
                description="",
                color=discord.Color.green()
            )

            embed.set_image(url="https://i.gifer.com/7eg0.gif")

            response_message = await message.reply(embed=embed)
            await asyncio.sleep(3.5)
            embed.set_image(url="")
            embed.add_field(name="Bot Version", value="1.5.0-beta", inline=False)
            await response_message.edit(embed=embed)
            await asyncio.sleep(0.5)
            embed.add_field(name="Developer", value="<@862571604751810602>", inline=False)
            await response_message.edit(embed=embed)
            embed.add_field(name="Status", value="🟢", inline=False)
            await asyncio.sleep(0.5)
            await response_message.edit(embed=embed)
            embed.add_field(name="work", value="🟢", inline=False)
            await asyncio.sleep(0.5)
            await response_message.edit(embed=embed)
            embed.add_field(name="fix/creating", value="🟡", inline=False)
            await asyncio.sleep(0.5)
            await response_message.edit(embed=embed)
            embed.add_field(name="Not working", value="🔴", inline=False)
            await asyncio.sleep(0.5)
            await response_message.edit(embed=embed)
            embed.add_field(name="Online24/7", value="🟢", inline=False)
            await asyncio.sleep(0.5)
            await response_message.edit(embed=embed)
            embed.add_field(name="Image processing", value="🟢", inline=False)
            await asyncio.sleep(0.5)
            await response_message.edit(embed=embed)
            embed.add_field(name="Process PDF files or others", value="🔴", inline=False)
            await asyncio.sleep(0.5)
            await response_message.edit(embed=embed)
            embed.add_field(name="Status Developer", value="ขก.ทำต่อละโว้ย / Too lazy to continue developing", inline=False)
            await asyncio.sleep(0.5)
            await response_message.edit(embed=embed)
            embed.add_field(name="About the Developer", value="Name: Frank", inline=False)
            await asyncio.sleep(0.5)
            await response_message.edit(embed=embed)
            embed.add_field(name="", value="Age: 14", inline=False)
            await asyncio.sleep(0.5)
            await response_message.edit(embed=embed)
            embed.add_field(name="", value="Gender: Boy", inline=False)
            await asyncio.sleep(0.5)
            await response_message.edit(embed=embed)
            embed.add_field(name="Discord", value="https://discord.gg/HN7Szyw8", inline=False)
            await asyncio.sleep(0.5)
            await response_message.edit(embed=embed)
            member_count = len(guild.members)
            channel_count = len(guild.channels)
            await asyncio.sleep(0.5)
            embed.add_field(name=f"{guild.name}", value=f"Member Count: {member_count}", inline=False)
            await asyncio.sleep(0.5)
            await response_message.edit(embed=embed)
            embed.add_field(name=f"{guild.name}", value=f"Channel Count: {channel_count}", inline=False)
            bot_ping = round(client.latency * 1000) 

            await asyncio.sleep(0.5)
            await response_message.edit(embed=embed)
            embed.add_field(name="Bot Ping", value=f"{bot_ping} ms", inline=False)
            await response_message.edit(embed=embed)
            return

    elif message.content.startswith('!set_chat'):
        if os.path.exists('chatbot_rooms.json'):
            with open('chatbot_rooms.json', 'r') as file:
                chatbot_rooms = json.load(file)
        else:
            chatbot_rooms = {}  

        server_id = str(message.guild.id)
        channel_id = str(message.channel.id)
        chatbot_rooms[server_id] = channel_id

        with open('chatbot_rooms.json', 'w') as file:
            json.dump(chatbot_rooms, file)

        await message.channel.send(f'บอทได้กำหนดให้ตอบกลับในห้องนี้เท่านั้น: {message.channel.mention}')
        return

    chatbot_room_id = str(message.guild.id)
    if chatbot_room_id in chatbot_rooms and message.channel.id == int(chatbot_rooms[chatbot_room_id]):
        question = message.content.strip()
        conversation_history = []

        if is_math_question(question) and question.strip().isdigit():
            try:
                result = eval_expression(question)
                await message.reply(f"ผลลัพธ์ของ {question} คือ {result}")
            except Exception as e:
                await message.reply(f"เกิดข้อผิดพลาดในการคำนวณ: {e}")
            return

        try:
            typing_message = await message.reply("กำลังพิม")

            for _ in range(3):
                await typing_message.edit(content="กำลังพิม.")
                await asyncio.sleep(0.25)
                await typing_message.edit(content="กำลังพิม..")
                await asyncio.sleep(0.25)
                await typing_message.edit(content="กำลังพิม...")
                await asyncio.sleep(0.25)

            response = await get_gemini_response(question, conversation_history)

            if response is not None:
                response = response.replace('Gemini', 'kit')
                response = response.replace('Google', 'DEV')
                response = response.replace('ฉัน', 'ผม')
                response = response.replace('ค่ะ', 'ครับ')
                response = response.replace('คะ', 'ครับ')

                if response:
                    if len(response) > 2000:
                        file_name = f"response_{message.author.id}.txt"
                        with open(file_name, 'w', encoding='utf-8') as file:
                            file.write(response)
                        with open(file_name, 'rb') as file:
                            await message.reply("ข้อความยาวเกินไป. ส่งไฟล์แทน.", file=discord.File(file, file_name))
                    else:
                        await typing_message.edit(content=response)

        except Exception as e:
            print(f"Error in chatbot room: {e}")
            await message.channel.send("เกิดข้อผิดพลาดในระบบของเรา. กรุณาลองใหม่อีกครั้ง.")


keep_alive()
client.run(os.getenv('Token'))
