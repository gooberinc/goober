import discord
from discord.ext import commands
from modules.image import *
from modules.volta.main import _
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageChops, ImageColor
import os, random, shutil, tempfile

async def deepfryimage(path):
    with Image.open(path).convert("RGB") as im:
        # make it burn
        for _ in range(3):
            im = im.resize((int(im.width * 0.7), int(im.height * 0.7)))
            im = im.resize((int(im.width * 1.5), int(im.height * 1.5)))
            im = ImageEnhance.Contrast(im).enhance(random.uniform(5, 10))
            im = ImageEnhance.Sharpness(im).enhance(random.uniform(10, 50))
            im = ImageEnhance.Brightness(im).enhance(random.uniform(1.5, 3))
            r, g, b = im.split()
            r = r.point(lambda i: min(255, i * random.uniform(1.2, 2.0)))
            g = g.point(lambda i: min(255, i * random.uniform(0.5, 1.5)))
            b = b.point(lambda i: min(255, i * random.uniform(0.5, 2.0)))
            channels = [r, g, b]
            random.shuffle(channels)
            im = Image.merge("RGB", tuple(channels))
            overlay_color = tuple(random.randint(0, 255) for _ in range(3))
            overlay = Image.new("RGB", im.size, overlay_color)
            im = ImageChops.add(im, overlay, scale=2.0, offset=random.randint(-64, 64))

            im = im.filter(ImageFilter.EDGE_ENHANCE_MORE)
            im = im.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5, 2)))
            for _ in range(3):
                tmp_path = tempfile.mktemp(suffix=".jpg")
                im.save(tmp_path, format="JPEG", quality=random.randint(5, 15))
                im = Image.open(tmp_path)
            if random.random() < 0.3:
                im = ImageOps.posterize(im, bits=random.choice([2, 3, 4]))
            if random.random() < 0.2:
                im = ImageOps.invert(im)
        out_path = tempfile.mktemp(suffix=".jpg")
        im.save(out_path, format="JPEG", quality=5)
        return out_path


class whami(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def fuckup(self, ctx):
        assets_folder = "assets/images"
        temp_input = None

        def get_random_asset_image():
            files = [f for f in os.listdir(assets_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
            if not files:
                return None
            return os.path.join(assets_folder, random.choice(files))

        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if attachment.content_type and attachment.content_type.startswith("image/"):
                ext = os.path.splitext(attachment.filename)[1]
                temp_input = f"tempy{ext}"
                await attachment.save(temp_input)
                input_path = temp_input
            else:
                fallback_image = get_random_asset_image()
                if fallback_image is None:
                    await ctx.reply(_('no_image_available'))
                    return
                temp_input = tempfile.mktemp(suffix=os.path.splitext(fallback_image)[1])
                shutil.copy(fallback_image, temp_input)
                input_path = temp_input
        else:
            fallback_image = get_random_asset_image()
            if fallback_image is None:
                await ctx.reply(_('no_image_available'))
                return
            temp_input = tempfile.mktemp(suffix=os.path.splitext(fallback_image)[1])
            shutil.copy(fallback_image, temp_input)
            input_path = temp_input

        output_path = await gen_meme(input_path)

        if output_path is None or not os.path.isfile(output_path):
            if temp_input and os.path.exists(temp_input):
                os.remove(temp_input)
            await ctx.reply(_('failed_generate_image'))
            return

        deepfried_path = await deepfryimage(output_path)
        await ctx.send(file=discord.File(deepfried_path))

        if temp_input and os.path.exists(temp_input):
            os.remove(temp_input)

async def setup(bot):
    await bot.add_cog(whami(bot))
