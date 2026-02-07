import flet as ft
import firebase_service
import threading
import time
import os
import calendar
import datetime

# Nombre del archivo de credenciales
# Nombre del archivo de credenciales
CREDENTIALS_FILE = "jonascuts-5aac9-firebase-adminsdk-fbsvc-2de12c37aa.json"

import sys

def resource_path(relative_path):
    """ Obtener ruta absoluta al recurso, funciona para dev y para PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main(page: ft.Page):
    page.title = "Gestor de Citas"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 500
    page.window_height = 700
    
    # --- ESTADO Y VARIABLES ---
    today = datetime.date.today()
    current_month_year = [today.month, today.year] # Lista mutable para navegar meses
    day_controls_map = {} # Mapa "YYYY-MM-DD" -> ft.Column (donde añadir citas)
    appointments_by_date = {} # Mapa "YYYY-MM-DD" -> list[dict] (datos completos)

    # --- DIALOGS (DEFINIDOS MAS ABAJO PARA USAR EL OVERLAY) ---
    # Borramos las definiciones antiguas que usaban page.dialog para evitar conflictos
    # Se redefinirán más abajo junto con el main_stack para tener acceso al overlay


    def show_day_appointments(date_str):
        print(f"DEBUG: Click en día {date_str}")
        try:
            citas_dia = appointments_by_date.get(date_str, [])
            
            if not citas_dia:
                content = ft.Text("No hay citas para este día.")
            else:
                lista_citas = ft.ListView(expand=True, spacing=10)
                for cita in citas_dia:
                    item = ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.PERSON),
                            ft.Column([
                                ft.Text(cita.get('nombre', 'Sin Nombre'), weight="bold"),
                                ft.Text(f"{cita.get('hora', '--:--')}", size=12, color="grey")
                            ])
                        ]),
                        padding=10,
                        bgcolor="white",
                        border_radius=5,
                        border=ft.border.all(1, "grey300"),
                        on_click=lambda e, c=cita: show_appointment_details(c),
                        ink=True
                    )
                    lista_citas.controls.append(item)
                content = ft.Container(content=lista_citas, height=300, width=400)

            dlg = ft.AlertDialog(
                title=ft.Text(f"Citas del {date_str}"),
                content=content,
                actions=[
                    ft.TextButton("Cerrar", on_click=lambda e: close_dialog(dlg))
                ],
            )
            page.dialog = dlg
            dlg.open = True
            page.update()
            print("DEBUG: Dialogo abierto")
        except Exception as e:
            print(f"ERROR al abrir dialogo: {e}")
            status_text.value = f"Error UI: {e}"
            status_text.update()

    # --- DATOS TEMPORALES ---
    # (El resto sigue igual)



    # --- COMPONENTES UI ---
    
    # 1. LISTA DE CITAS (ListView maneja su propio scroll y es eficiente)
    citas_list = ft.ListView(expand=True, spacing=10)
    
    # 2. CALENDARIO
    calendar_grid = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def build_calendar_view(year, month):
        day_controls_map.clear()
        calendar_grid.controls.clear()
        
        # Cabecera del mes
        month_name = calendar.month_name[month]
        calendar_grid.controls.append(
            ft.Container(
                content=ft.Text(f"{month_name} {year}", size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                padding=10,
                alignment=ft.Alignment(0, 0)
            )
        )
        
        # Cabecera de días (L M X J V S D)
        days_header = ft.Row(
            controls=[ft.Text(d, weight="bold", width=40, text_align="center") for d in ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY
        )
        calendar_grid.controls.append(days_header)

        # Matriz del mes
        cal = calendar.monthcalendar(year, month)
        
        for week in cal:
            week_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY)
            for day in week:
                if day == 0:
                    # Día vacío (pertenece a otro mes)
                    week_row.controls.append(ft.Container(width=40, height=50))
                else:
                    # Crear celda del día
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    
                    # Contenedor para los puntitos/citas del día
                    citas_container = ft.Column(spacing=2, height=30)
                    day_controls_map[date_str] = citas_container
                    
                    # Color del día actual
                    bg_color = "transparent"
                    if day == today.day and month == today.month and year == today.year:
                        bg_color = "blue100"

                    day_cell = ft.Container(
                        content=ft.Column([
                            ft.Text(str(day), weight="bold", size=12),
                            citas_container
                        ], spacing=0, alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        width=40,
                        height=50,
                        border=ft.border.all(1, "grey300"),
                        border_radius=5,
                        bgcolor=bg_color,
                        padding=2,
                        on_click=lambda e, d=date_str: show_day_appointments(d),
                        ink=True,
                    )
                    week_row.controls.append(day_cell)
            
            calendar_grid.controls.append(week_row)
        
        page.update()

    # Construir calendario inicial
    build_calendar_view(today.year, today.month)

    # --- LÓGICA DE ACTUALIZACIÓN ---
    status_text = ft.Text("Iniciando...", size=12, color="grey")
    total_citas_text = ft.Text("Citas: 0", size=12, weight="bold")

    def agregar_cita_ui(batch_data):
        # Si llega un solo dict (por retrocompatibilidad o prueba), lo convertimos a lista
        if isinstance(batch_data, dict):
            batch_data = [batch_data]
            
        print(f"DEBUG: Procesando lote de {len(batch_data)} citas")
        
        last_name = ""
        count_ok = 0
        new_cards = []
        
        for doc_data in batch_data:
            try:
                nombre = doc_data.get("nombre", "Sin nombre")
                fecha = doc_data.get("fecha", "")  # Esperamos YYYY-MM-DD
                hora = doc_data.get("hora", "")
                telefono = doc_data.get("telefono", "")
                last_name = nombre
                
                # Guardar datos completos en memoria
                if fecha not in appointments_by_date:
                    appointments_by_date[fecha] = []
                # Evitar duplicados si reprograma logica (opcional, por ahora append simple)
                appointments_by_date[fecha].append(doc_data)

                # 1. Crear tarjeta
                card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(icon="person", color="blue", size=16),
                            ft.Text(nombre, weight="bold", color="black")
                        ]),
                        ft.Text(f"{fecha} - {hora}", color="black"),
                        ft.Text(telefono, size=12, color="grey")
                    ]),
                    padding=10,
                    bgcolor="white",
                    border_radius=8,
                    border=ft.border.all(1, "blue100"),
                    margin=ft.margin.only(bottom=5),
                    width=400 # Forzar ancho
                )
                new_cards.append(card)

                # 2. Actualizar CALENDARIO
                if fecha in day_controls_map:
                    indicator = ft.Container(
                        bgcolor="blue",
                        width=30,
                        height=4,  # Una barrita azul
                        border_radius=2,
                        tooltip=f"{hora} - {nombre}"
                    )
                    day_controls_map[fecha].controls.append(indicator)
                
                count_ok += 1
            except Exception as e:
                print(f"ERROR procesando una cita individual: {e} - Data: {doc_data}")
        
        # --- ACTUALIZACIÓN MASIVA EFICIENTE ---
        if new_cards:
            # Concatenamos de golpe (mucho más rápido que insertar uno a uno)
            citas_list.controls = new_cards + citas_list.controls

        status_text.value = f"Última: {last_name} ({time.strftime('%H:%M:%S')})"
        total_citas_text.value = f"Citas: {len(citas_list.controls)}"
        
        # Actualizar UI
        status_text.update()
        total_citas_text.update()
        citas_list.update()
        calendar_grid.update()
        
        print(f"DEBUG: Lote procesado. Éxito: {count_ok}/{len(batch_data)}")

    # --- ESTRUCTURA PRINCIPAL (TABS) ---
    
    # --- ESTRUCTURA PRINCIPAL (VISIBILIDAD) ---
    
    # En lugar de sacar y meter controles (que a veces falla), 
    # los dejamos todos quietos y ocultamos/mostramos.
    
    # Contenedor para el calendario (para darle padding)
    calendar_container = ft.Container(content=calendar_grid, padding=10, visible=False, expand=True)
    
    # 1. LISTA DE CITAS (Wrapper para fondo)
    # Volvemos a Column, ahora que la estructura superior es correcta (Stack).
    # Column suele ser más "robusta" que ListView para mostrar cosas simples.
    citas_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)
    
    # Añadir item de prueba SIMPLE
    citas_list.controls.append(
        ft.Text("SI LEES ESTO, LA MJORA FUNCIONÓ", size=30, weight="bold", color="red", bgcolor="yellow")
    )

    citas_view = ft.Container(
        content=citas_list,
        bgcolor="#f0f0f0", # Gris muy claro
        expand=True,
        visible=True,
        alignment=ft.Alignment(0, -1) # Asegurar que se pinten arriba
    )

    # --- OVERLAY PERSONALIZADO (Reemplazo de Dialogs) ---
    dialog_overlay = ft.Container(
        visible=False,
        bgcolor="#80000000", # Negro al 50% de opacidad (Hex ARGB o RGBA según backend, Flet suele aceptar #AARRGGBB)
        alignment=ft.Alignment(0, 0), # Center
        expand=True,
        on_click=lambda e: close_dialog(None), # Click fuera cierra
    )

    def close_dialog(e):
        dialog_overlay.visible = False
        dialog_overlay.content = None
        dialog_overlay.update()

    def show_custom_dialog(content_control, title_text):
        card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(title_text, size=20, weight="bold", expand=True),
                    ft.IconButton(ft.Icons.CLOSE, on_click=close_dialog)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                content_control
            ], tight=True, spacing=10),
            padding=20,
            bgcolor="white",
            border_radius=10,
            width=350,
            shadow=ft.BoxShadow(blur_radius=15, color="#80000000"),
            on_click=lambda e: None # Evitar que el click cierre (propagación)
        )
        dialog_overlay.content = card
        dialog_overlay.visible = True
        dialog_overlay.update()

    # Redefinir las funciones de mostrar (usando el overlay)
    def show_appointment_details(cita):
        details_col = ft.Column([
            ft.Text(f"Nombre: {cita.get('nombre', 'N/A')}", weight="bold", size=18),
            ft.Text(f"Fecha: {cita.get('fecha', 'N/A')}"),
            ft.Text(f"Hora: {cita.get('hora', 'N/A')}"),
            ft.Text(f"Teléfono: {cita.get('telefono', 'N/A')}"),
            ft.Divider(),
            ft.Text(f"Servicio: {cita.get('servicio', 'No especificado')}"),
            ft.Text(f"Notas: {cita.get('notas', '')}"),
            ft.Container(height=10),
            ft.ElevatedButton("Cerrar", on_click=close_dialog, expand=True)
        ], tight=True)
        
        show_custom_dialog(details_col, "Detalles de la Cita")

    def show_day_appointments(date_str):
        print(f"DEBUG: Mostrando citas para {date_str}")
        citas_dia = appointments_by_date.get(date_str, [])
        
        content = None
        if not citas_dia:
            content = ft.Container(
                content=ft.Text("No hay citas para este día.", size=16, text_align="center"),
                padding=20, alignment=ft.alignment.center
            )
        else:
            lista = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, height=300)
            for cita in citas_dia:
                item = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PERSON, color="blue"),
                        ft.Column([
                            ft.Text(cita.get('nombre', 'Sin Nombre'), weight="bold"),
                            ft.Text(f"{cita.get('hora', '--:--')}", size=12, color="grey")
                        ])
                    ]),
                    padding=10,
                    bgcolor="grey50",
                    border_radius=8,
                    border=ft.border.all(1, "grey200"),
                    on_click=lambda e, c=cita: show_appointment_details(c),
                    ink=True
                )
                lista.controls.append(item)
            content = lista

        show_custom_dialog(content, f"Citas del {date_str}")
    
    # Area principal: Un Stack donde están los dos superpuestos + Overlay
    main_stack = ft.Stack(
        controls=[
            citas_view,
            calendar_container,
            dialog_overlay # SIEMPRE AL FINAL (ENCIMA)
        ],
        expand=True
    )

    # --- BOTONES DE NAVEGACIÓN ---
    btn_lista = ft.ElevatedButton("Lista", on_click=lambda _: cambiar_vista("lista"), bgcolor="blue", color="white")
    btn_calendario = ft.ElevatedButton("Calendario", on_click=lambda _: cambiar_vista("calendario"), bgcolor="white", color="blue")
    
    def manual_update(e):
        print("DEBUG: Refresco manual solicitado.")
        status_text.value = "Refrescando..."
        status_text.update()
        
        citas_list.update()
        page.update()
        
        status_text.value = "Pantalla actualizada"
        status_text.update()

    # Botón texto simple para evitar errores de iconos
    btn_refresh = ft.ElevatedButton("Refrescar", on_click=manual_update)

    def cambiar_vista(vista):
        if vista == "lista":
            citas_view.visible = True
            calendar_container.visible = False
            status_text.value = "Vista: Lista"
            
            btn_lista.bgcolor = "blue"
            btn_lista.color = "white"
            btn_calendario.bgcolor = "white"
            btn_calendario.color = "blue"
        else:
            citas_view.visible = False
            calendar_container.visible = True
            status_text.value = "Vista: Calendario"
            
            btn_lista.bgcolor = "white"
            btn_lista.color = "blue"
            btn_calendario.bgcolor = "blue"
            btn_calendario.color = "white"
        
        status_text.update()
        citas_view.update()
        calendar_container.update()
        btn_lista.update()
        btn_calendario.update()

    tabs = ft.Row(
        controls=[btn_lista, btn_calendario],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20
    )

    page.add(
        ft.Column(
            controls=[
                ft.Row([
                    ft.Text("Gestor de Citas", size=20, weight="bold"), 
                    btn_refresh,
                    status_text
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([total_citas_text], alignment=ft.MainAxisAlignment.END),
                tabs,
                ft.Divider(height=1),
                main_stack # Usamos el Stack
            ],
            expand=True
        )
    )
    
    page.update()

    # --- FIREBASE ---
    def iniciar_firebase():
        cred_path = resource_path(CREDENTIALS_FILE)
        status_text.value = "Conectando..."
        status_text.update()
        
        try:
            print(f"DEBUG: Buscando credenciales en: {cred_path}")
            service = firebase_service.FirebaseService(cred_path)
            service.connect()
            status_text.value = "Escuchando..."
            status_text.update()
            service.start_listening("citas", agregar_cita_ui)
        except Exception as e:
            status_text.value = f"Error: {str(e)[:20]}"
            status_text.update()

    threading.Thread(target=iniciar_firebase, daemon=True).start()

if __name__ == "__main__":
    ft.app(target=main)
