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
        boton.innerText = "Asegurando pieza en bóveda...";
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

        const datos = await respuesta.json();

        if (respuesta.status === 200) {
            alert(`¡Éxito! Pieza reservada con el UUID:\n${datos.orden_uuid}\n\nAbriendo pasarela segura...`);
            window.location.href = datos.url_pasarela; 
        } else if (respuesta.status === 409) {
            alert(`Lo sentimos: ${datos.mensaje}`);
            if (boton) {
                boton.innerText = "Completar el Pedido";
                boton.disabled = false;
            }
        } else {
            alert(`Error de transacción: ${datos.mensaje}`);
            if (boton) {
                boton.innerText = "Completar el Pedido";
                boton.disabled = false;
            }
        }
    } catch (error) {
        console.error("El backend no responde:", error);
        alert("No se pudo contactar con el taller central. Verifica que el servidor de Render esté encendido.");
        if (boton) {
            boton.innerText = "Completar el Pedido";
            boton.disabled = false;
        }
    }
}
