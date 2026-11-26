"""
Backend de la calculadora de Gomilocas.

Cómo ejecutarlo:
1. Guarda este archivo en la misma carpeta que index.html.
2. Abre una terminal en esa carpeta.
3. Ejecuta: python calculadora.py
4. Abre en el navegador: http://localhost:8000

Este servidor usa únicamente la biblioteca estándar de Python.
"""

from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import math


# 1. Obtiene la carpeta donde está guardado este archivo.
# Así el servidor encuentra index.html, css/ e img/ aunque se ejecute
# desde otra carpeta de la terminal.
CARPETA_PROYECTO = Path(__file__).resolve().parent


# 2. Precios tomados de los valores de las opciones del <select id="producto">
# de index.html. Se usan los valores del HTML de la calculadora,
# no los precios diferentes que aparecen en las tarjetas del catálogo.
PRODUCTOS = {
    "18000": {"nombre": "Bandeja loca", "precio": 18000},
    "10000": {"nombre": "Vaso enchilado", "precio": 10000},
    "3000": {"nombre": "Bolsita pequeña", "precio": 3000},
    "6000": {"nombre": "Bolsita mediana", "precio": 6000},
    "9000": {"nombre": "Bolsita grande", "precio": 9000},
    "5000": {"nombre": "Pincho dulce", "precio": 5000},
}


# 3. No se encontraron códigos concretos de descuento en index.html.
# Por eso el diccionario empieza vacío. Cuando tengas códigos reales,
# puedes agregarlos, por ejemplo: "GOMI10": 0.10 (10 % de descuento).
CODIGOS_DESCUENTO = {
    "GOMI10": 0.10,
    "GOMI15": 0.15,
    "GOMI20": 0.20
}


def calcular_pedido(producto, cantidad, codigo_descuento=""):
    """Valida los datos y devuelve el resumen y el total del pedido."""

    # 4. Comprueba que el producto exista en la lista de precios.
    if producto not in PRODUCTOS:
        raise ValueError("Selecciona un producto válido.")

    # 5. Convierte la cantidad a número entero y valida que sea positiva.
    try:
        cantidad = int(cantidad)
    except (TypeError, ValueError):
        raise ValueError("La cantidad debe ser un número entero.")

    if cantidad < 1:
        raise ValueError("La cantidad debe ser como mínimo 1.")

    # 6. Recupera el nombre y el precio unitario del producto elegido.
    informacion = PRODUCTOS[producto]
    nombre = informacion["nombre"]
    precio_unitario = informacion["precio"]

    # 7. Calcula el subtotal antes de aplicar promociones o descuentos.
    subtotal = precio_unitario * cantidad

    # 8. Aplica la promoción 2 x 1 a las bolsitas pequeñas los sábados
    # y domingos, tal como se describe en la sección Promociones de index.html.
    # En una compra de 1 se paga 1; de 2 se paga 1; de 3 se pagan 2, etc.
    descuento_promocion = 0
    es_fin_de_semana = datetime.now().weekday() in (5, 6)

    if producto == "3000" and es_fin_de_semana:
        unidades_cobradas = math.ceil(cantidad / 2)
        total_con_promocion = unidades_cobradas * precio_unitario
        descuento_promocion = subtotal - total_con_promocion
    else:
        total_con_promocion = subtotal

    # 9. Normaliza el código: elimina espacios y no distingue mayúsculas.
    codigo = (codigo_descuento or "").strip().upper()

    # 10. Si se escribió un código, verifica que esté configurado.
    # Como index.html no define códigos, por ahora cualquier código escrito
    # será rechazado hasta que agregues uno a CODIGOS_DESCUENTO.
    descuento_codigo = 0
    if codigo:
        if codigo not in CODIGOS_DESCUENTO:
            raise ValueError("El código de descuento no es válido.")
        porcentaje = CODIGOS_DESCUENTO[codigo]
        descuento_codigo = round(total_con_promocion * porcentaje)

    # 11. Resta el descuento por código al total con promoción.
    total = total_con_promocion - descuento_codigo

    # 12. Devuelve todos los datos que la página puede mostrar.
    return {
        "producto": nombre,
        "cantidad": cantidad,
        "precio_unitario": precio_unitario,
        "subtotal": subtotal,
        "descuento_promocion": descuento_promocion,
        "descuento_codigo": descuento_codigo,
        "total": total,
        "mensaje": (
            "Se aplicó la promoción 2 x 1 de fin de semana."
            if descuento_promocion > 0
            else "Pedido calculado correctamente."
        ),
    }


class ManejadorGomilocas(SimpleHTTPRequestHandler):
    """Atiende archivos de la página y solicitudes de cálculo."""

    # 13. Hace que los archivos HTML, CSS e imágenes se lean desde
    # la carpeta del proyecto, no desde la carpeta accidental de ejecución.
    def translate_path(self, path):
        ruta_solicitada = super().translate_path(path)
        nombre_relativo = Path(ruta_solicitada).relative_to(Path.cwd())
        return str(CARPETA_PROYECTO / nombre_relativo)

    # 14. Recibe los datos enviados por el navegador a /api/calcular.
    def do_POST(self):
        if self.path != "/api/calcular":
            self.send_error(404, "Ruta no encontrada")
            return

        try:
            # 15. Lee la cantidad de bytes del cuerpo de la solicitud.
            longitud = int(self.headers.get("Content-Length", "0"))
            cuerpo = self.rfile.read(longitud)

            # 16. Convierte el JSON recibido en un diccionario de Python.
            datos = json.loads(cuerpo.decode("utf-8"))

            # 17. Ejecuta la función que contiene las reglas de negocio.
            resultado = calcular_pedido(
                producto=str(datos.get("producto", "")),
                cantidad=datos.get("cantidad"),
                codigo_descuento=datos.get("descuento", ""),
            )

            # 18. Envía el resultado al navegador con estado HTTP 200.
            self.enviar_json(200, resultado)

        except (ValueError, json.JSONDecodeError) as error:
            # 19. Si los datos no son válidos, responde con un mensaje claro.
            self.enviar_json(400, {"error": str(error)})

    # 20. Convierte un diccionario a JSON y lo envía con las cabeceras correctas.
    def enviar_json(self, estado, datos):
        respuesta = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(respuesta)))
        self.end_headers()
        self.wfile.write(respuesta)


# 21. Esta condición inicia el servidor solo cuando ejecutas este archivo
# directamente; no lo inicia si se importa desde otro archivo Python.
if __name__ == "__main__":
    servidor = ThreadingHTTPServer(("localhost", 8000), ManejadorGomilocas)
    print("Calculadora Gomilocas activa en http://localhost:8000")
    print("Presiona Ctrl + C para detener el servidor.")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando el servidor...")
        servidor.server_close()
