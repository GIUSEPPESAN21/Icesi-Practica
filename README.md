Dashboard de Análisis de EVs y Chatbot con Gemini
Este repositorio contiene dos aplicaciones web construidas con Streamlit:

Analizador de Datos de Vehículos Eléctricos (app.py): Una herramienta interactiva para visualizar y analizar datos del mercado de vehículos eléctricos por segmento.

Chatbot con Gemini (chatbot_app.py): Un chatbot conversacional que utiliza la potente IA de Gemini de Google.

🚀 Cómo Empezar
1. Prerrequisitos
Python 3.8 o superior

Una clave de API de Google AI Studio para el chatbot.

2. Instalación
Clona este repositorio y navega a la carpeta del proyecto. Luego, instala las dependencias:

git clone [https://github.com/tu-usuario/tu-repositorio.git](https://github.com/tu-usuario/tu-repositorio.git)
cd tu-repositorio
pip install -r requirements.txt

3. Configuración del Chatbot (Local)
Para usar el chatbot, necesitas configurar tu clave de API de forma segura:

Crea una carpeta llamada .streamlit en la raíz de tu proyecto.

Dentro de .streamlit, crea un archivo llamado secrets.toml.

Añade tu clave de API al archivo de la siguiente manera:

# .streamlit/secrets.toml
GEMINI_API_KEY = "PEGA_AQUÍ_TU_NUEVA_CLAVE_DE_GEMINI"

IMPORTANTE: No subas este archivo a GitHub.

🏃 Cómo Ejecutar las Aplicaciones
Puedes ejecutar cualquiera de las dos aplicaciones desde tu terminal.

Para lanzar el Analizador de Datos:
Asegúrate de tener un archivo de datos (como Practica ICESI.csv) y ejecútalo. La aplicación te pedirá que lo subas.

streamlit run app.py

Para lanzar el Chatbot con Gemini:
Asegúrate de haber configurado tu archivo secrets.toml.

streamlit run chatbot_app.py
