import streamlit as st
import pandas as pd

st.set_page_config(page_title="Club de Licores", page_icon="🍸")

# Mostrar encabezado 
st.markdown("""
    <div style='text-align: left; display: flex; align-items: center; gap: 20px;'>
        <span style='font-size: 32px; font-weight: bold; color: black;'>Club de Licores</span>
        <span style='font-size: 32px; color: gray;'>Tu guía de coctelería</span>
    </div>
    <hr style='margin-top: 10px; margin-bottom: 20px;'>
""", unsafe_allow_html=True)

# === Cargar datos ===
recetas = pd.read_excel("data/recetas.xlsx", sheet_name="receta")
complementos = pd.read_excel("data/recetas.xlsx", sheet_name="complementos")
tecnicas = pd.read_excel("data/recetas.xlsx", sheet_name="tecnicas")
jarabes = pd.read_excel("data/recetas.xlsx", sheet_name="jarabe")
recursos = pd.read_excel("data/recetas.xlsx", sheet_name="recurso")

# === Sidebar ===

st.sidebar.title("Opciones")

# === Identificar columnas de licor base ===
columnas_licor = recetas.columns[8:39] 

# Verificar que haya columnas de licor disponibles
licores_disponibles = sorted(columnas_licor.tolist()) if not columnas_licor.empty else []

# Crear selector de licor base
licor_sel = st.sidebar.selectbox("Filtrar por licor base", ["Todos"] + licores_disponibles + ["Sin Alcohol"])

# Aplicar filtro según selección
if licor_sel == "Todos":
    recetas_filtradas = recetas
elif licor_sel == "Sin Alcohol":
    # Filtro: todas las columnas de licor tienen 0 o NaN
    recetas_filtradas = recetas[recetas[columnas_licor].fillna(0).sum(axis=1) == 0]
elif licor_sel in recetas.columns:
    # Filtro: valor positivo en la columna seleccionada
    recetas_filtradas = recetas[recetas[licor_sel].fillna(0) > 0]
else:
    # Filtro inválido (no debería pasar, pero cubre errores)
    recetas_filtradas = recetas.iloc[0:0]

# Obtener cócteles únicos y ordenarlos
cocteles = sorted(recetas_filtradas["coctel"].dropna().unique())

# Mantener selección previa si es válida, sino usar primero disponible
if "coctel_sel" not in st.session_state or st.session_state.coctel_sel not in cocteles:
    st.session_state.coctel_sel = cocteles[0] if cocteles else None

# Mostrar selector de cóctel o advertencia si no hay opciones
if cocteles:
    coctel_sel = st.sidebar.selectbox(
        "Selecciona un cóctel",
        cocteles,
        index=cocteles.index(st.session_state.coctel_sel),
        key="coctel_sel"
    )
else:
    coctel_sel = None
    st.sidebar.warning("No hay cócteles para ese licor base.")

# Escoger tipo de cálculo 
modo = st.sidebar.radio("Tipo de cantidad", ["Cantidad de cócteles", "Volumen total (litros)"])

# Escoger unidad de medida según modo
unidad_opciones = {
    "Mililitros (ml)": "ml",
    "Onzas (oz)": "oz"
}

if modo == "Cantidad de cócteles":
    unidad_label = st.sidebar.radio("Unidad de medida", list(unidad_opciones.keys()))
    unidad = unidad_opciones[unidad_label]
else:
    # Simular un radio con una sola opción seleccionada (Mililitros)
    unidad_label = st.sidebar.radio("Unidad de medida", ["Mililitros (ml)"], index=0)
    unidad = "ml"

factor_conversion = 1 if unidad == "ml" else 1 / 30

if modo == "Cantidad de cócteles":
    cantidad = st.sidebar.number_input("Número de cócteles", min_value=1, value=1)
    volumen_deseado = None
    litros = None
else:
    opciones_litros = [i * 0.5 for i in range(1, 21)]  # De 0.5 a 10 litros
    litros = st.sidebar.selectbox(
        "Litros totales",
        opciones_litros,
        index=1,
        format_func=lambda x: str(int(x)) if x == int(x) else str(x).replace(".", ",")
    )
    cantidad = None
    volumen_deseado = litros * 1000

# === Verificar selección válida de cóctel antes de continuar ===
if coctel_sel:
    receta_seleccionada = recetas[recetas["coctel"] == coctel_sel]
    
    if not receta_seleccionada.empty:
        fila_receta = receta_seleccionada.iloc[0]
    else:
        st.warning("No se encontró información para el cóctel seleccionado.")
        st.stop()
else:
    st.info("Selecciona un cóctel para ver los detalles.")
    st.stop()

# === Filtro receta ===
fila_receta = recetas[recetas["coctel"] == coctel_sel].iloc[0]
ingredientes = fila_receta.drop([
    "coctel", "vaso", "tecnica", "capacidad_vaso_sin_hielo",
    "cantidad_hielo", "hielo", "capacidad_vaso_con_hielo", "volumen"])
ingredientes = ingredientes[ingredientes.notna() & (ingredientes != 0)]

# Cálculo de volumen y factor
# 1. Obtener volumen base y volumen deseado
volumen_base = fila_receta["volumen"]
if modo == "Cantidad de cócteles":
    volumen_deseado = cantidad * volumen_base
else:
    volumen_deseado = litros * 1000

# 2. Calcular factor de escalado
factor = volumen_deseado / volumen_base

# 3. Calcular ingredientes escalados en ml
ingredientes_escalados_ml = ingredientes * factor

# 4. Convertir a la unidad final (ml u oz)
ingredientes_ajustados = ingredientes_escalados_ml * factor_conversion

# === Datos de técnica ===
tecnica_info = tecnicas[tecnicas["tecnica"] == fila_receta["tecnica"]].iloc[0]

# === Cantidad de recetas de cócteles ===
st.sidebar.markdown("---")  # línea separadora opcional
total_cocteles = recetas["coctel"].nunique()
st.sidebar.markdown(f"""
<div style='text-align: justify; font-style: italic; font-size: 13px;'>
    <p><b>Club de Licores</b> es una aplicación interactiva que permite explorar una amplia variedad de recetas de cócteles, conocer sus ingredientes, ajustar las cantidades según el número de personas o el volumen deseado, y descubrir datos curiosos, poemas, imágenes e incluso canciones asociadas a cada trago.</p>
    <p>Con una interfaz simple y amigable, esta app intenta contribuir al mundo de la coctelería entregando información práctica y didáctica, pero a la vez creativa y culturalmente enriquecida.</p>
    <p>Actualmente incluye <b>{total_cocteles}</b> recetas de cócteles.</p>
    <p>Desarrollada por Carlos Andrés González Miranda (Santiago de Chile, 2025).</p>
</div>
""", unsafe_allow_html=True)

# === Visualización central ===
st.markdown(f"<h3 style='font-size: 48px; color: #d23f29;'>{coctel_sel}</h3>", unsafe_allow_html=True)

# Mostrar imagen si existe (nombre del archivo debe coincidir con el cóctel)
from PIL import Image
import os
image_path = f"imagenes/{coctel_sel}.jpg"
if os.path.exists(image_path):
    st.image(image_path, width=400)
else:
    st.info("Imagen no disponible para este cóctel.") # Opcional: st.image("images/default.jpg", width=400)

# === Sección de ingredientes ===

st.markdown("### Ingredientes")

ingredientes_a_gusto = {
    "Sal": "sal",
    "Sal de Apio": "sal de apio",
    "Pimienta": "pimienta",
    "Canela": "canela",
    "Nuez Moscada": "nuez moscada",
    "Azúcar Flor": "azúcar flor"
}

ingredientes_gotas = {
    "Amargo de Angostura": "Amargo de Angostura",
    "Salsa Inglesa": "Salsa Inglesa",
    "Salsa Tabasco": "Salsa Tabasco"
}

for ing in ingredientes_ajustados.index:
    val_ajustado = ingredientes_ajustados[ing]
    val_base_ml = ingredientes_escalados_ml[ing]

    # Ingredientes que se agregan a gusto
    if ing in ingredientes_a_gusto:
        st.write(f"- Agregar {ingredientes_a_gusto[ing]} a gusto")

    # Ingredientes que se agregan en gotas
    elif ing in ingredientes_gotas:
        st.write(f"- Agregar algunas gotas de {ingredientes_gotas[ing]}")

    # Ingredientes con cantidad específica
    else:
        if unidad == "ml":
            cantidad = int(round(val_ajustado))  # Redondea a entero para evitar decimales innecesarios
        else:  # onzas
            cantidad = round(val_ajustado, 2)
            if cantidad.is_integer():
                cantidad = int(cantidad)  # Muestra como 1 en lugar de 1.0 si es entero

        st.write(f"- {ing}: {cantidad} {unidad}")

# === Sección de jarabes utilizados (si hay) ===

jarabes_columnas = [
    "Jarabe Simple", "Jarabe de Canela", "Jarabe de Jengibre",
    "Jarabe de Menta", "Jarabe de Cedrón", "Jarabe de Romero"
]

# Revisa si alguno de los jarabes tiene un valor mayor a 0
jarabes_presentes = [j for j in jarabes_columnas if j in ingredientes.index and ingredientes[j] > 0]

if jarabes_presentes:
    #st.subheader("Jarabe")
    for j in jarabes_presentes:
        fila_jarabe = jarabes[jarabes["jarabe"] == j]
        if not fila_jarabe.empty:
            st.markdown(f"**{j}**")
            st.write(fila_jarabe["preparación"].values[0])

# === Información sobre el hielo ===
hielo = fila_receta["hielo"]
if pd.notna(hielo) and str(hielo).strip().lower() in ["Sí", "Si", "sí", "si"]:
    st.markdown("### Hielo")
    st.write("❄️ Servir en un vaso o copa con hielo. Preferir hielos de mayor tamaño para retardar la dilución.")
else:
    st.markdown("### Hielo")
    st.write("🚫 Servir sin hielo.")

# === Técnica de preparación ===
st.markdown("### Técnica de preparación")
st.write(f"**{fila_receta['tecnica']} ({tecnica_info['nombre_español']})** – {tecnica_info['descripción']}")

# === Cristalería sugerida ===
st.markdown("### Cristalería sugerida")
st.write(f"{fila_receta['vaso']} – {int(fila_receta['capacidad_vaso_sin_hielo'])} ml")

# === Decoración sugerida (complementos con valor 1) ===
fila_complementos = complementos[complementos["coctel"] == coctel_sel]
if not fila_complementos.empty:
    decoraciones = fila_complementos.iloc[0].drop("coctel")
    decoraciones = decoraciones[decoraciones == 1].index.tolist()
    
    if decoraciones:
        st.markdown("### Garnitura (garnish)")
        st.write("Se sugiere acompañar con: " + ", ".join(decoraciones))

# === Sección recurso asociado (si existe) ===
recurso_fila = recursos[recursos["coctel"] == coctel_sel]

if not recurso_fila.empty:
    texto = recurso_fila.iloc[0].get("texto_enlace")
    url = recurso_fila.iloc[0].get("url")
    recurso = recurso_fila.iloc[0].get("recurso")

    # Mostrar texto largo si existe (como poema o relato)
    if pd.notna(recurso):
        lineas = recurso.strip().split("\n")
        titulo = lineas[0] if lineas else "Recurso"
        contenido = "\n".join(lineas[1:]).strip()
        st.markdown(f"### {titulo}")
        st.text(contenido)

    # Mostrar link si hay texto_enlace + url
    if pd.notna(texto) and pd.notna(url):
        st.markdown("### Vamos a ponerte un tema")
        st.markdown(f'<a href="{url}" target="_blank">🎵 {texto}</a>', unsafe_allow_html=True)