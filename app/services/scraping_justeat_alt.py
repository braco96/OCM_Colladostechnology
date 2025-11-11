import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bbdd import DatabaseManager

class SacarUrlsYNombres:
    def __init__(self, db_manager, max_lugares=50):
        """
        Constructor.
        
        Parámetros:
          - db_manager: Instancia de DatabaseManager para acceder a la BBDD.
          - max_lugares: Número máximo de lugares a procesar.
        """
        self.db_manager = db_manager
        self.max_lugares = max_lugares
        self.urls = []
        self.driver = None

    def setup_driver(self):
        """Configura el driver de Chrome."""
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def sacar_urls_y_nombres(self):
        """
        Extrae los nombres y URLs de los restaurantes a partir de los lugares incompletos.
        
        Retorna:
          - Una lista de diccionarios con las claves "nombre", "url" e "id_lugar".
        """
        # Configurar el driver si aún no se ha hecho
        if not self.driver:
            self.setup_driver()

        # Obtener los lugares incompletos desde la BBDD
        lugares_incompletos = self.db_manager.obtener_links_no_completos()
        if lugares_incompletos:
            # Procesa desde el 2do hasta el max_lugares (ajusta según necesites)
            for lugar in lugares_incompletos[1:self.max_lugares]:
                print(f"ID: {lugar['id_lugar']} | {lugar['municipio']}, {lugar['provincia']} ({lugar['codigo_postal']})")
                idlugar = lugar['id_lugar']
                cpostal = lugar['codigo_postal']
                
                # Armar la URL del listado de restaurantes para el código postal
                url_listado = f"https://www.just-eat.es/area/{cpostal}"
                self.driver.get(url_listado)
                
                # Hacer scroll para cargar todos los restaurantes
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                while True:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(0.1)
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                
                # Extraer los elementos <a> con la información básica de los restaurantes
                restaurant_elements = self.driver.find_elements(By.CSS_SELECTOR, "a._9NUh1")
                print(f"🔗 Se encontraron {len(restaurant_elements)} elementos en la lista.")
                
                base_url = "https://www.just-eat.es"
                for elem in restaurant_elements:
                    title = elem.get_attribute("title")
                    href = elem.get_attribute("href")
                    # Filtrar elementos sin título o que no contengan "/restaurants-"
                    if not title or "/restaurants-" not in href:
                        continue
                    url_restaurante = base_url + href if href.startswith("/") else href
                    self.urls.append({
                        "nombre": title,
                        "url": url_restaurante,
                        "id_lugar": idlugar 
                    })

        # Cerrar el driver al finalizar
        self.driver.quit()
        return self.urls

# --------------------------------------------------
# Ejemplo de uso:
# --------------------------------------------------
if __name__ == "__main__":
    # Conectar a la base de datos
    db_manager = DatabaseManager(
        host="localhost",
        user="root",
        password="collado",
        database="restaurantes_db_copy"
    )
    
    # Instanciar el objeto SacarUrlsYNombres
    extractor = SacarUrlsYNombres(db_manager,50)
    
    # Extraer las URLs y nombres de los restaurantes
    urls_extraidas = extractor.sacar_urls_y_nombres()
    
    # Imprimir resultados
    print("URLs obtenidas:")
    for registro in urls_extraidas:
        print(registro)
