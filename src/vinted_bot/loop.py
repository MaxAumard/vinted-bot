import asyncio
import logging
import os
import time
import uuid

from dataclasses import dataclass, asdict
from datetime import datetime
import re
from discord import Webhook, Embed
import aiohttp
from apscheduler.schedulers.background import BlockingScheduler

from vinted_bot.models.buffer_item import insert_buffer_item, Item, get_buffer_items, delete_buffer_item
from vinted_bot.models.searches import Search, get_all_searches, get_searches_by_search

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By

except Exception:
    os.system("pdm add selenium")
    raise


def url_gen(search):
    search = search.replace(" ", "%20")
    search = search.replace("/", "%2F")
    return f"https://www.vinted.fr/vetements?search_text={search}&order=newest_first"


def get_title_from_url(url: str):
    try:
        pattern = r"/([^/]+)/?$"
        match = re.search(pattern, url)
        title = match.group(1).replace("-", " ").split()
        title = " ".join(title[1:])
        return title
    except Exception:
        return "Titre non trouvé"


def options_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    return chrome_options


def search_on_vinted(searches: list[Search]) -> dict[str, list[Item]]:
    with webdriver.Chrome(options=options_driver()) as driver:
        datas = dict()
        for search in searches:
            datas[search.search] = list()
            url = url_gen(search.search)
            driver.get(url)

            items = driver.find_elements(By.CLASS_NAME, "feed-grid__item")[:5]
            for item in items:
                image_item = item.find_elements(By.CLASS_NAME, "web_ui__Image__content")[1]
                image = image_item.get_attribute("src")
                price = item.find_element(By.TAG_NAME, 'h3').text
                link = item.find_element(By.CLASS_NAME, "web_ui__ItemBox__overlay").get_attribute("href")
                title = image_item.get_attribute("alt")
                datas[search.search].append(Item(id=uuid.uuid4(),
                                                 search=search.search,
                                                 image=image,
                                                 price=price[:-2].replace(",", "."),
                                                 title=title,
                                                 url=link, ))
    return datas


async def send_items(search, new_items):
    searches = [search_object for search_object in get_searches_by_search(search)]
    for search in searches:
        if search.max_price:
            new_items = [item for item in new_items if float(item.price) <= float(search.max_price)]
        if not new_items:
            continue
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(search.webhook_url, session=session)
            for new_item in new_items:
                embed = Embed(title=new_item.title, url=new_item.url)
                embed.add_field(name="Recherche : ", value=new_item.search, inline=False)
                embed.add_field(name="prix : ", value=new_item.price, inline=False)
                embed.set_image(url=new_item.image)
                await webhook.send(embed=embed)


def loop():
    logging.info("Bot en fonctionnement : " + str(datetime.now())[:-7])
    scheduler = BlockingScheduler()
    scheduler.add_job(detector, 'interval', minutes=1)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        raise


def detector():
    searches: list[Search] = get_all_searches()
    datas = search_on_vinted(searches)
    for search, items in datas.items():
        if not items:
            continue
        buffer_item = get_buffer_items(search)
        if not buffer_item:
            [insert_buffer_item(**asdict(item)) for item in items]
            continue
        new_items = []
        for item in items:
            if item.image in [i.image for i in buffer_item]:
                break
            new_items.append(item)

        if new_items:
            asyncio.run(send_items(search, new_items))
        delete_buffer_item(search)
        [insert_buffer_item(**asdict(item)) for item in items]
