from flask import Flask, request, render_template_string, redirect, session, send_file
import sqlite3
from datetime import datetime
import csv
import os

app = Flask(__name__)

# CLAVE SESION
app.secret_key = "sensor123"

# CONTRASEÑA ADMIN
ADMIN_PASSWORD = "121102"

# BASE DE DATOS (UN SOLO ARCHIVO CENTRAL)
conexion = sqlite3.connect('sensor.db', check_same_thread=False)
cursor = conexion.cursor()

# =========================
# TABLA SENSOR (AHORA CON FECHA)
# =========================
cursor.execute('''
CREATE TABLE IF NOT EXISTS temperatura (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temp REAL,
    humedad REAL,
    fecha TEXT
)
''')

# =========================
# TABLA VISITAS
# =========================
cursor.execute('''
CREATE TABLE IF NOT EXISTS visitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT,
    navegador TEXT,
    fecha TEXT
)
''')

conexion.commit()

# LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        usuario = request.form['usuario']
        password = request.form['password']

        session['usuario'] = usuario

        ip = request.remote_addr
        navegador = request.user_agent.string
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "INSERT INTO visitas (ip, navegador, fecha) VALUES (?, ?, ?)",
            (ip, navegador, fecha)
        )

        conexion.commit()

        return redirect('/grafica')

    return '''
    <html>
    <body style="font-family:Arial; text-align:center; margin-top:100px;">
    <h1>LOGIN SENSOR DHT11</h1>

    <form method="POST">
    <input type="text" name="usuario" placeholder="Usuario" required><br><br>
    <input type="password" name="password" placeholder="Contraseña" required><br><br>
    <button type="submit">Entrar</button>
    </form>

    </body>
    </html>
    '''

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# GUARDAR SENSOR
@app.route('/guardar')
def guardar():

    temp = request.args.get('temp')
    humedad = request.args.get('humedad')
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO temperatura (temp, humedad, fecha) VALUES (?, ?, ?)",
        (temp, humedad, fecha)
    )

    conexion.commit()

    return "Datos guardados"

# GRAFICA
@app.route('/grafica')
def grafica():

    if 'usuario' not in session:
        return redirect('/')

    cursor.execute("SELECT * FROM temperatura ORDER BY id DESC LIMIT 20")
    datos = cursor.fetchall()

    html = """

    <html>
    <head>
    <title>DHT11 ONLINE</title>
    <meta http-equiv="refresh" content="5">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>

    <body style="font-family: Arial; text-align:center;">

    <h1>Sensor DHT11 Online</h1>

    <a href="/logout"><button>Cerrar Sesión</button></a>
    <a href="/admin"><button>Panel Admin</button></a>
    <a href="/descargar"><button>Descargar Base de Datos</button></a>

    <br><br>

    <canvas id="grafica"></canvas>

    <table border="1" style="margin:auto; margin-top:20px;">
    <tr>
    <th>ID</th>
    <th>Temperatura</th>
    <th>Humedad</th>
    <th>Fecha</th>
    </tr>

    {% for fila in datos %}
    <tr>
    <td>{{ fila[0] }}</td>
    <td>{{ fila[1] }}</td>
    <td>{{ fila[2] }}</td>
    <td>{{ fila[3] }}</td>
    </tr>
    {% endfor %}

    </table>

    <script>

    const datos = {{ datos|tojson }};
    const temperaturas = datos.map(x => x[1]);
    const humedad = datos.map(x => x[2]);
    const etiquetas = datos.map(x => x[0]);

    new Chart(document.getElementById('grafica'), {

        type: 'line',

        data: {

            labels: etiquetas,

            datasets: [

            {
                label: 'Temperatura',
                data: temperaturas
            },

            {
                label: 'Humedad',
                data: humedad
            }

            ]

        }

    });

    </script>

    </body>
    </html>

    """

    return render_template_string(html, datos=datos)

# =========================
# DESCARGAR BASE DE DATOS COMPLETA
# =========================
@app.route('/descargar')
def descargar():

    if 'usuario' not in session:
        return redirect('/')

    archivo = "sensor_completo.csv"

    cursor.execute("SELECT * FROM temperatura")
    datos = cursor.fetchall()

    with open(archivo, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Temperatura", "Humedad", "Fecha"])
        writer.writerows(datos)

    return send_file(archivo, as_attachment=True)

# PANEL ADMIN
@app.route('/admin', methods=['GET', 'POST'])
def admin():

    if 'usuario' not in session:
        return redirect('/')

    if not session.get('admin'):

        if request.method == 'POST':

            password = request.form['password']

            if password == ADMIN_PASSWORD:
                session['admin'] = True
                return redirect('/admin')
            else:
                return "<h1>Contraseña incorrecta</h1><a href='/admin'>Volver</a>"

        return '''
        <html>
        <body style="font-family:Arial; text-align:center; margin-top:100px;">
        <h1>Acceso Admin</h1>

        <form method="POST">
        <input type="password" name="password" required>
        <button>Entrar</button>
        </form>

        <a href="/grafica">Volver</a>
        </body>
        </html>
        '''

    cursor.execute("SELECT * FROM visitas ORDER BY id DESC")
    visitas = cursor.fetchall()

    return render_template_string("""
    <html>
    <body style="font-family:Arial; text-align:center;">
    <h1>Registro de Usuarios</h1>

    <a href="/grafica"><button>Volver</button></a>
    <a href="/logout"><button>Cerrar Sesión</button></a>

    <br><br>

    <table border="1" style="margin:auto;">
    <tr>
    <th>ID</th><th>IP</th><th>Navegador</th><th>Fecha</th>
    </tr>

    {% for fila in visitas %}
    <tr>
    <td>{{ fila[0] }}</td>
    <td>{{ fila[1] }}</td>
    <td>{{ fila[2] }}</td>
    <td>{{ fila[3] }}</td>
    </tr>
    {% endfor %}

    </table>

    </body>
    </html>
    """, visitas=visitas)

# =========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
