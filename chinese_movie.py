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
    # สำคัญ: ตั้งเวลา Timeout สำหรับ Async Script
    driver.set_script_timeout(15)
    return driver

def format_url(url_path):
    if not url_path:
        return ""
    if url_path.startswith('http'):
        return url_path
    elif url_path.startswith('//'):
        return f"https:{url_path}"
    else:
        return f"{DOMAIN}/{url_path.lstrip('/')}"

# ================== ฟังก์ชันดึงข้อมูล ==================
def get_movies_from_category(driver, cat_name, cat_id):
    movies = []
    
    try:
        print(f"  -> กำลังเปิดหน้าหมวดหมู่เพื่อทะลวง Cloudflare...")
        driver.get(f"{DOMAIN}/categories.php?id={cat_id}")
        time.sleep(5) # รอให้ระบบยืนยันตัวตน Cloudflare ทำงานเสร็จ
        
        # 🌟 ดึงข้อมูลหน้าแรก (หน้าที่ 1)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        cards = soup.find_all('div', class_='movie-card')
        
        # 🌟 โค้ด JavaScript ลับสำหรับเจาะ API จากภายในเบราว์เซอร์
        js_fetch_code = """
        var done = arguments[arguments.length - 1];
        var page = arguments[0];
        var cat_id = arguments[1];
        
        var formData = new FormData();
        formData.append('action', 'load_more_movies');
        formData.append('page', page);
        formData.append('category_id', cat_id);

        fetch('load_more_movies.php', {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.text())
        .then(html => done(html))
        .catch(err => done(""));
        """
        
        # ดึงหน้า 2, 3, 4... ไปเรื่อยๆ
        page = 2
        while True:
            print(f"     ดึงข้อมูลหน้า {page} ...")
            # สั่งให้เบราว์เซอร์ยิง API เองเลย
            api_html = driver.execute_async_script(js_fetch_code, page, cat_id)
            
            if not api_html or api_html.strip() == "":
                print("     ✅ กวาดข้อมูลจนสุดแล้ว (ไม่มีหนังเพิ่ม)")
                break
                
            api_soup = BeautifulSoup(api_html, 'html.parser')
            new_cards = api_soup.find_all('div', class_='movie-card')
            
            if not new_cards:
                print("     ✅ กวาดข้อมูลจนสุดแล้ว (หมดการ์ดหนัง)")
                break
                
            cards.extend(new_cards)
            
            # ถ้าหน้าล่าสุดที่ดึงมามีหนังไม่ถึง 30 เรื่อง แปลว่าเป็นหน้าสุดท้ายแล้ว
            if len(new_cards) < 30:
                print("     ✅ กวาดข้อมูลจนสุดแล้ว (ถึงหน้าสุดท้าย)")
                break
                
            page += 1
            time.sleep(1) # พัก 1 วิกันโดนบล็อก
            
        # ================== แปลงข้อมูลใส่ JSON Format ==================
        for card in cards:
            a_tag = card.find('a')
            img_tag = card.find('img')
            
            if a_tag and img_tag:
                full_link = format_url(a_tag.get('href', ''))
                full_img = format_url(img_tag.get('src', ''))
                
                title = img_tag.get('alt', 'ไม่ทราบชื่อเรื่อง')
                info_text = "ซับไทย" if cat_name == "ซับไทย" else "พากย์ไทย"
                
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
    print("🚀 เริ่มต้นดึงข้อมูลเว็บหนังสั้นจีน (เวอร์ชัน Hybrid API Bypass)\n")
    
    # เปิดเบราว์เซอร์แค่ตัวเดียว ใช้ลุยทุกหมวดหมู่ (ประหยัดแรมและเร็วขึ้น)
    print("⚙️ กำลังเตรียมเบราว์เซอร์...")
    main_driver = get_driver()
    
    all_groups_data = []
    
    try:
        for cat in CATEGORIES:
            print(f"==================================================")
            print(f"🎬 หมวดหมู่: {cat['name']} (ID: {cat['id']})")
            print(f"==================================================")
            
            movies_data = get_movies_from_category(main_driver, cat['name'], cat['id'])
            
            print(f"🎯 หมวด {cat['name']} กวาดมาได้ทั้งหมด {len(movies_data)} เรื่อง!\n")
            
            if movies_data:
                all_groups_data.append({
                    "name": f"🀄 {cat['name']}",
                    "image": "https://www.xn--72c9ab1ec1bc6q.online/assets/images/icon.webp",
                    "stations": movies_data
                })
    finally:
        main_driver.quit() # ปิดเบราว์เซอร์ตอนทำงานเสร็จทั้งหมด
            
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
