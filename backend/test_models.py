import os
import google.generativeai as genai
from dotenv import load_dotenv

def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "AIzaSyYourGeminiKeyHere...":
        print("LỖI: Chưa có API Key hợp lệ trong file .env!")
        return

    print("Đang kết nối tới Google AI Studio...")
    genai.configure(api_key=api_key)

    print("\n--- CÁC MODEL BẠN ĐƯỢC PHÉP SỬ DỤNG ---")
    try:
        found = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ {m.name}")
                found = True
        
        if not found:
            print("❌ Không tìm thấy model nào hỗ trợ generateContent cho API Key này.")
    except Exception as e:
        print(f"❌ Lỗi khi lấy danh sách model: {e}")

if __name__ == "__main__":
    main()
