document.addEventListener('DOMContentLoaded', () => {

    /* =========================================================
       1. SCROLL REVEAL (Galería)
       ========================================================= */
    const reveals = document.querySelectorAll('.reveal');
    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                observer.unobserve(entry.target); 
            }
        });
    }, { threshold: 0.15, rootMargin: "0px 0px -50px 0px" });

    reveals.forEach(reveal => revealObserver.observe(reveal));


    /* =========================================================
       2. STICKY SCROLL IRIS (Atelier)
       ========================================================= */
    const irisWrapper = document.querySelector('.iris-scroll-wrapper');
    const irisMask = document.querySelector('.iris-mask');

    if (irisWrapper && irisMask) {
        let ticking = false;
        window.addEventListener('scroll', () => {
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    const rect = irisWrapper.getBoundingClientRect();
                    let progress = 0;
                    
                    if (rect.top <= 0) {
                        progress = Math.abs(rect.top) / (rect.height - window.innerHeight);
                    }
                    
                    progress = Math.max(0, Math.min(1, progress));

                    if (progress > 0 && progress < 1) {
                        irisMask.classList.add('is-opening');
                    } else {
                        irisMask.classList.remove('is-opening');
                    }

                    const circleSize = progress * 150; 
                    irisMask.style.clipPath = `circle(${circleSize}% at 50% 50%)`;
                    ticking = false;
                });
                ticking = true;
            }
        }, { passive: true });
    }


    /* =========================================================
       3. RECEPTOR DE ADUANA VIP (Disparo de Certificado)
       ========================================================= */
    const parametrosURL = new URLSearchParams(window.location.search);
    const estatusTransaccion = parametrosURL.get('transaccion');
    const ordenUuid = parametrosURL.get('orden_uuid');

    if (estatusTransaccion === 'aprobada' && ordenUuid) {
        // Limpiamos la URL para que no se vuelva a disparar si el cliente recarga la página
        window.history.replaceState({}, document.title, window.location.pathname);

        alert("💎 ¡PAGO APROBADO EN FIRME!\n\nTu inversión ha sido capturada por la Bóveda Central. Estamos forjando tu Certificado VIP de Propiedad y despachándolo al correo...");

        // Tocamos la puerta de Python para que dispare el correo de Gmail
        fetch('https://joyeria-aura-42ax.onrender.com/api/confirmar-compra', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ orden_uuid: ordenUuid })
        })
        .then(res => res.json())
        .then(data => {
            if (data.estatus === 'CONFIRMADO' && data.correo_enviado) {
                alert(`✉️ ¡CERTIFICADO DESPACHADO CON ÉXITO!\n\nSe ha enviado un documento con calidad editorial a la bandeja de: ${data.email}\n\n(Por favor verifica también tu buzón de correo no deseado / SPAM).\n\n¡Bienvenido al exclusivo círculo de coleccionistas de AURA!`);
            } else {
                alert("⚠️ El pago está asegurado, pero hubo una demora al entregar el correo. El taller central te contactará directamente.");
            }
        })
        .catch(err => {
            console.error("Error al certificar:", err);
            alert("Tu pago fue procesado correctamente por la bóveda, pero no pudimos emitir el recibo digital por correo.");
        });

    } else if (estatusTransaccion === 'cancelada') {
        alert("Transacción pausada. Tu pieza seguirá reservada en bóveda por los próximos 15 minutos.");
    }

});


/* =========================================================
   4. FUNCIÓN TRANSACCIONAL GLOBAL (Invocada por index.html)
   ========================================================= */
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
        # 1. Buscamos la orden en SQL
        res_orden = boveda.table('ordenes_compra').select('joya_id, email_cliente, estatus').eq('id', uuid_orden).execute()
        if not res_orden.data:
            return jsonify({"mensaje": "Orden no localizada en la bóveda"}), 404

        joya_id = res_orden.data[0]['joya_id']
        email_cliente = res_orden.data[0]['email_cliente']
        estatus_actual = res_orden.data[0].get('estatus', 'PENDIENTE')

        # SEGURO ANTI-METRALLETA: Si el cliente recarga la página web 5 veces, no le disparamos 5 correos
        if estatus_actual == 'PAGADO':
            return jsonify({
                "estatus": "YA_PROCESADO", 
                "mensaje": "El certificado de esta pieza ya había sido emitido previamente."
            }), 200

        # ====================================================================
        # MARTILLAZO SQL: Cambiamos oficialmente el estatus a 'PAGADO'
        # ====================================================================
        boveda.table('ordenes_compra').update({"estatus": "PAGADO"}).eq('id', uuid_orden).execute()

        # 2. Extraemos datos de la joya para la carta
        res_joya = boveda.table('joyas_stock').select('nombre, precio_centavos').eq('id', joya_id).execute()
        nombre_joya = res_joya.data[0]['nombre']
        precio_formateado = f"{(res_joya.data[0]['precio_centavos'] / 100.0):,.2f}"

        # 3. Disparamos el cañón de Gmail
        exito_mail = enviar_certificado_html(email_cliente, nombre_joya, uuid_orden, precio_formateado)

        return jsonify({
            "estatus": "CONFIRMADO",
            "email": email_cliente,
            "correo_enviado": exito_mail
        }), 200

    except Exception as e:
        print(f"❌ [FALLO SQL / SMTP]: {e}")
        return jsonify({"mensaje": "Error interno al estampar el certificado."}), 500
