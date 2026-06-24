import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Busca donde dice CORS(app) y cámbialo por esto:
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://maximiliano1234345.github.io",
            "http://127.0.0.1:5500",
            "http://localhost:5500"
        ],
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")

boveda: Client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

# ====================================================================
# MOTOR DE COMUNICACIÓN VISA/MASTERCARD (PayPal REST API v2)
# ====================================================================
def obtener_gafete_paypal():
    """Llama a la puerta de PayPal con Usuario y Contraseña para pedir un Token temporal"""
    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "es_MX"}
    data = {"grant_type": "client_credentials"}
    
    respuesta = requests.post(url, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET), headers=headers, data=data)
    return respuesta.json()["access_token"]


@app.route('/api/reservar-pieza', methods=['POST'])
def despachar_transaccion():
    paquete_js = request.json
    email_cliente = paquete_js.get('email')
    id_joya = paquete_js.get('joya_id')

    if not email_cliente or not id_joya:
        return jsonify({"mensaje": "Faltan credenciales de inspección"}), 400

    try:
        # 1. DISPARAMOS EL CANDADO PESIMISTA EN POSTGRESQL
        res_boveda = boveda.rpc('reservar_pieza_para_pago', {
            'p_joya_id': int(id_joya),
            'p_cantidad': 1,
            'p_email_cliente': email_cliente
        }).execute()

        uuid_orden_supabase = res_boveda.data

        # 2. SEGUNDA LEY DE SEGURIDAD: Consultamos el precio REAL en la base de datos
        # (Jamás le creemos al precio que nos mande el archivo app.js)
        info_joya = boveda.table('joyas_stock').select('precio_centavos', 'nombre').eq('id', int(id_joya)).execute()
        
        precio_en_centavos = info_joya.data[0]['precio_centavos']
        nombre_pieza = info_joya.data[0]['nombre']
        
        # Convertimos los centavos enteros (1680000) al formato string que exige PayPal ("16800.00")
        precio_formato_paypal = f"{(precio_en_centavos / 100.0):.2f}"

        # 3. SOLICITAMOS LA APERTURA DE TERMINAL A PAYPAL
        token_paypal = obtener_gafete_paypal()
        url_ordenes_pp = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
        
        headers_pp = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token_paypal}"
        }

        # El manifiesto de cobro que verá el cliente en su pantalla de Visa/Mastercard:
        payload_pp = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": str(uuid_orden_supabase), # Enlazamos el UUID de Postgres con el recibo de PayPal
                "amount": {
                    "currency_code": "MXN",
                    "value": precio_formato_paypal
                },
                "description": f"Pieza AURA: {nombre_pieza} (Certificado para {email_cliente})"
            }],
            "application_context": {
                "brand_name": "AURA | ALTA JOYERÍA", # Sello de lujo en la cabecera del banco
                "landing_page": "LOGIN",
                "user_action": "PAY_NOW",
                # A dónde va a escupir PayPal al cliente cuando termine de teclear su tarjeta:
                "return_url": "http://127.0.0.1:5500/index.html?transaccion=aprobada",
                "cancel_url": "http://127.0.0.1:5500/index.html?transaccion=cancelada"
            }
        }

        respuesta_paypal = requests.post(url_ordenes_pp, headers=headers_pp, json=payload_pp).json()

        # Extraemos el enlace de pago seguro de entre la basura de datos que contesta PayPal
        enlace_aprobacion = next(item['href'] for item in respuesta_paypal['links'] if item['rel'] == 'approve')

        # Le inyectamos a nuestra fila de Supabase el ID de rastreo que le asignó PayPal
        boveda.table('ordenes_compra').update({"paypal_order_id": respuesta_paypal['id']}).eq('id', uuid_orden_supabase).execute()

        print(f"🔗 [TERMINAL ABIERTA]: Pasarela lista para orden -> {uuid_orden_supabase}")

        return jsonify({
            "estatus": "EXITO",
            "orden_uuid": uuid_orden_supabase,
            "url_pasarela": enlace_aprobacion
        }), 200

    except Exception as e:
        print(f"❌ [FALLO DE BÓVEDA]: {e}")
        return jsonify({"mensaje": "La pieza solicitada acaba de ser reservada por otro coleccionista."}), 409


if __name__ == '__main__':
    app.run(debug=True, port=5000)
