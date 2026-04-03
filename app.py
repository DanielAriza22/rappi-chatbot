import streamlit as st
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
import os

# Cargar API key
load_dotenv()
cliente = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Cargar Excel y lo almacena en cache
@st.cache_data
def cargar_datos():
    df_metrics = pd.read_excel("Sistema de Análisis Inteligente para Operaciones Rappi - Dummy Data (2).xlsx", sheet_name="RAW_INPUT_METRICS")
    df_orders = pd.read_excel("Sistema de Análisis Inteligente para Operaciones Rappi - Dummy Data (2).xlsx", sheet_name="RAW_ORDERS")
    return df_metrics, df_orders

df_metrics, df_orders = cargar_datos()

# Contexto que le damos al LLM sobre los datos
contexto_datos = f"""
Tienes acceso a datos operacionales de Rappi con estas características:

DATASET MÉTRICAS (df_metrics) - {len(df_metrics)} filas:
Columnas: COUNTRY, CITY, ZONE, ZONE_TYPE (Wealthy/Non Wealthy), 
ZONE_PRIORITIZATION (High Priority/Prioritized/Not Prioritized),
METRIC, L8W_ROLL, L7W_ROLL, L6W_ROLL, L5W_ROLL, L4W_ROLL, L3W_ROLL, L2W_ROLL, L1W_ROLL, L0W_ROLL
(L0W = semana más reciente, L8W = hace 8 semanas)

Métricas disponibles: Gross Profit UE, Perfect Orders, Lead Penetration, 
Pro Adoption, Turbo Adoption, Restaurants SST > SS CVR, Retail SST > SS CVR,
Non-Pro PTC > OP, MLTV Top Verticals Adoption, % PRO Users Who Breakeven,
Restaurants Markdowns / GMV, % Restaurants Sessions With Optimal Assortment

DATASET ÓRDENES (df_orders) - {len(df_orders)} filas:
Columnas: COUNTRY, CITY, ZONE, METRIC (siempre "Orders"),
L8W_ROLL = hace 8 semanas, L7W_ROLL = hace 7 semanas, L6W_ROLL = hace 6 semanas,
L5W_ROLL = hace 5 semanas, L4W_ROLL = hace 4 semanas, L3W_ROLL = hace 3 semanas,
L2W_ROLL = hace 2 semanas, L1W_ROLL = hace 1 semana, L0W_ROLL = semana actual

IMPORTANTE: Siempre usa los nombres técnicos reales de las columnas (L0W_ROLL, L1W_ROLL, etc.) 
   para filtrar y calcular
   Solo al final, cuando ya tengas el resultado, renombra las columnas así:
   .rename(columns={{
       'L0W_ROLL': 'Semana actual',
       'L1W_ROLL': 'Hace 1 semana',
       'L2W_ROLL': 'Hace 2 semanas',
       'L3W_ROLL': 'Hace 3 semanas',
       'L4W_ROLL': 'Hace 4 semanas',
       'L5W_ROLL': 'Hace 5 semanas',
       'L6W_ROLL': 'Hace 6 semanas',
       'L7W_ROLL': 'Hace 7 semanas',
       'L8W_ROLL': 'Hace 8 semanas'
   }})

Países: AR, BR, CL, CO, CR, EC, MX, PE, UY

Cuando el usuario haga una pregunta, genera ÚNICAMENTE código Python usando pandas
para responder. El código debe:
1. Usar df_metrics o df_orders según corresponda
2. Guardar el resultado en una variable llamada 'resultado'
3. No usar print(), solo asignar a 'resultado'
4. Ser conciso y directo

Solo responde con el código Python, sin explicaciones, sin ```python, sin nada más.
"""


# Historial del chat
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# Interfaz
st.title("🛵 Rappi Analytics")
st.caption(f"Datos cargados: {len(df_metrics):,} filas métricas | {len(df_orders):,} filas órdenes")
tab1, tab2 = st.tabs(["💬 Chatbot", "📊 Insights Automáticos"]) # Crea pestañas

with tab1:
    st.header("Chatbot de Datos")  
# Mostrar historial
for msg in st.session_state.mensajes:
    with st.chat_message(msg["rol"]):
        st.write(msg["contenido"])

# Input del usuario
pregunta = st.chat_input("Haz una pregunta sobre los datos de Rappi...")

if pregunta:
    # Mostrar pregunta del usuario
    with st.chat_message("user"):
        st.write(pregunta)
    st.session_state.mensajes.append({"rol": "user", "contenido": pregunta})

    with st.chat_message("assistant"):
        with st.spinner("Analizando datos..."):
            try:
                # Pedir código al LLM
                prompt = f"{contexto_datos}\n\nPregunta del usuario: {pregunta}"
                respuesta_llm = cliente.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
)
                codigo = respuesta_llm.choices[0].message.content.strip() # Primera respuesta de IA

                # Ejecutar el código generado
                entorno = {"df_metrics": df_metrics, "df_orders": df_orders, "pd": pd}
                exec(codigo, entorno)
                resultado = entorno.get("resultado", "No se pudo calcular")

                # Pedir al LLM que redacte respuesta bonita
                prompt_final = f"""
                El usuario preguntó: {pregunta}
                El resultado del análisis es: {resultado}
                Redacta una respuesta clara y concisa en español para un manager de operaciones.
                Si hay números, formatéalos bien. Máximo 3 párrafos.
                """
                respuesta_final = cliente.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt_final}])
                respuesta_texto = respuesta_final.choices[0].message.content

                st.write(respuesta_texto)
                
                # Mostrar tabla si el resultado es un dataframe
                if hasattr(resultado, 'to_frame') or hasattr(resultado, 'columns'):
                    st.dataframe(resultado)

                st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta_texto})  # Guarda memoria del chat

            except Exception as e:
                error_msg = f"No pude procesar esa pregunta. Intenta reformularla. (Error: {str(e)})"
                st.write(error_msg)
                st.session_state.mensajes.append({"rol": "assistant", "contenido": error_msg})

with tab2:
    st.header("Reporte de Insights Automáticos")
    st.caption("Análisis automático de anomalías, tendencias y oportunidades")
    if st.button("Generar Reporte"):
            with st.spinner("Analizando datos y generando reporte..."):
                from insights import generar_reporte
                reporte = generar_reporte(df_metrics, df_orders)
                st.markdown(reporte)
