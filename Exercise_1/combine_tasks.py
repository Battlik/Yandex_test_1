from support_platform_sql import SupportPlatform
import random
from datetime import datetime

# Списки для генерации случайных данных
first_names = ["Антон", "Наталья", "Виталий", "Екатерина", "Игорь", "Мария",
               "Сергей", "Ольга", "Дмитрий", "Елена"]
last_names = ["Иванов", "Петров", "Сидоров", "Кузнецов", "Попов",
              "Васильев", "Зайцев", "Смирнов", "Морозов", "Соколов"]
cities = ["Москва", "Уфа", "Краснодар", "Самара", "Казань",
          "Екатеринбург", "Новосибирск", "Питер", "Калининград", "Сочи"]
positions = ["Младший специалист", "Старший специалист", "Team Lead",
             "Менеджер", "Директор", "Инженер", "Аналитик"]
# Тексты для сообщений
user_messages = ["Здравствуйте, у меня вопрос по заказу",
                 "Когда придет мой заказ?",
                 "Спасибо за помощь",
                 "Где мой заказ?",
                 "Заказ задерживается"]
operator_messages = ["Здравствуйте! Как я могу помочь?",
                     "Ваш заказ в пути",
                     "Приносим извинения за задержку",
                     "Хорошего дня!",
                     "Спасибо за обращение"]
operator_special = ["Отлично, рад был помочь!",
                    "Отлично! Мы всегда рады помочь",
                    "Все отлично, спасибо, что обратились!"]


platform = SupportPlatform("platform.db")

# 1) Создаём клиентов
client_ids = []
for i in range(10):
    username = f"user{i+1}"
    name = random.choice(first_names)
    city = random.choice(cities)
    birth_year = random.randint(1970, 2000)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    birth_date = f"{birth_year:04d}-{birth_month:02d}-{birth_day:02d}"
    position = random.choice(positions)
    experience = random.randint(1, 20)
    client_id = platform.add_client(username, name, city, birth_date, position, experience)
    client_ids.append(client_id)

# 2) Создаём операторов
operator_ids = []
for i in range(3):
    full_name = random.choice(first_names) + " " + random.choice(last_names)
    city = random.choice(cities)
    birth_year = random.randint(1980, 2000)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    birth_date = f"{birth_year:04d}-{birth_month:02d}-{birth_day:02d}"
    position = "Оператор поддержки"
    experience = random.randint(1, 10)
    operator_id = platform.add_operator(full_name, city, birth_date, position, experience)
    operator_ids.append(operator_id)

# 3) Генерируем 100 чатов
chat_ids = []
for i in range(100):
    client_id = random.choice(client_ids)
    chat_id = platform.new_chat(client_id)
    chat_ids.append(chat_id)
    for j in range(random.randint(2, 4)):
        # Сообщение от клиента
        text = random.choice(user_messages)
        platform.send_message(chat_id, "client", text)
        # Ответ оператора
        if random.random() < 0.1:
            # С вероятностью 0.1 включаем слово "отлично"
            text = random.choice(operator_special)
        else:
            text = random.choice(operator_messages)
        platform.send_message(chat_id, "operator", text)
    # Закрываем чат с вероятностью 0.8
    if random.random() < 0.8:
        csat = random.randint(1, 5)
        platform.close_chat(chat_id, csat)

# 4) Генерируем таблицу заказов для SQL-задания
places = ["Теремок", "Вкусно и точка", "Евразия", "Кафе Пушкин", "Якитория"]
order_id = 1
for client_id in client_ids:
    # Каждый клиент делает от 1 до 10 заказов
    num_orders = random.randint(1, 10)
    for j in range(num_orders):
        price = random.randint(100, 5000)
        place = random.choice(places)
        # Вставляем заказ
        platform.cursor.execute(
            "INSERT INTO orders (order_id, price, order_client_id, place) VALUES (?, ?, ?, ?)",
            (order_id, price, client_id, place)
        )
        platform.conn.commit()
        # Привязываем некоторым чатам этот заказ (30% случаев)
        if random.random() < 0.3:
            platform.cursor.execute(
                "SELECT chat_id FROM chats WHERE client_id=? ORDER BY RANDOM() LIMIT 1",
                (client_id,)
            )
            row = platform.cursor.fetchone()
            if row:
                random_chat = row[0]
                platform.cursor.execute(
                    "UPDATE chats SET ticket_order_id=? WHERE chat_id=?",
                    (order_id, random_chat)
                )
                platform.conn.commit()
        order_id += 1

platform.conn.close()
print("Данные сгенерированы и сохранены в базе platform.db")
