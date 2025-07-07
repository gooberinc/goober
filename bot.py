import os
import re
import json
import time
import random
import traceback
import subprocess
import tempfile
import shutil
import uuid
import asyncio
import sys
from typing import List, Dict, Set, Optional, Tuple, Any, Union, Callable, Coroutine, TypeVar, Type

from modules.globalvars import *
from modules.prestartchecks import start_checks

# Print splash text and check for updates
print(splashtext)  # Print splash text (from modules/globalvars.py)
start_checks()

import requests
import discord
from discord.ext import commands
from discord import app_commands
from discord import Colour, Embed, File, Interaction, Message
from discord.abc import Messageable

from better_profanity import profanity
from discord.ext import commands

from modules.central import ping_server
from modules.volta.main import _, set_language
from modules.markovmemory import *
from modules.version import *
from modules.sentenceprocessing import *
from modules.unhandledexception import handle_exception
from modules.image import gen_meme, gen_demotivator

sys.excepthook = handle_exception
check_for_update()  # Check for updates (from modules/version.py)

# Type aliases
T = TypeVar('T')
MessageContext = Union[commands.Context, discord.Interaction]
MessageReference = Union[Message, discord.WebhookMessage]

# Constants with type hints
positive_gifs: List[str] = os.getenv("POSITIVE_GIFS", "").split(',')
currenthash: str = ""
launched: bool = False
slash_commands_enabled: bool = False

# Set up Discord bot intents and create bot instance
intents: discord.Intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot: commands.Bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=False, replied_user=True)
)

# Load memory and Markov model for text generation
memory: List[str] = load_memory()
markov_model: Optional[markovify.Text] = load_markov_model()
if not markov_model:
    print(f"{RED}{(_('markov_model_not_found'))}{RESET}")
    memory = load_memory()
    markov_model = train_markov_model(memory)

generated_sentences: Set[str] = set()
used_words: Set[str] = set()

async def load_cogs_from_folder(bot, folder_name="assets/cogs"):
    for filename in os.listdir(folder_name):
        if filename.endswith(".py") and not filename.startswith("_"):
            cog_name = filename[:-3]
            module_path = folder_name.replace("/", ".").replace("\\", ".") + f".{cog_name}"
            try:
                await bot.load_extension(module_path)
                print(f"{GREEN}{(_('loaded_cog'))} {cog_name}{RESET}")
            except Exception as e:
                print(f"{RED}{(_('cog_fail'))} {cog_name} {e}{RESET}")
                traceback.print_exc()

async def fetch_active_users() -> str:
    try:
        response: requests.Response = requests.get(f"{VERSION_URL}/active-users")
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "?"
    except Exception as e:
        print(f"{RED}{(_('error_fetching_active_users'))}{RESET} {e}")
        return "?"

async def send_alive_ping_periodically() -> None:
    while True:
        try:
            requests.post(f"{VERSION_URL}/aliveping", json={"name": NAME})
        except Exception as e:
            print(f"{RED}{(_('error_sending_alive_ping'))}{RESET} {e}")
        await asyncio.sleep(60)

# Event: Called when the bot is ready
@bot.event
async def on_ready() -> None:
    global launched
    global slash_commands_enabled
    global NAME
    
    folder_name: str = "cogs"
    if launched:
        return
        
    await load_cogs_from_folder(bot)
    try:
        synced: List[discord.app_commands.AppCommand] = await bot.tree.sync()
        print(f"{GREEN}{_('synced_commands')} {len(synced)} {(_('synced_commands2'))} {RESET}")
        slash_commands_enabled = True
        ping_server()  # ping_server from modules/central.py
        
        active_users: str = await fetch_active_users()
        print(f"{GREEN}{(_('active_users:'))} {active_users}{RESET}")
        print(f"{GREEN}{(_('started')).format(name=NAME)}{RESET}")

        bot.loop.create_task(send_alive_ping_periodically())
    except discord.errors.Forbidden as perm_error:
        print(f"{RED}Permission error while syncing commands: {perm_error}{RESET}") 
        print(f"{RED}Make sure the bot has the 'applications.commands' scope and is invited with the correct permissions.{RESET}")
        quit()
    except Exception as e:
        print(f"{RED}{(_('fail_commands_sync'))} {e}{RESET}")
        traceback.print_exc()
        quit()
        
    if not song:
        return  
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{song}"))
    launched = True

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    from modules.unhandledexception import handle_exception
    
    if isinstance(error, commands.CommandInvokeError):
        original: Exception = error.original
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
@bot.hybrid_command(description=f"{(_('command_desc_retrain'))}")
async def retrain(ctx: commands.Context) -> None:
    if ctx.author.id != ownerid:
        return

    message_ref: MessageReference = await send_message(ctx, f"{(_('command_markov_retrain'))}")
    try:
        with open(MEMORY_FILE, 'r') as f:
            memory: List[str] = json.load(f)
    except FileNotFoundError:
        await send_message(ctx, f"{(_('command_markov_memory_not_found'))}")
        return
    except json.JSONDecodeError:
        await send_message(ctx, f"{(_('command_markov_memory_is_corrupt'))}")
        return
        
    data_size: int = len(memory)
    processed_data: int = 0
    processing_message_ref: MessageReference = await send_message(ctx, f"{(_('command_markov_retraining')).format(processed_data=processed_data, data_size=data_size)}")
    start_time: float = time.time()
    
    for i, data in enumerate(memory):
        processed_data += 1
        if processed_data % 1000 == 0 or processed_data == data_size:
            await send_message(ctx, f"{(_('command_markov_retraining')).format(processed_data=processed_data, data_size=data_size)}", edit=True, message_reference=processing_message_ref)

    global markov_model
    markov_model = train_markov_model(memory)
    save_markov_model(markov_model)

    await send_message(ctx, f"{(_('command_markov_retrain_successful')).format(data_size=data_size)}", edit=True, message_reference=processing_message_ref)

# Command: Generate a sentence using the Markov model
@bot.hybrid_command(description=f"{(_('command_desc_talk'))}")
async def talk(ctx: commands.Context, sentence_size: int = 5) -> None:
    if not markov_model:
        await send_message(ctx, f"{(_('command_talk_insufficent_text'))}")
        return

    response: Optional[str] = None
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
        cleaned_response: str = re.sub(r'[^\w\s]', '', response).lower()
        coherent_response: str = rephrase_for_coherence(cleaned_response) 
        if random.random() < 0.9 and is_positive(coherent_response): 
            gif_url: str = random.choice(positive_gifs)
            combined_message: str = f"{coherent_response}\n[jif]({gif_url})"
        else:
            combined_message: str = coherent_response
        print(combined_message)
        os.environ['gooberlatestgen'] = combined_message
        await send_message(ctx, combined_message)
    else:
        await send_message(ctx, f"{(_('command_talk_generation_fail'))}")

# Command: Generate an image
@bot.hybrid_command(description=f"{(_('command_desc_help'))}")
async def impact(ctx: commands.Context) -> None:
    assets_folder: str = "assets/images"
    temp_input: Optional[str] = None

    def get_random_asset_image() -> Optional[str]:
        files: List[str] = [f for f in os.listdir(assets_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        if not files:
            return None
        return os.path.join(assets_folder, random.choice(files))

    if ctx.message.attachments:
        attachment: discord.Attachment = ctx.message.attachments[0]
        if attachment.content_type and attachment.content_type.startswith("image/"):
            ext: str = os.path.splitext(attachment.filename)[1]
            temp_input = f"tempy{ext}"
            await attachment.save(temp_input)
            input_path: str = temp_input
        else:
            fallback_image: Optional[str] = get_random_asset_image()
            if fallback_image is None:
                await ctx.reply((_('no_image_available')))
                return
            temp_input = tempfile.mktemp(suffix=os.path.splitext(fallback_image)[1])
            shutil.copy(fallback_image, temp_input)
            input_path = temp_input
    else:
        fallback_image = get_random_asset_image()
        if fallback_image is None:
            await ctx.reply((_('no_image_available')))
            return
        temp_input = tempfile.mktemp(suffix=os.path.splitext(fallback_image)[1])
        shutil.copy(fallback_image, temp_input)
        input_path = temp_input

    output_path: Optional[str] = await gen_meme(input_path)

    if output_path is None or not os.path.isfile(output_path):
        if temp_input and os.path.exists(temp_input):
            os.remove(temp_input)
        await ctx.reply((_('failed_generate_image')))
        return

    await ctx.send(file=discord.File(output_path))

    if temp_input and os.path.exists(temp_input):
        os.remove(temp_input)

# New demotivator command
@bot.hybrid_command(description="Generate a demotivator poster with two lines of text")
async def demotivator(ctx: commands.Context) -> None:
    assets_folder: str = "assets/images"
    temp_input: Optional[str] = None

    def get_random_asset_image() -> Optional[str]:
        files: List[str] = [f for f in os.listdir(assets_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        if not files:
            return None
        return os.path.join(assets_folder, random.choice(files))

    if ctx.message.attachments:
        attachment: discord.Attachment = ctx.message.attachments[0]
        if attachment.content_type and attachment.content_type.startswith("image/"):
            ext: str = os.path.splitext(attachment.filename)[1]
            temp_input = f"tempy{ext}"
            await attachment.save(temp_input)
            input_path: str = temp_input
        else:
            fallback_image: Optional[str] = get_random_asset_image()
            if fallback_image is None:
                await ctx.reply((_('no_image_available')))
                return
            temp_input = tempfile.mktemp(suffix=os.path.splitext(fallback_image)[1])
            shutil.copy(fallback_image, temp_input)
            input_path = temp_input
    else:
        fallback_image = get_random_asset_image()
        if fallback_image is None:
            await ctx.reply((_('no_image_available')))
            return
        temp_input = tempfile.mktemp(suffix=os.path.splitext(fallback_image)[1])
        shutil.copy(fallback_image, temp_input)
        input_path = temp_input

    output_path: Optional[str] = await gen_demotivator(input_path)

    if output_path is None or not os.path.isfile(output_path):
        if temp_input and os.path.exists(temp_input):
            os.remove(temp_input)
        await ctx.reply("Failed to generate demotivator.")
        return

    await ctx.send(file=discord.File(output_path))

    if temp_input and os.path.exists(temp_input):
        os.remove(temp_input)

bot.remove_command('help')
# Command: Show help information
@bot.hybrid_command(description=f"{(_('command_desc_help'))}")
async def help(ctx: commands.Context) -> None:
    embed: discord.Embed = discord.Embed(
        title=f"{(_('command_help_embed_title'))}",
        description=f"{(_('command_help_embed_desc'))}",
        color=Colour(0x000000)
    )

    command_categories: Dict[str, List[str]] = {
        f"{(_('command_help_categories_general'))}": ["mem", "talk", "about", "ping", "impact", "demotivator", "help"],
        f"{(_('command_help_categories_admin'))}": ["stats", "retrain", "setlanguage"]
    }

    custom_commands: List[str] = []
    for cog_name, cog in bot.cogs.items():
        for command in cog.get_commands():
            if command.name not in command_categories[f"{(_('command_help_categories_general'))}"] and command.name not in command_categories[f"{(_('command_help_categories_admin'))}"]:
                custom_commands.append(command.name)

    if custom_commands:
        embed.add_field(name=f"{(_('command_help_categories_custom'))}", value="\n".join([f"{PREFIX}{command}" for command in custom_commands]), inline=False)

    for category, commands_list in command_categories.items():
        commands_in_category: str = "\n".join([f"{PREFIX}{command}" for command in commands_list])
        embed.add_field(name=category, value=commands_in_category, inline=False)

    await send_message(ctx, embed=embed)

@bot.hybrid_command(description=f"{(_('command_desc_setlang'))}")
@app_commands.describe(locale="Choose your language")
async def setlanguage(ctx: commands.Context, locale: str) -> None:
    if ctx.author.id != ownerid:
        await ctx.send(":thumbsdown:")
        return
    await ctx.defer()
    set_language(locale)
    await ctx.send(":thumbsup:")

# Event: Called on every message
@bot.event
async def on_message(message: discord.Message) -> None:
    global memory, markov_model
    EMOJIS = ["\U0001F604", "\U0001F44D", "\U0001F525", "\U0001F4AF", "\U0001F389", "\U0001F60E"] # originally was emojis but it would probably shit itself on systems without unicode so....
    if message.author.bot:
        return

    if str(message.author.id) in BLACKLISTED_USERS:
        return

    if message.content.startswith((f"{PREFIX}talk", f"{PREFIX}mem", f"{PREFIX}help", f"{PREFIX}stats", f"{PREFIX}")):
        print(f"{(_('command_ran')).format(message=message)}")
        await bot.process_commands(message)
        return

    if profanity.contains_profanity(message.content):
        return

    if message.content:
        if not USERTRAIN_ENABLED:
            return
        formatted_message: str = append_mentions_to_18digit_integer(message.content)
        cleaned_message: str = preprocess_message(formatted_message)
        if cleaned_message:
            memory.append(cleaned_message)
            save_memory(memory)

        sentiment_score = is_positive(message.content) # doesnt work but im scared to change the logic now please ignore
        if sentiment_score > 0.8:
            if REACT != "True":
                return
            emoji = random.choice(EMOJIS)
            try:
                await message.add_reaction(emoji)
            except Exception as e:
                print(f"Failed to react with emoji: {e}")

    await bot.process_commands(message)

# Event: Called on every interaction (slash command, etc.)
@bot.event
async def on_interaction(interaction: discord.Interaction) -> None:
    print(f"{(_('command_ran_s')).format(interaction=interaction)}{interaction.data['name']}")

# Global check: Block blacklisted users from running commands
@bot.check
async def block_blacklisted(ctx: commands.Context) -> bool:
    if str(ctx.author.id) in BLACKLISTED_USERS:
        try:
            if isinstance(ctx, discord.Interaction):
                if not ctx.response.is_done():
                    await ctx.response.send_message((_('blacklisted')), ephemeral=True)
                else:
                    await ctx.followup.send((_('blacklisted')), ephemeral=True)
            else:
                await ctx.send((_('blacklisted_user')), ephemeral=True)
        except:
            pass
        return False
    return True

# Command: Show bot latency
@bot.hybrid_command(description=f"{(_('command_desc_ping'))}")
async def ping(ctx: commands.Context) -> None:
    await ctx.defer()
    latency: int = round(bot.latency * 1000)

    LOLembed: discord.Embed = discord.Embed(
        title="Pong!!",
        description=(
            f"{PING_LINE}\n"
            f"`{(_('command_ping_embed_desc'))}: {latency}ms`\n"
        ),
        color=Colour(0x000000)
    )
    LOLembed.set_footer(text=f"{(_('command_ping_footer'))} {ctx.author.name}", icon_url=ctx.author.avatar.url)

    await ctx.send(embed=LOLembed)

# Command: Show about information
@bot.hybrid_command(description=f"{(_('command_about_desc'))}")
async def about(ctx: commands.Context) -> None:
    print("-----------------------------------\n\n")
    latest_version: str = check_for_update()
    print("-----------------------------------")
    embed: discord.Embed = discord.Embed(title=f"{(_('command_about_embed_title'))}", description="", color=Colour(0x000000))
    embed.add_field(name=f"{(_('command_about_embed_field1'))}", value=f"{NAME}", inline=False)
    embed.add_field(name=f"{(_('command_about_embed_field2name'))}", value=f"{(_('command_about_embed_field2value')).format(local_version=local_version, latest_version=latest_version)}", inline=False)

    await send_message(ctx, embed=embed)

# Command: Show bot statistics (admin only)
@bot.hybrid_command(description="stats")
async def stats(ctx: commands.Context) -> None:
    if ctx.author.id != ownerid: 
        return
    print("-----------------------------------\n\n")
    latest_version: str = check_for_update()
    print("-----------------------------------")
    memory_file: str = 'memory.json'
    file_size: int = os.path.getsize(memory_file)
    
    with open(memory_file, 'r') as file:
        line_count: int = sum(1 for _ in file)

    embed: discord.Embed = discord.Embed(title=f"{(_('command_stats_embed_title'))}", description=f"{(_('command_stats_embed_desc'))}", color=Colour(0x000000))
    embed.add_field(name=f"{(_('command_stats_embed_field1name'))}", value=f"{(_('command_stats_embed_field1value')).format(file_size=file_size, line_count=line_count)}", inline=False)
    embed.add_field(name=f"{(_('command_stats_embed_field2name'))}", value=f"{(_('command_stats_embed_field2value')).format(local_version=local_version, latest_version=latest_version)}", inline=False)
    embed.add_field(name=f"{(_('command_stats_embed_field3name'))}", value=f"{(_('command_stats_embed_field3value')).format(NAME=NAME, PREFIX=PREFIX, ownerid=ownerid, PING_LINE=PING_LINE, showmemenabled=showmemenabled, USERTRAIN_ENABLED=USERTRAIN_ENABLED, song=song, splashtext=splashtext)}", inline=False)

    await send_message(ctx, embed=embed)

# Command: Upload memory.json to litterbox.catbox.moe and return the link
@bot.hybrid_command()
async def mem(ctx: commands.Context) -> None:
    if showmemenabled != "true":
        return
    command: str = """curl -F "reqtype=fileupload" -F "time=1h" -F "fileToUpload=@memory.json" https://litterbox.catbox.moe/resources/internals/api.php"""
    memorylitter: subprocess.CompletedProcess = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(memorylitter)
    await send_message(ctx, memorylitter.stdout.strip())

# Helper: Improve sentence coherence (simple capitalization fix)
def improve_sentence_coherence(sentence: str) -> str:
    # Capitalizes "i" to "I" in the sentence
    sentence = sentence.replace(" i ", " I ")
    return sentence

# Start the bot
bot.run(TOKEN)