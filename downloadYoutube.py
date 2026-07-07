import os
import re
import requests
from yt_dlp import YoutubeDL

def clean_filename(name):
    """Xóa các ký tự đặc biệt không hợp lệ trong tên file của Windows/Linux/Mac"""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def normalize_youtube_url(url):
    """
    Chuẩn hóa URL YouTube: Trích xuất ID video và đưa về dạng chuẩn duy nhất.
    Hỗ trợ cả link youtube.com, youtu.be và youtube.com/shorts
    """
    url = url.strip()
    # Biểu thức chính quy để tìm ID video (chứa 11 ký tự)
    regex = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([\w-]{11})'
    match = re.search(regex, url)
    
    if match:
        video_id = match.group(1)
        # Trả về định dạng URL chuẩn nhất, sạch sẽ nhất
        return f"https://www.youtube.com/watch?v={video_id}"
    else:
        # Nếu không trùng khớp, trả về None để báo link lỗi
        return None

def download_youtube_assets(url, custom_name=None, output_dir="Downloads"):
    # 1. CHUẨN HÓA URL TRƯỚC TIẾN
    clean_url = normalize_youtube_url(url)
    if not clean_url:
        print("❌ Lỗi: Đường dẫn YouTube không hợp lệ! Vui lòng kiểm tra lại.")
        return
    
    # Tạo thư mục lưu trữ nếu chưa có
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"⏳ Đang lấy thông tin video từ URL chuẩn: {clean_url}")
    
    # Cấu hình yt-dlp để lấy thông tin trước
    ydl_opts_info = {}
    with YoutubeDL(ydl_opts_info) as ydl:
        try:
            info = ydl.extract_info(clean_url, download=False)
            video_title = info.get('title', 'video')
            thumbnail_url = info.get('thumbnail')
        except Exception as e:
            print(f"❌ Lỗi khi lấy thông tin video: {e}")
            return

    # Xác định tên file cuối cùng (không kèm đuôi)
    if custom_name and custom_name.strip():
        final_name = clean_filename(custom_name.strip())
    else:
        final_name = clean_filename(video_title)

    # ----------------------------------------------------
    # 2. TẢI THUMBNAIL
    # ----------------------------------------------------
    if thumbnail_url:
        print("📸 Đang tải thumbnail...")
        try:
            clean_thumb_url = thumbnail_url.split('?')[0]
            thumb_ext = os.path.splitext(clean_thumb_url)[1]
            if not thumb_ext or len(thumb_ext) > 5: 
                thumb_ext = ".jpg"
                
            thumb_path = os.path.join(output_dir, f"{final_name}{thumb_ext}")
            
            response = requests.get(thumbnail_url, stream=True)
            if response.status_code == 200:
                with open(thumb_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                print(f"✅ Đã tải thumbnail: {thumb_path}")
            else:
                print("⚠️ Không thể tải ảnh thumbnail.")
        except Exception as e:
            print(f"⚠️ Lỗi khi tải thumbnail: {e}")

    # ----------------------------------------------------
    # 3. TẢI VIDEO (ĐÃ FIX LỖI FFMPEG)
    # ----------------------------------------------------
    print("🎥 Đang tải video (vui lòng chờ)...")
    
    ydl_opts_video = {
        'noplaylist': True,
        'format': 'best', # Lấy file chứa sẵn cả hình + tiếng (Không lo lỗi thiếu FFmpeg nữa)
        'outtmpl': os.path.join(output_dir, f"{final_name}.%(ext)s"),
    }
    
    try:
        with YoutubeDL(ydl_opts_video) as ydl:
            ydl.download([clean_url])
        print(f"🎉 Hoàn thành! Kiểm tra thư mục '{output_dir}'.")
    except Exception as e:
        print(f"❌ Lỗi khi tải video: {e}")

# --- KHU VỰC CHẠY TOOL ---
if __name__ == "__main__":
    youtube_url = input("Nhập URL video YouTube: ").strip()
    custom_title = input("Nhập tên muốn đổi (Bấm Enter để lấy tên gốc): ").strip()
    
    download_youtube_assets(youtube_url, custom_name=custom_title)