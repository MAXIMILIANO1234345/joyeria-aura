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

load_dotenv()

app = Flask(__name__)
# CORS configurado para permitir todo desde cualquier origen
CORS(app)

# Inicializar Supabase
boveda = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SECRET_KEY"))

# --- FUNCIONES DE SERVICIO ---
def obtener_token_paypal():
    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    data = {"grant_type": "client_credentials"}
    auth = (os.getenv("PAYPAL_CLIENT_ID"), os.getenv("PAYPAL_SECRET"))
    return requests.post(url, data=data, auth=auth).json()["access_token"]

def enviar_certificado_email(destinatario, nombre_joya, folio):
    remitente = os.getenv("EMAIL_TALLER")
    password = os.getenv("EMAIL_PASSWORD")
    
    msg = MIMEMultipart()
    msg['From'] = f"AURA Alta Joyería <{remitente}>"
    msg['To'] = destinatario
    msg['Subject'] = "💎 Certificado de Autenticidad AURA"
    
    html = f"<html><body><h1>Certificado AURA</h1><p>Gracias por tu compra de: {nombre_joya}</p><p>Folio: {folio}</p></body></html>"
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
def reservar_pieza():
    try:
        data = request.json
        email = data.get('email')
        joya_id = int(data.get('joya_id'))

        # 1. Obtener precio de la joya para cumplir restricciones SQL
        res_joya = boveda.table('joyas_stock').select('nombre, precio_centavos').eq('id', joya_id).execute()
        joya_info = res_joya.data[0]
        precio = joya_info['precio_centavos']

        # 2. Insertar en ordenes_compra (Cumpliendo NOT NULL de cantidad y monto)
        res_orden = boveda.table('ordenes_compra').insert({
            'usuario_email': email,
            'joya_id': joya_id,
            'cantidad': 1,
            'monto_total_centavos': precio,
            'estado': 'PENDIENTE_PAYPAL'
        }).execute()
        
        orden_uuid = res_orden.data[0]['id']

        # 3. Crear orden en PayPal
        token = obtener_token_paypal()
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
        
        # 4. Actualizar PayPal ID
        boveda.table('ordenes_compra').update({"paypal_order_id": paypal_res['id']}).eq('id', orden_uuid).execute()
        
        enlace = next(item['href'] for item in paypal_res['links'] if item['rel'] == 'approve')
        return jsonify({"orden_uuid": orden_uuid, "url_pasarela": enlace}), 200

    except Exception as e:
        print(f"ERROR: {traceback.format_exc()}")
        return jsonify({"mensaje": str(e)}), 500

@app.route('/api/confirmar-compra', methods=['POST'])
def confirmar_compra():
    uuid_orden = request.json.get('orden_uuid')
    try:
        # Actualizar a PAGADO
        boveda.table('ordenes_compra').update({"estado": "PAGADO"}).eq('id', uuid_orden).execute()
        
        # Obtener datos para correo
        res = boveda.table('ordenes_compra').select('joya_id, usuario_email').eq('id', uuid_orden).execute()
        res_joya = boveda.table('joyas_stock').select('nombre').eq('id', res.data[0]['joya_id']).execute()
        
        enviar_certificado_email(res.data[0]['usuario_email'], res_joya.data[0]['nombre'], uuid_orden)
        
        return jsonify({"estatus": "CONFIRMADO"}), 200
    except Exception as e:
        print(f"ERROR CONFIRMACION: {traceback.format_exc()}")
        return jsonify({"mensaje": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
