import pandas as pd
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
cliente = Groq(api_key=os.getenv("GROQ_API_KEY"))

def cargar_datos():
    df_metrics = pd.read_excel("Sistema de Análisis Inteligente para Operaciones Rappi - Dummy Data (2).xlsx", sheet_name="RAW_INPUT_METRICS")
    df_orders = pd.read_excel("Sistema de Análisis Inteligente para Operaciones Rappi - Dummy Data (2).xlsx", sheet_name="RAW_ORDERS")
    return df_metrics, df_orders

def detectar_anomalias(df):
    df = df.copy()
    
    # Separar métricas que son ratios (0 a 1) de las que pueden ser negativas
    metricas_ratio = ['Perfect Orders', 'Lead Penetration', 'Pro Adoption', 
                      'Turbo Adoption', 'Restaurants SST > SS CVR', 
                      'Retail SST > SS CVR', 'Non-Pro PTC > OP',
                      'MLTV Top Verticals Adoption', '% PRO Users Who Breakeven']
    
    df_ratio = df[df['METRIC'].isin(metricas_ratio)].copy()
    df_resto = df[~df['METRIC'].isin(metricas_ratio)].copy()
    
    # Para métricas ratio usar cambio porcentual normal
    df_ratio['cambio_pct'] = ((df_ratio['L0W_ROLL'] - df_ratio['L1W_ROLL']) / df_ratio['L1W_ROLL'].abs()) * 100
    df_ratio = df_ratio[df_ratio['L1W_ROLL'].abs() > 0.01]
    anomalias_ratio = df_ratio[df_ratio['cambio_pct'].abs() > 10]
    
    # Para métricas que pueden ser negativas usar diferencia absoluta
    df_resto['cambio_abs'] = df_resto['L0W_ROLL'] - df_resto['L1W_ROLL']
    df_resto['cambio_pct'] = df_resto['cambio_abs']
    anomalias_resto = df_resto[df_resto['cambio_abs'].abs() > 0.5]
    
    # Juntar ambos
    columnas = ['COUNTRY','CITY','ZONE','METRIC','L1W_ROLL','L0W_ROLL','cambio_pct']
    resultado = pd.concat([
        anomalias_ratio[columnas],
        anomalias_resto[columnas]
    ])
    
    resultado = resultado.rename(columns={
        'L1W_ROLL': 'Hace 1 semana',
        'L0W_ROLL': 'Semana actual',
        'cambio_pct': 'Cambio'
    })
    
    peores = resultado.sort_values('Cambio').head(10)
    mejores = resultado.sort_values('Cambio', ascending=False).head(10)
    return pd.concat([peores, mejores])

def detectar_tendencias(df):
    # Métricas con 3 semanas seguidas de deterioro
    df = df.copy()
    df['baja_3sem'] = (
        (df['L2W_ROLL'] > df['L1W_ROLL']) &
        (df['L1W_ROLL'] > df['L0W_ROLL']) &
        (df['L3W_ROLL'] > df['L2W_ROLL'])
    )
    tendencias = df[df['baja_3sem']][['COUNTRY','CITY','ZONE','METRIC','L3W_ROLL','L2W_ROLL','L1W_ROLL','L0W_ROLL']]
    tendencias = tendencias.rename(columns={
        'L3W_ROLL': 'Hace 3 semanas',
        'L2W_ROLL': 'Hace 2 semanas',
        'L1W_ROLL': 'Hace 1 semana',
        'L0W_ROLL': 'Semana actual'
    })
    return tendencias.head(20)

def detectar_benchmarking(df):
    # Zonas del mismo país y tipo con rendimiento muy diferente
    benchmark = df.groupby(['COUNTRY','ZONE_TYPE','METRIC'])['L0W_ROLL'].agg(['mean','std']).reset_index()
    benchmark.columns = ['COUNTRY','ZONE_TYPE','METRIC','Promedio','Desviacion']
    benchmark = benchmark[benchmark['Desviacion'] > 0].sort_values('Desviacion', ascending=False)
    return benchmark.head(20)

def detectar_correlaciones(df):
    # Zonas con bajo rendimiento en múltiples métricas simultáneamente
    pivot = df.pivot_table(index=['COUNTRY','CITY','ZONE'], columns='METRIC', values='L0W_ROLL')
    pivot = pivot.reset_index()
    return pivot.head(20)

def detectar_oportunidades(df_metrics, df_orders):
    # Zonas con órdenes creciendo pero métricas por debajo del promedio
    ordenes_recientes = df_orders[['COUNTRY','CITY','ZONE','L0W','L1W']].copy()
    ordenes_recientes['crecimiento_ordenes'] = ((ordenes_recientes['L0W'] - ordenes_recientes['L1W']) / ordenes_recientes['L1W'].abs()) * 100
    oportunidades = ordenes_recientes[ordenes_recientes['crecimiento_ordenes'] > 5]
    oportunidades = oportunidades.rename(columns={
        'L0W': 'Órdenes semana actual',
        'L1W': 'Órdenes hace 1 semana',
        'crecimiento_ordenes': 'Crecimiento %'
    })
    return oportunidades.sort_values('Crecimiento %', ascending=False).head(20)

def generar_reporte(df_metrics, df_orders):
    # Detectar todos los insights
    anomalias = detectar_anomalias(df_metrics)
    tendencias = detectar_tendencias(df_metrics)
    benchmark = detectar_benchmarking(df_metrics)
    correlaciones = detectar_correlaciones(df_metrics)
    oportunidades = detectar_oportunidades(df_metrics, df_orders)

    # Preparar resumen para el LLM
    resumen = f"""
    Analiza estos hallazgos de datos operacionales de Rappi y genera un reporte ejecutivo profesional en español.

    ANOMALÍAS DETECTADAS (cambios >10% semana a semana):
    {anomalias.to_string()}

    TENDENCIAS PREOCUPANTES (3+ semanas de deterioro):
    {tendencias.to_string()}

    BENCHMARKING (mayor dispersión entre zonas similares):
    {benchmark.to_string()}

    OPORTUNIDADES (zonas con órdenes creciendo):
    {oportunidades.to_string()}

    El reporte debe tener exactamente esta estructura en Markdown:
    # Reporte Ejecutivo Rappi - Insights Automáticos

    ## Resumen Ejecutivo
    (Top 3-5 hallazgos más críticos en bullets)

    ## Anomalías Detectadas
    (Explica los casos más graves con recomendación accionable)

    ## Tendencias Preocupantes
    (Explica patrones de deterioro con recomendación accionable)

    ## Benchmarking
    (Explica dispersión entre zonas similares con recomendación accionable)

    ## Oportunidades
    (Explica zonas con potencial con recomendación accionable)

    ## Próximos Pasos Recomendados
    (3 acciones concretas y priorizadas)

    Sé específico con nombres de zonas, países y números. Máximo 600 palabras.
    """

    respuesta = cliente.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": resumen}]
    )

    return respuesta.choices[0].message.content