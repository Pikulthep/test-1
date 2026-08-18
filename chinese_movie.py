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

# 🌟 จัดเต็มทุกหมวดหมู่
CATEGORIES = [
    {"name": "ข้ามมิติ", "id": "16", "max_page": 3},
    {"name": "ครอบครัว", "id": "1", "max_page": 2},
    {"name": "ความรัก", "id": "15", "max_page": 24},
    {"name": "คอมเมดี้", "id": "14", "max_page": 1},
    {"name": "ซับไทย", "id": "25", "max_page": 9},
    {"name": "ซีรีส์มาใหม่", "id": "5", "max_page": 1},
    {"name": "ซีรีส์แนะนำ", "id": "26", "max_page": 1},
    {"name": "ดราม่า", "id": "2", "max_page": 3},
    {"name": "พลิกเกม", "id": "23", "max_page": 7},
    {"name": "ย้อนยุค", "id": "22", "max_page": 7},
    {"name": "สะท้อนสังคม", "id": "3", "max_page": 1},
    {"name": "เกิดใหม่", "id": "17", "max_page": 3},
    {"name": "เทพเซียน", "id": "19", "max_page": 3},
    {"name": "แก้แค้น", "id": "13", "max_page": 6},
    {"name": "แอ็คชั่น", "id": "18", "max_page": 1}
]

SAVE_DIR = "output"
OUTPUT_FILE = os.path.join(SAVE_DIR, "chinese_movies.txt")

# ================== ฟังก์ชันช่วยเหลือ ==================
def get_driver():
    """ฟังก์ชันเปิดเบราว์เซอร์ล่องหน เพื่อหลบ Cloudflare"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # ปิดโหลดรูปเพื่อความไว
    prefs = {"profile.managed_default_content_settings.images": 2, "profile.managed_default_content_settings.stylesheets": 2}
    options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.set_page_load_timeout(45)
    return driver

# ================== ฟังก์ชันดึงข้อมูล ==================
def get_movies_from_category(cat_name, cat_id, max_page):
    movies = []
    driver = get_driver()
    
    try:
        print(f"  -> กำลังเปิดหน้าหมวดหมู่เพื่อหลบระบบป้องกัน (Cloudflare)...")
        driver.get(f"{DOMAIN}/categories.php?id={cat_id}")
        time.sleep(6) # ให้เวลาเจาะกำแพง
        
        # เลื่อนจอลงด้านล่างเพื่อให้เว็บโหลดหนังเพิ่ม (Infinite Scroll)
        for page in range(1, max_page):
            print(f"     เลื่อนจอโหลดข้อมูลหน้า {page + 1}/{max_page} ...")
            driver.execute_script("""
                var sentinel = document.getElementById('movie-sentinel');
                if(sentinel) {
                    sentinel.scrollIntoView();
                } else {
                    window.scrollTo(0, document.body.scrollHeight);
                }
            """)
            time.sleep(4) # รอให้การ์ดหนังหน้าใหม่เด้งขึ้นมา
            
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
        
    # ลบข้อมูลหนังที่ซ้ำกัน
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
    print("🚀 เริ่มต้นดึงข้อมูลเว็บหนังสั้นจีน (เวอร์ชัน Selenium Stealth + NatPlayer)\n")
    
    all_groups_data = []
    
    for cat in CATEGORIES:
        print(f"==================================================")
        print(f"🎬 หมวดหมู่: {cat['name']} (ID: {cat['id']})")
        print(f"==================================================")
        
        movies_data = get_movies_from_category(cat['name'], cat['id'], cat['max_page'])
        
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
