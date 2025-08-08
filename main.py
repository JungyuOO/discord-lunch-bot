import discord
from discord.ext import commands
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True  
bot = commands.Bot(command_prefix='!', intents=intents)

def get_latest_menu_image():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)

    # 1. 메인에서 최신 게시글 링크 추출
    driver.get('https://pf.kakao.com/_xfWxfCxj/posts')
    # 'a.link_board' 요소가 등장할 때까지 최대 2초 대기
    WebDriverWait(driver, 2).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'a.link_board'))
    )
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    first_link = soup.select_one('a.link_board')
    img_url = None

    if first_link:
        post_url = 'https://pf.kakao.com' + first_link['href']
        driver.get(post_url)
        # '.item_archive_image img' 요소가 등장할 때까지 최대 2초 대기
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.item_archive_image img'))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        img_tag = soup.select_one('.item_archive_image img')
        if img_tag:
            img_url = img_tag['src']

    driver.quit()
    return img_url

def download_image(img_url, filename='today_menu.jpg'):
    img_data = requests.get(img_url).content
    with open(filename, "wb") as f:
        f.write(img_data)

@bot.command()
async def 점심(ctx):
    img_url = get_latest_menu_image()
    if img_url:
        download_image(img_url)
        file = discord.File("today_menu.jpg")
        await ctx.send("대륭 17차 점심 메뉴", file=file)
    else:
        await ctx.send("오늘의 메뉴 이미지를 찾지 못했습니다.")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
