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
async function procesarPedido(idJoya) {
    const emailCliente = prompt("Para registrar el certificado de la pieza, ingresa tu correo electrónico:");
    if (!emailCliente) return;

    const boton = document.querySelector('.btn-checkout');
    if (boton) {
        boton.innerText = "Asegurando pieza en bóveda...";
        boton.disabled = true;
    }

    const cargaUtil = {
        email: emailCliente.trim(),
        joya_id: idJoya
    };

    try {
        const respuesta = await fetch('https://joyeria-aura-42ax.onrender.com/api/reservar-pieza', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cargaUtil)
        });

        const datos = await respuesta.json();

        if (respuesta.status === 200) {
            alert(`¡Éxito! Pieza reservada con el UUID:\n${datos.orden_uuid}\n\nAbriendo pasarela segura...`);
            window.location.href = datos.url_pasarela; 
        } else {
            alert(`Aviso de Bóveda: ${datos.mensaje || 'Transacción rechazada'}`);
            if (boton) { boton.innerText = "Completar el Pedido"; boton.disabled = false; }
        }
    } catch (error) {
        console.error("El backend no responde:", error);
        alert("No se pudo contactar con el taller central. Verifica que tu conexión sea estable.");
        if (boton) { boton.innerText = "Completar el Pedido"; boton.disabled = false; }
    }
}
