from flask import Flask, request, render_template_string, redirect

import sqlite3

app = Flask(__name__)

# BASE DE DATOS
conexion = sqlite3.connect('sensor.db', check_same_thread=False)
cursor = conexion.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS temperatura (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temp REAL,
    humedad REAL
)
''')

conexion.commit()

# LOGIN
@app.route('/', methods=['GET', 'POST'])

def login():

    if request.method == 'POST':

        password = request.form['password']

        if password == "24250510":

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

    <input type="text" placeholder="Usuario" required><br><br>

    <input type="password" name="password" placeholder="Contraseña" required><br><br>

    <button type="submit">Entrar</button>

    </form>

    </body>

    </html>

    '''

# GUARDAR DATOS
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

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=10000)
