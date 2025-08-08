from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import requests
import discord
from discord.ext import commands

def get_latest_menu_image():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)

    url = 'https://pf.kakao.com/_xfWxfCxj/posts'
    driver.get(url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # 최신(가장 위) 메뉴 이미지 하나만 추출!
    first_img = soup.select_one('.item_archive_image img')
    img_url = first_img['src'] if first_img else None

    driver.quit()
    return img_url

def download_image(img_url, filename='today_menu.jpg'):
    img_data = requests.get(img_url).content
    with open(filename, "wb") as f:
        f.write(img_data)

bot = commands.Bot(command_prefix='!')

@bot.command()
async def 점심(ctx):
    img_url = get_latest_menu_image()
    if img_url:
        download_image(img_url)
        file = discord.File("today_menu.jpg")
        await ctx.send(file=file)
    else:
        await ctx.send("오늘의 메뉴 이미지를 찾지 못했습니다.")

bot.run('YOUR_DISCORD_BOT_TOKEN')
