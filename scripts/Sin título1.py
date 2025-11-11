from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bbdd import DatabaseManager
import time


class Restaurante:
    def __init__(self, url, nombre, localizacion, estrellas):
        self.url = url
        self.nombre = nombre
        self.localizacion = localizacion if localizacion and localizacion.lower() != "none" else "Ubicación desconocida"
        self.estrellas = estrellas

    def __repr__(self):
        return f"{self.nombre} ({self.estrellas}⭐) - {self.localizacion}\n{self.url}\n"

    def es_completo(self):
        return all([self.url, self.nombre, self.localizacion != ", ", self.estrellas])


class RestauranteFetcher:
    def __init__(self, db_config):
        self.db_manager = db_manager = DatabaseManager(
            host="localhost",
            user="root",
            password="collado",
            database="restaurantes_db"
        )
        self.driver = self._setup_driver()

    def _setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def fetch_restaurantes_for_lugar(self, lugar):
        cpostal = lugar['codigo_postal']
        idlugar = lugar['id_lugar']
        restaurantes_info = []
        try:
            url_listado = f"https://www.just-eat.es/area/{cpostal}?filter=pizza"
            self.driver.get(url_listado)
            
            # Scroll para cargar todos los restaurantes
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.1)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Extraer los elementos <a> que contienen la info básica
            restaurant_elements = self.driver.find_elements(By.CSS_SELECTOR, "a._9NUh1")
            print(f"🔗 Se encontraron {len(restaurant_elements)} elementos en la lista.")

            # Extraer nombre (desde title) y URL; filtrar enlaces que no sean de restaurantes
            base_url = "https://www.just-eat.es"
            for elem in restaurant_elements:
                title = elem.get_attribute("title")
                href = elem.get_attribute("href")
                # Filtrar: se omiten elementos sin título o que no sean de restaurantes
                if not title or "/restaurants-" not in href:
                    continue
                url_restaurante = base_url + href if href.startswith("/") else href
                restaurantes_info.append({
                    "nombre": title,
                    "url": url_restaurante,
                    "id_lugar": idlugar
                })

            print(restaurantes_info)
        except Exception as e:
            print(f"Error obteniendo JSON-LD para {lugar['municipio']}: {e}")

        return restaurantes_info

    def fetch_all_restaurantes(self):
        lugares_incompletos = self.db_manager.get_lugares_incompletos()
        all_restaurantes = []
        for lugar in lugares_incompletos:
            print(f"Procesando lugar: {lugar['id_lugar']}, {lugar['municipio']}")
            restaurantes = self.fetch_restaurantes_for_lugar(lugar)
            all_restaurantes.extend(restaurantes)
        return all_restaurantes

    def clasificar_restaurantes(self, restaurantes):
        completos = []
        incompletos = []
        for restaurante in restaurantes:
            if restaurante['nombre'] and restaurante['url'] and restaurante['id_lugar']:
                completos.append(restaurante)
            else:
                incompletos.append(restaurante)
        return completos, incompletos

    def close(self):
        self.driver.quit()
# Configuración de la base de datos
 
# Aquí puedes tr 

