import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import os
import time
import concurrent.futures
import re
from datetime import datetime

# ================== CONFIG ==================
DOMAIN = "https://www.xn--72c9ab1ec1bc6q.online"

CATEGORIES = [
    {"name": "ข้ามมิติ", "id": "16", "max_page": 2},
    {"name": "ครอบครัว", "id": "1", "max_page": 1},
    {"name": "ความรัก", "id": "15", "max_page": 3},
    {"name": "พลิกเกม", "id": "23", "max_page": 2},
    {"name": "ย้อนยุค", "id": "22", "max_page": 2},
    {"name": "เกิดใหม่", "id": "17", "max_page": 1},
    {"name": "แก้แค้น", "id": "13", "max_page": 2}
]

SAVE_DIR = "output"
OUTPUT_FILE = os.path.join(SAVE_DIR, "chinese_movies.txt")

# 🌟 ปรับกลับมาใช้ 3 เพื่อไม่ให้ RAM ของ GitHub ระเบิด (เพราะ Selenium กินสเปค)
MAX_WORKERS = 3 

# ================== ฟังก์ชันช่วยเหลือ ==================
def get_driver():
    """ฟังก์ชันเปิดเบราว์เซอร์ล่องหน (ผ่านด่าน Cloudflare)"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--mute-audio")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # ปิดโหลดรูป/CSS ให้ทำงานไวขึ้น
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2
    }
    options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.set_page_load_timeout(45)
    return driver

# ================== ฟังก์ชันดึงข้อมูล ==================
def get_movie_video_link(movie_info):
    """มุดเข้าหน้าหนังเพื่อเจาะลิงก์ .m3u8"""
    driver = get_driver()
    try:
        driver.get(movie_info['url'])
        time.sleep(3) # รอให้หน้าเว็บและข้อมูลวิดีโอโหลดเสร็จ
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        m3u8_link = None
        
        # เจาะเอาลิงก์จากปุ่มเล่นวิดีโอ (ตามโค้ด HTML ของเว็บ)
        play_btn = soup.find('button', id='posterPlayer')
        if play_btn and play_btn.has_attr('data-video-url'):
            m3u8_link = play_btn['data-video-url']
            
        # ถ้าวิธีแรกพลาด ให้ลองดึงจาก Script Data
        if not m3u8_link:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                if 'contentUrl' in script.text and '.m3u8' in script.text:
                    match = re.search(r'"contentUrl"\s*:\s*"([^"]+)"', script.text)
                    if match:
                        m3u8_link = match.group(1)
                        break

        if m3u8_link:
            print(f"    ✅ เจาะลิงก์วิดีโอสำเร็จ: {movie_info['name']}")
            return {
                "name": movie_info['name'],
                "image": movie_info['image'],
                "url": m3u8_link,
                "info": "หนังสั้นจีน"
            }
        else:
            print(f"    ❌ ไม่พบลิงก์วิดีโอ: {movie_info['name']}")
            return None
            
    except Exception as e:
        print(f"    ⚠️ Error ขณะเจาะไฟล์: {movie_info['name']} ({str(e).split(chr(10))[0]})")
        return None
    finally:
        driver.quit()

def get_movies_from_category(cat_name, cat_id, max_page):
    """กวาดหน้าหมวดหมู่หลัก"""
    movie_links_data = []
    driver = get_driver()
    
    try:
        print(f"  -> กำลังเปิดหน้าหมวดหมู่เพื่อหลบระบบป้องกัน...")
        driver.get(f"{DOMAIN}/categories.php?id={cat_id}")
        time.sleep(5) # ให้เวลาเจาะกำแพง Cloudflare
        
        # 🌟 จำลองการเลื่อนจอลงข้างล่างเพื่อโหลดหนังหน้าถัดไป (Infinite Scroll)
        for page in range(1, max_page):
            print(f"     เลื่อนจอโหลดข้อมูลหน้า {page + 1}/{max_page} ...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4) 
            
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        cards = soup.find_all('div', class_='movie-card')
        
        if not cards:
            print("     [ไม่พบการ์ดหนัง] เว็บอาจจะบล็อก หรือไม่มีข้อมูล")
            
        for card in cards:
            a_tag = card.find('a')
            img_tag = card.find('img')
            
            if a_tag and img_tag:
                href = a_tag.get('href', '')
                full_link = f"{DOMAIN}/{href.lstrip('/')}" if not href.startswith('http') else href
                
                src = img_tag.get('src', '')
                full_img = f"{DOMAIN}/{src.lstrip('/')}" if not src.startswith('http') else src
                
                title = img_tag.get('alt', 'ไม่ทราบชื่อเรื่อง')
                
                movie_links_data.append({
                    "name": title,
                    "image": full_img,
                    "url": full_link
                })
                
    except Exception as e:
        print(f"     [Error] ดึงหน้ารวมล้มเหลว: {e}")
    finally:
        driver.quit()
        
    # ตัดลิงก์ซ้ำ
    unique_links = {v['url']: v for v in movie_links_data}.values()
    unique_links_list = list(unique_links)
    
    final_movies = []
    if unique_links_list:
        print(f"  🎯 พบลิงก์ทั้งหมด {len(unique_links_list)} เรื่อง")
        print(f"  ⏳ เริ่มมุดเจาะดึงข้อมูลวิดีโอ (รันขนาน {MAX_WORKERS} หน้าต่าง)...")
        
        # วิ่งเจาะไฟล์วิดีโอทีละ 3 หน้าต่าง
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = executor.map(get_movie_video_link, unique_links_list)
            for res in results:
                if res:
                    final_movies.append(res)
                    
    return final_movies

# ================== Main Program ==================
if __name__ == "__main__":
    start_time = time.time()
    print("🚀 เริ่มต้นดึงข้อมูลและเจาะไฟล์เว็บหนังสั้นจีน (เวอร์ชัน Selenium Stealth)\n")
    
    all_groups_data = []
    
    for cat in CATEGORIES:
        print(f"==================================================")
        print(f"🎬 หมวดหมู่: {cat['name']} (ID: {cat['id']})")
        print(f"==================================================")
        
        movies_data = get_movies_from_category(cat['name'], cat['id'], cat['max_page'])
        
        print(f"✅ หมวด {cat['name']} เจาะวิดีโอสำเร็จ {len(movies_data)} เรื่อง\n")
        
        if movies_data:
            all_groups_data.append({
                "name": f"🀄 {cat['name']}",
                "image": "https://www.xn--72c9ab1ec1bc6q.online/assets/images/icon.webp",
                "stations": movies_data
            })
            
    # ================== สร้างไฟล์ JSON ==================
    print(f"💾 กำลังสร้างไฟล์เพลย์ลิสต์ {OUTPUT_FILE} ...")
    os.makedirs(SAVE_DIR, exist_ok=True)
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    final_data = {
        "name": "รวมหนังสั้นจีน (โรงหยก)", 
        "author": f"Auto Update ({current_date})", 
        "info": "ซีรีส์จีนสั้นยอดฮิต",
        "image": "https://www.xn--72c9ab1ec1bc6q.online/assets/images/icon.webp",
        "groups": all_groups_data 
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    elapsed = time.time() - start_time
    print(f"🎉 จบการทำงานทั้งหมดภายในเวลา {elapsed / 60:.2f} นาที!")
