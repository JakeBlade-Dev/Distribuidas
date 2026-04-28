import os
import smtplib
from email.mime.text import MIMEText
from flask import Flask, jsonify, request
from mssql_python import connect
from flask_cors import CORS

app = Flask(__name__)

# ==============================
# 🌐 CORS (CORREGIDO)
# ==============================
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response


# ==============================
# 🔌 CONEXIÓN A SQL SERVER
# ==============================
def get_connection():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    port = os.getenv("DB_PORT", "1433")

    if not server:
        raise ValueError("Falta DB_SERVER")
    if not database:
        raise ValueError("Falta DB_DATABASE")
    if not username:
        raise ValueError("Falta DB_USERNAME")
    if not password:
        raise ValueError("Falta DB_PASSWORD")

    connection_string = (
        f"Server=tcp:{server},{port};"
        f"Database={database};"
        f"Uid={username};"
        f"Pwd={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Authentication=SqlPassword;"
    )

    return connect(connection_string)


# ==============================
# ✉️ ENVÍO DE CORREO
# ==============================
def enviar_correo_alerta(asunto, mensaje, destino):
    remitente = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")

    if not remitente or not password:
        raise ValueError("Faltan credenciales de correo")

    msg = MIMEText(mensaje)
    msg["Subject"] = asunto
    msg["From"] = remitente
    msg["To"] = destino

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(remitente, password)
        server.send_message(msg)


# ==============================
# 🏠 HOME
# ==============================
@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "API Flask funcionando correctamente en Render"
    })


# ==============================
# 📩 ENVIAR CORREO
# ==============================
@app.route("/enviar-alerta", methods=["POST", "OPTIONS"])
def enviar_alerta():

    # Manejo explícito de preflight
    if request.method == "OPTIONS":
        return jsonify({"success": True})

    try:
        data = request.get_json()

        destino = data.get("to")
        asunto = data.get("subject")
        mensaje = data.get("message")

        if not destino or not asunto or not mensaje:
            return jsonify({
                "success": False,
                "message": "Faltan datos"
            }), 400

        if "@" not in destino:
            return jsonify({
                "success": False,
                "message": "Correo inválido"
            }), 400

        enviar_correo_alerta(asunto, mensaje, destino)

        return jsonify({
            "success": True,
            "message": "Correo enviado correctamente"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==============================
# 🧪 DEBUG VARIABLES
# ==============================
@app.route("/debug-env")
def debug_env():
    return jsonify({
        "DB_SERVER": os.getenv("DB_SERVER"),
        "DB_DATABASE": os.getenv("DB_DATABASE"),
        "DB_USERNAME": os.getenv("DB_USERNAME"),
        "DB_PASSWORD_EXISTS": bool(os.getenv("DB_PASSWORD")),
        "DB_PORT": os.getenv("DB_PORT"),
        "EMAIL_USER": os.getenv("EMAIL_USER"),
        "EMAIL_PASS_EXISTS": bool(os.getenv("EMAIL_PASS"))
    })


# ==============================
# 🧪 TEST DB
# ==============================
@app.route("/test-db")
def test_db():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT GETDATE()")
        row = cursor.fetchone()

        return jsonify({
            "success": True,
            "server_date": str(row[0])
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# 📦 PRODUCTOS
# ==============================
@app.route("/productos")
def listar_productos():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TOP 20 id, nombre, precio, imagen_url
            FROM productos
            ORDER BY id DESC
        """)

        rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append({
                "id": row[0],
                "nombre": row[1],
                "precio": float(row[2]) if row[2] else None,
                "imagen_url": row[3],
            })

        return jsonify({
            "success": True,
            "data": data
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# 🚀 RUN
# ==============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
