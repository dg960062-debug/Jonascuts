import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from plyer import notification
import threading
import smtplib
import ssl
from email.message import EmailMessage


class FirebaseService:
    def __init__(self, cred_path):
        self.cred_path = cred_path
        self.db = None
        self.callback = None
        self.is_connected = False

    def connect(self):
        try:
            cred = credentials.Certificate(self.cred_path)
            # Evitar inicializar si ya existe
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            self.is_connected = True
            print("Conectado a Firebase correctamente.")
        except Exception as e:
            print(f"Error al conectar con Firebase: {e}")
            self.is_connected = False

    def start_listening(self, collection_name, on_new_document_callback):
        if not self.is_connected:
            print("No estás conectado a Firebase.")
            return

        self.callback = on_new_document_callback
        
        # Referencia a la colección
        col_ref = self.db.collection(collection_name)
        
        # Escuchar cambios en tiempo real
        col_ref.on_snapshot(self._on_snapshot)

    def _on_snapshot(self, col_snapshot, changes, read_time):
        new_docs_batch = []
        for change in changes:
            if change.type.name == 'ADDED':
                doc_data = change.document.to_dict()
                doc_id = change.document.id
                print(f"Nueva cita detectada: {doc_id}")
                new_docs_batch.append(doc_data)

        if new_docs_batch:
            # Llamar al callback de la UI CON LA LISTA COMPLETA
            if self.callback:
                print(f"DEBUG: Enviando lote de {len(new_docs_batch)} citas a la UI")
                try:
                    self.callback(new_docs_batch)
                except Exception as e:
                    print(f"ERROR en callback UI: {e}")
            
            # Notificaciones: Si son muchas (carga inicial), solo notificar genérico
            if len(new_docs_batch) > 3:
                 self._show_notification("Citas Cargadas", f"Se han cargado {len(new_docs_batch)} citas existentes.")
            else:
                # Si son pocas, notificar una a una
                for doc in new_docs_batch:
                    nombre = doc.get("nombre", "Cliente")
                    hora = doc.get("hora", "?")
                    nombre = doc.get("nombre", "Cliente")
                    hora = doc.get("hora", "?")
                    self._show_notification("Nueva Cita", f"{nombre} ha reservado a las {hora}")
                    
                    # Enviar Email
                    threading.Thread(target=self.send_email_notification, args=(doc,)).start()

    def send_email_notification(self, doc_data):
        # --- CONFIGURACIÓN ---
        GMAIL_USER = "dg960062@gmail.com"      # <--- PON TU CORREO AQUÍ
        GMAIL_PASS = "cpwjnuzajwesmgwm"        # <--- PON TU CONTRASEÑA DE APLICACIÓN AQUÍ (No la normal)
        DEST_EMAIL = "dare234234@gmail.com" # <--- A QUIEN SE LE ENVIA
        # ---------------------

        if "TU_CORREO" in GMAIL_USER:
            print("SISTEMA DE CORREO: Credenciales no configuradas. Omite el envío.")
            return

        nombre = doc_data.get("nombre", "Sin nombre")
        fecha = doc_data.get("fecha", "Sin fecha")
        hora = doc_data.get("hora", "Sin hora")
        telefono = doc_data.get("telefono", "Sin teléfono")
        servicio = doc_data.get("servicio", "Estándar")

        subject = f"Nueva Cita: {nombre} - {fecha} {hora}"
        body = f"""
        ¡Nueva Reserva Recibida!
        
        Cliente: {nombre}
        Fecha: {fecha}
        Hora: {hora}
        Teléfono: {telefono}
        Servicio: {servicio}
        
        Revisa la aplicación para más detalles.
        """

        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = GMAIL_USER
        msg['To'] = DEST_EMAIL

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(GMAIL_USER, GMAIL_PASS)
                server.send_message(msg)
                print(f"CORREO ADMIN ENVIADO a {DEST_EMAIL}")

                # --- CORREO AL CLIENTE (Si existe) ---
                client_email = doc_data.get("email") # O "correo"
                if client_email and "@" in client_email:
                    subject_client = "Confirmación de Cita - JonasCuts"
                    body_client = f"""
                    Hola {nombre},
                    
                    Tu cita ha sido confirmada con éxito.
                    
                    Fecha: {fecha}
                    Hora: {hora}
                    Servicio: {servicio}
                    
                    ¡Gracias por elegirnos!
                    """
                    msg_client = EmailMessage()
                    msg_client.set_content(body_client)
                    msg_client['Subject'] = subject_client
                    msg_client['From'] = GMAIL_USER
                    msg_client['To'] = client_email
                    
                    server.send_message(msg_client)
                    print(f"CORREO CLIENTE ENVIADO a {client_email}")
        except Exception as e:
            print(f"ERROR AL ENVIAR CORREO: {e}")


    def _show_notification(self, title, message):
        try:
            notification.notify(
                title=title,
                message=message,
                app_name='Gestor de Citas',
                timeout=10
            )
        except Exception as e:
            print(f"Error al mostrar notificación: {e}")

