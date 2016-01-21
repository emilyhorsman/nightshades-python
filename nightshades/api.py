import psycopg2

def get_users():
  conn = psycopg2.connect('dbname=nightshades')
  cur  = conn.cursor()

  cur.execute('SELECT * FROM nightshades.users;')
  row = cur.fetchone()

  cur.close()
  conn.close()

  return row
