import os
import smtplib
from email.mime.text import MIMEText
from flask import Flask, jsonify, request
from flask_cors import CORS
from mssql_python import connect

app = Flask(__name__)

# ==============================
# 🌐 CORS (CORRECTO)
# ==============================
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"]
)

@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


# ==============================
# 🔌 CONEXIÓN SQL SERVER
# ==============================
def get_connection():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    port = os.getenv("DB_PORT", "1433")

    if not server or not database or not username or not password:
        raise ValueError("Faltan variables de entorno DB")

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
        "message": "API Flask funcionando correctamente"
    })


# ==============================
# 📩 ENVIAR CORREO (JSON + FORM)
# ==============================
@app.route("/enviar-alerta", methods=["POST", "OPTIONS"])
def enviar_alerta():

    # Preflight CORS
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    try:
        # 🔥 soporta JSON y formulario
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

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
# 🧪 DEBUG
# ==============================
@app.route("/debug-env")
def debug_env():
    return jsonify({
        "EMAIL_USER": os.getenv("EMAIL_USER"),
        "EMAIL_PASS_EXISTS": bool(os.getenv("EMAIL_PASS")),
        "DB_SERVER": os.getenv("DB_SERVER"),
    })


# ==============================
# 🚀 RUN
# ==============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
