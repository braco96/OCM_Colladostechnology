import time
import difflib
import json
import re
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bbdd import DatabaseManager  # Se asume que en bbdd.py se define DatabaseManager
import threading
import time
from selenium.webdriver.common.by import By
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
mostrar=False
# Función para gestionar la ejecución en hilos


def is_external_link(href):
    """
    Determina si 'href' apunta a un enlace externo:
    Se considera externo todo dominio que NO contenga 'google'.
    """
    if not href or not href.startswith("http"):
        return False
    parsed = urlparse(href)
    domain = parsed.netloc.lower()
    return ("google" not in domain)
class ContrasteDeDatos:
    def __init__(self, driver):
        self.driver = driver
        self.resultados=[]
        # ... (otros inicializadores)

    # ... (otros métodos existentes)

    def scroll_y_coger_enlaces(self, max_intentos=50, pause_segundos=1):
        enlaces_en_orden = []
        enlaces_set = set()
        intentos = 0
        xpath_contenedor = '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]'
        
        # Esperar a que exista el contenedor
        try:
            contenedor = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath_contenedor))
            )
        except:
            print("No se encontró el contenedor con la XPath especificada.")
            return []
    
        while intentos < max_intentos:
            # Scroll en ese elemento
            self.driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight;", contenedor)
            time.sleep(pause_segundos)
    
            # Ver si hay indicación de final
            if 'Has llegado al final de la lista.' in self.driver.page_source:
                print("Se alcanzó el final de la lista.")
                break
    
            # Recoger enlaces en orden
            enlaces = contenedor.find_elements(By.XPATH, ".//a[contains(@class,'hfpxzc')]")
            for a in enlaces:
                href = a.get_attribute('href')
                if href and href not in enlaces_set:
                    enlaces_en_orden.append(href)
                    enlaces_set.add(href)
                    print(href)
    
            intentos += 1
    
        return enlaces_en_orden

    def aceptar_cookies(self):
        try:
            boton_aceptar = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Aceptar todo')]"))
            )
            boton_aceptar.click()
            #time.sleep(1)
            print("[TRACE] ✔ Cookies aceptadas.")
        except Exception:
            pass

    def cerrar_panel_si_existe(self):
        try:
            boton_cerrar = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@class='omsYrc' and @aria-label='Cerrar']"))
            )
            boton_cerrar.click()
            print("[TRACE] Panel lateral cerrado.")
            #time.sleep(1)
        except Exception:
            pass

    def cerrar_omnibox(self):
        """
        Detecta si aparece el panel omnibox (por ejemplo, con id "omnibox-container")
        y, de ser así, intenta cerrarlo pulsando el botón cuyo aria-label sea "Ocultar el panel lateral".
        """
        try:
            omnibox = WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located((By.ID, "omnibox-container"))
            )
            print("[TRACE] Se detectó el panel omnibox.")
            cerrar_btn = omnibox.find_element(By.XPATH, ".//button[@aria-label='Ocultar el panel lateral']")
            cerrar_btn.click()
            print("[TRACE] Panel omnibox cerrado.")
            #time.sleep(1)
        except Exception as e:
            print(f"[TRACE] Panel omnibox no se encontró o no se pudo cerrar:  ")

    def cerrar_direcciones(self):
        """
        Comprueba si existe el panel de direcciones (con clase 'MJtgzc') y, 
        de ser así, lo cierra pulsando el botón con aria-label "Cerrar indicaciones".
        """
        try:
            # Se intenta ubicar el contenedor de direcciones
            direcciones = WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'MJtgzc')]"))
            )
            print("[TRACE] Se detectó el panel de direcciones.")
            # Buscar el botón de cerrar dentro del panel
            cerrar_btn = direcciones.find_element(By.XPATH, ".//button[@aria-label='Cerrar indicaciones']")
            cerrar_btn.click()
            print("[TRACE] Panel de direcciones cerrado.")
            #time.sleep(1)
        except Exception as e:
            print(f"[TRACE] Panel de direcciones no encontrado o no se pudo cerrar: ")

    def analizar_botones(self):
        original_window = self.driver.current_window_handle
        info_botones = {}
        all_external_links = set()
    
        # Buscar si existe el botón "Ver todo"
        try:
            boton_ver_todo = self.driver.find_element(By.XPATH, "//button[.//span[text()='Ver todo']]")
            boton_ver_todo.click()
            self.aceptar_cookies()  # Aceptar cookies si es necesario
            # Volver a realizar el análisis de botones después de pulsar "Ver todo"
        except Exception:
            pass  # Si no existe el botón "Ver todo", no hacemos nada
    
        # Procedemos con el análisis de los botones
        botones = self.driver.find_elements(By.TAG_NAME, "button")
        for boton in botones:
            try:
                texto = boton.get_attribute("aria-label") or boton.text.strip()
                if not texto:
                    continue
                info_botones[texto] = boton
                if any(palabra in texto.lower() for palabra in ["pedido", "comprar", "reservar"]):
                    pestañas_antes = self.driver.window_handles
                    boton.click()
                    self.aceptar_cookies()
                    pestañas_despues = self.driver.window_handles
                    if len(pestañas_despues) > len(pestañas_antes):
                        nueva_pestaña = list(set(pestañas_despues) - set(pestañas_antes))[0]
                        self.driver.switch_to.window(nueva_pestaña)
                        links = self.driver.find_elements(By.TAG_NAME, "a")
                        for l in links:
                            href = l.get_attribute("href")
                            if is_external_link(href):
                                all_external_links.add(href)
                        self.driver.close()
                        self.driver.switch_to.window(original_window)
                    else:
                        links = self.driver.find_elements(By.TAG_NAME, "a")
                        for l in links:
                            href = l.get_attribute("href")
                            if is_external_link(href):
                                all_external_links.add(href)
                        self.driver.back()
                        self.aceptar_cookies()
            except Exception:
                continue
    
        # Analizar los enlaces actuales después de procesar los botones
        links_actual = self.driver.find_elements(By.TAG_NAME, "a")
        for lnk in links_actual:
            href = lnk.get_attribute("href")
            if is_external_link(href):
                all_external_links.add(href)
        self.driver.switch_to.window(original_window)
    
        lista_enlaces = list(all_external_links)
        num_externos = len(lista_enlaces)
        return info_botones, num_externos, lista_enlaces
    
    def buscar_en_google_maps(self):
        print("[TRACE] Abriendo Google Maps en una nueva pestaña...")
        self.driver.get("https://www.google.es/maps")
        self.aceptar_cookies()
        self.cerrar_omnibox()

        # Aquí inicia la búsqueda por cada restaurante
        if True :
            cp = '28229'
            texto_buscado = cp + '  restaurantes'
            self.cerrar_panel_si_existe()
            self.cerrar_omnibox()
            self.cerrar_direcciones()

            # PRIMERA BÚSQUEDA: dirección + código postal
            print(f"\n[TRACE] ========== Buscando dirección: '{texto_buscado}' ========== ")
            try:
                buscador = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "searchboxinput"))
                )
                buscador.clear()
                buscador.send_keys(texto_buscado)

                boton_buscar = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "searchbox-searchbutton"))
                )
                boton_buscar.click()
                time.sleep(2)
                self.aceptar_cookies()
                self.cerrar_omnibox()
                self.cerrar_direcciones()
                
                # Scroll hasta el final de la lista
                enlaces=self.scroll_y_coger_enlaces() 
                self.enlaces=enlaces
                self.procesar_en_hilos(enlaces)
                
            except Exception as e:
                print(f"[ERROR] Error durante búsqueda y scroll: {e}")
    def procesar_en_hilos(self, lista_restaurantes):
        num_threads = 20  # o el número que prefieras
        total_items = len(lista_restaurantes)
        tamaño_base = total_items // num_threads
        resto = total_items % num_threads
    
        # Crear las sublistas inicializando con tamaño base
        sublistas = []
        start_idx = 0
    
        for i in range(num_threads):
            # Para las primeras 'resto' sublistas, añádele uno más
            tamaño_sublista = tamaño_base + (1 if i < resto else 0)
            end_idx = start_idx + tamaño_sublista
            sublistas.append(lista_restaurantes[start_idx:end_idx])
            start_idx = end_idx
    
        # Crear y arrancar los hilos
        threads = []
        resultados = []
        lock = threading.Lock()

        def procesar_sublista(sublista):
            chrome_options = Options()
            if mostrar:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            try:
                contraste = ContrasteDeDatos(driver)
                contraste.extraer(sublista)
                with lock:
                    resultados.extend(contraste.resultados)
            finally:
                driver.quit()

        for sublista in sublistas:
            hilo = threading.Thread(target=procesar_sublista, args=(sublista,))
            threads.append(hilo)
            hilo.start()

        for hilo in threads:
            hilo.join()

        self.resultados=resultados                   
    def extraer(self,enlaces):
             print("[TRACE] Abriendo Google Maps en una nueva pestaña...")
             
             self.cerrar_omnibox()
             for enlace in enlaces:
          
                 self.driver.get(enlace)
                 self.aceptar_cookies()
                 self.cerrar_panel_si_existe()
                 self.cerrar_omnibox()
                 self.cerrar_direcciones()
         
                 # PRIMERA BÚSQUEDA: dirección + código postal
                 print(f"\n[TRACE] ========== Buscando dirección: 'texto_buscado' ========== ")
                  
         
            
                 try:
                         WebDriverWait(self.driver, 5).until(
                             EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'Dirección:')]"))
                         )
                         print("[TRACE] Negocio único cargado.")
                 except Exception:
                         print("[TRACE] Ni siquiera apareció 'Dirección:' => no hay datos.")
                         
                         continue
        
                     # EXTRAER DIRECCIÓN
                 try:
                         direccion_element = WebDriverWait(self.driver, 10).until(
                             EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'Dirección:')]"))
                         )
                         direccion_label = direccion_element.get_attribute("aria-label")
                         direccion_extraida = direccion_label.split("Dirección:")[-1].strip() if direccion_label else None
                         print(f"[TRACE] Dirección extraída: {direccion_extraida}")
                 except Exception as e:
                         direccion_extraida = None
                         print(f"[TRACE] No se pudo extraer la dirección: {e}")
        
                     # EXTRAER DATOS DE GOOGLE: nombre, rating y reseñas
                 try:
                         gm_name_elem = WebDriverWait(self.driver, 10).until(
                             EC.presence_of_element_located((By.XPATH, "//h1[contains(@class, 'DUwDvf')]"))
                         )
                         google_name = gm_name_elem.text.strip()
                         print(f"[TRACE] Nombre de Google Maps: {google_name}")
                         if google_name: 
                             print(f"[TRACE] Nombre actualizado en la base de datos para ID {google_name}")
        
                 except Exception as e:
                         google_name = None
                         print(f"[TRACE] No se pudo extraer el nombre de Google Maps: {e}")
        
                 try:
                         rating_elem = WebDriverWait(self.driver, 10).until(
                             EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'F7nice')]"))
                         )
                         # Primero se intenta obtener el texto del span con aria-hidden="true"
                         try:
                             rating_span = rating_elem.find_element(By.XPATH, ".//span[@aria-hidden='true']")
                             rating_text = rating_span.text.strip()
                         except Exception:
                             rating_text = rating_elem.get_attribute("aria-label")
                         # Buscar una cadena numérica (por ejemplo, 4,2) y reemplazar la coma por punto
                         match = re.search(r'(\d+[\.,]\d+)', rating_text)
                         if match:
                             rating_value = float(match.group(1).replace(",", "."))
                         else:
                             rating_value = None
                         print(f"[TRACE] Rating extraído: {rating_value}")
                 except Exception as e:
                         rating_value = None
                         print(f"[TRACE] No se pudo extraer el rating: {e}")
        
                 try:
                         reviews_elem = WebDriverWait(self.driver, 10).until(
                             EC.presence_of_element_located((By.XPATH, "//span[contains(@aria-label, 'reseñas')]"))
                         )
                         reviews_text = reviews_elem.get_attribute("aria-label")
                         reviews_number_match = re.search(r'\d+', reviews_text)
                         reviews_number = reviews_number_match.group() if reviews_number_match else None
                         print(f"[TRACE] Reseñas extraídas: {reviews_number}")
                 except Exception as e:
                         reviews_number = None
                         print(f"[TRACE] No se pudo extraer el número de reseñas: {e}")
        
                     # Pulsar el botón para desplegar el horario                # EXTRAER HORARIO
                     # Intentar pulsar el botón de horario inicialmente
                 try:
                         horario_btn = WebDriverWait(self.driver, 10).until(
                             EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'OMl5r') and contains(@jsaction, 'pane.openhours.wfvdle53.dropdown')]"))
                         )
                         if horario_btn.is_displayed():
                             print("[TRACE] Pulsando el botón de horario...")
                             horario_btn.click()
                 except Exception:
                         print("[TRACE] No se encontró el botón de horario o ya está desplegado.")
                     
                     # Intentar extraer el horario
                 try:
                         horario_detail = WebDriverWait(self.driver, 10).until(
                             EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 't39EB')]"))
                         )
                         horario_text = horario_detail.get_attribute("aria-label")
                         print(f"[TRACE] Horario extraído: {horario_text}")
                     
                         # Si aparece "Abre pronto", intentamos pulsar el botón otra vez
                         if "Abre pronto" in horario_text:
                             print("[TRACE] Detectado 'Abre pronto'. Intentando pulsar el botón de nuevo...")
                             
                             try:
                                 horario_btn = WebDriverWait(self.driver, 10).until(
                                     EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'OMl5r') and contains(@jsaction, 'pane.openhours.wfvdle53.dropdown')]"))
                                 )
                                 if horario_btn.is_displayed():
                                     print("[TRACE] Pulsando el botón de horario nuevamente...")
                                     horario_btn.click()
                     
                                     # Extraer el horario otra vez después de abrirlo
                                     horario_detail = WebDriverWait(self.driver, 10).until(
                                         EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 't39EBf')]"))
                                     )
                                     horario_text = horario_detail.get_attribute("aria-label")
                                     print(f"[TRACE] Horario actualizado: {horario_text}")
                     
                             except Exception as e:
                                 print(f"[TRACE] No se pudo pulsar el botón de horario de nuevo: {e}")
                     
                 except Exception as e:
                         horario_text = None
                         print(f"[TRACE] No se pudo extraer el horario: {e}")
        
        
                     # Obtener el enlace de Google pulsando el botón "Compartir"
                 try:
                         compartir_btn = WebDriverWait(self.driver, 10).until(
                             EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Compartir')]"))
                         )
                         compartir_btn.click()
                         #time.sleep(1)
                         share_input = WebDriverWait(self.driver, 10).until(
                             EC.presence_of_element_located((By.XPATH, "//input[@class='vrsrZe']"))
                         )
                         google_link = share_input.get_attribute("value")
                         print(f"[TRACE] Link de Google obtenido: {google_link}")
                         # Cerrar el modal de compartir usando el botón cuyo span contiene el icono ''
                         try:
                             close_share_btn = WebDriverWait(self.driver, 10).until(
                                 EC.element_to_be_clickable((By.XPATH, "//span[@class='G6JA1c google-symbols' and contains(text(), '')]/ancestor::button"))
                             )
                             close_share_btn.click()
                             WebDriverWait(self.driver, 10).until(
                                 EC.invisibility_of_element_located((By.XPATH, "//div[contains(@class, 'm6QErb XiKgde')]"))
                             )
                         except Exception as e:
                             print(f"[TRACE] No se pudo cerrar el modal de compartir: {e}")
                 except Exception as e:
                         google_link = self.driver.current_url
                         print(f"[TRACE] No se pudo obtener el link de compartir, usando current_url: {google_link}. Error: {e}")
        
                     # Analizar botones para extraer otros enlaces (intermediarios)
                 info_botones, num_externarios, lista_enlaces = self.analizar_botones()
        
                     # Extraer datos adicionales (teléfono, rango de precios)
                 telefono_encontrado = None
                 rango_precios = None
                 for txt in info_botones:
                         if "Teléfono" in txt:
                             telefono_encontrado = txt.split(":")[-1].strip()
                         elif "€" in txt:
                             rango_precios = txt.strip()
                 try:
                         telefono_btn = WebDriverWait(self.driver, 5).until(
                             EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'Teléfono')]"))
                         )
                         telefono_encontrado = telefono_btn.get_attribute("aria-label")
                         print(f"[TRACE] Teléfono encontrado por aria-label: {telefono_encontrado}")
                 except Exception as e:
                         print(f"[TRACE] No se pudo encontrar el teléfono con aria-label: {e}")
        
                     # Construir el objeto resultado
                 resultado = {
                         "restaurante": google_name,
                         "telefono_encontrado": telefono_encontrado,
                         "direccion_encontrada": direccion_extraida,
                         "rango_precios": rango_precios,
                         "horario": horario_text,
                         "link": google_link,
                         "google_name": google_name,
                         "rating": rating_value,
                         "reviews": reviews_number,
                         "intermediarios": num_externarios,
                         "urls_intermediarios": json.dumps(lista_enlaces),
                         "links_externos": lista_enlaces
                     }
                 self.resultados.append(resultado)
        
                    
        
                  
         
                 
         
         
             self.driver.close() 
 



if __name__ == "__main__":
    # Configuración del driver de Selenium
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    # Datos de ejemplo: lista de restaurantes
    
    # Crear instancia de ContrasteDeDatos
    contraste = ContrasteDeDatos(driver)

    # Iniciar la búsqueda en Google Maps
    contraste.buscar_en_google_maps()
    
    for con in contraste.resultados:
        db.insertar_googlemaps(con)
    # Al terminar, cerrar el driver
    driver.quit()
