import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime

# ================== CONFIG ==================
DOMAIN = "https://www.xn--72c9ab1ec1bc6q.online" # โดเมนเว็บหนังสั้นจีน

# 🌟 ตั้งค่าหมวดหมู่ที่ต้องการดึง (ดู ID ได้จากลิงก์บนเว็บ หรือจากโค้ด HTML)
CATEGORIES = [
    {"name": "ข้ามมิติ", "id": "16", "max_page": 2}

]

SAVE_DIR = "output"
OUTPUT_FILE = os.path.join(SAVE_DIR, "chinese_movies.txt")

# ================== ฟังก์ชันดึงข้อมูล ==================
def get_movies_from_category(cat_name, cat_id, max_page):
    movies = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # เว็บนี้ใช้ระบบ API (POST) ในการโหลดหน้า 2, 3, 4... ซึ่งไวมาก!
    api_url = f"{DOMAIN}/load_more_movies.php"
    
    for page in range(1, max_page + 1):
        print(f"  -> กำลังดึงหน้า {page}/{max_page} ...")
        
        try:
            if page == 1:
                # หน้า 1 ดึงจาก URL ปกติ
                url = f"{DOMAIN}/categories.php?id={cat_id}"
                res = requests.get(url, headers=headers, timeout=10)
                html_data = res.text
            else:
                # หน้า 2 เป็นต้นไป ยิง API โหลดข้อมูลตรงๆ
                payload = {
                    'action': 'load_more_movies',
                    'page': page,
                    'category_id': cat_id
                }
                res = requests.post(api_url, data=payload, headers=headers, timeout=10)
                html_data = res.text
                
            if not html_data.strip():
                print("     [หมดหน้า] ไม่มีหนังเพิ่มเติมแล้ว")
                break
                
            soup = BeautifulSoup(html_data, 'html.parser')
            
            # ค้นหาการ์ดหนังทั้งหมด
            cards = soup.find_all('div', class_='movie-card')
            
            for card in cards:
                a_tag = card.find('a')
                img_tag = card.find('img')
                
                if a_tag and img_tag:
                    # 1. ดึงลิงก์
                    href = a_tag.get('href', '')
                    full_link = f"{DOMAIN}/{href}" if not href.startswith('http') else href
                    
                    # 2. ดึงรูปโปสเตอร์
                    src = img_tag.get('src', '')
                    full_img = f"{DOMAIN}/{src}" if not src.startswith('http') else src
                    
                    # 3. ดึงชื่อเรื่อง
                    title = img_tag.get('alt', 'ไม่ทราบชื่อเรื่อง')
                    
                    # เก็บเข้า List
                    movies.append({
                        "name": title,
                        "image": full_img,
                        "url": full_link,
                        "info": "หนังสั้นจีน"
                    })
                    
        except Exception as e:
            print(f"     [Error] ดึงข้อมูลล้มเหลว: {e}")
            
    # ลบข้อมูลที่ซ้ำกัน (ป้องกันบั๊กเว็บส่งหนังซ้ำ)
    unique_movies = {v['url']:v for v in movies}.values()
    return list(unique_movies)

# ================== Main Program ==================
if __name__ == "__main__":
    start_time = time.time()
    print("🚀 เริ่มต้นดึงข้อมูลเว็บหนังสั้นจีน\n")
    
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
    print(f"🎉 จบการทำงานทั้งหมดภายในเวลา {elapsed:.2f} วินาที!")
