import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import markovify
import nltk
from nltk.tokenize import word_tokenize
import random
import os
import time
import re
import os
import requests
import platform
import subprocess
import psutil
import pickle
import hashlib
from better_profanity import profanity
from config import *
import traceback
import shutil
from nltk.sentiment.vader import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

print(splashtext) # you can use https://patorjk.com/software/taag/ for 3d text or just remove this entirely

os.makedirs("memories", exist_ok=True)
os.makedirs("models", exist_ok=True)


def download_json():
    locales_dir = "locales"
    response = requests.get(f"{VERSION_URL}/goob/locales/{LOCALE}.json")
    if response.status_code == 200:

        if not os.path.exists(locales_dir):
            os.makedirs(locales_dir)
        file_path = os.path.join(locales_dir, f"{LOCALE}.json")
        if os.path.exists(file_path):
            return
        else:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(response.text)

    if not os.path.exists(os.path.join(locales_dir, "en.json")):
        
        response = requests.get(f"{VERSION_URL}/goob/locales/en.json")
        if response.status_code == 200:
            with open(os.path.join(locales_dir, "en.json"), "w", encoding="utf-8") as file:
                file.write(response.text)

download_json()
def load_translations():
    translations = {}
    translations_dir = os.path.join(os.path.dirname(__file__), "locales")
    
    for filename in os.listdir(translations_dir):
        if filename.endswith(".json"):
            lang_code = filename.replace(".json", "")
            with open(os.path.join(translations_dir, filename), "r", encoding="utf-8") as f:
                translations[lang_code] = json.load(f)
    
    return translations

translations = load_translations()

def get_translation(lang: str, key: str):
    lang_translations = translations.get(lang, translations["en"])
    if key not in lang_translations:
        print(f"{RED}Missing key: {key} in language {lang}{RESET}")
    return lang_translations.get(key, key)



def is_name_available(NAME):
    if os.getenv("gooberTOKEN"):
        return
    try:
        response = requests.post(f"{VERSION_URL}/check-if-available", json={"name": NAME}, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            data = response.json()
            return data.get("available", False)
        else:
            print(f"{get_translation(LOCALE, 'name_check')}", response.json())
            return False
    except Exception as e:
        print(f"{get_translation(LOCALE, 'name_check2')}", e)
        return False

def register_name(NAME):
    try:
        if ALIVEPING == False:
            return
        # check if the name is avaliable
        if not is_name_available(NAME):
            if os.getenv("gooberTOKEN"):
                return
            print(f"{RED}{get_translation(LOCALE, 'name_taken')}{RESET}")
            quit()
        
        # if it is register it
        response = requests.post(f"{VERSION_URL}/register", json={"name": NAME}, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            
            if not os.getenv("gooberTOKEN"):
                print(f"{GREEN}{get_translation(LOCALE, 'add_token').format(token=token)} gooberTOKEN=<token>.{RESET}")
                quit()
            else:
                print(f"{GREEN}{RESET}")
            
            return token
        else:
            print(f"{RED}{get_translation(LOCALE, 'token_exists').format()}{RESET}", response.json())
            return None
    except Exception as e:
        print(f"{RED}{get_translation(LOCALE, 'registration_error').format()}{RESET}", e)
        return None

register_name(NAME)

def save_markov_model(model, filename='markov_model.pkl'):
    model_file = f"models/{filename}"
    with open(model_file, "wb") as f:
        pickle.dump(model, f)
    print(f"{GREEN}Markov model saved to {model_file}{RESET}")

def load_markov_model(server_id=None):
    if server_id:
        filename = f"markov_model_{server_id}.pkl"
    else:
        filename = "markov_model.pkl"
    
    model_file = f"models/{filename}"

def get_latest_version_info():

    try:

        response = requests.get(UPDATE_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"{RED}{get_translation(LOCALE, 'version_error')} {response.status_code}{RESET}")
            return None
    except requests.RequestException as e:
        print(f"{RED}{get_translation(LOCALE, 'version_error')} {e}{RESET}")
        return None
    
async def load_cogs_from_folder(bot, folder_name="cogs"):
    for filename in os.listdir(folder_name):
        if filename.endswith(".py") and not filename.startswith("_"):
            cog_name = filename[:-3]
            try:
                await bot.load_extension(f"{folder_name}.{cog_name}")
                print(f"{GREEN}{get_translation(LOCALE, 'loaded_cog')} {cog_name}{RESET}")
            except Exception as e:
                print(f"{RED}{get_translation(LOCALE, 'cog_fail')} {cog_name} {e}{RESET}")
                traceback.print_exc()

currenthash = ""
def generate_sha256_of_current_file():
    global currenthash
    sha256_hash = hashlib.sha256()
    with open(__file__, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    currenthash = sha256_hash.hexdigest()



latest_version = "0.0.0"
local_version = "rewrite/seperate-memories"
os.environ['gooberlocal_version'] = local_version


def check_for_update():
    if ALIVEPING == "false":
        return
    global latest_version, local_version 
    
    latest_version_info = get_latest_version_info()
    if not latest_version_info:
        print(f"{get_translation(LOCALE, 'fetch_update_fail')}")
        return None, None 

    latest_version = latest_version_info.get("version")
    os.environ['gooberlatest_version'] = latest_version
    download_url = latest_version_info.get("download_url")

    if not latest_version or not download_url:
        print(f"{RED}{get_translation(LOCALE, 'invalid_server')}{RESET}")
        return None, None 

    if local_version == "0.0.0":
        with open(LOCAL_VERSION_FILE, "w") as f:
            f.write(latest_version)
    generate_sha256_of_current_file()
    gooberhash = latest_version_info.get("hash")
    if gooberhash == currenthash:
        if local_version < latest_version:
            print(f"{YELLOW}{get_translation(LOCALE, 'new_version').format(latest_version=latest_version, local_version=local_version)}{RESET}")
            print(f"{YELLOW}{get_translation(LOCALE, 'changelog').format(VERSION_URL=VERSION_URL)}{RESET}")
        else:
            print(f"{GREEN}{get_translation(LOCALE, 'latest_version')} {local_version}{RESET}")
            print(f"{get_translation(LOCALE, 'latest_version2').format(VERSION_URL=VERSION_URL)}\n\n")
    else:
        print(f"{YELLOW}{get_translation(LOCALE, 'modification_warning')}")
        print(f"{YELLOW}{get_translation(LOCALE, 'reported_version')} {local_version}{RESET}")
        print(f"{DEBUG}{get_translation(LOCALE, 'current_hash')} {currenthash}{RESET}")


check_for_update()

def get_file_info(file_path):
    try:
        file_size = os.path.getsize(file_path)
        with open(file_path, "r") as f:
            lines = f.readlines()
        return {"file_size_bytes": file_size, "line_count": len(lines)}
    except Exception as e:
        return {"error": str(e)}

nltk.download('punkt')

def load_memory(server_id=None):
    if server_id:
        memory_file = f"memories/memory_{server_id}.json"
    else:
        memory_file = "memories/memory.json"
    
    data = []
    try:
        with open(memory_file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        print(f"{RED}Error decoding memory file {memory_file}{RESET}")
    
    return data

def save_memory(memory, server_id=None):
    if server_id:
        memory_file = f"memories/memory_{server_id}.json"
    else:
        memory_file = "memories/memory.json"
    
    with open(memory_file, "w") as f:
        json.dump(memory, f, indent=4)

def train_markov_model(memory, additional_data=None, server_id=None):
    if not memory:
        return None
    
    text = "\n".join(memory)
    if additional_data:
        text += "\n" + "\n".join(additional_data)
    
    try:
        model = markovify.NewlineText(text, state_size=2)
        if server_id:
            model_filename = f"markov_model_{server_id}.pkl"
            save_markov_model(model, model_filename)
        return model
    except Exception as e:
        print(f"{RED}Error training model: {e}{RESET}")
        return None

#this doesnt work and im extremely pissed and mad
def append_mentions_to_18digit_integer(message):
    pattern = r'\b\d{18}\b'
    return re.sub(pattern, lambda match: f"", message)

def preprocess_message(message):
    message = append_mentions_to_18digit_integer(message)
    tokens = word_tokenize(message)
    tokens = [token for token in tokens if token.isalnum()]
    return " ".join(tokens)


intents = discord.Intents.default()

intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=False, replied_user=True))
memory = load_memory() 
markov_model = load_markov_model()
if not markov_model:
    print(f"{get_translation(LOCALE, 'no_model')}")
    memory = load_memory()
    markov_model = train_markov_model(memory)

generated_sentences = set()
used_words = set()

slash_commands_enabled = False
@bot.event
async def on_ready():
    
    folder_name = "cogs"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"{GREEN}{get_translation(LOCALE, 'folder_created').format(folder_name=folder_name)}{RESET}")
    else:
       print(f"{DEBUG}{get_translation(LOCALE, 'folder_exists').format(folder_name=folder_name)}{RESET}")
    markov_model = train_markov_model(memory)
    await load_cogs_from_folder(bot)
    global slash_commands_enabled
    print(f"{GREEN}{get_translation(LOCALE, 'logged_in')} {bot.user}{RESET}")
    try:
        synced = await bot.tree.sync()
        print(f"{GREEN}{get_translation(LOCALE, 'synced_commands')} {len(synced)} {get_translation(LOCALE, 'synced_commands2')} {RESET}")
        slash_commands_enabled = True
        ping_server()
        print(f"{GREEN}{get_translation(LOCALE, 'started').format()}{RESET}")
    except Exception as e:
        print(f"{RED}{get_translation(LOCALE, 'fail_commands_sync')} {e}{RESET}")
        traceback.print_exc()
        quit()
    if not song:
        return  
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{song}"))

def ping_server():
    if ALIVEPING == "false":
        print(f"{YELLOW}{get_translation(LOCALE, 'pinging_disabled')}{RESET}")
        os.environ['gooberauthenticated'] = 'No'
        return
    file_info = get_file_info(MEMORY_FILE)
    payload = {
        "name": NAME,
        "memory_file_info": file_info,
        "version": local_version,
        "slash_commands": slash_commands_enabled,
        "token": gooberTOKEN
    }
    try:
        response = requests.post(VERSION_URL+"/ping", json=payload)
        if response.status_code == 200:
            print(f"{GREEN}{get_translation(LOCALE, 'goober_ping_success').format(NAME=NAME)}{RESET}")
            os.environ['gooberauthenticated'] = 'Yes'
        else:
            print(f"{RED}{get_translation(LOCALE, 'goober_ping_fail')} {response.status_code}{RESET}")
            os.environ['gooberauthenticated'] = 'No'
    except Exception as e:
        print(f"{RED}{get_translation(LOCALE, 'goober_ping_fail2')} {str(e)}{RESET}")
        os.environ['gooberauthenticated'] = 'No'


positive_gifs = os.getenv("POSITIVE_GIFS").split(',')

def is_positive(sentence):
    scores = analyzer.polarity_scores(sentence)
    sentiment_score = scores['compound']

        # forcin this fucker
    debug_message = f"{DEBUG}{get_translation(LOCALE, 'sentence_positivity')} {sentiment_score}{RESET}"
    print(debug_message) 

    return sentiment_score > 0.1


async def send_message(ctx, message=None, embed=None, file=None, edit=False, message_reference=None):
    if edit and message_reference:
        try:
            # Editing the existing message
            await message_reference.edit(content=message, embed=embed)
        except Exception as e:
            await ctx.send(f"{RED}{get_translation(LOCALE, 'edit_fail')} {e}{RESET}")
    else:
        if hasattr(ctx, "respond"):
            # For slash command contexts
            sent_message = None
            if embed:
                sent_message = await ctx.respond(embed=embed, ephemeral=False)
            elif message:
                sent_message = await ctx.respond(message, ephemeral=False)
            if file:
                sent_message = await ctx.respond(file=file, ephemeral=False)
        else:

            sent_message = None
            if embed:
                sent_message = await ctx.send(embed=embed)
            elif message:
                sent_message = await ctx.send(message)
            if file:
                sent_message = await ctx.send(file=file)
        return sent_message

@bot.hybrid_command(description="Retrain Markov models for servers")
@app_commands.choices(option=[
    app_commands.Choice(name="Retrain current server", value="current"),
    app_commands.Choice(name="Retrain all servers", value="all"),
    app_commands.Choice(name="Select servers to retrain", value="select")
])
async def retrain_models(ctx, option: app_commands.Choice[str]):
    if ctx.author.id != ownerid:
        return await ctx.send("You don't have permission to use this command.", ephemeral=True)

    if option.value == "current":
        server_id = ctx.guild.id if ctx.guild else "DM"
        await retrain_single_server(ctx, server_id)
    
    elif option.value == "all":
        await retrain_all_servers(ctx)
    
    elif option.value == "select":
        await show_server_selection(ctx)

async def retrain_single_server(ctx, server_id):
    memory_file = f"memories/memory_{server_id}.json"
    model_file = f"models/markov_model_{server_id}.pkl"
    
    try:
        with open(memory_file, 'r') as f:
            memory = json.load(f)
    except FileNotFoundError:
        return await ctx.send(f"No memory data found for server {server_id}", ephemeral=True)
    
    processing_msg = await ctx.send(f"Retraining model for server {server_id}...")
    
    model = train_markov_model(memory, server_id=server_id)
    
    if model:
        await processing_msg.edit(content=f"Successfully retrained model for server {server_id}")
    else:
        await processing_msg.edit(content=f"Failed to retrain model for server {server_id}")

async def retrain_all_servers(ctx):
    memory_files = [f for f in os.listdir("memories/") if f.startswith("memory_") and f.endswith(".json")]
    
    if not memory_files:
        return await ctx.send("No server memory files found to retrain.", ephemeral=True)
    
    progress_msg = await ctx.send(f"Retraining models for {len(memory_files)} servers...")
    success_count = 0
    
    for mem_file in memory_files:
        try:
            server_id = mem_file.replace("memory_", "").replace(".json", "")
            with open(f"memories/{mem_file}", 'r') as f:
                memory = json.load(f)
            
            model = train_markov_model(memory, server_id=server_id)
            if model:
                success_count += 1
            
            if success_count % 5 == 0:
                await progress_msg.edit(content=f"Retraining in progress... {success_count}/{len(memory_files)} completed")
        
        except Exception as e:
            print(f"Error retraining {mem_file}: {e}")
    
    await progress_msg.edit(content=f"Retraining complete successfully retrained {success_count}/{len(memory_files)} servers")

async def show_server_selection(ctx):
    memory_files = [f for f in os.listdir("memories/") if f.startswith("memory_") and f.endswith(".json")]
    
    if not memory_files:
        return await ctx.send("No server memory files found.", ephemeral=True)
    options = []
    for mem_file in memory_files:
        server_id = mem_file.replace("memory_", "").replace(".json", "")
        server_name = f"Server {server_id}"  
        if server_id != "DM":
            guild = bot.get_guild(int(server_id))
            if guild:
                server_name = guild.name
        
        options.append(discord.SelectOption(label=server_name, value=server_id))
    select_menus = []
    for i in range(0, len(options), 25):
        chunk = options[i:i+25]
        
        select = discord.ui.Select(
            placeholder=f"Select servers to retrain ({i+1}-{min(i+25, len(options))})",
            min_values=1,
            max_values=len(chunk),
            options=chunk
        )
        
        select_menus.append(select)
    view = discord.ui.View()
    for menu in select_menus:
        menu.callback = lambda interaction, m=menu: handle_server_selection(interaction, m)
        view.add_item(menu)
    
    await ctx.send("Select which servers to retrain:", view=view)

async def handle_server_selection(interaction, select_menu):
    await interaction.response.defer()
    
    selected_servers = select_menu.values
    if not selected_servers:
        return await interaction.followup.send("No servers selected.", ephemeral=True)
    
    progress_msg = await interaction.followup.send(f"Retraining {len(selected_servers)} selected servers...")
    success_count = 0
    
    for server_id in selected_servers:
        try:
            memory_file = f"memories/memory_{server_id}.json"
            with open(memory_file, 'r') as f:
                memory = json.load(f)
            
            model = train_markov_model(memory, server_id=server_id)
            if model:
                success_count += 1
            if success_count % 5 == 0:
                await progress_msg.edit(content=f"Retraining in progress... {success_count}/{len(selected_servers)} completed")
        
        except Exception as e:
            print(f"Error retraining {server_id}: {e}")
    
    await progress_msg.edit(content=f"Retraining complete Successfully retrained {success_count}/{len(selected_servers)} selected servers")

@bot.hybrid_command(description=f"{get_translation(LOCALE, 'command_desc_talk')}")
async def talk(ctx, sentence_size: int = 5):
    server_id = ctx.guild.id if ctx.guild else "DM"
    markov_model = load_markov_model(server_id)
    
    if not markov_model:
        memory = load_memory(server_id)
        markov_model = train_markov_model(memory, server_id=server_id)
        if not markov_model:
            await send_message(ctx, f"{get_translation(LOCALE, 'command_talk_insufficent_text')}")
            return

    response = None
    for _ in range(20):
        if sentence_size == 1:
            response = markov_model.make_short_sentence(max_chars=100, tries=100)
            if response:
                response = response.split()[0]
        else:
            response = markov_model.make_sentence(tries=100, max_words=sentence_size)

        if response and response not in generated_sentences:
            if sentence_size > 1:
                response = improve_sentence_coherence(response)
            generated_sentences.add(response)
            break

    if response:
        cleaned_response = re.sub(r'[^\w\s]', '', response).lower()
        coherent_response = rephrase_for_coherence(cleaned_response)
        if random.random() < 0.9 and is_positive(coherent_response):
            gif_url = random.choice(positive_gifs)
            combined_message = f"{coherent_response}\n[jif]({gif_url})"
        else:
            combined_message = coherent_response
        print(combined_message)
        os.environ['gooberlatestgen'] = combined_message
        await send_message(ctx, combined_message)
    else:
        await send_message(ctx, f"{get_translation(LOCALE, 'command_talk_generation_fail')}")


def improve_sentence_coherence(sentence):

    sentence = sentence.replace(" i ", " I ")  
    return sentence

def rephrase_for_coherence(sentence):

    words = sentence.split()

    coherent_sentence = " ".join(words)
    return coherent_sentence

bot.help_command = None


@bot.hybrid_command(description=f"{get_translation(LOCALE, 'command_desc_help')}")
async def help(ctx):
    embed = discord.Embed(
        title=f"{get_translation(LOCALE, 'command_help_embed_title')}",
        description=f"{get_translation(LOCALE, 'command_help_embed_desc')}",
        color=discord.Color.blue()
    )

    command_categories = {
        f"{get_translation(LOCALE, 'command_help_categories_general')}": ["mem", "talk", "about", "ping"],
        f"{get_translation(LOCALE, 'command_help_categories_admin')}": ["stats", "retrain"]
    }

    custom_commands = []
    for cog_name, cog in bot.cogs.items():
        for command in cog.get_commands():
            if command.name not in command_categories[f"{get_translation(LOCALE, 'command_help_categories_general')}"] and command.name not in command_categories[f"{get_translation(LOCALE, 'command_help_categories_admin')}"]:
                custom_commands.append(command.name)

    if custom_commands:
        embed.add_field(name=f"{get_translation(LOCALE, 'command_help_categories_custom')}", value="\n".join([f"{PREFIX}{command}" for command in custom_commands]), inline=False)

    for category, commands_list in command_categories.items():
        commands_in_category = "\n".join([f"{PREFIX}{command}" for command in commands_list])
        embed.add_field(name=category, value=commands_in_category, inline=False)

    await send_message(ctx, embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if str(message.author.id) in BLACKLISTED_USERS:
        return

    if message.content.startswith((f"{PREFIX}talk", f"{PREFIX}mem", f"{PREFIX}help", f"{PREFIX}stats", f"{PREFIX}")):
        print(f"{get_translation(LOCALE, 'command_ran').format(message=message)}")
        await bot.process_commands(message)
        return

    if profanity.contains_profanity(message.content):
        return

    if message.content and USERTRAIN_ENABLED:
        server_id = message.guild.id if message.guild else "DM"
        memory = load_memory(server_id)
        
        formatted_message = append_mentions_to_18digit_integer(message.content)
        cleaned_message = preprocess_message(formatted_message)
        
        if cleaned_message:
            memory.append(cleaned_message)
            save_memory(memory, server_id)

    await bot.process_commands(message)


@bot.event
async def on_interaction(interaction):
    try:
        if interaction.type == discord.InteractionType.application_command:
            command_name = interaction.data.get('name', 'unknown')
            print(f"{get_translation(LOCALE, 'command_ran_s').format(interaction=interaction)}{command_name}")
    except Exception as e:
        print(f"{RED}Error handling interaction: {e}{RESET}")
        traceback.print_exc()

@bot.check
async def block_blacklisted(ctx):
    if str(ctx.author.id) in BLACKLISTED_USERS:
        try:
            if isinstance(ctx, discord.Interaction):
                if not ctx.response.is_done():
                    await ctx.response.send_message("You are blacklisted.", ephemeral=True)
                else:
                    await ctx.followup.send("You are blacklisted.", ephemeral=True)
            else:
                await ctx.send("You are blacklisted.", ephemeral=True)
        except:
            pass
        return False
    return True

@bot.hybrid_command(description=f"{get_translation(LOCALE, 'command_desc_ping')}")
async def ping(ctx):
    await ctx.defer()
    latency = round(bot.latency * 1000)

    LOLembed = discord.Embed(
        title="Pong!!",
        description=(
            f"{PING_LINE}\n"
            f"`{get_translation(LOCALE, 'command_ping_embed_desc')}: {latency}ms`\n"
        ),
        color=discord.Color.blue()
    )
    LOLembed.set_footer(text=f"{get_translation(LOCALE, 'command_ping_footer')} {ctx.author.name}", icon_url=ctx.author.avatar.url)

    await ctx.send(embed=LOLembed)

@bot.hybrid_command(description=f"{get_translation(LOCALE, 'command_about_desc')}")
async def about(ctx):
    print("-----------------------------------\n\n")
    try:
        check_for_update()
    except Exception as e:
        pass
    print("-----------------------------------")
    embed = discord.Embed(title=f"{get_translation(LOCALE, 'command_about_embed_title')}", description="", color=discord.Color.blue())
    embed.add_field(name=f"{get_translation(LOCALE, 'command_about_embed_field1')}", value=f"{NAME}", inline=False)
    embed.add_field(name=f"{get_translation(LOCALE, 'command_about_embed_field2name')}", value=f"{get_translation(LOCALE, 'command_about_embed_field2value').format(local_version=local_version, latest_version=latest_version)}", inline=False)

    await send_message(ctx, embed=embed)

@bot.hybrid_command(description="stats")
async def stats(ctx):
    if ctx.author.id != ownerid: 
        return
    print("-----------------------------------\n\n")
    try:
        check_for_update()
    except Exception as e:
        pass
    print("-----------------------------------")
    memory_file = 'memory.json'
    file_size = os.path.getsize(memory_file)
    
    with open(memory_file, 'r') as file:
        line_count = sum(1 for _ in file)
    embed = discord.Embed(title=f"{get_translation(LOCALE, 'command_stats_embed_title')}", description=f"{get_translation(LOCALE, 'command_stats_embed_desc')}", color=discord.Color.blue())
    embed.add_field(name=f"{get_translation(LOCALE, 'command_stats_embed_field1name')}", value=f"{get_translation(LOCALE, 'command_stats_embed_field1value').format(file_size=file_size, line_count=line_count)}", inline=False)
    embed.add_field(name=f"{get_translation(LOCALE, 'command_stats_embed_field2name')}", value=f"{get_translation(LOCALE, 'command_stats_embed_field2value').format(local_version=local_version, latest_version=latest_version)}", inline=False)
    embed.add_field(name=f"{get_translation(LOCALE, 'command_stats_embed_field3name')}", value=f"{get_translation(LOCALE, 'command_stats_embed_field3value').format(NAME=NAME, PREFIX=PREFIX, ownerid=ownerid, cooldown_time=cooldown_time, PING_LINE=PING_LINE, showmemenabled=showmemenabled, USERTRAIN_ENABLED=USERTRAIN_ENABLED, last_random_talk_time=last_random_talk_time, song=song, splashtext=splashtext)}", inline=False)
 
    await send_message(ctx, embed=embed)

@bot.hybrid_command()
async def mem(ctx):
    if showmemenabled != "true":
        return
    server_id = ctx.guild.id if ctx.guild else "DM"
    memory_file = f"memories/memory_{server_id}.json" if server_id else "memories/memory.json"
    try:
        with open(memory_file, "r") as f:
            await send_message(ctx, file=discord.File(f, memory_file))
    except FileNotFoundError:
        await send_message(ctx, f"No memory file found at {memory_file}")

def improve_sentence_coherence(sentence):
    sentence = sentence.replace(" i ", " I ")
    return sentence

bot.run(TOKEN)
