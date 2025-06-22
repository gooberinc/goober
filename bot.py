import os
import re
import json
import time
import random
import shutil
import traceback
import subprocess
import requests
import psutil

import discord
from discord.ext import commands, tasks
from discord import app_commands

import nltk
from nltk.data import find
from nltk import download
from better_profanity import profanity

from modules.globalvars import *
from modules.central import ping_server
from modules.translations import *
from modules.markovmemory import *
from modules.version import *
from modules.sentenceprocessing import *
from modules.prestartchecks import start_checks
from modules.unhandledexception import handle_exception
from discord.ext import commands, tasks
from discord import app_commands
sys.excepthook = handle_exception

# Print splash text and check for updates
print(splashtext)  # Print splash text (from modules/globalvars.py)
start_checks()
check_for_update()  # Check for updates (from modules/version.py)
launched = False

# Ensure required NLTK resources are available
def check_resources():
    # Check for required NLTK resources and download if missing
    resources = {
        'vader_lexicon': 'sentiment/vader_lexicon',
        'punkt_tab': 'tokenizers/punkt',
    }
    for resource, path in resources.items():
        try:
            find(path)  # find is from nltk.data
            print(f"{resource} is already installed.")
        except LookupError:
            download(resource)  # download is from nltk

check_resources()

# Download locale JSON files if not present
def download_json():
    # Download the locale JSON file from GitHub if not present
    locales_dir = "locales"
    response = requests.get(f"https://raw.githubusercontent.com/gooberinc/goober/refs/heads/main/locales/{LOCALE}.json")
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
        response = requests.get(f"https://raw.githubusercontent.com/gooberinc/goober/refs/heads/main/locales/en.json")
        if response.status_code == 200:
            with open(os.path.join(locales_dir, "en.json"), "w", encoding="utf-8") as file:
                file.write(response.text)

download_json()

# Dynamically load all cogs (extensions) from the cogs folder
async def load_cogs_from_folder(bot, folder_name="cogs"):
    # Loads all Python files in the cogs folder as Discord bot extensions
    for filename in os.listdir(folder_name):
        if filename.endswith(".py") and not filename.startswith("_"):
            cog_name = filename[:-3]
            try:
                await bot.load_extension(f"{folder_name}.{cog_name}")
                print(f"{GREEN}{get_translation(LOCALE, 'loaded_cog')} {cog_name}{RESET}")  # get_translation from modules/translations.py
            except Exception as e:
                print(f"{RED}{get_translation(LOCALE, 'cog_fail')} {cog_name} {e}{RESET}")
                traceback.print_exc()

currenthash = ""

# Set up Discord bot intents and create bot instance
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=False, replied_user=True)
)

# Load memory and Markov model for text generation
memory = load_memory()
markov_model = load_markov_model()
if not markov_model:
    print(f"{get_translation(LOCALE, 'no_model')}")
    memory = load_memory()
    markov_model = train_markov_model(memory)

generated_sentences = set()
used_words = set()

# Event: Called when the bot is ready
@bot.event
async def on_ready():
    global launched
    global slash_commands_enabled
    folder_name = "cogs"
    if launched == True:
        return
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"{GREEN}{get_translation(LOCALE, 'folder_created').format(folder_name=folder_name)}{RESET}")
    else:
        print(f"{DEBUG}{get_translation(LOCALE, 'folder_exists').format(folder_name=folder_name)}{RESET}")
    await load_cogs_from_folder(bot)
    try:
        synced = await bot.tree.sync()
        print(f"{GREEN}{get_translation(LOCALE, 'synced_commands')} {len(synced)} {get_translation(LOCALE, 'synced_commands2')} {RESET}")
        slash_commands_enabled = True
        ping_server()  # ping_server from modules/central.py
        print(f"{GREEN}{get_translation(LOCALE, 'started').format()}{RESET}")
    except discord.errors.Forbidden as perm_error:
        print(f"{RED}Permission error while syncing commands: {perm_error}{RESET}")
        print(f"{RED}Make sure the bot has the 'applications.commands' scope and is invited with the correct permissions.{RESET}")
        quit()
    except Exception as e:
        print(f"{RED}{get_translation(LOCALE, 'fail_commands_sync')} {e}{RESET}")
        traceback.print_exc()
        quit()
        print(f"{GREEN}{get_translation(LOCALE, 'started').format()}{RESET}")
    except Exception as e:
        print(f"{RED}{get_translation(LOCALE, 'fail_commands_sync')} {e}{RESET}")
        traceback.print_exc()
        quit()
    if not song:
        return  
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{song}"))
    launched = True

# Load positive GIF URLs from environment variable
positive_gifs = os.getenv("POSITIVE_GIFS").split(',')

@bot.event
async def on_command_error(ctx, error):
    from modules.unhandledexception import handle_exception
    
    if isinstance(error, commands.CommandInvokeError):
        original = error.original
        handle_exception(
            type(original), original, original.__traceback__, 
            context=f"Command: {ctx.command} | User: {ctx.author}"
        )
    else:
        handle_exception(
            type(error), error, error.__traceback__, 
            context=f"Command: {ctx.command} | User: {ctx.author}"
        )





# Command: Retrain the Markov model from memory
@bot.hybrid_command(description=f"{get_translation(LOCALE, 'command_desc_retrain')}")
async def retrain(ctx):
    if ctx.author.id != ownerid:
        return

    message_ref = await send_message(ctx, f"{get_translation(LOCALE, 'command_markov_retrain')}")  # send_message from modules/sentenceprocessing.py
    try:
        with open(MEMORY_FILE, 'r') as f:
            memory = json.load(f)
    except FileNotFoundError:
        await send_message(ctx, f"{get_translation(LOCALE, 'command_markov_memory_not_found')}")
        return
    except json.JSONDecodeError:
        await send_message(ctx, f"{get_translation(LOCALE, 'command_markov_memory_is_corrupt')}")
        return
    data_size = len(memory)
    processed_data = 0
    processing_message_ref = await send_message(ctx, f"{get_translation(LOCALE, 'command_markov_retraining').format(processed_data=processed_data, data_size=data_size)}")
    start_time = time.time()
    for i, data in enumerate(memory):
        processed_data += 1
        if processed_data % 1000 == 0 or processed_data == data_size:
            await send_message(ctx, f"{get_translation(LOCALE, 'command_markov_retraining').format(processed_data=processed_data, data_size=data_size)}", edit=True, message_reference=processing_message_ref)

    global markov_model
    markov_model = train_markov_model(memory)
    save_markov_model(markov_model)

    await send_message(ctx, f"{get_translation(LOCALE, 'command_markov_retrain_successful').format(data_size=data_size)}", edit=True, message_reference=processing_message_ref)

# Command: Generate a sentence using the Markov model
@bot.hybrid_command(description=f"{get_translation(LOCALE, 'command_desc_talk')}")
async def talk(ctx, sentence_size: int = 5):
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

# Remove default help command to use custom help
bot.help_command = None

# Command: Show help information
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

# Event: Called on every message
@bot.event
async def on_message(message):
    global memory, markov_model, last_random_talk_time

    # Ignore bot messages
    if message.author.bot:
        return

    # Ignore messages from blacklisted users
    if str(message.author.id) in BLACKLISTED_USERS:
        return

    # Process commands if message starts with a command prefix
    if message.content.startswith((f"{PREFIX}talk", f"{PREFIX}mem", f"{PREFIX}help", f"{PREFIX}stats", f"{PREFIX}")):
        print(f"{get_translation(LOCALE, 'command_ran').format(message=message)}")
        await bot.process_commands(message)
        return

    # Ignore messages with profanity
    if profanity.contains_profanity(message.content):  # profanity from better_profanity
        return

    # Add user messages to memory for training if enabled
    if message.content:
        if not USERTRAIN_ENABLED:
            return
        formatted_message = append_mentions_to_18digit_integer(message.content)  # append_mentions_to_18digit_integer from modules/sentenceprocessing.py
        cleaned_message = preprocess_message(formatted_message)  # preprocess_message from modules/sentenceprocessing.py
        if cleaned_message:
            memory.append(cleaned_message)
            save_memory(memory)  # save_memory from modules/markovmemory.py

    # Process any commands in the message
    await bot.process_commands(message)

# Event: Called on every interaction (slash command, etc.)
@bot.event
async def on_interaction(interaction):
    print(f"{get_translation(LOCALE, 'command_ran_s').format(interaction=interaction)}{interaction.data['name']}")

# Global check: Block blacklisted users from running commands
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

# Command: Show bot latency
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

# Command: Show about information
@bot.hybrid_command(description=f"{get_translation(LOCALE, 'command_about_desc')}")
async def about(ctx):
    print("-----------------------------------\n\n")
    try:
        check_for_update()  # check_for_update from modules/version.py
    except Exception as e:
        pass
    print("-----------------------------------")
    embed = discord.Embed(title=f"{get_translation(LOCALE, 'command_about_embed_title')}", description="", color=discord.Color.blue())
    embed.add_field(name=f"{get_translation(LOCALE, 'command_about_embed_field1')}", value=f"{NAME}", inline=False)
    embed.add_field(name=f"{get_translation(LOCALE, 'command_about_embed_field2name')}", value=f"{get_translation(LOCALE, 'command_about_embed_field2value').format(local_version=local_version, latest_version=latest_version)}", inline=False)

    await send_message(ctx, embed=embed)

# Command: Show bot statistics (admin only)
@bot.hybrid_command(description="stats")
async def stats(ctx):
    if ctx.author.id != ownerid: 
        return
    print("-----------------------------------\n\n")
    try:
        check_for_update()  # check_for_update from modules/version.py
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

# Command: Upload memory.json to litterbox.catbox.moe and return the link
@bot.hybrid_command()
async def mem(ctx):
    if showmemenabled != "true":
        return
    command = """curl -F "reqtype=fileupload" -F "time=1h" -F "fileToUpload=@memory.json" https://litterbox.catbox.moe/resources/internals/api.php"""
    memorylitter = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(memorylitter)
    await send_message(ctx, memorylitter.stdout.strip())

# Helper: Improve sentence coherence (simple capitalization fix)
def improve_sentence_coherence(sentence):
    # Capitalizes "i" to "I" in the sentence
    sentence = sentence.replace(" i ", " I ")
    return sentence

# Start the bot
bot.run(TOKEN)
