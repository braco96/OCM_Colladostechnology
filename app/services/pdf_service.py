#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 17:00:51 2025

@author: luis
"""
from bbdd import DatabaseManager
db_manager = DatabaseManager(
      host="localhost",
      user="root",
      password="collado",
      database="restaurantes_db"
  )
db_manager.conectar()
db_manager.generar_pdf("hola")