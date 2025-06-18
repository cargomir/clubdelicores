import streamlit as st
import pandas as pd
from PIL import Image
import base64
from io import BytesIO

# === Configuración de la página ===

st.set_page_config(page_title="Club de Licores", page_icon="imagenes/favicon.ico")

#  === Inyección de estilos adaptativos  === 
st.markdown("""
    <style>
    @media (prefers-color-scheme: dark) {
        body, .stApp {
            background-color: #1e1e1e !important;
            color: #f0f0f0 !important;
        }

        .stSidebar {
            background-color: #2a2a2a !important;
            color: #f0f0f0 !important;
        }

        .stSidebar .css-1cypcdb, .stSidebar .css-1v3fvcr, .stSidebar .css-qbe2hs {
            color: #f0f0f0 !important;
        }
                         
        .stRadio > label, .stSelectbox label, .stTextInput label {
            color: #f0f0f0 !important;
        }

        .css-1offfwp {
            color: #f0f0f0 !important;
        }

        .css-1cpxqw2, .css-1d391kg {
            background-color: #383838 !important;
            color: #ffffff !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# === Color personalizado para la barra lateral ===
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        background-color: #f0f2f6;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# === Encabezado ===

# Convertir imagen a base64
def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Cargar y convertir imagen
logo = Image.open("imagenes/icon.png").convert("RGBA")
logo_base64 = image_to_base64(logo)

# Encabezado
col1, col2 = st.columns([1, 5])  # mantener buen ancho para el logo

with col1:
    st.markdown(
        f"""
        <div style='display: flex; align-items: center; justify-content: flex-start; margin-top: 30px;'>
            <img src='data:image/png;base64,{logo_base64}' width='90'>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(f"""
        <div id='encabezado-app' style='padding-top: 10px; line-height: 1.2; margin-top: 20px;'>
            <div class='titulo-principal'>Club de Licores</div>
            <div class='subtitulo-principal'>Tu guía de coctelería</div>
        </div>

        <style>
        @media (prefers-color-scheme: dark) {{
            .titulo-principal {{
                font-size: 42px;
                font-weight: bold;
                color: white !important;
            }}
            .subtitulo-principal {{
                font-size: 28px;
                color: #cccccc !important;
            }}
        }}
        @media (prefers-color-scheme: light) {{
            .titulo-principal {{
                font-size: 42px;
                font-weight: bold;
                color: black !important;
            }}
            .subtitulo-principal {{
                font-size: 28px;
                color: gray !important;
            }}
        }}
        </style>
    """, unsafe_allow_html=True)

# Línea separadora
st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

# === Cargar datos ===
recetas = pd.read_excel("data/recetas.xlsx", sheet_name="receta")
complementos = pd.read_excel("data/recetas.xlsx", sheet_name="complementos")
tecnicas = pd.read_excel("data/recetas.xlsx", sheet_name="tecnicas")
jarabes = pd.read_excel("data/recetas.xlsx", sheet_name="jarabe")
recursos = pd.read_excel("data/recetas.xlsx", sheet_name="recurso")

# === Sidebar ===

st.sidebar.title("Opciones")

# === Identificar columnas de licor base ===
columnas_licor = recetas.columns[8:46]
columnas_ingredientes = recetas.columns[48:80]

# === Paso 1: Obtener selección actual o default
licor_actual = st.session_state.get("licor_sel", "Todos")
ingrediente_actual = st.session_state.get("ingrediente_sel", "Todos")

# === Paso 2: Filtrar recetas según selección actual
recetas_filtradas = recetas.copy()

# Aplicar filtro por licor si corresponde
if licor_actual == "Sin Alcohol":
    recetas_filtradas = recetas_filtradas[recetas_filtradas[columnas_licor].fillna(0).sum(axis=1) == 0]
elif licor_actual != "Todos":
    recetas_filtradas = recetas_filtradas[recetas_filtradas[licor_actual].fillna(0) > 0]

# Aplicar filtro por ingrediente si corresponde
if ingrediente_actual != "Todos":
    recetas_filtradas = recetas_filtradas[recetas_filtradas[ingrediente_actual].fillna(0) > 0]

# === Paso 3: Obtener opciones disponibles actualizadas
licores_disponibles = [
    col for col in columnas_licor
    if recetas_filtradas[col].fillna(0).sum() > 0
]
ingredientes_disponibles = [
    col for col in columnas_ingredientes
    if recetas_filtradas[col].fillna(0).sum() > 0
]

# === Paso 4: Selectores interdependientes (actualización en orden visual)
licor_sel = st.sidebar.selectbox(
    "Filtra por licor base",
    ["Todos"] + sorted(licores_disponibles) + ["Sin Alcohol"],
    index=(["Todos"] + sorted(licores_disponibles) + ["Sin Alcohol"]).index(licor_actual)
    if licor_actual in (["Todos"] + licores_disponibles + ["Sin Alcohol"]) else 0,
    key="licor_sel"
)

ingrediente_sel = st.sidebar.selectbox(
    "Filtra por otro tipo de ingrediente",
    ["Todos"] + sorted(ingredientes_disponibles),
    index=(["Todos"] + sorted(ingredientes_disponibles)).index(ingrediente_actual)
    if ingrediente_actual in (["Todos"] + ingredientes_disponibles) else 0,
    key="ingrediente_sel"
)

# === Paso 5: Volver a filtrar con selecciones finales
recetas_final = recetas.copy()

if st.session_state.licor_sel == "Sin Alcohol":
    recetas_final = recetas_final[recetas_final[columnas_licor].fillna(0).sum(axis=1) == 0]
elif st.session_state.licor_sel != "Todos":
    recetas_final = recetas_final[recetas_final[st.session_state.licor_sel].fillna(0) > 0]

if st.session_state.ingrediente_sel != "Todos":
    recetas_final = recetas_final[recetas_final[st.session_state.ingrediente_sel].fillna(0) > 0]

# === Paso 6: Selector de cóctel dependiente de ambos
cocteles = sorted(recetas_final["coctel"].dropna().unique())
if "coctel_sel" not in st.session_state or st.session_state.coctel_sel not in cocteles:
    st.session_state.coctel_sel = cocteles[0] if cocteles else None

if cocteles:
    coctel_sel = st.sidebar.selectbox(
        "Selecciona un cóctel",
        cocteles,
        index=cocteles.index(st.session_state.coctel_sel),
        key="coctel_sel"
    )
else:
    st.sidebar.warning("No hay cócteles para esa combinación.")
    coctel_sel = None

# === Selector tipo de cálculo  ===

# Definir el valor predeterminado si se limpió
modo_por_defecto = "Cantidad de cócteles"

# Recuperar desde session_state si está seteado por el botón
modo = st.session_state.get("modo_forzado", modo_por_defecto)

# Mostrar el radio sin `key`, pero con valor controlado
modo = st.sidebar.radio(
    "Tipo de cantidad",
    ["Cantidad de cócteles", "Volumen total (litros)"],
    index=0 if modo == "Cantidad de cócteles" else 1
)

# Guardar el valor actual del radio si no fue forzado (flujo normal)
st.session_state["modo_forzado"] = modo

# Escoger unidad de medida según modo
unidad_opciones = {
    "Mililitros (ml)": "ml",
    "Onzas (oz)": "oz"
}

if modo == "Cantidad de cócteles":
    unidad_label = st.sidebar.radio("Unidad de medida", list(unidad_opciones.keys()),
        key="unidad_label")
    unidad = unidad_opciones[unidad_label]
else:
    # Simular un radio con una sola opción seleccionada (Mililitros)
    unidad_label = st.sidebar.radio("Unidad de medida", ["Mililitros (ml)"], index=0,
    key="unidad_label")
    unidad = "ml"

factor_conversion = 1 if unidad == "ml" else 1 / 30

if modo == "Cantidad de cócteles":
    cantidad = st.sidebar.number_input("Número de cócteles", min_value=1, value=1, 
    key="cantidad")
    volumen_deseado = None
    litros = None
else:
    opciones_litros = [i * 0.5 for i in range(1, 21)]  # De 0.5 a 10 litros
    litros = st.sidebar.selectbox(
        "Litros totales",
        opciones_litros,
        index=1,
        format_func=lambda x: str(int(x)) if x == int(x) else str(x).replace(".", ","),
    key="litros"
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

# === Botón de limpiar filtros ===
if st.sidebar.button("Limpiar selección"):
    # Borrar campos específicos
    for clave in ["licor_sel", "ingrediente_sel", "coctel_sel", "unidad_label", "cantidad", "litros"]:
        st.session_state.pop(clave, None)

    # Forzar que vuelva a modo por defecto
    st.session_state["modo_forzado"] = "Cantidad de cócteles"
    st.rerun()

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
st.sidebar.markdown("---")  # línea separadora

total_cocteles = recetas["coctel"].nunique()

st.sidebar.markdown(f"""
<div style='text-align: justify; font-style: italic; font-size: 13px;'>
    <p><b>Club de Licores</b> es una aplicación interactiva que permite explorar una amplia variedad de recetas de cócteles, conocer sus ingredientes, ajustar las cantidades según el número de personas o el volumen deseado, y descubrir datos curiosos, poemas, imágenes e incluso canciones asociadas a cada trago.</p>
    <p>Con una interfaz simple y amigable, esta app intenta contribuir al mundo de la coctelería entregando información práctica y didáctica, pero a la vez creativa y culturalmente enriquecida.</p>
    <p>Actualmente incluye <b>{total_cocteles}</b> recetas de cócteles.</p>
    <p>Desarrollada por Carlos Andrés González Miranda (Santiago de Chile, 2025).</p>
    <p style="margin-top:10px;">
        <a href="mailto:clubdelicores@gmail.com" target="_blank" style="text-decoration: none;">
            <img src="https://img.icons8.com/color/24/000000/gmail-new.png" style="vertical-align: middle;"/> clubdelicores@gmail.com
        </a><br>
        <a href="https://instagram.com/clubdelicores" target="_blank" style="text-decoration: none;">
            <img src="https://img.icons8.com/fluency/24/000000/instagram-new.png" style="vertical-align: middle;"/> @clubdelicores
        </a>
    </p>
</div>
""", unsafe_allow_html=True)

# === Visualización central ===

st.markdown(f"<h3 style='font-size: 48px; color: #e63118; font-weight: bold;'>{coctel_sel}</h3>", unsafe_allow_html=True)

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
    "Azúcar Flor": "azúcar flor",
    "Harina Tostada": "harina tostada"
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

# === Sección recursos asociados (si existen) ===

recurso_fila = recursos[recursos["coctel"] == coctel_sel]

if not recurso_fila.empty:
    fila = recurso_fila.iloc[0]

     # Mostrar observaciones (si existen)
    if pd.notna(fila.get("observaciones")):
        st.markdown("### Observaciones")
        st.markdown(fila["observaciones"])

    # Verificar si hay al menos un recurso adicional
    hay_recursos = any([
        pd.notna(fila.get("recurso")),
        pd.notna(fila.get("texto_enlace_musica")) and pd.notna(fila.get("url_musica")),
        pd.notna(fila.get("texto_enlace_otro")) and pd.notna(fila.get("url_otro")),
    ])

    if hay_recursos:
        st.markdown("---")
        st.markdown(
            "<h2 style='color: #e63118; font-size: 36px; font-weight: bold;'>Recursos adicionales</h2>",
            unsafe_allow_html=True
        )

       # Mostrar recurso largo (como poema o relato)
        if pd.notna(fila.get("recurso")):
            lineas = fila["recurso"].strip().split("\n")
            titulo = lineas[0] if lineas else "Recurso"
            contenido = "\n".join(lineas[1:]).strip()
            st.markdown(f"### {titulo}")
            st.text(contenido)

        # Mostrar enlace musical (si existe)
        if pd.notna(fila.get("texto_enlace_musica")) and pd.notna(fila.get("url_musica")):
            st.markdown("### Vamos a ponerte un tema")
            st.markdown(f'<a href="{fila["url_musica"]}" target="_blank">🎵 {fila["texto_enlace_musica"]}</a>', unsafe_allow_html=True)

        # Mostrar otro enlace adicional (si existe)
        if pd.notna(fila.get("texto_enlace_otro")) and pd.notna(fila.get("url_otro")):
            st.markdown("### Déjate Sorprender")
            st.markdown(f'<a href="{fila["url_otro"]}" target="_blank">🔗 {fila["texto_enlace_otro"]}</a>', unsafe_allow_html=True)