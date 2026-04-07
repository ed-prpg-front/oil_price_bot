import requests
from config import TARGET_URL

def fetch_prices():
    try:
        response = requests.get(TARGET_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
        prices = {}
        
        # Если данные приходят внутри ключа "data"
        if isinstance(data, dict) and "data" in data:
            items = data["data"]
        elif isinstance(data, list):
            items = data
        else:
            items = []
        
        for item in items:
            name = item.get("name")
            # Проверяем, что в способах доставки есть PICKUP (автоналив)
            delivery_types = item.get("product_delivery_types", [])
            if "PICKUP" not in delivery_types:
                continue  # пропускаем товары, которые нельзя отгрузить автотранспортом
            
            price = item.get("min_price")
            if name and price:
                if "АИ-92" in name:
                    prices["АИ-92"] = float(price)
                elif "АИ-95" in name:
                    prices["АИ-95"] = float(price)
        
        return prices if prices else None
    except Exception as e:
        print(f"Ошибка получения цен: {e}")
        return None
