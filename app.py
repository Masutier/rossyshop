import os
import json
import sqlite3 as sql3
import pandas as pd
from datetime import datetime, date, timedelta
from flask import Flask, flash, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from utils import crearFolder, clean_file
from operator import itemgetter
from collections import OrderedDict
from genDocs.xlsx_1 import *
from dbs.dbs import *

with open("dbs/rossy.json") as config_file:
    config = json.load(config_file)

app = Flask(__name__)
app.config['SECRET_KEY'] = config['SECRET_KEY']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
formatted_date = datetime.today().date()
timing = formatted_date.strftime("%b_%d_%Y")
origen_path = "/home/gabriel/Downloads/"
DESTINY_PATH = "/home/gabriel/Documents/catalogRossy/accounts/"
DOWNLOAD_PATH = "static/docs/"

"""
sudo systemctl daemon-reload
sudo systemctl start evalinstructor
sudo systemctl enable evalinstructor  # Auto-start on boot

sudo systemctl status evalinstructor  # Verify it's running
"""

@app.route("/")
def home():
    try:
        allventas = call_db_dict(f"SELECT * FROM ventas ORDER BY FECHA")
        allabonos = call_db_dict("SELECT * FROM abonos ORDER BY FECHA")
        cartera = []
        totVentas = 0
        totAbonos = 0

        for venta in allventas:
            cliente = call_db_one_dict(f"SELECT * FROM clientes WHERE ID = ?", (venta["CLIENTE_ID"],))
            total = int(venta['P_CATALOGO_PRODUCTO']) * int(venta['CANTIDAD'])
            totVentas += total

            cartera.append({
                'item': 'venta',
                'id': venta["ID"],
                'cliente': cliente['NOMBRE'], 
                'producto': venta['DESCRIPCION_PRODUCTO'],
                'total': total,
                'fecha': venta['FECHA'],
            })

        for abono in allabonos:
            cliente = call_db_one_dict(f"SELECT * FROM clientes WHERE ID = ?", (abono["CLIENTE_ID"],))
            totAbonos += abono['VALOR']

            cartera.append({
                'item': 'abono',
                'id': abono["ID"],
                'cliente': cliente['NOMBRE'], 
                'abono': abono['VALOR'],
                'notas': abono['NOTAS'],
                'fecha': abono['FECHA'],
            })

        cartera = sorted(cartera, key=lambda x: x['fecha'], reverse=True)
        return render_template('home.html', title="Rossy's Shop", cartera=cartera, totVentas=totVentas, totAbonos=totAbonos)
    except Exception as e:
        startApp()
        flash(f'Error al comenzar la app: {str(e)}')

        return render_template('home.html', title="Rossy's Shop")


@app.route('/odsLoad')
def odsLoad():

    return render_template('ods_load.html', title="ods Load",)


# >>>>>>>>> CLIENTES >>>>>>>>>

@app.route('/all_clientes')
def all_clientes():
    clientes = call_db_dict("SELECT * FROM clientes")

    return render_template('clientes/clientes.html', title="Clientes", clientes=clientes)


@app.route('/crearCliente', methods=['GET', 'POST'])
def crearCliente():
    if request.method == "POST":
        incomming = request.form
        deuda = 0

        save_data(f"INSERT INTO clientes (NOMBRE, DIRECCION, BARRIO, TELEFONO, EMPRESA, CLIENTE_DE, COMPRA, DEUDA) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (incomming['nombre'], incomming['direccion'], incomming['barrio'], str(incomming['telefono']), incomming['empresa'], incomming['cliente_de'], incomming['compra'], deuda))

        flash('El cliente se creo exitosamente!.')
        return redirect(url_for('all_clientes'))
    
    return render_template('clientes/crear_cliente.html', title="Crear Cliente")


@app.route('/mostrarCliente/<int:id>', methods=['GET', 'POST'])
def mostrarCliente(id):
    cliente = call_db_one_dict(f"SELECT * FROM clientes WHERE ID = ?", (id,))
    ventas = call_db_all_dict(f"SELECT * FROM ventas WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (id,))
    abonos = call_db_all_dict(f"SELECT * FROM abonos WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (id,))
    ventasAll = []

    for ventax in ventas:
        total = int(ventax['P_CATALOGO_PRODUCTO']) * int(ventax['CANTIDAD'])

        ventasAll.append({
            'id': ventax["ID"],
            'producto': ventax['DESCRIPCION_PRODUCTO'], 
            'productoVal': ventax['P_CATALOGO_PRODUCTO'],
            'qty': ventax["CANTIDAD"],
            'total': total,
            'fecha': ventax['FECHA']
        })

    return render_template('clientes/cliente.html', title="Cliente", cliente=cliente, ventasAll=ventasAll, abonos=abonos)


@app.route('/modificarCliente/<int:id>', methods=['GET', 'POST'])
def modificarCliente(id):
    if request.method == "POST":
        incomming = request.form

        sqlquery = """UPDATE clientes SET NOMBRE=?, DIRECCION=?, BARRIO=?, TELEFONO=?, EMPRESA=?, CLIENTE_DE=?, COMPRA=? WHERE id=?"""
        data1 = (incomming['nombre'], incomming['direccion'], incomming['barrio'], incomming['telefono'], incomming['empresa'], incomming['cliente_de'], incomming['compra'], id)
        update_data(sqlquery, data1)

        flash('La informacion del cliente se actualizo correctamente!.')
        return redirect(url_for('all_clientes'))

    cliente = call_db_one_dict(f"SELECT * FROM clientes WHERE ID = ?", (id,))
    return render_template('clientes/modificar_cliente.html', title="Modificar Cliente", cliente=cliente)


@app.route('/load_clientes', methods=['GET', 'POST'])
def load_clientes():
    if request.method == "POST":
        inFile = request.files['plantillaVentas']

        filename = secure_filename(inFile.filename)
        filenamex = filename.split('.')
        fileNewName = filenamex[0] + "_" + str(timing) + "." + filenamex[-1] # Rename file adding date
        filepath = os.path.join(DESTINY_PATH, fileNewName)
        inFile.save(filepath) # save crude file

        # Process sheet ventas
        dataframe = pd.read_excel(filepath, sheet_name='Clientes')
        dfClientes = clean_file(dataframe)

        # loop through the rows using iterrows()
        for index, row in dfClientes.iterrows():
            save_data(f"INSERT INTO clientes (NOMBRE, DIRECCION, BARRIO, TELEFONO, EMPRESA, CLIENTE_DE, COMPRA, DEUDA) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (row['NOMBRE'], row['DIRECCION'], row['BARRIO'], row['TELEFONO'], row['EMPRESA'], row['CLIENTE_DE'], row['COMPRA'], 0))

        flash('La plantilla se subio exitosamente!.')
        return redirect(url_for('home'))

    return render_template('ods_load.html', title="ods Load", function="load_clientes")


# >>>>>>>>> VENTAS >>>>>>>>>

@app.route('/all_ventas')
def all_ventas():
    ventas = call_db_dict(f"SELECT * FROM ventas WHERE IMPRENTA = 'NO'")
    ventasAll = []

    for ventax in ventas:
        cliente = call_db_one_dict(f"SELECT * FROM clientes WHERE ID = ?", (ventax["CLIENTE_ID"],))
        total = int(ventax['P_CATALOGO_PRODUCTO']) * int(ventax['CANTIDAD'])

        ventasAll.append({
            'id': ventax["ID"],
            'cliente': cliente['NOMBRE'], 
            'producto': ventax['DESCRIPCION_PRODUCTO'],
            'revista': ventax['REVISTA_PRODUCTO'],
            'campanna': ventax['CAMPANNA_PRODUCTO'],
            'productoVal': ventax['P_CATALOGO_PRODUCTO'],
            'qty': ventax['CANTIDAD'],
            'total': total,
            'fecha': ventax['FECHA'],
            'impreso': ventax['IMPRENTA']
        })

    return render_template('ventas/ventas.html', title="Ventas", ventasAll=ventasAll)


@app.route('/historia_ventas')
def historia_ventas():
    ventas = call_db_dict(f"SELECT * FROM ventas")
    ventasAll = []

    for ventax in ventas:
        cliente = call_db_one_dict(f"SELECT * FROM clientes WHERE ID = ?", (ventax["CLIENTE_ID"],))
        total = int(ventax['P_CATALOGO_PRODUCTO']) * int(ventax['CANTIDAD'])

        ventasAll.append({
            'id': ventax["ID"],
            'cliente': cliente['NOMBRE'], 
            'producto': ventax['DESCRIPCION_PRODUCTO'],
            'revista': ventax['REVISTA_PRODUCTO'],
            'campanna': ventax['CAMPANNA_PRODUCTO'],
            'productoVal': ventax['P_CATALOGO_PRODUCTO'],
            'qty': ventax['CANTIDAD'],
            'total': total,
            'fecha': ventax['FECHA'],
            'impreso': ventax['IMPRENTA']
        })
        
    return render_template('ventas/ventas.html', title="Ventas Novaventa", ventasAll=ventasAll)


@app.route('/crearVenta', methods=['GET', 'POST'])
def crearVenta():
    sqlQuery = """SELECT ID, NOMBRE FROM clientes"""
    clientes = call_db_dict(sqlQuery,)
    sqlQuery = """SELECT * FROM productos ORDER BY CL ASC"""
    productos = call_db_dict(sqlQuery,)

    if request.method == "POST":
        incomming = request.form
        prod = incomming['producto'].split(",")
        cl = int(prod[0])
        revista = prod[1]

        cliente = call_db_one_dict(f"SELECT * FROM clientes WHERE ID =?", (incomming['cliente'],)) 
        producto = call_db_two_all_dict(f"SELECT * FROM productos WHERE CL =? AND REVISTA =?", (cl), (revista))

        total = int(producto['P_CATALOGO']) * int(incomming['qty'])
        imprenta = "NO"
        fecha_imprenta = datetime.today().date()

        save_data(f"INSERT INTO ventas (CLIENTE_ID, CL_PRODUCTO, DESCRIPCION_PRODUCTO, P_LISTA_PRODUCTO, P_CATALOGO_PRODUCTO, REVISTA_PRODUCTO, CAMPANNA_PRODUCTO, CANTIDAD, IMPRENTA, FECHA_IMPRENTA) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (incomming['cliente'], producto['CL'], producto['DESCRIPCION'], producto['P_LISTA'], producto['P_CATALOGO'], producto['REVISTA'], producto['CAMPANNA'], int(incomming['qty']), imprenta, fecha_imprenta,))

        deuda = int(cliente['DEUDA']) + int(total)
        fecha = datetime.today().date()
        sqlquery = """UPDATE clientes SET DEUDA=?, FECHA_ULTIMA_COMPRA=? WHERE id=?"""
        data1 = (deuda, fecha, incomming['cliente'])
        update_data(sqlquery, data1)

        flash('La Venta se creo exitosamente!.')
        return redirect(url_for('home'))
    
    return render_template('ventas/crear_venta.html', title="Crear Venta", clientes=clientes, productos=productos)


@app.route('/mostrarVenta/<int:id>', methods=['GET', 'POST'])
def mostrarVenta(id):
    venta = call_db_one_dict(f"SELECT * FROM ventas WHERE ID = ?", (id,))
    cliente = call_db_one_dict(f"SELECT * FROM clientes WHERE ID = ?", (int(venta['CLIENTE_ID']),))

    total = venta['P_CATALOGO_PRODUCTO'] * venta['CANTIDAD']

    return render_template('ventas/venta.html', title="Mostrar Venta", cliente=cliente, venta=venta, total=total)


@app.route('/modificarVenta/<int:id>', methods=['GET', 'POST'])
def modificarVenta(id):
    venta = call_db_one_dict(f"SELECT * FROM ventas WHERE ID = ?", (id,))
    cliente = call_db_one_dict(f"SELECT * FROM clientes WHERE ID =?", (venta['CLIENTE_ID'],)) 
    ventax = {
        'id': venta['ID'],
        'cliente': cliente['NOMBRE'],
        'productoCl': venta['CL_PRODUCTO'],  
        'producto': venta['DESCRIPCION_PRODUCTO'], 
        'productoVal': venta['P_CATALOGO_PRODUCTO'],
        'revista': venta['REVISTA_PRODUCTO'],
        'campanna': venta['CAMPANNA_PRODUCTO'],
        'qty': venta['CANTIDAD'],
        'imprenta': venta['IMPRENTA'],
    }

    if request.method == "POST":
        incomming = request.form
        oldValue = (venta['P_CATALOGO_PRODUCTO'] * venta['CANTIDAD'])
        newValue = (int(incomming['ventaVal']) * int(incomming['qty']))

        if newValue < oldValue:
            difer = oldValue - newValue
            deuda = int(cliente['DEUDA']) - difer

            sqlquery = """UPDATE ventas SET CANTIDAD=?, P_CATALOGO_PRODUCTO=?, IMPRENTA=? WHERE id=?"""
            data1 = (incomming['qty'], incomming['ventaVal'], incomming['imprenta'], id)
            update_data(sqlquery, data1)

            sqlquery = """UPDATE clientes SET DEUDA=? WHERE id=?"""
            data1 = (deuda, cliente['ID'])
            update_data(sqlquery, data1)

            flash('La informacion de la venta se actualizo correctamente!.')
            return redirect(url_for('all_ventas'))

        elif newValue > oldValue:
            difer = newValue - oldValue
            deuda = int(cliente['DEUDA']) + difer

            sqlquery = """UPDATE ventas SET CANTIDAD=?, P_CATALOGO_PRODUCTO=?, IMPRENTA=? WHERE id=?"""
            data1 = (incomming['qty'], incomming['ventaVal'], incomming['imprenta'], id)
            update_data(sqlquery, data1)

            sqlquery = """UPDATE clientes SET DEUDA=? WHERE id=?"""
            data1 = (deuda, cliente['ID'])
            update_data(sqlquery, data1)

            flash('La informacion de la venta se actualizo correctamente!.')
            return redirect(url_for('all_ventas'))

        else:
            sqlquery = """UPDATE ventas SET IMPRENTA=? WHERE id=?"""
            data1 = (incomming['imprenta'], id)
            update_data(sqlquery, data1)

            flash('La informacion de la venta se actualizo correctamente!.')
            return redirect(url_for('all_ventas'))

    return render_template('ventas/modificar_venta.html', title="Modificar Venta", ventax=ventax)


@app.route('/load_ventas', methods=['GET', 'POST'])
def load_ventas():
    if request.method == "POST":
        inFile = request.files['plantillaVentas']

        filename = secure_filename(inFile.filename)
        filenamex = filename.split('.')
        fileNewName = filenamex[0] + "_" + str(timing) + "." + filenamex[-1] # Rename file adding date
        filepath = os.path.join(DESTINY_PATH, fileNewName)
        inFile.save(filepath) # save crude file

        # Process sheet ventas
        dataframe = pd.read_excel(filepath, sheet_name='Ventas')
        dfVentas = clean_file(dataframe)

        save_db(dfVentas, "ventas")

        flash('La plantilla se subio exitosamente!.')
        return redirect(url_for('home'))
    
    return render_template('ods_load.html', title="ods Load", function="load_ventas")


@app.route('/filtrar/<filter>')
def filtrar(filter):
    revista = filter.upper()
    ventas = call_db_all_dict(f"SELECT * FROM ventas WHERE IMPRENTA = 'NO' AND REVISTA_PRODUCTO = ?", (revista,))
    ventasAll = []

    for ventax in ventas:
        cliente = call_db_one_dict(f"SELECT * FROM clientes WHERE ID = ?", (ventax["CLIENTE_ID"],))
        total = int(ventax['P_CATALOGO_PRODUCTO']) * int(ventax['CANTIDAD'])

        ventasAll.append({
            'id': ventax["ID"],
            'cliente': cliente['NOMBRE'], 
            'producto': ventax['DESCRIPCION_PRODUCTO'],
            'revista': ventax['REVISTA_PRODUCTO'],
            'campanna': ventax['CAMPANNA_PRODUCTO'],
            'productoVal': ventax['P_CATALOGO_PRODUCTO'],
            'qty': ventax['CANTIDAD'],
            'total': total,
            'fecha': ventax['FECHA'],
            'impreso': ventax['IMPRENTA']
        })
        
    title = "Ventas " + filter
    return render_template('ventas/ventas.html', title=title, ventasAll=ventasAll)


# >>>>>>>>> PRODUCTOS >>>>>>>>>

@app.route('/all_productos')
def all_productos():
    sqlQuery = f"""SELECT * FROM productos"""
    productos = call_db_dict(sqlQuery)

    return render_template('productos/productos.html', title="Productos", productos=productos)


@app.route('/crearProducto', methods=['GET', 'POST'])
def crearProducto():
    if request.method == "POST":
        incomming = request.form
        productos = call_db_dict("SELECT * FROM productos")

        for producto in productos:
            if int(incomming['cl']) == int(producto['CL']) and int(incomming['pcatalogo']) == int(producto['P_CATALOGO']):
                flash('El Producto YA EXISTE!.')
                return redirect(url_for('all_productos'))
            elif int(incomming['cl']) == int(producto['CL']) and int(incomming['pcatalogo']) == int(producto['P_CATALOGO']):
                flash('El Producto YA EXISTE pero es diferente!.')
                return redirect(url_for('all_productos'))
            else:
                save_data(f"INSERT INTO productos (CL, DESCRIPCION, P_CATALOGO, UBICACION, REVISTA) VALUES (?, ?, ?, ?, ?)", (int(incomming['cl']), incomming['descripcion'], int(incomming['pcatalogo']), incomming['ubica'], incomming['revista']))
                flash('El Producto se creo exitosamente!.')
                return redirect(url_for('all_productos'))
    
    return render_template('productos/crear_producto.html', title="Crear Producto")


@app.route('/load_productos', methods=['GET', 'POST'])
def load_productos():
    if request.method == "POST":
        inFile = request.files['plantillaVentas']

        filename = secure_filename(inFile.filename)
        filenamex = filename.split('.')
        fileNewName = filenamex[0] + "_" + str(timing) + "." + filenamex[-1] # Rename file adding date
        filepath = os.path.join(DESTINY_PATH, fileNewName)
        inFile.save(filepath) # save crude file

        # Process sheet ventas
        dataframe = pd.read_excel(filepath, sheet_name='Productos')
        dfProductos = clean_file(dataframe)

        # loop through the rows using iterrows()
        for index, row in dfProductos.iterrows():
            save_data(f"INSERT INTO productos (CL, DESCRIPCION, P_LISTA, P_CATALOGO, UBICACION, REVISTA, CAMPANNA) VALUES (?, ?, ?, ?, ?, ?, ?)", (row['CL'], row['DESCRIPCION'], row['P_LISTA'], row['P_CATALOGO'], row['UBICACION'], row['REVISTA'], row['CAMPANNA']))

        flash('La plantilla se subio exitosamente!.')
        return redirect(url_for('home'))
    
    return render_template('ods_load.html', title="ods Load", function="load_productos")


# >>>>>>>>> ABONOS >>>>>>>>>

@app.route('/all_abonos')
def all_abonos():
    sqlQuery = f"""SELECT * FROM abonos"""
    abonos = call_db_dict(sqlQuery)
    sqlQuery = f"""SELECT * FROM clientes"""
    clientes = call_db_dict(sqlQuery)
    abonosAll = []

    for pagox in abonos:
        cliente = call_db_one_dict(f"SELECT * FROM clientes WHERE ID = ?", (pagox["CLIENTE_ID"],))
        abonosAll.append({
            'id': pagox["ID"],
            'cliente': cliente['NOMBRE'], 
            'notas': pagox['NOTAS'], 
            'valor': pagox['VALOR'], 
            'fecha': pagox['FECHA']
        })

    return render_template('abonos/abonos.html', title="Abonos", abonosAll=abonosAll)


@app.route('/crearAbono', methods=['GET', 'POST'])
def crearAbono():
    sqlQuery = """SELECT ID, NOMBRE FROM clientes"""
    clientes = call_db_dict(sqlQuery,)

    if request.method == "POST":
        incomming = request.form

        save_data(f"INSERT INTO abonos (CLIENTE_ID, NOTAS, VALOR) VALUES (?, ?, ?)", (incomming['cliente'], incomming['notas'], incomming['valor']))
        cliente = call_db_one_dict(f"SELECT * FROM clientes WHERE ID = ?", (incomming['cliente'],))

        deuda = int(cliente['DEUDA']) - int(incomming['valor'])
        fecha = datetime.today().date()
        sqlquery = """UPDATE clientes SET DEUDA=?, FECHA_ULTIMO_ABONO=? WHERE id=?"""
        data1 = (deuda, fecha, incomming['cliente'])
        update_data(sqlquery, data1)

        flash('El abono se registro exitosamente!.')
        return redirect(url_for('all_abonos'))
    
    return render_template('abonos/crear_abono.html', title="Crear Abono", clientes=clientes)


@app.route('/mostrarAbono/<int:id>', methods=['GET', 'POST'])
def mostrarAbono(id):
    abono = call_db_one_dict(f"SELECT * FROM abonos WHERE ID = ?", (id,))
    cliente = call_db_one_dict(f"SELECT * FROM clientes WHERE ID = ?", (int(abono['CLIENTE_ID']),))

    return render_template('abonos/abono.html', title="Mostrar Abono", abono=abono, cliente=cliente)


@app.route('/modificarAbono/<int:id>', methods=['GET', 'POST'])
def modificarAbono(id):
    abono = call_db_one_dict(f"SELECT * FROM abonos WHERE ID= ?", (id,))
    cliente = call_db_one_dict(f"SELECT * FROM clientes WHERE ID= ?", (int(abono['CLIENTE_ID']),))

    if request.method == "POST":
        incomming = request.form
        sqlquery = """UPDATE abonos SET VALOR= ?, NOTAS= ? WHERE id= ?"""
        data1 = (incomming['valor'], incomming['notas'], id)
        update_data(sqlquery, data1)
        flash('El abono se actualizo exitosamente!.')
        return redirect(url_for('all_abonos'))
    
    return render_template('abonos/modificar_abono.html', title="Crear Abono", abono=abono, cliente=cliente)


# >>>>>>>>> GENERAR RECIBOS >>>>>>>>>

@app.route('/registrosExcel')
def registrosExcel():
    catalogList = []
    chkFolder = os.path.isdir(DOWNLOAD_PATH)

    if not chkFolder:
        flash('No se encontraron catalogos anteriores.')
        return render_template('reportes/registrosExcel.html', title="Registros Excel",)
    else:
        catalogList = os.listdir(DOWNLOAD_PATH)
        catalogList.sort()
        return render_template('reportes/registrosExcel.html', title="Registros Excel", catalogList=catalogList)


@app.route('/cobrosXlsx/<filter>')
def cobrosXlsx(filter):
    revista = filter.upper()
    ventasAll = call_db_all_dict(f"SELECT * FROM ventas WHERE IMPRENTA = 'NO' AND REVISTA_PRODUCTO = ?", (revista,))
    clientes = []
    ventas = []

    if ventasAll:
        for venta in ventasAll:
            clientex = call_db_one_dict(f"SELECT * FROM clientes WHERE ID = ?", (venta["CLIENTE_ID"],))

            if {'nombre':clientex['NOMBRE'], 'deuda':clientex['DEUDA']} not in clientes:
                clientes.append({'nombre':clientex['NOMBRE'], 'deuda':clientex['DEUDA']})

            cant = venta['CANTIDAD']
            total = int(venta['P_CATALOGO_PRODUCTO']) * int(venta['CANTIDAD'])
            ventas.append({
                'id': clientex['ID'], 
                'cliente': clientex['NOMBRE'], 
                'producto': venta['DESCRIPCION_PRODUCTO'], 
                'productoVal': venta['P_CATALOGO_PRODUCTO'],
                'qty': cant,
                'total': total,
            })

            # sqlquery = """UPDATE ventas SET IMPRENTA=? WHERE id=?"""
            # data1 = ("SI", venta['ID'])
            # update_data(sqlquery, data1)
            createfile = "Imprimir" + "_" + filter + "_"
            
        reporteCobrosXlsx(clientes, ventas, createfile)
        flash("Los recibos se crearon satisfactoriamente!!")
        return redirect(url_for('registrosExcel'))
    else:
        flash(f'No se encontraron ventas de { revista }.')
        return redirect(url_for('all_ventas'))


@app.route('/delete_recibo/<file>')
def delete_recibo(file):
    os.remove(DOWNLOAD_PATH + file)
    flash("El recibo se elimino satisfactoriamente!!")
    return redirect(url_for('registrosExcel'))


@app.route('/cobrosPdf')
def cobrosPdf():
    ventasAll = call_db_dict(f"SELECT * FROM ventas WHERE IMPRENTA = 'NO'")
    client = []
    ventas = []

    for venta in ventasAll:
        clientex = call_db_one_dict(f"SELECT * FROM clientes WHERE ID = ?", (venta["CLIENTE_ID"],))

        if clientex['NOMBRE'] not in client:
            client.append(clientex['NOMBRE'])
        
        producto = call_db_one_dict(f"SELECT * FROM productos WHERE CL = ?", (venta["PRODUCTO_ID"],))
        cant = venta['CANTIDAD']
        total = int(producto['P_CATALOGO']) * int(venta['CANTIDAD'])

        ventas.append({
            'cliente': clientex['NOMBRE'], 
            'producto': producto['DESCRIPCION'], 
            'productoVal': producto['P_CATALOGO'],
            'qty': cant,
            'total': total,
        })
        
    reporteCobros(client, ventas)
    return render_template('ventas/ventas.html', title="Ventas", client=client, ventas=ventas)


@app.route('/cartera')
def cartera():
    clientes = call_db_dict("SELECT * FROM clientes")
    ventas = call_db_dict("SELECT * FROM clientes")
    abonos = call_db_dict("SELECT * FROM clientes")
    allnames = []
    cartera = []
    totcartera = []

    for cliente in clientes:
        totVentas = 0
        totAbonos = 0
        ventas = call_db_all_dict(f"SELECT * FROM ventas WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (cliente['ID'],))
        abonos = call_db_all_dict(f"SELECT * FROM abonos WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (cliente['ID'],))

        if cliente['NOMBRE'] not in allnames:
            allnames.append(cliente['NOMBRE'])

        for ventax in ventas:
            total = int(ventax['P_CATALOGO_PRODUCTO']) * int(ventax['CANTIDAD'])
            cartera.append({
                'cliente': cliente["NOMBRE"],
                'id': ventax["ID"],
                'descripcion': ventax['DESCRIPCION_PRODUCTO'], 
                'revista': ventax['REVISTA_PRODUCTO'], 
                'qty': ventax["CANTIDAD"],
                'Vtotal': total,
                'fecha': ventax['FECHA']
            })
            totVentas += total
        
        for abonox in abonos:
            cartera.append({
                'cliente': cliente["NOMBRE"],
                'id': abonox["ID"],
                'descripcion': abonox['NOTAS'], 
                'Atotal': abonox["VALOR"],
                'fecha': ventax['FECHA']
            })
            totAbonos += abonox["VALOR"]
        totcartera.append({'cliente': cliente["NOMBRE"], 'totVentas': totVentas, 'totAbonos': totAbonos})

    return render_template('reportes/cartera.html', title="Cartera", allnames=allnames, cartera=cartera, totcartera=totcartera)


@app.route('/carteraXlsx')
def carteraXlsx():
    clientes = call_db_dict("SELECT * FROM clientes")
    ventas = call_db_dict("SELECT * FROM clientes")
    abonos = call_db_dict("SELECT * FROM clientes")
    allnames = []
    cartera = []
    totcartera = []

    for cliente in clientes:
        totVentas = 0
        totAbonos = 0
        ventas = call_db_all_dict(f"SELECT * FROM ventas WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (cliente['ID'],))
        abonos = call_db_all_dict(f"SELECT * FROM abonos WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (cliente['ID'],))

        if cliente['NOMBRE'] not in allnames:
            allnames.append({'nombre': cliente['NOMBRE']})

        for ventax in ventas:
            total = int(ventax['P_CATALOGO_PRODUCTO']) * int(ventax['CANTIDAD'])
            cartera.append({
                'cliente': cliente['NOMBRE'],
                'id': ventax["ID"],
                'descripcion': ventax['DESCRIPCION_PRODUCTO'], 
                'revista': ventax['REVISTA_PRODUCTO'], 
                'qty': ventax['CANTIDAD'],
                'Vtotal': total,
                'Atotal': "",
                'fecha': ventax['FECHA']
            })
            totVentas += total
        
        for abonox in abonos:
            cartera.append({
                'cliente': cliente['NOMBRE'],
                'id': abonox["ID"],
                'descripcion': abonox['NOTAS'], 
                'revista': "", 
                'qty': "", 
                'Vtotal': "", 
                'Atotal': abonox['VALOR'],
                'fecha': ventax['FECHA']
            })
            totAbonos += abonox['VALOR']

        grandTot = totVentas - totAbonos
        
        totcartera.append({'cliente': cliente['NOMBRE'], 'totVentas': totVentas, 'totAbonos': totAbonos, 'grandTot': grandTot})

    createfile = "Imprimir" + "_" + "Cartera" + "_"
            
    reporteCarteraXlsx(allnames, cartera, totcartera, createfile)
    flash("El excel de cartera se creo satisfactoriamente!!")
    return redirect(url_for('registrosExcel'))


if __name__ == "__main__":
    app.run(debug=True)


