/* =========================================================
   0. MOTOR DE FÍSICAS CUSTOM PARA A-FRAME (Interacción VIP)
   ========================================================= */
if (typeof AFRAME !== 'undefined') {
    AFRAME.registerComponent('drag-rotate-component', {
        schema: { speed: { default: 1.5 } },
        init: function () {
            this.ifMouseDown = false;
            this.x_cord = 0;
            this.y_cord = 0;

            this.onMouseDown = this.onMouseDown.bind(this);
            this.onMouseUp = this.onMouseUp.bind(this);
            this.onMouseMove = this.onMouseMove.bind(this);

            this.el.sceneEl.addEventListener('loaded', () => {
                const canvas = this.el.sceneEl.canvas;
                canvas.addEventListener('mousedown', this.onMouseDown);
                canvas.addEventListener('mouseup', this.onMouseUp);
                canvas.addEventListener('mousemove', this.onMouseMove);
                canvas.addEventListener('mouseleave', this.onMouseUp);

                canvas.addEventListener('touchstart', this.onMouseDown, {passive: false});
                canvas.addEventListener('touchend', this.onMouseUp);
                canvas.addEventListener('touchmove', this.onMouseMove, {passive: false});
            });
        },
        onMouseDown: function (event) {
            this.ifMouseDown = true;
            this.x_cord = event.clientX || (event.touches ? event.touches[0].clientX : 0);
            this.y_cord = event.clientY || (event.touches ? event.touches[0].clientY : 0);
        },
        onMouseUp: function () {
            this.ifMouseDown = false;
        },
        onMouseMove: function (event) {
            if (this.ifMouseDown) {
                let temp_x = event.clientX || (event.touches ? event.touches[0].clientX : 0);
                let temp_y = event.clientY || (event.touches ? event.touches[0].clientY : 0);
                let x_temp = temp_x - this.x_cord;
                let y_temp = temp_y - this.y_cord;

                this.el.object3D.rotation.y += x_temp * this.data.speed / 100;
                this.el.object3D.rotation.x += y_temp * this.data.speed / 100;

                this.x_cord = temp_x;
                this.y_cord = temp_y;
            }
        }
    });
}


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
       2. STICKY SCROLL IRIS OPTIMIZADO
       ========================================================= */
    const irisWrapper = document.querySelector('.iris-scroll-wrapper');
    const irisMask = document.querySelector('.iris-mask');

    if (irisWrapper && irisMask) {
        let ticking = false;

        const handleIrisScroll = () => {
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
        };

        const irisIntersectionObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                window.addEventListener('scroll', handleIrisScroll, { passive: true });
            } else {
                window.removeEventListener('scroll', handleIrisScroll);
            }
        });

        irisIntersectionObserver.observe(irisWrapper);
    }


    /* =========================================================
       3. RECEPTOR DE ADUANA VIP (PAYPAL / BACKEND)
       ========================================================= */
    const parametrosURL = new URLSearchParams(window.location.search);
    const estatusTransaccion = parametrosURL.get('transaccion');
    const ordenUuid = parametrosURL.get('orden_uuid');

    if (estatusTransaccion === 'aprobada' && ordenUuid) {
        window.history.replaceState({}, document.title, window.location.pathname);

        mostrarAlertaVIP(
            "Inversión Asegurada", 
            "Tu adquisición ha sido capturada por la Bóveda Central. Estamos generando tu Recibo de Transacción y tu Certificado de Autenticidad...",
            "bi-shield-check"
        );

        fetch('https://joyeria-aura-42ax.onrender.com/api/confirmar-compra', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ orden_uuid: ordenUuid })
        })
        .then(res => res.json())
        .then(data => {
            if (data.estatus === 'CONFIRMADO' && data.correo_enviado) {
                setTimeout(() => {
                    mostrarToastVIP(`✉️ Recibo y Certificado digital despachados a tu correo electrónico.`);
                }, 3000); 
            } else if (data.estatus === 'YA_PROCESADO') {
                mostrarToastVIP("Aviso: " + data.mensaje);
            } else {
                mostrarToastVIP("⚠️ El pago está asegurado, pero hubo una demora al entregar los documentos digitales.");
            }
        })
        .catch(err => {
            console.error("Error al certificar:", err);
            mostrarToastVIP("Tu pago fue procesado, pero no pudimos emitir los recibos digitales.");
        });

    } else if (estatusTransaccion === 'cancelada') {
        mostrarToastVIP("Transacción pausada. Tu selección seguirá reservada en bóveda.");
    }

    actualizarUI();
    
    // Disparar modal de bienvenida si no se ha mostrado
    if (!localStorage.getItem("welcomeModalShown")) {
        const welcomeModal = new bootstrap.Modal(document.getElementById('welcomeGuideModal'));
        welcomeModal.show();
        localStorage.setItem("welcomeModalShown", "true");
    }
});


/* =========================================================
   4. CONTROLADORES DE ALERTAS Y TOASTS
   ========================================================= */
function mostrarAlertaVIP(titulo, mensaje, icono = 'bi-gem') {
    document.getElementById('aura-alert-title').innerText = titulo;
    document.getElementById('aura-alert-message').innerText = mensaje;
    
    const iconElement = document.getElementById('aura-alert-icon');
    iconElement.className = `bi ${icono} mb-2 mt-3`;
    iconElement.style.fontSize = '2.5rem';
    iconElement.style.color = 'var(--oro-rosa-cenizo)';

    const alertModal = new bootstrap.Modal(document.getElementById('auraAlertModal'));
    alertModal.show();
}

function mostrarToastVIP(mensaje) {
    document.getElementById('aura-toast-message').innerText = mensaje;
    const toastEl = document.getElementById('auraToast');
    const toast = new bootstrap.Toast(toastEl, { delay: 4500 });
    toast.show();
}


/* =========================================================
   5. CATÁLOGO COMPLETO Y SISTEMA DE CARRITO DE COMPRAS VIP
   ========================================================= */
const catalogoJoyas = {
    // Anillos
    1: { nombre: "Solitario Eternidad", precio: 24500, imagen: "oro1.png" },
    2: { nombre: "Crossover Lumina", precio: 16800, imagen: "anillo mariposa.png" },
    3: { nombre: "Esencia Pura", precio: 3200, imagen: "puma1.png" },
    4: { nombre: "Mariposa Cristal", precio: 12400, imagen: "anillo_4_render_1.jpg" },
    5: { nombre: "Aura Imperial", precio: 35000, imagen: "anillo_5_render_1.jpg" },
    6: { nombre: "Zafiro Noche", precio: 28900, imagen: "anillo_6_render_1.jpg" },
    7: { nombre: "Alianza Platino", precio: 19500, imagen: "anillo_7_render_1.jpg" },
    8: { nombre: "Rosa Eterna", precio: 21000, imagen: "anillo_8_render_1.jpg" },
    
    // Collares
    9: { nombre: "Gargantilla Zafiro", precio: 45000, imagen: "collar_1_render_1.jpg" },
    10: { nombre: "Colgante Lágrima", precio: 32500, imagen: "collar_2_render_1.jpg" },
    11: { nombre: "Cadena Veneciana Oro", precio: 18900, imagen: "collar_3_render_1.jpg" },
    12: { nombre: "Perla de Tahití", precio: 27000, imagen: "collar_4_render_1.jpg" },
    13: { nombre: "Cruz de Diamantes", precio: 55000, imagen: "collar_5_render_1.jpg" },
    14: { nombre: "Constelación", precio: 89000, imagen: "collar_6_render_1.jpg" },
    
    // Pulseras
    15: { nombre: "Brazalete Infinito", precio: 22000, imagen: "pulsera_1_render_1.jpg" },
    16: { nombre: "Pulsera Riviera (Tenis)", precio: 115000, imagen: "pulsera_2_render_1.jpg" },
    17: { nombre: "Esclava Oro 18k", precio: 19400, imagen: "pulsera_3_render_1.jpg" },
    18: { nombre: "Brazalete Felino", precio: 43000, imagen: "pulsera_4_render_1.jpg" },
    19: { nombre: "Pulsera Charms AURA", precio: 14000, imagen: "pulsera_5_render_1.jpg" },
    20: { nombre: "Malla de Oro Rosa", precio: 26800, imagen: "pulsera_6_render_1.jpg" }
};

let carritoCrudo = JSON.parse(localStorage.getItem('carritoAura')) || [];
let carrito = carritoCrudo.filter(item => item.joya_id !== null && typeof item.joya_id !== 'object');

function actualizarUI() {
    const contenedor = document.getElementById('contenedor-carrito');
    const totalElement = document.getElementById('total-carrito');
    const indicador = document.getElementById('cart-indicator');

    if (carrito.length === 0) {
        contenedor.innerHTML = `<div class="text-center mt-5"><p class="text-muted font-serif" style="font-size: 1.2rem; font-style: italic;">Tu reserva está vacía.</p></div>`;
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
                    <img src="${joya.imagen}" alt="${joya.nombre}" loading="lazy" style="width: 70px; height: 70px; object-fit: cover; border-radius: 8px; margin-right: 15px;">
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
    // REGLA DE BÓVEDA: Solo permitir procesar una pieza a la vez (evita corromper la BD)
    if (carrito.length > 0 && carrito[0].joya_id !== idJoya) {
        mostrarToastVIP("Por protocolos de seguridad en tu certificado, procesa la compra de una pieza a la vez. Vacía tu bolsa primero.");
        return;
    }
    
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
    
    mostrarToastVIP("💎 Pieza añadida a tu selección.");
}

function eliminarDelCarrito(index) {
    carrito.splice(index, 1);
    localStorage.setItem('carritoAura', JSON.stringify(carrito));
    actualizarUI(); 
}

async function procesarCheckoutCarrito() {
    if (carrito.length === 0) {
        mostrarToastVIP("Tu selección está vacía. Explora nuestro Atelier primero.");
        return;
    }

    const usuarioActivo = localStorage.getItem('auraVIP_User');
    if (!usuarioActivo) {
        mostrarAlertaVIP(
            "Autenticación Requerida", 
            "Por protocolos de seguridad, es obligatorio iniciar sesión en nuestra bóveda antes de procesar una inversión.",
            "bi-shield-lock"
        );
        
        const cartElement = document.getElementById('cartDrawer');
        const cartOffcanvas = bootstrap.Offcanvas.getInstance(cartElement);
        if (cartOffcanvas) cartOffcanvas.hide();
        
        setTimeout(() => {
            const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
            loginModal.show();
        }, 500);
        return;
    }

    const boton = document.querySelector('.btn-checkout');
    if (boton) {
        boton.innerText = "Asegurando colección...";
        boton.disabled = true;
    }

    try {
       // Reemplaza el fetch viejo hacia /api/reservar-carrito por este:
const respuesta = await fetch('https://joyeria-aura-42ax.onrender.com/api/procesar-pago-seguro', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        email: emailUsuario, // El email del cliente
        items: carritoActual, // El array con los IDs de las joyas
        token: tokenGeneradoPorPasarela // El token seguro (ej. de Stripe)
    })
});

const resultado = await respuesta.json();

if (respuesta.ok) {
    console.log("Transacción exitosa, UUID:", resultado.orden_uuid);
    // Redirigir a pantalla de éxito o limpiar carrito
} else {
    console.error("Error en el pago:", resultado.mensaje);
}
}


/* =========================================================
   6. VISOR 3D (Renderizado desde el HTML)
   ========================================================= */
function abrirModelo3D(modeloGlb) {
    const contenedor = document.getElementById('contenedorEscena3D');
    
    // Inyecta dinámicamente la escena A-Frame para no saturar la memoria desde el inicio
    contenedor.innerHTML = `
        <a-scene embedded vr-mode-ui="enabled: false" background="color: #f4f4f4">
            <a-assets>
                <a-asset-item id="modeloJoya" src="${modeloGlb}"></a-asset-item>
            </a-assets>
            
            <a-entity gltf-model="#modeloJoya" 
                      position="0 0 -3" 
                      scale="1.5 1.5 1.5" 
                      drag-rotate-component>
                <a-animation attribute="rotation" to="0 360 0" dur="15000" repeat="indefinite" easing="linear"></a-animation>
            </a-entity>
            
            <a-camera position="0 0 0" look-controls="enabled: false" wasd-controls="enabled: false"></a-camera>
            <a-light type="ambient" color="#ffffff" intensity="0.8"></a-light>
            <a-light type="directional" color="#ffffff" intensity="0.6" position="-1 2 1"></a-light>
        </a-scene>
    `;
    
    const visorModal = new bootstrap.Modal(document.getElementById('visor3DModal'));
    visorModal.show();
}

function limpiarVisor3D() {
    const contenedor = document.getElementById('contenedorEscena3D');
    contenedor.innerHTML = ''; // Destruye la escena para ahorrar recursos (impuesto térmico)
}


/* =========================================================
   7. SISTEMA DE AUTENTICACIÓN (Login / Registro + 2FA)
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
        mostrarToastVIP("Por favor, llena todos los campos correctamente.");
        return;
    }

    btn.innerText = "Creando cuenta..."; btn.disabled = true;

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
            mostrarToastVIP("✉️ Token enviado con éxito.");
        } else {
            mostrarToastVIP("Aviso: " + data.mensaje);
        }
    } catch (error) {
        mostrarToastVIP("Error de conexión con la bóveda.");
    } finally {
        btn.innerText = "Registrarse"; btn.disabled = false;
    }
}

async function procesarLogin() {
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value.trim();
    const btn = document.getElementById('btn-login');

    if (!email.includes('@') || !password) {
        mostrarToastVIP("Por favor, ingresa tu correo y contraseña.");
        return;
    }

    btn.innerText = "Verificando..."; btn.disabled = true;

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
            mostrarToastVIP("✉️ Token de seguridad enviado.");
        } else {
            mostrarToastVIP(data.mensaje);
        }
    } catch (error) {
        mostrarToastVIP("Error de conexión.");
    } finally {
        btn.innerText = "Entrar"; btn.disabled = false;
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
        mostrarToastVIP("Ingresa el token completo.");
        return;
    }

    btn.innerText = "Validando..."; btn.disabled = true;

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
            if (modalInstance) modalInstance.hide();
            
            mostrarAlertaVIP(
                "Acceso Concedido", 
                `Bienvenido de vuelta a tu colección privada, ${data.usuario || data.email}.`, 
                "bi-unlock"
            );
            
            reiniciarModalLogin();
            gestionarAccesoPerfil(); 
        } else {
            mostrarToastVIP("Error: " + data.mensaje);
        }
    } catch (error) {
        mostrarToastVIP("Error de conexión.");
    } finally {
        btn.innerText = "Verificar Token"; btn.disabled = false;
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
   8. MI BÓVEDA (Gestión del Panel de Perfil y Descargas)
   ========================================================= */
function gestionarAccesoPerfil() {
    const usuarioActivo = localStorage.getItem('auraVIP_User');
    
    if (!usuarioActivo) {
        const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
        loginModal.show();
    } else {
        const profileOffcanvas = new bootstrap.Offcanvas(document.getElementById('profileDrawer'));
        profileOffcanvas.show();
        cargarDatosPerfil(usuarioActivo);
    }
}

async function cargarDatosPerfil(emailUsuario) {
    document.getElementById('perfil-email').innerText = emailUsuario;
    document.getElementById('perfil-nombre').innerText = "Cargando datos...";
    document.getElementById('perfil-telefono').innerText = "Cargando...";
    document.getElementById('perfil-pedidos-container').innerHTML = '<p class="text-muted" style="font-size: 0.9rem; font-style: italic;">Conectando con la bóveda central...</p>';

    try {
        const respuesta = await fetch('https://joyeria-aura-42ax.onrender.com/api/perfil-usuario', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: emailUsuario })
        });

        if (respuesta.status === 200) {
            const datos = await respuesta.json();
            document.getElementById('perfil-nombre').innerText = datos.usuario || "Coleccionista VIP";
            document.getElementById('perfil-telefono').innerText = datos.telefono || "Teléfono no registrado";
            
            const contenedorPedidos = document.getElementById('perfil-pedidos-container');
            
            if (datos.pedidos && datos.pedidos.length > 0) {
                let htmlPedidos = '';
                datos.pedidos.forEach(pedido => {
                    
                    let botonDescarga = '';
                    if (pedido.estado === 'PAGADO') {
                        botonDescarga = `
                        <div class="mt-2 text-end">
                            <a href="https://joyeria-aura-42ax.onrender.com/api/descargar-certificado/${pedido.id_orden}" 
                               target="_blank"
                               class="btn btn-sm" 
                               style="font-size: 0.75rem; letter-spacing: 1px; color: var(--oro-rosa-cenizo); border: 1px solid var(--oro-rosa-cenizo); border-radius: 4px; text-decoration: none; padding: 4px 10px; transition: all 0.3s ease;">
                               <i class="bi bi-file-earmark-pdf me-1"></i> Obtener Certificado
                            </a>
                        </div>`;
                    }

                    htmlPedidos += `
                        <div class="mb-3 p-3" style="background-color: #fcfcfc; border-radius: 8px; border-left: 3px solid var(--oro-rosa-cenizo); box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
                            <p class="mb-1 fw-bold font-serif" style="font-size: 1rem;">${pedido.nombre_joya}</p>
                            <p class="mb-1 text-muted" style="font-size: 0.8rem;">Folio: ${pedido.id_orden.substring(0,8)}...</p>
                            <p class="mb-1 text-muted" style="font-size: 0.8rem;">Fecha: ${new Date(pedido.fecha).toLocaleDateString()}</p>
                            <span class="badge ${pedido.estado === 'PAGADO' ? 'bg-success' : 'bg-warning text-dark'}" style="font-size: 0.7rem; letter-spacing: 1px;">
                                ${pedido.estado === 'PAGADO' ? 'ASEGURADO' : 'PENDIENTE DE PAGO'}
                            </span>
                            ${botonDescarga}
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
        document.getElementById('perfil-nombre').innerText = "Modo Sin Conexión";
        document.getElementById('perfil-pedidos-container').innerHTML = '<p class="text-muted" style="font-size: 0.9rem;">Revisa tu conexión a internet.</p>';
    }
}

function cerrarSesionVIP() {
    localStorage.removeItem('auraVIP_User');
    
    const profileElement = document.getElementById('profileDrawer');
    const profileOffcanvas = bootstrap.Offcanvas.getInstance(profileElement);
    if(profileOffcanvas) profileOffcanvas.hide();
    
    mostrarToastVIP("🔒 Bóveda cerrada. Hasta pronto.");
}

function seleccionarYGuiar(idJoya) {
    agregarAlCarrito(idJoya);
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('welcomeGuideModal'));
    if(modal) modal.hide();
    
    document.getElementById('galeria').scrollIntoView({ behavior: 'smooth' });
    
    mostrarToastVIP("Excelente elección. Hemos reservado tu pieza en tu bolsa.");
}
