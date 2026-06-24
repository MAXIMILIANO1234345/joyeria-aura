document.addEventListener('DOMContentLoaded', () => {

    /* =========================================================
       1. SCROLL REVEAL (Galería)
       ========================================================= */
    const reveals = document.querySelectorAll('.reveal');
    
    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                // [AGREGADO PRO]: Desconectar el observador una vez revelado
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
        let ticking = false; // Candado para el motor de frames

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

                    ticking = false; // Liberar el candado
                });

                ticking = true; // Bloquear hasta el siguiente frame
            }
        }, { passive: true }); // [AGREGADO PRO]: Alerta de scroll fluido
    }

});

// Esta función se comunicará con Python en el puerto 5000
async function procesarPedido(idJoya) {
    const emailCliente = prompt("Para registrar el certificado de la pieza, ingresa tu correo electrónico:");
    if (!emailCliente) return;

    const boton = document.querySelector('.btn-checkout');
    boton.innerText = "Asegurando pieza en bóveda...";
    boton.disabled = true;

    const cargaUtil = {
        email: emailCliente.trim(),
        joya_id: idJoya
    };

    try {
        // Invocamos la ruta POST de Flask[cite: 3]
        const respuesta = await fetch('http://localhost:5000/api/reservar-pieza', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cargaUtil)
        });

        const datos = await respuesta.json();

        if (respuesta.status === 200) {
            alert(`¡Éxito! Pieza reservada con el UUID:\n${datos.orden_uuid}\n\nAbriendo pasarela segura...`);
            // Te redirige al sandbox de PayPal con el token generado por Python[cite: 3]
            window.location.href = datos.url_pasarela; 
        } else if (respuesta.status === 409) {
            // Si el procedimiento almacenado arrojó un rollback porque la pieza fue adquirida por otro coleccionista[cite: 3]
            alert(`Lo sentimos: ${datos.mensaje}`);
            boton.innerText = "Completar el Pedido";
            boton.disabled = false;
        } else {
            alert(`Error de transacción: ${datos.mensaje}`);
            boton.innerText = "Completar el Pedido";
            boton.disabled = false;
        }
    } catch (error) {
        console.error("El backend no responde:", error);
        alert("No se pudo contactar con el taller central. Verifica que Flask esté corriendo.");
        boton.innerText = "Completar el Pedido";
        boton.disabled = false;
    }
}