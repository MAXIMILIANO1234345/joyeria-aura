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

const catalogoJoyas = {
    1: { nombre: "Solitario Eternidad", precio: 24500, imagen: "https://images.unsplash.com/photo-1605100804763-247f67b2548e?q=80&w=200&auto=format&fit=crop" },
    2: { nombre: "Crossover Lumina", precio: 16800, imagen: "https://images.unsplash.com/photo-1611591437281-460bfbe1220a?q=80&w=200&auto=format&fit=crop" },
    3: { nombre: "Esencia Pura", precio: 3200, imagen: "https://images.unsplash.com/photo-1599643478524-fb66f7ca265b?q=80&w=200&auto=format&fit=crop" }
};

// Auto-sanación del carrito
let carritoCrudo = JSON.parse(localStorage.getItem('carritoAura')) || [];
let carrito = carritoCrudo.filter(item => item.joya_id !== null && typeof item.joya_id !== 'object');

if (carritoCrudo.length !== carrito.length) {
    localStorage.setItem('carritoAura', JSON.stringify(carrito));
    console.warn("AURA: Se detectó y limpió información obsoleta en el carrito de compras.");
}

function actualizarUI() {
    const contenedor = document.getElementById('contenedor-carrito');
    const totalElement = document.getElementById('total-carrito');
    const indicador = document.getElementById('cart-indicator');

    if (carrito.length === 0) {
        contenedor.innerHTML = `
            <div class="text-center mt-5">
                <p class="text-muted font-serif" style="font-size: 1.2rem; font-style: italic;">Tu reserva está vacía.</p>
            </div>`;
        totalElement.innerText = "$ 0 MXN";
        indicador.style.display = 'none';
        return;
    }

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

    contenedor.innerHTML = htmlCarrito;
    totalElement.innerText = `$ ${total.toLocaleString()} MXN`;
    
    indicador.innerText = cantidadTotalPiezas;
    indicador.style.display = 'flex';
    indicador.style.alignItems = 'center';
    indicador.style.justifyContent = 'center';
    indicador.style.fontSize = '9px';
    indicador.style.color = 'white';
}

function agregarAlCarrito(idJoya, cantidad = 1) {
    const itemExistente = carrito.find(item => item.joya_id === idJoya);
    
    if (itemExistente) {
        itemExistente.cantidad += cantidad;
    } else {
        carrito.push({ joya_id: idJoya, cantidad: cantidad });
    }
    
    localStorage.setItem('carritoAura', JSON.stringify(carrito));
    actualizarUI();
    
    const cartOffcanvas = new bootstrap.Offcanvas(document.getElementById('cartDrawer'));
    cartOffcanvas.show();
}

function eliminarDelCarrito(index) {
    carrito.splice(index, 1);
    localStorage.setItem('carritoAura', JSON.stringify(carrito));
    actualizarUI(); 
}

// --- REGLA DE NEGOCIO: EXIGIR LOGIN PARA COMPRAR ---
async function procesarCheckoutCarrito() {
    if (carrito.length === 0) {
        alert("Tu selección está vacía. Explora nuestro Atelier primero para añadir piezas.");
        return;
    }

    const usuarioActivo = localStorage.getItem('auraVIP_User');
    if (!usuarioActivo) {
        alert("Atención: Por protocolos de seguridad de nuestra bóveda, es obligatorio iniciar sesión o crear una cuenta antes de procesar una inversión.");
        
        const cartElement = document.getElementById('cartDrawer');
        const cartOffcanvas = bootstrap.Offcanvas.getInstance(cartElement);
        if (cartOffcanvas) cartOffcanvas.hide();
        
        const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
        loginModal.show();
        return;
    }

    const boton = document.querySelector('.btn-checkout');
    if (boton) {
        boton.innerText = "Asegurando colección...";
        boton.disabled = true;
    }

    const cargaUtil = {
        email: usuarioActivo, 
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
        alert("No se pudo contactar con el taller central.");
        if (boton) { boton.innerText = "Completar la Inversión"; boton.disabled = false; }
    }
}


/* =========================================================
   5. SISTEMA DE AUTENTICACIÓN (Login / Registro + 2FA)
   ========================================================= */

let correoTemporal = ""; 

function mostrarSeccion(seccion) {
    const isLogin = seccion === 'login';
    document.getElementById('auth-login-form').style.display = isLogin ? 'block' : 'none';
    document.getElementById('auth-registro-form').style.display = isLogin ? 'none' : 'block';
    
    document.getElementById('tab-login').className = isLogin ? "btn btn-outline-dark mx-1 fw-bold" : "btn btn-outline-dark mx-1 text-muted border-0";
    document.getElementById('tab-registro').className = !isLogin ? "btn btn-outline-dark mx-1 fw-bold" : "btn btn-outline-dark mx-1 text-muted border-0";
    document.getElementById('auth-subtitle').innerText = isLogin ? "Accede a tu colección privada." : "Únete al círculo exclusivo de coleccionistas.";
}

async function procesarRegistro() {
    const usuario = document.getElementById('reg-usuario').value.trim();
    const telefono = document.getElementById('reg-telefono').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value.trim();
    const btn = document.getElementById('btn-registro');

    if (!usuario || !telefono || !email.includes('@') || password.length < 4) {
        alert("Por favor, llena todos los campos correctamente.");
        return;
    }

    btn.innerText = "Creando cuenta..."; 
    btn.disabled = true;

    try {
        const res = await fetch('https://joyeria-aura-42ax.onrender.com/api/crear-cuenta', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usuario, telefono, email, password })
        });
        const data = await res.json();

        if (res.status === 200) {
            correoTemporal = email;
            transicionA2FA("Hemos enviado un token de verificación a tu correo.");
        } else {
            alert("Aviso: " + data.mensaje);
        }
    } catch (error) {
        alert("Error de conexión.");
    } finally {
        btn.innerText = "Registrarse"; 
        btn.disabled = false;
    }
}

async function procesarLogin() {
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value.trim();
    const btn = document.getElementById('btn-login');

    if (!email.includes('@') || !password) {
        alert("Ingresa tu correo y contraseña.");
        return;
    }

    btn.innerText = "Verificando..."; 
    btn.disabled = true;

    try {
        const res = await fetch('https://joyeria-aura-42ax.onrender.com/api/iniciar-sesion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (res.status === 200) {
            correoTemporal = email;
            transicionA2FA("Seguridad de Bóveda: Ingresa el token enviado a tu correo para acceder.");
        } else {
            alert("Acceso denegado: " + data.mensaje);
        }
    } catch (error) {
        alert("Error de conexión.");
    } finally {
        btn.innerText = "Entrar"; 
        btn.disabled = false;
    }
}

function transicionA2FA(mensaje) {
    document.getElementById('auth-toggle-btns').style.display = 'none';
    document.getElementById('auth-login-form').style.display = 'none';
    document.getElementById('auth-registro-form').style.display = 'none';
    document.getElementById('auth-paso-2').style.display = 'block';
    document.getElementById('auth-subtitle').innerText = mensaje;
}

async function verificarCodigoAcceso() {
    const codigo = document.getElementById('auth-codigo-input').value.trim();
    const btn = document.getElementById('btn-verificar-codigo');

    if (codigo.length < 5) {
        alert("Ingresa el token completo.");
        return;
    }

    btn.innerText = "Validando..."; 
    btn.disabled = true;

    try {
        const res = await fetch('https://joyeria-aura-42ax.onrender.com/api/verificar-codigo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: correoTemporal, codigo })
        });
        const data = await res.json();

        if (res.status === 200) {
            localStorage.setItem('auraVIP_User', data.email); 
            
            const modalInstance = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
            if (modalInstance) {
                modalInstance.hide();
            }
            
            alert(`¡Autenticación exitosa!\nBienvenido a la bóveda, ${data.usuario || data.email}.`);
            reiniciarModalLogin();
            
            // Opcional: abrir automáticamente el perfil después de iniciar sesión
            gestionarAccesoPerfil();
        } else {
            alert("Error: " + data.mensaje);
        }
    } catch (error) {
        alert("Error de conexión.");
    } finally {
        btn.innerText = "Verificar Token"; 
        btn.disabled = false;
    }
}

function reiniciarModalLogin() {
    document.getElementById('auth-toggle-btns').style.display = 'flex';
    document.getElementById('auth-paso-2').style.display = 'none';
    mostrarSeccion('login'); 
    
    document.getElementById('auth-codigo-input').value = "";
    document.getElementById('login-email').value = "";
    document.getElementById('login-password').value = "";
    document.getElementById('reg-usuario').value = "";
    document.getElementById('reg-telefono').value = "";
    document.getElementById('reg-email').value = "";
    document.getElementById('reg-password').value = "";
    
    correoTemporal = "";
}


/* =========================================================
   6. MI BÓVEDA (Gestión del Panel de Perfil)
   ========================================================= */

// Función "Portero": decide si abre el modal de Login o el panel de Perfil
function gestionarAccesoPerfil() {
    const usuarioActivo = localStorage.getItem('auraVIP_User');
    
    if (!usuarioActivo) {
        // No hay sesión: Abrir Modal de Iniciar Sesión
        const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
        loginModal.show();
    } else {
        // Sí hay sesión: Abrir el Offcanvas de "Mi Bóveda"
        const profileOffcanvas = new bootstrap.Offcanvas(document.getElementById('profileDrawer'));
        profileOffcanvas.show();
        
        // Llamamos al backend para cargar los datos en vivo
        cargarDatosPerfil(usuarioActivo);
    }
}

// Función que pide a Python el nombre, teléfono e historial de compras del usuario
async function cargarDatosPerfil(emailUsuario) {
    // Ponemos estado de carga visualmente
    document.getElementById('perfil-email').innerText = emailUsuario;
    document.getElementById('perfil-nombre').innerText = "Cargando datos...";
    document.getElementById('perfil-telefono').innerText = "Cargando datos...";
    document.getElementById('perfil-pedidos-container').innerHTML = '<p class="text-muted" style="font-size: 0.9rem; font-style: italic;">Conectando con la bóveda central...</p>';

    try {
        // ATENCIÓN: Esta es la ruta que crearemos en Python en el siguiente paso
        const respuesta = await fetch('https://joyeria-aura-42ax.onrender.com/api/perfil-usuario', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: emailUsuario })
        });

        if (respuesta.status === 200) {
            const datos = await respuesta.json();
            
            // Llenar datos personales
            document.getElementById('perfil-nombre').innerText = datos.usuario || "Coleccionista VIP";
            document.getElementById('perfil-telefono').innerText = datos.telefono || "Teléfono no registrado";
            
            // Llenar el historial de compras
            const contenedorPedidos = document.getElementById('perfil-pedidos-container');
            
            if (datos.pedidos && datos.pedidos.length > 0) {
                let htmlPedidos = '';
                datos.pedidos.forEach(pedido => {
                    // Diseño elegante para cada pedido
                    htmlPedidos += `
                        <div class="mb-3 p-3" style="background-color: #fcfcfc; border-radius: 8px; border-left: 3px solid var(--oro-rosa-cenizo); box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
                            <p class="mb-1 fw-bold font-serif" style="font-size: 1rem;">${pedido.nombre_joya}</p>
                            <p class="mb-1 text-muted" style="font-size: 0.8rem;">Folio: ${pedido.id_orden.substring(0,8)}...</p>
                            <p class="mb-1 text-muted" style="font-size: 0.8rem;">Fecha: ${new Date(pedido.fecha).toLocaleDateString()}</p>
                            <span class="badge ${pedido.estado === 'PAGADO' ? 'bg-success' : 'bg-warning text-dark'}" style="font-size: 0.7rem; letter-spacing: 1px;">
                                ${pedido.estado === 'PAGADO' ? 'ASEGURADO' : 'PENDIENTE DE PAGO'}
                            </span>
                        </div>
                    `;
                });
                contenedorPedidos.innerHTML = htmlPedidos;
            } else {
                contenedorPedidos.innerHTML = '<p class="text-muted" style="font-size: 0.9rem; font-style: italic;">Aún no tienes piezas en tu bóveda.</p>';
            }
        } else {
            document.getElementById('perfil-nombre').innerText = "Error de conexión";
            document.getElementById('perfil-pedidos-container').innerHTML = '<p class="text-danger" style="font-size: 0.9rem;">No pudimos sincronizar tu perfil.</p>';
        }
    } catch (error) {
        console.error("Error al cargar perfil:", error);
        document.getElementById('perfil-nombre').innerText = "Modo Sin Conexión";
        document.getElementById('perfil-pedidos-container').innerHTML = '<p class="text-muted" style="font-size: 0.9rem;">Revisa tu conexión a internet.</p>';
    }
}

// Función para cerrar la sesión y borrar la memoria
function cerrarSesionVIP() {
    if(confirm("¿Estás seguro de que deseas cerrar tu bóveda?")) {
        localStorage.removeItem('auraVIP_User');
        
        // Cerrar el panel
        const profileElement = document.getElementById('profileDrawer');
        const profileOffcanvas = bootstrap.Offcanvas.getInstance(profileElement);
        if(profileOffcanvas) profileOffcanvas.hide();
        
        alert("Sesión cerrada correctamente. Hasta pronto.");
    }
}
