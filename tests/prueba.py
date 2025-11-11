
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from difflib import SequenceMatcher  # Para comparar similitud de nombres

# Clase Restaurante
class Restaurante:
    def __init__(self, url, nombre, localizacion, estrellas):
        self.url = url
        self.nombre = nombre
        self.localizacion = localizacion if localizacion != ', ' else None
        self.estrellas = estrellas

    def __repr__(self):
        return f"{self.nombre} ({self.estrellas}⭐) - {self.localizacion}\n{self.url}\n"
 

# Clase Lugar para almacenar información de los lugares encontrados
class Lugar:
    def __init__(self, restaurante):
        self.restaurante = restaurante
        self.url_base = ""  # URL tras la búsqueda
        self.nombre = None  # Nombre del lugar seleccionado
        self.rating = None  # Puntuación del lugar seleccionado
        self.link = None  # URL real del lugar seleccionado

    def set_info(self, nombre, rating, link):
        self.nombre = nombre
        self.rating = rating
        self.link = link

    def __repr__(self):
        return f"Restaurante: {self.restaurante.localizacion} | Seleccionado: {self.nombre} ({self.rating}⭐) | {self.link}"

# Clase ContrasteDeDatos para buscar en Google Maps
class ContrasteDeDatos:
    def __init__(self, driver, lista_restaurantes):
        self.driver = driver
        self.lista_restaurantes = lista_restaurantes
        self.lugares = []  # Lista de objetos Lugar (uno por restaurante)

    def buscar_en_google_maps(self):
        """
        Realiza la búsqueda de cada restaurante en Google Maps y guarda solo el lugar más parecido.
        """
        # 1. Abrir Google Maps
        maps_url = "https://www.google.es/maps"
        self.driver.get(maps_url)
        
        # Intentar aceptar las cookies si aparece el botón
        try:
            boton_aceptar = self.driver.find_element(By.XPATH, "//button[contains(., 'Aceptar todo')]")
            boton_aceptar.click()
            time.sleep(2)  # Esperar a que desaparezca
            print("✔ Se aceptaron las cookies de Google Maps.")
        except:
            print("⚠ No se encontró el botón de 'Aceptar todo', continuando...")

        time.sleep(3)  # Esperar que cargue

        # 2. Buscar cada restaurante en la lista
        for restaurante in self.lista_restaurantes:
            lugar = Lugar(restaurante)
            nombre_restaurante = restaurante.localizacion.lower()  # Normalizamos el nombre

            # Buscar la localización
            buscador = self.driver.find_element(By.ID, "searchboxinput")
            buscador.clear()
            buscador.send_keys(restaurante.localizacion)

            # Hacer clic en el botón de búsqueda
            boton_busqueda = self.driver.find_element(By.ID, "searchbox-searchbutton")
            boton_busqueda.click()

            # Esperar para que carguen los resultados
            time.sleep(4)

            # Guardar la URL base tras la búsqueda
            lugar.url_base = self.driver.current_url

            # Capturar todos los lugares en los resultados
            resultados = self.driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK.THOPZb.CpccDe")

            # Contar cuántos lugares se encontraron
            total_lugares = len(resultados)
            print(f"\nSe encontraron {total_lugares} lugares para '{restaurante.nombre}':\n")

            # Variables para encontrar el lugar con mayor similitud
            mejor_coincidencia = None
            mejor_similitud = 0.0
            mejor_rating = "Sin puntuación"
            mejor_link = "No disponible"

            # Iterar sobre los resultados para encontrar el más parecido
            for resultado in resultados:
                try:
                    boton_lugar = resultado.find_element(By.CSS_SELECTOR, "button.hfpxzc")
                    nombre_lugar = boton_lugar.get_attribute("aria-label").lower()  # Normalizamos el nombre
                except:
                    nombre_lugar = "Nombre no encontrado"

                # Calcular la similitud entre el nombre buscado y el encontrado
                similitud = SequenceMatcher(None, nombre_restaurante, nombre_lugar).ratio()

                try:
                    elemento_rating = resultado.find_element(By.CSS_SELECTOR, "span.MW4etd")
                    rating_lugar = elemento_rating.text
                except:
                    rating_lugar = "Sin puntuación"

                # Guardamos el lugar con la mayor similitud
                if similitud > mejor_similitud:
                    mejor_similitud = similitud
                    mejor_coincidencia = nombre_lugar
                    mejor_rating = rating_lugar

                    # Hacer clic en el botón para obtener la URL real
                    try:
                        print(f"Seleccionando mejor coincidencia: {nombre_lugar} ({similitud:.2f})")
                        boton_lugar.click()
                        time.sleep(3)
                        mejor_link = self.driver.current_url
                    except:
                        mejor_link = "No disponible"

                    # Regresar a la página base antes de probar la siguiente
                    self.driver.get(lugar.url_base)
                    time.sleep(2)

            # Si encontramos una coincidencia válida, la guardamos
            if mejor_coincidencia and mejor_similitud >= 0.6:  # Umbral de similitud
                lugar.set_info(mejor_coincidencia, mejor_rating, mejor_link)
                print(f"\n✔ Se seleccionó: {mejor_coincidencia} (Similitud: {mejor_similitud:.2f})\n")
            else:
                print("\n❌ No se encontró una coincidencia aceptable.\n")

            print("-------------------------------------------------------------")

            # Agregar el objeto Lugar a la lista de lugares
            self.lugares.append(lugar)

    def mostrar_resultados(self):
        """
        Muestra los lugares seleccionados.
        """
        for lugar in self.lugares:
            print(f"Restaurante: {lugar.restaurante.localizacion}")
            print(f"URL Base: {lugar.url_base}")
            if lugar.nombre:
                print(f"Nombre: {lugar.nombre} | Rating: {lugar.rating} | Link: {lugar.link}")
            else:
                print("⚠ No se encontró un lugar adecuado.")
            print("-------------------------------------------------------------")


if __name__ == "__main__":
    # 1. Iniciar el driver (Chrome, en este caso)
    driver = webdriver.Chrome()  # Asegúrate de tener chromedriver en PATH o usa webdriver_manager

    # 2. Instanciar la clase con la lista de restaurantes
    contraste = ContrasteDeDatos(driver, completos)

    # 3. Ejecutar la búsqueda en Google Maps
    contraste.buscar_en_google_maps()

    # 4. Mostrar los resultados obtenidos
    contraste.mostrar_resultados()

    # 5. (Opcional) Cerrar el navegador cuando hayas terminado
    # driver.quit()
