import re
from modules.globalvars import *
from modules.translations import *
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
analyzer = SentimentIntensityAnalyzer()

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
    
#this doesnt work and im extremely pissed and mad
def append_mentions_to_18digit_integer(message):
    pattern = r'\b\d{18}\b'
    return re.sub(pattern, lambda match: f"", message)

def preprocess_message(message):
    message = append_mentions_to_18digit_integer(message)
    tokens = word_tokenize(message)
    tokens = [token for token in tokens if token.isalnum()]
    return " ".join(tokens)

def improve_sentence_coherence(sentence):

    sentence = sentence.replace(" i ", " I ")  
    return sentence

def rephrase_for_coherence(sentence):

    words = sentence.split()

    coherent_sentence = " ".join(words)
    return coherent_sentence