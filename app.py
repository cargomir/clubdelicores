import re
import requests
import streamlit as st
from bs4 import BeautifulSoup
import unicodedata
from streamlit_javascript import st_javascript
import base64
from urllib.parse import urljoin

st.set_page_config(
    page_title="Conversor de Monedas",
    page_icon="Imágenes/favicon_10_pesos_simplificado.ico",
    layout="centered"
)

if "moneda_sel" not in st.session_state:
    st.session_state.moneda_sel = "ARS"

# =========================
# Estilo
# =========================

st.markdown(
    """
    <style>
    .stApp { background-color: #fff1fd; }

    /* empuja el selector un poquito a la derecha visualmente (solo escritorio) */
    div[data-testid="column"]:last-child { 
        display:flex; 
        justify-content:flex-end; 
    }

    /* ===== SOLO MÓVIL ===== */
    @media (max-width: 768px) {

        /* quitar padding lateral que corre todo */
        section.main > div {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================
# Detectar ancho (mobile vs desktop)
# =========================

width = st_javascript("window.innerWidth")  # puede devolver None al primer render
if width is None:
    width = 1200  # fallback

is_mobile = width < 700

# =========================
# Config
# =========================
# Nota:
# Este código accede a la página de Indicadores Diarios del Banco Central de Chile,
# identifica dinámicamente el enlace "Ver lista" asociado a "Otros tipos de cambio nominal"
# y obtiene la URL correspondiente para consultar el detalle de esas series.
#
# El sitio del Banco Central genera estos enlaces con parámetros dinámicos, por lo que
# no existe una URL fija y estable para acceder directamente a la lista. Por esta razón,
# el código debe navegar y extraer el enlace desde el HTML de la página cada vez que se ejecuta.
#
# Dado que depende de la estructura del sitio web, este procedimiento puede requerir
# mantención en el futuro si el Banco Central modifica el diseño de la página, los textos
# de los enlaces o la organización del contenido.

URL_INDICADORES = "https://si3.bcentral.cl/Indicadoressiete/secure/IndicadoresDiarios.aspx?Idioma=es-CL"

@st.cache_data(ttl=600)
def _obtener_url_lista_otro_tc() -> str:
    sess = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
        "Referer": "https://si3.bcentral.cl/",
    }

    r = sess.get(URL_INDICADORES, timeout=30, headers=headers, allow_redirects=True)
    r.raise_for_status()
    r.encoding = "utf-8"

    soup = BeautifulSoup(r.text, "html.parser")

    # 1) Buscar el texto exacto del bloque
    texto_objetivo = soup.find(string=lambda s: s and "Otros tipos de cambio nominal" in s)
    if not texto_objetivo:
        raise ValueError("No encontré el texto 'Otros tipos de cambio nominal'.")

    # 2) Subir a un contenedor razonable
    contenedor = texto_objetivo.parent
    for _ in range(5):
        if contenedor is None:
            break

        # buscar dentro del contenedor un link que diga "Ver lista"
        link = contenedor.find("a", string=lambda s: s and s.strip() == "Ver lista")
        if link and link.get("href"):
            return urljoin(URL_INDICADORES, link["href"])

        contenedor = contenedor.parent

    raise ValueError("Encontré el bloque, pero no su link 'Ver lista' asociado.")

# Respaldos (obtenidos desde el sitio web del Banco Central con fecha 16.03.2026)
# Nota:
# Los valores incluidos en este diccionario corresponden a un respaldo manual de tipos de cambio
# expresados en CLP por unidad de moneda extranjera, obtenidos desde el sitio web del Banco Central
# de Chile. Estos datos se utilizan como referencia o respaldo en caso de que la
# consulta automática de indicadores no esté disponible o falle por cambios en la estructura del
# sitio o problemas de conexión. Dado que los tipos de cambio varían diariamente, este bloque requiere mantención periódica.
RESPALDO_CLP_POR = {
    "ARS": 0.65,
    "USD": 913.98,
    "EUR": 1045.62,
    "UYU": 22.52,
    "BRL": 172.74,
    "PEN": 264.72,
    "COP": 0.25,
    "MXN": 51.09,
    "VES": 2.07,
    "BOB": 133.23,
    "CAD": 665.54,
}

FLAGS = {
    "ARS": ("https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1e6-1f1f7.svg", "🇦🇷"),
    "USD": ("https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1fa-1f1f8.svg", "🇺🇸"),
    "EUR": ("https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1ea-1f1fa.svg", "🇪🇺"),
    "UYU": ("https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1fa-1f1fe.svg", "🇺🇾"),
    "CLP": ("https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1e8-1f1f1.svg", "🇨🇱"),
    "BRL": ("https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1e7-1f1f7.svg", "🇧🇷"),
    "PEN": ("https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1f5-1f1ea.svg", "🇵🇪"),
    "COP": ("https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1e8-1f1f4.svg", "🇨🇴"),
    "MXN": ("https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1f2-1f1fd.svg", "🇲🇽"),
    "VES": ("https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1fb-1f1ea.svg", "🇻🇪"),
    "BOB": ("https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1e7-1f1f4.svg", "🇧🇴"),
    "CAD": ("https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1e8-1f1e6.svg", "🇨🇦"),
}

MONEDAS_LABEL = {
    "ARS": "Peso argentino (ARS)",
    "USD": "Dólar estadounidense (USD)",
    "EUR": "Euro (EUR)",
    "UYU": "Peso uruguayo (UYU)",
    "BRL": "Real brasileño (BRL)",
    "PEN": "Sol peruano (PEN)",
    "COP": "Peso colombiano (COP)",
    "MXN": "Peso mexicano (MXN)",
    "VES": "Bolívar venezolano (VES)",
    "BOB": "Boliviano (BOB)",
    "CAD": "Dólar canadiense (CAD)",
}

MONEDAS_ENTERAS = ["ARS", "UYU", "COP", "VES"]

MESES_ABREV = {
    "ene": "01", "feb": "02", "mar": "03", "abr": "04",
    "may": "05", "jun": "06", "jul": "07", "ago": "08",
    "sep": "09", "set": "09", "oct": "10", "nov": "11", "dic": "12",
}

def _extraer_fecha_bcch(texto: str) -> str | None:
    # Busca: "26 Ene 2026" (con variaciones de mayúsculas)
    m = re.search(r"\b(\d{1,2})\s+([A-Za-zÁÉÍÓÚÑáéíóúñ]{3})\s+(\d{4})\b", texto)
    if not m:
        return None
    d, mes_abrev, y = m.groups()
    mes_abrev = mes_abrev.lower()
    mes = MESES_ABREV.get(mes_abrev)
    if not mes:
        return None
    return f"{int(d):02d}-{mes}-{y}"   # "26-01-2026"

def _to_float_es(num_str: str) -> float:
    # "1.234,56" -> 1234.56
    return float(num_str.replace(".", "").replace(",", "."))

def _fmt_cl_es(x: float, dec=2) -> str:
    s = f"{x:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def _fmt_entero_puntos(n: int) -> str:
    # 1234567 -> "1.234.567"
    return format(int(n), ",").replace(",", ".")

def _fmt_decimal_cl(x: float, dec=2) -> str:
    # 1234567.89 -> "1.234.567,89"
    return _fmt_cl_es(x, dec)

def _sin_tildes(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))
    
@st.cache_data(ttl=600)
def _obtener_clp_por_bcch(moneda: str):
    sess = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
        "Referer": "https://si3.bcentral.cl/",
    }

    # Usamos SOLO esta página (la lista) porque trae Euro + Peso argentino,
    # y también trae monedas con el mismo valor que el dólar (p.ej. Balboa panameño).
    url_lista = _obtener_url_lista_otro_tc()  # <-- NUEVO (link del día)
    r = sess.get(url_lista, timeout=30, headers=headers, allow_redirects=True)
    r.raise_for_status()
    r.encoding = "utf-8"  # 👈 clave

    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text("\n", strip=True)
    

    # -------- FECHA DEL DÍA --------
    fecha = _extraer_fecha_bcch(text)

    # -------- MONEDAS --------

    ETIQUETA = {
        "ARS": "Peso argentino",
        "USD": "Balboa panameño",     
        "EUR": "Euro",
        "UYU": "Peso uruguayo",
        "BRL": "Real brasileño",
        "PEN": "Nuevo sol peruano",
        "COP": "Peso colombiano",
        "MXN": "Peso mexicano",
        "VES": "Bolívar fuerte venezolano",
        "BOB": "Boliviano",
        "CAD": "Dólar canadiense",
    }

    etiqueta = ETIQUETA[moneda]

    # Busca: "<Etiqueta> <número estilo ES>"
    text_norm = _sin_tildes(text)
    etiqueta_norm = _sin_tildes(etiqueta)

    m = re.search(
        rf"{re.escape(etiqueta_norm)}\s+(\d+(?:\.\d{{3}})*(?:,\d+)?)",
        text_norm,
        flags=re.I
    )

    if not m:
        raise ValueError(f"No encontré '{etiqueta}' en la lista del día.")

    valor = _to_float_es(m.group(1))

    return valor, fecha

def obtener_clp_por(moneda: str):
    try:
        valor, fecha = _obtener_clp_por_bcch(moneda)
        return valor, "BCCh", fecha
    except Exception as e:
        st.error(f"Error al leer BCCh: {e}")
        return float(RESPALDO_CLP_POR[moneda]), "RESPALDO", None
    
def mostrar_logo_centrado(ruta, ancho=120):
    with open(ruta, "rb") as f:
        data = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <div style="
            width:100%;
            display:flex;
            justify-content:center;
            margin-top:-60px;
        ">
            <img src="data:image/png;base64,{data}" width="{ancho}" />
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# Header (2 layouts: móvil / escritorio)
# =========================

opciones = list(MONEDAS_LABEL.keys())

if is_mobile:
    # --- Logo PERFECTAMENTE centrado (HTML puro) ---
    mostrar_logo_centrado("Imágenes/logo1.png", ancho=120)

    # --- Selector centrado y MÁS ARRIBA ---
    st.markdown("<div style='margin-top:-20px;'>", unsafe_allow_html=True)

    s1, s2, s3 = st.columns([1, 4, 1])
    with s2:
        moneda_sel = st.selectbox(
            "Moneda",
            opciones,
            index=opciones.index(st.session_state.moneda_sel),
            format_func=lambda x: MONEDAS_LABEL[x],
            label_visibility="collapsed"
        )

    st.markdown("</div>", unsafe_allow_html=True)

else:
    # ---- Layout escritorio: logo izquierda + selector derecha (bajado) ----
    col_logo, col_mid, col_der = st.columns([1, 3, 3])

    with col_logo:
        st.markdown(
            "<div style='margin-top:0px; height:100%; display:flex; align-items:center;'>",
            unsafe_allow_html=True
        )
        st.image("Imágenes/logo1.png", width=200)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_mid:
        st.write("")

    with col_der:
        st.markdown("<div style='margin-top:40px;'>", unsafe_allow_html=True)

        moneda_sel = st.selectbox(
            "Moneda",
            opciones,
            index=opciones.index(st.session_state.moneda_sel),
            format_func=lambda x: MONEDAS_LABEL[x],
            label_visibility="collapsed"
        )

        st.markdown("</div>", unsafe_allow_html=True)

st.session_state.moneda_sel = moneda_sel

# Título dinámico
nombre_moneda = {
    "ARS": "Pesos Argentinos",
    "USD": "Dólares",
    "EUR": "Euros",
    "UYU": "Pesos Uruguayos",
    "BRL": "Reales",
    "PEN": "Soles",
    "COP": "Pesos Colombianos",
    "MXN": "Pesos Mexicanos",
    "VES": "Bolívares",
    "BOB": "Bolivianos",
    "CAD": "Dólares Canadienses",
}[moneda_sel]

if is_mobile:
    st.markdown(
        f"""
        <div style="
            text-align:left;
            font-size:22px;
            font-weight:700;
            margin-top:-20px;
            margin-bottom:10px;
        ">
            Conversor {nombre_moneda} ↔ Pesos Chilenos
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.subheader(f"Conversor {nombre_moneda} ↔ Pesos Chilenos")

# Selector dirección
st.markdown( "<div style='font-size:22px; font-weight:700; margin-top:10px;'>Dirección de conversión:</div>", unsafe_allow_html=True ) 

if is_mobile: 
    c1, c2, c3 = st.columns([1, 6, 1]) # centro más ancho 
    with c2: 
        direccion = st.radio( 
            "Dirección de conversión", 
            [f"{moneda_sel} → CLP", f"CLP → {moneda_sel}"], 
            horizontal=True, 
            label_visibility="collapsed", 
            key="direccion_radio" 
            ) 
else: 
    direccion = st.radio( 
        "Dirección de conversión", 
        [f"{moneda_sel} → CLP", f"CLP → {moneda_sel}"], 
        horizontal=True, 
        label_visibility="collapsed", 
        key="direccion_radio" )

# Banderitas para el subtítulo visual
flag_moneda_url, flag_moneda_emoji = FLAGS[moneda_sel]
flag_clp_url, flag_clp_emoji = FLAGS["CLP"]

if direccion.startswith("CLP"):
    flag_izq, flag_der = flag_clp_url, flag_moneda_url
else:
    flag_izq, flag_der = flag_moneda_url, flag_clp_url

# --- BANDERAS CENTRADAS SOLO EN MÓVIL ---
if is_mobile:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; margin: 6px 0 12px 0;">
          <div style="
              display:inline-flex; align-items:center; gap:8px;
              background-color:#ffd6e8; padding:6px 14px; border-radius:20px;
              font-size:20px; font-weight:600; color:#8b004b;
          ">
            <img src="{flag_izq}" width="22" />
            <span> → </span>
            <img src="{flag_der}" width="22" />
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:10px; margin: 6px 0 12px 0;">
          <div style="
              display:inline-flex; align-items:center; gap:8px;
              background-color:#ffd6e8; padding:6px 14px; border-radius:20px;
              font-size:20px; font-weight:600; color:#8b004b;
          ">
            <img src="{flag_izq}" width="22" />
            <span> → </span>
            <img src="{flag_der}" width="22" />
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# Tipo de cambio
# =========================
clp_por_moneda, fuente, fecha_bcch = obtener_clp_por(moneda_sel)

if fuente == "BCCh":
    if fecha_bcch:
        st.caption(
            f"Tipo de cambio: 1 {moneda_sel} ≈ {_fmt_cl_es(clp_por_moneda, 2)} CLP.\n"
            f"Fuente: Banco Central de Chile. Datos al {fecha_bcch}."
        )
    else:
        st.caption(
            f"Tipo de cambio: 1 {moneda_sel} ≈ {_fmt_cl_es(clp_por_moneda, 2)} CLP.\n"
            f"Fuente: Banco Central de Chile, Indicadores diarios."
        )
else:
    st.caption(
        f"Tipo de cambio (respaldo): 1 {moneda_sel} ≈ {_fmt_cl_es(clp_por_moneda, 2)} CLP."
    )
    st.warning("No pude obtener el tipo de cambio del BCCh; usando valor de respaldo.")

moneda_por_clp = 1 / clp_por_moneda  # 1 CLP en moneda seleccionada

# =========================
# Input + cálculo
# =========================
label_input = (
    f"Ingresa el monto en {moneda_sel}:"
    if direccion.startswith(moneda_sel)
    else "Ingresa el monto en pesos chilenos (CLP):"
)

st.markdown(
    f"<div style='font-size:22px; font-weight:700; margin-top:15px;'>{label_input}</div>",
    unsafe_allow_html=True
)

monto = st.number_input(
    "Monto",
    min_value=0,
    step=1,
    format="%d",
    label_visibility="collapsed"
)

if monto > 0:
    if direccion.startswith(moneda_sel):  # MONEDA -> CLP
        resultado = round(monto * clp_por_moneda)

        izq_txt = _fmt_entero_puntos(monto)  # miles con punto (monto es int por tu number_input)
        der_txt = _fmt_entero_puntos(resultado)

        izq_flag = flag_moneda_url
        der_flag = flag_clp_url

    else:  # CLP -> MONEDA
        valor = monto * moneda_por_clp

        # Monedas que se usan sin decimales
        if moneda_sel in MONEDAS_ENTERAS:
            resultado = int(round(valor))
            der_txt = _fmt_entero_puntos(resultado)
        else:
            resultado = round(valor, 2)
            der_txt = _fmt_decimal_cl(resultado, 2)  # miles con punto y coma decimal

        izq_txt = _fmt_entero_puntos(monto)  # CLP siempre entero con miles en punto
        izq_flag = flag_clp_url
        der_flag = flag_moneda_url

    st.markdown(
        f"""
        <div style="
            background-color: #F4F8F3;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-size: 22px;
            font-weight: bold;
            color: #683154;
        ">
            {izq_txt}
            <img src="{izq_flag}" width="26" style="vertical-align:middle; margin-left:6px;" />
            &nbsp; equivalen aproximadamente a &nbsp;
            {der_txt}
            <img src="{der_flag}" width="26" style="vertical-align:middle; margin-left:6px;" />
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <div style="
            background-color: #F4F8F3;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-size: 18px;
            font-weight: 600;
            color: #683154;
        ">
            Ingresa un monto mayor que 0 para realizar la conversión.
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown(
"""
<hr style="margin-top:40px;margin-bottom:10px">

<div style="text-align: center; font-size: 0.9em; color: gray;">
Aplicación desarrollada por <b>Julieta Paz González Loyola</b> y 
<b>Carlos Andrés González Miranda</b><br>
Contacto: consultoraconexos@gmail.com<br>
<i>Santiago de Chile, 2026</i>
</div>
""",
unsafe_allow_html=True
)
