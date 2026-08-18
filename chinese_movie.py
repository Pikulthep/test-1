import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import os
import time
from datetime import datetime

# ================== CONFIG ==================
DOMAIN = "https://www.xn--72c9ab1ec1bc6q.online"

# 🌟 ไม่ต้องพึ่ง max_page อีกต่อไป! บอทจะเลื่อนกวาดจนกว่าจะสุดหน้าเว็บเอง
CATEGORIES = [
    {"name": "ข้ามมิติ", "id": "16"},
    {"name": "ครอบครัว", "id": "1"},
    {"name": "ความรัก", "id": "15"},
    {"name": "คอมเมดี้", "id": "14"},
    {"name": "ซับไทย", "id": "25"},
    {"name": "ซีรีส์มาใหม่", "id": "5"},
    {"name": "ซีรีส์แนะนำ", "id": "26"},
    {"name": "ดราม่า", "id": "2"},
    {"name": "พลิกเกม", "id": "23"},
    {"name": "ย้อนยุค", "id": "22"},
    {"name": "สะท้อนสังคม", "id": "3"},
    {"name": "เกิดใหม่", "id": "17"},
    {"name": "เทพเซียน", "id": "19"},
    {"name": "แก้แค้น", "id": "13"},
    {"name": "แอ็คชั่น", "id": "18"}
]

SAVE_DIR = "output"
OUTPUT_FILE = os.path.join(SAVE_DIR, "chinese_movies.txt")

# ================== ฟังก์ชันช่วยเหลือ ==================
def get_driver():
    """เปิดเบราว์เซอร์ล่องหน เพื่อหลบ Cloudflare"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
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

def format_url(url_path):
    """ฟังก์ชันจัดการลิงก์ให้สมบูรณ์ ป้องกันบั๊กลิงก์เสีย"""
    if not url_path:
        return ""
    if url_path.startswith('http'):
        return url_path
    elif url_path.startswith('//'):
        return f"https:{url_path}"
    else:
        return f"{DOMAIN}/{url_path.lstrip('/')}"

# ================== ฟังก์ชันดึงข้อมูล ==================
def get_movies_from_category(cat_name, cat_id):
    movies = []
    driver = get_driver()
    
    try:
        print(f"  -> กำลังเปิดหน้าหมวดหมู่ {cat_name}...")
        driver.get(f"{DOMAIN}/categories.php?id={cat_id}")
        time.sleep(6) # ให้เวลาเจาะกำแพง Cloudflare
        
        last_count = 0
        retry = 0
        
        # 🌟 ระบบเลื่อนจอแบบ Smart Scroll (ฉลาดและทนทานขึ้น)
        for _ in range(60): # ลูปสูงสุดเผื่อไว้ 60 ครั้ง (รองรับหนัง 1,800+ เรื่อง)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # 1. เช็คว่าเจอข้อความ "ไม่มีหนังเพิ่มเติมแล้ว" (id="movie-end") หรือยัง
            end_element = soup.find('div', id='movie-end')
            if end_element and 'hidden' not in end_element.get('class', []):
                print("     ✅ ดึงข้อมูลจนสุดหน้าเว็บแล้ว")
                break
                
            # 2. เช็คจำนวนการ์ดหนังว่าเพิ่มขึ้นไหม
            current_count = len(soup.find_all('div', class_='movie-card'))
            if current_count > last_count:
                print(f"     ⏳ กำลังโหลด... กวาดมาได้แล้ว {current_count} เรื่อง")
                last_count = current_count
                retry = 0
            else:
                retry += 1
                # ทริก: ขยับจอขึ้นลงนิดหน่อย เพื่อกระตุ้นระบบโหลดของเว็บ
                driver.execute_script("window.scrollBy(0, -800);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                if retry >= 4:
                    print("     ⚠️ โหลดหน้าเว็บเพิ่มไม่ได้แล้ว (อาจจะสุดหน้าจริงๆ)")
                    break
            
        # กวาดข้อมูลจากโครงสร้างที่ดึงได้ทั้งหมด
        final_soup = BeautifulSoup(driver.page_source, 'html.parser')
        cards = final_soup.find_all('div', class_='movie-card')
        
        if not cards:
            print("     [ไม่พบการ์ดหนัง] เว็บอาจจะบล็อก หรือไม่มีข้อมูล")
            
        for card in cards:
            a_tag = card.find('a')
            img_tag = card.find('img')
            
            if a_tag and img_tag:
                full_link = format_url(a_tag.get('href', ''))
                full_img = format_url(img_tag.get('src', ''))
                
                title = img_tag.get('alt', 'ไม่ทราบชื่อเรื่อง')
                info_text = "ซับไทย" if cat_name == "ซับไทย" else "พากย์ไทย"
                
                # โครงสร้าง JSON ของ NatPlayer
                movies.append({
                    "name": title,
                    "url": full_link,
                    "image": full_img,
                    "referer": DOMAIN,
                    "info": info_text,
                    "playInNatPlayer": "true"
                })
                
    except Exception as e:
        print(f"     [Error] ดึงข้อมูลล้มเหลว: {e}")
    finally:
        driver.quit()
        
    # ตัดข้อมูลที่ซ้ำกันทิ้ง
    unique_movies = []
    seen = set()
    for m in movies:
        if m['url'] not in seen:
            seen.add(m['url'])
            unique_movies.append(m)
            
    return unique_movies

# ================== Main Program ==================
if __name__ == "__main__":
    start_time = time.time()
    print("🚀 เริ่มต้นดึงข้อมูลเว็บหนังสั้นจีน (เวอร์ชัน NatPlayer + Smart Infinite Scroll)\n")
    
    all_groups_data = []
    
    for cat in CATEGORIES:
        print(f"==================================================")
        print(f"🎬 หมวดหมู่: {cat['name']} (ID: {cat['id']})")
        print(f"==================================================")
        
        movies_data = get_movies_from_category(cat['name'], cat['id'])
        
        print(f"✅ ดึงสำเร็จ {len(movies_data)} เรื่อง\n")
        
        if movies_data:
            all_groups_data.append({
                "name": f"🀄 {cat['name']}",
                "image": "https://www.xn--72c9ab1ec1bc6q.online/assets/images/icon.webp",
                "stations": movies_data
            })
            
    # ================== สร้างไฟล์ JSON ==================
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
