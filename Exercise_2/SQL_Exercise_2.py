import sqlite3

# Подключаемся к базе данных из Exercise_1
conn = sqlite3.connect("../Exercise_1/platform.db")
cur = conn.cursor()

# a) Ники клиентов, поставивших csat меньше 3
cur.execute("""
SELECT DISTINCT c.username
FROM clients c
JOIN chats ct ON c.client_id = ct.client_id
WHERE ct.csat IS NOT NULL AND ct.csat < 3
""")
low_csat = [row[0] for row in cur.fetchall()]
with open("low_csat_clients.txt", "w", encoding="utf-8") as f:
    for nick in low_csat:
        f.write(nick + "\n")

# б) ID тикетов, содержащих слово "отлично", отсортированные по убыванию CSAT
cur.execute("""
SELECT DISTINCT ct.chat_id
FROM messages m
JOIN chats ct ON m.chat_id = ct.chat_id
WHERE m.text LIKE '%отлично%'
ORDER BY ct.csat DESC
""")
excellent_tickets = [str(row[0]) for row in cur.fetchall()]
with open("tickets_with_excellent.txt", "w", encoding="utf-8") as f:
    for t in excellent_tickets:
        f.write(t + "\n")

# в) ID клиентов, сделавших больше пяти заказов в "Теремок" и "Вкусно и точка"
#     на сумму от 2000 до 10000 рублей, и max сумма их заказа
cur.execute("""
SELECT o.order_client_id AS frequent_customer, MAX(o.price) AS max_sum
FROM orders o
WHERE o.place IN ('Теремок', 'Вкусно и точка')
  AND o.price BETWEEN 2000 AND 10000
GROUP BY o.order_client_id
HAVING COUNT(*) > 5
""")
freq_customers = cur.fetchall()
with open("frequent_customers.txt", "w", encoding="utf-8") as f:
    for row in freq_customers:
        f.write(f"{row[0]}\t{row[1]}\n")

# г) Объединённая таблица клиентов, заказов и тикетов (до 1000 записей)
cur.execute("""
SELECT c.client_id, c.username, o.order_id, o.price, o.place, ct.chat_id, ct.csat, ct.creation_time
FROM clients c
JOIN orders o ON c.client_id = o.order_client_id
LEFT JOIN chats ct ON o.order_id = ct.ticket_order_id
LIMIT 1000
""")
combined = cur.fetchall()
with open("combined_records.txt", "w", encoding="utf-8") as f:
    for row in combined:
        f.write("\t".join([str(item) if item is not None else "" for item in row]) + "\n")

conn.close()
