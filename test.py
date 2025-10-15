import requests

# O'z token va chat ID ingizni qo'ying
TOKEN = '8103713689:AAGfZPutlB7apOiPWGYYaUXHnhJPl8NGCeE'
CHAT_ID = '7782143104'

def test_bot():
    print("🤖 Botni tekshirish...")
    
    # 1. Bot ma'lumotlarini olish
    url = f"https://api.telegram.org/bot{TOKEN}/getMe"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('ok'):
            bot_name = data['result']['first_name']
            print(f"✅ Bot topildi: {bot_name}")
        else:
            print(f"❌ Bot topilmadi: {data}")
            return False
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return False

def test_chat():
    print("💬 Chatni tekshirish...")
    
    # 2. Xabar yuborish
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': '🔧 Test xabari - Bu Flask loyihasidan test!',
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        data = response.json()
        
        if data.get('ok'):
            print("✅ Test xabar yuborildi! Telegram bot ishlayapti 🎉")
            return True
        else:
            print(f"❌ Xabar yuborilmadi: {data}")
            return False
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return False

if __name__ == "__main__":
    print("Telegram bot testi boshlanmoqda...")
    
    if test_bot():
        test_chat()
    else:
        print("Iltimos, token ni tekshiring!")