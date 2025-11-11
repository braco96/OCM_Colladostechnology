from bbdd import DatabaseManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class ContrasteDeDatos:
    def __init__(self, driver, lista_restaurantes):
        self.driver = driver
        self.lista_restaurantes = lista_restaurantes
        self.resultados = []

    def aceptar_cookies(self):
        try:
            boton_aceptar = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Aceptar todo')]"))
            )
            boton_aceptar.click()
            print("✔ Cookies aceptadas.")
            time.sleep(2)
        except:
            pass

    def analizar_botones(self):
        """ 
        Busca todos los <button> de la página y recoge:
        - aria-label (o texto del botón) como clave
        - la referencia al botón en un diccionario
        
        Si un botón contiene las palabras clave ('pedido', 'comprar', 'reservar'), abrimos su contenido
        en la nueva pestaña/ventana (si se genera), contamos cuántos botones hay y la cerramos.
        """
        # Esperar un poco para que la página y botones terminen de cargar
        time.sleep(2)
        botones = self.driver.find_elements(By.TAG_NAME, "button")
        info_botones = {}
        intermediarios = 0

        for boton in botones:
            try:
                texto = boton.get_attribute("aria-label") or boton.text.strip()
                if not texto:
                    continue
                info_botones[texto] = boton

                # Si es un botón relacionado con pedido, compra o reserva
                if any(palabra in texto.lower() for palabra in ["pedido", "comprar", "reservar"]):
                    # Guardamos pestañas abiertas antes de hacer clic
                    pestañas_antes = self.driver.window_handles

                    boton.click()
                    time.sleep(3)

                    # Revisamos si se abrió una nueva pestaña/ventana
                    pestañas_despues = self.driver.window_handles
                    if len(pestañas_despues) > len(pestañas_antes):
                        # Cambiamos foco a la nueva pestaña
                        nueva_pestaña = list(set(pestañas_despues) - set(pestañas_antes))[0]
                        self.driver.switch_to.window(nueva_pestaña)

                        # Contamos sus botones
                        num_botones = len(self.driver.find_elements(By.TAG_NAME, "button"))
                        intermediarios = num_botones

                        # Cerramos la pestaña emergente
                        self.driver.close()
                        # Volvemos a la pestaña anterior
                        self.driver.switch_to.window(pestañas_antes[0])
                    else:
                        # Si no abre nueva pestaña, puede que sea un popup en la misma pestaña
                        # Podríamos buscar un botón de 'cerrar' dentro de la misma página si fuera el caso.
                        # Aquí, a modo de ejemplo, volvemos atrás.
                        time.sleep(1)
                        self.driver.back()
                        time.sleep(2)
            except:
                # Ignorar cualquier error puntual al analizar este botón
                continue

        return info_botones, intermediarios

    def extraer_datos_restaurante(self):
        """
        Se encarga de analizar los botones una vez la página está cargada
        y extraer del aria-label (u otro texto) el teléfono, dirección y rango de precios.
        """
        info_botones, _ = self.analizar_botones()
        data = {"telefono": None, "direccion": None, "rango_precios": None}

        for texto in info_botones:
            # Extraer teléfono
            if "Teléfono" in texto:
                data["telefono"] = texto.split(":")[-1].strip()

            # Extraer dirección
            elif "Dirección" in texto:
                data["direccion"] = texto.split(":")[-1].strip()

            # Si contiene símbolo €, podría ser rango de precios
            elif "€" in texto:
                data["rango_precios"] = texto.strip()

        return data

    def buscar_en_google_maps(self):
        """
        Abre Google Maps en una nueva pestaña, busca cada restaurante y
        tras esperar a que aparezca la información, extrae los datos.
        """
        # Abrimos Maps en una nueva pestaña
        self.driver.execute_script("window.open('about:blank','_blank');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get("https://www.google.es/maps")
        time.sleep(3)

        # Aceptar cookies
        self.aceptar_cookies()

        for restaurante in self.lista_restaurantes:
            nombre = restaurante['nombre']
            direccion = restaurante.get('direccion', '')

            print(f"\n🔍 Buscando: {nombre}")

            try:
                # Buscar en el input
                buscador = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "searchboxinput"))
                )
                buscador.clear()
                buscador.send_keys(nombre + " " + direccion)

                # Clic en botón de búsqueda
                boton_buscar = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "searchbox-searchbutton"))
                )
                boton_buscar.click()

                # Esperar a que aparezca algo que indique que el resultado se cargó
                # Por ejemplo, el botón de 'Dirección'.
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'Dirección')]"))
                )

                # Extraer datos
                datos_restaurante = self.extraer_datos_restaurante()
                link_actual = self.driver.current_url

                # Volvemos a analizar los botones (así obtenemos intermediarios también).
                _, intermediarios = self.analizar_botones()

                self.resultados.append({
                    'Base': restaurante,
                    'restaurante': nombre,
                    'direccion': datos_restaurante['direccion'],
                    'telefono': datos_restaurante['telefono'],
                    'rango_precios': datos_restaurante['rango_precios'],
                    'link': link_actual,
                    'intermediarios': intermediarios
                })

                # Volver a la pantalla anterior para limpiar la búsqueda
                self.driver.back()
                time.sleep(2)

            except Exception as e:
                print(f"⚠ Error al buscar {nombre}: {e}")

        # Cerrar la pestaña de Maps y volver a la principal
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    def mostrar_resultados(self):
        print("\n📊 RESULTADOS OBTENIDOS:")
        for res in self.resultados:
            print(f"\nNombre: {res['restaurante']}")
            print(f"Dirección: {res['direccion']}")
            print(f"Teléfono: {res['telefono']}")
            print(f"Rango de precios: {res['rango_precios']}")
            print(f"Google Maps: {res['link']}")
            print(f"Intermediarios detectados: {res['intermediarios']}")
            print("---------------------------------")

# Uso del código:
if __name__ == "__main__":
    # Crear e inicializar el driver de Chrome
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    # Instancia de DatabaseManager
    db_manager = DatabaseManager(
        host="localhost",
        user="root",
        password="collado",
        database="restaurantes_db_copy"
    )
    
    # Obtener lista de restaurantes desde la base de datos
    completos = db_manager.get_justEat_localizados()

    # Crear instancia de ContrasteDeDatos con el driver
    contraste = ContrasteDeDatos(driver, completos)

    # Ejecutar la búsqueda
    contraste.buscar_en_google_maps()

    # Mostrar resultados
    contraste.mostrar_resultados()

    # Cerrar driver al finalizar
    driver.quit()
