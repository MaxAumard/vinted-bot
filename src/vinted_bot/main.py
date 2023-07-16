import logging
import os
from threading import Thread

import discord.ext
from discord.ext import commands
from flask import Flask

from vinted_bot.models.channels_bot import insert_channel_bot, get_all_channel_bot, get_channel_bot, delete_channel_bot
from vinted_bot.models.searches import insert_search, get_searches_by_channel, delete_search, delete_search_by_channel

app = Flask(__name__)


@app.route('/')
def main():
    return "Server online!"


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    server = Thread(target=run)
    server.start()


intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=os.getenv("PREFIX"), intents=intents)  # put your own prefix here


@bot.event
async def on_ready():
    logging.info("Bot online")


@bot.command()
async def add_bot(ctx, bot_name):
    # si il y a deja un webhook dans ma base de donnée dans le meme channel, alors ne fait rien
    if channel_bot := get_channel_bot(ctx.channel.id):
        await ctx.send(
            f"{ctx.author.mention} - **❌ Le bot {channel_bot.webhook_name} est déjà présent dans ce channel !**")
        return

    # sinon, crée le webhook et l'ajoute dans la base de donnée
    webhook = await ctx.channel.create_webhook(name=bot_name)
    insert_channel_bot(ctx.channel.id, webhook.id, webhook.name, webhook.url)
    await ctx.send(f"{ctx.author.mention} - **✔️ Bot {bot_name} ajouté au channel !**")


@bot.command()
async def remove_bot(ctx, bot_name):
    inside = False
    for webhook in await ctx.channel.webhooks():
        if webhook.name == bot_name:
            await webhook.delete()
            await ctx.send(f"{ctx.author.mention} - **✔️ Bot {bot_name} supprimé du channel !**")
            inside = True
    if not inside:
        await ctx.send(f"{ctx.author.mention} - **❌ Le bot {bot_name} n'est pas présent dans ce channel !**")
        return
    delete_channel_bot(ctx.channel.id)
    delete_search_by_channel(ctx.channel.id)


@bot.command()
async def searches(ctx):
    searches = get_searches_by_channel(ctx.channel.id)

    if not searches:
        await ctx.send(f"{ctx.author.mention} - **❌ Aucune recherche n'est enregistrée dans ce channel !**")
        return

    embed = discord.Embed(title="Searches Bot", color=0xFFFFFF)
    for search in searches:
        embed.add_field(name=search.search, value="", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def add_search(ctx, search):
    if not get_channel_bot(ctx.channel.id):
        await ctx.send(
            f"{ctx.author.mention} - **❌ Aucun bot n'est présent dans ce channel !**")
        return
    actual_searches = get_searches_by_channel(ctx.channel.id)
    for actual_search in actual_searches:
        if actual_search.search == search:
            await ctx.send(
                f"{ctx.author.mention} - **❌ La recherche {search} est déjà présente dans ce channel !**")
            return
    insert_search(ctx.channel.id, search)
    await ctx.send(f"{ctx.author.mention} - **✔️ Recherche {search} ajoutée au channel !**")


@bot.command()
async def remove_search(ctx, search):
    actual_searches = get_searches_by_channel(ctx.channel.id)
    for actual_search in actual_searches:
        if actual_search.search == search:
            delete_search(ctx.channel.id, search)
            await ctx.send(f"{ctx.author.mention} - **✔️ Recherche {search} supprimée du channel !**")
            return
    await ctx.send(f"{ctx.author.mention} - **❌ La recherche {search} n'est pas présente dans ce channel !**")


def main():
    keep_alive()
    bot.run(os.getenv("TOKEN"))
