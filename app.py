from flask import Flask, request, render_template_string, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)

# CLAVE SESION
app.secret_key = "sensor123"

# BASE DE DATOS
conexion = sqlite3.connect('sensor.db', check_same_thread=False)
cursor = conexion.cursor()

# TABLA SENSOR
cursor.execute('''
CREATE TABLE IF NOT EXISTS temperatura (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temp REAL,
    humedad REAL
)
''')

# TABLA VISITAS
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

        if password == "24250510":

            session['usuario'] = usuario

            # GUARDAR VISITA
            ip = request.remote_addr
            navegador = request.user_agent.string
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                "INSERT INTO visitas (ip, navegador, fecha) VALUES (?, ?, ?)",
                (ip, navegador, fecha)
            )

            conexion.commit()

            return redirect('/grafica')

        else:

            return '''
            <h1>Contraseña incorrecta</h1>
            <a href="/">Volver</a>
            '''

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

# CERRAR SESION
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# GUARDAR DATOS SENSOR
@app.route('/guardar')
def guardar():

    temp = request.args.get('temp')
    humedad = request.args.get('humedad')

    cursor.execute(
        "INSERT INTO temperatura (temp, humedad) VALUES (?, ?)",
        (temp, humedad)
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

    <a href="/logout">
    <button>Cerrar Sesión</button>
    </a>

    <br><br>

    <a href="/admin">
    <button>Panel Admin</button>
    </a>

    <canvas id="grafica"></canvas>

    <table border="1" style="margin:auto; margin-top:20px;">

    <tr>

    <th>ID</th>
    <th>Temperatura</th>
    <th>Humedad</th>

    </tr>

    {% for fila in datos %}

    <tr>

    <td>{{ fila[0] }}</td>
    <td>{{ fila[1] }}</td>
    <td>{{ fila[2] }}</td>

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

# PANEL ADMIN
@app.route('/admin')
def admin():

    if 'usuario' not in session:
        return redirect('/')

    cursor.execute("SELECT * FROM visitas ORDER BY id DESC")

    visitas = cursor.fetchall()

    html = """

    <html>

    <body style="font-family:Arial; text-align:center;">

    <h1>Registro de Usuarios</h1>

    <a href="/grafica">
    <button>Volver</button>
    </a>

    <br><br>

    <table border="1" style="margin:auto;">

    <tr>

    <th>ID</th>
    <th>IP</th>
    <th>Navegador</th>
    <th>Fecha</th>

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

    """

    return render_template_string(html, visitas=visitas)

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=10000)
