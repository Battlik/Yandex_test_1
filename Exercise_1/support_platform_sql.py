import sqlite3
import random
from datetime import datetime
import json

# Класс для работы с платформой поддержки
class SupportPlatform:
    def __init__(self, db_path="platform.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Таблица клиентов (пользователей)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id INTEGER PRIMARY KEY,
            username TEXT,
            name TEXT,
            city TEXT,
            birth_date TEXT,
            position TEXT,
            experience INTEGER
        )
        """)
        # Таблица операторов
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS operators (
            operator_id INTEGER PRIMARY KEY,
            name TEXT,
            city TEXT,
            birth_date TEXT,
            position TEXT,
            experience INTEGER
        )
        """)
        # Таблица чатов (тикетов)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY,
            client_id INTEGER,
            operator_id INTEGER,
            is_closed INTEGER,
            csat INTEGER,
            creation_time TEXT,
            close_time TEXT,
            ticket_order_id INTEGER,
            FOREIGN KEY(client_id) REFERENCES clients(client_id),
            FOREIGN KEY(operator_id) REFERENCES operators(operator_id),
            FOREIGN KEY(ticket_order_id) REFERENCES orders(order_id)
        )
        """)
        # Таблица сообщений
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            sender TEXT,
            text TEXT,
            timestamp TEXT,
            FOREIGN KEY(chat_id) REFERENCES chats(chat_id)
        )
        """)
        # Таблица заказов для SQL-заданий
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            price INTEGER,
            order_client_id INTEGER,
            place TEXT,
            FOREIGN KEY(order_client_id) REFERENCES clients(client_id)
        )
        """)
        self.conn.commit()

    # Добавить нового клиента (пользователя)
    def add_client(self, username, name, city, birth_date, position, experience):
        self.cursor.execute(
            "INSERT INTO clients (username, name, city, birth_date, position, experience) VALUES (?, ?, ?, ?, ?, ?)",
            (username, name, city, birth_date, position, experience)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    # Добавить нового оператора поддержки
    def add_operator(self, name, city, birth_date, position, experience):
        self.cursor.execute(
            "INSERT INTO operators (name, city, birth_date, position, experience) VALUES (?, ?, ?, ?, ?)",
            (name, city, birth_date, position, experience)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    # Создать новый чат (тикет) от клиента
    def new_chat(self, client_id, ticket_order_id=None):
        # Найти случайного свободного оператора (у которого нет незакрытых чатов)
        self.cursor.execute("""
        SELECT operator_id
        FROM operators
        WHERE operator_id NOT IN (
            SELECT operator_id FROM chats WHERE is_closed=0
        )
        """)
        free_ops = [row[0] for row in self.cursor.fetchall()]
        if not free_ops:
            # Если свободных операторов нет, выбираем случайного
            self.cursor.execute("SELECT operator_id FROM operators")
            free_ops = [row[0] for row in self.cursor.fetchall()]
        operator_id = random.choice(free_ops) if free_ops else None
        creation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # По умолчанию чат открыт (is_closed=0), csat = NULL до закрытия
        self.cursor.execute("""
        INSERT INTO chats (client_id, operator_id, is_closed, csat, creation_time, close_time, ticket_order_id)
        VALUES (?, ?, 0, NULL, ?, NULL, ?)
        """, (client_id, operator_id, creation_time, ticket_order_id))
        self.conn.commit()
        return self.cursor.lastrowid

    # Отправить сообщение в чат
    def send_message(self, chat_id, sender, text):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO messages (chat_id, sender, text, timestamp) VALUES (?, ?, ?, ?)",
            (chat_id, sender, text, timestamp)
        )
        self.conn.commit()

    # Закрыть чат оператором с выставлением CSAT
    def close_chat(self, chat_id, csat):
        close_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "UPDATE chats SET is_closed=1, csat=?, close_time=? WHERE chat_id=?",
            (csat, close_time, chat_id)
        )
        self.conn.commit()

    # Выгрузка всех чатов в формате JSON
    def export_all_chats(self):
        self.cursor.execute("SELECT chat_id, client_id, operator_id, is_closed, csat, creation_time, close_time FROM chats")
        chats = []
        for row in self.cursor.fetchall():
            chat_id, client_id, operator_id, is_closed, csat, creation_time, close_time = row
            # Получаем ник клиента
            self.cursor.execute("SELECT username FROM clients WHERE client_id=?", (client_id,))
            client_row = self.cursor.fetchone()
            username = client_row[0] if client_row else None
            # Получаем имя оператора
            self.cursor.execute("SELECT name FROM operators WHERE operator_id=?", (operator_id,))
            op_row = self.cursor.fetchone()
            operator_name = op_row[0] if op_row else None
            # Получаем сообщения чата
            self.cursor.execute(
                "SELECT sender, text, timestamp FROM messages WHERE chat_id=? ORDER BY timestamp",
                (chat_id,)
            )
            messages = [{"sender": mrow[0], "text": mrow[1], "timestamp": mrow[2]} for mrow in self.cursor.fetchall()]
            chats.append({
                "chat_id": chat_id,
                "client": username,
                "operator": operator_name,
                "is_closed": bool(is_closed),
                "csat": csat,
                "creation_time": creation_time,
                "close_time": close_time,
                "messages": messages
            })
        output = json.dumps(chats, ensure_ascii=False, indent=2)
        print(output)

    # Выгрузка чатов для конкретного оператора
    def export_chats_by_operator(self, operator_id):
        self.cursor.execute(
            "SELECT chat_id, client_id, is_closed, csat, creation_time, close_time FROM chats WHERE operator_id=?",
            (operator_id,)
        )
        chats = []
        for row in self.cursor.fetchall():
            chat_id, client_id, is_closed, csat, creation_time, close_time = row
            self.cursor.execute("SELECT username FROM clients WHERE client_id=?", (client_id,))
            client_row = self.cursor.fetchone()
            username = client_row[0] if client_row else None
            self.cursor.execute(
                "SELECT sender, text, timestamp FROM messages WHERE chat_id=? ORDER BY timestamp",
                (chat_id,)
            )
            messages = [{"sender": mrow[0], "text": mrow[1], "timestamp": mrow[2]} for mrow in self.cursor.fetchall()]
            chats.append({
                "chat_id": chat_id,
                "client": username,
                "is_closed": bool(is_closed),
                "csat": csat,
                "creation_time": creation_time,
                "close_time": close_time,
                "messages": messages
            })
        output = json.dumps(chats, ensure_ascii=False, indent=2)
        print(output)

    # Выгрузка чатов для конкретного клиента
    def export_chats_by_client(self, client_id):
        self.cursor.execute(
            "SELECT chat_id, operator_id, is_closed, csat, creation_time, close_time FROM chats WHERE client_id=?",
            (client_id,)
        )
        chats = []
        for row in self.cursor.fetchall():
            chat_id, operator_id, is_closed, csat, creation_time, close_time = row
            self.cursor.execute("SELECT name FROM operators WHERE operator_id=?", (operator_id,))
            op_row = self.cursor.fetchone()
            operator_name = op_row[0] if op_row else None
            self.cursor.execute(
                "SELECT sender, text, timestamp FROM messages WHERE chat_id=? ORDER BY timestamp",
                (chat_id,)
            )
            messages = [{"sender": mrow[0], "text": mrow[1], "timestamp": mrow[2]} for mrow in self.cursor.fetchall()]
            chats.append({
                "chat_id": chat_id,
                "operator": operator_name,
                "is_closed": bool(is_closed),
                "csat": csat,
                "creation_time": creation_time,
                "close_time": close_time,
                "messages": messages
            })
        output = json.dumps(chats, ensure_ascii=False, indent=2)
        print(output)

    # Выгрузка профилей всех операторов
    def export_operator_profiles(self):
        self.cursor.execute("SELECT operator_id, name, city, birth_date, position, experience FROM operators")
        operators = []
        for row in self.cursor.fetchall():
            operators.append({
                "operator_id": row[0],
                "name": row[1],
                "city": row[2],
                "birth_date": row[3],
                "position": row[4],
                "experience": row[5]
            })
        output = json.dumps(operators, ensure_ascii=False, indent=2)
        print(output)

    # Выгрузка профилей всех клиентов
    def export_client_profiles(self):
        self.cursor.execute("SELECT client_id, username, name, city, birth_date, position, experience FROM clients")
        clients = []
        for row in self.cursor.fetchall():
            clients.append({
                "client_id": row[0],
                "username": row[1],
                "name": row[2],
                "city": row[3],
                "birth_date": row[4],
                "position": row[5],
                "experience": row[6]
            })
        output = json.dumps(clients, ensure_ascii=False, indent=2)
        print(output)
