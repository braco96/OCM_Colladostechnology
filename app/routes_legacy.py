from flask import Flask, render_template, jsonify, request
from bbdd import DatabaseManager#conda install -c anaconda mysql-connector-python
db = DatabaseManager(host="localhost", user="root", password="collado", database="restaurantes_db")
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Nuevo_Just_Eat import JustEatScraper
from contraste import ContrasteDeDatos
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from horario import HorarioProcessor
from whatsapp import whatsapp
import json 
import threading
from flask import send_file
from datetime import datetime
def obtener_fecha_hora_actual():
    """Devuelve la fecha y hora actual en formato 'YYYY-MM-DD HH:MM:SS'"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

app = Flask(__name__)

# Ejemplo de uso
fecha_hora = obtener_fecha_hora_actual()
print(fecha_hora)
# Configuración de la base de datos
db = DatabaseManager(host="localhost", user="root", password="collado", database="restaurantes_db")
mostrar=True
# Página padre
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/api/procesar_whatsapp', methods=['POST'])
def api_procesar_whatsapp():
    data = request.get_json()
    if not data or 'datos' not in data:
        return jsonify({"error": "No se enviaron datos"}), 400

    lista_restaurantes = data['datos']

    try:
        whatsapp_obj = whatsapp(lista_restaurantes)
        print("Objeto whatsapp creado")
        whatsapp_obj.abrir_whatsapp_web()
        print("Whatsapp Web abierto")
        whatsapp_obj.visitar_numeros()
        print("Visita de números completada")
        return jsonify({"mensaje": "Mensajes de WhatsApp procesados correctamente."})
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": f"Error al procesar WhatsApp: {str(e)}"}), 500



@app.route('/api/generar_pdf', methods=['POST'])
def api_generar_pdf():
    data = request.get_json()
    if not data or 'datos' not in data:
        return jsonify({"error": "No se enviaron datos"}), 400

    lista_datos = data['datos']
    # Llamamos al método generar_pdf de la base de datos
    nombre_pdf = db.generar_pdf(lista_datos, "reporte.pdf")
    
    try:
        return send_file(nombre_pdf, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"Error al enviar el archivo: {e}"}), 500
# Página para "Lista de Trabajo"
@app.route('/lista_de_trabajo')
def lista_de_trabajo():
    return render_template('lista_de_trabajo.html')

@app.route('/telefonos')
def mostrar_telefonos():  # ✅ Nombre único
    return render_template('moviles.html')


# Endpoint para obtener datos de lista de trabajo 
@app.route('/cuestionario', methods=['GET'])
def cuestionario():
    return render_template('cuestionario.html')

 
@app.route('/restaurantes_movil', methods=['GET'])
def obtener_movil(): 
    # Se obtienen los registros (por ejemplo, 200) de la base de datos
    restaurantes =db.candidatos_con_movil(50) 
    print(len(restaurantes))
    return jsonify(restaurantes)

@app.route('/restaurantes_google', methods=['GET'])
def obtener_Google(): 
    # Se obtienen los registros (por ejemplo, 200) de la base de datos
    #restaurantes =db.candidatos_con_movil(2000)
    restaurantes = db.get_interesa(5)
    
    return jsonify(restaurantes)


@app.route('/restaurantes_activo', methods=['GET'])
def obtener_restaurantes():
    restaurantes = db.get_interesa(5)
    return jsonify(restaurantes)
# Endpoint para recibir datos procesados (usado si se envían acciones que no sean procesamiento)
@app.route('/recibir_datos', methods=['POST'])
def recibir_datos():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400

    accion = data.get('accion')
    if not accion:
        return jsonify({"error": "No se especificó la acción (botón)"}), 400

    datos_recibidos = data.get('datos')
    if datos_recibidos is None:
        return jsonify({"error": "No se enviaron datos específicos"}), 400

    print(f"Acción recibida: {accion}")
    print("Datos recibidos:")
    print(datos_recibidos)

    return jsonify({"mensaje": f"Datos recibidos para la acción '{accion}' y mostrados en consola"}), 200

# Página para "Captar Nuevos Datos"
@app.route('/captar_nuevos_datos')
def captar_nuevos_datos():
    return render_template('captar_nuevos_datos.html')
 

# Nuevo endpoint para obtener restaurantes NO completos
@app.route('/restaurantes_no_completos_Google', methods=['GET'])
def obtener_restaurantes_no_completos_Google():
    restaurantes = db.obtener_restaurantes_no_completos(200)
    print(f"DEBUG: Total restaurantes : {len(restaurantes)}")
    return jsonify(restaurantes)
resultados_finales = []
enlaces=[]
raspado=[]
@app.route('/api/procesar_datos_Google', methods=['POST'])
def api_procesar_datos_Google():
    data = request.get_json()
    if not data or 'datos' not in data:
        return jsonify({"error": "No se enviaron datos"}), 400

    lista_restaurantes = data['datos']
    

    # Crear driver sólo una vez
    
    chrome_options = Options()
   
      
    for cp in lista_restaurantes:
            raspa = {
                'url_google': cp.get('url_google', ''),
                'fecha_inicio': cp.get('fecha_inicio', ''),
                'fecha_fin': cp.get('fecha_fin', ''),
                'nombre': cp.get('nombre', ''),
                'id_palabra': cp.get('id_palabra'),
                'id_lugar': cp.get('id_lugar'),
                'id_unico': cp.get('id_unico'),  # Asegúrate de que este campo exista en "cp"
                'completado': cp.get('completado', 1),
                'interesa': cp.get('interesa', 0)-1,
                'cp':cp.get('cp', ''),
                'provincia':cp.get('provincia', '')
            }
            raspa['fecha_inicio']=obtener_fecha_hora_actual()
            
            # Obtener lugares incompletos por id_lugar 
            # Si devuelve None, pasar al siguiente
            
            # Crear instancia de ContrasteDeDatos (pasando lista completa y db)
           # contraste = ContrasteDeDatos(driver, str(cdp[0]['codigo_postal']))
            contraste = ContrasteDeDatos(None, raspa,db.obtener_pasados())
            
            contraste.buscar_en_google_maps()
            raspa['url_google']=json.dumps(contraste.enlaces)
            raspa['fecha_fin']=obtener_fecha_hora_actual()
            # Guardar resultados 
            resultados_finales.append(contraste.resultados)
            db.actualizar_raspado(raspa)
            db.insertar_resultados(contraste.resultados)
            
            raspado.append(raspa)  
        # Devolver todos los resultados al final
    return jsonify(resultados_finales)
    
     
 
@app.route('/procesar_calendario')
def procesar_calendario():
    return render_template('procesar_calendario.html')
@app.route('/restaurantes_en_proceso', methods=['GET'])
def obtener_restaurantes_en_proceso():
    # Se obtienen los restaurantes cuyo campo "interesa" es igual a 5
    restaurantes = db.get_interesa(5)
    return jsonify(restaurantes)

@app.route('/restaurantes_finalizados', methods=['GET'])
def obtener_restaurantes_finalizados():
    # Se obtienen los restaurantes cuyo campo "interesa" es igual a -4
    restaurantes = db.get_interesa(-4)
    return jsonify(restaurantes)

@app.route('/api/procesar_horarios', methods=['POST'])
def api_procesar_horarios():
    data = request.get_json()
    if not data or 'datos' not in data:
        return jsonify({"error": "No se enviaron datos"}), 400

    # Si se envió la acción "procesar_horario", actualizamos los horarios
    accion = data.get('accion', '')
    if accion == 'procesar_horario':
        lista_restaurantes = data['datos']
        db.actualizar_horarios(lista_restaurantes)
        return jsonify({"mensaje": "Horarios actualizados correctamente"})
    else:
        return jsonify({"error": "Acción no reconocida"}), 400

@app.route('/api/procesar_llamadas', methods=['POST'])
def api_procesar_llamadas():
    from flask import request, jsonify
    data = request.get_json()
    if not data or 'id_justeat' not in data or 'estado' not in data:
        return jsonify({"error": "Datos incompletos"}), 400

    id_justeat = data['id_justeat']
    estado = data['estado'].lower()
    # Si el estado es "interesado", asignamos 5; de lo contrario, -4.
    interesa_value = 5 if estado == "interesado" else -4

    # Llama a la función de la base de datos para actualizar "interesa"
    db.set_interesa(id_justeat, interesa_value)

    return jsonify({"mensaje": f"Restaurante {id_justeat} actualizado con interesa {interesa_value}"})

@app.route('/restaurantes_no_completos_JustEat', methods=['GET'])
def obtener_restaurantes_no_completos_JustEat():
    restaurantes = db.get_justEat_en_cola(200)
    print('hay : ',len(restaurantes))
    return jsonify(restaurantes)

# Nuevo endpoint para procesar los datos seleccionados con ContrasteDeDatos
@app.route('/api/procesar_datos_JustEat', methods=['POST'])
def api_procesar_datos_JustEat():
    data = request.get_json()
    if not data or 'datos' not in data:
        return jsonify({"error": "No se enviaron datos"}), 400

    # La lista enviada contiene los registros seleccionados (objetos JSON)
    lista_restaurantes = data['datos']

    chrome_options = Options() 
    if(mostrar):
        chrome_options.add_argument("--headless")  # Activa el modo headless
        chrome_options.add_argument("--disable-gpu")  # Opcional, mejora el rendimiento en algunas máquinas
        chrome_options.add_argument("--no-sandbox")  # Útil en entornos Linux
        chrome_options.add_argument("--disable-dev-shm-usage")  # Para evitar problemas de memoria compartida en Linux
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Procesar los datos seleccionados

    # Procesar los datos seleccionados
    scraper = JustEatScraper(driver,lista_restaurantes,db)
    
    resultados=scraper.ejecutar_scraper()
    scraper.cerrar()

    driver.quit()

    return jsonify(scraper.lista)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
  