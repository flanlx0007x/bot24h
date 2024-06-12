import discord
from discord.ext import commands, tasks
import google.generativeai as genai
import os
import math
import json
import time 
import asyncio
import random
import string
from sever import keep_alive
conversation_history = []

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

def generate_random_string(length):
  characters = string.ascii_letters + string.digits
  random_string = ''.join(random.choice(characters) for _ in range(length))
  return random_string


random_string = generate_random_string(32)

new_url = f"https://gift.truemoney.com/campaign/?v={random_string}"


intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)

Token = os.getenv('Token')

statuses = [
  "เหงา",
  "เบื่อหว่าา",
  "ขก.ทำต่อละ",
  "อยากกลับบ้าน",
  "How to ลาออกดิสพี่กล้วย",
  "ไม่อยากไปทำงาน",
  "กินไรดีน้า",
  "ติวไม่ทันแล้ว",
  "หลับไปเลยละกัน",
  "ตื่นแล้วนะ",
  "อยากกินหมูกระทะ",
  "ง่วงนอนจังเลย",
  "อยากไปเที่ยว",
  "บทจะเศร้าก็เศร้านะ",
  "ทำไมต้องมีวันจันทร์",
  "คิดถึงจังเลย",
  "เงินเดือนออกแล้ว",
  "หิวววว",
  "ร้อนจังเลยวันนี้",
  "วันนี้ฝนตกหนักจัง"
] 
chatbot_rooms = {}

status_index = 0

@tasks.loop(seconds=3)
async def change_status():
  global status_index
  await client.change_presence(activity=discord.Game(name=statuses[status_index]))
  status_index = (status_index + 1) % len(statuses)

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
              if message.content.startswith('!Gen'):

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
              if message.content.startswith('Clear_history'):
                conversation_history = []
                await message.reply("ได้ทำการล้างประวัติการสอบถามและตอบกลับแล้ว:✅")
                return
              if message.content.startswith('Show_history'):
                  full_history_text = show_history(conversation_history)
                  await message.channel.send(full_history_text)
                  return  

              if message.content.startswith('status'):
                  if isinstance(message.channel, discord.TextChannel) and isinstance(message.guild, discord.Guild):
                    guild = message.guild 


                    embed = discord.Embed(
                        title="Status",
                        description=f"",
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
                    embed.add_field(name="Online24/7", value="🟢", inline=False)
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
                    embed.add_field(name="Discord", value="https://discord.gg/J3t92TM3wJ", inline=False)
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
              if message.content.startswith('!set_chat'):
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
                    try:
                        typing_message = await message.reply("กำลังพิม")

                        while True:
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
                                        file_name = f'ข้อความ-bot.txt'
                                        with open(file_name, 'w', encoding='utf-8') as file:
                                            file.write(response)
                                        await message.channel.send(f'ข้อความยาวเกิน 2000 ตัวอักษร บันทึกไว้ในไฟล์ {file_name}', file=discord.File(file_name))
                                        os.remove(file_name)
                                    else:
                                        await typing_message.edit(content=response)
                                else:
                                    await typing_message.edit(content="ไม่สามารถตอบคำถามนี้ได้")
                                break

                    except Exception as e:
                        await typing_message.edit(content=f"เกิดข้อผิดพลาด: {e}")

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError('Please set the GOOGLE_API_KEY environment variable')

genai.configure(api_key=GOOGLE_API_KEY)

generation_config = {
  "temperature": 1,
  "top_p": 0.99,
  "top_k": 0,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
  
}
safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE"
  },
]


async def get_gemini_response(question, conversation_history):
  try:
      model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
      generation_config=generation_config,
      safety_settings=safety_settings
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




def is_math_question(question):
    math_operators = ['+', '-', '*', '/', '**','//','%']
    return any(op in question for op in math_operators)

def eval_expression(expression):
    return eval(expression)
keep_alive()
client.run(Token)
