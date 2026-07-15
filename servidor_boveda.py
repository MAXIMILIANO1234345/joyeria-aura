# ==========================================
# @author: Maximiliano Cabello
# Proyecto: AURA Alta Joyería - Servidor Central (Stripe Producción)
# ==========================================

import os
import smtplib
import traceback
import random
import io
import stripe
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
CORS(app)

# Configuración de Supabase y Stripe
boveda = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SECRET_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# ==========================================
# MOTORES DE CORREO (SMTP)
# ==========================================

def enviar_ticket_compra_html(destinatario, nombre_pieza, uuid_orden, precio_mxn):
    remitente = os.getenv("EMAIL_TALLER")
    password = os.getenv("EMAIL_PASSWORD")
    
    msg = MIMEMultipart()
    msg['From'] = f"AURA Alta Joyería <{remitente}>"
    msg['To'] = destinatario
    msg['Subject'] = f"Recibo de Inversión - Orden {str(uuid_orden)[:8]}"
    
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
        
        enviar_codigo_email(email, codigo)
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
        
        enviar_codigo_email(email, codigo)
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
# PASARELA DE PAGO: STRIPE (WHITE-LABEL & TOKENIZADO)
# ==========================================

@app.route('/api/procesar-pago-seguro', methods=['POST', 'OPTIONS'])
def procesar_pago_seguro():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        data = request.json
        email = data.get('email')
        items = data.get('items', [])
        token_stripe = data.get('token')

        if not items or not token_stripe:
            return jsonify({"mensaje": "Datos de compra incompletos"}), 400

        res_user = boveda.table('usuarios_vip').select('id').eq('email', email).execute()
        usuario_uuid = res_user.data[0]['id'] if res_user.data else None

        monto_total_centavos = 0
        cantidad_total = 0
        
        for item in items:
            joya_id = int(item.get('joya_id'))
            cantidad = int(item.get('cantidad', 1))
            
            res_joya = boveda.table('joyas_stock').select('precio_centavos').eq('id', joya_id).execute()
            if res_joya.data:
                # --- PARCHE DE PRECIO APLICADO AQUÍ ---
                # Esto transforma los "15" pesos de Supabase en "1500" centavos para Stripe automáticamente
                precio_base_db = float(res_joya.data[0]['precio_centavos'])
                monto_total_centavos += int(precio_base_db * 100 * cantidad)
                cantidad_total += cantidad

        # Seguridad de la Pasarela: Evitar que se envíen menos de 10 pesos
        if monto_total_centavos < 1000:
             return jsonify({"mensaje": "Por seguridad bancaria, la inversión mínima es de $10.00 MXN."}), 400

        primer_joya_id = int(items[0]['joya_id'])

        cargo = stripe.Charge.create(
            amount=monto_total_centavos,
            currency="mxn",
            source=token_stripe,
            description=f"Inversión AURA - Usuario: {email}"
        )

        res_orden = boveda.table('ordenes_compra').insert({
            'usuario_email': email,
            'usuario_id': usuario_uuid,
            'joya_id': primer_joya_id, 
            'cantidad': cantidad_total,
            'monto_total_centavos': monto_total_centavos,
            'estado': 'PAGADO', 
            'stripe_charge_id': cargo.id
        }).execute()
        
        orden_uuid = res_orden.data[0]['id']

        res_joya = boveda.table('joyas_stock').select('nombre').eq('id', primer_joya_id).execute()
        nombre_joya = res_joya.data[0]['nombre']
        precio_formateado = f"{(monto_total_centavos / 100.0):,.2f}"

        enviar_ticket_compra_html(email, nombre_joya, orden_uuid, precio_formateado)
        enviar_certificado_html(email, nombre_joya, orden_uuid)

        return jsonify({
            "estatus": "CONFIRMADO", 
            "orden_uuid": orden_uuid,
            "mensaje": "Transacción exitosa. Revisar bandeja de entrada."
        }), 200

    except stripe.error.CardError as e:
        return jsonify({"mensaje": "La tarjeta fue declinada.", "detalle": str(e)}), 402
    except stripe.error.StripeError as e:
        return jsonify({"mensaje": "Error en la pasarela de pagos.", "detalle": str(e)}), 400
    except Exception as e:
        print(f"❌ [ERROR PROCESAR PAGO]: {traceback.format_exc()}")
        return jsonify({"mensaje": "Error interno en el procesamiento"}), 500


@app.route('/api/webhook/stripe', methods=['POST'])
def webhook_stripe():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return jsonify({"error": "Payload invalido"}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({"error": "Firma invalida"}), 400

    if event['type'] == 'charge.succeeded':
        charge = event['data']['object']
        print(f"✅ [WEBHOOK AUDIT]: Cargo {charge['id']} verificado exitosamente.")
        
    elif event['type'] == 'charge.refunded':
        charge = event['data']['object']
        boveda.table('ordenes_compra').update({"estado": "REEMBOLSADO"}).eq('stripe_charge_id', charge['id']).execute()
        print(f"⚠️ [WEBHOOK AUDIT]: Cargo {charge['id']} reembolsado.")

    return jsonify({"status": "success"}), 200

# ==========================================
# GENERADOR DE CERTIFICADOS PDF
# ==========================================

@app.route('/api/descargar-certificado/<orden_uuid>', methods=['GET'])
def descargar_certificado(orden_uuid):
    try:
        res = boveda.table('ordenes_compra').select('joya_id, fecha_creacion, monto_total_centavos').eq('id', orden_uuid).execute()
        if not res.data:
            return jsonify({"mensaje": "Orden no encontrada"}), 404
            
        orden = res.data[0]
        
        res_joya = boveda.table('joyas_stock').select('nombre').eq('id', orden['joya_id']).execute()
        nombre_joya = res_joya.data[0]['nombre'] if res_joya.data else "Joya AURA"
        precio_formateado = f"{(orden['monto_total_centavos'] / 100.0):,.2f}"

        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        
        # Cabecera
        pdf.set_font('helvetica', 'B', 24)
        pdf.cell(0, 20, 'AURA', ln=True, align='C')
        
        pdf.set_font('helvetica', 'I', 10)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, 'CERTIFICADO DE AUTENTICIDAD Y PROPIEDAD', ln=True, align='C')
        pdf.line(20, 45, 190, 45)
        
        # Cuerpo
        pdf.ln(20)
        pdf.set_font('helvetica', '', 12)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 10, 'Se certifica la adquisicion de la pieza:', ln=True, align='C')
        
        pdf.ln(10)
        pdf.set_font('helvetica', 'B', 20)
        pdf.set_text_color(183, 110, 121) 
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

        pdf_bytes = bytes(pdf.output())
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Certificado_AURA_{str(orden_uuid)[:8]}.pdf'
        )

    except Exception as e:
        print(f"❌ [ERROR PDF]: {traceback.format_exc()}")
        return jsonify({"mensaje": "Error al generar certificado"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)