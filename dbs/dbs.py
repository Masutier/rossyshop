import os
import sqlite3 as sql3
from datetime import datetime, date
from flask import flash, session, redirect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
today = str(datetime.today().date())
today = today.replace("-", "_")
db_name = "rossy_acc.db"


def createDB():
    conn=sql3.connect(os.path.join(BASE_DIR, db_name))
    conn.commit()
    conn.close()


def db_conn():
    conn = sql3.connect('dbs/' + db_name)
    conn.row_factory = sql3.Row
    return conn


def call_db(sqlQuery):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    dbData = conn.execute(sqlQuery,).fetchall()
    conn.close()
    return dbData


def call_db_dict(sqlQuery):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    conn.row_factory = sql3.Row
    dbData = conn.execute(sqlQuery).fetchall()
    conn.close()
    return dbData


def call_db_one(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    dbData = conn.execute(sqlQuery, data1,).fetchone() # SEE data1 as a tuple
    conn.close()
    return dbData


def call_db_one_dict(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    conn.row_factory = sql3.Row
    dbData = conn.execute(sqlQuery, data1).fetchone() # SEE data1 as a tuple
    conn.close()
    return dbData


def call_db_all(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    dbData = conn.execute(sqlQuery, data1).fetchall()
    conn.close()
    return dbData


def call_db_all_dict(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    conn.row_factory = sql3.Row
    dbData = conn.execute(sqlQuery, data1).fetchall()
    conn.close()
    return dbData


def save_db(dataframe, table):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    dataframe.to_sql(name=table, con=conn, if_exists="replace", index=False)
    conn.close()


def save_venta(dataframe, table):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    dataframe.to_sql(name=table, con=conn, if_exists="append", index=False)
    conn.close()


def call_db_two_all_dict(sqlQuery, data1, data2):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    conn.row_factory = sql3.Row
    dbData = conn.execute(sqlQuery, (data1, data2)).fetchone()
    conn.close()
    return dbData


def call_db_two_all(sqlQuery, data1, data2):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    dbData = conn.execute(sqlQuery, (data1, data2)).fetchall()
    conn.close()
    return dbData


def save_data(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    cursor = conn.cursor()
    cursor.execute(sqlQuery, data1)
    conn.commit()
    conn.close()


def update_db(sqlQuery, data1, data2):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    cur = conn.cursor()
    cur.execute(sqlQuery, (data1, data2))
    conn.commit()
    conn.close()


def update_data(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    cur = conn.cursor()
    cur.execute(sqlQuery, data1)
    conn.commit()
    conn.close()


def delete_two_db(sqlQuery, data1, data2):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    cur = conn.cursor()
    cur.execute(sqlQuery, (data1, data2))
    conn.commit()
    conn.close()


# Crea la tabla clientes
def createTable(sqlQuery):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    cur=conn.cursor()
    cur.execute(sqlQuery,)
    conn.commit()
    conn.close()


def startApp():
    clientesQuery = f"""CREATE TABLE IF NOT EXISTS clientes (
            ID INTEGER PRIMARY KEY NOT NULL,
            NOMBRE TEXT NOT NULL,
            DIRECCION TEXT,
            BARRIO TEXT,
            TELEFONO TEXT,
            EMPRESA TEXT,
            CLIENTE_DE TEXT,
            COMPRA TEXT,
            DEUDA INTEGER,
            FECHA_ULTIMA_COMPRA DATETIME,
            FECHA_ULTIMO_ABONO DATETIME,
            FECHA DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    createTable(clientesQuery)

    productosQuery = f"""CREATE TABLE productos (
            ID INTEGER PRIMARY KEY NOT NULL,
            CL INTEGER,
            DESCRIPCION TEXT,
            P_LISTA INTEGER,
            P_CATALOGO INTEGER,
            UBICACION TEXT,
            REVISTA TEXT,
            CAMPANNA TEXT,
            FECHA DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    createTable(productosQuery)

    ventasQuery = f"""CREATE TABLE IF NOT EXISTS ventas (
            ID INTEGER PRIMARY KEY NOT NULL,
            CLIENTE_ID INTEGER,
            CL_PRODUCTO INTEGER,
            DESCRIPCION_PRODUCTO TEXT,
            P_LISTA_PRODUCTO INTEGER,
            P_CATALOGO_PRODUCTO INTEGER,
            REVISTA_PRODUCTO TEXT,
            CAMPANNA_PRODUCTO TEXT,
            CANTIDAD INTEGER,
            IMPRENTA TEXT,
            FECHA_IMPRENTA DATETIME,
            FECHA DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(CLIENTE_ID) REFERENCES clientes(ID)
        )"""
    createTable(ventasQuery)

    abonosQuery = f"""CREATE TABLE abonos (
            ID INTEGER PRIMARY KEY NOT NULL,
            CLIENTE_ID INTEGER,
            VALOR INTEGER,
            NOTAS TEXT,
            FECHA DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(CLIENTE_ID) REFERENCES clientes(ID)
        )"""
    createTable(abonosQuery)
