import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os

CREDENTIALS_FILE = "jonascuts-5aac9-firebase-adminsdk-fbsvc-2de12c37aa.json"

def list_collections():
    try:
        cred = credentials.Certificate(CREDENTIALS_FILE)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        collections = db.collections()
        
        print("\n--- COLECCIONES ENCONTRADAS ---")
        count = 0
        for col in collections:
            print(f"- {col.id}")
            count += 1
            
            # Imprimir primer documento para ver qué tiene
            docs = col.limit(1).stream()
            for doc in docs:
                print(f"  Ejemplo de datos en '{col.id}': {doc.to_dict()}")
        
        if count == 0:
            print("No se encontraron colecciones (la base de datos parece vacía).")
            
        print("-------------------------------\n")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_collections()
