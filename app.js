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
       3. RECEPTOR DE ADUANA (Retorno de PayPal)
       ========================================================= */
    const parametrosURL = new URLSearchParams(window.location.search);
    if (parametrosURL.get('transaccion') === 'aprobada') {
        window.history.replaceState({}, document.title, window.location.pathname);
        alert("💎 ¡PAGO APROBADO POR VISA/MASTERCARD!\n\nTu orden ha sido capturada en firme por la bóveda. El taller ha iniciado el proceso de forjado de tu pieza.");
    } else if (parametrosURL.get('transaccion') === 'cancelada') {
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
        boton.innerText = "Consultando a la Bóveda...";
        boton.disabled = true;
    }

    const cargaUtil = {
        email: emailCliente.trim(),
        joya_id: idJoya
    };

    try {
        const respuesta = await fetch('https://joyeria-aura.onrender.com/api/reservar-pieza', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cargaUtil)
        });

        // ====================================================================
        // EL ESTETOSCOPIO: Capturamos la verdad cruda antes de que Chrome explote
        // ====================================================================
        const estatusHTTP = respuesta.status;
        const textoCrudo = await respuesta.text(); 

        console.log(`[DIAGNÓSTICO] Código de estatus devuelto por Render: ${estatusHTTP}`);
        console.log(`[DIAGNÓSTICO] Respuesta cruda del servidor: "${textoCrudo}"`);

        if (!textoCrudo || textoCrudo.trim() === "") {
            throw new Error(`El servidor respondió con código ${estatusHTTP}, pero el mensaje vino 100% vacío. Python se estrelló por dentro.`);
        }

        const datos = JSON.parse(textoCrudo);

        if (estatusHTTP === 200) {
            alert(`¡Éxito! Pieza reservada.\nUUID: ${datos.orden_uuid}\n\nAbriendo pasarela...`);
            window.location.href = datos.url_pasarela; 
        } else {
            alert(`Aviso de Bóveda: ${datos.mensaje || 'Transacción rechazada'}`);
            if (boton) { boton.innerText = "Completar el Pedido"; boton.disabled = false; }
        }

    } catch (error) {
        console.error("Resultado del análisis forense:", error);
        alert(`Fallo de transmisión: ${error.message}`);
        if (boton) { boton.innerText = "Completar el Pedido"; boton.disabled = false; }
    }
}
