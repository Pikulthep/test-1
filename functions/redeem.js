export async function onRequestPost(context) {
  const request = context.request;
  const formData = await request.formData();
  const code = formData.get('code');

  // ตรวจสอบรหัสผ่าน
  if (code === "LXSCXJZWC3") {
    const successHTML = `
    <!doctype html>
    <html lang="th">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title>ผลลัพธ์การตรวจสอบ</title>
            <!-- ดึง CSS จากไฟล์ของคุณเอง -->
            <link rel="stylesheet" href="/assets/style.css">
        </head>
        <body class="user-bg">
            <div class="user-wrap">
                <div class="user-card">
                    <div class="logo ok">✓</div>
                    <h1>ลิงก์เข้าสู่ระบบของคุณ</h1>
                    <div class="info-grid">
                        <div>
                            <span>แพ็กเกจ</span>
                            <b>พรีเมียม</b>
                        </div>
                        <div>
                            <span>ประเทศ</span>
                            <b>SN</b>
                        </div>
                        <div>
                            <span>จอที่ดูได้</span>
                            <b>4</b>
                        </div>
                    </div>
                    <div class="link-box">
                        <label>🖥️ ดูผ่านคอมพิวเตอร์ (PC)</label>
                        <div class="copy-row">
                            <input readonly value="https://www.netflix.com/browse?nftoken=MOCK_TOKEN_PC">
                            <button class="btn copy" data-copy="https://www.netflix.com/browse?nftoken=MOCK_TOKEN_PC">คัดลอก</button>
                            <a class="btn primary" target="_blank" href="https://www.netflix.com/browse?nftoken=MOCK_TOKEN_PC">เปิด</a>
                        </div>
                    </div>
                    <div class="link-box">
                        <label>📱 ดูผ่านมือถือ/แท็บเล็ต (Mobile)</label>
                        <div class="copy-row">
                            <input readonly value="https://www.netflix.com/unsupported?nftoken=MOCK_TOKEN_MOBILE">
                            <button class="btn copy" data-copy="https://www.netflix.com/unsupported?nftoken=MOCK_TOKEN_MOBILE">คัดลอก</button>
                            <a class="btn primary" target="_blank" href="https://www.netflix.com/unsupported?nftoken=MOCK_TOKEN_MOBILE">เปิด</a>
                        </div>
                    </div>
                    <p class="muted small">
                        รหัสของคุณ: <code>${code}</code>
                        <br>· เซสชันหมดอายุ: <code>2026-07-07 16:26:10 UTC</code>
                    </p>
                    <div class="row center">
                        <a class="btn ghost" href="/">← กลับไปหน้าแรก</a>
                    </div>
                </div>
            </div>
            <script>
                document.querySelectorAll('.copy').forEach(b => b.addEventListener('click', () => {
                    navigator.clipboard.writeText(b.dataset.copy);
                    const old = b.textContent;
                    b.textContent = 'คัดลอกแล้ว';
                    setTimeout(() => b.textContent = old, 1300);
                }));
            </script>
        </body>
    </html>
    `;

    return new Response(successHTML, {
      headers: { "Content-Type": "text/html; charset=utf-8" }
    });
  } 
  
  // กรณีที่กรอกรหัสผิด
  else {
    const errorHTML = `
    <!doctype html>
    <html lang="th">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title>เกิดข้อผิดพลาด</title>
            <!-- ดึง CSS จากไฟล์ของคุณเอง -->
            <link rel="stylesheet" href="/assets/style.css">
        </head>
        <body class="user-bg">
            <div class="user-wrap">
                <div class="user-card" style="text-align: center;">
                    <div class="logo" style="background: red;">X</div>
                    <h1>รหัสไม่ถูกต้อง</h1>
                    <p class="muted">ขออภัย รหัสที่คุณกรอกไม่ถูกต้อง หรืออาจจะหมดอายุการใช้งานไปแล้ว</p>
                    <br>
                    <a class="btn primary big" href="/">ลองใหม่อีกครั้ง</a>
                </div>
            </div>
        </body>
    </html>
    `;

    return new Response(errorHTML, {
      status: 400,
      headers: { "Content-Type": "text/html; charset=utf-8" }
    });
  }
}
