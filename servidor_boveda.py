import os
import smtplib
import traceback
import requests
import random
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from supabase import create_client
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
# Configuración global de CORS para permitir todas las solicitudes del frontend
CORS(app)

# Configuración de Supabase
boveda = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SECRET_KEY"))

# ==========================================
# MOTORES DE CORREO (SMTP)
# ==========================================

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

def enviar_codigo_email(destinatario, codigo):
    remitente = os.getenv("EMAIL_TALLER")
    password = os.getenv("EMAIL_PASSWORD")
    
    msg = MIMEMultipart()
    msg['From'] = f"AURA Alta Joyería <{remitente}>"
    msg['To'] = destinatario
    msg['Subject'] = "AURA - Token de Seguridad VIP"
    
    html = f"""
    <html>
        <body style="font-family: sans-serif; text-align: center; color: #333;">
            <h2>Autenticación de Bóveda AURA</h2>
            <p>Tu token de acceso de 6 dígitos es:</p>
            <h1 style="letter-spacing: 5px; color: #5a2e3f;">{codigo}</h1>
            <p style="font-size: 0.8rem; color: #777;">Este token expirará en 15 minutos. Si no solicitaste este acceso, por favor ignora este mensaje.</p>
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
        print(f"❌ [SMTP ERROR - TOKEN]: {str(e)}")
        return False


# ==========================================
# RUTAS DE AUTENTICACIÓN VIP Y PERFIL
# ==========================================

@app.route('/api/crear-cuenta', methods=['POST', 'OPTIONS'])
def crear_cuenta():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        data = request.json
        usuario = data.get('usuario', '').strip()
        telefono = data.get('telefono', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        
        if not all([usuario, telefono, email, password]):
            return jsonify({"mensaje": "Todos los campos son obligatorios"}), 400
            
        res_existente = boveda.table('usuarios_vip').select('id').eq('email', email).execute()
        if res_existente.data:
            return jsonify({"mensaje": "Este correo ya está registrado. Por favor, inicia sesión."}), 409
            
        codigo = str(random.randint(100000, 999999))
        expiracion = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
        hashed_pw = generate_password_hash(password)
        
        boveda.table('usuarios_vip').insert({
            "usuario": usuario,
            "telefono": telefono,
            "email": email, 
            "password_hash": hashed_pw,
            "codigo_acceso": codigo, 
            "expiracion_codigo": expiracion,
            "cuenta_verificada": False
        }).execute()
        
        exito = enviar_codigo_email(email, codigo)
        return jsonify({"mensaje": "Cuenta creada. Token enviado al correo."}), 200
            
    except Exception as e:
        print(f"❌ [ERROR CREAR CUENTA]: {traceback.format_exc()}")
        return jsonify({"mensaje": "Error interno del servidor"}), 500


@app.route('/api/iniciar-sesion', methods=['POST', 'OPTIONS'])
def iniciar_sesion():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        email = request.json.get('email', '').strip().lower()
        password = request.json.get('password', '').strip()
        
        res_usuario = boveda.table('usuarios_vip').select('*').eq('email', email).execute()
        
        if not res_usuario.data:
            return jsonify({"mensaje": "El correo no está registrado en nuestra bóveda."}), 404
            
        usuario = res_usuario.data[0]
        
        if not check_password_hash(usuario['password_hash'], password):
            return jsonify({"mensaje": "Contraseña incorrecta."}), 401
            
        codigo = str(random.randint(100000, 999999))
        expiracion = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
        
        boveda.table('usuarios_vip').update({
            "codigo_acceso": codigo, 
            "expiracion_codigo": expiracion
        }).eq('email', email).execute()
        
        exito = enviar_codigo_email(email, codigo)
        return jsonify({"mensaje": "Credenciales correctas. Código 2FA enviado."}), 200
        
    except Exception as e:
        print(f"❌ [ERROR INICIAR SESIÓN]: {traceback.format_exc()}")
        return jsonify({"mensaje": "Error interno del servidor"}), 500


@app.route('/api/verificar-codigo', methods=['POST', 'OPTIONS'])
def verificar_codigo():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        email = request.json.get('email', '').strip().lower()
        codigo = request.json.get('codigo', '').strip()
        
        res_usuario = boveda.table('usuarios_vip').select('*').eq('email', email).execute()
        if not res_usuario.data:
            return jsonify({"mensaje": "Usuario no encontrado"}), 404
            
        usuario = res_usuario.data[0]
        
        if usuario.get('codigo_acceso') != codigo:
            return jsonify({"mensaje": "Token incorrecto"}), 401
            
        expiracion_str = usuario.get('expiracion_codigo')
        if expiracion_str:
            expiracion = datetime.fromisoformat(expiracion_str.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expiracion:
                return jsonify({"mensaje": "El token ha expirado"}), 401
        
        ahora = datetime.now(timezone.utc).isoformat()
        
        boveda.table('usuarios_vip').update({
            "codigo_acceso": None, 
            "ultimo_acceso": ahora,
            "cuenta_verificada": True
        }).eq('email', email).execute()
        
        return jsonify({"mensaje": "Acceso concedido", "email": email, "usuario": usuario['usuario']}), 200
        
    except Exception as e:
        print(f"❌ [ERROR VERIFICAR CÓDIGO]: {traceback.format_exc()}")
        return jsonify({"mensaje": "Error interno del servidor"}), 500


# --- NUEVA RUTA: PERFIL DEL USUARIO (INTEGRACIÓN 3NF) ---
@app.route('/api/perfil-usuario', methods=['POST', 'OPTIONS'])
def perfil_usuario():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        email = request.json.get('email', '').strip().lower()
        
        # 1. Obtener los datos del usuario (Nombre, Teléfono y su UUID)
        res_user = boveda.table('usuarios_vip').select('id, usuario, telefono').eq('email', email).execute()
        
        if not res_user.data:
            return jsonify({"mensaje": "Usuario no encontrado"}), 404
            
        user_data = res_user.data[0]
        usuario_id = user_data['id']
        
        # 2. Buscar todas las órdenes de este usuario gracias al nuevo "cable" relacional (usuario_id)
        res_pedidos = boveda.table('ordenes_compra').select('id, estado, fecha_creacion, joya_id').eq('usuario_id', usuario_id).order('fecha_creacion', desc=True).execute()
        
        historial = []
        if res_pedidos.data:
            for pedido in res_pedidos.data:
                # 3. Buscar el nombre de la joya para cada pedido
                res_joya = boveda.table('joyas_stock').select('nombre').eq('id', pedido['joya_id']).execute()
                nombre_pieza = res_joya.data[0]['nombre'] if res_joya.data else "Joya AURA"
                
                historial.append({
                    "id_orden": pedido['id'],
                    "estado": pedido['estado'],
                    "fecha": pedido['fecha_creacion'],
                    "nombre_joya": nombre_pieza
                })
                
        return jsonify({
            "usuario": user_data['usuario'],
            "telefono": user_data['telefono'],
            "pedidos": historial
        }), 200

    except Exception as e:
        print(f"❌ [ERROR PERFIL]: {traceback.format_exc()}")
        return jsonify({"mensaje": "Error interno del servidor"}), 500


# ==========================================
# RUTAS DE RESERVA Y PASARELA DE PAGO
# ==========================================

@app.route('/api/reservar-carrito', methods=['POST', 'OPTIONS'])
def reservar_carrito():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        data = request.json
        email = data.get('email')
        items = data.get('items', [])

        if not items:
            return jsonify({"mensaje": "El carrito está vacío"}), 400

        # --- NUEVA INTEGRACIÓN ---
        # Buscamos el ID único del usuario para formalizar la relación en la base de datos
        res_user = boveda.table('usuarios_vip').select('id').eq('email', email).execute()
        usuario_uuid = res_user.data[0]['id'] if res_user.data else None

        monto_total_centavos = 0
        cantidad_total = 0
        
        for item in items:
            joya_id_raw = item.get('joya_id')
            if joya_id_raw is None or isinstance(joya_id_raw, dict):
                return jsonify({"mensaje": "Formato desactualizado. Por favor, limpia tu carrito."}), 400
                
            joya_id = int(joya_id_raw)
            cantidad = int(item.get('cantidad', 1))
            
            res_joya = boveda.table('joyas_stock').select('precio_centavos').eq('id', joya_id).execute()
            if res_joya.data:
                monto_total_centavos += (res_joya.data[0]['precio_centavos'] * cantidad)
                cantidad_total += cantidad

        primer_joya_id = int(items[0]['joya_id'])

        # --- AHORA GUARDAMOS TANTO EL EMAIL COMO EL usuario_id ---
        res_orden = boveda.table('ordenes_compra').insert({
            'usuario_email': email,
            'usuario_id': usuario_uuid,  # El nuevo "cable" hacia la tabla VIP
            'joya_id': primer_joya_id, 
            'cantidad': cantidad_total,
            'monto_total_centavos': monto_total_centavos,
            'estado': 'PENDIENTE_PAYPAL'
        }).execute()
        
        orden_uuid = res_orden.data[0]['id']

        token_req = requests.post(
            "https://api-m.sandbox.paypal.com/v1/oauth2/token", 
            data={"grant_type": "client_credentials"}, 
            auth=(os.getenv("PAYPAL_CLIENT_ID"), os.getenv("PAYPAL_SECRET"))
        )
        token = token_req.json()["access_token"]
        
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{"amount": {"currency_code": "MXN", "value": f"{monto_total_centavos/100:.2f}"}}],
            "application_context": {
                "return_url": f"https://maximiliano1234345.github.io/joyeria-aura/index.html?transaccion=aprobada&orden_uuid={orden_uuid}",
                "cancel_url": "https://maximiliano1234345.github.io/joyeria-aura/index.html?transaccion=cancelada"
            }
        }
        paypal_res = requests.post("https://api-m.sandbox.paypal.com/v2/checkout/orders", headers=headers, json=payload).json()
        
        boveda.table('ordenes_compra').update({"paypal_order_id": paypal_res['id']}).eq('id', orden_uuid).execute()
        
        enlace = next(item['href'] for item in paypal_res['links'] if item['rel'] == 'approve')
        return jsonify({"orden_uuid": orden_uuid, "url_pasarela": enlace}), 200

    except Exception as e:
        print(f"❌ [RESERVAR CARRITO ERROR]: {traceback.format_exc()}")
        return jsonify({"mensaje": "Error en reserva del carrito"}), 500


@app.route('/api/confirmar-compra', methods=['POST'])
def confirmar_compra():
    uuid_orden = request.json.get('orden_uuid')
    try:
        boveda.table('ordenes_compra').update({"estado": "PAGADO"}).eq('id', uuid_orden).execute()
        
        res = boveda.table('ordenes_compra').select('joya_id, usuario_email').eq('id', uuid_orden).execute()
        email_cliente = res.data[0]['usuario_email']
        joya_id = res.data[0]['joya_id']
        
        res_joya = boveda.table('joyas_stock').select('nombre, precio_centavos').eq('id', joya_id).execute()
        nombre_joya = res_joya.data[0]['nombre']
        precio_formateado = f"{(res_joya.data[0]['precio_centavos'] / 100.0):,.2f}"
        
        exito = enviar_certificado_html(email_cliente, nombre_joya, uuid_orden, precio_formateado)
        
        return jsonify({"estatus": "CONFIRMADO", "correo_enviado": exito}), 200
        
    except Exception:
        print(f"❌ [CONFIRMAR ERROR]: {traceback.format_exc()}")
        return jsonify({"mensaje": "Error interno"}), 500


if __name__ == '__main__':
    app.run(port=5000)
