import re  # Para limpiar las estrellas de los restaurantes
import json
import textwrap  # Para dividir los enlaces largos en líneas más cortas
import urllib.parse  # Para limpiar y acortar los enlaces
from horario import HorarioProcessor
import mysql.connector
import json
import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import blue, black, red 

class Restaurante:
    def __init__(self, id_justeat, url, nombre, localizacion, estrellas):
        self.id_justeat = id_justeat
        self.url = url
        self.nombre = nombre
        self.localizacion = localizacion if localizacion and localizacion.lower() != "none" else "Ubicación desconocida"
        self.estrellas = estrellas

    def __repr__(self):
        return f"{self.nombre} ({self.estrellas}⭐) - {self.localizacion}\n{self.url}\n"

    def es_completo(self):
        return all([
            self.url,
            self.nombre,
            self.localizacion != "Ubicación desconocida",
            self.estrellas
        ])

class DatabaseManager:
    def __init__(self, host, user, password, database):
        """Inicializa la conexión con la base de datos."""
        self.config = {
            "host": host,
            "user": user,
            "password": password,
            "database": database
        }
        self.conexion = None
        self.cursor = None
        self.conectar()
    def actualizar_movil_a_true(self, id_googlemaps):
        """Actualiza la columna 'movil' a True dado un id_googlemaps."""
        try:
            sql = """
                UPDATE GoogleMapsRestaurantes
                SET movil = TRUE
                WHERE id_googlemaps = %s
            """
            self.cursor.execute(sql, (id_googlemaps,))
            self.conexion.commit()
            print(f"🔄 'movil' actualizado a TRUE para id_googlemaps = {id_googlemaps}")
        except mysql.connector.Error as err:
            print(f"❌ Error al actualizar 'movil': {err}")
    def actualizar_mensaje(self, mensaje, id_googlemaps):
        """Actualiza la columna 'mensaje' con el texto dado para un id_googlemaps."""
        try:
            sql = """
                UPDATE GoogleMapsRestaurantes
                SET mensaje = %s
                WHERE id_googlemaps = %s
            """
            self.cursor.execute(sql, (mensaje, id_googlemaps))
            self.conexion.commit()
            print(f"📩 Mensaje actualizado para id_googlemaps = {id_googlemaps}")
        except mysql.connector.Error as err:
            print(f"❌ Error al actualizar mensaje: {err}")

    def conectar(self):
        """Establece la conexión con la base de datos."""
        try:
            self.conexion = mysql.connector.connect(**self.config)
            self.cursor = self.conexion.cursor(dictionary=True)
            print("✅ Conexión exitosa a MySQL")
        except mysql.connector.Error as err:
            print(f"❌ Error al conectar: {err}")

    def cerrar(self):
        """Cierra la conexión a la base de datos."""
        if self.conexion:
            self.cursor.close()
            self.conexion.close()
            print("🔌 Conexión cerrada.")

    def obtener_lugares(self):
        """
        Obtiene todos los lugares de la tabla 'Lugar', agrupados por municipio, código postal e ID del lugar.
        :return: Lista de diccionarios con los campos id_lugar, municipio y codigo_postal.
        """
        query = """
        SELECT id_lugar, municipio, codigo_postal 
        FROM Lugar
        ORDER BY municipio, codigo_postal;
        """
        try:
            self.cursor.execute(query)
            lugares = self.cursor.fetchall()
            return lugares
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener los lugares: {err}")
            return []

    def obtener_datos_filtrados(self,max_registros):
         """
         Devuelve los registros que cumplan tu condición (ejemplo de filtrado).
         """
         query = f"""SELECT * FROM Raspado WHERE interesa=1 ;

 """
         try:
             self.cursor.execute(query)
             resultados = self.cursor.fetchall()
             return resultados
         except mysql.connector.Error as err:
             print(f"❌ Error al obtener datos filtrados: {err}")
             return []
    def obtener_datos_llamadas(self,max_registros):
         """
         Devuelve los registros que cumplan tu condición (ejemplo de filtrado).
         """
         query = f"""SELECT 
  j.id_justeat, 
  j.link_justeat, 
  j.nombre AS justeat_nombre, 
  j.direccion AS justeat_direccion, 
  j.estrellas AS justeat_estrellas, 
  j.comentarios AS justeat_comentarios, 
  j.carta, 
  j.horario, 
  j.lugares, 
  j.completo, 
  j.interesa AS justeat_interesa,
  g.*
FROM GoogleMapsRestaurantes g
LEFT JOIN JusteatRestaurantes j ON j.id_justeat = g.id_justeat
WHERE g.interesa = 4
  AND g.telefono IS NOT NULL
LIMIT {max_registros}
 """
         try:
             self.cursor.execute(query)
             resultados = self.cursor.fetchall()
             return resultados
         except mysql.connector.Error as err:
             print(f"❌ Error al obtener datos filtrados: {err}")
             return []

    def candidatos_con_movil(self, max_registros):
        """
        Devuelve los registros donde el número de teléfono comienza con 6 o 7.
        """
        query = f"""SELECT * FROM GoogleMapsRestaurantes WHERE    (telefono LIKE '6%' OR telefono LIKE '7%')   AND tipo = 1   AND TRIM(urls_intermediarios) = '[]'   AND calendario IS NOT NULL
LIMIT {max_registros};

        
        """
        try:
            self.cursor.execute(query)
            resultados = self.cursor.fetchall()
            return resultados
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener datos de candidatos con móvil: {err}")
            return []

    def marcar_lugar_completo(self, id_lugar):
        """
        Actualiza el registro de la tabla Lugar para establecer 'completo' en TRUE,
        para el lugar cuyo id_lugar se pasa como parámetro.
        """
        query = "UPDATE Lugar SET completo = TRUE WHERE id_lugar = %s"
        try:
            self.cursor.execute(query, (id_lugar,))
            self.conexion.commit()
            print(f"✅ Lugar {id_lugar} marcado como completo.")
        except mysql.connector.Error as err:
            print(f"❌ Error al marcar lugar {id_lugar} como completo: {err}")

    def get_lugares_incompletos(self,id_):
        """
        Devuelve todos los lugares con 'completo' = FALSE.
        """
        query = f"SELECT codigo_postal FROM Lugar WHERE id_lugar = {id_};"
        try:
            self.cursor.execute(query)
            lugares = self.cursor.fetchall()
            return lugares
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener lugares incompletos: {err}")
            return None

    def obtener_links_no_completos(self):
        """
        Obtiene los links de JusteatRestaurantes que tienen 'completo' = 0.
        """
        query = "SELECT link_justeat FROM JusteatRestaurantes WHERE completo = 0"
        try:
            self.cursor.execute(query)
            resultados = self.cursor.fetchall()
            links = [row['link_justeat'] for row in resultados]
            return links
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener links no completos: {err}")
            return []
    def obtener_restaurantes_no_completos(self,max_registros):
        query = f"""SELECT *  FROM   Raspado WHERE interesa = 0 AND id_palabra=0;"""#academia baile
        try:
            self.cursor.execute(query)
            no_completos = self.cursor.fetchall()
            return no_completos
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener lugares incompletos: {err}")
            return None
    def obtener_pasados(self):
        query = """SELECT DISTINCT direccion FROM GoogleMapsRestaurantes;"""
        try:
            self.cursor.execute(query)
            resultados = self.cursor.fetchall()
            # Obtener la lista de direcciones
            direcciones = [str(row['direccion']) for row in resultados]
            return direcciones
        except mysql.connector.Error as err:
            print(f"Error al obtener las direcciones: {err}")
            return []
    def actualizar_raspado(self, raspado):
        """
        Actualiza un registro de raspado en la base de datos usando los datos del diccionario proporcionado.
    
        :param raspado: dict con los campos a actualizar, debe contener 'id_unico' como identificador
        """
        query = """
        UPDATE Raspado
        SET 
            url_google = %s,
            fecha_inicio = %s,
            fecha_fin = %s,
            nombre = %s,
            id_palabra = %s,
            id_lugar = %s,
            completado = %s,
            interesa = %s
        WHERE id_unico = %s
        """
        valores = (
            raspado.get('url_google', ''),
            raspado.get('fecha_inicio', ''),
            raspado.get('fecha_fin', ''),
            raspado.get('nombre', ''),
            raspado.get('id_palabra'),
            raspado.get('id_lugar'),
            raspado.get('completado', 1),
            raspado.get('interesa', 0),
            raspado.get('id_unico')
        )
        cursor = self.conexion.cursor()
        cursor.execute(query, valores)
        self.conexion.commit()
        
    def insertar_resultados(self, resultados):
        if isinstance(resultados, list):
            for resultado in resultados:
                print("Inserting resultado:")
                # Llamada recursiva o lógica similar
                self.insertar_resultado(resultado)
            return
        # Si no es lista, procede como antes
        print("💾 Iniciando inserción de resultado...")
        # ... resto del código ...
    def insertar_resultado(self, resultado):
        print("💾 Iniciando inserción de resultado...")
        
        # Preparar los datos con trazas para verificar
        print("Datos recibidos:")
        for key, value in resultado.items():
            print(f"  {key}: {value}")
        
        sql = """
        INSERT INTO GoogleMapsRestaurantes (
            id_raspado,
            nombre,
            direccion,
            estrellas,
            comentarios,
            intermediarios,
            urls_intermediarios,
            link_googlemaps,
            telefono,
            calendario,
            tipo,
            fecha_inicio,
            fecha_fin,
            id_lugar,
            cps,
            interesa,
            url_google
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
        """
        # Crear los parámetros con trazas
        params = (
            resultado['id_raspado'],
            resultado['nombre'],
            resultado['direccion'],
            resultado['estrellas'],
            resultado['comentarios'],
            resultado['intermediarios'],
            resultado['urls_intermediarios'],
            resultado['link_googlemaps'],
            resultado['telefono'],
            resultado['calendario'],
            resultado['tipo'],
            resultado['fecha_inicio'],
            resultado['fecha_fin'],
            resultado['id_lugar'],
            resultado['cps'],
            resultado['interesa'],
            resultado['url_google']
        )
        print("Parámetros para la consulta:")
        for i, param in enumerate(params, start=1):
            print(f"  param {i}: {param}")
        try:
            cursor = self.conexion.cursor()
            print("Ejecutando consulta...")
            cursor.execute(sql, params)
            print("Commit en curso...")
            self.conexion.commit()
            print("🎉 Inserción completada exitosamente.")
        except Exception as e:
            print(f"❌ Error durante la inserción: {e}")
                
            
    def obtener_restaurantes_completos(self, id_lugar):
            """
            Obtiene los registros de JusteatRestaurantes que tienen 'completo' = 1 y cuyo id_lugar coincide.
            Retorna una lista de objetos Restaurante.
            """
            query = """
                SELECT id_justeat, link_justeat, nombre, direccion, estrellas
                FROM JusteatRestaurantes
                WHERE completo = 1 AND id_lugar = %s
            """
            try:
                self.cursor.execute(query, (id_lugar,))
                resultados = self.cursor.fetchall()
                restaurantes = []
                for row in resultados:
                    restaurante = Restaurante(
                        id_justeat=row['id_justeat'],
                        url=row['link_justeat'],
                        nombre=row['nombre'],
                        localizacion=row['direccion'],
                        estrellas=row['estrellas']
                    )
                    restaurantes.append(restaurante)
                return restaurantes
            except mysql.connector.Error as err:
                print(f"❌ Error al obtener restaurantes completos: {err}")
                return []

    def insertar_googlemaps_restaurantes(self, lista_resultados):
        """
        Inserta en la tabla GoogleMapsRestaurantes los registros obtenidos de la búsqueda en Google Maps.
        
        Estructura en 'lista_resultados':
        {
             'id_raspado': <valor>,
             'nombre': <valor>,
             ... (otros campos que se ignoran)
        }
        
        Sólo se insertan los campos 'id_justeat' y 'nombre'. El resto de columnas se dejan en NULL o su valor por defecto.
        """
        query = """
        INSERT INTO GoogleMapsRestaurantes (id_justeat, nombre)
        VALUES (%s, %s)
        """
        try:
            for resultado in lista_resultados:
                print(resultado)
                id_justeat = json(resultado.get('id_lugar'))
                if id_justeat is None:
                    print(f"⚠ Advertencia: El restaurante {resultado.get('nombre', 'desconocido')} no tiene id_justeat. Se omite.")
                    continue
                nombre = resultado.get('nombre')
                self.cursor.execute(query, (id_justeat, nombre))
            self.conexion.commit()
            print(f"✅ {len(lista_resultados)} registros insertados en GoogleMapsRestaurantes.")
        except mysql.connector.Error as err:
            print(f"❌ Error al insertar en GoogleMapsRestaurantes: {err}")
    

    def generar_pdf(self, datos, nombre_archivo="reporte.pdf"):
        """
        Genera un PDF con la siguiente estructura para cada restaurante:
    
          Encabezado general (una vez al inicio):
            "Reporte de Restaurantes" y una línea que indica el orden: 
              Orden: Nombre | Dirección | HORARIO
    
          Para cada restaurante se dibuja un bloque (rectángulo) que abarca:
          
            Lado izquierdo (desde el margen izquierdo hasta antes del área reservada):
              Línea 1:
                - Nombre (completo)
                - HORARIO completo (del día actual, obtenido del JSON del campo "horario")
              Línea 2:
                - Dirección (completa)
              Línea 3:
                - Teléfono (10 caracteres, en rojo) y Enlace a Google Maps (si existe, se muestra como "Google Maps" en azul)
              Línea 4 en adelante (si hay intermediarios):
                - Cada URL de "urls_intermediarios" se imprime en una línea:
                    * Si contiene "just-eat", "uber", "glovoapp", "instagram" o "facebook", se usa el acrónimo;
                    * En otro caso se trunca a 15 caracteres.
                Se genera además un hipervínculo usando la URL original.
          
            Área reservada en el margen derecho (fija, 80 pts de ancho):
              - En la primera línea del bloque se dibujan 2 círculos (centrados en cada mitad del área).
              - En la segunda línea del bloque se dibujan las etiquetas correspondientes ("repartidoderes" y "web").
          
          Se deja un pequeño espacio entre bloques.
        """
        c = canvas.Canvas(nombre_archivo, pagesize=letter)
        page_width, page_height = letter
        margin_left = 50
        margin_right = 50
        reserved_width = 80  # Área fija para los círculos en el margen derecho
        x_reserved = page_width - margin_right - reserved_width  # Inicio del área reservada
        line_height = 12
        padding = 4
        block_spacing = 10  # Espacio entre bloques
    
        y = page_height - 50  # Posición vertical inicial
    
        # Título y encabezado (una sola vez)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin_left, y, "Reporte de Restaurantes")
        y -= 25
        c.setFont("Helvetica-Bold", 10)
        header_text = "Orden: Nombre | Dirección | HORARIO"
        c.drawString(margin_left, y, header_text)
        y -= 20
        c.setFont("Helvetica", 10)
    
        # Definir áreas para el lado izquierdo:
        # Línea 1: nombre y horario
        x_nombre = margin_left
        col_nombre = 100  # ancho reservado para el nombre
        x_horario = x_nombre + col_nombre + 10  # horario se imprime a la derecha del nombre
    
        # Línea 2: dirección
        x_direccion = margin_left
    
        # Línea 3: teléfono y Google Maps
        x_telefono = margin_left
        col_telefono = 60  # ancho para el teléfono
        x_gmaps = x_telefono + col_telefono + 10
    
        # Mapeo del día actual para filtrar el horario (se asume que el JSON tiene días en minúsculas)
        weekday_map = {
            0: "lunes",
            1: "martes",
            2: "miercoles",
            3: "jueves",
            4: "viernes",
            5: "sabado",
            6: "domingo"
        }
        current_day = weekday_map[datetime.datetime.now().weekday()]
    
        for item in datos:
            # Procesar intermediarios: generar lista de tuplas (texto, url)
            intermediarios_info = []
            urls_intermediarios = item.get('urls_intermediarios', None)
            if urls_intermediarios:
                if isinstance(urls_intermediarios, str):
                    try:
                        urls_intermediarios = json.loads(urls_intermediarios)
                    except Exception:
                        urls_intermediarios = [urls_intermediarios]
                if isinstance(urls_intermediarios, list):
                    for url in urls_intermediarios:
                        url_lower = url.lower()
                        if "just-eat" in url_lower:
                            texto = "JustEat"
                        elif "uber" in url_lower:
                            texto = "Uber"
                        elif "glovoapp" in url_lower:
                            texto = "Gloovo"
                        elif "instagram" in url_lower:
                            texto = "Instagram"
                        elif "facebook" in url_lower:
                            texto = "Facebook"
                        else:
                            texto = url
                        intermediarios_info.append((texto, url))
            num_intermediarios = len(intermediarios_info)
            # Ahora tenemos 3 líneas fijas: línea 1 (nombre + horario), línea 2 (dirección), línea 3 (teléfono y Google Maps)
            fixed_lines = 3
            block_line_count = fixed_lines + num_intermediarios
            block_height = block_line_count * line_height + padding
    
            # Si no hay espacio vertical suficiente, pasamos a una nueva página
            if y - block_height < 50:
                c.showPage()
                y = page_height - 50
                c.setFont("Helvetica-Bold", 16)
                c.drawString(margin_left, y, "Reporte de Restaurantes")
                y -= 25
                c.setFont("Helvetica-Bold", 10)
                c.drawString(margin_left, y, header_text)
                y -= 20
                c.setFont("Helvetica", 10)
    
            block_top = y
            block_bottom = y - block_height
    
            # Dibujar el rectángulo del bloque (desde el margen izquierdo hasta el final del área reservada)
            rect_x = margin_left - 2
            rect_y = block_bottom - 2
            rect_width = (x_reserved + reserved_width) - (margin_left - 2)
            rect_height = block_height + 4
            c.rect(rect_x, rect_y, rect_width, rect_height, stroke=1, fill=0)
    
            # --- Línea 1: Nombre y HORARIO ---
            line1_y = block_top - line_height + 2  # ajuste de línea base
            nombre = str(item.get('nombre', ''))
            c.drawString(x_nombre, line1_y, nombre)
            # Procesar el HORARIO (se espera que el campo "horario" sea un JSON con días)
            horario_raw = item.get('horario', '')
            horario_text = ""
            try:
                if isinstance(horario_raw, str):
                    horario_data = json.loads(horario_raw)
                else:
                    horario_data = horario_raw
                if current_day in horario_data:
                    intervals = []
                    for interval in horario_data[current_day]:
                        if len(interval) >= 2:
                            intervals.append(f"{interval[0]}-{interval[1]}")
                    horario_text = ", ".join(intervals)
            except Exception as e:
                horario_text = str(horario_raw)
            c.drawString(x_horario, line1_y, horario_text)
    
            # --- Línea 2: Dirección ---
            line2_y = block_top - 2*line_height + 2
            direccion = str(item.get('direccion', ''))
            c.drawString(x_direccion, line2_y, direccion)
    
            # --- Línea 3: Teléfono y Google Maps ---
            line3_y = block_top - 3*line_height + 2
            telefono = str(item.get('telefono', ''))
            c.setFillColor(red)
            c.drawString(x_telefono, line3_y, telefono)
            c.setFillColor(black)
            googlemaps_link = item.get('link_googlemaps', '')
            if googlemaps_link:
                c.setFillColor(blue)
                gmaps_text = "Google Maps"
                c.drawString(x_gmaps, line3_y, gmaps_text)
                tw = c.stringWidth(gmaps_text, "Helvetica", 10)
                c.linkURL(googlemaps_link, (x_gmaps, line3_y, x_gmaps + tw, line3_y + 10))
                c.setFillColor(black)
    
            # --- Líneas adicionales: Intermediarios ---
            intermediario_y = block_top - 4*line_height + 2
            for texto, url in intermediarios_info:
                c.setFillColor(blue)
                c.drawString(x_telefono, intermediario_y, texto)
                tw = c.stringWidth(texto, "Helvetica", 10)
                c.linkURL(url, (x_telefono, intermediario_y, x_telefono + tw, intermediario_y + line_height))
                c.setFillColor(black)
                intermediario_y -= line_height
    
            # --- Área reservada en el margen derecho ---
            # Se reserva el área [x_reserved, x_reserved + reserved_width] y se divide en dos mitades.
            half_area = reserved_width / 2
            x_circle1 = x_reserved + half_area/2  # centro de la primera mitad
            x_circle2 = x_reserved + half_area + half_area/2  # centro de la segunda mitad
    
            # Dibujar círculos en la primera línea del bloque (line1_y)
            radius = 5
            c.circle(x_circle1, line1_y, radius, stroke=1, fill=0)
            c.circle(x_circle2, line1_y, radius, stroke=1, fill=0)
            # Dibujar etiquetas en la segunda línea del bloque (line2_y)
            c.setFont("Helvetica", 8)
            c.drawCentredString(x_circle1, line2_y - 10, "repartidoderes")
            c.drawCentredString(x_circle2, line2_y - 10, "web")
            c.setFont("Helvetica", 10)
    
            y = block_bottom - block_spacing
    
        c.save()
        print(f"✅ PDF generado: {nombre_archivo}")
        return nombre_archivo



    def contar_caracteres_intermediarios(self,url):
        """
        Extrae y cuenta los caracteres a partir de "https://www." en un link.
        """
        match = re.search(r"https://www\.(.+)", url)
        if match:
            return len(match.group(1))  # Devuelve la cantidad de caracteres después de "https://www."
        return 0  # Si no hay coincidencia, devuelve 0
        def insertar_restaurantes_justeat(self, id_lugar, restaurantes):
            """
            Inserta una lista de restaurantes en la tabla JusteatRestaurantes usando link_justeat y nombre.
            Genera un nuevo id_justeat (auto_increment) para cada registro insertado.
            """
            query = """
            INSERT INTO JusteatRestaurantes (link_justeat, nombre, id_lugar)
            VALUES (%s, %s, %s)
            """
            try:
                for restaurante in restaurantes:
                    self.cursor.execute(query, (restaurante.url, restaurante.nombre, id_lugar))
                self.conexion.commit()
                print(f"✅ {len(restaurantes)} restaurantes insertados en JusteatRestaurantes (mínimo).")
            except mysql.connector.Error as err:
                print(f"❌ Error al insertar restaurantes en JustEat (mínimo): {err}")
    def update_nombre(self, id_justeat, nuevo_nombre):
        """
        Actualiza el nombre del restaurante en la base de datos para un ID específico de JustEat.
        """
        try:
            query = "UPDATE GoogleMapsRestaurantes SET nombre = %s WHERE id_justeat = %s"
            self.cursor.execute(query, (nuevo_nombre, id_justeat))
            self.conexion.commit()
            print(f"[DB] Nombre actualizado correctamente para ID {id_justeat}")
        except Exception as e:
            print(f"[DB] Error al actualizar el nombre para ID {id_justeat}: {e}")


    def insertar_urls_por_lugar(self, id_lugar, registros):
        """
        Inserta una lista de registros en la tabla urls_porlugar.
        
        Cada registro debe ser un dict con:
          - "url": la URL de JustEat (url_justeat)
          - "nombre": el nombre del establecimiento
        """
        query = """
        INSERT INTO urls_porlugar (id_lugar, url_justeat, nombre)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE id_lugar = VALUES(id_lugar)
        """
        try:
            for registro in registros:
                self.cursor.execute(query, (
                    id_lugar,
                    registro["url"],
                    registro["nombre"]
                ))
            self.conexion.commit()
            print(f"✅ {len(registros)} registros insertados/actualizados en urls_porlugar para id_lugar {id_lugar}.")
        except mysql.connector.Error as err:
            print(f"❌ Error al insertar en urls_porlugar: {err}")

    def obtener_urls(self):
        """
        Recupera todos los registros de la tabla urls_porlugar.
        """
        query = "SELECT * FROM urls_porlugar"
        try:
            self.cursor.execute(query)
            registros = self.cursor.fetchall()
            print(f"✅ Se han obtenido {len(registros)} registros de urls_porlugar.")
            return registros
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener registros de urls_porlugar: {err}")
            return [] 

    def get_Google_en_cola(self, max_registros):
        """
        Devuelve los registros de JusteatRestaurantes que cumplan la condición (por ejemplo, identidad > 0)
        limitando a 'max_registros'.
        """
        query = f"""
            SELECT *
            FROM JusteatRestaurantes
            WHERE interesa > 0
            LIMIT {max_registros};
        """
        try:
            self.cursor.execute(query)
            registros = self.cursor.fetchall()
            print(f"✅ Se han obtenido {len(registros)} registros.")
            return registros
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener registros: {err}")
            return []

    def insertar_googlemaps_restaurante(self, datos):
        """
        Inserta en GoogleMapsRestaurantes el id_justeat y nombre; el resto se deja a NULL por defecto.
        """
        query = """
                INSERT INTO GoogleMapsRestaurantes (id_justeat, nombre)
                VALUES (%s, %s)
            """
        valores = (datos['id_lugar'], datos['nombre'])
        try:
            print(f"----------------------------------------------------------------")
            self.cursor.execute(query, valores)
            print(f"✅siiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")
            self.conexion.commit()
        except mysql.connector.Error as err:
            print(f"❌ Error al insertar en GoogleMapsRestaurantes: {err}")
            raise

    def update_interesa(self, id_justeat, datos_actualizados):
        """
        Toma el identificador y un diccionario con los datos actualizados obtenidos
        de Google (por ejemplo: 'direccion_encontrada', 'telefono_encontrado', 'rango_precios',
        'link', 'intermediarios' y 'links_externos') y actualiza la fila correspondiente
        en la tabla GoogleMapsRestaurantes. Además, se actualiza el campo 'interesa' a 2,
        indicando que el registro ha sido procesado.
    
        Parámetros:
          - id_justeat: ID del restaurante en Just Eat.
          - datos_actualizados: dict con los campos actualizados (ajústalo según tu esquema).
    
        Ejemplo:
          {
             "direccion_encontrada": "C. Sagunto, 3, 11300 La Línea de la Concepción, Cádiz",
             "telefono_encontrado": "123456789",
             "rango_precios": "€€",
             "link": "https://www.google.es/maps/...",
             "intermediarios": 3,
             "links_externos": ["https://...", "https://..."]
          }
        """
        query = """
            UPDATE GoogleMapsRestaurantes
            SET direccion_encontrada = %s,
                telefono_encontrado = %s,
                rango_precios = %s,
                link = %s,
                intermediarios = %s,
                links_externos = %s,
                interesa = %s
            WHERE id_justeat = %s
        """
        valores = (
            datos_actualizados.get("direccion_encontrada"),
            datos_actualizados.get("telefono_encontrado"),
            datos_actualizados.get("rango_precios"),
            datos_actualizados.get("link"),
            datos_actualizados.get("intermediarios"),
            json.dumps(datos_actualizados.get("links_externos", [])),
            2,  # Se marca el registro procesado
            id_justeat
        )
        try:
            self.cursor.execute(query, valores)
            self.conexion.commit()
            print(f"✅ Registro para id_justeat {id_justeat} actualizado en GoogleMapsRestaurantes.")
        except mysql.connector.Error as err:
            print(f"❌ Error al actualizar GoogleMapsRestaurantes para id_justeat {id_justeat}: {err}")
            raise
 

    def actualizar_horarios(self, restaurantes_json):
        """
        Recorre una lista de entidades (en formato JSON) de GoogleRestaurantes, procesa el campo "calendario"
        para extraer los intervalos de horarios usando HorarioProcessor y actualiza en la base de datos la columna
        "horario" con el resultado (almacenado como JSON). Además, fija el campo "interesa" a 4 si hay horario.
        Si no hay horario pero existe 'link_googlemaps', actualiza "interesa" a -1.
        """
        print(restaurantes_json)
        updates_count = 0  # Contador de actualizaciones realizadas
    
        for restaurante in restaurantes_json:
            # Extraemos el texto del campo calendario
            calendario_text = restaurante.get('calendario', '')
            restaurant_id = restaurante.get('id_googlemaps')
    
            if not restaurant_id:
                continue  # Si no hay ID, no se puede actualizar
    
            if calendario_text:  
                # Si hay calendario, procesamos el horario
                processor = HorarioProcessor(calendario_text)
                horario_dict = processor.procesar()
                horario_json = json.dumps(horario_dict)
    
                # Query para actualizar horario y fija "interesa" a 4
                query = "UPDATE GoogleMapsRestaurantes SET horario = %s, interesa = 4 WHERE id_googlemaps = %s"
                params = (horario_json, restaurant_id)
    
            elif restaurante.get('link_googlemaps', ''):
                # Si no hay horario pero sí link_googlemaps, actualiza interesa a -1
                query = "UPDATE GoogleMapsRestaurantes SET horario = %s, interesa = -1 WHERE id_googlemaps = %s"
                params = (None, restaurant_id)  # Se guarda NULL en horario
    
            else:
                continue  # Si no hay calendario ni link_googlemaps, se omite
    
            # Ejecutar la consulta
            self.cursor.execute(query, params)
    
            # Verificar si se actualizó alguna fila
            affected = self.cursor.rowcount
            if affected > 0:
                print(f"Actualizado restaurante id {restaurant_id}")
                updates_count += affected
            else:
                print(f"No se actualizó restaurante id {restaurant_id}")
    
        # Confirmar cambios en la base de datos
        self.conexion.commit()
        print(f"Total de actualizaciones realizadas: {updates_count}")


    def set_interesa(self, id_justeat, interesa_value):
        """
        Actualiza la columna 'interesa' en la tabla GoogleMapsRestaurantes para el restaurante
        identificado por 'id_justeat', asignándole el valor numérico proporcionado.
    
        Parámetros:
          - id_justeat: Identificador del restaurante (campo 'id_justeat').
          - interesa_value: Número que se asignará a la columna 'interesa'.
        """
        query = "UPDATE GoogleMapsRestaurantes SET interesa = %s WHERE id_justeat = %s"
        self.cursor.execute(query, (interesa_value, id_justeat))
        
        affected = self.cursor.rowcount
        if affected > 0:
            print(f"Actualizado restaurante con id_justeat {id_justeat} a interesa: {interesa_value}")
        else:
            print(f"No se actualizó ningún restaurante con id_justeat {id_justeat}")
        
        self.conexion.commit()

    def get_interesa(self, interesa_value):
        query = "SELECT * FROM GoogleMapsRestaurantes WHERE id_lugar IN (     SELECT    id_lugar  FROM Lugar     WHERE provincia = 'Madrid' AND tipo = 2 );"
        self.cursor.execute(query)
        resultados = self.cursor.fetchall()
        if resultados:
            print(f"Mostrando restaurantes con interesa: {interesa_value}")
        else:
            print("No se encontró ningún restaurante con ese valor de interesa")
        return resultados

        
        self.conexion.commit()
    def get_justEat_en_cola(self, max):
        """
        Devuelve los registros de JusteatRestaurantes con 'interesa = -1',
        ordenados de menor a mayor frecuencia de 'nombre'.
        """
        query = f"""
            SELECT * FROM (   SELECT *,           ROW_NUMBER() OVER (PARTITION BY telefono) AS rn   FROM GoogleMapsRestaurantes ) AS sub WHERE rn = 1 LIMIT {max};
        """
        try:
            self.cursor.execute(query)
            registros = self.cursor.fetchall()
            print(f"✅ Se han obtenido {len(registros)} registros.")
            return registros
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener registros: {err}")
            return []
    def get_JustEat_by_id(self, id_justeat):
        """
        Devuelve el registro (objeto o diccionario) de JustEatRestaurantes correspondiente al id dado.
        """
        query = "SELECT * FROM JustEatRestaurantes WHERE id_justeat = %s;"
        try:
            self.cursor.execute(query, (id_justeat,))
            registro = self.cursor.fetchone()
            return registro
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener JustEatRestaurantes con id {id_justeat}: {err}")
            return None

    def get_justEat_compilar(self):
        """
        Obtiene los registros de JusteatRestaurantes con 'interesa = 2' 
        cuyo id_justeat aparece en GoogleMapsRestaurantes y donde 'completo' es FALSE.
        """
        query = """SELECT j.*
    FROM JusteatRestaurantes j
    WHERE j.interesa = 1
      AND j.id_justeat IN (
        SELECT g.id_justeat
        FROM GoogleMapsRestaurantes g
        WHERE g.interesa = 0
      );
        """
        try:
            self.cursor.execute(query)
            registros = self.cursor.fetchall()
            print(f"✅ Se han obtenido {len(registros)} registros de JusteatRestaurantes con completo = FALSE en GoogleMapsRestaurantes.")
            return registros
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener registros: {err}")
            return []


    def get_justEat_localizados(self):
        """
        Obtiene los registros de GoogleMapsRestaurantes donde link_googlemaps NO es NULL 
        y devuelve la lista de objetos JustEatRestaurantes correspondientes (usando su id).
        """
        query = "SELECT * FROM GoogleMapsRestaurantes WHERE link_googlemaps IS NOT NULL;"
        try:
            self.cursor.execute(query)
            registros = self.cursor.fetchall()
            print(f"✅ Se han obtenido {len(registros)} registros con link_googlemaps IS NOT NULL.")
            resultado = []
            for reg in registros:
                id_justeat = reg['id_justeat'] if isinstance(reg, dict) else reg[1]
                justeat_obj = self.get_JustEat_by_id(id_justeat)
                if justeat_obj is not None:
                    resultado.append(justeat_obj)
            return resultado
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener registros: {err}")
            return []

    def get_justEat_sin_asignar(self):
        """
        Obtiene los registros de JusteatRestaurantes con 'interesa = -1'.
        """
        query = "SELECT * FROM JusteatRestaurantes WHERE interesa = -1;"
        try:
            self.cursor.execute(query)
            registros = self.cursor.fetchall()
            print(f"✅ Se han obtenido {len(registros)} registros de urls_porlugar.")
            return registros
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener registros de urls_porlugar: {err}")
            return []
    def get_calendario(self):
        """
        Obtiene los registros de JusteatRestaurantes con 'interesa = -1'.
        """
        query = "SELECT calendario FROM GoogleMapsRestaurantes WHERE calendario IS NOT NULL"
        try:
            self.cursor.execute(query)
            registros = self.cursor.fetchall()
            print(f"✅ Se han obtenido {len(registros)} registros de calendario.")
            return registros
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener calendario de urls_porlugar: {err}")
            return []

    def get_justEat_descartados(self):
        """
        Obtiene los registros de JusteatRestaurantes con 'interesa = 0'.
        """
        query = "SELECT * FROM JusteatRestaurantes WHERE interesa = 0;"
        try:
            self.cursor.execute(query)
            registros = self.cursor.fetchall()
            print(f"✅ Se han obtenido {len(registros)} registros de urls_porlugar.")
            return registros
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener registros de urls_porlugar: {err}")
            return []

    def update_restaurante_con_datos(self, datos):
        """
        Actualiza las columnas (nombre, direccion, cp, estrellas, comentarios, horario)
        en la tabla JusteatRestaurantes para el id_justeat dado, y pone 'interesa' a 1.
        """
        horario_json = json.dumps(datos['horario'], ensure_ascii=False) if datos['horario'] else None
    
        query = """
            UPDATE JusteatRestaurantes
            SET nombre=%s,
                direccion=%s,
                cp=%s,
                estrellas=%s,
                comentarios=%s,
                horario=%s,
                interesa=1
            WHERE id_justeat=%s
        """
        values = (
            datos['nombre'],
            datos['direccion'],
            datos['cp'],
            datos['estrellas'],
            datos['comentarios'],
            horario_json,
            datos['id_justeat']
        )
    
        try:
            self.cursor.execute(query, values)
            self.conexion.commit()
            print(f"Datos de ID {datos['id_justeat']} actualizados correctamente en la BBDD. (interesa=1)")
        except Exception as e:
            print(f"Error al actualizar el ID {datos['id_justeat']}: {e}")

    def insertar_lugares(self, lugares_por_provincia):
        """
        Inserta una lista de lugares en la tabla 'Lugar'.
        :param lugares_por_provincia: Diccionario con provincias como claves y listas de objetos Lugar como valores.
        """
        query = """
        INSERT INTO Lugar (provincia, municipio, codigo_postal, completo) 
        VALUES (%s, %s, %s, %s)
        """  
        try:
            datos_a_insertar = [
                (lugar.provincia, lugar.municipio, lugar.codigo_postal, False)
                for lugares in lugares_por_provincia.values()
                for lugar in lugares
            ]
            
            if datos_a_insertar:
                self.cursor.executemany(query, datos_a_insertar)
                self.conexion.commit()
                print(f"✅ {len(datos_a_insertar)} lugares insertados en la base de datos.")
            else:
                print("⚠ No hay datos para insertar.")
        except mysql.connector.Error as err:
            print(f"❌ Error al insertar lugares: {err}")
    def update_google_resultados(self, id_justeat, datos_resultados):
        """
        Actualiza en la tabla GoogleMapsRestaurantes los datos extraídos de Google para el restaurante
        identificado por id_justeat. Se esperan las siguientes claves en datos_resultados:
          - telefono_encontrado
          - direccion_encontrada
          - rango_precios
          - link         (link obtenido de Google Maps)
          - intermediarios
          - links_externos (lista de enlaces externos)
          - horario      (opcional, puede ser None)
        Además, se marca el registro con interesa = 2.
        """
        query = """
            UPDATE GoogleMapsRestaurantes
            SET 
                telefono = %s,
                direccion_encontrada = %s,
                rango_precios = %s,
                link_googlemaps = %s,
                intermediarios = %s,
                links_externos = %s,
                horario = %s,
                interesa = %s
            WHERE id_justeat = %s
        """
        valores = (
            datos_resultados.get("telefono_encontrado"),
            datos_resultados.get("direccion_encontrada"),
            datos_resultados.get("rango_precios"),
            datos_resultados.get("link"),
            datos_resultados.get("intermediarios"),
            json.dumps(datos_resultados.get("links_externos", [])),
            datos_resultados.get("horario"),  # Puede ser None si no se extrajo horario
            2,  # Se marca como procesado
            id_justeat
        )
        try:
            self.cursor.execute(query, valores)
            self.conexion.commit()
            print(f"✅ Actualización exitosa para id_justeat {id_justeat}.")
        except mysql.connector.Error as err:
            print(f"❌ Error al actualizar id_justeat {id_justeat}: {err}")
            raise

    def update_interesa(self, id_justeat, datos_actualizados):
        """
        Actualiza en GoogleMapsRestaurantes los campos obtenidos de Google,
        y establece 'interesa' a 2 para indicar que se ha realizado el upgrade.
        Se esperan las siguientes claves en datos_actualizados:
          - direccion_encontrada
          - telefono_encontrado
          - rango_precios
          - link
          - intermediarios
          - links_externos  (lista, que se almacena en JSON)
          - horario         (opcional, puede ser None)
        """
        query = """
            UPDATE GoogleMapsRestaurantes
            SET direccion_encontrada = %s,
                telefono_encontrado = %s,
                rango_precios = %s,
                link = %s,
                intermediarios = %s,
                links_externos = %s,
                horario = %s,
                interesa = %s
            WHERE id_justeat = %s
        """
        valores = (
            datos_actualizados.get("direccion_encontrada"),
            datos_actualizados.get("telefono_encontrado"),
            datos_actualizados.get("rango_precios"),
            datos_actualizados.get("link"),
            datos_actualizados.get("intermediarios"),
            json.dumps(datos_actualizados.get("links_externos", [])),
            datos_actualizados.get("horario"),  # puede ser None si no se encontró
            1,  # Marca como procesado
            id_justeat
        )
        try:
            self.cursor.execute(query, valores)
            self.conexion.commit()
            print(f"✅ Registro para id_justeat {id_justeat} actualizado en GoogleMapsRestaurantes.")
        except mysql.connector.Error as err:
            print(f"❌ Error al actualizar GoogleMapsRestaurantes para id_justeat {id_justeat}: {err}")
            raise

    def asignar_id_lugar_si_existe(self, link_justeat, id_lugar):
        """
        Actualiza el campo id_lugar de un restaurante existente en JusteatRestaurantes, 
        identificado por su link_justeat.
        """
        query_check = "SELECT id_justeat FROM JusteatRestaurantes WHERE link_justeat = %s"
        try:
            self.cursor.execute(query_check, (link_justeat,))
            result = self.cursor.fetchone()
            if result:
                query_update = "UPDATE JusteatRestaurantes SET id_lugar = %s WHERE link_justeat = %s"
                self.cursor.execute(query_update, (id_lugar, link_justeat))
                self.conexion.commit()
                print(f"✅ Restaurante con link '{link_justeat}' actualizado con id_lugar {id_lugar}.")
            else:
                print(f"ℹ️ No se encontró un restaurante con link '{link_justeat}'. No se realizó actualización.")
        except mysql.connector.Error as err:
            print(f"❌ Error al asignar id_lugar al restaurante con link '{link_justeat}': {err}")

    def insertar_restaurantes_no_completos(self, id_lugar, restaurantes_incompletos):
        """
        Inserta restaurantes incompletos en JusteatRestaurantes. [**Posible borrador, ajustar según tu lógica**]
        """
        query = """ 
        (id_justeat, id_lugar, nombre, link_justeat)
        INSERT INTO JusteatRestaurantes (link_justeat, nombre, direccion, estrellas, completo, id_lugar)
        VALUES (NULL, %s, %s, %s)
        """
        try:
            for restaurante in restaurantes_incompletos:
                self.cursor.execute(query, (id_lugar, restaurante.nombre, restaurante.url))
            self.conexion.commit()
            print(f"✅ {len(restaurantes_incompletos)} restaurantes incompletos insertados en RestaurantesNoCompletos.")
        except mysql.connector.Error as err:
            print(f"❌ Error al insertar restaurantes incompletos: {err}")
            
 
            
            
    def todos_cp(self):
        query="SELECT DISTINCT codigo_postal FROM Lugar;"
        try:
            self.cursor.execute(query)
            no_completos = self.cursor.fetchall()
            return no_completos
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener lugares incompletos: {err}")
            return None
    def buscar(self,a):
        query=f"SELECT * FROM Lugar WHERE codigo_postal = '{a}';                  ;"
        try:
            self.cursor.execute(query)
            no_completos = self.cursor.fetchall()
            return no_completos
        except mysql.connector.Error as err:
            print(f"❌ Error al obtener lugares incompletos: {err}")
            return None
if __name__ == '__main__':
    db = DatabaseManager(host="localhost", user="root", password="collado", database="restaurantes_db")
    a=db.todos_cp()
    b=[]
    cps = [str(row['codigo_postal']) for row in a]
    for cp in cps: 
        print(cp,',********************')
        b.append(db.buscar(cp))
        
            
    print(len(a))