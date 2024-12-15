import hmac

import requests

from loader import SECRET_KEY, BOT_TOKEN, CHANNEL_ID, ADMIN_ID, ADMIN_ID2, ADMIN_ID3, db, MERCHANT_DOMAIN

import sqlite3


def generate_merchant_signature(merchant_account, merchant_domain, order_reference, order_date, amount, currency, product_name, product_price, product_count):
    signature_string = f"{merchant_account};{merchant_domain};{order_reference};{order_date};{amount};{currency};"
    signature_string += f"{';'.join(product_name)};{';'.join(map(str, product_count))};{';'.join(map(str, product_price))}"
    hash_signature = hmac.new(SECRET_KEY.encode('utf-8'), signature_string.encode('utf-8'), digestmod='md5').hexdigest()
    return hash_signature


def generate_signature(order_reference, status, current_time, secret_key=SECRET_KEY):
    data_string = f"{order_reference};{status};{current_time}"
    signature = hmac.new(secret_key.encode('utf-8'), data_string.encode('utf-8'), digestmod='md5').hexdigest()
    return signature


def extract_user_id_from_reference(order_reference):
    return order_reference.split("_")[1]

def get_user_info_from_telegram(user_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
    params = {
        'chat_id': CHANNEL_ID,  # ID канала или группы
        'user_id': user_id  # ID пользователя
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            user_info = data['result']['user']
            return user_info  # возвращает данные о пользователе (например, 'username', 'first_name', 'last_name')
        else:
            print("Ошибка получения информации о пользователе")
            return None
    else:
        print("Ошибка запроса к API Telegram")
        return None


def check_user_in_subs(user_id):
    # Отправляем GET-запрос
    url = f"{MERCHANT_DOMAIN}/tables"
    response = requests.get(url)

    # Проверяем, что запрос успешен
    if response.status_code == 200:
        data = response.json()

        # Ищем пользователя в таблице "subs"
        subs = data.get('subs', [])
        for sub in subs:
            if sub.get('subsuser') == user_id:
                print(f"User {user_id} found in subscriptions.")
                return True
        print(f"User {user_id} not found in subscriptions.")
        return False
    else:
        print(f"Failed to get data. Status code: {response.status_code}")
        return False

def get_table_data(table_name):
    try:
        conn = sqlite3.connect('database.db')  # Укажите путь к вашей базе данных
        cursor = conn.cursor()

        # Выполняем запрос для получения всех данных из таблицы
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()  # Получаем все строки из таблицы

        # Получаем имена колонок
        column_names = [description[0] for description in cursor.description]

        conn.close()

        # Возвращаем данные таблицы как список словарей (для лучшей читаемости)
        return [dict(zip(column_names, row)) for row in rows]
    except Exception as e:
        return {"error": str(e)}  # Возвращаем ошибку в формате JSON

def get_table_names():
    try:
        conn = sqlite3.connect('database.db')  # Укажите путь к вашей базе данных
        cursor = conn.cursor()

        # Запрос для получения всех таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()  # Получаем все таблицы

        conn.close()

        # Возвращаем имена всех таблиц
        return [table[0] for table in tables]  # Это список имен таблиц
    except Exception as e:
        return str(e)  # Возвращаем ошибку, если она возникла


def add_user_to_channel(user_id):
    dbuser = db.get_user(user_id)
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/approveChatJoinRequest?chat_id={CHANNEL_ID}&user_id={user_id}")
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={user_id}&text=Дякуємо за оплату! Ваша місячна підписка на канал LookBook активована.")
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={ADMIN_ID}&text=Користувач @{dbuser[0]} - {dbuser[1]} доданий до каналу!")
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={ADMIN_ID2}&text=Користувач @{dbuser[0]} - {dbuser[1]} доданий до каналу!")

def delete_user_from_channel(user_id):
    user_info = get_user_info_from_telegram(user_id)
    ban_url = f'https://api.telegram.org/bot{BOT_TOKEN}/banChatMember'
    ban_params = {
        'chat_id': CHANNEL_ID,
        'user_id': user_id
    }
    ban_response = requests.post(ban_url, params=ban_params)

    if ban_response.status_code == 200:
        unban_url = f'https://api.telegram.org/bot{BOT_TOKEN}/unbanChatMember'
        unban_params = {
            'chat_id': CHANNEL_ID,
            'user_id': user_id
        }
        unban_response = requests.post(unban_url, params=unban_params)
        print("Користувача видалено з каналу.")

        if user_info:
            username = user_info.get('username', 'Неизвестно')
            fullname = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}"

            requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={ADMIN_ID}&text=Користувачa @{username} - {fullname} видалено каналу!")
    else:
        print("Помилка при видаленні користувача:", ban_response.json())

