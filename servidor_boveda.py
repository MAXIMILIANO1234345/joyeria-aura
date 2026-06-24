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
# CORS simplificado y reforzado: abre la puerta a todo
CORS(app)

url_supabase = os.getenv("SUPABASE_URL")
clave_supabase = os.getenv("SUPABASE_SECRET_KEY")
boveda = create_client(url_supabase, clave_supabase)

# --- Funciones auxiliares (PayPal, Correo) se mantienen igual ---
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
    except:
        return False

# --- RUTAS ---
@app.route('/api/reservar-pieza', methods=['POST'])
def despachar_transaccion():
    paquete_js = request.json
    email_cliente = paquete_js.get('email')
    id_joya = paquete_js.get('joya_id')

    try:
        res_boveda = boveda.table('ordenes_compra').insert({
            'usuario_email': email_cliente,
            'joya_id': int(id_joya),
            'estado': 'PENDIENTE_PAYPAL'
        }).execute()
        
        uuid_orden = res_boveda.data[0]['id']
        # ... lógica PayPal ...
        return jsonify({"orden_uuid": uuid_orden, "url_pasarela": "https://sandbox.paypal.com/..."}), 200
    except Exception as e:
        return jsonify({"mensaje": str(e)}), 400

@app.route('/api/confirmar-compra', methods=['POST'])
def liquidar_y_certificar():
    data = request.json
    uuid_orden = data.get('orden_uuid')
    
try:
        # Aquí estamos agregando 'cantidad': 1 para cumplir con el contrato de la base de datos
        res_boveda = boveda.table('ordenes_compra').insert({
            'usuario_email': email_cliente,
            'joya_id': int(id_joya),
            'estado': 'PENDIENTE_PAYPAL',
            'cantidad': 1 
        }).execute()
        
        uuid_orden = res_boveda.data[0]['id']
        # ... resto del código ...
        if not res_orden.data:
            return jsonify({"mensaje": "Orden no localizada"}), 404

        # Actualización de estado
        boveda.table('ordenes_compra').update({"estado": "PAGADO"}).eq('id', uuid_orden).execute()
        return jsonify({"estatus": "CONFIRMADO"}), 200
    except Exception:
        return jsonify({"mensaje": "Error interno"}), 500

if __name__ == '__main__':
    app.run()
