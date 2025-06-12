# Salve como check_db.py na raiz do projeto
import sqlite3

conn = sqlite3.connect('data/orbit.db')
cur = conn.cursor()

print("Usuários:")
for row in cur.execute("SELECT * FROM user"):
    print(row)

print("\nCards:")
for row in cur.execute("SELECT * FROM card"):
    print(row)

conn.close()