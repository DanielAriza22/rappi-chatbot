# Rappi Analytics Chatbot

Sistema de análisis inteligente para operaciones Rappi con chatbot 
conversacional e insights automáticos.

## Demo en nube
- Prueba de Chatbot - (https://rappi-chatbot-gends6duygoagvy7vwuieb.streamlit.app/)

## Descripción
Este sistema permite a usuarios no técnicos hacer preguntas en lenguaje 
natural sobre métricas operacionales de Rappi y recibir respuestas precisas 
sin necesidad de conocer SQL o Python.

## Arquitectura
- **Streamlit**: Interfaz visual del chatbot
- **Pandas**: Análisis de datos local (nunca se manda el Excel completo al LLM)
- **Groq (Llama 3)**: Generación de código pandas y redacción de respuestas
- **El flujo**: Usuario pregunta → LLM genera código → Pandas ejecuta contra datos reales → LLM redacta respuesta

## Funcionalidades
### Pestaña 1: Chatbot
- Preguntas de filtrado, comparación, tendencias y agregaciones
- Memoria conversacional
- Respuestas en lenguaje natural con tablas

### Pestaña 2: Insights Automáticos
- Anomalías: zonas con cambios drásticos semana a semana
- Tendencias preocupantes: métricas en deterioro 3+ semanas
- Benchmarking: dispersión entre zonas similares
- Correlaciones entre métricas
- Oportunidades: zonas con órdenes creciendo

## Instalación local
1. Clona el repositorio
2. Crea un archivo `.env` con tu API key:
```
GROQ_API_KEY=ClaveAqui
```
3. Instala las dependencias:
```
pip install -r requirements.txt
```
4. Corre la aplicación:
```
streamlit run app.py
```

## Costo estimado
- Groq API: **gratuito** con límites del free tier:
  - 500 preguntas por día (cada pregunta hace 2 llamadas al LLM)
  - Si se agota el límite diario, se resetea automáticamente al día siguiente
  - Sin tarjeta de crédito requerida
- Streamlit Cloud: **gratuito**
- Costo: **$0**
- - La arquitectura permite migrar a otro LLM fácilmente si los precios cambian

## 🔧 Stack tecnológico
- Python 3.12
- Streamlit
- Pandas
- Groq (Llama 3.3 70b)
```
