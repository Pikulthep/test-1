import requests
from bs4 import BeautifulSoup
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
MAX_WORKERS = 10 # จำนวน Thread ที่จะใช้วิ่งมุดเจาะพร้อมๆ กัน (เร็วสะใจแน่นอน)

# ================== ฟังก์ชันดึงข้อมูล ==================
def get_movie_video_link(movie_info):
    """ฟังก์ชันมุดเข้าไปในหน้าหนังแต่ละเรื่อง เพื่อดึงลิงก์ .m3u8 ออกมา"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': f"{DOMAIN}/categories.php"
    }
    
    try:
        res = requests.get(movie_info['url'], headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        m3u8_link = None
        
        # วิธีเจาะที่ 1: ดึงจากปุ่มเล่นวิดีโอ (id="posterPlayer")
        play_btn = soup.find('button', id='posterPlayer')
        if play_btn and play_btn.has_attr('data-video-url'):
            m3u8_link = play_btn['data-video-url']
            
        # วิธีเจาะที่ 2: ดึงจาก JSON-LD (เผื่อวิธีแรกเว็บเปลี่ยนโค้ด)
        if not m3u8_link:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                if 'contentUrl' in script.text and '.m3u8' in script.text:
                    match = re.search(r'"contentUrl"\s*:\s*"([^"]+)"', script.text)
                    if match:
                        m3u8_link = match.group(1)
                        break

        # จัดแพ็กเกจข้อมูลส่งกลับไป
        if m3u8_link:
            print(f"    ✅ เจาะลิงก์วิดีโอสำเร็จ: {movie_info['name']}")
            return {
                "name": movie_info['name'],
                "image": movie_info['image'],
                "url": m3u8_link,
                "info": "หนังสั้นจีน"
            }
        else:
            print(f"    ❌ ไม่พบลิงก์วิดีโอในหน้า: {movie_info['name']}")
            return None
            
    except Exception as e:
        print(f"    ⚠️ Error ขณะเจาะไฟล์วิดีโอ {movie_info['name']}: {e}")
        return None

def get_movies_from_category(cat_name, cat_id, max_page):
    movie_links_data = []
    # เพิ่ม Header พรางตัวให้เนียนขึ้น ป้องกันเว็บส่งข้อมูลเปล่ามาให้
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    }
    
    api_url = f"{DOMAIN}/load_more_movies.php"
    
    for page in range(1, max_page + 1):
        print(f"  -> กำลังดึงหน้ารวม {page}/{max_page} ...")
        try:
            if page == 1:
                url = f"{DOMAIN}/categories.php?id={cat_id}"
                res = requests.get(url, headers=headers, timeout=10)
                html_data = res.text
            else:
                payload = {'action': 'load_more_movies', 'page': page, 'category_id': cat_id}
                headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
                headers['X-Requested-With'] = 'XMLHttpRequest'
                res = requests.post(api_url, data=payload, headers=headers, timeout=10)
                html_data = res.text
                
            soup = BeautifulSoup(html_data, 'html.parser')
            cards = soup.find_all('div', class_='movie-card')
            
            if not cards:
                print("     [ไม่พบการ์ดหนัง] อาจจะหมดหน้า หรือถูกระบบป้องกันบล็อก")
                break
            
            for card in cards:
                a_tag = card.find('a')
                img_tag = card.find('img')
                
                if a_tag and img_tag:
                    href = a_tag.get('href', '')
                    # แก้ปัญหา slash ซ้อน (//) ด้วยการใช้ lstrip
                    full_link = f"{DOMAIN}/{href.lstrip('/')}" if not href.startswith('http') else href
                    
                    src = img_tag.get('src', '')
                    full_img = f"{DOMAIN}/{src.lstrip('/')}" if not src.startswith('http') else src
                    
                    title = img_tag.get('alt', 'ไม่ทราบชื่อเรื่อง')
                    
                    # เก็บลิงก์หน้าเว็บไว้ก่อน เพื่อเอาไปเจาะต่อ
                    movie_links_data.append({
                        "name": title,
                        "image": full_img,
                        "url": full_link
                    })
                    
        except Exception as e:
            print(f"     [Error] ดึงหน้ารวมล้มเหลว: {e}")
            
    # ตัดข้อมูลที่ซ้ำกัน
    unique_links = {v['url']: v for v in movie_links_data}.values()
    unique_links_list = list(unique_links)
    
    if unique_links_list:
        print(f"  🎯 พบลิงก์ทั้งหมด {len(unique_links_list)} เรื่อง กำลังเปิดระบบ Multithreading มุดไปเจาะไฟล์วิดีโอ...")
    
    # 🌟 วิ่งมุดเจาะเอาลิงก์วิดีโอ .m3u8 พร้อมๆ กัน
    final_movies = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(get_movie_video_link, unique_links_list)
        for res in results:
            if res:
                final_movies.append(res)
                
    return final_movies

# ================== Main Program ==================
if __name__ == "__main__":
    start_time = time.time()
    print("🚀 เริ่มต้นดึงข้อมูลและเจาะไฟล์เว็บหนังสั้นจีน (เวอร์ชัน Deep Dive)\n")
    
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
