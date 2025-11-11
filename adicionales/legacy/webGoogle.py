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
from horario import HorarioProcessor


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
    def __init__(self, driver, lista_restaurantes, db_manager):
        self.driver = driver
        self.lista_restaurantes = lista_restaurantes
        self.db_manager = db_manager
        # Inserta registro inicial en la tabla (sólo id_justeat y nombre)
        # for a in lista_restaurantes:
             #self.db_manager.insertar_googlemaps_restaurantes([a])
        self.resultados = []

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
 


    def extraer(self,enlace):
        print("[TRACE] Abriendo Google Maps en una nueva pestaña...")
        self.driver.get(enlace)
        self.aceptar_cookies()
        self.cerrar_omnibox()
    
        for restaurante in self.lista_restaurantes:
            nombre = restaurante.get('justeat_nombre', '')
            cp = restaurante.get('cp', '')
            direccion_original = restaurante.get("justeat_direccion", '')
            texto_buscado = direccion_original + ' , ' + cp
    
    
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
    
                divs = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'Nv2PK')]")
                if divs:
                    print("[TRACE] Resultados encontrados en la búsqueda por dirección.")
                else:
                    print("[TRACE] No se encontraron resultados visibles por dirección.")
            except Exception as e:
                print(f"[ERROR] Error durante la búsqueda por dirección: {e}")
    
            time.sleep(1)
    
            # SEGUNDA BÚSQUEDA: nombre del restaurante (ya centrados en la zona)
            print(f"\n[TRACE] ========== Buscando nombre del local: '{nombre}' ========== ")
            try:
                buscador = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "searchboxinput"))
                )
                buscador.clear()
                buscador.send_keys(nombre)
    
                boton_buscar = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "searchbox-searchbutton"))
                )
                boton_buscar.click()
                time.sleep(2)
                self.aceptar_cookies()
                self.cerrar_omnibox()
                self.cerrar_direcciones()
    
                divs_nombre = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'Nv2PK')]")
                if divs_nombre:
                    print("[TRACE] Resultados encontrados tras buscar por nombre del restaurante.")
                else:
                    print("[TRACE] No se encontraron resultados tras buscar por nombre.") 
                divs = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'Nv2PK')]") 
     
                     
                
                print("[TRACE] No hay resultados => asumimos negocio único (o no existe).")
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'Dirección:')]"))
                    )
                    print("[TRACE] Negocio único cargado.")
                except Exception:
                    print("[TRACE] Ni siquiera apareció 'Dirección:' => no hay datos.")
                    self.db_manager.set_interesa(restaurante['id_justeat'], -1)
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
                        self.db_manager.update_nombre(restaurante['id_justeat'], google_name)
                        print(f"[TRACE] Nombre actualizado en la base de datos para ID {restaurante['id_justeat']}")

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
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 't39EBf')]"))
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
                    telefono_encontrado = telefono_btn.get_attribute("aria-label").split("Teléfono:")[-1].strip()
                    print(f"[TRACE] Teléfono encontrado por aria-label: {telefono_encontrado}")
                except Exception as e:
                    print(f"[TRACE] No se pudo encontrar el teléfono con aria-label: {e}")

                # Construir el objeto resultado
                resultado = {
                    "Base": restaurante,
                    "restaurante": nombre,
                    "direccion_original": direccion_original,
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

                # Upgrade: actualizar la tabla GoogleMapsRestaurantes con los nuevos campos
                try:
                    self.db_manager.cursor.execute("""
                        UPDATE GoogleMapsRestaurantes
                        SET 
                            direccion = %s,
                            link_googlemaps = %s,
                            telefono = %s,
                            calendario = %s,
                            estrellas = %s,
                            comentarios = %s,
                            intermediarios = %s,
                            urls_intermediarios = %s,
                            interesa = %s
                        WHERE id_justeat = %s
                    """, (
                        direccion_extraida,
                        google_link,
                        telefono_encontrado,
                        horario_text,
                        rating_value,
                        reviews_number,
                        num_externarios,
                        json.dumps(lista_enlaces),
                        1,
                        restaurante['id_justeat']
                    ))
                    self.db_manager.conexion.commit()
                    print(f"✅ Upgrade completado para ID {restaurante['id_justeat']}")
                except Exception as e:
                    self.db_manager.set_interesa(restaurante['id_justeat'], -1)
                     
                    print(f"❌ Error al actualizar para ID {restaurante['id_justeat']}: {e}")
                    print(f"✅ Upgrade completado para interesa = -1")

                self.driver.back()
                #time.sleep(2)
                self.aceptar_cookies()
                self.cerrar_omnibox()
    
            except Exception as e:
                print(f"[TRACE] Error al buscar '{texto_buscado}': {e}")
    
        print("[TRACE] Cerrando pestaña de Google Maps y regresando a la original...")
        self.driver.close() 
    
 
