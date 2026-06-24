import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv() # <--- Absorbe lo que guardaste en el archivo oculto .env

app = Flask(__name__)
CORS(app) 

# REGLA DE BÓVEDA: Las claves ya no existen en el código, viven en la RAM:
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

boveda: Client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
@app.route('/api/reservar-pieza', methods=['POST'])
def despachar_transaccion():
    paquete_js = request.json
    
    email_cliente = paquete_js.get('email')
    id_joya = paquete_js.get('joya_id')

    if not email_cliente or not id_joya:
        return jsonify({"estatus": "ERROR", "mensaje": "Faltan datos de inspección"}), 400

    print(f"⚡ [BÓVEDA]: Solicitud de reserva recibida para {email_cliente}, Pieza #{id_joya}")

    try:
        # INVOCAMOS EL PROCEDIMIENTO ALMACENADO CON CANDADO PESIMISTA (FOR UPDATE)
        # Python no calcula nada, le delega la responsabilidad matemática a Postgres
        respuesta = boveda.rpc(
            'reservar_pieza_para_pago', 
            {
                'p_joya_id': int(id_joya),
                'p_cantidad': 1,
                'p_email_cliente': email_cliente
            }
        ).execute()

        uuid_generado = respuesta.data

        print(f"🔒 [BÓVEDA]: Candado cerrado con éxito. Orden -> {uuid_generado}")

        return jsonify({
            "estatus": "EXITO",
            "orden_uuid": uuid_generado,
            # Aquí en el futuro le pegaremos el link real que nos devuelva la API de PayPal
            "url_pasarela": f"https://sandbox.paypal.com/checkout?token={uuid_generado}"
        }), 200

    except Exception as e:
        error_crudo = str(e)
        print(f"❌ [BÓVEDA RECHAZO]: {error_crudo}")
        
        # Si Postgres arrojó un ROLLBACK (ej. stock en cero), devolvemos un código 409 (Conflict)
        return jsonify({
            "estatus": "AGOTADO",
            "mensaje": "La pieza acaba de ser adquirida por otro coleccionista."
        }), 409


if __name__ == '__main__':
    # Prendemos el motor en el puerto 5000 de tu computadora
    app.run(debug=True, port=5000)