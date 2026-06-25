import os
import smtplib
import traceback
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from supabase import create_client
from dotenv import load_dotenv
import uuid
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuración de Supabase
boveda = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SECRET_KEY"))

# --- MOTOR DE CORREO (SMTP_SSL) ---
def enviar_certificado_html(destinatario, nombre_pieza, uuid_orden, precio_mxn):
    remitente = os.getenv("EMAIL_TALLER")
    password = os.getenv("EMAIL_PASSWORD")
    
    msg = MIMEMultipart()
    msg['From'] = f"AURA Alta Joyería <{remitente}>"
    msg['To'] = destinatario
    msg['Subject'] = f"💎 Certificado de Propiedad: {nombre_pieza}"
    
    html = f"""
    <html>
        <body>
            <h1>Certificado AURA</h1>
            <p>Gracias por tu adquisición de: <strong>{nombre_pieza}</strong></p>
            <p>Inversión: <strong>${precio_mxn} MXN</strong></p>
            <p>Folio de Bóveda: <code>{uuid_orden}</code></p>
        </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(remitente, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"❌ [SMTP ERROR CRÍTICO]: {str(e)}")
        return False

# --- RUTAS API ---
@app.route('/api/reservar-pieza', methods=['POST'])
def reservar_pieza():
    try:
        data = request.json
        email = data.get('email')
        joya_id = int(data.get('joya_id'))

        # Obtener precio para cumplir restricciones SQL
        res_joya = boveda.table('joyas_stock').select('nombre, precio_centavos').eq('id', joya_id).execute()
        joya_info = res_joya.data[0]
        precio = joya_info['precio_centavos']

        # Insertar con columnas exactas de tu tabla
        res_orden = boveda.table('ordenes_compra').insert({
            'usuario_email': email,
            'joya_id': joya_id,
            'cantidad': 1,
            'monto_total_centavos': precio,
            'estado': 'PENDIENTE_PAYPAL'
        }).execute()
        
        orden_uuid = res_orden.data[0]['id']

        # Crear orden PayPal
        token = requests.post("https://api-m.sandbox.paypal.com/v1/oauth2/token", 
                              data={"grant_type": "client_credentials"}, 
                              auth=(os.getenv("PAYPAL_CLIENT_ID"), os.getenv("PAYPAL_SECRET"))).json()["access_token"]
        
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{"amount": {"currency_code": "MXN", "value": f"{precio/100:.2f}"}}],
            "application_context": {
                "return_url": f"https://maximiliano1234345.github.io/joyeria-aura/index.html?transaccion=aprobada&orden_uuid={orden_uuid}",
                "cancel_url": "https://maximiliano1234345.github.io/joyeria-aura/index.html?transaccion=cancelada"
            }
        }
        paypal_res = requests.post("https://api-m.sandbox.paypal.com/v2/checkout/orders", headers=headers, json=payload).json()
        
        # Guardar PayPal ID
        boveda.table('ordenes_compra').update({"paypal_order_id": paypal_res['id']}).eq('id', orden_uuid).execute()
        
        enlace = next(item['href'] for item in paypal_res['links'] if item['rel'] == 'approve')
        return jsonify({"orden_uuid": orden_uuid, "url_pasarela": enlace}), 200

    except Exception:
        print(f"❌ [RESERVAR ERROR]: {traceback.format_exc()}")
        return jsonify({"mensaje": "Error en reserva"}), 500

@app.route('/api/confirmar-compra', methods=['POST'])
def confirmar_compra():
    uuid_orden = request.json.get('orden_uuid')
    try:
        # Actualizar estado
        boveda.table('ordenes_compra').update({"estado": "PAGADO"}).eq('id', uuid_orden).execute()
        
        # Obtener datos para correo
        res = boveda.table('ordenes_compra').select('joya_id, usuario_email').eq('id', uuid_orden).execute()
        email_cliente = res.data[0]['usuario_email']
        joya_id = res.data[0]['joya_id']
        
        res_joya = boveda.table('joyas_stock').select('nombre, precio_centavos').eq('id', joya_id).execute()
        nombre_joya = res_joya.data[0]['nombre']
        precio_formateado = f"{(res_joya.data[0]['precio_centavos'] / 100.0):,.2f}"
        
        # LLAMADO CORRECTO: nombre de función y 4 argumentos
        exito = enviar_certificado_html(email_cliente, nombre_joya, uuid_orden, precio_formateado)
        
        return jsonify({"estatus": "CONFIRMADO", "correo_enviado": exito}), 200
        
    except Exception:
        print(f"❌ [CONFIRMAR ERROR]: {traceback.format_exc()}")
        return jsonify({"mensaje": "Error interno"}), 500

if __name__ == '__main__':
    app.run(port=5000)
