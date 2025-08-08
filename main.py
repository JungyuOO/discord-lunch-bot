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
from datetime import datetime
import pytz

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True  
bot = commands.Bot(command_prefix='!', intents=intents)

# ----- 메뉴 이미지 추출 함수 -----
def get_latest_menu_image(meal_type='lunch'):
    '''
    meal_type: 'lunch' or 'dinner' (여기선 실제로 동일 게시글에서 이미지를 추출함)
    '''
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
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

# ----- 이미지 다운로드 -----
def download_image(img_url, filename='today_menu.jpg'):
    try:
        img_data = requests.get(img_url, timeout=5).content
        with open(filename, "wb") as f:
            f.write(img_data)
    except Exception as e:
        print("이미지 다운로드 실패:", e)

# ----- 점심 명령어 -----
@bot.command()
async def 점심(ctx):
    now = datetime.now(pytz.timezone('Asia/Seoul'))
    weekday = now.weekday()  # 월:0 ~ 일:6
    if weekday >= 5:  # 5,6=토,일
        await ctx.send("주말에는 봇이 운영하지 않습니다! 🙏")
        return
    if not (10 <= now.hour < 14):
        await ctx.send("지금은 점심 시간(10시~14시)이 아닙니다! ⏰")
        return

    img_url = get_latest_menu_image('lunch')
    if img_url:
        download_image(img_url, 'today_menu.jpg')
        file = discord.File("today_menu.jpg")
        await ctx.send("대륭 17차 점심 메뉴", file=file)
    else:
        await ctx.send("오늘의 메뉴 이미지를 찾지 못했습니다.\n(카카오 페이지 접속 지연/변경/차단일 수 있음)")

# ----- 저녁 명령어 -----
@bot.command()
async def 저녁(ctx):
    now = datetime.now(pytz.timezone('Asia/Seoul'))
    weekday = now.weekday()  # 월:0 ~ 일:6
    if weekday >= 5:  # 5,6=토,일
        await ctx.send("주말에는 봇이 운영하지 않습니다! 🙏")
        return
    if weekday == 4:  # 4=금요일
        await ctx.send("금요일은 석식을 운영하지 않습니다! 🍱")
        return
    if not (16 <= now.hour < 18):
        await ctx.send("지금은 저녁 시간(16시~18시)이 아닙니다! ⏰")
        return

    img_url = get_latest_menu_image('dinner')
    if img_url:
        download_image(img_url, 'dinner_menu.jpg')
        file = discord.File("dinner_menu.jpg")
        await ctx.send("대륭 17차 저녁 메뉴", file=file)
    else:
        await ctx.send("오늘의 저녁 메뉴 이미지를 찾지 못했습니다.\n(카카오 페이지 접속 지연/변경/차단일 수 있음)")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
