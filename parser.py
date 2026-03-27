import requests

# URL API, который вы нашли
API_URL = "https://trade.tatneft.ru/promo/ajax/products.php"

def fetch_prices():
    """
    Получает цены на АИ-92 и АИ-95 (автоналив) с сайта Татнефти
    Возвращает словарь вида {"АИ-92": 69000, "АИ-95": 70500} или None в случае ошибки
    """
    try:
        # Отправляем GET-запрос к API
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        
        # Преобразуем JSON в Python-объект
        data = response.json()
        
        # Проверяем, что ответ успешный
        if data.get("result") != "success":
            print("API вернул ошибку:", data)
            return None
        
        prices = {}
        
        # Проходим по всем группам продуктов
        for group in data.get("list", []):
            group_name = group.get("name", "")
            
            # Нас интересуют только АИ-92 и АИ-95
            if "АИ-92" in group_name or "АИ-95" in group_name:
                # В каждой группе есть массив products с конкретными позициями
                for product in group.get("products", []):
                    # Нам нужен автотранспорт и формат "на розлив"
                    if (product.get("shipping_method") == "Автотранспорт" 
                        and product.get("format") == "for_bottling"
                        and product.get("online") == "yes"):  # доступно для покупки
                        
                        # Определяем, АИ-92 это или АИ-95
                        product_name = product.get("name", "")
                        price = product.get("price")
                        
                        if price is not None:
                            if "АИ-92" in product_name:
                                prices["АИ-92"] = float(price)
                            elif "АИ-95" in product_name:
                                prices["АИ-95"] = float(price)
        
        # Проверяем, что нашли оба продукта
        if "АИ-92" in prices and "АИ-95" in prices:
            return prices
        else:
            print("Не удалось найти цены для обоих продуктов")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")
        return None
    except ValueError as e:
        print(f"Ошибка при разборе JSON: {e}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return None

# Для тестирования (можно запустить этот файл отдельно)
if __name__ == "__main__":
    prices = fetch_prices()
    if prices:
        print(f"АИ-92: {prices['АИ-92']} ₽/т")
        print(f"АИ-95: {prices['АИ-95']} ₽/т")
    else:
        print("Не удалось получить цены")