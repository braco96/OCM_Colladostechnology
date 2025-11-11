import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyperclip
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse
from selenium.webdriver.common.keys import Keys


from selenium.common.exceptions import TimeoutException
class whatsapp:
    def __init__(self,  lista_restaurantes ):
        self.mostrar=True
        # Configura las opciones de Chrome para usar el perfil Default con depuración remota
        
        self.lista_restaurantes = lista_restaurantes 
        self.resultados = []
        self.mensaje_base = (
    "Hola, mi nombre es *Luis Bravo*, soy *ingeniero informático y matemático*, "
    "trabajo para *Collado's Technology*, *empresa de marketing digital y desarrollo web*.\n\n"
    "He notado que {nombre} *no cuenta actualmente con una página web*, y por ello me gustaría ofrecerle algo especial , \n"
    "*el diseño completo de su página web de forma totalmente gratuita*, *sin ningún coste inicial*.\n\n"
    "Esta promoción es *exclusiva para los primeros 10 negocios* que deseen descubrir cómo podría lucir su sitio web profesional utilizando *nuestras herramientas y tecnologías*.\n"
    "Por *0 euros*, podrá disponer de una *web funcional, moderna y adaptada* a las necesidades específicas de su negocio.\n\n"
    "Una vez finalizado el desarrollo, y *solo si queda satisfecho con el resultado*, podrá optar por mantener el servicio con una de estas dos opciones:\n"
    "• *280 € al año*, sin cuotas mensuales.\n"
    "• *350 € por 4 años*, sin cargos adicionales.\n\n"
    "*¿Qué incluye su página web personalizada?*\n"
    "• *Diseño profesional y adaptable a dispositivos móviles*.\n"
    "• *Carta digital actualizada*.\n"
    "• *Avisos sobre productos no disponibles*.\n"
    "• *Opción para pedidos para recoger*.\n"
    "• *Envío de SMS a clientes (opcional)*.\n"
    "• *Asistencia técnica y mantenimiento*.\n\n"
    "*No se trata de una plantilla genérica*. El diseño será *exclusivo y pensado para su negocio*.\n"
    "Y si finalmente decide no continuar, *no tendrá que pagar absolutamente nada*.\n"
    "*Es mi forma de empezar, ayudando a los primeros 10 clientes sin compromiso*.\n\n"
    "*Quedo a su disposición para hablar cuando le venga bien*.\n"
    "Si está interesado/a, *solo necesito que me facilite su nombre y un momento adecuado para llamarle*.\n\n"
    "Gracias por su tiempo y atención.\n"
    "Reciba un cordial saludo,\n"
    "*Luis Bravo*\n"
    "*Collado's Technology*"
)




    def extraer_intermediarios(self, urls_intermediarios):
        intermediarios_info = []

        if urls_intermediarios:
            if isinstance(urls_intermediarios, str):
                try:
                    urls_intermediarios = json.loads(urls_intermediarios)
                except Exception:
                    urls_intermediarios = [urls_intermediarios]
            if isinstance(urls_intermediarios, list):
                for url in urls_intermediarios:
                    url_lower = url.lower()

                    # Inicializar la variable texto antes de usarla
                    texto = None

                    # Verificar las diferentes condiciones de intermediarios
                    if "just-eat" in url_lower:
                        texto = "JustEat"
                    elif "uber" in url_lower:
                        texto = "Uber"
                    elif "glovoapp" in url_lower:
                        texto = "Glovo" 
                    
                    # Si se ha asignado un valor a texto, agregar la información al listado
                    if texto:
                        intermediarios_info.append((texto, url))
    
        return intermediarios_info
    def mensaje_ya_enviado(self, clave):
        try:
            # Espera a que los mensajes de hoy aparezcan
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "message-out"))
            )
    
            # Desplázate hacia arriba para cargar los mensajes anteriores si es necesario
            while True:
                self.driver.execute_script("arguments[0].scrollTop = 0;", self.driver.find_element(By.CLASS_NAME, "message-list"))
                WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "message-out"))
                )
                mensajes = self.driver.find_elements(By.CLASS_NAME, "message-out")
                
                # Salir del ciclo si no se cargaron más mensajes
                if len(mensajes) == 0:
                    break
    
            # Ahora revisa los mensajes de hoy (siendo más específicos)
            for mensaje in mensajes[::-1]:  # Recorre de atrás hacia adelante para los mensajes recientes
                texto_elementos = mensaje.find_elements(By.CLASS_NAME, "selectable-text")
                for elem in texto_elementos:
                    texto = elem.text
                    if clave in texto:
                        return True
    
            return False
    
        except Exception as e:
            print(f"[!] Error comprobando mensaje previo: {e}")
            return False


    def crear_mensaje(self, restaurante):
       nombre = restaurante.get("nombre", "")
       urls_intermediarios = restaurante.get("urls_intermediarios", [])
       intermediarios_info = self.extraer_intermediarios(urls_intermediarios)
       intermediarios_str =''
       enlaces_str=''
       if not intermediarios_info:
           intermediarios_str = "just-eat"
       else:
               intermediarios_str = ", ".join(i[0] for i in intermediarios_info)
               enlaces_str = "\n".join(f"{i[0]}: {i[1]}" for i in intermediarios_info)

       # Crear el mensaje final como un solo bloque
       mensaje_final = self.mensaje_base.format(
           nombre=nombre,
           intermediarios=intermediarios_str,
           enlaces=enlaces_str
       )
       
       return mensaje_final


    def abrir_whatsapp_web(self):
        print("Abriendo WhatsApp Web...")
        
        chrome_options = Options()
    
        # Ruta a un perfil exclusivo de Chrome para Selenium con sesión ya iniciada
        chrome_options.add_argument("user-data-dir=/home/braco/.config/selenium-profile")
        chrome_options.add_argument("profile-directory=Default")
        
        # Condicional para modo headless
        if not self.mostrar:
            # ⚠ WhatsApp Web no siempre funciona bien en headless
            chrome_options.add_argument("--headless=new")  # Intenta con el nuevo modo headless
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
    
        # Inicializa el driver
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
    
        # Abre WhatsApp Web
        self.driver.get("https://web.whatsapp.com")
        print("Esperando sesión de WhatsApp...")
    
        try:
            WebDriverWait(self.driver, 90).until(
                EC.presence_of_element_located((By.ID, "pane-side"))
            )
            print("✅ Sesión iniciada correctamente en WhatsApp Web.")
        except Exception as e:
            print("❌ No se pudo cargar WhatsApp Web. Error:", e)
             


    def visitar_numeros(self):
        for restaurante in self.lista_restaurantes:
            telefono = 696032954  # Usa el teléfono correcto de cada restaurante aquí
            if not telefono:
                continue
        
            mensaje = self.crear_mensaje(restaurante)
            if not mensaje:
                continue
        
            print("\nGenerando mensaje para:", restaurante.get("nombre"))
            print("Mensaje generado:\n", mensaje)
        
            try:
                url_whatsapp = f"https://web.whatsapp.com/send?phone={telefono}"
                self.driver.get(url_whatsapp)
        
                campo_mensaje = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'div[contenteditable="true"][data-tab="10"]')
                    )
                )
        
                # Esperar un poco a que se cargue completamente
                time.sleep(5)
        
                # Enviar el mensaje completo
                pyperclip.copy(mensaje)
                campo_mensaje.click()
                campo_mensaje.send_keys(Keys.CONTROL, 'v')  # Pegado con Ctrl+V (en Windows/Linux)
                campo_mensaje.send_keys(Keys.ENTER)  # Enviar
        
                print(f"✅ Mensaje completo enviado a {telefono}")
                time.sleep(10)  # Espera antes de pasar al siguiente
        
            except Exception as e:
                print(f"❌ Error al enviar mensaje a {telefono}: {e}")
