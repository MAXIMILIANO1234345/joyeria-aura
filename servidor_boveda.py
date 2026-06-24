import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv
import traceback

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

url_supabase: str = os.getenv("SUPABASE_URL")
clave_supabase: str = os.getenv("SUPABASE_SECRET_KEY")
boveda: Client = create_client(url_supabase, clave_supabase)

def obtener_gafete_paypal():
    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    secret = os.getenv("PAYPAL_SECRET")
    respuesta = requests.post(url, headers=headers, data=data, auth=(client_id, secret))
    return respuesta.json()["access_token"]

def enviar_certificado_html(destinatario, nombre_pieza, uuid_orden, precio_mxn):
    remitente = os.getenv("EMAIL_TALLER")
    password = os.getenv("EMAIL_PASSWORD")
    msg = MIMEMultipart()
    msg['From'] = f"AURA Alta Joyería <{remitente}>"
    msg['To'] = destinatario
    msg['Subject'] = f"💎 Certificado de Propiedad: {nombre_pieza}"
    
    html = f"<html><body><h1>Certificado AURA</h1><p>Pieza: {nombre_pieza}</p><p>Folio: {uuid_orden}</p></body></html>"
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remitente, password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ Error SMTP: {e}")
        return False

@app.route('/api/confirmar-compra', methods=['POST', 'OPTIONS'])
def liquidar_y_certificar():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.json
    uuid_orden = data.get('orden_uuid')

    if not uuid_orden:
        return jsonify({"mensaje": "Falta UUID"}), 400

    try:
        # CORRECCIÓN: Usando 'usuario_email' y 'estado' como en image_f674a8.png
        res_orden = boveda.table('ordenes_compra').select('joya_id, usuario_email, estado').eq('id', uuid_orden).execute()
        
        if not res_orden.data:
            return jsonify({"mensaje": "Orden no localizada"}), 404

        joya_id = res_orden.data[0]['joya_id']
        email_cliente = res_orden.data[0]['usuario_email']
        estatus_actual = res_orden.data[0].get('estado')

        if estatus_actual == 'PAGADO':
            return jsonify({"estatus": "YA_PROCESADO"}), 200

        # CORRECCIÓN: Actualizando la columna 'estado'
        boveda.table('ordenes_compra').update({"estado": "PAGADO"}).eq('id', uuid_orden).execute()

        res_joya = boveda.table('joyas_stock').select('nombre, precio_centavos').eq('id', joya_id).execute()
        nombre_joya = res_joya.data[0]['nombre']
        precio = f"{(res_joya.data[0]['precio_centavos'] / 100.0):,.2f}"

        exito_mail = enviar_certificado_html(email_cliente, nombre_joya, uuid_orden, precio)

        return jsonify({"estatus": "CONFIRMADO", "correo_enviado": exito_mail}), 200

    except Exception:
        print(f"❌ CRASH: {traceback.format_exc()}")
        return jsonify({"mensaje": "Error interno"}), 500

if __name__ == '__main__':
    app.run()
