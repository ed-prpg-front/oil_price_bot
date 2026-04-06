import requests
from config import TARGET_URL

def fetch_prices():
    try:
        response = requests.get(TARGET_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Данные лежат внутри ключа "data"
        items = data.get("data", [])
        prices = {}
        
        for item in items:
            name = item.get("name")
            price = item.get("min_price")
            if name and price:
                if "АИ-92" in name:
                    prices["АИ-92"] = float(price)
                elif "АИ-95" in name:
                    prices["АИ-95"] = float(price)
        
        # Если нашли оба продукта — возвращаем, иначе None
        return prices if len(prices) == 2 else None
        
    except Exception as e:
        print(f"Ошибка получения цен: {e}")
        return None
