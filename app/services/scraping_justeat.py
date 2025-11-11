import time
import json
import mysql.connector
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bbdd import DatabaseManager  # Tu módulo con la lógica de la DB

class JustEatScraper:
    def __init__(self, driver,lista,db_manager):
        self.lista=lista
        self.driver = driver
        self.db_manager = db_manager  
 
    def extraer_datos(self, restaurante):
        """
        Navega a la URL de Just Eat, extrae datos del JSON-LD y los retorna en un dict.
        """
        url = restaurante['link_justeat']
        id_justeat = restaurante['id_justeat']
        self.driver.get(url)
        time.sleep(3)  # Esperar a que cargue la página
        
        try:
            script_tag = self.driver.find_element(By.XPATH, "//script[@type='application/ld+json']")
            data = json.loads(script_tag.get_attribute("innerHTML"))

            nombre = data.get("name", "No disponible")
            direccion = data.get("address", {}).get("streetAddress", "No disponible")
            cp = data.get("address", {}).get("postalCode", "No disponible")  # <<< CODIGO POSTAL
            estrellas = data.get("aggregateRating", {}).get("ratingValue", None)
            comentarios = data.get("aggregateRating", {}).get("reviewCount", None)
            horario = data.get("openingHours", [])  # Suele ser lista
            
            print("\n===============================")
            print(f"ID: {id_justeat}")
            print(f"Nombre: {nombre}")
            print(f"Dirección: {direccion}")
            print(f"Código postal: {cp}")
            print(f"Estrellas: {estrellas}")
            print(f"Número de comentarios: {comentarios}")
            print(f"Horario: {horario if horario else 'No disponible'}")
            print("===============================\n")
 
            return {
                "id_justeat": id_justeat,
                "nombre": nombre,
                "direccion": direccion,
                "cp": cp,  # lo añadimos al dict
                "estrellas": estrellas,
                "comentarios": comentarios,
                "horario": horario
            }
        except Exception as e:
            print(f"❌ Error al extraer datos de {url}: {e}")
            return None

    def ejecutar_scraper(self):
        """
        Recorre todos los restaurantes que están en cola y guarda la info en la BBDD.
        """
        restaurantes = self.lista
        for restaurante in restaurantes:
            datos = self.extraer_datos(restaurante)
            if datos:
                # Guardar en la base de datos
                try:
                    self.db_manager.update_restaurante_con_datos(datos)
                    self.db_manager.insertar_googlemaps_restaurante(datos)
                except:
                    print('No se introducen')
            else:
                print(f"No se pudieron extraer datos para el ID {restaurante['id_justeat']}")

    def cerrar(self):
        self.driver.quit()

if __name__ == "__main__":
    try: 
            db_manager = DatabaseManager(
                host="localhost",
                user="root",
                password="collado",
                database="restaurantes_db_copy"
            )
            restaurantes= db_manager.get_justEat_en_cola(2)
            scraper = JustEatScraper(db_manager,restaurantes)
            
            scraper.ejecutar_scraper()
            scraper.cerrar()
    except:
        print('***********Volvemos en 5 segundos*************')
        
    
