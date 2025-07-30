import os
import sqlite3 as sql3
from datetime import datetime, date
from flask import flash, session, redirect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
today = str(datetime.today().date())
today = today.replace("-", "_")
db_name = "rossy_acc.db"
db_name_clientes = "rossy_clientes.db"
db_name_movim = "rossy_ventas.db"


def createDB():
    conn=sql3.connect(os.path.join(BASE_DIR, db_name))
    conn.commit()
    conn.close()


def db_conn():
    conn = sql3.connect('dbs/' + db_name)
    conn.row_factory = sql3.Row
    return conn


def call_db_dict(sqlQuery):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    conn.row_factory = sql3.Row
    dbData = conn.execute(sqlQuery).fetchall()
    conn.close()
    return dbData


def call_db_one_dict(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    conn.row_factory = sql3.Row
    dbData = conn.execute(sqlQuery, data1).fetchone()
    conn.close()
    return dbData


def call_db_all_dict(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    conn.row_factory = sql3.Row
    dbData = conn.execute(sqlQuery, data1).fetchall()
    conn.close()
    return dbData


def call_db_two_all_dict(sqlQuery, data1, data2):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    conn.row_factory = sql3.Row
    dbData = conn.execute(sqlQuery, (data1, data2)).fetchone()
    conn.close()
    return dbData


def save_data(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    cursor = conn.cursor()
    cursor.execute(sqlQuery, data1)
    conn.commit()
    conn.close()


def update_data(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    cur = conn.cursor()
    cur.execute(sqlQuery, data1)
    conn.commit()
    conn.close()


# <<<<<<<<<<<<<<<<<<<<<<<<<<<< CLIENTES >>>>>>>>>>>>>>>>>>>>>>>>>>>

def call_db_dict_clientes(sqlQuery):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name_clientes))
    conn.row_factory = sql3.Row
    dbData = conn.execute(sqlQuery).fetchall()
    conn.close()
    return dbData


def save_data_clientes(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name_clientes))
    cursor = conn.cursor()
    cursor.execute(sqlQuery, data1)
    conn.commit()
    conn.close()


def call_db_one_dict_clientes(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name_clientes))
    conn.row_factory = sql3.Row
    dbData = conn.execute(sqlQuery, data1).fetchone()
    conn.close()
    return dbData


def update_data_clientes(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name_clientes))
    cur = conn.cursor()
    cur.execute(sqlQuery, data1)
    conn.commit()
    conn.close()


# <<<<<<<<<<<<<<<<<<<<<<<<<<<< MOVIMIENTOS >>>>>>>>>>>>>>>>>>>>>>>>>>>

def call_db_dict_movim(sqlQuery):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name_movim))
    conn.row_factory = sql3.Row
    dbData = conn.execute(sqlQuery).fetchall()
    conn.close()
    return dbData


def save_data_movim(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name_movim))
    cursor = conn.cursor()
    cursor.execute(sqlQuery, data1)
    conn.commit()
    conn.close()


def call_db_one_dict_movim(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name_movim))
    conn.row_factory = sql3.Row
    dbData = conn.execute(sqlQuery, data1).fetchone()
    conn.close()
    return dbData


def update_data_movim(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name_movim))
    cur = conn.cursor()
    cur.execute(sqlQuery, data1)
    conn.commit()
    conn.close()


def delete_data_movim(sqlQuery, data1):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    cur = conn.cursor()
    cur.execute(sqlQuery, (data1,))
    conn.commit()
    conn.close()


# <<<<<<<<<<<<<<<<<<<<<<<<<<<< CREATE TABLES >>>>>>>>>>>>>>>>>>>>>>>>>>>

def createTable(sqlQuery):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name))
    cur=conn.cursor()
    cur.execute(sqlQuery,)
    conn.commit()
    conn.close()


def createTableClientes(sqlQuery):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name_clientes))
    cur=conn.cursor()
    cur.execute(sqlQuery,)
    conn.commit()
    conn.close()


def createTableMovim(sqlQuery):
    conn = sql3.connect(os.path.join(BASE_DIR, db_name_movim))
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
    createTableClientes(clientesQuery)


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
    createTableMovim(ventasQuery)


    abonosQuery = f"""CREATE TABLE abonos (
            ID INTEGER PRIMARY KEY NOT NULL,
            CLIENTE_ID INTEGER,
            VALOR INTEGER,
            NOTAS TEXT,
            FECHA DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(CLIENTE_ID) REFERENCES clientes(ID)
        )"""
    createTableMovim(abonosQuery)


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

