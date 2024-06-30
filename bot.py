import os
import discord
from discord.ext import commands
from g4f.client import Client
from g4f.Provider import FreeGpt, ChatgptNext, AItianhuSpace, You, OpenaiChat, FreeChatgpt, Liaobots, Gemini, Bing, Blackbox
import nest_asyncio

# Menerapkan nest_asyncio
nest_asyncio.apply()

# Token dari bot Discord Anda
TOKEN = 'DISCORD_TOKEN'

# Membuat instance bot Discord dengan intents yang diperlukan
intents = discord.Intents.default()
intents.message_content = True  # Mengaktifkan intent untuk membaca konten pesan

bot = commands.Bot(command_prefix='/', intents=intents)

# Dictionary untuk menyimpan konteks percakapan
conversation_context = {}

# Event untuk menangani kejadian bot siap
@bot.event
async def on_ready():
    print(f'Bot telah login sebagai {bot.user}')

# Fungsi untuk membersihkan respons yang tidak diinginkan
def clean_response(response):
    return response.replace('$@$v=undefined-rv2$@$', '')

# Function to get the response from G4F
async def get_g4f_response(pertanyaan, context):
    providers = [FreeGpt]
    
    for provider in providers:
        try:
            g4f_client = Client(provider=provider)
            messages = context + [{"role": "user", "content": pertanyaan}]
            chat_completion = g4f_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                stream=True
            )
            
            response = ""
            for completion in chat_completion:
                response += completion.choices[0].delta.content or ""
            
            return clean_response(response), messages
        
        except Exception as e:
            print(f'Error fetching response from G4F with provider {provider}: {e}')
            continue
    
    raise Exception("All providers failed")

# Command untuk mengirim pesan ke model GPT-4
@bot.command()
async def chat(ctx, *, pertanyaan):
    user_id = ctx.author.id
    async with ctx.typing():
        # Tambahkan "gunakan bahasa indonesia" ke pertanyaan
        pertanyaan += " gunakan bahasa indonesia"
        
        # Mengirim pertanyaan ke G4F dan mendapatkan respon
        try:
            context = conversation_context.get(user_id, [])
            response, new_context = await get_g4f_response(pertanyaan, context)
            print(f'Response from G4F: {response}')
            
            # Simpan konteks percakapan yang diperbarui
            conversation_context[user_id] = new_context

            # Membagi respons jika terlalu panjang
            if len(response) > 2000:
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                for chunk in chunks:
                    await ctx.reply(chunk)
            else:
                await ctx.reply(response)  # Gunakan reply untuk membalas user
            
        except Exception as e:
            print(f'Error fetching response from G4F: {e}')
            await ctx.reply('Maaf, terjadi kesalahan. Coba lagi nanti.')

# Event untuk menangani pesan
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    user_id = message.author.id
    
    # Periksa apakah pesan adalah balasan terhadap pesan bot
    if message.reference and message.reference.message_id:
        ref_message = await message.channel.fetch_message(message.reference.message_id)
        if ref_message.author == bot.user:
            pertanyaan = message.content
            context = conversation_context.get(user_id, [])
            async with message.channel.typing():
                try:
                    pertanyaan += " gunakan bahasa indonesia"
                    response, new_context = await get_g4f_response(pertanyaan, context)
                    print(f'Response from G4F: {response}')
                    
                    # Simpan konteks percakapan yang diperbarui
                    conversation_context[user_id] = new_context

                    if len(response) > 2000:
                        chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                        for chunk in chunks:
                            await message.reply(chunk)
                    else:
                        await message.reply(response)
                
                except Exception as e:
                    print(f'Error fetching response from G4F: {e}')
                    await message.reply('Maaf, terjadi kesalahan. Coba lagi nanti.')
    
    # Jika pesan bukan balasan, periksa apakah diawali dengan prefix
    elif message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)

# Menjalankan bot dengan token Discord
bot.run(TOKEN)
