from flask import Flask, request, render_template_string, redirect, session, send_file
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
import csv

def fecha_actual():
    return datetime.now(
        ZoneInfo("America/Mexico_City")
    ).strftime("%Y-%m-%d %H:%M:%S")

app = Flask(__name__)
app.secret_key = "sensor123"

API_KEY = "ARDUINO123"

conexion = sqlite3.connect("sensor.db", check_same_thread=False)
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE,
    password TEXT,
    rol TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS temperatura (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temp REAL,
    humedad REAL,
    fecha TEXT,
    usuario_envio TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS visitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT,
    navegador TEXT,
    fecha TEXT
)
""")

cursor.execute("""
INSERT OR IGNORE INTO usuarios(usuario,password,rol)
VALUES ('admin','121102','admin')
""")

cursor.execute("""
INSERT OR IGNORE INTO usuarios(usuario,password,rol)
VALUES ('consulta','1234','consulta')
""")

conexion.commit()

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        cursor.execute(
            "SELECT usuario, rol FROM usuarios WHERE usuario=? AND password=?",
            (usuario,password)
        )
        user = cursor.fetchone()

        if user:
            session["usuario"] = user[0]
            session["rol"] = user[1]

            cursor.execute(
                "INSERT INTO visitas(ip,navegador,fecha) VALUES(?,?,?)",
                (
                    request.remote_addr,
                    request.user_agent.string,
                    fecha_actual()
                )
            )
            conexion.commit()

            return redirect("/grafica")

        return "<h1>Login incorrecto</h1><a href='/'>Volver</a>"

    return """
    <html><body style='font-family:Arial;text-align:center;margin-top:100px;'>
    <h1>LOGIN SENSOR DHT11</h1>
    <form method='POST'>
    <input name='usuario' placeholder='Usuario'><br><br>
    <input type='password' name='password' placeholder='Contraseña'><br><br>
    <button>Entrar</button>
    </form>
    </body></html>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/guardar")
def guardar():
    key = request.args.get("key")
    usuario = request.args.get("user")
    temp = request.args.get("temp")
    humedad = request.args.get("humedad")

    if key != API_KEY:
        return "NO AUTORIZADO", 401

    cursor.execute("SELECT * FROM usuarios WHERE usuario=?", (usuario,))
    if not cursor.fetchone():
        return "USUARIO INVALIDO", 401

    cursor.execute(
        "INSERT INTO temperatura(temp,humedad,fecha,usuario_envio) VALUES(?,?,?,?)",
        (
            temp,
            humedad,
            fecha_actual(),
            usuario
        )
    )
    conexion.commit()

    return "OK"

@app.route("/grafica")
def grafica():
    if "usuario" not in session:
        return redirect("/")

    if session["rol"] == "consulta":
        hoy = fecha_actual()[:10]
        cursor.execute(
            "SELECT * FROM temperatura WHERE fecha LIKE ? ORDER BY id DESC LIMIT 100",
            (hoy + "%",)
        )
    else:
        fecha = request.args.get("fecha")
        if fecha:
            cursor.execute(
                "SELECT * FROM temperatura WHERE fecha LIKE ? ORDER BY id DESC",
                (fecha + "%",)
            )
        else:
            cursor.execute(
                "SELECT * FROM temperatura ORDER BY id DESC LIMIT 100"
            )

    datos = cursor.fetchall()
    fecha_servidor = fecha_actual()

    html = """
    <html>
    <head>
    <meta http-equiv="refresh" content="10">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body style="font-family:Arial;text-align:center;">

    <h1>Dashboard IoT</h1>
    <h3>Fecha y hora del servidor: {{ fecha_servidor }}</h3>

    <a href="/logout"><button>Cerrar Sesión</button></a>

    {% if session['rol'] == 'admin' %}
    <a href="/admin"><button>Panel Admin</button></a>

    <form method="GET" action="/grafica">
    <input type="date" name="fecha">
    <button type="submit">Buscar Fecha</button>
    </form>
    {% endif %}

    <canvas id="grafica"></canvas>

    <table border="1" style="margin:auto;">
    <tr>
    <th>ID</th>
    <th>Temp</th>
    <th>Humedad</th>
    <th>Fecha</th>
    <th>Usuario</th>
    </tr>

    {% for fila in datos %}
    <tr>
    <td>{{fila[0]}}</td>
    <td>{{fila[1]}}</td>
    <td>{{fila[2]}}</td>
    <td>{{fila[3]}}</td>
    <td>{{fila[4]}}</td>
    </tr>
    {% endfor %}
    </table>

    <script>
    const datos = {{ datos|tojson }};
    new Chart(document.getElementById('grafica'),{
      type:'line',
      data:{
        labels:datos.map(x=>x[0]),
        datasets:[
          {label:'Temperatura',data:datos.map(x=>x[1])},
          {label:'Humedad',data:datos.map(x=>x[2])}
        ]
      }
    });
    </script>

    </body>
    </html>
    """
    return render_template_string(
        html,
        datos=datos,
        fecha_servidor=fecha_servidor
    )

@app.route("/admin")
def admin():
    if session.get("rol") != "admin":
        return "NO AUTORIZADO"

    cursor.execute("SELECT * FROM visitas ORDER BY id DESC")
    visitas = cursor.fetchall()

    return render_template_string("""
    <h1>Panel Administrador</h1>

    <a href="/grafica"><button>Volver</button></a>
    <a href="/logout"><button>Cerrar Sesión</button></a>
    <a href="/descargar"><button>Descargar CSV</button></a>

    <table border="1">
    <tr><th>ID</th><th>IP</th><th>Navegador</th><th>Fecha</th></tr>

    {% for v in visitas %}
    <tr>
    <td>{{v[0]}}</td>
    <td>{{v[1]}}</td>
    <td>{{v[2]}}</td>
    <td>{{v[3]}}</td>
    </tr>
    {% endfor %}
    </table>
    """, visitas=visitas)

@app.route("/descargar")
def descargar():
    if session.get("rol") != "admin":
        return "NO AUTORIZADO"

    archivo = "sensores.csv"

    cursor.execute("SELECT * FROM temperatura")
    datos = cursor.fetchall()

    with open(archivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID","TEMP","HUMEDAD","FECHA","USUARIO"])
        writer.writerows(datos)

    return send_file(archivo, as_attachment=True)
    
    @app.route("/ver_db")
def ver_db():

    cursor.execute("""
    SELECT *
    FROM temperatura
    ORDER BY id DESC
    """)

    datos = cursor.fetchall()

    html = """
    <h1>Base de Datos SQLite</h1>

    <table border='1'>
    <tr>
        <th>ID</th>
        <th>Temperatura</th>
        <th>Humedad</th>
        <th>Fecha</th>
        <th>Usuario</th>
    </tr>
    """

    for fila in datos:
        html += f"""
        <tr>
            <td>{fila[0]}</td>
            <td>{fila[1]}</td>
            <td>{fila[2]}</td>
            <td>{fila[3]}</td>
            <td>{fila[4]}</td>
        </tr>
        """

    html += "</table>"

    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
