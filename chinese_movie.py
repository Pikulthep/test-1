import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime

# ================== CONFIG ==================
DOMAIN = "https://www.xn--72c9ab1ec1bc6q.online"

# 🌟 จัดเต็มทุกหมวดหมู่ ครอบคลุมหนังทั้งหมดกว่า 1,800 เรื่อง
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

# ================== ฟังก์ชันดึงข้อมูล ==================
def get_movies_from_category(cat_name, cat_id, max_page):
    movies = []
    api_url = f"{DOMAIN}/load_more_movies.php"
    
    for page in range(1, max_page + 1):
        print(f"  -> กำลังดึงหน้า {page}/{max_page} ...")
        try:
            if page == 1:
                # ดึงหน้าแรก
                url = f"{DOMAIN}/categories.php?id={cat_id}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                res = requests.get(url, headers=headers, timeout=15)
                html_data = res.text
            else:
                # ดึงหน้าถัดๆ ไป ผ่าน API ด้วยคำสั่ง POST แบบเนียนๆ
                payload = {'action': 'load_more_movies', 'page': page, 'category_id': cat_id}
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest'
                }
                res = requests.post(api_url, data=payload, headers=headers, timeout=15)
                html_data = res.text
                
            soup = BeautifulSoup(html_data, 'html.parser')
            cards = soup.find_all('div', class_='movie-card')
            
            if not cards:
                print("     [หมดหน้า] ไม่มีหนังเพิ่มเติมแล้ว")
                break
                
            for card in cards:
                a_tag = card.find('a')
                img_tag = card.find('img')
                
                if a_tag and img_tag:
                    # จัดการลิงก์และรูปภาพ
                    href = a_tag.get('href', '')
                    full_link = f"{DOMAIN}/{href.lstrip('/')}" if not href.startswith('http') else href
                    
                    src = img_tag.get('src', '')
                    full_img = f"{DOMAIN}/{src.lstrip('/')}" if not src.startswith('http') else src
                    
                    title = img_tag.get('alt', 'ไม่ทราบชื่อเรื่อง')
                    
                    # ตรวจสอบว่าหมวดซับไทย หรือ พากย์ไทย
                    info_text = "ซับไทย" if cat_name == "ซับไทย" else "พากย์ไทย"
                    
                    # 🌟 โครงสร้าง JSON ตามที่ผู้ใช้ต้องการเป๊ะๆ
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
            
    # ลบข้อมูลหนังที่ซ้ำกัน (ป้องกันเว็บส่งข้อมูลหน้าซ้อนกัน)
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
    print("🚀 เริ่มต้นดึงข้อมูลเว็บหนังสั้นจีน (เวอร์ชัน NatPlayer Fast Scrape)\n")
    
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
