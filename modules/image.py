import os
import random
import re
from PIL import Image, ImageDraw, ImageFont
from modules.markovmemory import load_markov_model
from modules.sentenceprocessing import improve_sentence_coherence, rephrase_for_coherence

generated_sentences = set()

async def gen_image(sentence_size=5, max_attempts=10):
    images_folder = "assets/images"
    image_files = [f for f in os.listdir(images_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    if not image_files:
        return

    markov_model = load_markov_model()
    if not markov_model:
        return

    def load_font(size):
        return ImageFont.truetype("assets/fonts/Impact.ttf", size=size)

    def draw_text_with_outline(draw, text, x, y, font):
        outline_offsets = [(-2, -2), (-2, 2), (2, -2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)]
        for ox, oy in outline_offsets:
            draw.text((x + ox, y + oy), text, font=font, fill="black")
        draw.text((x, y), text, font=font, fill="white")

    def text_height(font, text):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[3] - bbox[1]

    def fits_in_width(text, font, max_width):
        bbox = draw.textbbox((0,0), text, font=font)
        text_width = bbox[2] - bbox[0]
        return text_width <= max_width

    def split_text_to_fit(text, font, max_width):
        words = text.split()
        for i in range(len(words), 0, -1):
            top_text = " ".join(words[:i])
            bottom_text = " ".join(words[i:])
            if fits_in_width(top_text, font, max_width) and fits_in_width(bottom_text, font, max_width):
                return top_text, bottom_text
        midpoint = len(words)//2
        return " ".join(words[:midpoint]), " ".join(words[midpoint:])

    coherent_response = "no text generated"
    attempt = 0
    while attempt < max_attempts:
        chosen_image_path = os.path.join(images_folder, random.choice(image_files))
        img = Image.open(chosen_image_path).convert("RGBA")
        draw = ImageDraw.Draw(img)
        width, height = img.size

        font_size = int(height / 10)
        font = load_font(font_size)

        # Generate text
        response = None
        for _ in range(20):
            if sentence_size == 1:
                candidate = markov_model.make_short_sentence(max_chars=100, tries=100)
                if candidate:
                    candidate = candidate.split()[0]
            else:
                candidate = markov_model.make_sentence(tries=100, max_words=sentence_size)

            if candidate and candidate not in generated_sentences:
                if sentence_size > 1:
                    candidate = improve_sentence_coherence(candidate)
                generated_sentences.add(candidate)
                response = candidate
                break

        if not response:
            response = "no text generated"

        cleaned_response = re.sub(r'[^\w\s]', '', response).lower()
        coherent_response = rephrase_for_coherence(cleaned_response).upper()
        bbox = draw.textbbox((0, 0), coherent_response, font=font)
        text_width = bbox[2] - bbox[0]
        text_height_px = bbox[3] - bbox[1]
        max_text_height = height // 4

        if text_width <= width and text_height_px <= max_text_height:
            # Fits on top, draw at y=0 (top)
            draw_text_with_outline(draw, coherent_response, (width - text_width) / 2, 0, font)
            img.save("output.png")
            return
        top_text, bottom_text = split_text_to_fit(coherent_response, font, width)

        top_bbox = draw.textbbox((0,0), top_text, font=font)
        bottom_bbox = draw.textbbox((0,0), bottom_text, font=font)

        top_height = top_bbox[3] - top_bbox[1]
        bottom_height = bottom_bbox[3] - bottom_bbox[1]
        if top_height <= max_text_height and bottom_height <= max_text_height:
            # top text
            draw_text_with_outline(draw, top_text, (width - (top_bbox[2]-top_bbox[0])) / 2, 0, font)
            y_bottom = height - bottom_height - int(height * 0.04)
            draw_text_with_outline(draw, bottom_text, (width - (bottom_bbox[2]-bottom_bbox[0])) / 2, y_bottom, font)
            img.save("output.png")
            return
        attempt += 1

    # If all attempts fail, cry.
    truncated = coherent_response[:100]
    bbox = draw.textbbox((0, 0), truncated, font=font)
    text_width = bbox[2] - bbox[0]
    draw_text_with_outline(draw, truncated, (width - text_width) / 2, 0, font)
    img.save("output.png")
