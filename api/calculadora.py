from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, quote
from html import escape


# Productos y precios de la calculadora
PRODUCTOS = {
    "18000": {"nombre": "Bandeja loca", "precio": 18000},
    "10000": {"nombre": "Vaso enchilado", "precio": 10000},
    "3000": {"nombre": "Bolsita pequeña", "precio": 3000},
    "6000": {"nombre": "Bolsita mediana", "precio": 6000},
    "9000": {"nombre": "Bolsita grande", "precio": 9000},
    "5000": {"nombre": "Pincho dulce", "precio": 5000},
}


# Códigos de descuento disponibles
CODIGOS_DESCUENTO = {
    "GOMI10": 0.10,
    "GOMI15": 0.15,
    "GOMI20": 0.20
}


def formatear_pesos(monto):
    """Muestra los valores en pesos colombianos."""
    return f"${monto:,}".replace(",", ".")


def calcular_pedido(producto, cantidad, codigo_descuento=""):
    """Calcula el pedido aplicando las promociones correspondientes."""

    if producto not in PRODUCTOS:
        raise ValueError("Selecciona un producto válido.")

    try:
        cantidad = int(cantidad)
    except (TypeError, ValueError):
        raise ValueError("La cantidad debe ser un número entero.")

    if cantidad < 1:
        raise ValueError("La cantidad debe ser como mínimo 1.")

    informacion = PRODUCTOS[producto]
    nombre = informacion["nombre"]
    precio_unitario = informacion["precio"]

    # Calcula el subtotal
    subtotal = precio_unitario * cantidad

    # Verifica si es sábado o domingo en horario de Colombia
    horario_colombia = timezone(timedelta(hours=-5))
    fecha_actual = datetime.now(horario_colombia)
    es_fin_de_semana = fecha_actual.weekday() in (5, 6)

    # Promoción 2 x 1 para bolsitas pequeñas
    descuento_promocion = 0

    if producto == "3000" and es_fin_de_semana:
        unidades_cobradas = (cantidad + 1) // 2
        total_con_promocion = unidades_cobradas * precio_unitario
        descuento_promocion = subtotal - total_con_promocion
    else:
        total_con_promocion = subtotal

    # Valida el código de descuento
    codigo = (codigo_descuento or "").strip().upper()
    descuento_codigo = 0

    if codigo:
        if codigo not in CODIGOS_DESCUENTO:
            raise ValueError("El código de descuento no es válido.")

        porcentaje = CODIGOS_DESCUENTO[codigo]
        descuento_codigo = round(total_con_promocion * porcentaje)

    # Calcula el total final
    total = total_con_promocion - descuento_codigo

    mensaje = (
        "Se aplicó la promoción 2 x 1 de fin de semana."
        if descuento_promocion > 0
        else "Pedido calculado correctamente."
    )

    if descuento_codigo > 0:
        mensaje += " También se aplicó tu código de descuento."

    return {
        "producto": nombre,
        "cantidad": cantidad,
        "precio_unitario": precio_unitario,
        "subtotal": subtotal,
        "descuento_promocion": descuento_promocion,
        "descuento_codigo": descuento_codigo,
        "total": total,
        "mensaje": mensaje
    }


class handler(BaseHTTPRequestHandler):

    def enviar_html(self, contenido, estado=200):
        respuesta = contenido.encode("utf-8")

        self.send_response(estado)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(respuesta)))
        self.end_headers()
        self.wfile.write(respuesta)

    def do_GET(self):
        contenido = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Gomilocas - Calculadora</title>
        </head>
        <body>
            <h1>Calculadora Gomilocas</h1>
            <p>Para calcular tu pedido, regresa a la página principal
            y completa el formulario.</p>
            <a href="/">Volver a Gomilocas</a>
        </body>
        </html>
        """
        self.enviar_html(contenido)

    def do_POST(self):
        try:
            longitud = int(self.headers.get("Content-Length", "0"))
            cuerpo = self.rfile.read(longitud).decode("utf-8")

            datos = parse_qs(cuerpo, keep_blank_values=True)

            producto = datos.get("producto", [""])[0]
            cantidad = datos.get("cantidad", [""])[0]
            descuento = datos.get("descuento", [""])[0]

            resultado = calcular_pedido(
                producto,
                cantidad,
                descuento
            )

            nombre = escape(resultado["producto"])
            cantidad = resultado["cantidad"]
            precio = formatear_pesos(resultado["precio_unitario"])
            subtotal = formatear_pesos(resultado["subtotal"])
            descuento_promo = formatear_pesos(
                resultado["descuento_promocion"]
            )
            descuento_codigo = formatear_pesos(
                resultado["descuento_codigo"]
            )
            total = formatear_pesos(resultado["total"])
            mensaje = escape(resultado["mensaje"])

            texto_whatsapp = (
                f"Hola, quiero realizar un pedido en Gomilocas. "
                f"Producto: {nombre}. Cantidad: {cantidad}. "
                f"Total estimado: {total}."
            )

            enlace_whatsapp = (
                "https://wa.me/573017518888?text="
                + quote(texto_whatsapp)
            )

            contenido = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Resultado de tu pedido | Gomilocas</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background: #fff4f7;
                        margin: 0;
                        padding: 30px 15px;
                        color: #333;
                    }}
                    .contenedor {{
                        max-width: 480px;
                        margin: 30px auto;
                        background: white;
                        padding: 30px;
                        border-radius: 18px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                    }}
                    h1 {{
                        text-align: center;
                        color: #d63384;
                    }}
                    .fila {{
                        display: flex;
                        justify-content: space-between;
                        gap: 15px;
                        padding: 10px 0;
                        border-bottom: 1px solid #eee;
                    }}
                    .total {{
                        font-size: 25px;
                        font-weight: bold;
                        color: #d63384;
                        text-align: center;
                        margin: 25px 0;
                    }}
                    .mensaje {{
                        text-align: center;
                        color: #555;
                    }}
                    .boton {{
                        display: block;
                        text-align: center;
                        padding: 13px;
                        margin-top: 15px;
                        border-radius: 10px;
                        text-decoration: none;
                        font-weight: bold;
                    }}
                    .whatsapp {{
                        background: #25d366;
                        color: white;
                    }}
                    .volver {{
                        background: #fce4ec;
                        color: #a51d5d;
                    }}
                </style>
            </head>
            <body>
                <div class="contenedor">
                    <h1>¡Tu pedido está calculado!</h1>

                    <div class="fila">
                        <span>Producto</span>
                        <strong>{nombre}</strong>
                    </div>

                    <div class="fila">
                        <span>Cantidad</span>
                        <strong>{cantidad}</strong>
                    </div>

                    <div class="fila">
                        <span>Precio unitario</span>
                        <strong>{precio}</strong>
                    </div>

                    <div class="fila">
                        <span>Subtotal</span>
                        <strong>{subtotal}</strong>
                    </div>

                    <div class="fila">
                        <span>Descuento promoción</span>
                        <strong>{descuento_promo}</strong>
                    </div>

                    <div class="fila">
                        <span>Descuento por código</span>
                        <strong>{descuento_codigo}</strong>
                    </div>

                    <div class="total">
                        Total: {total}
                    </div>

                    <p class="mensaje">{mensaje}</p>

                    <a class="boton whatsapp"
                       href="{enlace_whatsapp}"
                       target="_blank"
                       rel="noopener">
                       Continuar por WhatsApp
                    </a>

                    <a class="boton volver" href="/#calculadora">
                       Volver a la calculadora
                    </a>
                </div>
            </body>
            </html>
            """

            self.enviar_html(contenido)

        except ValueError as error:
            mensaje_error = escape(str(error))

            contenido = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Error en el pedido | Gomilocas</title>
            </head>
            <body>
                <h1>No pudimos calcular tu pedido</h1>
                <p>{mensaje_error}</p>
                <a href="/#calculadora">Regresar e intentarlo nuevamente</a>
            </body>
            </html>
            """

            self.enviar_html(contenido, 400)