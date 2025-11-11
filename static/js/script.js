// Variable global para almacenar los datos actuales
let currentData = [];

// Variable global para definir la fuente (Google o JustEat)
// Por defecto se usa "Google"
let currentSource = "Google";

// NUEVA VARIABLE: Usaremos esta constante en lugar de la cadena "procesar"
const ACCION_PROCESAR_LOQUE_PROCESAMOS = "PROCESAR_loque procesamos";

// Función recursiva para renderizar valores complejos (objetos o arrays)
function renderValue(value) {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === 'object') {
    if (Array.isArray(value)) {
      let listHtml = '<ul style="list-style: none; padding-left: 10px; margin: 0;">';
      value.forEach(item => {
        listHtml += `<li>${renderValue(item)}</li>`;
      });
      listHtml += '</ul>';
      return listHtml;
    } else {
      let objHtml = '<div style="font-size: 0.8em; padding-left: 10px;">';
      for (const key in value) {
        if (Object.hasOwn(value, key)) {
          objHtml += `<div><strong>${key}:</strong> ${renderValue(value[key])}</div>`;
        }
      }
      objHtml += '</div>';
      return objHtml;
    }
  }
  return value;
}

// Función para cargar datos según el contexto
// Si filtro es "captar", se usa el endpoint /restaurantes_no_completos_<Fuente>
async function cargarDatos(filtro) {
  let endpoint = "";
  if (filtro === "captar") {
    endpoint = '/restaurantes_no_completos_' + currentSource;
  } 
  if (filtro === "trasladarllamadas") {
    endpoint = '/restaurantes_activo';
  }
  if (filtro === "trasladardatos") {
    endpoint = '/restaurantes_google';
  }
  if (filtro === "0") {
    endpoint = '/restaurantes_google';
  } else if (filtro === "en_proceso") {
    endpoint = '/restaurantes_en_proceso';
  } else if (filtro === "finalizados") {
    endpoint = '/restaurantes_finalizados';
  } else if (filtro === "trasladarllamadas") {
    endpoint = '/restaurantes_activo';
  } else if (filtro === "trasladardatos") {
    endpoint = '/restaurantes_google';
  }
  try {
    const response = await fetch(endpoint);
    const data = await response.json();
    currentData = data;

    // Actualizar la tabla (se espera que existan <thead id="table-head"> y <tbody id="table-body">)
    const tableHead = document.getElementById('table-head');
    const tableBody = document.getElementById('table-body');

    if (tableHead && tableBody) {
      tableHead.innerHTML = '';
      tableBody.innerHTML = '';

      if (data.length > 0) {
        // Crear encabezado con columna de selección
        const headerRow = document.createElement('tr');
        const thSelect = document.createElement('th');
        thSelect.textContent = "Seleccionar";
        headerRow.appendChild(thSelect);
        Object.keys(data[0]).forEach(key => {
          const th = document.createElement('th');
          th.textContent = key;
          headerRow.appendChild(th);
        });
        tableHead.appendChild(headerRow);

        // Crear filas de datos
        data.forEach((item, index) => {
          const tr = document.createElement('tr');
          // Columna con checkbox
          const tdSelect = document.createElement('td');
          const checkbox = document.createElement('input');
          checkbox.type = 'checkbox';
          checkbox.className = 'row-selector';
          checkbox.value = index;
          checkbox.addEventListener('change', function() {
            if (this.checked) {
              tr.classList.add('selected');
            } else {
              tr.classList.remove('selected');
            }
          });
          tdSelect.appendChild(checkbox);
          tr.appendChild(tdSelect);

          // Rellenar el resto de columnas
          Object.entries(item).forEach(([key, value]) => {
            const td = document.createElement('td');
            if (typeof value === 'object' && value !== null) {
              td.innerHTML = renderValue(value);
            } else {
              td.textContent = value;
            }
            tr.appendChild(td);
          });
          tableBody.appendChild(tr);
        });
      } else {
        // Mensaje en caso de no haber datos
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 10;
        cell.textContent = "No se encontraron datos.";
        row.appendChild(cell);
        tableBody.appendChild(row);
      }
    }
  } catch (error) {
    console.error("Error al cargar datos:", error);
  }
}

/// Función para enviar la acción con los datos seleccionados
function enviarDatosAccion(accion) {
  const checkboxes = document.querySelectorAll('input.row-selector:checked');
  const datosSeleccionados = Array.from(checkboxes).map(cb => currentData[cb.value]);

  if (datosSeleccionados.length === 0) {
    alert("No hay filas seleccionadas.");
    return;
  }

  // Seleccionar el endpoint según la acción
  let endpoint = "";
  // Se usa la nueva variable en lugar de la cadena "procesar"
  if (accion === ACCION_PROCESAR_LOQUE_PROCESAMOS) {
    endpoint = '/api/procesar_datos_' + currentSource;
  } else if (accion === 'procesar_horario') {
    endpoint = '/api/procesar_horarios';
  } else {
    endpoint = '/recibir_datos';
  }

  fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      accion: accion,
      datos: datosSeleccionados
    })
  })
    .then(response => response.json())
    .then(result => {
      alert("Acción '" + accion + "' enviada. Respuesta: " + (result.mensaje || "Procesado con éxito"));
    })
    .catch(error => {
      console.error("Error en " + accion + ":", error);
    });
}

// Función para marcar o desmarcar todas las filas
function toggleSelectAll(selectAll = true) {
  const checkboxes = document.querySelectorAll('input.row-selector');
  checkboxes.forEach(cb => {
    cb.checked = selectAll;
    const row = cb.closest('tr');
    if (selectAll) {
      row.classList.add('selected');
    } else {
      row.classList.remove('selected');
    }
  });
}

document.addEventListener("DOMContentLoaded", function() {
  // Caso "Captar Nuevos Datos"
  if (document.getElementById("btnRecopilar")) {
    // Configuración del interruptor de fuente: Google y JustEat
    const btnGoogle = document.getElementById("btnGoogle");
    const btnJustEat = document.getElementById("btnJustEat");

    if (btnGoogle && btnJustEat) {
      btnGoogle.addEventListener("click", function() {
        currentSource = "Google";
        btnGoogle.classList.add("active");
        btnJustEat.classList.remove("active");
        cargarDatos("captar");
      });

      btnJustEat.addEventListener("click", function() {
        currentSource = "JustEat";
        btnJustEat.classList.add("active");
        btnGoogle.classList.remove("active");
        cargarDatos("captar");
      });
    }

    // Botón "Seleccionar Todo"
    const btnSelectAll = document.getElementById("btnSelectAll");
    if (btnSelectAll) {
      btnSelectAll.addEventListener("click", function() {
        toggleSelectAll(true);
      });
    }

    // Eventos propios de "Captar Nuevos Datos"
    const btnRecopilar = document.getElementById("btnRecopilar");
    if (btnRecopilar) {
      btnRecopilar.addEventListener("click", function() {
        cargarDatos("captar");
      });
    }
    const btnProcesar = document.getElementById("btnProcesar");
    if (btnProcesar) {
      // Aquí usamos la nueva variable en lugar de "procesar"
      btnProcesar.addEventListener("click", function() {
        enviarDatosAccion(ACCION_PROCESAR_LOQUE_PROCESAMOS);
      });
    }

  // Caso "Lista de Trabajo"
  } else if (document.getElementById("btnPorLlamar")) {
    // Eventos para filtrar datos
    const btnPorLlamar = document.getElementById("btnPorLlamar");
    if (btnPorLlamar) {
      btnPorLlamar.addEventListener("click", function() {
        cargarDatos("0");
      });
    }
    const btnEnProceso = document.getElementById("btnEnProceso");
    if (btnEnProceso) {
      btnEnProceso.addEventListener("click", function() {
        cargarDatos("en_proceso");
      });
    }
    const btnFinalizados = document.getElementById("btnFinalizados");
    if (btnFinalizados) {
      btnFinalizados.addEventListener("click", function() {
        cargarDatos("finalizados");
      });
    }

    // Botones para trasladar datos
    const btnTrasladar = document.getElementById("btnTrasladarLL");
    if (btnTrasladar) {
      btnTrasladar.addEventListener("click", function() {
        cargarDatos("trasladarllamadas");
      });
    }
    const btnTrasladarLL = document.getElementById("btnTrasladarLO");
    if (btnTrasladarLL) {
      btnTrasladarLL.addEventListener("click", function() {
        cargarDatos("trasladardatos");
      });
    }

    // Eventos para acciones específicas en "Lista de Trabajo"
    const btnPulirHorario = document.getElementById("btnPulirHorario");
    if (btnPulirHorario) {
      btnPulirHorario.addEventListener("click", function() {
        enviarDatosAccion("pulir_horario");
      });
    }
    const btnPulirPelidos = document.getElementById("btnPulirPelidos");
    if (btnPulirPelidos) {
      btnPulirPelidos.addEventListener("click", function() {
        enviarDatosAccion("pulir_pelidos");
      });
    }
    const btnConcatenarIntermediarios = document.getElementById("btnConcatenarIntermediarios");
    if (btnConcatenarIntermediarios) {
      btnConcatenarIntermediarios.addEventListener("click", function() {
        enviarDatosAccion("concatenar_intermediarios");
      });
    }

    // Cargar datos por defecto si ya existen las tablas
    if (document.getElementById("table-head") && document.getElementById("table-body")) {
      cargarDatos("0");
    }
  }
});
