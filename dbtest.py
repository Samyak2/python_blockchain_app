import sqlite3
 
from sqlite3 import Error
 
def sql_connection():
 
    try:
 
        con = sqlite3.connect('mining.db')
 
        return con
 
    except Error:
 
        print(Error)
 
# def sql_table(con):
 
#     cursorObj = con.cursor()
 
#     cursorObj.execute("CREATE TABLE mining(id integer PRIMARY KEY, mining bool)")
 
#     con.commit()

con = sql_connection()

def is_mining():
    cursor = con.cursor()
    cursor.execute("SELECT mining from mining")
    row = cursor.fetchone()
    return bool(row[0])

def set_mining():
    cursor = con.cursor()
    cursor.execute("UPDATE mining SET mining=1 where id=1")
    con.commit()

def set_notmining():
    cursor = con.cursor()
    cursor.execute("UPDATE mining SET mining=0 where id=1")
    con.commit()

if __name__ == "__main__":
    con = sql_connection()
    
    # # sql_table(con)

    cursor = con.cursor()
    # cursor.execute("INSERT INTO mining VALUES(1, false)")
    # cursor.execute("UPDATE mining SET mining=true where id=1")
    cursor.execute("SELECT mining from mining")
    row = cursor.fetchone()
    print(bool(row[0]))
    con.commit()