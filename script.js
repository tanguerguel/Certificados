let usuariosData = [];
let imagenBase64 = null;
let usuarioActual = null;
let imagenPosteriorCache = {};

// ============================================
// CONFIGURACIÓN
// ============================================
const CONFIG = {
    imagenBase: 'certificado_base.jpg',  // ✅ JPG
    posiciones: {
        nombre: { x: 148, y: 80 },
        registro: { x: 40, y: 175 }
    },
    // Mapeo de cursos a imágenes posteriores
    cursoPosterior: {
        'ingles'    : 'certificado_posterior1.jpg',  
        'ashaninka' : 'certificado_posterior1.jpg',    
        'matsigenka': 'certificado_posterior1.jpg',
        'default'   : 'certificado_posterior1.jpg'  
    }
};
// ============================================
// CARGAR DATOS
// ============================================
async function cargarDatos() {
    try {
        const response = await fetch('data.json');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        usuariosData = data.usuarios;
        console.log(`✅ ${usuariosData.length} certificados cargados`);
        console.log('📋 Primer usuario:', usuariosData[0]);
    } catch (error) {
        console.warn('⚠️ Error cargando datos:', error);
        // Datos de ejemplo para pruebas
        usuariosData = [
            ];
    }
}

// ============================================
// CARGAR LIBRERÍAS
// ============================================
function cargarLibreria(url) {
    return new Promise((resolve, reject) => {
        if (document.querySelector(`script[src="${url}"]`)) {
            resolve();
            return;
        }
        const script = document.createElement('script');
        script.src = url;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// ============================================
// CONVERTIR IMAGEN A BASE64
// ============================================
async function imagenABase64(url) {
    try {
        console.log(`📸 Cargando imagen: ${url}`);
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Error ${response.status}`);
        
        const blob = await response.blob();
        console.log(`📸 Tamaño: ${(blob.size / 1024 / 1024).toFixed(2)} MB`);
        
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                console.log('✅ Imagen convertida a Base64');
                resolve(reader.result);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    } catch (error) {
        console.error('❌ Error cargando imagen:', error);
        throw error;
    }
}

// ============================================
// OBTENER IMAGEN POSTERIOR SEGÚN CURSO
// ============================================
function getImagenPosterior(curso) {
    // Normalizar curso (minúsculas, sin espacios)
    const cursoKey = curso ? curso.toLowerCase().trim() : '';
    
    // Buscar en el mapeo
    if (CONFIG.cursoPosterior[cursoKey]) {
        return CONFIG.cursoPosterior[cursoKey];
    }
    
    // Si no encuentra, usar la primera como default
    console.warn(`⚠️ Curso "${curso}" no tiene imagen asignada, usando certificado_posterior1.jpg`);
    return 'certificado_posterior1.jpg';
}

// ============================================
// DESCARGAR CERTIFICADO (CON DOS HOJAS)
// ============================================
async function descargarCertificado(usuario) {
    const loadingMsg = document.getElementById('loadingMsg');
    loadingMsg.style.display = 'block';
    loadingMsg.textContent = '⏳ Generando certificado...';

    try {
        // === VALIDAR USUARIO ===
        if (!usuario) throw new Error('Usuario es null o undefined');
        if (!usuario.nombre) throw new Error('El usuario no tiene propiedad "nombre"');
        if (!usuario.num_registro) throw new Error('El usuario no tiene propiedad "num_registro"');

        console.log('📋 Usuario recibido:', usuario);

        // 1. Cargar pdf-lib
        console.log('📚 Cargando pdf-lib...');
        await cargarLibreria('https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js');
        console.log('✅ pdf-lib cargado');

        // 2. Cargar imagen frontal
        if (!imagenBase64) {
            imagenBase64 = await imagenABase64(CONFIG.imagenBase);
        }

        // 3. Cargar imagen posterior según curso
        const imagenPosterior = getImagenPosterior(usuario.curso);
        console.log(`📸 Imagen posterior para curso "${usuario.curso}": ${imagenPosterior}`);
        
        let imagenPosteriorBase64 = imagenPosteriorCache[imagenPosterior];
        if (!imagenPosteriorBase64) {
            imagenPosteriorBase64 = await imagenABase64(imagenPosterior);
            imagenPosteriorCache[imagenPosterior] = imagenPosteriorBase64;
        }

        // 4. Crear PDF
        const { PDFDocument, rgb, StandardFonts } = PDFLib;
        const doc = await PDFDocument.create();
        
        // ========== HOJA 1: CERTIFICADO FRONTAL ==========
        const page1 = doc.addPage([842, 595]);
        await dibujarPagina(doc, page1, imagenBase64, usuario, false);
        console.log('✅ Página 1 (frontal) agregada');

        // ========== HOJA 2: CERTIFICADO POSTERIOR ==========
        const page2 = doc.addPage([842, 595]);
        await dibujarPagina(doc, page2, imagenPosteriorBase64, usuario, true);
        console.log('✅ Página 2 (posterior) agregada');

        // 5. Guardar PDF
        const pdfBytes = await doc.save();
        const blob = new Blob([pdfBytes], { type: 'application/pdf' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `certificado_${usuario.id}_${usuario.nombre.replace(/\s/g, '_')}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
        
        console.log('✅ PDF generado exitosamente');
        loadingMsg.textContent = '✅ ¡Certificado generado!';
        loadingMsg.style.color = '#27ae60';
        setTimeout(() => {
            loadingMsg.style.display = 'none';
            loadingMsg.style.color = '';
        }, 3000);

    } catch (error) {
        console.error('❌ Error detallado:', error);
        loadingMsg.textContent = `❌ Error: ${error.message}`;
        loadingMsg.style.color = 'red';
        setTimeout(() => {
            loadingMsg.style.display = 'none';
            loadingMsg.style.color = '';
        }, 5000);
    }
}

// ============================================
// DIBUJAR PÁGINA DEL PDF
// ============================================
async function dibujarPagina(doc, page, imagenBase64, usuario, esPosterior) {
    const { rgb, StandardFonts } = PDFLib;
    
    // Convertir imagen
    const imageBytes = await fetch(imagenBase64).then(res => res.arrayBuffer());
    const imageUint8 = new Uint8Array(imageBytes);
    
    // Embedir imagen
    let image;
    try {
        image = await doc.embedJpg(imageUint8);
        console.log('✅ Imagen JPG embebida');
    } catch (e) {
        image = await doc.embedPng(imageUint8);
        console.log('✅ Imagen PNG embebida');
    }

    // Dibujar imagen de fondo
    const { width: imgWidth, height: imgHeight } = image;
    const pageWidth = page.getWidth();
    const pageHeight = page.getHeight();
    
    const scale = Math.min(pageWidth / imgWidth, pageHeight / imgHeight);
    const scaledWidth = imgWidth * scale;
    const scaledHeight = imgHeight * scale;
    const x = (pageWidth - scaledWidth) / 2;
    const y = (pageHeight - scaledHeight) / 2;
    
    page.drawImage(image, {
        x: x,
        y: y,
        width: scaledWidth,
        height: scaledHeight,
    });

    // Si es la página frontal, agregar texto
    if (!esPosterior) {
        // NOMBRE
        const font = await doc.embedFont(StandardFonts.HelveticaBold);
        const fontSize = 27;
        const text = usuario.nombre.toUpperCase();
        const textWidth = font.widthOfTextAtSize(text, fontSize);
        const textX = ((pageWidth - textWidth) / 2) + 50;
        const textY = pageHeight / 2 + 53;
        
        page.drawText(text, {
            x: textX,
            y: textY,
            size: fontSize,
            font: font,
            color: rgb(0.1, 0.1, 0.18),
        });

        // NÚMERO DE REGISTRO
        const fontNormal = await doc.embedFont(StandardFonts.Helvetica);
        const fontSizeReg = 16;
        const regX = pageWidth - 75;
        const regY = 20;
        
        page.drawText(usuario.num_registro, {
            x: regX,
            y: regY,
            size: fontSizeReg,
            font: fontNormal,
            color: rgb(0.18, 0.18, 0.18),
        });

        // ========== QR CODE (COMENTADO) ==========
        // Cuando tengas la imagen del QR, descomenta esto:
        /*
        // Cargar imagen QR
        const qrImage = await cargarImagenQR('qr_code.png');
        if (qrImage) {
            const qrWidth = 60;
            const qrHeight = 60;
            const qrX = pageWidth - 90;
            const qrY = 30;
            
            page.drawImage(qrImage, {
                x: qrX,
                y: qrY,
                width: qrWidth,
                height: qrHeight,
            });
            console.log('✅ QR Code agregado');
        }
        */

        // DNI (opcional)
       // if (usuario.DNI) {
        //    doc.setFontSize(12);
         //   doc.setFont('helvetica', 'normal');
         //   doc.setTextColor(0.3, 0.3, 0.3);
            // Agregar DNI en alguna posición
      //  }
    }
}

// ============================================
// FUNCIÓN PARA CARGAR QR (COMENTADA)
// ============================================
/*
async function cargarImagenQR(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) return null;
        const bytes = await response.arrayBuffer();
        const uint8 = new Uint8Array(bytes);
        const { PDFDocument } = PDFLib;
        const doc = await PDFDocument.create();
        let image;
        try {
            image = await doc.embedJpg(uint8);
        } catch (e) {
            image = await doc.embedPng(uint8);
        }
        return image;
    } catch (error) {
        console.error('❌ Error cargando QR:', error);
        return null;
    }
}
*/

// ============================================
// LOGIN
// ============================================
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const nombre = document.getElementById('nombre').value.trim();
    const contrasena = document.getElementById('contrasena').value.trim();
    const errorMsg = document.getElementById('errorMsg');
    const loadingMsg = document.getElementById('loadingMsg');
    const downloadSection = document.getElementById('downloadSection');
    
    // Ocultar sección de descarga anterior
    downloadSection.style.display = 'none';
    
    if (!nombre || !contrasena) {
        errorMsg.textContent = '❌ Completa todos los campos.';
        errorMsg.style.display = 'block';
        return;
    }

    errorMsg.style.display = 'none';
    loadingMsg.style.display = 'block';
    loadingMsg.textContent = '⏳ Verificando credenciales...';
    
    if (usuariosData.length === 0) {
        await cargarDatos();
    }

    //console.log(`🔍 Buscando: "${nombre}" con contraseña: "${contrasena}"`);
    
    const usuario = usuariosData.find(u => 
        u.nombre.toLowerCase() === nombre.toLowerCase() && 
        u.contrasena === contrasena
    );

    console.log(`🔍 Usuario encontrado:`, usuario);

    loadingMsg.style.display = 'none';

    if (usuario) {
        usuarioActual = usuario;
        // Mostrar botón de descarga
        downloadSection.style.display = 'block';
        errorMsg.style.display = 'none';
        
        // Mensaje de éxito
        const successMsg = document.createElement('div');
        successMsg.id = 'successMsg';
        successMsg.style.cssText = 'color: #27ae60; text-align: center; margin-top: 10px; font-size: 14px;';
        successMsg.textContent = '✅ Sesión iniciada correctamente. Haz clic en "Descargar Certificado".';
        
        // Eliminar mensaje anterior si existe
        const oldMsg = document.getElementById('successMsg');
        if (oldMsg) oldMsg.remove();
        
        document.getElementById('loginForm').appendChild(successMsg);
        
        // Limpiar campos
        document.getElementById('nombre').value = '';
        document.getElementById('contrasena').value = '';
    } else {
        errorMsg.textContent = '❌ Credenciales incorrectas. Verifica tu Nombre y contraseña.';
        errorMsg.style.display = 'block';
    }
});

// ============================================
// BOTÓN DESCARGAR
// ============================================
document.getElementById('btnDownload').addEventListener('click', async function() {
    if (usuarioActual) {
        await descargarCertificado(usuarioActual);
    } else {
        alert('Por favor, inicia sesión primero.');
    }
});

// ============================================
// INICIAR
// ============================================
cargarDatos();