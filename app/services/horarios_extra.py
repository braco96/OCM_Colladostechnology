#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 22 13:28:24 2025

@author: luis
"""
import re
import datetime

class HorarioProcessor:
    def __init__(self, texto):
        """
        Inicializa el procesador con el texto a procesar.
        """
        # Reemplaza espacios no separables por espacios normales
        self.texto = texto.replace('\xa0', ' ')
        # Diccionario para mapear variantes de días a su forma canónica (sin tildes)
        self.dias_canon = {
            "lunes": "lunes",
            "martes": "martes",
            "miércoles": "miercoles",
            "miercoles": "miercoles",
            "jueves": "jueves",
            "viernes": "viernes",
            "sábado": "sabado",
            "sabado": "sabado",
            "domingo": "domingo"
        }

    def procesar(self):
        """
        Procesa el texto y retorna un diccionario donde cada clave es el día canónico
        y el valor es una lista de intervalos de hora. Cada intervalo se representa como una lista
        de dos elementos (hora de apertura y hora de cierre). Si se detecta "cerrado", se asigna una lista vacía.
        
        Ejemplo de resultado:
          {
              'miercoles': [['12:00', '24:00']],
              'jueves': [['12:00', '24:00']],
              'viernes': [['12:00', '24:00']],
              ...
          }
        """
        horarios = {}
        # Separa el texto en segmentos usando ';' como delimitador
        segmentos = self.texto.split(";")
        for seg in segmentos:
            seg = seg.strip()
            if not seg:
                continue

            # Separa cada segmento usando ',' para extraer el día y la información
            partes = seg.split(",")
            if len(partes) < 2:
                continue

            # El primer elemento se asume que contiene el día (puede incluir paréntesis u otro texto)
            dia_raw = partes[0].strip().lower()
            dia_canon = None
            for dia_variant, dia_norm in self.dias_canon.items():
                if dia_raw.startswith(dia_variant):
                    dia_canon = dia_norm
                    break
            if not dia_canon:
                continue

            # Une el resto de la información
            info = ",".join(partes[1:]).strip()

            # Si se detecta "cerrado", se asigna un intervalo vacío
            if "cerrado" in info.lower():
                horarios[dia_canon] = []
                continue

            # Extrae todos los patrones de hora en formato HH:MM
            times = re.findall(r'(\d{1,2}:\d{2})', info)
            if times:
                # Si el número de tiempos es par, los agrupamos en pares (cada par es un intervalo)
                if len(times) % 2 == 0:
                    intervals = [times[i:i+2] for i in range(0, len(times), 2)]
                else:
                    # Si el número de tiempos no es par, se deja la lista tal cual
                    intervals = times
                horarios[dia_canon] = intervals
        return horarios

    def esta_abierto(self):
        """
        Determina si actualmente (fecha y hora de hoy) se encuentra abierto según
        el calendario procesado en self.texto.

        Retorna:
          True si la hora actual (formato HH:MM) cae dentro de algún intervalo definido
          para el día de hoy; False en caso contrario.
        """
        # Mapeo del día actual (0=lunes, 6=domingo) a nuestro formato canónico
        dias_map = {
            0: "lunes",
            1: "martes",
            2: "miercoles",
            3: "jueves",
            4: "viernes",
            5: "sabado",
            6: "domingo"
        }
        ahora = datetime.datetime.now()
        dia_actual = dias_map[ahora.weekday()]
        hora_actual = ahora.strftime("%H:%M")
        
        # Función auxiliar para convertir "HH:MM" a minutos desde medianoche
        def tiempo_a_minutos(t):
            h, m = map(int, t.split(":"))
            return h * 60 + m

        minutos_actuales = tiempo_a_minutos(hora_actual)
        horarios = self.procesar()
        if dia_actual not in horarios:
            return False
        
        for intervalo in horarios[dia_actual]:
            if isinstance(intervalo, list) and len(intervalo) == 2:
                apertura, cierre = intervalo
            else:
                continue
            # Si la hora de cierre es "24:00", se trata como "23:59"
            if cierre == "24:00":
                cierre = "23:59"
            inicio = tiempo_a_minutos(apertura)
            fin = tiempo_a_minutos(cierre)
            if inicio <= minutos_actuales <= fin:
                return True
        
        return False


# Ejemplo de uso:
if __name__ == "__main__":
    # Supón que obtienes el calendario (por ejemplo, desde la BD) y lo asignas a "ejemplo_texto"
    ejemplo_texto = "Lunes, 08:00, 14:00; Martes, 08:00, 14:00; Miércoles, 08:00, 14:00; Jueves, 08:00, 14:00; Viernes, 08:00, 14:00; Sábado, 10:00, 12:00; Domingo, cerrado"
    processor = HorarioProcessor(ejemplo_texto)
    intervalos = processor.procesar()
    print("Intervalos extraídos:", intervalos)
    
    if processor.esta_abierto():
        print("Actualmente: ABIERTO")
    else:
        print("Actualmente: CERRADO")
