import requests
from bs4 import BeautifulSoup

PRODUCT_URLS = {
    "АИ-92": "https://new.trade.tatneft.ru/promo/production/58",
    "АИ-95": "https://new.trade.tatneft.ru/promo/production/67"
}

def fetch_prices():
    prices = {}
    for product_name, url in PRODUCT_URLS.items():
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем все элементы с ценой
            price_elements = soup.find_all('div', class_='text-regular-28')
            
            max_price = 0
            for el in price_elements:
                price_text = el.get_text(strip=True)
                price_text = price_text.replace('\xa0', '').replace('₽', '').strip()
                if price_text.isdigit():
                    price = int(price_text)
                    if price > max_price:
                        max_price = price
            
            if max_price > 0:
                prices[product_name] = float(max_price)
            else:
                prices[product_name] = None
                
        except Exception as e:
            print(f"Ошибка парсинга {product_name}: {e}")
            prices[product_name] = None
    
    if any(p is None for p in prices.values()):
        return None
    return prices
