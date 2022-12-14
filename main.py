import discord
from discord.ext import tasks, commands
import datetime
import re
import logging
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)


def _prefix_callable(bot, msg: discord.Message):
    base = [f"<@{bot.user.id}> ", f"<@!{bot.user.id}> "]
    if msg.guild is None:
        base.append('/')
    return base


intents = discord.Intents.all()
allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=True)
bot = commands.Bot(command_prefix=_prefix_callable, intents=intents, allowed_mentions=allowed_mentions)


@bot.event
async def on_ready():
    print("Bot is ready.")
    print(f"{bot.user}\n{bot.user.id}")
    print("------")

    await check_mondo.start()


@tasks.loop(minutes=1)
async def check_mondo():
    await bot.wait_until_ready()
    now = datetime.datetime.now()

    if now.strftime("%H:%M") != "00:00":
        return

    record_date = now - datetime.timedelta(days=1)

    date_regex = re.compile("[0-9]{4}/[0-9]{2}/[0-9]{2}")  # YYYY/MM/DD
    score_regex = re.compile("Score: [0-9]{1,2}/[0-9]{2}")  # Score: 00/00
    score_list = []

    mondo_ch = bot.get_channel(986346869720502384)
    async for message in mondo_ch.history(after=now - datetime.timedelta(days=1)):
        if "#Mondo" not in message.content:
            continue

        if not (date_match := date_regex.search(message.content)):
            logging.info("data is not included in the message")
            continue

        if record_date.strftime("%Y/%m/%d") != date_match.group():
            logging.info("date is not today")
            continue

        if not (score_match := score_regex.search(message.content)):
            if "不正解" not in message.content:  # 不正解の場合は「Score: 不正解」の形になる
                logging.info("score is not included in the message")
                continue

        if score_match is None:
            point = -1
        else:
            point, _ = map(int, score_match.group().split()[1].split("/"))

        score_list.append([message.author.name, point])
        score_list = sorted(score_list, key=lambda x: x[1], reverse=True)

    result = "Mondo Stats for " + record_date.strftime("%Y/%m/%d") + "\n"
    for i, (name, rate) in enumerate(score_list):
        result += f"{i + 1}: {name} {rate}points\n"

    stat_ch = bot.get_channel(1045714805266317322)
    await stat_ch.send(result)


@bot.command()
async def ping(ctx):
    await ctx.send("pong")


@bot.event
async def on_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    else:
        raise error


if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))
