import requests
from bs4 import BeautifulSoup
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
def get_movies_from_category(cat_name, cat_id):
    movies = []
    
    # 🌟 สร้าง Session เพื่อเก็บคุกกี้ ป้องกันการโดนเตะ
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': f"{DOMAIN}/categories.php?id={cat_id}"
    }
    
    try:
        # ดึงหน้าแรก (หน้าที่ 1) เพื่อเอาคุกกี้และข้อมูลชุดแรก 30 เรื่อง
        print(f"  -> ดึงหน้า 1...")
        res = session.get(f"{DOMAIN}/categories.php?id={cat_id}", headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        cards = soup.find_all('div', class_='movie-card')
        
        # 🌟 ลูปยิง API ขอหน้า 2, 3, 4 ไปเรื่อยๆ จนกว่ามันจะส่งเนื้อหาเปล่ามาให้
        page = 2
        while True:
            print(f"  -> ดึงหน้า {page}...")
            api_url = f"{DOMAIN}/load_more_movies.php"
            payload = {'action': 'load_more_movies', 'page': page, 'category_id': cat_id}
            
            # ยิง POST ตามแบบฉบับที่หน้าเว็บมันเขียนเป๊ะๆ
            post_headers = headers.copy()
            post_headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            post_headers['X-Requested-With'] = 'XMLHttpRequest'
            
            api_res = session.post(api_url, data=payload, headers=post_headers, timeout=10)
            html_data = api_res.text
            
            # ถ้า API ส่งค่าว่างมา แปลว่าหนังหมดหมวดแล้ว
            if not html_data.strip():
                print("     ✅ หมดแล้ว! ไม่มีหนังเพิ่มเติม")
                break
                
            api_soup = BeautifulSoup(html_data, 'html.parser')
            new_cards = api_soup.find_all('div', class_='movie-card')
            
            if not new_cards:
                print("     ✅ หมดแล้ว! ไม่พบการ์ดหนัง")
                break
                
            # เอาการ์ดหนังหน้าใหม่ไปรวมกับของเก่า
            cards.extend(new_cards)
            
            # เช็คว่าถ้าหน้าสุดท้ายมันดึงมาไม่ถึง 30 เรื่อง แปลว่าหมดพอดี ไม่ต้องขอหน้าถัดไปแล้ว
            if len(new_cards) < 30:
                print("     ✅ หมดแล้ว! ถึงหน้าสุดท้ายพอดี")
                break
                
            page += 1
            time.sleep(1) # พักหายใจ 1 วิ ป้องกันโดนแบน
            
        # ================== แกะข้อมูลใส่แพ็กเกจ JSON ==================
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
    print("🚀 เริ่มต้นดึงข้อมูลเว็บหนังสั้นจีน (เวอร์ชัน API Direct + NatPlayer)\n")
    
    all_groups_data = []
    
    for cat in CATEGORIES:
        print(f"==================================================")
        print(f"🎬 หมวดหมู่: {cat['name']} (ID: {cat['id']})")
        print(f"==================================================")
        
        movies_data = get_movies_from_category(cat['name'], cat['id'])
        
        print(f"✅ หมวด {cat['name']} ดึงสำเร็จ {len(movies_data)} เรื่อง\n")
        
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
