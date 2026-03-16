import streamlit as st
import pandas as pd
from PIL import Image
import base64
from io import BytesIO
import re
import random

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

# === Identificar columnas ===
columnas_licor = recetas.columns[8:56]

# === Paso 1: Aplicar filtro por palabra clave ===
palabra_clave = st.session_state.get("palabra_clave_input", "").strip().lower()

recetas_filtradas = recetas.copy()
if palabra_clave:
    def cocteles_con_palabra(df, col_coctel="coctel"):
        df = df.copy()
        df = df.fillna("").astype(str)
        df["texto_total"] = df.drop(columns=[col_coctel]).agg(" ".join, axis=1).str.lower()
        # Coincidencia también en el nombre del cóctel
        coincidencias_nombre = df[df[col_coctel].str.lower().str.contains(palabra_clave)][col_coctel]
        coincidencias_texto = df[df["texto_total"].str.contains(palabra_clave)][col_coctel]
        return set(coincidencias_nombre) | set(coincidencias_texto)
    
    def cocteles_con_palabra_en_recetas(df, col_coctel="coctel"):
        df = df.copy()
        df = df.fillna("").astype(str)
        texto_filas = df.drop(columns=[col_coctel]).agg(" ".join, axis=1).str.lower()

        # Coincidencia en columnas (nombres de columna)
        columnas_con_match = [col for col in df.columns if palabra_clave in col.lower()]

        desde_texto = df[texto_filas.str.contains(palabra_clave)][col_coctel]
        desde_nombre = df[df[col_coctel].str.lower().str.contains(palabra_clave)][col_coctel]

        if columnas_con_match:
            cols_numericas = df[columnas_con_match].apply(pd.to_numeric, errors='coerce').fillna(0)
            desde_columnas = df[cols_numericas.sum(axis=1) > 0][col_coctel]
        else:
            desde_columnas = pd.Series([], dtype=str)

        return set(desde_texto) | set(desde_nombre) | set(desde_columnas)

    # Unimos los resultados de todas las fuentes
    cocteles_validos = sorted(set(
        cocteles_con_palabra_en_recetas(recetas) |
        cocteles_con_palabra_en_recetas(complementos) |
        cocteles_con_palabra(recursos)
    ))

    # Filtrar
    recetas_filtradas = recetas[recetas["coctel"].isin(cocteles_validos)]
    complementos_filtrados = complementos[complementos["coctel"].isin(cocteles_validos)]
    recursos_filtrados = recursos[recursos["coctel"].isin(cocteles_validos)]

else:
    complementos_filtrados = complementos
    recursos_filtrados = recursos

# === Paso 2: Obtener opciones disponibles actualizadas ===
licores_disponibles = [
    col for col in columnas_licor
    if recetas_filtradas[col].fillna(0).sum() > 0
]

# === Paso 3: Obtener selección actual o default ===
licor_actual = st.session_state.get("licor_sel", "Todos")

# === Paso 4: Selectores de licor e ingrediente ===
# Verificamos si hay cócteles sin alcohol en las recetas filtradas
hay_sin_alcohol = recetas_filtradas[columnas_licor].fillna(0).sum(axis=1).eq(0).any()

# Armamos el selector dinámicamente
opciones_licor = ["Todos"] + sorted(licores_disponibles)
if hay_sin_alcohol and "Sin Alcohol" not in opciones_licor:
    opciones_licor.append("Sin Alcohol")

licor_sel = st.sidebar.selectbox(
    "Filtra por licor base",
    opciones_licor,
    index=opciones_licor.index(licor_actual)
    if licor_actual in opciones_licor else 0,
    key="licor_sel"
)

# === Paso 5: Aplicar filtro por licor ===
recetas_final = recetas_filtradas.copy()

if st.session_state.licor_sel == "Sin Alcohol":
    recetas_final = recetas_final[recetas_final[columnas_licor].fillna(0).sum(axis=1) == 0]
elif st.session_state.licor_sel != "Todos":
    recetas_final = recetas_final[recetas_final[st.session_state.licor_sel].fillna(0) > 0]

# === Paso 6: Mostrar campo de búsqueda por palabra clave ===
palabra_clave_input = st.sidebar.text_input(
    "Buscar por palabra clave",
    value=st.session_state.get("palabra_clave_input", ""),
    key="palabra_clave_input",
    placeholder="Ej: jengibre, limón, Borges",
    help="Escribe una palabra y presiona Enter para buscar"
)

# === Paso 7: Selector de cóctel dependiente ===
cocteles = sorted(recetas_final["coctel"].dropna().unique())

if cocteles:
    coctel_sel = st.sidebar.selectbox(
        "Selecciona un cóctel",
        cocteles,
        index=cocteles.index(
            st.session_state.coctel_sel
        ) if "coctel_sel" in st.session_state and st.session_state.coctel_sel in cocteles else cocteles.index(random.choice(cocteles)),
        key="coctel_sel"
    )
else:
    if "coctel_sel" in st.session_state:
        del st.session_state["coctel_sel"]
    st.sidebar.warning("No hay cócteles para esa búsqueda, inténtalo otra vez.")
    st.stop()

# === Selector tipo de cálculo  ===

# Escoger tipo de cálculo con control de estado limpio
modo_por_defecto = "Cantidad de cócteles"

# Establecer valor predeterminado si no existe
modo_actual = st.session_state.get("modo_forzado", modo_por_defecto)

modo = st.sidebar.radio(
    "Tipo de cantidad",
    ["Cantidad de cócteles", "Volumen total (litros)"],
    index=["Cantidad de cócteles", "Volumen total (litros)"].index(modo_actual),
    key="modo_forzado"
)

# Escoger unidad de medida según modo
unidad_opciones = {
    "Mililitros (ml)": "ml",
    "Onzas (oz)": "oz"
}

# Definir valor por defecto para la interfaz visual
unidad_predeterminada = "Mililitros (ml)"
unidad_label_actual = st.session_state.get("unidad_label", unidad_predeterminada)

if modo == "Cantidad de cócteles":
    unidad_label = st.sidebar.radio(
        "Unidad de medida",
        options=list(unidad_opciones.keys()),
        index=list(unidad_opciones.keys()).index(unidad_label_actual),
        key="unidad_label"
    )
    unidad = unidad_opciones[unidad_label]

else:
    # Forzar visualización y lógica a Mililitros (ml)
    unidad_label = st.sidebar.radio(
        "Unidad de medida",
        ["Mililitros (ml)"],
        index=0,
        key="unidad_label"
    )
    unidad = "ml"


factor_conversion = 1 if unidad == "ml" else 1 / 30

if modo == "Cantidad de cócteles":
    # Controlar valor predeterminado de cantidad
    cantidad_predeterminada = 1
    cantidad_actual = st.session_state.get("cantidad", cantidad_predeterminada)

    cantidad = st.sidebar.number_input(
        "Número de cócteles",
        min_value=1,
        value=cantidad_actual,
        key="cantidad"
    )
    volumen_deseado = None
    litros = None

else:
    opciones_litros = [i * 0.5 for i in range(1, 21)]  # De 0.5 a 10 litros

    # Controlar valor predeterminado para litros (por ejemplo, 1 litro)
    litros_predeterminados = opciones_litros[1]  # es 1.0
    litros_actual = st.session_state.get("litros", litros_predeterminados)

    litros = st.sidebar.selectbox(
        "Litros totales",
        opciones_litros,
        index=opciones_litros.index(litros_actual),
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

# === Obtener ingredientes de la receta seleccionada ===
ingredientes = fila_receta.drop([
    "coctel", "vaso", "tecnica", "capacidad_vaso_sin_hielo",
    "cantidad_hielo", "hielo", "capacidad_vaso_con_hielo", "volumen"
])
ingredientes = ingredientes[ingredientes.notna() & (ingredientes != 0)]

# === Botón de limpiar filtros ===
CAMPOS_RESET = ["licor_sel", "coctel_sel", "unidad_label", "cantidad", "litros", "palabra_clave_input", "modo_forzado"]

if st.sidebar.button("Limpiar selección"):
    for clave in CAMPOS_RESET:
        st.session_state.pop(clave, None)
    st.rerun()

# Cálculo de volumen y factor
# 1. Obtener volumen base y volumen deseado
volumen_base = fila_receta["volumen"]
if modo == "Cantidad de cócteles":
    volumen_deseado = cantidad * volumen_base
else:
    volumen_deseado = litros * 1000

# 2. Calcular factor de escalado
factor = volumen_deseado / volumen_base

# 3. Calcular ingredientes escalados en ml (todos los ingredientes, sin excluir)
ingredientes_escalados_ml = ingredientes * factor

ingredientes_a_gusto = {
    "Sal": "sal",
    "Sal de Apio": "sal de apio",
    "Pimienta": "pimienta",
    "Canela": "canela",
    "Nuez Moscada": "nuez moscada",
    "Whisky o Brandy": "whisky o brandy",
    "Leche Condensada": "leche condensada",
    "Anís Estrella": "anís estrella"
}

ingredientes_gotas = {
    "Amargo de Angostura": "Amargo de Angostura",
    "Salsa Inglesa": "Salsa Inglesa",
    "Salsa Tabasco": "Salsa Tabasco",
    "Agua": "agua",
    "Esencia de Vainilla 2": "esencia de vainilla",
    "Agua de Azahar": "agua de azahar"
}

ingredientes_unidades = {
    "Terrón de Azúcar": "terrón de azúcar",
    "Hojas de Menta": "hojas de menta",
    "Hojas de Albahaca": "hojas de albahaca",
    "Limón Sutil Trozado": "limón sutil trozado",
    "Trozos de Pepino": "trozos de pepino",
    "Trozos de Jengibre": "trozos de jengibre",
    "Frutillas Trozadas": "frutillas trozadas",
    "Moras": "moras",
    "Frambuesas": "frambuesas",
    "Arándanos": "arándanos",
    "Uvas": "uvas",
    "Rama de Canela": "rama(s) de canela",
    "Clavos de Olor": "clavo(s) de olor",
    "Naranja en Rodajas": "naranja(s) en rodajas",	
    "Manzana en Cubos": "manzana(s) en cubos",
    "Huevo": "huevo(s)",
    "Melón": "melón tuna entero",
    "Durazno Trozado": "durazno(s) en cubos",
    "Cascarita de Naranja": "cascarita(s) de naranja"
}

ingredientes_cucharaditas = {
    "Azúcar Flor": "azúcar flor (glas)",
    "Harina Tostada": "harina tostada",
    "Cacao": "cacao en polvo sin azúcar",
    "Esencia de Vainilla 3": "esencia de vainilla",
    "Café Instantáneo": "café instantáneo"
}

ingredientes_cucharadas = {
    "Azúcar": "azúcar",
     "Café Instantáneo 2": "café instantáneo"
}

ingredientes_tazas = {
    "Azúcar 2": "azúcar",
}

ingredientes_gramos = {
    "Chirimoya": "chirimoya",
    "Frutillas": "frutillas",
    "Mango": "mango maduro",
    "Azúcar 3": "azúcar",
    "Leche Condensada 2": "leche condensada"
}

# 4. Convertir a la unidad final (solo líquidos u otros convertibles)
ingredientes_a_excluir = set(ingredientes_a_gusto) | set(ingredientes_gotas) | set(ingredientes_unidades) | set(ingredientes_cucharadas) | set(ingredientes_tazas) | set(ingredientes_gramos)
ingredientes_convertibles = [ing for ing in ingredientes.index if ing not in ingredientes_a_excluir]

ingredientes_ajustados = ingredientes_escalados_ml.copy()
for ing in ingredientes_convertibles:
    ingredientes_ajustados[ing] *= factor_conversion

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
    <p>En <b>Club de Licores</b> entendemos la coctelería como una forma de encuentro y una expresión de cultura, creatividad y alegría. Nos apasiona compartir la mesa y celebrar la buena vida; por eso promovemos un consumo de alcohol moderado y responsable.</p>
    <hr style="margin-top:40px;margin-bottom:15px;">
    <p>Aplicación desarrollada por Carlos Andrés González Miranda (2025). Para consultas o sugerencias, comunícate a través de los siguientes medios:</p>
    <p style="margin-top:0px;">
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

for ing in ingredientes_ajustados.index:
    val_ajustado = ingredientes_ajustados[ing]
    val_base_ml = ingredientes_escalados_ml[ing]

    # Ingredientes que se agregan a gusto
    if ing in ingredientes_a_gusto:
        st.write(f"- Agregar {ingredientes_a_gusto[ing]} a gusto")

    # Ingredientes que se agregan en gotas
    elif ing in ingredientes_gotas:
        st.write(f"- Algunas gotas de {ingredientes_gotas[ing]}")
    
    # Ingredientes que se agregan en unidades
    elif ing in ingredientes_unidades:
        cantidad_u = int(round(val_ajustado))
        nombre_u = ingredientes_unidades[ing]
        st.write(f"- {cantidad_u} {nombre_u}")
    
    # Ingredientes que se agregan en cucharaditas
    elif ing in ingredientes_cucharaditas:
        cantidad_c = int(round(val_ajustado))
        nombre_c = ingredientes_cucharaditas[ing]
        st.write(f"- {cantidad_c} cucharadita(s) de {nombre_c}")

    # Ingredientes que se agregan en cucharadas
    elif ing in ingredientes_cucharadas:
        cantidad_c2 = int(round(val_ajustado))
        nombre_c2 = ingredientes_cucharadas[ing]
        st.write(f"- {cantidad_c2} cucharada(s) de {nombre_c2}")
    
    # Ingredientes que se agregan en tazas
    elif ing in ingredientes_tazas:
        cantidad_c3 = int(round(val_ajustado))
        nombre_c3 = ingredientes_tazas[ing]
        st.write(f"- {cantidad_c3} taza(s) de {nombre_c3}")

    # Ingredientes que se agregan en gramos
    elif ing in ingredientes_gramos:
        cantidad_g = int(round(val_ajustado))
        nombre_g = ingredientes_gramos[ing]
        st.write(f"- {cantidad_g} g de {nombre_g}")

    # Ingredientes con cantidad específica
    else:
        if unidad == "ml":
            cantidad = int(round(val_ajustado))  # Redondea a entero para evitar decimales innecesarios
        else:  # onzas
            cantidad = round(val_ajustado, 2)
            if cantidad.is_integer():
                cantidad = int(cantidad)  # Muestra como 1 en lugar de 1.0 si es entero

        st.write(f"- {cantidad} {unidad} de {ing}")

# === Sección de información para la preparación (si hay) ===
recurso_fila = recursos[recursos["coctel"] == coctel_sel]

if not recurso_fila.empty:
    fila = recurso_fila.iloc[0]
    
    # Mostrar preparación (si existe)
    if pd.notna(fila.get("preparacion")):
        st.markdown("### Preparación")
        st.markdown(f"🥄 {fila['preparacion']}")

# === Sección de jarabes utilizados (si hay) ===

jarabes_columnas = [
    "Jarabe Simple", "Jarabe de Canela", "Jarabe de Jengibre",
    "Jarabe de Menta", "Jarabe de Cedrón", "Jarabe de Romero", 
    "Jarabe de Jamaica", "Jarabe de Miel", "Jarabe de Frambuesa",
    "Jarabe de Butterfly Pea y Jengibre"
]

# Revisa si alguno de los jarabes tiene un valor mayor a 0
jarabes_presentes = [j for j in jarabes_columnas if j in ingredientes.index and ingredientes[j] > 0]

if jarabes_presentes:
    #st.subheader("Jarabe")
    for j in jarabes_presentes:
        fila_jarabe = jarabes[jarabes["jarabe"] == j]
        if not fila_jarabe.empty:
            st.markdown(f"**💡 {j}**")
            st.write(fila_jarabe["preparación"].values[0])

# === Técnica de preparación ===
st.markdown("### Técnica")
st.write(f"🛠️ **{tecnica_info['nombre_español']} ({fila_receta['tecnica']})** – {tecnica_info['descripción']}")

# === Información sobre el hielo ===
hielo = fila_receta["hielo"]
if pd.notna(hielo) and str(hielo).strip().lower() in ["Sí", "Si", "sí", "si"]:
    st.markdown("### Hielo")
    st.write("❄️ Servir con hielo.")
else:
    st.markdown("### Hielo")
    st.write("🚫 Servir sin hielo.")

# === Cristalería sugerida ===
st.markdown("### Cristalería sugerida")
st.write(f"🥂 {fila_receta['vaso']} – {int(fila_receta['capacidad_vaso_sin_hielo'])} ml")

# === Decoración sugerida (complementos con valor 1) ===
fila_complementos = complementos[complementos["coctel"] == coctel_sel]
if not fila_complementos.empty:
    decoraciones = fila_complementos.iloc[0].drop("coctel")
    decoraciones = decoraciones[decoraciones == 1].index.tolist()
    
    if decoraciones:
        st.markdown("### Garnitura (garnish)")
        st.write("🍋‍🟩 Acompañar con: " + ", ".join(decoraciones))

# === Sección recursos asociados (si existen) ===

if not recurso_fila.empty:
    fila = recurso_fila.iloc[0]
    
    # Mostrar observaciones (si existen)
    if pd.notna(fila.get("observaciones")):
        st.markdown("### Observaciones")
        st.markdown(f"📝 {fila['observaciones']}")

    # Verificar si hay al menos un recurso adicional
    hay_recursos = any([
        pd.notna(fila.get("recurso")),
        pd.notna(fila.get("texto_enlace_musica")) and pd.notna(fila.get("url_musica")),
        pd.notna(fila.get("texto_enlace_otro")) and pd.notna(fila.get("url_otro")),
        pd.notna(fila.get("texto_enlace_musica_2")) and pd.notna(fila.get("url_musica_2")),
        pd.notna(fila.get("imagen")),
    ])

    if hay_recursos:
        st.markdown("---")
        st.markdown(
            "<h2 style='color: #e63118; font-size: 36px; font-weight: bold;'>Recursos adicionales</h2>",
            unsafe_allow_html=True
        )
        
        # === Mostrar IMAGEN Y CRÉDITOS ===
        if pd.notna(fila.get("imagen")):
            lineas = [l.strip() for l in fila["imagen"].split("\n") if l.strip()]

            # 1) Primera línea: nombre del archivo
            archivo_imagen = lineas[0] if len(lineas) > 0 else ""

            # 2) El texto (si lo hubiera)
            contenido = "\n".join(lineas[1:]) if len(lineas) > 1 else ""

            # Ruta completa
            image_path = f"imagenes/{archivo_imagen}"

            # Mostrar imagen desde carpeta local
            if os.path.exists(image_path):
                st.image(image_path, width="stretch")
            else:
                st.warning(f"Imagen no encontrada: {archivo_imagen}")

            # Mostrar texto si existe(opcional)
            if contenido:
                st.text(contenido)
                
       # Mostrar recurso largo (como poema o relato)
        if pd.notna(fila.get("recurso")):
            lineas = fila["recurso"].strip().split("\n")
            titulo = lineas[0] if lineas else "Recurso"
            contenido = "\n".join(lineas[1:]).strip()
            st.markdown(f"### {titulo}")
            st.text(contenido)

        # Mostrar otro enlace adicional (si existe)
        if pd.notna(fila.get("texto_enlace_otro")) and pd.notna(fila.get("url_otro")):
            st.markdown("### Déjate Sorprender")
            st.markdown(f'<a href="{fila["url_otro"]}" target="_blank">📼 {fila["texto_enlace_otro"]}</a>', unsafe_allow_html=True)

        # Mostrar enlace musical (si existe)
        if pd.notna(fila.get("texto_enlace_musica")) and pd.notna(fila.get("url_musica")):
            st.markdown("### Vamos a ponerte un tema")
            st.markdown(
                f'<a href="{fila["url_musica"]}" target="_blank">📀 {fila["texto_enlace_musica"]}</a>',
                unsafe_allow_html=True
            )

            # Mostrar explicación si existe
            if pd.notna(fila.get("cita_letra")):
                st.markdown(
                    f'>La canción se seleccionó porque este verso lo pide:\n>\n> *{fila["cita_letra"]}*'
                )

        # Mostrar otro enlace musical (si existe)
        if pd.notna(fila.get("texto_enlace_musica_2")) and pd.notna(fila.get("url_musica_2")):
            st.markdown("### Vamos a ponerte otro tema")
            st.markdown(
                f'<a href="{fila["url_musica_2"]}" target="_blank">📀 {fila["texto_enlace_musica_2"]}</a>',
                unsafe_allow_html=True
            )

            # Mostrar explicación si existe
            if pd.notna(fila.get("cita_letra_2")):
                st.markdown(
                    f'>La canción se seleccionó porque este verso lo pide:\n>\n> *{fila["cita_letra_2"]}*'
                )


st.markdown(
"""
<hr style="margin-top:40px;margin-bottom:10px">

<div style="text-align: center; font-size: 0.9em; color: gray;"></i>
<i>Aplicación desarrollada por <b>Carlos Andrés González Miranda</b><br></i>
<i>Contacto: clubdelicores@gmail.com<br></i>
<i>Santiago de Chile, 2025</i>
</div>
""",
unsafe_allow_html=True
)
        