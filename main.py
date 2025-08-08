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
from selenium.common.exceptions import TimeoutException

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True  
bot = commands.Bot(command_prefix='!', intents=intents)

def get_latest_menu_image():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # User-Agent 지정해서 bot 차단 회피
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)

    img_url = None
    try:
        # 1. 메인에서 최신 게시글 링크 추출 (최대 5초 대기)
        driver.get('https://pf.kakao.com/_xfWxfCxj/posts')
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.link_board'))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        first_link = soup.select_one('a.link_board')
        if first_link:
            post_url = 'https://pf.kakao.com' + first_link['href']
            driver.get(post_url)
            # 2. 상세페이지에서 이미지 태그 등장까지 최대 5초 대기
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.item_archive_image img'))
            )
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            img_tag = soup.select_one('.item_archive_image img')
            if img_tag:
                img_url = img_tag['src']
    except TimeoutException:
        print("Timeout: 카카오 페이지 요소를 못 찾음 (네트워크 지연/차단 가능성)")
    except Exception as e:
        print("오류:", e)
    finally:
        driver.quit()
    return img_url

def download_image(img_url, filename='today_menu.jpg'):
    # 이미지 다운로드 (에러 핸들링)
    try:
        img_data = requests.get(img_url, timeout=5).content
        with open(filename, "wb") as f:
            f.write(img_data)
    except Exception as e:
        print("이미지 다운로드 실패:", e)

@bot.command()
async def 점심(ctx):
    img_url = get_latest_menu_image()
    if img_url:
        download_image(img_url)
        file = discord.File("today_menu.jpg")
        await ctx.send("대륭 17차 점심 메뉴", file=file)
    else:
        await ctx.send("오늘의 메뉴 이미지를 찾지 못했습니다.\n(카카오 페이지 접속 지연/변경/차단일 수 있음)")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
