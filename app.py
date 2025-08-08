import os
import json
import sqlite3 as sql3
import pandas as pd
from datetime import datetime, date, timedelta
from flask import Flask, flash, render_template, request, redirect, url_for, send_from_directory
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
DOWNLOAD_PATH = "docs/recibos/"

"""
sudo systemctl daemon-reload
sudo systemctl start evalinstructor
sudo systemctl enable evalinstructor  # Auto-start on boot
sudo systemctl status evalinstructor  # Verify it's running
"""

@app.route("/")
def home():
    novaQty = 0
    leonQty = 0
    modaQty = 0
    clientesQty = 0
    inventQty = 0
    ventasQty = 0
    abonosQty = 0
    totVentas = 0
    totAbonos = 0
    allclientes = []

    nova = call_db_all_dict(f"SELECT * FROM productos WHERE REVISTA = ?", ('NOVAVENTA',))
    for item in nova:
        novaQty += 1

    leon = call_db_all_dict(f"SELECT * FROM productos WHERE REVISTA = ?", ('LEONISA',))
    for item in leon:
        leonQty += 1

    moda = call_db_all_dict(f"SELECT * FROM productos WHERE REVISTA = ?", ('MODA_INT',))
    for item in moda:
        modaQty += 1

    invent = call_db_all_dict(f"SELECT * FROM productos WHERE REVISTA = ?", ('INVENTARIO',))
    for item in invent:
        inventQty += 1
    
    productos = {'novaQty':novaQty, 'leonQty':leonQty, 'modaQty':modaQty, 'inventQty':inventQty}


    clientes = call_db_dict_clientes("SELECT * FROM clientes")
    ventas = call_db_dict_movim("SELECT * FROM ventas")
    abonos = call_db_dict_movim("SELECT * FROM abonos")
    totcartera = []

    for cliente in clientes:
        clientesQty += 1

        ventas = call_db_all_dict_movim(f"SELECT * FROM ventas WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (cliente['ID'],))
        for ventax in ventas:
            ventasQty += 1
            total = int(ventax['P_VENTA']) * int(ventax['CANTIDAD'])
            totVentas += total

        abonos = call_db_all_dict_movim(f"SELECT * FROM abonos WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (cliente['ID'],))
        for abonox in abonos:
            abonosQty += 1
            totAbonos += abonox["VALOR"]

    allclientes = {'clientesQty': clientesQty, 'totVentas': totVentas, 'totAbonos': totAbonos, 'ventasQty':ventasQty, 'abonosQty':abonosQty}


    title = "Administracion Productos"
    return render_template('home.html', title="Rossy's Shop", productos=productos, allclientes=allclientes)


@app.route('/odsLoad')
def odsLoad():

    return render_template('ods_load.html', title="ods Load",)


# >>>>>>>>> CLIENTES >>>>>>>>>

@app.route('/all_clientes')
def all_clientes():
    clientes = call_db_dict_clientes("SELECT * FROM clientes")

    return render_template('clientes/clientes.html', title="Clientes", clientes=clientes)


@app.route('/crearCliente', methods=['GET', 'POST'])
def crearCliente():
    if request.method == "POST":
        incomming = request.form
        deuda = 0

        save_data_clientes(f"INSERT INTO clientes (NOMBRE, DIRECCION, BARRIO, TELEFONO, EMPRESA, CLIENTE_DE, COMPRA, DEUDA) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (incomming['nombre'], incomming['direccion'], incomming['barrio'], str(incomming['telefono']), incomming['empresa'], incomming['cliente_de'], incomming['compra'], deuda))

        flash('El cliente se creo exitosamente!.')
        return redirect(url_for('all_clientes'))
    
    return render_template('clientes/crear_cliente.html', title="Crear Cliente")


@app.route('/mostrarCliente/<int:id>', methods=['GET', 'POST'])
def mostrarCliente(id):
    cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID = ?", (id,))
    ventas = call_db_all_dict_movim(f"SELECT * FROM ventas WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (id,))
    abonos = call_db_all_dict_movim(f"SELECT * FROM abonos WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (id,))
    ventasAll = []
    gtotal = 0

    for ventax in ventas:
        
        total = int(ventax['P_VENTA']) * int(ventax['CANTIDAD'])
        gtotal += total
        print("total", int(ventax['P_VENTA']), '*', int(ventax['CANTIDAD']))
        print('gtotal', gtotal)

        ventasAll.append({
            'id': ventax["ID"],
            'producto': ventax['DESCRIPCION_PRODUCTO'], 
            'productoVal': ventax['P_VENTA'],
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
        update_data_clientes(sqlquery, data1)

        flash('La informacion del cliente se actualizo correctamente!.')
        return redirect(url_for('all_clientes'))

    cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID = ?", (id,))
    return render_template('clientes/modificar_cliente.html', title="Modificar Cliente", cliente=cliente)


@app.route('/load_clientes', methods=['GET', 'POST'])
def load_clientes():
    if request.method == "POST":
        clientes = []
        existe = ""
        DEUDA = 0
        inFile = request.files['plantillaVentas']
        names = call_db_dict_clientes("SELECT NOMBRE FROM clientes")

        if names:
            for name in names:
                clientes.append(name['NOMBRE'])

        try:
            dataframe = pd.read_excel(inFile, sheet_name='Clientes')
            dfClientes = clean_file(dataframe)
        except Exception as e:
            flash(f'No existe la Pestanna "Clientes", Error {str(e)}')
            return redirect(url_for('all_clientes'))

        if not names:
            for index, row in dfClientes.iterrows():
                save_data_clientes(f"INSERT INTO clientes (NOMBRE, DIRECCION, BARRIO, TELEFONO, EMPRESA, CLIENTE_DE, COMPRA, DEUDA) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (row['NOMBRE'], row['DIRECCION'], row['BARRIO'], row['TELEFONO'], row['EMPRESA'], row['CLIENTE_DE'], row['COMPRA'], DEUDA))
        else:
            for index, row in dfClientes.iterrows():
                if row['NOMBRE'] in clientes:
                    existe = "SI"
                else:
                    save_data_clientes(f"INSERT INTO clientes (NOMBRE, DIRECCION, BARRIO, TELEFONO, EMPRESA, CLIENTE_DE, COMPRA, DEUDA) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (row['NOMBRE'], row['DIRECCION'], row['BARRIO'], row['TELEFONO'], row['EMPRESA'], row['CLIENTE_DE'], row['COMPRA'], DEUDA))

        if existe == "SI":
            flash('Hay varios Clientes que ya existen!.')
        else:
            flash('La plantilla se subio exitosamente!.')

        return redirect(url_for('all_clientes'))

    return render_template('ods_load.html', title="ods Load", function="load_clientes")


# >>>>>>>>> PRODUCTOS >>>>>>>>>

@app.route('/all_productos')
def all_productos():
    productos = call_db_dict(f"SELECT * FROM productos")

    return render_template('productos/productos.html', title="Productos", productos=productos)


@app.route('/crearProducto', methods=['GET', 'POST'])
def crearProducto():
    if request.method == "POST":
        incomming = request.form
        productos = call_db_dict("SELECT * FROM productos")

        for producto in productos:
            if int(incomming['cl']) == int(producto['CL']) and int(incomming['pcatalogo']) == int(producto['P_VENTA']):
                flash('El Producto YA EXISTE!.')
                return redirect(url_for('all_productos'))
            elif int(incomming['cl']) == int(producto['CL']) and int(incomming['pcatalogo']) == int(producto['P_VENTA']):
                flash('El Producto YA EXISTE pero es diferente!.')
                return redirect(url_for('all_productos'))
            else:
                save_data(f"INSERT INTO productos (CL, DESCRIPCION, P_VENTA, UBICACION, REVISTA, CAMPANNA) VALUES (?, ?, ?, ?, ?, ?)", (int(incomming['cl']), incomming['descripcion'], int(incomming['pcatalogo']), incomming['ubica'], incomming['revista'], incomming['CAMPANNA']))
                flash('El Producto se creo exitosamente!.')
                return redirect(url_for('all_productos'))
    
    return render_template('productos/crear_producto.html', title="Crear Producto")


@app.route('/mostrarProducto/<int:id>', methods=['GET', 'POST'])
def mostrarProducto(id):
    producto = call_db_one_dict(f"SELECT * FROM productos WHERE ID = ?", (id,))

    return render_template('productos/producto.html', title="Mostrar Producto", producto=producto)


@app.route('/modificarProducto/<int:id>', methods=['GET', 'POST'])
def modificarProducto(id):
    producto = call_db_one_dict(f"SELECT * FROM productos WHERE ID = ?", (id,))

    if request.method == "POST":
        incomming = request.form
        update_data("UPDATE productos SET DESCRIPCION =?, P_COSTO =?, P_VENTA= ?, UBICACION= ?, REVISTA= ?, CAMPANNA= ? WHERE id= ?", (incomming['descripcion'], incomming['costo'], incomming['venta'], incomming['ubica'], incomming['revista'], incomming['campanna'], id))
        flash('El producto se actualizo exitosamente!.')
        return redirect(url_for('all_productos'))

    return render_template('productos/modificar_producto.html', title="Modificar Producto", producto=producto)


@app.route('/load_productos', methods=['GET', 'POST'])
def load_productos():
    if request.method == "POST":
        productos = []
        existe = ""
        inFile = request.files['plantillaVentas']
        products = call_db_dict(f"SELECT * FROM productos")

        if products:
            for prod in products:
                productos.append([prod['CL'], prod['REVISTA'], prod['CAMPANNA']])

        try:
            dataframe = pd.read_excel(inFile, sheet_name='Productos')
            dfProductos = clean_file(dataframe)
        except Exception as e:
            flash(f'No existe la Pestanna "Productos", Error {str(e)}')
            return redirect(url_for('all_productos'))

        if not products:
            for index, row in dfProductos.iterrows():
                save_data(f"INSERT INTO productos (CL, DESCRIPCION, P_COSTO, P_VENTA, UBICACION, REVISTA, CAMPANNA) VALUES (?, ?, ?, ?, ?, ?, ?)", (row['CL'], row['DESCRIPCION'], row['P_COSTO'], row['P_VENTA'], row['UBICACION'], row['REVISTA'], row['CAMPANNA']))
        else:
            for index, row in dfProductos.iterrows():
                if [row['CL'], row['REVISTA'], row['CAMPANNA']] in productos:
                    existe = "SI"
                else:
                    save_data(f"INSERT INTO productos (CL, DESCRIPCION, P_COSTO, P_VENTA, UBICACION, REVISTA, CAMPANNA) VALUES (?, ?, ?, ?, ?, ?, ?)", (row['CL'], row['DESCRIPCION'], row['P_COSTO'], row['P_VENTA'], row['UBICACION'], row['REVISTA'], row['CAMPANNA']))

        if existe == "SI":
            flash('Hay varios Productos que ya existen, Pero los que no, se grabaron exitosamente!.')
        else:
            flash('La plantilla se subio exitosamente!.')

        return redirect(url_for('all_productos'))

    return render_template('ods_load.html', title="ods Load", function="load_productos")


@app.route('/filtrarProd/<filter>')
def filtrarProd(filter):
    revista = filter.upper()
    productosAll = call_db_all_dict(f"SELECT * FROM productos WHERE REVISTA = ?", (revista,))
    productos = []

    for productx in productosAll:
        productos.append({
            'ID': productx["ID"],
            'CL': productx["CL"],
            'DESCRIPCION': productx['DESCRIPCION'], 
            'P_CATALOGO': productx['P_VENTA'],
            'UBICACION': productx['UBICACION'],
            'REVISTA': productx['REVISTA'],
            'CAMPANNA': productx['CAMPANNA'],
            'FECHA': productx['FECHA'],
        })
        
    title = "Productos " + filter
    return render_template('productos/productos.html', title=title, productos=productos)


@app.route('/adminProducts')
def adminProducts():
    novaQty = 0
    leonQty = 0
    modaQty = 0
    inventQty = 0

    nova = call_db_all_dict(f"SELECT * FROM productos WHERE REVISTA = ?", ('NOVAVENTA',))
    for item in nova:
        novaQty += 1

    leon = call_db_all_dict(f"SELECT * FROM productos WHERE REVISTA = ?", ('LEONISA',))
    for item in leon:
        leonQty += 1

    moda = call_db_all_dict(f"SELECT * FROM productos WHERE REVISTA = ?", ('MODA_INT',))
    for item in moda:
        modaQty += 1

    invent = call_db_all_dict(f"SELECT * FROM productos WHERE REVISTA = ?", ('INVENTARIO',))
    for item in invent:
        inventQty += 1

    title = "Administracion Productos"
    return render_template('productos/admin_products.html', title=title, novaQty=novaQty, leonQty=leonQty, modaQty=modaQty, inventQty=inventQty)


@app.route('/askDeleteProducto/<int:id>')
def askDeleteProducto(id):
    producto = call_db_one_dict(f"SELECT * FROM productos WHERE ID = ?", (id,))
    return render_template('productos/eliminar_producto.html', title="Eliminar Producto", producto=producto)


@app.route('/deleteProducto/<int:id>')
def deleteProducto(id):
    delete_data(f"DELETE FROM productos WHERE ID = ?", id)
    flash('El producto se elimino exitosamente!.')
    return redirect(url_for('all_productos'))


# >>>>>>>>> VENTAS >>>>>>>>>

@app.route('/all_ventas')
def all_ventas():
    ventas = call_db_dict_movim(f"SELECT * FROM ventas WHERE IMPRENTA = 'NO'")
    ventasAll = []

    for ventax in ventas:
        cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID = ?", (ventax["CLIENTE_ID"],))
        total = int(ventax['P_VENTA']) * int(ventax['CANTIDAD'])

        ventasAll.append({
            'id': ventax["ID"],
            'cliente': cliente['NOMBRE'], 
            'producto': ventax['DESCRIPCION_PRODUCTO'],
            'revista': ventax['REVISTA'],
            'campanna': ventax['CAMPANNA'],
            'productoVal': ventax['P_VENTA'],
            'qty': ventax['CANTIDAD'],
            'total': total,
            'fecha': ventax['FECHA'],
            'impreso': ventax['IMPRENTA']
        })

    return render_template('ventas/ventas.html', title="Ventas", ventasAll=ventasAll)


@app.route('/historia_ventas')
def historia_ventas():
    ventas = call_db_dict_movim(f"SELECT * FROM ventas")
    ventasAll = []

    for ventax in ventas:
        cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID = ?", (ventax["CLIENTE_ID"],))
        total = int(ventax['P_VENTA']) * int(ventax['CANTIDAD'])

        ventasAll.append({
            'id': ventax["ID"],
            'cliente': cliente['NOMBRE'], 
            'producto': ventax['DESCRIPCION_PRODUCTO'],
            'revista': ventax['REVISTA'],
            'campanna': ventax['CAMPANNA'],
            'productoVal': ventax['P_VENTA'],
            'qty': ventax['CANTIDAD'],
            'total': total,
            'fecha': ventax['FECHA'],
            'impreso': ventax['IMPRENTA']
        })
        
    return render_template('ventas/ventas.html', title="Ventas Novaventa", ventasAll=ventasAll)


@app.route('/crearVenta', methods=['GET', 'POST'])
def crearVenta():
    revistas = []
    clientes = call_db_dict_clientes(f"SELECT ID, NOMBRE FROM clientes")
    productos = call_db_dict("SELECT * FROM productos ORDER BY CL ASC")

    for prod in productos:
        if prod['REVISTA'] not in revistas:
            revistas.append(prod['REVISTA'])

    if request.method == "POST":
        incomming = request.form

        if incomming['producto1']:
            prod = incomming['producto1']
        else:
            prod = incomming['producto2']

        cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID =?", (incomming['cliente'],)) 
        producto = call_db_two_all_dict(f"SELECT * FROM productos WHERE CL =? AND REVISTA =?", (prod), (incomming['revista']))

        total = int(producto['P_VENTA']) * int(incomming['qty'])
        imprenta = "NO"
        fecha_imprenta = datetime.today().date()

        save_data_movim(f"INSERT INTO ventas (CLIENTE_ID, CL_PRODUCTO, DESCRIPCION_PRODUCTO, NOTA_DESCRIPTIVA, P_COSTO, P_VENTA, REVISTA, CAMPANNA, CANTIDAD, IMPRENTA, FECHA_IMPRENTA) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (incomming['cliente'], producto['CL'], producto['DESCRIPCION'], incomming['nota_descriptiva'], producto['P_COSTO'], producto['P_VENTA'], producto['REVISTA'], producto['CAMPANNA'], int(incomming['qty']), imprenta, fecha_imprenta, ))

        deuda = int(cliente['DEUDA']) + int(total)
        fecha = datetime.today().date()
        update_data_clientes(f"UPDATE clientes SET DEUDA=?, FECHA_ULTIMA_COMPRA=? WHERE id=?", (deuda, fecha, incomming['cliente']))

        flash('La Venta se creo exitosamente!.')
        return redirect(url_for('home'))
    
    return render_template('ventas/crear_venta.html', title="Crear Venta", clientes=clientes, productos=productos, revistas=revistas)


@app.route('/mostrarVenta/<int:id>', methods=['GET', 'POST'])
def mostrarVenta(id):
    venta = call_db_one_dict_movim(f"SELECT * FROM ventas WHERE ID = ?", (id,))
    cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID = ?", (int(venta['CLIENTE_ID']),))

    total = venta['P_VENTA'] * venta['CANTIDAD']

    return render_template('ventas/venta.html', title="Mostrar Venta", cliente=cliente, venta=venta, total=total)


@app.route('/modificarVenta/<int:id>', methods=['GET', 'POST'])
def modificarVenta(id):
    venta = call_db_one_dict_movim(f"SELECT * FROM ventas WHERE ID = ?", (id,))
    cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID =?", (venta['CLIENTE_ID'],)) 
    ventax = {
        'id': venta['ID'],
        'cliente': cliente['NOMBRE'],
        'productoCl': venta['CL_PRODUCTO'],  
        'producto': venta['DESCRIPCION_PRODUCTO'], 
        'nota_descriptiva': venta['NOTA_DESCRIPTIVA'], 
        'productoVal': venta['P_VENTA'],
        'revista': venta['REVISTA'],
        'campanna': venta['CAMPANNA'],
        'qty': venta['CANTIDAD'],
        'imprenta': venta['IMPRENTA'],
    }

    if request.method == "POST":
        incomming = request.form
        oldValue = (venta['P_VENTA'] * venta['CANTIDAD'])
        newValue = (int(incomming['ventaVal']) * int(incomming['qty']))
        if newValue < oldValue:
            difer = oldValue - newValue
            deuda = int(cliente['DEUDA']) - difer

            update_data_movim(f"UPDATE ventas SET CANTIDAD=?, P_VENTA=?, IMPRENTA=? WHERE id=?", (incomming['qty'], incomming['ventaVal'], incomming['imprenta'], id))
            update_data_clientes(f"UPDATE clientes SET DEUDA=? WHERE id=?", (deuda, cliente['ID']))

            flash('La informacion de la venta se actualizo correctamente!.')
            return redirect(url_for('all_ventas'))

        elif newValue > oldValue:
            difer = newValue - oldValue
            deuda = int(cliente['DEUDA']) + difer

            update_data_movim(f"UPDATE ventas SET CANTIDAD=?, P_VENTA=?, IMPRENTA=? WHERE id=?", (incomming['qty'], incomming['ventaVal'], incomming['imprenta'], id))
            update_data_clientes(f"UPDATE clientes SET DEUDA=? WHERE id=?", (deuda, cliente['ID']))

            flash('La informacion de la venta se actualizo correctamente!.')
            return redirect(url_for('all_ventas'))

        else:
            update_data_movim(f"UPDATE ventas SET IMPRENTA=? WHERE id=?", (incomming['imprenta'], id))

            flash('La informacion de la venta se actualizo correctamente!.')
            return redirect(url_for('all_ventas'))

    return render_template('ventas/modificar_venta.html', title="Modificar Venta", ventax=ventax)


@app.route('/load_ventas', methods=['GET', 'POST'])
def load_ventas():
    if request.method == "POST":
        inFile = request.files['plantillaVentas']
        dataframe = pd.read_excel(inFile, sheet_name='Ventas')
        dfVentas = clean_file(dataframe)

        try:
            productos = call_db_all_dict(f"SELECT * FROM productos WHERE REVISTA =? AND CAMPANNA = ?", (dfVentas.at[0, 'REVISTA'], dfVentas.at[0, 'CAMPANNA']))
        except:
            flash("No se encontraron registros de Productos")
            return redirect(url_for('home'))

        for index, row in dfVentas.iterrows():
            cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID = ?", (row['CLIENTE_ID'],))
            for product in productos:
                if product['CL'] == row['CL_PRODUCTO']:
                    imprenta = "NO"
                    total = product['P_VENTA'] * row['CANTIDAD']
                    deuda = int(cliente['DEUDA']) + total
                    fecha = datetime.today().date()

                    save_data_movim(f"INSERT INTO ventas (CLIENTE_ID, CL_PRODUCTO, DESCRIPCION_PRODUCTO, NOTA_DESCRIPTIVA, CANTIDAD, P_COSTO, P_VENTA, REVISTA, CAMPANNA, IMPRENTA) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (row['CLIENTE_ID'], row['CL_PRODUCTO'], product['DESCRIPCION'], row['NOTA_DESCRIPTIVA'], row['CANTIDAD'], product['P_COSTO'], product['P_VENTA'], row['REVISTA'], row['CAMPANNA'], imprenta))
                    update_data_clientes(f"UPDATE clientes SET DEUDA=?, FECHA_ULTIMA_COMPRA=? WHERE id=?", (deuda, fecha, row['CLIENTE_ID']))

        flash('La plantilla se subio exitosamente!.')
        return redirect(url_for('home'))

    return render_template('ods_load.html', title="ods Load", function="load_ventas")


@app.route('/filtrarAll/<filter>')
def filtrarAll(filter):
    revista = filter.upper()
    ventas = call_db_all_dict_movim(f"SELECT * FROM ventas WHERE REVISTA = ?", (revista,))
    ventasAll = []

    for ventax in ventas:
        cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID = ?", (ventax["CLIENTE_ID"],))
        total = int(ventax['P_VENTA']) * int(ventax['CANTIDAD'])

        ventasAll.append({
            'id': ventax["ID"],
            'cliente': cliente['NOMBRE'], 
            'producto': ventax['DESCRIPCION_PRODUCTO'],
            'nota_descriptiva': ventax['NOTA_DESCRIPTIVA'], 
            'revista': ventax['REVISTA'],
            'campanna': ventax['CAMPANNA'],
            'productoVal': ventax['P_VENTA'],
            'qty': ventax['CANTIDAD'],
            'total': total,
            'fecha': ventax['FECHA'],
            'impreso': ventax['IMPRENTA']
        })
        
    title = "Ventas " + filter
    return render_template('ventas/ventas.html', title=title, ventasAll=ventasAll)


@app.route('/filtrar/<filter>')
def filtrar(filter):
    revista = filter.upper()
    ventas = call_db_all_dict_movim(f"SELECT * FROM ventas WHERE IMPRENTA = 'NO' AND REVISTA = ?", (revista,))
    ventasAll = []

    for ventax in ventas:
        cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID = ?", (ventax["CLIENTE_ID"],))
        total = int(ventax['P_VENTA']) * int(ventax['CANTIDAD'])

        ventasAll.append({
            'id': ventax["ID"],
            'cliente': cliente['NOMBRE'], 
            'producto': ventax['DESCRIPCION_PRODUCTO'],
            'nota_descriptiva': ventax['NOTA_DESCRIPTIVA'], 
            'revista': ventax['REVISTA'],
            'campanna': ventax['CAMPANNA'],
            'productoVal': ventax['P_VENTA'],
            'qty': ventax['CANTIDAD'],
            'total': total,
            'fecha': ventax['FECHA'],
            'impreso': ventax['IMPRENTA']
        })
        
    title = "Ventas " + filter
    return render_template('ventas/ventas.html', title=title, ventasAll=ventasAll)


@app.route('/askDeleteVenta/<int:id>')
def askDeleteVenta(id):
    venta = call_db_one_dict_movim(f"SELECT * FROM ventas WHERE ID = ?", (id,))
    return render_template('ventas/eliminar_venta.html', title="Eliminar Venta", venta=venta)


@app.route('/deleteVenta/<int:id>')
def deleteVenta(id):
    venta = call_db_one_dict_movim(f"SELECT * FROM ventas WHERE ID = ?", (id,))
    cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID =?", (venta['CLIENTE_ID'],)) 

    total = int(venta['P_VENTA']) * int(venta['CANTIDAD'])
    deuda = int(cliente['DEUDA']) - int(total)

    update_data_clientes(f"UPDATE clientes SET DEUDA=?, WHERE id=?", (deuda, venta['CLIENTE_ID']))
    delete_data_movim(f"DELETE FROM ventas WHERE ID = ?", id)
    
    flash('El registro de la venta se elimino exitosamente!.')
    return redirect(url_for('all_ventas'))


# >>>>>>>>> ABONOS >>>>>>>>>

@app.route('/all_abonos')
def all_abonos():
    abonos = call_db_dict_movim(f"SELECT * FROM abonos")
    clientes = call_db_dict_clientes(f"SELECT * FROM clientes")
    abonosAll = []

    for pagox in abonos:
        cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID = ?", (pagox["CLIENTE_ID"],))
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
    clientes = call_db_dict_clientes(sqlQuery,)

    if request.method == "POST":
        incomming = request.form

        save_data_movim(f"INSERT INTO abonos (CLIENTE_ID, NOTAS, VALOR) VALUES (?, ?, ?)", (incomming['cliente'], incomming['notas'], incomming['valor']))
        cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID = ?", (incomming['cliente'],))

        deuda = int(cliente['DEUDA']) - int(incomming['valor'])
        fecha = datetime.today().date()
        update_data_clientes("UPDATE clientes SET DEUDA=?, FECHA_ULTIMO_ABONO=? WHERE id=?", (deuda, fecha, incomming['cliente']))

        flash('El abono se registro exitosamente!.')
        return redirect(url_for('all_abonos'))
    
    return render_template('abonos/crear_abono.html', title="Crear Abono", clientes=clientes)


@app.route('/mostrarAbono/<int:id>', methods=['GET', 'POST'])
def mostrarAbono(id):
    abono = call_db_one_dict_movim(f"SELECT * FROM abonos WHERE ID = ?", (id,))
    cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID = ?", (int(abono['CLIENTE_ID']),))

    return render_template('abonos/abono.html', title="Mostrar Abono", abono=abono, cliente=cliente)


@app.route('/modificarAbono/<int:id>', methods=['GET', 'POST'])
def modificarAbono(id):
    abono = call_db_one_dict_movim(f"SELECT * FROM abonos WHERE ID= ?", (id,))
    cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID= ?", (int(abono['CLIENTE_ID']),))

    if request.method == "POST":
        incomming = request.form
        update_data_movim("UPDATE abonos SET VALOR= ?, NOTAS= ? WHERE id= ?", (incomming['valor'], incomming['notas'], id))
        flash('El abono se actualizo exitosamente!.')
        return redirect(url_for('all_abonos'))
    
    return render_template('abonos/modificar_abono.html', title="Crear Abono", abono=abono, cliente=cliente)


@app.route('/askDeleteAbono/<int:id>')
def askDeleteAbono(id):
    abono = call_db_one_dict_movim(f"SELECT * FROM abonos WHERE ID = ?", (id,))
    return render_template('abonos/eliminar_abono.html', title="Eliminar Abono", abono=abono)


@app.route('/deleteAbono/<int:id>')
def deleteAbono(id):
    delete_data_movim(f"DELETE FROM abonos WHERE ID = ?", id)
    flash('El registro del abono se elimino exitosamente!.')
    return redirect(url_for('all_ventas'))


# >>>>>>>>> GENERAR RECIBOS >>>>>>>>>

@app.route('/registrosExcel')
def registrosExcel():
    campa = []
    catalogList = []
    chkFolder = os.path.isdir(DOWNLOAD_PATH)

    if not chkFolder:
        flash('No se encontraron catalogos anteriores.')
    else:
        catalogList = os.listdir(DOWNLOAD_PATH)
        catalogList.sort()
    
    ventas = call_db_dict_movim(f"SELECT REVISTA, CAMPANNA FROM ventas")

    for venta in ventas:
        if ({'revista': venta['REVISTA'], 'campana': venta['CAMPANNA']}) not in campa:
            campa.append({'revista': venta['REVISTA'], 'campana': venta['CAMPANNA']})

    return render_template('reportes/registrosExcel.html', title="Registros Excel", catalogList=catalogList, campa=campa)


@app.route('/cobrosXlsx', methods=['GET', 'POST'])
def cobrosXlsx():
    if request.method == "POST":
        ventasAll = call_db_all_dict_movim(f"SELECT * FROM ventas WHERE IMPRENTA='NO' AND REVISTA =? AND CAMPANNA =?", (request.form['data1'], request.form['data2']))
        clientes = []
        ventas = []

        if ventasAll:
            for venta in ventasAll:
                clientex = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID = ?", (venta["CLIENTE_ID"],))

                if {'nombre':clientex['NOMBRE'], 'deuda':clientex['DEUDA']} not in clientes:
                    clientes.append({'nombre':clientex['NOMBRE'], 'deuda':clientex['DEUDA']})

                cant = venta['CANTIDAD']
                total = int(venta['P_VENTA']) * int(venta['CANTIDAD'])
                campanna = venta['CAMPANNA']
                ventas.append({
                    'id': clientex['ID'], 
                    'cliente': clientex['NOMBRE'], 
                    'producto': venta['DESCRIPCION_PRODUCTO'], 
                    'productoVal': venta['P_VENTA'],
                    'qty': cant,
                    'total': total,
                })

                createfile = "Reporte" + "_" + request.form['data1'] + "_" + request.form['data2'] + "_"
                imprenta = "SI"
                fecha = datetime.today().date()
                print("Listo para gravar")
                update_data_movim(f"UPDATE ventas SET IMPRENTA=?, FECHA_IMPRENTA=? WHERE id=?", (imprenta, fecha, venta['ID']))
                print('supuesto ya gravo')

            reporteCobrosXlsx(clientes, ventas, createfile)
            flash("Los recibos se crearon satisfactoriamente!!")
            return redirect(url_for('registrosExcel'))
        else:
            flash(f'No se encontraron ventas de { request.form['data1'] }.')
            return redirect(url_for('all_ventas'))


@app.route('/delete_recibo/<file>')
def delete_recibo(file):
    os.remove(DOWNLOAD_PATH + file)
    flash("El recibo se elimino satisfactoriamente!!")
    return redirect(url_for('registrosExcel'))


@app.route('/cobrosPdf')
def cobrosPdf():
    ventasAll = call_db_dict_movim(f"SELECT * FROM ventas WHERE IMPRENTA = 'NO'")
    client = []
    ventas = []

    for venta in ventasAll:
        clientex = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID = ?", (venta["CLIENTE_ID"],))

        if clientex['NOMBRE'] not in client:
            client.append(clientex['NOMBRE'])
        
        producto = call_db_one_dict(f"SELECT * FROM productos WHERE CL = ?", (venta["PRODUCTO_ID"],))
        cant = venta['CANTIDAD']
        total = int(producto['P_VENTA']) * int(venta['CANTIDAD'])

        ventas.append({
            'cliente': clientex['NOMBRE'], 
            'producto': producto['DESCRIPCION'], 
            'productoVal': producto['P_VENTA'],
            'qty': cant,
            'total': total,
        })
        
    reporteCobros(client, ventas)
    return render_template('ventas/ventas.html', title="Ventas", client=client, ventas=ventas)


@app.route('/cartera')
def cartera():
    clientes = call_db_dict_clientes("SELECT * FROM clientes")
    ventas = call_db_dict_movim("SELECT * FROM ventas")
    abonos = call_db_dict_movim("SELECT * FROM abonos")
    totcartera = []

    for cliente in clientes:
        totVentas = 0
        totAbonos = 0
        ventas = call_db_all_dict_movim(f"SELECT * FROM ventas WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (cliente['ID'],))
        abonos = call_db_all_dict_movim(f"SELECT * FROM abonos WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (cliente['ID'],))

        for ventax in ventas:
            total = int(ventax['P_VENTA']) * int(ventax['CANTIDAD'])
            totVentas += total

        for abonox in abonos:
            totAbonos += abonox["VALOR"]

        totcartera.append({'id': cliente["ID"], 'cliente': cliente["NOMBRE"], 'totVentas': totVentas, 'totAbonos': totAbonos})

    return render_template('reportes/carteras.html', title="Cartera", totcartera=totcartera)


@app.route('/mostrarCartera/<int:id>', methods=['GET', 'POST'])
def mostrarCartera(id):
    cliente = call_db_one_dict_clientes(f"SELECT * FROM clientes WHERE ID = ?", (id,))
    ventas = call_db_all_dict_movim(f"SELECT * FROM ventas WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (cliente['ID'],))
    abonos = call_db_all_dict_movim(f"SELECT * FROM abonos WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (cliente['ID'],))
    cartera = []
    totVentas = 0
    totAbonos = 0
    totcartera = []

    for ventax in ventas:
        total = int(ventax['P_VENTA']) * int(ventax['CANTIDAD'])
        totVentas += total
        cartera.append({
            'cliente': cliente["NOMBRE"],
            'id': ventax["ID"],
            'descripcion': ventax['DESCRIPCION_PRODUCTO'], 
            'revista': ventax['REVISTA'], 
            'campanna': ventax['CAMPANNA'], 
            'qty': ventax["CANTIDAD"],
            'Vtotal': total,
            'fecha': ventax['FECHA']
        })

    for abonox in abonos:
        totAbonos += abonox["VALOR"]
        cartera.append({
            'cliente': cliente["NOMBRE"],
            'id': abonox["ID"],
            'descripcion': abonox['NOTAS'], 
            'Atotal': abonox["VALOR"],
            'fecha': ventax['FECHA']
        })

    return render_template('reportes/cartera.html', title="Cartera", cartera=cartera, totVentas=totVentas, totAbonos=totAbonos)


@app.route('/carteraXlsx')
def carteraXlsx():
    clientes = call_db_dict_clientes("SELECT * FROM clientes")
    ventas = call_db_dict_movim("SELECT * FROM ventas")
    abonos = call_db_dict_movim("SELECT * FROM abonos")
    allnames = []
    cartera = []
    totcartera = []

    for cliente in clientes:
        totVentas = 0
        totAbonos = 0
        ventas = call_db_all_dict_movim(f"SELECT * FROM ventas WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (cliente['ID'],))
        abonos = call_db_all_dict_movim(f"SELECT * FROM abonos WHERE CLIENTE_ID = ? ORDER BY FECHA DESC", (cliente['ID'],))

        if cliente['NOMBRE'] not in allnames:
            allnames.append({'nombre': cliente['NOMBRE']})

        for ventax in ventas:
            total = int(ventax['P_VENTA']) * int(ventax['CANTIDAD'])
            cartera.append({
                'cliente': cliente['NOMBRE'],
                'id': ventax["ID"],
                'descripcion': ventax['DESCRIPCION_PRODUCTO'], 
                'revista': ventax['REVISTA'], 
                'campanna': ventax['CAMPANNA'], 
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
        
        totcartera.append({'cliente': cliente['NOMBRE'], 'deuda': cliente['DEUDA'], 'totVentas': totVentas, 'totAbonos': totAbonos, 'grandTot': grandTot})

    createfile = "Reporte" + "_" + "Cartera" + "_"
            
    reporteCarteraXlsx(allnames, cartera, totcartera, createfile)
    flash("El excel de cartera se creo satisfactoriamente!!")
    return redirect(url_for('registrosExcel'))


@app.route('/uploads/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    
    return send_from_directory(directory=DOWNLOAD_PATH, path=filename)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5005, debug=True)

