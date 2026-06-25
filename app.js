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
        window.history.replaceState({}, document.title, window.location.pathname);

        alert("💎 ¡PAGO APROBADO EN FIRME!\n\nTu inversión ha sido capturada por la Bóveda Central. Estamos forjando tu Certificado VIP de Propiedad y despachándolo al correo...");

        fetch('https://joyeria-aura-42ax.onrender.com/api/confirmar-compra', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ orden_uuid: ordenUuid })
        })
        .then(res => res.json())
        .then(data => {
            if (data.estatus === 'CONFIRMADO' && data.correo_enviado) {
                alert("✉️ ¡CERTIFICADO DESPACHADO CON ÉXITO!\n\nSe ha enviado un documento con calidad editorial a la bandeja de: " + data.email + "\n\n(Por favor verifica también tu buzón de correo no deseado / SPAM).\n\n¡Bienvenido al exclusivo círculo de coleccionistas de AURA!");
            } else if (data.estatus === 'YA_PROCESADO') {
                alert("Aviso de Bóveda: " + data.mensaje);
            } else {
                alert("⚠️ El pago está asegurado, pero hubo una demora al entregar el correo. El taller central te contactará directamente.");
            }
        })
        .catch(err => {
            console.error("Error al certificar:", err);
            alert("Tu pago fue procesado correctamente por la bóveda, pero no pudimos emitir el recibo digital por correo.");
        });

    } else if (estatusTransaccion === 'cancelada') {
        alert("Transacción pausada. Tu selección seguirá reservada en bóveda por los próximos 15 minutos.");
    }

    // Inicializar la vista del carrito al cargar la página
    actualizarUI();
});


/* =========================================================
   4. SISTEMA DE CARRITO DE COMPRAS VIP (UI + Local Storage)
   ========================================================= */

// Diccionario de productos para que el frontend sepa qué mostrar
const catalogoJoyas = {
    1: { nombre: "Solitario Eternidad", precio: 24500, imagen: "https://images.unsplash.com/photo-1605100804763-247f67b2548e?q=80&w=200&auto=format&fit=crop" },
    2: { nombre: "Crossover Lumina", precio: 16800, imagen: "https://images.unsplash.com/photo-1611591437281-460bfbe1220a?q=80&w=200&auto=format&fit=crop" },
    3: { nombre: "Esencia Pura", precio: 3200, imagen: "https://images.unsplash.com/photo-1599643478524-fb66f7ca265b?q=80&w=200&auto=format&fit=crop" }
};

/* --- NUEVO SISTEMA DE AUTO-SANACIÓN DEL CARRITO --- */
// Leemos la memoria del navegador
let carritoCrudo = JSON.parse(localStorage.getItem('carritoAura')) || [];

// Filtramos cualquier pieza corrupta (por ejemplo, si el joya_id guardado viejo era un objeto en lugar de un número)
let carrito = carritoCrudo.filter(item => item.joya_id !== null && typeof item.joya_id !== 'object');

// Si se encontró basura y se limpió, guardamos el carrito limpio de vuelta para proteger el backend
if (carritoCrudo.length !== carrito.length) {
    localStorage.setItem('carritoAura', JSON.stringify(carrito));
    console.warn("AURA: Se detectó y limpió información obsoleta en el carrito de compras.");
}
/* -------------------------------------------------- */


// Actualizar la interfaz (Barra lateral, precios y contador)
function actualizarUI() {
    const contenedor = document.getElementById('contenedor-carrito');
    const totalElement = document.getElementById('total-carrito');
    const indicador = document.getElementById('cart-indicator');

    // Si está vacío
    if (carrito.length === 0) {
        contenedor.innerHTML = `
            <div class="text-center mt-5">
                <p class="text-muted font-serif" style="font-size: 1.2rem; font-style: italic;">Tu reserva está vacía.</p>
            </div>`;
        totalElement.innerText = "$ 0 MXN";
        indicador.style.display = 'none';
        return;
    }

    // Si tiene productos, construimos el HTML
    let htmlCarrito = '';
    let total = 0;
    let cantidadTotalPiezas = 0;

    carrito.forEach((item, index) => {
        const joya = catalogoJoyas[item.joya_id];
        if (joya) {
            const subtotal = joya.precio * item.cantidad;
            total += subtotal;
            cantidadTotalPiezas += item.cantidad;

            htmlCarrito += `
                <div class="cart-item d-flex align-items-center mb-4" style="border-bottom: 1px solid #eee; padding-bottom: 15px;">
                    <img src="${joya.imagen}" alt="${joya.nombre}" style="width: 70px; height: 70px; object-fit: cover; border-radius: 8px; margin-right: 15px;">
                    <div class="cart-item-details flex-grow-1">
                        <h6 class="cart-item-title font-serif mb-1" style="font-size: 1.1rem;">${joya.nombre}</h6>
                        <p class="mb-1 text-muted" style="font-size: 0.8rem;">Cantidad: ${item.cantidad}</p>
                        <p class="fw-medium mb-0" style="font-size: 0.9rem;">$ ${subtotal.toLocaleString()} MXN</p>
                    </div>
                    <button class="btn btn-sm" onclick="eliminarDelCarrito(${index})" style="background: none; border: none; color: var(--ciruela-oscuro); font-size: 1.2rem;">
                        <i class="bi bi-x-circle"></i>
                    </button>
                </div>
            `;
        }
    });

    // Inyectamos el HTML al menú lateral
    contenedor.innerHTML = htmlCarrito;
    totalElement.innerText = `$ ${total.toLocaleString()} MXN`;
    
    // Actualizamos el puntito rojo del icono
    indicador.innerText = cantidadTotalPiezas;
    indicador.style.display = 'flex';
    indicador.style.alignItems = 'center';
    indicador.style.justifyContent = 'center';
    indicador.style.fontSize = '9px';
    indicador.style.color = 'white';
}

// Función para agregar una joya al carrito
function agregarAlCarrito(idJoya, cantidad = 1) {
    const itemExistente = carrito.find(item => item.joya_id === idJoya);
    
    if (itemExistente) {
        itemExistente.cantidad += cantidad;
    } else {
        carrito.push({ joya_id: idJoya, cantidad: cantidad });
    }
    
    localStorage.setItem('carritoAura', JSON.stringify(carrito));
    
    // Actualizamos la vista
    actualizarUI();
    
    // Abrimos el menú lateral automáticamente para mostrarle al usuario que se agregó
    const cartOffcanvas = new bootstrap.Offcanvas(document.getElementById('cartDrawer'));
    cartOffcanvas.show();
}

// Función para eliminar un item específico del carrito
function eliminarDelCarrito(index) {
    carrito.splice(index, 1); // Quitamos el elemento del array
    localStorage.setItem('carritoAura', JSON.stringify(carrito)); // Guardamos en memoria
    actualizarUI(); // Refrescamos la vista
}

// Función para procesar TODO el carrito con el backend
async function procesarCheckoutCarrito() {
    if (carrito.length === 0) {
        alert("Tu selección está vacía. Explora nuestro Atelier primero para añadir piezas.");
        return;
    }

    const emailCliente = prompt("Para registrar el certificado de tus piezas, ingresa tu correo electrónico:");
    if (!emailCliente) return;

    const boton = document.querySelector('.btn-checkout');
    if (boton) {
        boton.innerText = "Asegurando colección...";
        boton.disabled = true;
    }

    const cargaUtil = {
        email: emailCliente.trim(),
        items: carrito
    };

    try {
        const respuesta = await fetch('https://joyeria-aura-42ax.onrender.com/api/reservar-carrito', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cargaUtil)
        });

        const datos = await respuesta.json();

        if (respuesta.status === 200) {
            // Ya no usamos alert, redirigimos directo a la pasarela
            localStorage.removeItem('carritoAura'); 
            carrito = []; 
            actualizarUI(); 
            window.location.href = datos.url_pasarela; 
        } else {
            alert("Aviso de Bóveda: " + (datos.mensaje || "Transacción rechazada"));
            if (boton) { boton.innerText = "Completar la Inversión"; boton.disabled = false; }
        }
    } catch (error) {
        console.error("El backend no responde:", error);
        alert("No se pudo contactar con el taller central. Verifica que tu conexión sea estable.");
        if (boton) { boton.innerText = "Completar la Inversión"; boton.disabled = false; }
    }
}
