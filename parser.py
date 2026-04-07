import requests
from bs4 import BeautifulSoup
#from config import TARGET_URL

def fetch_prices():
    try:
        response = requests.get(TARGET_URL, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Находим все карточки товаров
        product_cards = soup.find_all('div', class_='space-y-[20px] rounded-[16px] bg-white p-[20px]')
        
        prices = {}
        for card in product_cards:
            # Ищем название товара
            name_elem = card.find('div', class_='text-regular-23')
            if not name_elem:
                continue
            name = name_elem.get_text(strip=True)
            
            # Проверяем, что это АИ-92 или АИ-95
            if "АИ-92" in name:
                product_key = "АИ-92"
            elif "АИ-95" in name:
                product_key = "АИ-95"
            else:
                continue  # не наш продукт
            
            # Ищем цену в этом же блоке
            price_elem = card.find('div', class_='text-regular-28')
            if not price_elem:
                # Если не нашли, возможно цена в мобильной версии
                price_elem = card.find('div', class_='text-regular-28 max-md:hidden')
            
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Очищаем от &nbsp;, пробелов и символа рубля
                price_text = price_text.replace('\xa0', '').replace('₽', '').strip()
                price = float(price_text)
                prices[product_key] = price
        
        return prices if prices else None
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        return None
