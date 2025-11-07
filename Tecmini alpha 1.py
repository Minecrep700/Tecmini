# ==========================================================
# 🌐 TECMINI 0.1 — Plataforma Educativa Completa
# ==========================================================
# Versión: alpha 1
# Propósito: Completar e integrar el módulo de ENSEÑANZA (Cursos)
# con lecciones, progreso por usuario, evaluaciones y guardado.
#
# Este archivo implementa:
# - Registro y clasificación del usuario (nombre, edad, categoría).
# - Base de datos SQLite con tablas: usuarios, cursos, lecciones,
#   progreso, preguntas, puntajes, insignias.
# - Interfaz amigable con Tkinter para navegar entre:
#   Inicio -> Menú -> Cursos -> Lecciones -> Evaluaciones -> Minijuegos -> Ranking
# - Sistema de puntajes y guardado del progreso por usuario.
# - Comentarios detallados dentro del código explicando cada bloque.
#
# Nota: Este archivo está pensado para ser independiente y ejecutable.
# ==========================================================

import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import random
import textwrap
import datetime
import os

# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================
DB_FILE = "tecmini_cursos_alpha_1.db"

# Asegurarnos que el directorio del archivo exista (por si acaso)
if not os.path.exists(os.path.dirname(os.path.abspath(DB_FILE))):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(DB_FILE)))
    except Exception:
        # Si no se puede crear el directorio, esto no es co,
        # SQLite usará la ruta relativa actual.
        pass

# ==========================================================
# BASE DE DATOS: CREACIÓN Y POBLACIÓN INICIAL
# ==========================================================
def crear_base_datos():
    """
    Crea las tablas necesarias para el sistema:
    - usuarios: información del usuario
    - cursos: metadatos del curso
    - lecciones: contenido por lección asociado a cursos
    - progreso: registra qué lecciones completó cada usuario
    - preguntas: preguntas de evaluación vinculadas a lecciones
    - puntajes: historial de guardado de puntaje por usuario
    - insignias: medallas/insignias que el usuario obtiene
    """
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()

    # Crear tabla usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        edad INTEGER NOT NULL,
        categoria TEXT NOT NULL,
        puntos INTEGER DEFAULT 0,
        fecha_registro TEXT
    )
    """)

    # Crear tabla cursos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        descripcion TEXT,
        categoria TEXT
    )
    """)

    # Crear tabla lecciones
    # Cada lección pertenece a un curso y tiene orden (orden en curso)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lecciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        curso_id INTEGER NOT NULL,
        orden INTEGER NOT NULL,
        titulo TEXT NOT NULL,
        contenido TEXT NOT NULL,
        tipo_contenido TEXT DEFAULT 'texto', -- texto, video_placeholder, imagen_placeholder
        duracion_estimada INTEGER DEFAULT 5,
        FOREIGN KEY (curso_id) REFERENCES cursos(id)
    )
    """)

    # Crear tabla preguntas (evaluaciones por lección)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS preguntas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        leccion_id INTEGER NOT NULL,
        pregunta TEXT NOT NULL,
        opcion_correcta TEXT NOT NULL,
        opcion_incorrecta1 TEXT NOT NULL,
        opcion_incorrecta2 TEXT,
        opcion_incorrecta3 TEXT,
        puntos INTEGER DEFAULT 5,
        FOREIGN KEY (leccion_id) REFERENCES lecciones(id)
    )
    """)

    # Crear tabla progreso del usuario respecto a lecciones
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS progreso (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        leccion_id INTEGER NOT NULL,
        completado INTEGER DEFAULT 0,
        fecha_completado TEXT,
        calificacion INTEGER,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
        FOREIGN KEY (leccion_id) REFERENCES lecciones(id)
    )
    """)

    # Tabla de puntajes históricos (registro por evento)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS puntajes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        puntos INTEGER NOT NULL,
        motivo TEXT,
        fecha TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    """)

    # Tabla de insignias (badges)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS insignias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        descripcion TEXT,
        puntos_minimos INTEGER DEFAULT 0
    )
    """)

    # Tabla de insignias ganadas por usuario
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS insignias_usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        insignia_id INTEGER NOT NULL,
        fecha TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
        FOREIGN KEY (insignia_id) REFERENCES insignias(id)
    )
    """)

    conexion.commit()

    # POBLACIÓN INICIAL: cursos, lecciones, preguntas e insignias si están vacíos
    cursor.execute("SELECT COUNT(*) FROM cursos")
    if cursor.fetchone()[0] == 0:
        # Añadimos cursos demo con descripción
        cursos_demo = [
            ("Internet y su historia",
             "Breve historia del Internet: ARPANET, expansión, WWW y usos educativos.",
             "Tecnología"),
            ("Fake News: identificación y verificación",
             "Cómo reconocer noticias falsas y técnicas para verificar información.",
             "Educación Digital"),
            ("Ciberseguridad básica",
             "Buenas prácticas: contraseñas, actualizaciones, phishing y privacidad.",
             "Seguridad"),
        ]
        cursor.executemany("INSERT INTO cursos (titulo, descripcion, categoria) VALUES (?, ?, ?)", cursos_demo)
        conexion.commit()

    cursor.execute("SELECT COUNT(*) FROM lecciones")
    if cursor.fetchone()[0] == 0:
        # Recuperamos ids de cursos recién insertados
        cursor.execute("SELECT id, titulo FROM cursos")
        cursos_ids = cursor.fetchall()
        # Mapear títulos a ids
        cursos_map = {titulo: cid for cid, titulo in cursos_ids}

        # Lecciones por curso — cada tuple: (curso_titulo, orden, titulo_leccion, contenido)
        lecciones_demo = [
            ("Internet y su historia", 1, "¿Qué es Internet?", "Internet es una red global... (texto demo)."),
            ("Internet y su historia", 2, "Primeros hitos: ARPANET y TCP/IP", "ARPANET fue... (texto demo)."),
            ("Internet y su historia", 3, "La llegada del WWW y navegadores", "Tim Berners-Lee creó... (texto demo)."),

            ("Fake News: identificación y verificación", 1, "¿Qué son las Fake News?", "Las fake news son... (texto demo)."),
            ("Fake News: identificación y verificación", 2, "Técnicas para verificar una noticia", "Verificar fuentes, cross-check, fechas..."),
            ("Fake News: identificación y verificación", 3, "Ejemplo práctico: cómo verificar", "Caso práctico: buscar origen, buscar imágenes inversas..."),

            ("Ciberseguridad básica", 1, "Contraseñas seguras", "Usa contraseñas largas, mezcla de caracteres..."),
            ("Ciberseguridad básica", 2, "Phishing: correos y enlaces", "No abras enlaces, verifica remitentes..."),
            ("Ciberseguridad básica", 3, "Actualizaciones y copias de seguridad", "Mantén tu equipo actualizado y has backups."),
        ]

        for curso_t, orden, titulo_l, contenido in lecciones_demo:
            curso_id = cursos_map.get(curso_t)
            if curso_id:
                cursor.execute("""
                INSERT INTO lecciones (curso_id, orden, titulo, contenido, tipo_contenido, duracion_estimada)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (curso_id, orden, titulo_l, contenido, "texto", 5))

        conexion.commit()

    cursor.execute("SELECT COUNT(*) FROM preguntas")
    if cursor.fetchone()[0] == 0:
        # Asociar preguntas a las primeras lecciones (buscar algunos IDs)
        cursor.execute("SELECT id, titulo FROM lecciones")
        lecs = cursor.fetchall()
        # Crear preguntas dummy (1 por lección)
        preguntas_demo = []
        for leccion_id, titulo_lec in lecs:
            # Pregunta corta basada en título para demo
            pregunta = f"¿Cuál es el punto central de '{titulo_lec}'?"
            preguntas_demo.append((leccion_id, pregunta,
                                   "Respuesta correcta de ejemplo",
                                   "Opción incorrecta A",
                                   "Opción incorrecta B",
                                   "Opción incorrecta C",
                                   5))
        cursor.executemany("""
        INSERT INTO preguntas (leccion_id, pregunta, opcion_correcta, opcion_incorrecta1, opcion_incorrecta2, opcion_incorrecta3, puntos)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, preguntas_demo)
        conexion.commit()

    cursor.execute("SELECT COUNT(*) FROM insignias")
    if cursor.fetchone()[0] == 0:
        insignias_demo = [
            ("Explorador", "Completa tu primer curso", 20),
            ("Verificador", "Responde correctamente 5 preguntas de Fake News", 30),
            ("Guardían digital", "Alcanza 100 puntos", 100)
        ]
        cursor.executemany("INSERT INTO insignias (nombre, descripcion, puntos_minimos) VALUES (?, ?, ?)", insignias_demo)
        conexion.commit()

    conexion.close()

# ==========================================================
# APLICACIÓN: INTERFAZ Y LÓGICA
# ==========================================================
class TecminiCursosApp(tk.Tk):
    """
    Clase principal que controla la interfaz de usuarios, cursos,
    lecciones, evaluaciones y el sistema de puntajes/progreso.
    """
    def __init__(self):
        super().__init__()
        self.title("TECMINI Cursos - Módulo de Enseñanza")
        self.geometry("1000x700")
        self.config(bg="#F4FBF6")

        # Datos del usuario actual (serán asignados tras registro/login)
        self.usuario_id = None
        self.nombre = None
        self.edad = None
        self.categoria = None
        self.puntos = 0

        # Variables de estado UI
        self.curso_actual_id = None
        self.leccion_actual_id = None
        self.leccion_index = 0
        self.lecciones_lista = []

        # Preparar base de datos inicial y mostrar inicio
        crear_base_datos()
        self.mostrar_inicio()

    # ---------------------------
    # UTILIDADES DE BD
    # ---------------------------
    def ejecutar_query(self, query, params=(), fetchone=False, fetchall=False, commit=False):
        """Helper para ejecutar queries de SQLite de forma segura."""
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute(query, params)
        resultado = None
        if fetchone:
            resultado = cur.fetchone()
        if fetchall:
            resultado = cur.fetchall()
        if commit:
            conn.commit()
        conn.close()
        return resultado

    # ---------------------------
    # PANTALLA INICIAL: registro / login simple
    # ---------------------------
    def mostrar_inicio(self):
        """Pantalla que solicita nombre y edad, registra al usuario y clasifica."""
        for widget in self.winfo_children():
            widget.destroy()

        header = tk.Frame(self, bg="#E8F9F2")
        header.pack(fill="x")
        tk.Label(header, text="TECMINI — Cursos Interactivos", font=("Segoe UI", 24, "bold"), bg="#E8F9F2", fg="#1B5E20").pack(padx=20, pady=15)

        # Contenedor central
        cont = tk.Frame(self, bg="#F4FBF6")
        cont.pack(expand=True)

        panel = tk.Frame(cont, bg="#FFFFFF", bd=1, relief="solid")
        panel.pack(pady=30, ipadx=30, ipady=30)

        tk.Label(panel, text="Nombre", font=("Segoe UI", 14), bg="#FFFFFF").grid(row=0, column=0, sticky="w", pady=5)
        nombre_entry = tk.Entry(panel, font=("Segoe UI", 12), width=30)
        nombre_entry.grid(row=0, column=1, pady=5, padx=10)

        tk.Label(panel, text="Edad", font=("Segoe UI", 14), bg="#FFFFFF").grid(row=1, column=0, sticky="w", pady=5)
        edad_entry = tk.Entry(panel, font=("Segoe UI", 12), width=10)
        edad_entry.grid(row=1, column=1, pady=5, padx=10, sticky="w")

        # Mensaje con clasificación automática
        clasif_label = tk.Label(panel, text="", bg="#FFFFFF", font=("Segoe UI", 11, "italic"))
        clasif_label.grid(row=2, column=0, columnspan=2, pady=8)

        def actualizar_clasificacion(*args):
            try:
                edad_val = int(edad_entry.get())
                if edad_val <= 12:
                    cat = "Infantil"
                elif 13 <= edad_val <= 17:
                    cat = "Adolescente"
                else:
                    cat = "Adulto"
                clasif_label.config(text=f"Clasificación estimada: {cat}")
            except Exception:
                clasif_label.config(text="")

        edad_entry.bind("<KeyRelease>", actualizar_clasificacion)

        def registrar():
            nombre = nombre_entry.get().strip()
            try:
                edad_val = int(edad_entry.get().strip())
            except Exception:
                messagebox.showwarning("Edad inválida", "Por favor ingresa un número válido para la edad.")
                return

            if not nombre:
                messagebox.showwarning("Nombre vacío", "Por favor ingresa tu nombre.")
                return

            # Clasificar
            if edad_val <= 12:
                categoria = "Infantil"
            elif 13 <= edad_val <= 17:
                categoria = "Adolescente"
            else:
                categoria = "Adulto"

            fecha = datetime.datetime.now().isoformat(timespec='seconds')
            self.ejecutar_query("INSERT INTO usuarios (nombre, edad, categoria, puntos, fecha_registro) VALUES (?, ?, ?, ?, ?)",
                               (nombre, edad_val, categoria, 0, fecha), commit=True)
            # Recuperar el id del usuario recién insertado
            usuario_id = self.ejecutar_query("SELECT id FROM usuarios WHERE nombre=? AND fecha_registro=?", (nombre, fecha), fetchone=True)
            if usuario_id:
                self.usuario_id = usuario_id[0]
                self.nombre = nombre
                self.edad = age_val = edad_val
                self.categoria = categoria
                self.puntos = 0
                messagebox.showinfo("Registro", f"Registro exitoso. Bienvenido, {nombre} ({categoria})")
                self.mostrar_menu()
            else:
                messagebox.showerror("Error", "No se pudo registrar el usuario. Intenta de nuevo.")

        def login():
            nombre = nombre_entry.get().strip()
            if not nombre:
                messagebox.showwarning("Nombre vacío", "Ingresa el nombre con el que te registraste.")
                return
            user = self.ejecutar_query("SELECT id, edad, categoria, puntos FROM usuarios WHERE nombre=?", (nombre,), fetchone=True)
            if not user:
                messagebox.showwarning("No registrado", "Usuario no encontrado. Regístrate primero.")
                return
            self.usuario_id = user[0]
            self.nombre = nombre
            self.edad = user[1]
            self.categoria = user[2]
            self.puntos = user[3] or 0
            messagebox.showinfo("Login", f"Hola de nuevo, {self.nombre} ({self.categoria}). Bienvenido.")
            self.mostrar_menu()

        btn_frame = tk.Frame(panel, bg="#FFFFFF")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=15)
        tk.Button(btn_frame, text="Registrar", bg="#4CAF50", fg="white", font=("Segoe UI", 12), command=registrar).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Iniciar sesión", bg="#2196F3", fg="white", font=("Segoe UI", 12), command=login).pack(side="left", padx=8)

        # Nota: Si deseas, puedes pre-completar con usuarios demo para pruebas.
        demo_frame = tk.Frame(self, bg="#F4FBF6")
        demo_frame.pack(side="bottom", pady=10)
        tk.Label(demo_frame, text="Consejo: Usa un nombre nuevo o un nombre existente para cargar progreso.", bg="#F4FBF6", font=("Segoe UI", 10, "italic")).pack()

    # ---------------------------
    # MENU PRINCIPAL
    # ---------------------------
    def mostrar_menu(self):
        """Muestra el menú principal con cursos, progreso, puntajes y configuración."""
        for widget in self.winfo_children():
            widget.destroy()

        top = tk.Frame(self, bg="#E8F9F2")
        top.pack(fill="x")
        tk.Label(top, text=f"TECMINI — Bienvenido {self.nombre}", font=("Segoe UI", 20, "bold"), bg="#E8F9F2", fg="#1B5E20").pack(side="left", padx=20, pady=10)
        tk.Label(top, text=f"Puntos: {self.puntos}", font=("Segoe UI", 12, "bold"), bg="#E8F9F2").pack(side="right", padx=20)

        main = tk.Frame(self, bg="#F4FBF6")
        main.pack(expand=True, fill="both", padx=30, pady=20)

        # Panel izquierdo: lista de cursos
        left = tk.Frame(main, bg="#F4FBF6")
        left.pack(side="left", fill="y", padx=10)

        tk.Label(left, text="Cursos disponibles", font=("Segoe UI", 16, "bold"), bg="#F4FBF6").pack(anchor="w", pady=10)

        cursos = self.ejecutar_query("SELECT id, titulo, categoria FROM cursos", fetchall=True)
        for cid, titulo, cat in cursos:
            btn = tk.Button(left, text=f"{titulo} ({cat})", width=30, anchor="w", bg="#E0F2F1", command=lambda c=cid: self.abrir_curso(c))
            btn.pack(pady=4)

        # Panel derecho: acciones y progreso
        right = tk.Frame(main, bg="#F4FBF6")
        right.pack(side="right", expand=True, fill="both")

        tk.Label(right, text="Tu progreso y herramientas", font=("Segoe UI", 16, "bold"), bg="#F4FBF6").pack(anchor="w", pady=10)

        tk.Button(right, text="Ver mi progreso", width=25, bg="#A5D6A7", command=self.mostrar_progreso).pack(pady=8)
        tk.Button(right, text="Ir al Quiz global", width=25, bg="#AED581", command=self.mostrar_quiz_global).pack(pady=8)
        tk.Button(right, text="Ver Ranking", width=25, bg="#81C784", command=self.mostrar_ranking).pack(pady=8)
        tk.Button(right, text="Administrar Contenido (dev)", width=25, bg="#C5E1A5", command=self.admin_contenido).pack(pady=8)
        tk.Button(right, text="Cerrar sesión", width=25, bg="#FFCCBC", command=self.cerrar_sesion).pack(pady=8)

    # ---------------------------
    # ABRIR CURSO: listar lecciones y permitir iniciar
    # ---------------------------
    def abrir_curso(self, curso_id):
        """Muestra las lecciones del curso y permite iniciar desde la primera lección no completada."""
        for widget in self.winfo_children():
            widget.destroy()

        # Recuperar meta del curso
        curso = self.ejecutar_query("SELECT titulo, descripcion FROM cursos WHERE id=?", (curso_id,), fetchone=True)
        if not curso:
            messagebox.showerror("Error", "Curso no encontrado.")
            self.mostrar_menu()
            return
        titulo_c, descripcion = curso

        top = tk.Frame(self, bg="#E8F9F2")
        top.pack(fill="x")
        tk.Button(top, text="⬅ Volver al menú", command=self.mostrar_menu).pack(side="left", padx=10, pady=10)
        tk.Label(top, text=f"{titulo_c}", font=("Segoe UI", 20, "bold"), bg="#E8F9F2").pack(side="left", padx=20)

        # Recuperar lecciones del curso ordenadas
        lecciones = self.ejecutar_query("SELECT id, orden, titulo, duracion_estimada FROM lecciones WHERE curso_id=? ORDER BY orden ASC", (curso_id,), fetchall=True)
        if not lecciones:
            tk.Label(self, text="Este curso no tiene lecciones todavía.", font=("Segoe UI", 12), bg="#F4FBF6").pack(pady=20)
            return

        # Panel de lista de lecciones
        list_frame = tk.Frame(self, bg="#F4FBF6")
        list_frame.pack(side="left", fill="y", padx=20, pady=10)

        tk.Label(list_frame, text="Lecciones", font=("Segoe UI", 14, "bold"), bg="#F4FBF6").pack(anchor="w", pady=5)
        # Buscar progreso por usuario para este curso
        leccion_ids = [l[0] for l in lecciones]
        progreso_map = {}
        if self.usuario_id:
            # Obtener progreso de usuario sólo para estas lecciones
            placeholders = ",".join("?" for _ in leccion_ids)
            query = f"SELECT leccion_id, completado FROM progreso WHERE usuario_id=? AND leccion_id IN ({placeholders})"
            params = (self.usuario_id,) + tuple(leccion_ids)
            rows = self.ejecutar_query(query, params, fetchall=True)
            for lecid, comp in rows:
                progreso_map[lecid] = comp

        for lecid, orden, titulo_lec, dur in lecciones:
            estado = "Pendiente"
            if progreso_map.get(lecid) == 1:
                estado = "Completada"
            btn_text = f"{orden}. {titulo_lec} — {estado}"
            tk.Button(list_frame, text=btn_text, anchor="w", width=40, bg="#E0F2F1", command=lambda lid=lecid: self.abrir_leccion(lid)).pack(pady=4)

        # Panel derecho: descripción y acciones del curso
        right = tk.Frame(self, bg="#F4FBF6")
        right.pack(side="right", expand=True, fill="both", padx=20, pady=10)

        tk.Label(right, text="Descripción", font=("Segoe UI", 14, "bold"), bg="#F4FBF6").pack(anchor="w")
        txt = tk.Text(right, width=60, height=7, wrap="word", font=("Segoe UI", 11))
        txt.insert("1.0", descripcion or "Sin descripción")
        txt.config(state="disabled")
        txt.pack(pady=10)

        # Botón iniciar curso: busca la primera lección no completada
        def iniciar_curso():
            # Buscar primera lección no completada
            primer_lec = None
            for lecid, orden, titulo_lec, dur in lecciones:
                if progreso_map.get(lecid) != 1:
                    primer_lec = lecid
                    break
            if primer_lec is None:
                # Todas completadas: preguntar si quiere repasar
                res = messagebox.askyesno("Curso completo", "Ya completaste este curso. ¿Quieres repasar desde la primera lección?")
                if res:
                    primer_lec = lecciones[0][0]
                else:
                    return
            self.abrir_leccion(primer_lec)

        tk.Button(right, text="▶ Iniciar/Continuar Curso", font=("Segoe UI", 12, "bold"), bg="#81C784", command=iniciar_curso).pack(pady=10)
        tk.Button(right, text="📥 Marcar curso como completado (dev)", bg="#C8E6C9", command=lambda: self.marcar_curso_como_completado(leccion_ids)).pack(pady=6)

    def marcar_curso_como_completado(self, leccion_ids):
        """Utility dev: marca todas las lecciones de un curso como completadas por el usuario."""
        if not self.usuario_id:
            messagebox.showwarning("No logueado", "Inicia sesión primero.")
            return
        fecha = datetime.datetime.now().isoformat(timespec='seconds')
        for lid in leccion_ids:
            # verificar si ya existe
            existing = self.ejecutar_query("SELECT id FROM progreso WHERE usuario_id=? AND leccion_id=?", (self.usuario_id, lid), fetchone=True)
            if existing:
                self.ejecutar_query("UPDATE progreso SET completado=1, fecha_completado=? WHERE id=?", (fecha, existing[0]), commit=True)
            else:
                self.ejecutar_query("INSERT INTO progreso (usuario_id, leccion_id, completado, fecha_completado) VALUES (?, ?, ?, ?)",
                                    (self.usuario_id, lid, 1, fecha), commit=True)
        # Otorgar puntos por el total de lecciones
        puntos_ganados = 10 * len(leccion_ids)
        self.anotar_puntos(puntos_ganados, motivo="Completado masivo (dev)")
        messagebox.showinfo("Completado", f"Se marcaron {len(leccion_ids)} lecciones como completadas. +{puntos_ganados} pts")
        self.mostrar_menu()

    # ---------------------------
    # ABRIR LECCIÓN: mostrar contenido y evaluación
    # ---------------------------
    def abrir_leccion(self, leccion_id):
        """Muestra el contenido de la lección y su evaluación asociada."""
        for widget in self.winfo_children():
            widget.destroy()

        # Recuperar info de la lección
        lec = self.ejecutar_query("SELECT curso_id, orden, titulo, contenido, tipo_contenido, duracion_estimada FROM lecciones WHERE id=?", (leccion_id,), fetchone=True)
        if not lec:
            messagebox.showerror("Error", "Lección no encontrada.")
            self.mostrar_menu()
            return
        curso_id, orden, titulo_lec, contenido, tipo, dur = lec
        # Guardar estado actual
        self.curso_actual_id = curso_id
        self.leccion_actual_id = leccion_id

        # Header con navegación básica
        top = tk.Frame(self, bg="#E8F9F2")
        top.pack(fill="x")
        tk.Button(top, text="⬅ Volver al curso", command=lambda: self.abrir_curso(curso_id)).pack(side="left", padx=8, pady=8)
        tk.Label(top, text=f"Lección {orden}: {titulo_lec}", font=("Segoe UI", 16, "bold"), bg="#E8F9F2").pack(side="left", padx=20)

        # Contenido
        content_frame = tk.Frame(self, bg="#F4FBF6")
        content_frame.pack(expand=True, fill="both", padx=20, pady=10)

        # Mostrar el contenido (texto y placeholders)
        text_widget = tk.Text(content_frame, wrap="word", font=("Segoe UI", 12), padx=10, pady=10, height=18)
        text_widget.insert("1.0", contenido)
        text_widget.config(state="disabled")
        text_widget.pack(expand=True, fill="both")

        # Panel inferior: acciones: marcar completado, ir a evaluación, siguiente / anterior
        action_frame = tk.Frame(self, bg="#F4FBF6")
        action_frame.pack(fill="x", pady=10)

        # Verificar si ya completó
        prog = self.ejecutar_query("SELECT id, completado, calificacion FROM progreso WHERE usuario_id=? AND leccion_id=?", (self.usuario_id, leccion_id), fetchone=True)
        completado = False
        calificacion = None
        if prog:
            completado = bool(prog[1])
            calificacion = prog[2]

        status_lbl = tk.Label(action_frame, text=f"Estado: {'Completada' if completado else 'Pendiente'}    Calificación: {calificacion if calificacion is not None else 'N/A'}", bg="#F4FBF6", font=("Segoe UI", 11, "italic"))
        status_lbl.pack(side="left", padx=10)

        def marcar_como_completada():
            fecha = datetime.datetime.now().isoformat(timespec='seconds')
            if prog:
                # actualizar
                self.ejecutar_query("UPDATE progreso SET completado=1, fecha_completado=? WHERE id=?", (fecha, prog[0]), commit=True)
            else:
                self.ejecutar_query("INSERT INTO progreso (usuario_id, leccion_id, completado, fecha_completado) VALUES (?, ?, ?, ?)",
                                    (self.usuario_id, leccion_id, 1, fecha), commit=True)
            # otorgar puntos por completar la lección
            puntos = 10
            self.anotar_puntos(puntos, motivo=f"Completó lección {titulo_lec}")
            messagebox.showinfo("Completado", f"Lección marcada como completada. +{puntos} pts")
            self.abrir_curso(curso_id)

        def ir_a_evaluacion():
            self.mostrar_evaluacion(leccion_id)

        tk.Button(action_frame, text="✔ Marcar como completada", bg="#66BB6A", command=marcar_como_completada).pack(side="right", padx=8)
        tk.Button(action_frame, text="📝 Ir a evaluación", bg="#FFC107", command=ir_a_evaluacion).pack(side="right", padx=8)

        # Navegación: siguiente y anterior
        # Obtener lista de lecciones del curso para navegar
        lecs = self.ejecutar_query("SELECT id FROM lecciones WHERE curso_id=? ORDER BY orden ASC", (curso_id,), fetchall=True)
        lecs_ids = [r[0] for r in lecs]
        try:
            idx = lecs_ids.index(leccion_id)
        except ValueError:
            idx = 0

        def ir_a_indice(nidx):
            if 0 <= nidx < len(lecs_ids):
                self.abrir_leccion(lecs_ids[nidx])

        nav_frame = tk.Frame(self, bg="#F4FBF6")
        nav_frame.pack(fill="x", pady=4)
        tk.Button(nav_frame, text="<< Anterior", command=lambda: ir_a_indice(idx-1)).pack(side="left", padx=8)
        tk.Button(nav_frame, text="Siguiente >>", command=lambda: ir_a_indice(idx+1)).pack(side="right", padx=8)

    # ---------------------------
    # EVALUACIÓN: preguntas vinculadas a lección
    # ---------------------------
    def mostrar_evaluacion(self, leccion_id):
        """Muestra preguntas asociadas a la lección y califica."""
        for widget in self.winfo_children():
            widget.destroy()

        # Cargar preguntas de la lección (hay 0 o varias)
        preguntas = self.ejecutar_query("SELECT id, pregunta, opcion_correcta, opcion_incorrecta1, opcion_incorrecta2, opcion_incorrecta3, puntos FROM preguntas WHERE leccion_id=?", (leccion_id,), fetchall=True)
        if not preguntas:
            messagebox.showinfo("Evaluación", "No hay evaluación para esta lección.")
            self.abrir_leccion(leccion_id)
            return

        # Estado para seguimiento
        respuestas_usuario = {}
        total_puntos_posibles = sum(p[-1] for p in preguntas)

        # Interfaz
        top = tk.Frame(self, bg="#E8F9F2")
        top.pack(fill="x")
        tk.Button(top, text="⬅ Volver a la lección", command=lambda: self.abrir_leccion(leccion_id)).pack(side="left", padx=8, pady=8)
        tk.Label(top, text="Evaluación — Responde las preguntas", font=("Segoe UI", 16, "bold"), bg="#E8F9F2").pack(padx=20, pady=10)

        canvas = tk.Canvas(self, bg="#F4FBF6")
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        frame = tk.Frame(canvas, bg="#F4FBF6")
        canvas.create_window((0,0), window=frame, anchor='nw')
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Para cada pregunta, mostrar opciones radio
        vars_list = []
        for idx, p in enumerate(preguntas, start=1):
            pid = p[0]
            texto = p[1]
            correcta = p[2]
            opts = [correcta]
            # incluir opciones incorrectas si no son None
            for opt in p[3:6]:
                if opt:
                    opts.append(opt)
            random.shuffle(opts)

            qframe = tk.LabelFrame(frame, text=f"Pregunta {idx}", font=("Segoe UI", 12, "bold"), bg="#F4FBF6")
            qframe.pack(fill="x", padx=10, pady=6)
            tk.Label(qframe, text=texto, wraplength=800, justify="left", bg="#F4FBF6", font=("Segoe UI", 11)).pack(anchor="w", padx=10, pady=4)
            var = tk.StringVar(value="")
            vars_list.append((pid, p[-1], correcta, var))
            for opt in opts:
                tk.Radiobutton(qframe, text=opt, variable=var, value=opt, bg="#F4FBF6", anchor="w").pack(fill="x", padx=20, pady=2)

        # Botón de enviar evaluación
        def enviar_evaluacion():
            # calcular calificación
            puntos_obtenidos = 0
            por_pregunta = []
            for pid, pts, correcta, var in vars_list:
                sel = var.get()
                if sel == correcta:
                    puntos_obtenidos += pts
                    por_pregunta.append((pid, True, pts))
                else:
                    por_pregunta.append((pid, False, 0))
            # Guardar progreso y calificación en tabla progreso
            fecha = datetime.datetime.now().isoformat(timespec='seconds')
            # marcar la lección como completada y guardar calificación
            existing = self.ejecutar_query("SELECT id FROM progreso WHERE usuario_id=? AND leccion_id=?", (self.usuario_id, leccion_id), fetchone=True)
            if existing:
                self.ejecutar_query("UPDATE progreso SET completado=1, fecha_completado=?, calificacion=? WHERE id=?", (fecha, puntos_obtenidos, existing[0]), commit=True)
            else:
                self.ejecutar_query("INSERT INTO progreso (usuario_id, leccion_id, completado, fecha_completado, calificacion) VALUES (?, ?, ?, ?, ?)",
                                    (self.usuario_id, leccion_id, 1, fecha, puntos_obtenidos), commit=True)
            # Otorgar puntos en función de puntos obtenidos (puede escalar)
            puntos_para_usuario = puntos_obtenidos  # esquema: 1:1
            if puntos_para_usuario > 0:
                self.anotar_puntos(puntos_para_usuario, motivo=f"Evaluación lección {leccion_id}")
            # Mostrar resultado
            messagebox.showinfo("Evaluación enviada", f"Obtuviste {puntos_obtenidos} / {total_puntos_posibles} puntos en esta evaluación.\nHas ganado {puntos_para_usuario} pts.")
            self.abrir_leccion(leccion_id)

        tk.Button(frame, text="📤 Enviar evaluación", bg="#4CAF50", fg="white", font=("Segoe UI", 12, "bold"), command=enviar_evaluacion).pack(pady=16)

    # ---------------------------
    # FUNCIONES DE PUNTOS E INSIGNIAS
    # ---------------------------
    def anotar_puntos(self, puntos, motivo=""):
        """Añade puntos al usuario, registra en historial y comprueba insignias."""
        if not self.usuario_id:
            return
        # Actualizar puntos totales en usuarios
        usuario = self.ejecutar_query("SELECT puntos FROM usuarios WHERE id=?", (self.usuario_id,), fetchone=True)
        if usuario:
            nuevos = (usuario[0] or 0) + puntos
            self.ejecutar_query("UPDATE usuarios SET puntos=? WHERE id=?", (nuevos, self.usuario_id), commit=True)
            self.puntos = nuevos
            # Registrar en tabla de puntajes
            fecha = datetime.datetime.now().isoformat(timespec='seconds')
            self.ejecutar_query("INSERT INTO puntajes (usuario_id, puntos, motivo, fecha) VALUES (?, ?, ?, ?)",
                                (self.usuario_id, puntos, motivo, fecha), commit=True)
            # Comprobar insignias
            self.comprobar_insignias()

    def comprobar_insignias(self):
        """Otorga insignias si el usuario cumple requisitos de puntos mínimos."""
        if not self.usuario_id:
            return
        # Recuperar puntos actuales
        usuario = self.ejecutar_query("SELECT puntos FROM usuarios WHERE id=?", (self.usuario_id,), fetchone=True)
        if not usuario:
            return
        puntos = usuario[0] or 0
        # Buscar insignias que el usuario no tenga y cuyo puntos_minimos <= puntos
        insignias = self.ejecutar_query("SELECT id, nombre, puntos_minimos FROM insignias WHERE puntos_minimos <= ?", (puntos,), fetchall=True)
        for ins_id, nombre, puntos_req in insignias:
            ya_tiene = self.ejecutar_query("SELECT id FROM insignias_usuario WHERE usuario_id=? AND insignia_id=?", (self.usuario_id, ins_id), fetchone=True)
            if not ya_tiene:
                fecha = datetime.datetime.now().isoformat(timespec='seconds')
                self.ejecutar_query("INSERT INTO insignias_usuario (usuario_id, insignia_id, fecha) VALUES (?, ?, ?)", (self.usuario_id, ins_id, fecha), commit=True)
                messagebox.showinfo("¡Insignia obtenida!", f"Has obtenido la insignia '{nombre}' por alcanzar {puntos_req} puntos.")

    # ---------------------------
    # PROGRESO: ver lecciones completadas
    # ---------------------------
    def mostrar_progreso(self):
        """Muestra un resumen del progreso del usuario (por curso, lecciones completadas)."""
        if not self.usuario_id:
            messagebox.showwarning("No logueado", "Inicia sesión o regístrate primero.")
            return

        for widget in self.winfo_children():
            widget.destroy()

        top = tk.Frame(self, bg="#E8F9F2")
        top.pack(fill="x")
        tk.Button(top, text="⬅ Volver", command=self.mostrar_menu).pack(side="left", padx=10, pady=8)
        tk.Label(top, text="Tu progreso", font=("Segoe UI", 18, "bold"), bg="#E8F9F2").pack(padx=20, pady=8)

        # Obtener cursos y conteo de lecciones/completadas
        cursos = self.ejecutar_query("SELECT id, titulo FROM cursos", fetchall=True)
        container = tk.Frame(self, bg="#F4FBF6")
        container.pack(fill="both", expand=True, padx=20, pady=10)
        for cid, titulo in cursos:
            total = self.ejecutar_query("SELECT COUNT(*) FROM lecciones WHERE curso_id=?", (cid,), fetchone=True)[0]
            completadas = self.ejecutar_query("""SELECT COUNT(*) FROM progreso p
                                                JOIN lecciones l ON p.leccion_id=l.id
                                                WHERE p.usuario_id=? AND l.curso_id=? AND p.completado=1""", (self.usuario_id, cid), fetchone=True)[0]
            porcentaje = int((completadas/total)*100) if total > 0 else 0
            frame = tk.Frame(container, bg="#FFFFFF", bd=1, relief="solid")
            frame.pack(fill="x", pady=6)
            tk.Label(frame, text=f"{titulo}", font=("Segoe UI", 14, "bold"), bg="#FFFFFF").pack(anchor="w", padx=10, pady=4)
            tk.Label(frame, text=f"{completadas} / {total} lecciones completadas — {porcentaje} %", bg="#FFFFFF", font=("Segoe UI", 11)).pack(anchor="w", padx=10)
            progress = ttk.Progressbar(frame, length=300, value=porcentaje)
            progress.pack(padx=10, pady=8)

        # Ver insignias obtenidas
        insignias = self.ejecutar_query("""SELECT i.nombre, i.descripcion, iu.fecha
                                          FROM insignias_usuario iu JOIN insignias i ON iu.insignia_id=i.id
                                          WHERE iu.usuario_id=?""", (self.usuario_id,), fetchall=True)
        tk.Label(container, text="Insignias obtenidas:", font=("Segoe UI", 14, "bold"), bg="#F4FBF6").pack(anchor="w", pady=6)
        if insignias:
            for nombre, desc, fecha in insignias:
                tk.Label(container, text=f"🏅 {nombre} — {desc} ({fecha})", bg="#F4FBF6").pack(anchor="w", padx=10)
        else:
            tk.Label(container, text="Aún no tienes insignias. Sigue aprendiendo para obtenerlas!", bg="#F4FBF6").pack(anchor="w", padx=10, pady=6)

    # ---------------------------
    # QUIZ GLOBAL (aleatorio)
    # ---------------------------
    def mostrar_quiz_global(self):
        """Muestra preguntas aleatorias de la base de preguntas (global)."""
        for widget in self.winfo_children():
            widget.destroy()

        top = tk.Frame(self, bg="#E8F9F2")
        top.pack(fill="x")
        tk.Button(top, text="⬅ Volver", command=self.mostrar_menu).pack(side="left", padx=10, pady=8)
        tk.Label(top, text="Quiz Global", font=("Segoe UI", 18, "bold"), bg="#E8F9F2").pack(padx=10, pady=8)

        # Seleccionar 5 preguntas al azar
        preguntas = self.ejecutar_query("SELECT id, pregunta, opcion_correcta, opcion_incorrecta1, opcion_incorrecta2, opcion_incorrecta3, puntos FROM preguntas ORDER BY RANDOM() LIMIT 5", fetchall=True)
        if not preguntas:
            tk.Label(self, text="No hay preguntas en la base de datos.", bg="#F4FBF6").pack(pady=20)
            tk.Button(self, text="⬅ Volver", command=self.mostrar_menu).pack(pady=10)
            return

        canvas = tk.Canvas(self, bg="#F4FBF6")
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)
        frame = tk.Frame(canvas, bg="#F4FBF6")
        canvas.create_window((0,0), window=frame, anchor='nw')
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        vars_q = []
        total_possible = 0
        for idx, p in enumerate(preguntas, start=1):
            pid = p[0]
            texto = p[1]
            correcta = p[2]
            opts = [correcta] + [o for o in p[3:6] if o]
            random.shuffle(opts)
            puntos = p[-1]
            total_possible += puntos

            qf = tk.LabelFrame(frame, text=f"Pregunta {idx} — {puntos} pts", bg="#F4FBF6")
            qf.pack(fill="x", padx=10, pady=6)
            tk.Label(qf, text=texto, wraplength=800, justify="left", bg="#F4FBF6").pack(anchor="w", padx=8, pady=4)
            var = tk.StringVar(value="")
            vars_q.append((pid, correcta, puntos, var))
            for opt in opts:
                tk.Radiobutton(qf, text=opt, variable=var, value=opt, bg="#F4FBF6").pack(anchor="w", padx=12)

        def enviar_quiz_global():
            puntos_obtenidos = 0
            for pid, correcta, pts, var in vars_q:
                if var.get() == correcta:
                    puntos_obtenidos += pts
            # Guardar puntos en historial y usuario
            self.anotar_puntos(puntos_obtenidos, motivo="Quiz global")
            messagebox.showinfo("Resultado", f"Has obtenido {puntos_obtenidos} pts en el quiz global (máx {total_possible}).")
            self.mostrar_menu()

        tk.Button(frame, text="Enviar respuestas", bg="#4CAF50", fg="white", command=enviar_quiz_global).pack(pady=12)

    # ---------------------------
    # RANKING: top usuarios por puntos
    # ---------------------------
    def mostrar_ranking(self):
        for widget in self.winfo_children():
            widget.destroy()

        top = tk.Frame(self, bg="#E8F9F2")
        top.pack(fill="x")
        tk.Button(top, text="⬅ Volver", command=self.mostrar_menu).pack(side="left", padx=10, pady=8)
        tk.Label(top, text="🏆 Ranking de usuarios", font=("Segoe UI", 18, "bold"), bg="#E8F9F2").pack(pady=8)

        ranking = self.ejecutar_query("SELECT nombre, categoria, puntos FROM usuarios ORDER BY puntos DESC LIMIT 20", fetchall=True)
        frame = tk.Frame(self, bg="#F4FBF6")
        frame.pack(padx=20, pady=10, fill="both", expand=True)
        for i, (nombre, cat, puntos) in enumerate(ranking, start=1):
            tk.Label(frame, text=f"{i}. {nombre} ({cat}) — {puntos} pts", bg="#F4FBF6", font=("Segoe UI", 12)).pack(anchor="w", pady=2)

    # ---------------------------
    # ADMIN: añadir curso/lección/pregunta (dev helper)
    # ---------------------------
    def admin_contenido(self):
        """Simple interfaz para añadir cursos/lecciones/preguntas (no robusta)."""
        for widget in self.winfo_children():
            widget.destroy()

        top = tk.Frame(self, bg="#E8F9F2")
        top.pack(fill="x")
        tk.Button(top, text="⬅ Volver", command=self.mostrar_menu).pack(side="left", padx=10, pady=8)
        tk.Label(top, text="Administrar contenido (dev)", font=("Segoe UI", 18, "bold"), bg="#E8F9F2").pack(pady=8)

        frame = tk.Frame(self, bg="#F4FBF6")
        frame.pack(padx=20, pady=10, fill="both", expand=True)

        # Sección crear curso
        tk.Label(frame, text="Crear nuevo curso", font=("Segoe UI", 14, "bold"), bg="#F4FBF6").grid(row=0, column=0, sticky="w")
        tk.Label(frame, text="Título:", bg="#F4FBF6").grid(row=1, column=0, sticky="w")
        title_e = tk.Entry(frame, width=50)
        title_e.grid(row=1, column=1, sticky="w")
        tk.Label(frame, text="Descripción:", bg="#F4FBF6").grid(row=2, column=0, sticky="nw")
        desc_e = tk.Text(frame, width=50, height=5)
        desc_e.grid(row=2, column=1, sticky="w")

        def crear_curso():
            t = title_e.get().strip()
            d = desc_e.get("1.0", "end").strip()
            if not t:
                messagebox.showwarning("Título vacío", "Ingresa un título para el curso.")
                return
            self.ejecutar_query("INSERT INTO cursos (titulo, descripcion) VALUES (?, ?)", (t, d), commit=True)
            messagebox.showinfo("Curso creado", f"Curso '{t}' creado.")
            self.mostrar_menu()

        tk.Button(frame, text="Crear curso", bg="#4CAF50", fg="white", command=crear_curso).grid(row=3, column=1, sticky="w", pady=8)

        # Sección crear lección
        tk.Label(frame, text="Crear lección (para curso existente)", font=("Segoe UI", 14, "bold"), bg="#F4FBF6").grid(row=4, column=0, columnspan=2, pady=10, sticky="w")
        tk.Label(frame, text="Curso (ID):", bg="#F4FBF6").grid(row=5, column=0, sticky="w")
        curso_id_e = tk.Entry(frame, width=10)
        curso_id_e.grid(row=5, column=1, sticky="w")
        tk.Label(frame, text="Orden:", bg="#F4FBF6").grid(row=6, column=0, sticky="w")
        orden_e = tk.Entry(frame, width=10)
        orden_e.grid(row=6, column=1, sticky="w")
        tk.Label(frame, text="Título lección:", bg="#F4FBF6").grid(row=7, column=0, sticky="w")
        titulo_lec_e = tk.Entry(frame, width=50)
        titulo_lec_e.grid(row=7, column=1, sticky="w")
        tk.Label(frame, text="Contenido:", bg="#F4FBF6").grid(row=8, column=0, sticky="nw")
        contenido_lec_e = tk.Text(frame, width=50, height=6)
        contenido_lec_e.grid(row=8, column=1, sticky="w")

        def crear_leccion():
            try:
                cid = int(curso_id_e.get().strip())
                orden = int(orden_e.get().strip())
            except Exception:
                messagebox.showwarning("Datos inválidos", "Curso ID y orden deben ser números.")
                return
            titulo = titulo_lec_e.get().strip()
            contenido = contenido_lec_e.get("1.0", "end").strip()
            if not titulo or not contenido:
                messagebox.showwarning("Faltan datos", "Completa título y contenido.")
                return
            self.ejecutar_query("INSERT INTO lecciones (curso_id, orden, titulo, contenido) VALUES (?, ?, ?, ?)", (cid, orden, titulo, contenido), commit=True)
            messagebox.showinfo("Lección creada", f"Lección '{titulo}' creada.")
            self.mostrar_menu()

        tk.Button(frame, text="Crear lección", bg="#4CAF50", fg="white", command=crear_leccion).grid(row=9, column=1, sticky="w", pady=6)

    # ---------------------------
    # CERRAR SESIÓN
    # ---------------------------
    def cerrar_sesion(self):
        self.usuario_id = None
        self.nombre = None
        self.edad = None
        self.categoria = None
        self.puntos = 0
        messagebox.showinfo("Sesión cerrada", "Has cerrado la sesión.")
        self.mostrar_inicio()

# ==========================================================
# EJECUCIÓN PRINCIPAL
# ==========================================================
if __name__ == "__main__":
    # Ejecutar app
    app = TecminiCursosApp()
    app.mainloop()
