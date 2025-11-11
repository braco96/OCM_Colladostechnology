import mysql.connector

# Configuración de conexión como root
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "collado"  # Ajusta la contraseña de tu root
}

def main():
    # Conectar a MySQL sin seleccionar base de datos
    conexion = mysql.connector.connect(**DB_CONFIG)
    cursor = conexion.cursor()

    # Eliminar la base de datos si ya existe y crear una nueva
    cursor.execute("DROP DATABASE IF EXISTS restaurantes_db")
    cursor.execute("CREATE DATABASE restaurantes_db")
    cursor.execute("USE restaurantes_db")

    print("✅ Base de datos 'restaurantes_db' creada correctamente.")

    # Crear la tabla Lugar
    cursor.execute("""
        CREATE TABLE Lugar (
            id_lugar INT AUTO_INCREMENT PRIMARY KEY, 
            provincia VARCHAR(100),
            municipio VARCHAR(100), 
            fase INT DEFAULT 0  
            --la fase de un lugar implica nºraspados ejercidos sobre la zona
        )
    """)

    # Crear la tabla urls_porlugar (si la necesitas)
    cursor.execute("""
        CREATE TABLE Raspado (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_lugar INT NOT NULL,
            url_google VARCHAR(255) NOT NULL,   pasa a ser una lista ordenada muy grande
            nombre VARCHAR(255) NOT NULL,
            UNIQUE KEY unique_id_lugar_url (id_lugar, url_google),
            FOREIGN KEY (id_lugar) REFERENCES Lugar(id_lugar)
        )
    """)

    # Crear la tabla GoogleMapsRestaurantes
    #
    # - Copiamos muchos de los campos de JusteatRestaurantes menos 'carta' y 'horario'
    # - Añadimos 'id_justeat' como FK obligatoria y 'nombre' como NOT NULL.
    # - Añadimos 'telefono' y una columna generada 'es_movil' que depende de 'telefono'.
    # - OJO: es_movil como columna generada requiere MySQL 8.0+.
    #
    # Si usas MySQL < 8.0, elimina es_movil y usa un trigger o lógica en Python.

    cursor.execute("""CREATE TABLE GoogleMapsRestaurantes (
    --id de lugares  lista de varcahr con los id_lugar asociados
    
    id_googlemaps INT AUTO_INCREMENT PRIMARY KEY,
    id_justeat INT NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    direccion VARCHAR(255) DEFAULT NULL,
    estrellas DECIMAL(2,1) DEFAULT NULL,
    comentarios INT DEFAULT NULL,         -- Cantidad de reseñas (comentarios)
    intermediarios INT DEFAULT 0,           -- Número de intermediarios encontrados
    urls_intermediarios JSON DEFAULT NULL,  -- Conjunto de URLs de intermediarios (en JSON)
    link_googlemaps TEXT DEFAULT NULL,      -- Cambiado a TEXT
    telefono VARCHAR(20) DEFAULT NULL,
    calendario TEXT DEFAULT NULL,           -- Cambiado a TEXT (calendario no procesado)
    tipo TINYINT NOT NULL,
    
);


)

    """) 
    # Confirmar los cambios
    conexion.commit()
    print("✅ Todas las tablas han sido creadas correctamente.")

    # Cerrar conexión
    cursor.close()
    conexion.close()
    print("🔌 Conexión cerrada.")

if __name__ == "__main__":
    main()
