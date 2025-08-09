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
import glob
from dotenv import load_dotenv
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import pytz
from discord.ext import tasks

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True  
bot = commands.Bot(command_prefix='!', intents=intents)

# ----- 자동 정리 백그라운드 태스크 -----
@tasks.loop(hours=1)  # 매시간마다 체크
async def auto_cleanup():
    """자동으로 이전 메뉴 이미지들을 정리"""
    cleanup_old_menu_images()

@auto_cleanup.before_loop
async def before_auto_cleanup():
    await bot.wait_until_ready()

# ----- 이전 메뉴 이미지 파일 정리 함수 -----
def cleanup_old_menu_images():
    """오늘 날짜가 아닌 메뉴 이미지 파일들을 삭제"""
    try:
        today = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d')
        
        # 모든 메뉴 이미지 파일 패턴 검색
        patterns = ['*_menu_*.jpg', 'today_menu.jpg', 'dinner_menu.jpg']
        
        for pattern in patterns:
            files = glob.glob(pattern)
            for file in files:
                # 파일 생성 날짜 확인
                file_date = datetime.fromtimestamp(os.path.getctime(file), pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d')
                
                if file_date != today:
                    os.remove(file)
                    print(f"이전 메뉴 이미지 삭제: {file}")
                    
    except Exception as e:
        print(f"이전 파일 정리 중 오류: {e}")

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

# ----- 이미지 다운로드 (날짜별 파일명) -----
def download_image(img_url, meal_type='lunch'):
    try:
        today = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d')
        filename = f'{meal_type}_menu_{today}.jpg'
        
        # 해당 파일이 이미 존재하면 다운로드 스킵
        if os.path.exists(filename):
            return filename
            
        img_data = requests.get(img_url, timeout=5).content
        with open(filename, "wb") as f:
            f.write(img_data)
        return filename
    except Exception as e:
        print("이미지 다운로드 실패:", e)
        return None

# ----- 점심 명령어 -----
@bot.command()
async def 점심(ctx):
    # 이전 메뉴 이미지 정리
    cleanup_old_menu_images()
    
    now = datetime.now(pytz.timezone('Asia/Seoul'))
    weekday = now.weekday()  # 월:0 ~ 일:6
    if weekday >= 5:  # 5,6=토,일
        await ctx.send("주말에는 봇이 운영하지 않습니다!")
        return
    if not (10 <= now.hour < 14):
        await ctx.send("지금은 점심 시간(10시~14시)이 아닙니다!")
        return

    today = now.strftime('%Y-%m-%d')
    filename = f'lunch_menu_{today}.jpg'
    
    # 이미 오늘 점심 이미지가 있는지 확인
    if os.path.exists(filename):
        file = discord.File(filename)
        await ctx.send("대륭 17차 점심 메뉴 (캐시)", file=file)
        return
    
    # 없으면 새로 크롤링
    img_url = get_latest_menu_image('lunch')
    if img_url:
        downloaded_file = download_image(img_url, 'lunch')
        if downloaded_file:
            file = discord.File(downloaded_file)
            await ctx.send("대륭 17차 점심 메뉴", file=file)
        else:
            await ctx.send("이미지 다운로드에 실패했습니다.")
    else:
        await ctx.send("오늘의 메뉴 이미지를 찾지 못했습니다.\n(카카오 페이지 접속 지연/변경/차단)")

# ----- 저녁 명령어 -----
@bot.command()
async def 저녁(ctx):
    # 이전 메뉴 이미지 정리
    cleanup_old_menu_images()
    
    now = datetime.now(pytz.timezone('Asia/Seoul'))
    weekday = now.weekday()  # 월:0 ~ 일:6
    if weekday >= 5:  # 5,6=토,일
        await ctx.send("주말에는 봇이 운영하지 않습니다!")
        return
    if weekday == 4:  # 4=금요일
        await ctx.send("금요일은 석식을 운영하지 않습니다!")
        return
    if not (16 <= now.hour < 18):
        await ctx.send("지금은 저녁 시간(16시~18시)이 아닙니다!")
        return

    today = now.strftime('%Y-%m-%d')
    filename = f'dinner_menu_{today}.jpg'
    
    # 이미 오늘 저녁 이미지가 있는지 확인
    if os.path.exists(filename):
        file = discord.File(filename)
        await ctx.send("대륭 17차 저녁 메뉴 (캐시)", file=file)
        return
    
    # 없으면 새로 크롤링
    img_url = get_latest_menu_image('dinner')
    if img_url:
        downloaded_file = download_image(img_url, 'dinner')
        if downloaded_file:
            file = discord.File(downloaded_file)
            await ctx.send("대륭 17차 저녁 메뉴", file=file)
        else:
            await ctx.send("이미지 다운로드에 실패했습니다.")
    else:
        await ctx.send("오늘의 저녁 메뉴 이미지를 찾지 못했습니다.\n(카카오 페이지 접속 지연/변경/차단)")

@bot.event
async def on_ready():
    print(f'{bot.user} 봇이 시작되었습니다!')
    auto_cleanup.start()  # 자동 정리 태스크 시작

bot.run(os.getenv('DISCORD_BOT_TOKEN'))