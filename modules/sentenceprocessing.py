import re
from modules.globalvars import *
from modules.volta.main import _

import spacy
from spacy.tokens import Doc
from spacytextblob.spacytextblob import SpacyTextBlob

import logging
logger = logging.getLogger("goober")


def check_resources():
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logging.critical((_('spacy_model_not_found')))
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
    if "spacytextblob" not in nlp.pipe_names:
        nlp.add_pipe("spacytextblob")
    logger.info((_('spacy_initialized')))

check_resources()

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("spacytextblob")
Doc.set_extension("polarity", getter=lambda doc: doc._.blob.polarity)

def is_positive(sentence):
    doc = nlp(sentence)
    sentiment_score = doc._.polarity  # from spacytextblob

    debug_message = f"{(_('sentence_positivity'))} {sentiment_score}{RESET}"
    logger.debug(debug_message)

    return sentiment_score > 0.6 # had to raise the bar because it kept saying "death to jews" was fine and it kept reacting to them

async def send_message(ctx, message=None, embed=None, file=None, edit=False, message_reference=None):
    if edit and message_reference:
        try:
            await message_reference.edit(content=message, embed=embed)
        except Exception as e:
            await ctx.send(f"{RED}{(_('edit_fail'))} {e}{RESET}")
    else:
        if hasattr(ctx, "respond"):
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

def append_mentions_to_18digit_integer(message):
    pattern = r'\b\d{18}\b'
    return re.sub(pattern, lambda match: "", message)

def preprocess_message(message):
    message = append_mentions_to_18digit_integer(message)
    doc = nlp(message)
    tokens = [token.text for token in doc if token.is_alpha or token.is_digit]
    return " ".join(tokens)

def improve_sentence_coherence(sentence):
    return re.sub(r'\bi\b', 'I', sentence)

def rephrase_for_coherence(sentence):
    words = sentence.split()
    coherent_sentence = " ".join(words)
    return coherent_sentence
