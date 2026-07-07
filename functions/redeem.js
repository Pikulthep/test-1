export async function onRequestPost(context) {
  const request = context.request;
  const formData = await request.formData();
  const code = formData.get('code');

  // ตรวจสอบรหัสผ่าน (สามารถเพิ่มรหัสอื่นๆ หรือเชื่อมต่อ Database ได้ในอนาคต)
  if (code === "LXSCXJZWC3") {
    
    // โค้ด HTML หน้าผลลัพธ์ (แก้ไขคำว่า พรีเมียม ให้แสดงผลถูกต้องแล้ว)
    const successHTML = `
    <!doctype html>
    <html lang="vi">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title>Kết quả</title>
            <link rel="stylesheet" href="https://netflix.lunakey.net/assets/style.css">
        </head>
        <body class="user-bg">
            <div class="user-wrap">
                <div class="user-card">
                    <div class="logo ok">✓</div>
                    <h1>Link đăng nhập của bạn</h1>
                    <div class="info-grid">
                        <div>
                            <span>Plan</span>
                            <b>พรีเมียม</b>
                        </div>
                        <div>
                            <span>Country</span>
                            <b>SN</b>
                        </div>
                        <div>
                            <span>Streams</span>
                            <b>4</b>
                        </div>
                    </div>
                    <div class="link-box">
                        <label>🖥️ PC</label>
                        <div class="copy-row">
                            <input readonly value="https://www.netflix.com/browse?nftoken=MOCK_TOKEN_PC">
                            <button class="btn copy" data-copy="https://www.netflix.com/browse?nftoken=MOCK_TOKEN_PC">Copy</button>
                            <a class="btn primary" target="_blank" href="https://www.netflix.com/browse?nftoken=MOCK_TOKEN_PC">Mở</a>
                        </div>
                    </div>
                    <div class="link-box">
                        <label>📱 Mobile</label>
                        <div class="copy-row">
                            <input readonly value="https://www.netflix.com/unsupported?nftoken=MOCK_TOKEN_MOBILE">
                            <button class="btn copy" data-copy="https://www.netflix.com/unsupported?nftoken=MOCK_TOKEN_MOBILE">Copy</button>
                            <a class="btn primary" target="_blank" href="https://www.netflix.com/unsupported?nftoken=MOCK_TOKEN_MOBILE">Mở</a>
                        </div>
                    </div>
                    <p class="muted small">
                        Mã của bạn: <code>${code}</code>
                        <br>· Token hết hạn: <code>2026-07-07 16:26:10 UTC</code>
                    </p>
                    <div class="row center">
                        <a class="btn ghost" href="/">← Quay lại</a>
                    </div>
                </div>
            </div>
            <script>
                document.querySelectorAll('.copy').forEach(b => b.addEventListener('click', () => {
                    navigator.clipboard.writeText(b.dataset.copy);
                    const old = b.textContent;
                    b.textContent = 'Đã copy';
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
  
  // กรณีที่กรอกรหัสผิด จะแสดงหน้าแจ้งเตือนง่ายๆ และปุ่มกลับไปหน้าแรก
  else {
    const errorHTML = `
    <!doctype html>
    <html lang="vi">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title>Lỗi</title>
            <link rel="stylesheet" href="https://netflix.lunakey.net/assets/style.css">
        </head>
        <body class="user-bg">
            <div class="user-wrap">
                <div class="user-card" style="text-align: center;">
                    <div class="logo" style="background: red;">X</div>
                    <h1>Mã không hợp lệ</h1>
                    <p class="muted">Rất tiếc, mã bạn nhập không chính xác hoặc đã hết hạn.</p>
                    <br>
                    <a class="btn primary big" href="/">Quay lại</a>
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