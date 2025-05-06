import streamlit as st
import pandas as pd

st.set_page_config(page_title="Club de Licores", page_icon="🍸")

# Mostrar encabezado 
st.markdown("""
    <div style='text-align: left; display: flex; align-items: center; gap: 20px;'>
        <span style='font-size: 24px; font-weight: bold;'>Club de Licores</span>
        <span style='font-size: 24px; color: gray;'>Tu guía de coctelería</span>
    </div>
    <hr style='margin-top: 10px; margin-bottom: 20px;'>
""", unsafe_allow_html=True)

# === Cargar datos ===
recetas = pd.read_excel("coctel_app/data/recetas.xlsx", sheet_name="receta")
complementos = pd.read_excel("coctel_app/data/recetas.xlsx", sheet_name="complementos")
tecnicas = pd.read_excel("coctel_app/data/recetas.xlsx", sheet_name="tecnicas")
jarabes = pd.read_excel("coctel_app/data/recetas.xlsx", sheet_name="jarabe")
recursos = pd.read_excel("coctel_app/data/recetas.xlsx", sheet_name="recurso")

# === Sidebar ===

st.sidebar.title("Opciones")

# Obtener cócteles únicos y ordenarlos
cocteles = sorted(recetas["coctel"].dropna().unique())

# Usar session_state para mantener la selección
if "coctel_sel" not in st.session_state:
    st.session_state.coctel_sel = cocteles[0]  # Valor por defecto

# Mostrar selector con valor recordado
coctel_sel = st.sidebar.selectbox(
    "Selecciona un cóctel",
    cocteles,
    index=cocteles.index(st.session_state.coctel_sel),
    key="coctel_sel"
)

# Escoger unidad de medida
unidad = st.sidebar.radio("Unidad de medida", ["ml", "oz"])
factor_conversion = 1 if unidad == "ml" else 1/30

# Escoger tipo de cálculo 
modo = st.sidebar.radio("Tipo de cantidad", ["Cantidad de cócteles", "Volumen total (litros)"])

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

    # Formato para visualización
    litros_mostrados = str(int(litros)) if litros == int(litros) else str(litros).replace(".", ",")
    st.write(f"Volumen total: {litros_mostrados} litros ({int(volumen_deseado)} ml)")

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

# === Visualización central ===
st.title(f" {coctel_sel}")

# Mostrar imagen si existe (nombre del archivo debe coincidir con el cóctel)
from PIL import Image
import os
image_path = f"coctel_app/imagenes/{coctel_sel}.jpg"
if os.path.exists(image_path):
    st.image(image_path, width=400)
else:
    st.info("Imagen no disponible para este cóctel.") # Opcional: st.image("images/default.jpg", width=400)

# === Sección de ingredientes ===

st.markdown("### Ingredientes")

ingredientes_a_gusto = {
    "Sal": "sal",
    "Sal de Apio": "sal de apio",
    "Pimienta": "pimienta"
}

ingredientes_gotas = {
    "Amargo de Angostura": "Amargo de Angostura",
    "Salsa Inglesa": "Salsa Inglesa",
    "Salsa Tabasco": "Salsa Tabasco"
}

for ing in ingredientes_ajustados.index:
    val_ajustado = ingredientes_ajustados[ing]
    val_base_ml = ingredientes_escalados_ml[ing]

    if ing in ingredientes_a_gusto and round(val_base_ml) == 1:
        st.write(f"- Agregar {ingredientes_a_gusto[ing]} a gusto")
    elif ing in ingredientes_gotas and round(val_base_ml) == 1:
        st.write(f"- Agregar algunas gotas de {ingredientes_gotas[ing]}")
    else:
        if unidad == "ml":
            cantidad = int(round(val_ajustado))
        else:  # oz
            cantidad = round(val_ajustado, 2)
            cantidad = int(cantidad) if cantidad == int(cantidad) else cantidad
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
if pd.notna(hielo) and str(hielo).strip().lower() in ["sí", "si", "true", "1"]:
    st.markdown("### Hielo")
    st.write("❄️ Servir en un vaso o copa con hielo. Preferir hielos de mayor tamaño para retardar la dilución")
else:
    st.markdown("### Hielo")
    st.write("🚫 Servir en una copa sin hielo, debido a que la temperatura se bajó durante la preparación.")

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

    # Si hay texto y URL, se muestra el enlace clicable
    if pd.notna(texto) and pd.notna(url):
        st.markdown("### Vamos a ponerte un tema")
        st.markdown(f'<a href="{url}" target="_blank">🎵 {texto}</a>', unsafe_allow_html=True)

    # Si hay un texto largo pero sin URL, usar primera línea como título
    elif pd.notna(recurso):
        lineas = recurso.strip().split("\n")
        titulo = lineas[0] if lineas else "Recurso"
        contenido = "\n".join(lineas[1:]).strip()
        st.markdown(f"### {titulo}")
        st.text(contenido)