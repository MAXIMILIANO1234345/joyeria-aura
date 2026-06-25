# ==========================================
# @author: Maximiliano Cabello
# Proyecto: AURA Alta Joyería - Servidor Central
# ==========================================

import os
import smtplib
import traceback
import requests
import random
import io
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from supabase import create_client
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF

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

def enviar_ticket_compra_html(destinatario, nombre_pieza, uuid_orden, precio_mxn):
    remitente = os.getenv("EMAIL_TALLER")
    password = os.getenv("EMAIL_PASSWORD")
    
    msg = MIMEMultipart()
    msg['From'] = f"AURA Alta Joyería <{remitente}>"
    msg['To'] = destinatario
    msg['Subject'] = f"Recibo de Inversión - Orden {uuid_orden[:8]}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500&family=Jost:wght@300;400&display=swap" rel="stylesheet">
    </head>
    <body style="font-family: 'Jost', sans-serif; background-color: #fafafa; padding: 30px 15px; margin: 0;">
        <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; padding: 40px; border: 1px solid #eeeeee;">
            <h1 style="font-family: 'Cormorant Garamond', serif; font-size: 24px; color: #111; letter-spacing: 4px; text-align: center; margin-bottom: 5px;">AURA</h1>
            <p style="text-align: center; font-size: 10px; letter-spacing: 2px; color: #999; text-transform: uppercase; border-bottom: 1px solid #eee; padding-bottom: 15px;">Recibo de Transaccion</p>
            
            <p style="font-size: 14px; color: #444; margin-top: 30px;">Estimado cliente,</p>
            <p style="font-size: 14px; color: #444; line-height: 1.5;">Hemos asegurado exitosamente su inversion en nuestra boveda central. A continuacion, los detalles de su transaccion:</p>
            
            <div style="background-color: #f9f9f9; padding: 20px; margin: 25px 0; border-radius: 4px;">
                <p style="margin: 0 0 10px 0; font-size: 13px; color: #333;"><strong>Pieza:</strong> {nombre_pieza}</p>
                <p style="margin: 0 0 10px 0; font-size: 13px; color: #333;"><strong>Folio de Orden:</strong> {uuid_orden}</p>
                <p style="margin: 0 0 10px 0; font-size: 13px; color: #333;"><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                <hr style="border: 0; border-top: 1px solid #ddd; margin: 15px 0;">
                <p style="margin: 0; font-size: 15px; color: #111; text-align: right;"><strong>Total: ${precio_mxn} MXN</strong></p>
            </div>
            
            <p style="font-size: 12px; color: #777; text-align: center; margin-top: 40px;">En breve recibira un segundo correo con el Certificado de Autenticidad de su pieza.</p>
        </div>
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
        print(f"❌ [SMTP ERROR - TICKET]: {str(e)}")
        return False

def enviar_certificado_html(destinatario, nombre_pieza, uuid_orden):
    remitente = os.getenv("EMAIL_TALLER")
    password = os.getenv("EMAIL_PASSWORD")
    
    msg = MIMEMultipart()
    msg['From'] = f"AURA Alta Joyería <{remitente}>"
    msg['To'] = destinatario
    msg['Subject'] = f"💎 Certificado de Autenticidad: {nombre_pieza}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500&family=Jost:wght@300;400&display=swap" rel="stylesheet">
    </head>
    <body style="font-family: 'Jost', sans-serif; background-color: #f4f4f4; padding: 40px 20px; text-align: center; margin: 0;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 50px 40px; border: 1px solid #eaeaea; box-shadow: 0 10px 30px rgba(0,0,0,0.05);">
            
            <h1 style="font-family: 'Cormorant Garamond', serif; font-size: 36px; color: #222; letter-spacing: 6px; margin-bottom: 5px;">AURA</h1>
            <p style="font-size: 11px; letter-spacing: 3px; color: #888; text-transform: uppercase; border-bottom: 1px solid #b76e79; padding-bottom: 20px; margin-top: 0;">
                Alta Joyeria • Certificado de Propiedad
            </p>
            
            <p style="margin-top: 40px; font-size: 15px; color: #555; font-weight: 300;">Extendemos el presente documento para certificar la autenticidad y propiedad de la pieza:</p>
            <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 28px; color: #b76e79; margin: 25px 0; font-style: italic;">{nombre_pieza}</h2>
            <p style="font-size: 14px; color: #555; font-weight: 300; line-height: 1.6;">Forjada con los mas altos estandares eticos y de calidad, garantizando la pureza de sus materiales. Esta pieza pertenece oficialmente a la coleccion privada de su portador.</p>
            
            <div style="margin-top: 40px; padding: 25px; background-color: #fcfcfc; border-left: 3px solid #b76e79; text-align: left;">
                <p style="margin: 5px 0; font-size: 13px; color: #333;"><strong>FOLIO DE REGISTRO EN BOVEDA:</strong> <br><span style="font-family: monospace; color: #777; font-size: 12px;">{uuid_orden}</span></p>
                <p style="margin: 15px 0 5px 0; font-size: 13px; color: #333;"><strong>FECHA DE EMISION:</strong> <br><span style="color: #555;">{datetime.now().strftime('%d/%m/%Y')}</span></p>
            </div>
            
            <p style="margin-top: 50px; font-size: 11px; color: #aaa; font-style: italic;">Este documento digital esta respaldado por los registros centrales del Atelier AURA.</p>
        </div>
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
        print(f"❌ [SMTP ERROR - CERTIFICADO]: {str(e)}")
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
            <h2>Autenticacion de Boveda AURA</h2>
            <p>Tu token de acceso de 6 digitos es:</p>
            <h1 style="letter-spacing: 5px; color: #5a2e3f;">{codigo}</h1>
            <p style="font-size: 0.8rem; color: #777;">Este token expirara en 15 minutos. Si no solicitaste este acceso, por favor ignora este mensaje.</p>
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
            return jsonify({"mensaje": "Este correo ya esta registrado. Por favor, inicia sesion."}), 409
            
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
            return jsonify({"mensaje": "El correo no esta registrado en nuestra boveda."}), 404
            
        usuario = res_usuario.data[0]
        
        if not check_password_hash(usuario['password_hash'], password):
            return jsonify({"mensaje": "Contrasena incorrecta."}), 401
            
        codigo = str(random.randint(100000, 999999))
        expiracion = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
        
        boveda.table('usuarios_vip').update({
            "codigo_acceso": codigo, 
            "expiracion_codigo": expiracion
        }).eq('email', email).execute()
        
        exito = enviar_codigo_email(email, codigo)
        return jsonify({"mensaje": "Credenciales correctas. Codigo 2FA enviado."}), 200
        
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

@app.route('/api/perfil-usuario', methods=['POST', 'OPTIONS'])
def perfil_usuario():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        email = request.json.get('email', '').strip().lower()
        
        res_user = boveda.table('usuarios_vip').select('id, usuario, telefono').eq('email', email).execute()
        
        if not res_user.data:
            return jsonify({"mensaje": "Usuario no encontrado"}), 404
            
        user_data = res_user.data[0]
        usuario_id = user_data['id']
        
        res_pedidos = boveda.table('ordenes_compra').select('id, estado, fecha_creacion, joya_id').eq('usuario_id', usuario_id).order('fecha_creacion', desc=True).execute()
        
        historial = []
        if res_pedidos.data:
            for pedido in res_pedidos.data:
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
            return jsonify({"mensaje": "El carrito esta vacio"}), 400

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

        res_orden = boveda.table('ordenes_compra').insert({
            'usuario_email': email,
            'usuario_id': usuario_uuid,
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
        
        # Disparamos ambos correos de forma independiente
        exito_ticket = enviar_ticket_compra_html(email_cliente, nombre_joya, uuid_orden, precio_formateado)
        exito_cert = enviar_certificado_html(email_cliente, nombre_joya, uuid_orden)
        
        exito_total = exito_ticket and exito_cert
        
        return jsonify({"estatus": "CONFIRMADO", "correo_enviado": exito_total}), 200
        
    except Exception:
        print(f"❌ [CONFIRMAR ERROR]: {traceback.format_exc()}")
        return jsonify({"mensaje": "Error interno"}), 500

# ==========================================
# NUEVO: GENERADOR DE CERTIFICADOS PDF
# ==========================================

@app.route('/api/descargar-certificado/<orden_uuid>', methods=['GET'])
def descargar_certificado(orden_uuid):
    try:
        # 1. Buscar los detalles de la orden
        res = boveda.table('ordenes_compra').select('joya_id, fecha_creacion, monto_total_centavos').eq('id', orden_uuid).execute()
        if not res.data:
            return jsonify({"mensaje": "Orden no encontrada"}), 404
            
        orden = res.data[0]
        
        # 2. Buscar el nombre de la joya
        res_joya = boveda.table('joyas_stock').select('nombre').eq('id', orden['joya_id']).execute()
        nombre_joya = res_joya.data[0]['nombre'] if res_joya.data else "Joya AURA"
        precio_formateado = f"{(orden['monto_total_centavos'] / 100.0):,.2f}"

        # 3. Construir el PDF
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        
        # Cabecera
        pdf.set_font('helvetica', 'B', 24)
        pdf.cell(0, 20, 'AURA', ln=True, align='C')
        
        pdf.set_font('helvetica', 'I', 10)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, 'CERTIFICADO DE AUTENTICIDAD Y PROPIEDAD', ln=True, align='C')
        pdf.line(20, 45, 190, 45) # Linea divisoria
        
        # Cuerpo
        pdf.ln(20)
        pdf.set_font('helvetica', '', 12)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 10, 'Se certifica la adquisicion de la pieza:', ln=True, align='C')
        
        pdf.ln(10)
        pdf.set_font('helvetica', 'B', 20)
        pdf.set_text_color(183, 110, 121) # Oro rosa cenizo
        pdf.cell(0, 10, nombre_joya, ln=True, align='C')
        
        # Detalles
        pdf.ln(20)
        pdf.set_font('helvetica', '', 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 8, f"Folio de Boveda: {orden_uuid}", ln=True, align='L')
        pdf.cell(0, 8, f"Fecha de Adquisicion: {orden['fecha_creacion'][:10]}", ln=True, align='L')
        pdf.cell(0, 8, f"Inversion: ${precio_formateado} MXN", ln=True, align='L')
        
        # Pie
        pdf.ln(30)
        pdf.set_font('helvetica', 'I', 9)
        pdf.set_text_color(150, 150, 150)
        pdf.multi_cell(0, 5, 'Esta pieza ha sido forjada en nuestro Atelier siguiendo los mas estrictos controles de calidad, garantizando la pureza de sus materiales y el origen etico de sus gemas.', align='C')

        # CORRECCIÓN AQUÍ: Obtener el bytearray de fpdf2 directamente
        pdf_bytes = bytes(pdf.output())
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Certificado_AURA_{orden_uuid[:8]}.pdf'
        )

    except Exception as e:
        print(f"❌ [ERROR PDF]: {traceback.format_exc()}")
        return jsonify({"mensaje": "Error al generar certificado"}), 500
