import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# MODO NUCLEAR DE CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# --- CREDENCIALES DE BÓVEDA ---
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


# ====================================================================
# MOTOR SMTP: Redacción del Certificado VIP (Vía Gmail)
# ====================================================================
def enviar_certificado_html(destinatario, nombre_pieza, uuid_orden, precio_mxn):
    remitente = os.getenv("EMAIL_TALLER")
    password = os.getenv("EMAIL_PASSWORD")

    if not remitente or not password:
        print("⚠️ [ADVERTENCIA]: Faltan variables EMAIL_TALLER o EMAIL_PASSWORD en Render.")
        return False

    msg = MIMEMultipart()
    msg['From'] = f"AURA Alta Joyería <{remitente}>"
    msg['To'] = destinatario
    msg['Subject'] = f"💎 Certificado de Propiedad: {nombre_pieza} | AURA Atelier"

    # Plantilla HTML de Lujo Editorial
    html_editorial = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="background-color: #F4F3F0; font-family: 'Times New Roman', Times, serif; color: #111111; margin: 0; padding: 40px 20px;">
        <div style="max-width: 560px; margin: 0 auto; background-color: #FFFFFF; padding: 50px 40px; border: 1px solid #E2DFD9; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.03);">
            
            <div style="font-size: 26px; letter-spacing: 8px; font-weight: bold; margin-bottom: 5px;">AURA</div>
            <div style="font-size: 10px; letter-spacing: 4px; color: #888888; text-transform: uppercase; margin-bottom: 40px;">Atelier de Alta Joyería</div>
            
            <h1 style="font-size: 22px; font-weight: normal; font-style: italic; margin-bottom: 10px;">Certificado de Autenticidad y Adquisición</h1>
            <p style="font-size: 14px; color: #555555; line-height: 1.5; margin-bottom: 30px;">
                Emitido a favor de <strong>{destinatario}</strong> como titular en firme.
            </p>

            <div style="margin: 30px 0; padding: 25px 0; border-top: 1px solid #E2DFD9; border-bottom: 1px solid #E2DFD9;">
                <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 2px; color: #A37E2C; margin-bottom: 8px;">Pieza Coleccionista</div>
                <div style="font-size: 28px; font-weight: bold; letter-spacing: 1px; color: #111111;">"{nombre_pieza}"</div>
            </div>

            <table style="width: 100%; text-align: left; font-size: 13px; line-height: 2; margin-bottom: 40px; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #F4F3F0;">
                    <td style="color: #777777; width: 45%;">Folio de Bóveda:</td>
                    <td style="font-family: monospace; font-size: 11px; color: #333333;">{uuid_orden}</td>
                </tr>
                <tr style="border-bottom: 1px solid #F4F3F0;">
                    <td style="color: #777777;">Inversión Capturada:</td>
                    <td><strong>${precio_mxn} MXN</strong></td>
                </tr>
                <tr>
                    <td style="color: #777777;">Estatus de Custodia:</td>
                    <td style="color: #2E7D32;">● En Taller Central (Asignando lingote)</td>
                </tr>
            </table>

            <p style="font-size: 13px; color: #666666; font-style: italic; line-height: 1.6; margin-bottom: 40px;">
                "La luz no se crea, se captura."<br>
                Su platino ha sido separado. Un maestro orfebre iniciará el proceso manual de pulido hoy mismo.
            </p>

            <div style="font-size: 10px; color: #AAAAAA; letter-spacing: 1px; border-top: 1px solid #F4F3F0; padding-top: 20px;">
                AURA ALTA JOYERÍA · PARÍS · LONDRES · CIUDAD DE MÉXICO<br>
                Documento con validez legal y respaldo criptográfico en Supabase.
            </div>

        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_editorial, 'html'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remitente, password)
            server.send_message(msg)
        print(f"✉️ [ÉXITO SMTP]: Certificado VIP despachado a {destinatario}")
        return True
    except Exception as e:
        print(f"❌ [ERROR SMTP GMAIL]: {e}")
        return False


@app.route('/', methods=['GET'])
def recepcion_principal():
    return jsonify({"estatus": "ONLINE 🟢", "taller": "AURA Atelier VIP"}), 200


# ====================================================================
# ENDPOINT 1: El que genera la orden y manda a PayPal
# ====================================================================
@app.route('/api/reservar-pieza', methods=['POST', 'OPTIONS'])
def despachar_transaccion():
    if request.method == 'OPTIONS':
        res = jsonify({"mensaje": "CORS OK"})
        res.headers.add('Access-Control-Allow-Origin', '*')
        res.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        res.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return res, 200

    paquete_js = request.json
    email_cliente = paquete_js.get('email')
    id_joya = paquete_js.get('joya_id')

    if not email_cliente or not id_joya:
        return jsonify({"mensaje": "Faltan datos de cliente"}), 400

    try:
        res_boveda = boveda.rpc('reservar_pieza_para_pago', {
            'p_joya_id': int(id_joya),
            'p_cantidad': 1,
            'p_email_cliente': email_cliente
        }).execute()

        uuid_orden_supabase = res_boveda.data

        info_joya = boveda.table('joyas_stock').select('precio_centavos', 'nombre').eq('id', int(id_joya)).execute()
        precio_formato_paypal = f"{(info_joya.data[0]['precio_centavos'] / 100.0):.2f}"

        token_paypal = obtener_gafete_paypal()
        url_ordenes_pp = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
        
        headers_pp = {"Content-Type": "application/json", "Authorization": f"Bearer {token_paypal}"}

        # ⚠️ ATENCIÓN AQUÍ: Le pegamos el orden_uuid a la URL de retorno para que JS lo pueda atrapar
        url_aprobada = f"https://maximiliano1234345.github.io/joyeria-aura/index.html?transaccion=aprobada&orden_uuid={str(uuid_orden_supabase)}"
        url_cancelada = "https://maximiliano1234345.github.io/joyeria-aura/index.html?transaccion=cancelada"

        payload_pp = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": str(uuid_orden_supabase),
                "amount": {"currency_code": "MXN", "value": precio_formato_paypal},
                "description": f"Pieza AURA: {info_joya.data[0]['nombre']}"
            }],
            "application_context": {
                "brand_name": "AURA | ALTA JOYERÍA",
                "return_url": url_aprobada,
                "cancel_url": url_cancelada
            }
        }

        respuesta_paypal = requests.post(url_ordenes_pp, headers=headers_pp, json=payload_pp).json()
        enlace_aprobacion = next(item['href'] for item in respuesta_paypal['links'] if item['rel'] == 'approve')

        boveda.table('ordenes_compra').update({"paypal_order_id": respuesta_paypal['id']}).eq('id', uuid_orden_supabase).execute()

        return jsonify({"estatus": "EXITO", "orden_uuid": uuid_orden_supabase, "url_pasarela": enlace_aprobacion}), 200

    except Exception as e:
        return jsonify({"mensaje": "La pieza ya fue reservada por otro cliente."}), 409


# ====================================================================
# ENDPOINT 2 (NUEVO): El que escucha el regreso de PayPal y dispara el correo
# ====================================================================
@app.route('/api/confirmar-compra', methods=['POST', 'OPTIONS'])
def liquidar_y_certificar():
    if request.method == 'OPTIONS':
        res = jsonify({"mensaje": "CORS OK"})
        res.headers.add('Access-Control-Allow-Origin', '*')
        res.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        res.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return res, 200

    data = request.json
    uuid_orden = data.get('orden_uuid')

    if not uuid_orden:
        return jsonify({"mensaje": "Falta el UUID de la orden"}), 400

    try:
        # 1. Buscamos qué joya compró y quién es el dueño:
        res_orden = boveda.table('ordenes_compra').select('joya_id, email_cliente').eq('id', uuid_orden).execute()
        if not res_orden.data:
            return jsonify({"mensaje": "Orden no localizada"}), 404

        joya_id = res_orden.data[0]['joya_id']
        email_cliente = res_orden.data[0]['email_cliente']

        # 2. Buscamos el nombre elegante y el precio de la joya:
        res_joya = boveda.table('joyas_stock').select('nombre, precio_centavos').eq('id', joya_id).execute()
        nombre_joya = res_joya.data[0]['nombre']
        precio_formateado = f"{(res_joya.data[0]['precio_centavos'] / 100.0):,.2f}"

        # 3. Disparamos el misil de Gmail:
        exito_mail = enviar_certificado_html(email_cliente, nombre_joya, uuid_orden, precio_formateado)

        return jsonify({
            "estatus": "CONFIRMADO",
            "email": email_cliente,
            "correo_enviado": exito_mail
        }), 200

    except Exception as e:
        print(f"❌ [FALLO DE CONFIRMACIÓN]: {e}")
        return jsonify({"mensaje": "Error interno al despachar el certificado"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
