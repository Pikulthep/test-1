import json
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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
    """เปิดเบราว์เซอร์ล่องหน พร้อมระบบพรางตัวขั้นสุดยอด"""
    options = Options()
    options.add_argument("--headless=new") # ใช้โหมด Headless ตัวใหม่ เนียนกว่าเดิม
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    prefs = {"profile.managed_default_content_settings.images": 2, "profile.managed_default_content_settings.stylesheets": 2}
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # 🌟 ฝังโค้ดพรางตัว ลบคำว่า webdriver ก่อนที่ Cloudflare จะตรวจเจอ
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    driver.set_page_load_timeout(45)
    driver.set_script_timeout(30)
    return driver

def format_url(url_path):
    if not url_path: return ""
    if url_path.startswith('http'): return url_path
    elif url_path.startswith('//'): return f"https:{url_path}"
    else: return f"{DOMAIN}/{url_path.lstrip('/')}"

# ================== ฟังก์ชันดึงข้อมูลแบบฉีด API (Injection) ==================
def fetch_data_via_js(driver, cat_id, page):
    """สั่งให้เบราว์เซอร์เป็นคนยิง API ขอข้อมูลหนังมาให้เราเอง"""
    if page == 1:
        # หน้า 1 ดึงจาก URL หมวดหมู่ตรงๆ
        js_code = """
        var cat_id = arguments[0];
        var done = arguments[arguments.length - 1];
        fetch('categories.php?id=' + cat_id)
        .then(r => r.text())
        .then(html => done(html))
        .catch(e => done(""));
        """
        return driver.execute_async_script(js_code, cat_id)
    else:
        # หน้า 2+ ดึงผ่าน API โหลดหนังเพิ่ม
        js_code = """
        var cat_id = arguments[0];
        var page = arguments[1];
        var done = arguments[arguments.length - 1];
        var fd = new FormData();
        fd.append('action', 'load_more_movies');
        fd.append('category_id', cat_id);
        fd.append('page', page);
        fetch('load_more_movies.php', {
            method: 'POST',
            body: fd,
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        })
        .then(r => r.text())
        .then(html => done(html))
        .catch(e => done(""));
        """
        return driver.execute_async_script(js_code, cat_id, page)

def process_category(driver, cat_name, cat_id):
    movies = []
    seen = set()
    page = 1
    
    while True:
        print(f"     ดึงข้อมูลหน้า {page} ...")
        
        # ยิงขอข้อมูลจากเบราว์เซอร์
        html = fetch_data_via_js(driver, cat_id, page)
        
        if not html or html.strip() == "":
            print("     ✅ กวาดข้อมูลจนสุดแล้ว (ไม่มีข้อมูลตอบกลับ)")
            break
            
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all('div', class_='movie-card')
        
        if not cards:
            print("     ✅ กวาดข้อมูลจนสุดแล้ว (หมดการ์ดหนัง)")
            break
            
        for card in cards:
            a_tag = card.find('a')
            img_tag = card.find('img')
            
            if a_tag and img_tag:
                full_link = format_url(a_tag.get('href', ''))
                
                # ตัดลิงก์ซ้ำตั้งแต่ตอนดึง
                if full_link in seen: 
                    continue
                seen.add(full_link)
                
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
                
        # ถ้าดึงมาได้น้อยกว่า 30 เรื่อง แสดงว่าเป็นหน้าสุดท้ายแน่นอน
        if len(cards) < 30:
            print("     ✅ กวาดข้อมูลจนสุดแล้ว (ถึงหน้าสุดท้ายพอดี)")
            break
            
        page += 1
        time.sleep(1.5) # พักจิบน้ำแป๊บนึง ไม่ให้เซิร์ฟเวอร์เว็บตกใจ
        
    return movies

# ================== Main Program ==================
if __name__ == "__main__":
    start_time = time.time()
    print("🚀 เริ่มต้นดึงข้อมูลเว็บหนังสั้นจีน (เวอร์ชัน Single-Page API Injection)\n")
    
    print("⚙️ กำลังเปิดเบราว์เซอร์ และทำการล้างสมอง Cloudflare...")
    driver = get_driver()
    
    all_groups_data = []
    
    try:
        # 🌟 เปิดหน้าเว็บแค่ "ครั้งเดียว" เพื่อขอวีซ่าจาก Cloudflare 
        driver.get(f"{DOMAIN}/categories.php")
        try:
            # รอจนกว่าหัวเว็บจะโหลดขึ้นมา (แปลว่าผ่าน Cloudflare แล้ว)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".site-header"))
            )
            print("✅ ผ่านด่าน Cloudflare สำเร็จ! เริ่มต้นดูดข้อมูลแบบไร้รอยต่อได้เลย\n")
        except:
            print("⚠️ ไม่สามารถยืนยันตัวตนกับ Cloudflare ได้ แต่จะลองฝืนดึงข้อมูลดู\n")
            
        # ลุยดึงทุกหมวดหมู่ผ่าน API จากหน้าเดิม โดยไม่เปลี่ยน URL อีกเลย!
        for cat in CATEGORIES:
            print(f"==================================================")
            print(f"🎬 หมวดหมู่: {cat['name']} (ID: {cat['id']})")
            print(f"==================================================")
            
            movies_data = process_category(driver, cat['name'], cat['id'])
            
            print(f"🎯 หมวด {cat['name']} กวาดมาได้ทั้งหมด {len(movies_data)} เรื่อง!\n")
            
            if movies_data:
                all_groups_data.append({
                    "name": f"🀄 {cat['name']}",
                    "image": "https://www.xn--72c9ab1ec1bc6q.online/assets/images/icon.webp",
                    "stations": movies_data
                })
                
    finally:
        driver.quit() # ปิดเบราว์เซอร์เมื่อกวาดเรียบทุกหมวดแล้ว
            
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
