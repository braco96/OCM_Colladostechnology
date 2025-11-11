# Proyecto: Scraping Just Eat / Google Maps + Panel Flask

Este proyecto recopila información de restaurantes desde **Just Eat** y **Google Maps**, la normaliza y la guarda en **MySQL**, ofreciendo además un **panel Flask** con varios endpoints para operar sobre los datos (generar PDF, procesar horarios, WhatsApp, etc.).

Incluye estructura, dependencias, variables de entorno, esquema SQL, endpoints y guía de refactorización.

---

## 📁 Estructura sugerida

```
app/
├─ db/
│  └─ bbdd.py
├─ services/
│  ├─ scraping_justeat.py
│  ├─ scraping_maps.py
│  ├─ horarios.py
│  └─ whatsapp_service.py
├─ templates/
├─ routes.py
├─ __init__.py
scripts/
├─ run_justeat.py
├─ run_maps.py
migrations/
├─ 0001_base.sql
├─ 0002_indices.sql
tests/
│  └─ test_horarios.py
.env.example
requirements.txt
wsgi.py
```

---

## ⚙️ Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Requisitos
- Python 3.10+
- MySQL 8.x
- Google Chrome y webdriver-manager
- Flask 3.x, Selenium 4.x

---

## ⚙️ Variables de entorno (`.env`)

```ini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=collado
DB_NAME=restaurantes_db
SELENIUM_HEADLESS=true
FLASK_ENV=development
FLASK_PORT=5000
```

---

## 🧠 Esquema base de datos

Incluye tablas `Lugar`, `JusteatRestaurantes`, `Raspado` y `GoogleMapsRestaurantes` con claves foráneas y JSONs para URLs y horarios.

---

## 🚀 Ejecutar la API Flask

```bash
export FLASK_APP=wsgi.py
flask run --host=0.0.0.0 --port=5000
```

---

## 🔍 Scraping

- `JustEatScraper`: extrae datos de páginas Just Eat y los guarda.
- `ContrasteDeDatos`: busca restaurantes en Google Maps y recopila datos extendidos.
- `HorarioProcessor`: convierte texto de horarios a JSON estructurado.

---

## 📡 Endpoints principales

- `GET /restaurantes_movil` – Devuelve restaurantes con teléfono móvil.
- `POST /api/generar_pdf` – Genera reporte PDF.
- `POST /api/procesar_datos_Google` – Procesa scraping Maps.
- `POST /api/procesar_datos_JustEat` – Procesa scraping Just Eat.

---

## 🧩 Refactor pendiente

- Unificar versiones duplicadas (`contraste.PY`, `Nuevo_Just_Eat`).
- Sustituir `print` por `logging`.
- Manejar Selenium con `WebDriverWait`, no `sleep`.
- Crear job schedulers en vez de `while True` infinitos.

---

## 🧾 Licencia

Uso interno.
