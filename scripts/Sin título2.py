#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 15 16:10:50 2025

@author: luis
"""

import time
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bbdd import DatabaseManager  # Se asume que en bbdd.py se define DatabaseManager con las funciones indicadas

class SacarUrlsYNombres:
    def __init__(self, db_manager, max_lugares=250):
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
        self.lugares_incompletos = self.db_manager.get_lugares_incompletos()
        if self.lugares_incompletos:
            for lugar in self.lugares_incompletos[0:self.max_lugares]:
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
                    #time.sleep(0.000000000000000000000000000001)
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

        # Cerrar el driver al finalizar el scraping
        self.driver.quit()
        return self.urls

    def procesar_registros(self, registros_scrapeados):
        """
        Procesa los registros obtenidos del scraping:
          - Recupera todos los registros de la tabla urls_porlugar.
          - Si la URL del registro scrapeado no existe en la BD, la inserta.
          - Si ya existe, actualiza el id_lugar mediante asignar_id_lugar_si_existe.
          - Finalmente, marca cada lugar procesado como completo.
        """
        # Recuperar todos los registros de urls_porlugar (sin filtrar)
        registros_db = self.db_manager.obtener_urls()
        urls_existentes = {registro["url_justeat"] for registro in registros_db}
        
        for registro in registros_scrapeados:
                self.db_manager.insertar_urls_por_lugar(registro["id_lugar"], [registro])
        
        # Marcar cada lugar procesado como completo
        for lugar in self.lugares_incompletos[0:self.max_lugares]:
            self.db_manager.marcar_lugar_completo(lugar["id_lugar"])

# --------------------------------------------------
# Ejemplo de uso e integración
# --------------------------------------------------
import time

if __name__ == "__main__":
    while True:
        try:
            # Conectar a la base de datos (la conexión se inicia en el constructor de DatabaseManager)
            db_manager = DatabaseManager(
                host="localhost",
                user="root",
                password="collado",
                database="restaurantes_db"
            )
            
            # Instanciar el objeto SacarUrlsYNombres y extraer los datos del scraping
            extractor = SacarUrlsYNombres(db_manager)
            registros_scrapeados = extractor.sacar_urls_y_nombres()
            
            print("URLs obtenidas del scraping:")
            for registro in registros_scrapeados:
                print(registro)
            
            # Procesar los registros (insertar o actualizar en la BD y marcar lugares completos)
            extractor.procesar_registros(registros_scrapeados)
            
            # Cerrar la conexión a la BD
            db_manager.cerrar()
            
        except Exception as e:
            print(f"Se produjo un error: {e}. Esperando 30 segundos antes de reintentar...")
            time.sleep(10)
