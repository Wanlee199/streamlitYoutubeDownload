import streamlit as st
import os
import re
import requests
import io
import zipfile
from yt_dlp import YoutubeDL

# --- CÁC HÀM BỔ TRỢ ---
def clean_filename(name):
    """Xóa ký tự đặc biệt để làm tên file hợp lệ"""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def normalize_youtube_url(url):
    """Chuẩn hóa URL YouTube từ bất kỳ dạng nào"""
    url = url.strip()
    regex = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([\w-]{11})'
    match = re.search(regex, url)
    return f"https://www.youtube.com/watch?v={match.group(1)}" if match else None

# --- KHỞI TẠO CÁC BIẾN TRẠNG THÁI (SESSION STATE) ---
if 'zip_data' not in st.session_state:
    st.session_state['zip_data'] = None
if 'is_scanning' not in st.session_state:
    st.session_state['is_scanning'] = False

# --- GIAO DIỆN WEB ---
st.set_page_config(page_title="YouTube Bulk Downloader", page_icon="🗂️", layout="centered")

st.title("🗂️ YouTube Bulk Downloader (Upload TXT)")
st.write("Upload file `.txt` chứa danh sách link YouTube để đóng gói ZIP tải về hàng loạt.")

# Thanh upload file
uploaded_file = st.file_uploader("Chọn file .txt chứa danh sách URL YouTube:", type=["txt"])

# Thêm nút tải file mẫu list.txt
if os.path.exists("list.txt"):
    try:
        with open("list.txt", "r", encoding="utf-8") as f:
            sample_data = f.read()
        st.download_button(
            label="📄 Tải xuống file mẫu list.txt",
            data=sample_data,
            file_name="list.txt",
            mime="text/plain",
            key="download_sample_list"
        )
    except Exception as e:
        pass

if uploaded_file is not None:
    # Đọc danh sách URL từ file txt
    raw_content = uploaded_file.read().decode("utf-8")
    urls = [line.strip() for line in raw_content.splitlines() if line.strip()]
    
    if not urls:
        st.error("❌ File .txt trống hoặc không tìm thấy URL nào.")
    else:
        st.success(f"📋 Tìm thấy {len(urls)} đường dẫn trong file.")
        
        with st.expander("Xem chi tiết danh sách URL"):
            for i, u in enumerate(urls, 1):
                st.write(f"{i}. {u}")
        
        # Định nghĩa callback để đặt trạng thái đang quét
        def handle_scan_callback():
            st.session_state['is_scanning'] = True

        # Nút kích hoạt đóng gói (Quét video)
        st.button(
            "⚡ Bắt đầu quét và chuẩn bị File ZIP", 
            use_container_width=True, 
            disabled=st.session_state['is_scanning'], 
            on_click=handle_scan_callback
        )
        
        if st.session_state['is_scanning']:
            # Reset lại trạng thái tải về khi người dùng quét danh sách mới
            st.session_state['zip_data'] = None
            
            try:
                zip_buffer = io.BytesIO()
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    success_count = 0
                    
                    for index, raw_url in enumerate(urls):
                        clean_url = normalize_youtube_url(raw_url)
                        if not clean_url:
                            st.warning(f"⚠️ Dòng {index+1}: URL không hợp lệ -> `{raw_url}`")
                            continue
                            
                        status_text.text(f"⏳ Đang xử lý ({index+1}/{len(urls)}): {clean_url}")
                        
                        try:
                            with YoutubeDL({}) as ydl:
                                info = ydl.extract_info(clean_url, download=False)
                                video_title = info.get('title', f"video_{index+1}")
                                thumbnail_url = info.get('thumbnail')
                            
                            final_name = clean_filename(video_title)
                            
                            # A. Đóng gói Thumbnail
                            if thumbnail_url:
                                clean_thumb_url = thumbnail_url.split('?')[0]
                                thumb_ext = os.path.splitext(clean_thumb_url)[1] or ".jpg"
                                img_response = requests.get(thumbnail_url)
                                if img_response.status_code == 200:
                                    zip_file.writestr(f"{final_name}{thumb_ext}", img_response.content)
                            
                            # B. Đóng gói Video
                            temp_video_path = f"temp_{index}_{final_name}.mp4"
                            ydl_opts_video = {
                                'noplaylist': True,
                                'format': 'best',
                                'outtmpl': temp_video_path,
                                'quiet': True,
                            }
                            with YoutubeDL(ydl_opts_video) as ydl:
                                ydl.download([clean_url])
                            
                            if os.path.exists(temp_video_path):
                                with open(temp_video_path, "rb") as f:
                                    zip_file.writestr(f"{final_name}.mp4", f.read())
                                os.remove(temp_video_path)
                                
                            success_count += 1
                            
                        except Exception as e:
                            st.error(f"❌ Lỗi ở dòng {index+1}: {e}")
                            if os.path.exists(temp_video_path):
                                os.remove(temp_video_path)
                        
                        progress_bar.progress((index + 1) / len(urls))
                
                st.session_state['zip_data'] = zip_buffer.getvalue()
                status_text.text(f"✅ Đã xử lý xong! Đóng gói thành công {success_count}/{len(urls)} video vào bộ nhớ tạm.")
            finally:
                st.session_state['is_scanning'] = False
                st.rerun()

        # --- KHU VỰC NÚT DOWNLOAD VỚI CHỐNG SPAM & LOADING ---
        if st.session_state['zip_data'] is not None:
            st.write("---")
            st.subheader("🎁 File của bạn đã sẵn sàng!")
            
            import base64
            zip_b64 = base64.b64encode(st.session_state['zip_data']).decode('utf-8')
            
            # Nút tải xuống tùy chỉnh sử dụng HTML/CSS/JS thuần để có hiệu ứng vô hiệu hóa ngay lập tức
            custom_download_html = f"""
            <style>
            .download-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                width: 100%;
                margin-top: 10px;
            }}
            .custom-download-btn {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 100%;
                height: 45px;
                background: linear-gradient(135deg, #FF4B4B 0%, #FF2B2B 100%);
                color: #FFFFFF !important;
                border: none;
                border-radius: 8px;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 16px;
                font-weight: 600;
                text-decoration: none !important;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(255, 75, 75, 0.25);
                user-select: none;
                text-align: center;
            }}
            .custom-download-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(255, 75, 75, 0.4);
                background: linear-gradient(135deg, #FF6B6B 0%, #FF4B4B 100%);
            }}
            .custom-download-btn:active {{
                transform: translateY(1px);
            }}
            .custom-download-btn.disabled {{
                background: #4A4A4A !important;
                color: #888888 !important;
                cursor: not-allowed;
                pointer-events: none;
                box-shadow: none;
                transform: none;
            }}
            </style>
            
            <div class="download-container">
                <a href="data:application/zip;base64,{zip_b64}" 
                   download="youtube_bulk_downloads.zip" 
                   id="zip-download-btn" 
                   class="custom-download-btn" 
                   onclick="this.classList.add('disabled'); this.innerHTML='⏳ Đang chuẩn bị và tải xuống... Vui lòng chờ'; var btn=this; setTimeout(function(){{ btn.classList.remove('disabled'); btn.innerHTML='📥 BẤM VÀO ĐÂY ĐỂ TẢI XUỐNG FILE .ZIP'; }}, 5000);">
                    📥 BẤM VÀO ĐÂY ĐỂ TẢI XUỐNG FILE .ZIP
                </a>
            </div>
            """
            st.markdown(custom_download_html, unsafe_allow_html=True)