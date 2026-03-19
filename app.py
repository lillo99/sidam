"""
Sidam - Distinta Base Extractor
Web App Streamlit locale
"""

import io
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from distinta_base_extractor import MEDIA_TYPES, build_excel, extract_bom

load_dotenv()

# Legge la chiave da .env (locale) oppure da st.secrets (Streamlit Cloud)
def _get_api_key() -> str:
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return os.getenv("ANTHROPIC_API_KEY", "")

# ── Configurazione pagina ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="Distinta Base Extractor · Sidam",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .step-header {
        background: #f0f4ff;
        border-left: 4px solid #4472C4;
        padding: 0.4rem 0.8rem;
        border-radius: 0 6px 6px 0;
        margin-bottom: 0.8rem;
        font-weight: 600;
    }
    .stDataEditor { font-size: 13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🏭 Distinta Base\nExtractor")
    st.divider()
    st.subheader("⚙️ Impostazioni")
    api_key_input = st.text_input(
        "Anthropic API Key",
        value=_get_api_key(),
        type="password",
        help="In locale: usa il file .env. Su Streamlit Cloud: usa i Secrets dell'app.",
    )
    st.divider()
    st.markdown(
        "**Come si usa:**\n"
        "1. Carica lo screenshot del gestionale\n"
        "2. (opzionale) Carica il template Excel\n"
        "3. Clicca **Estrai Distinta Base**\n"
        "4. Correggi i dati se necessario\n"
        "5. Copia la tabella o scarica l'Excel"
    )
    st.divider()
    st.caption("Powered by Claude Opus · Sidam")

# ── Intestazione ───────────────────────────────────────────────────────────────

st.title("🏭 Distinta Base Extractor")
st.markdown("Carica uno screenshot del gestionale e ottieni la distinta base pronta per Excel.")

col_left, col_right = st.columns([1, 1], gap="large")

# ── STEP 1: Upload immagine ───────────────────────────────────────────────────

with col_left:
    st.markdown('<div class="step-header">📷 Step 1 · Screenshot gestionale</div>', unsafe_allow_html=True)
    uploaded_img = st.file_uploader(
        "Trascina qui lo screenshot",
        type=["png", "jpg", "jpeg", "webp"],
        key="image_uploader",
        label_visibility="collapsed",
    )
    if uploaded_img:
        st.image(uploaded_img, caption=uploaded_img.name, use_container_width=True)

# ── STEP 2: Upload template Excel ─────────────────────────────────────────────

with col_right:
    st.markdown('<div class="step-header">📄 Step 2 · Template Excel (opzionale)</div>', unsafe_allow_html=True)
    uploaded_xlsx = st.file_uploader(
        "Carica il file Excel template (.xlsx)",
        type=["xlsx", "xls"],
        key="excel_uploader",
        label_visibility="collapsed",
    )
    if uploaded_xlsx:
        st.success(f"Template caricato: **{uploaded_xlsx.name}**")
        if uploaded_xlsx.name.endswith(".xls"):
            st.warning("Il file verrà convertito automaticamente in .xlsx")

st.divider()

# ── STEP 3: Estrazione ────────────────────────────────────────────────────────

st.markdown('<div class="step-header">🤖 Step 3 · Estrai con Claude Vision</div>', unsafe_allow_html=True)

if st.button("🚀 Estrai Distinta Base", type="primary", disabled=(uploaded_img is None)):
    if not api_key_input:
        st.error("Inserisci la Anthropic API Key nella barra laterale.")
        st.stop()

    media_type = MEDIA_TYPES.get(Path(uploaded_img.name).suffix.lower(), "image/png")
    image_bytes = uploaded_img.read()

    with st.spinner("Claude sta analizzando l'immagine..."):
        try:
            items = extract_bom(image_bytes, media_type, api_key=api_key_input)
            st.session_state["items"] = items
            st.session_state["extraction_done"] = True
        except Exception as e:
            st.error(f"Errore durante l'estrazione: {e}")
            st.stop()

    st.success(f"✅ Estratti **{len(items)} componenti**")

# ── STEP 4: Revisione tabella ─────────────────────────────────────────────────

COL_DISPLAY = ["Descrizione componente", "Codice articolo", "Quantità", "Unità di misura"]
COL_KEYS    = ["denominazione", "codice", "quantita", "um"]

if st.session_state.get("extraction_done"):
    st.divider()
    st.markdown('<div class="step-header">✏️ Step 4 · Revisiona e correggi</div>', unsafe_allow_html=True)
    st.caption("Puoi modificare direttamente le celle. Le modifiche si riflettono automaticamente su Step 5.")

    df = pd.DataFrame(st.session_state["items"], columns=COL_KEYS)
    df.columns = COL_DISPLAY

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Descrizione componente": st.column_config.TextColumn(width="large"),
            "Codice articolo":        st.column_config.TextColumn(width="small"),
            "Quantità":               st.column_config.TextColumn(width="small"),
            "Unità di misura":        st.column_config.TextColumn(width="small"),
        },
        hide_index=True,
        key="editor",
    )

    # Sincronizza session state con le modifiche dell'editor
    st.session_state["items"] = (
        edited_df.rename(columns=dict(zip(COL_DISPLAY, COL_KEYS)))
        .to_dict("records")
    )

    # ── STEP 5: Copia & Download ───────────────────────────────────────────────

    st.divider()
    st.markdown('<div class="step-header">⬇️ Step 5 · Copia tabella o scarica Excel</div>', unsafe_allow_html=True)

    tab_copy, tab_download = st.tabs(["📋 Copia negli appunti", "📥 Scarica Excel"])

    # Tab "Copia": genera TSV (tab-separated) → incollabile direttamente in Excel
    with tab_copy:
        st.caption(
            "Clicca **Copy** in alto a destra del riquadro, "
            "poi incolla direttamente nel foglio Excel con **Ctrl+V** / **Cmd+V**."
        )
        # Intestazione + righe separate da tab — Excel riconosce automaticamente le colonne
        tsv_lines = ["\t".join(COL_DISPLAY)]
        for item in st.session_state["items"]:
            tsv_lines.append(
                "\t".join([
                    str(item.get("denominazione", "")),
                    str(item.get("codice", "")),
                    str(item.get("quantita", "")),
                    str(item.get("um", "")),
                ])
            )
        tsv_text = "\n".join(tsv_lines)
        st.code(tsv_text, language=None)

    # Tab "Scarica": genera file .xlsx completo
    with tab_download:
        template_bytes = None
        output_name = "distinta_base.xlsx"

        if uploaded_xlsx:
            raw = uploaded_xlsx.read()
            if uploaded_xlsx.name.endswith(".xls"):
                import xlrd, openpyxl as oxl
                wb_old = xlrd.open_workbook(file_contents=raw)
                wb_new = oxl.Workbook()
                wb_new.remove(wb_new.active)
                for sh in wb_old.sheets():
                    ws_n = wb_new.create_sheet(title=sh.name)
                    for r in range(sh.nrows):
                        for c in range(sh.ncols):
                            v = sh.cell(r, c).value
                            ws_n.cell(row=r+1, column=c+1, value=v if v != "" else None)
                buf = io.BytesIO()
                wb_new.save(buf)
                template_bytes = buf.getvalue()
            else:
                template_bytes = raw
            output_name = Path(uploaded_xlsx.name).stem + "_aggiornato.xlsx"

        excel_bytes = build_excel(st.session_state["items"], template_bytes)

        col_dl, col_info = st.columns([1, 2])
        with col_dl:
            st.download_button(
                label="📥 Scarica Excel",
                data=excel_bytes,
                file_name=output_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
        with col_info:
            st.info(
                f"**{len(st.session_state['items'])} righe** nel foglio DATABASE.\n\n"
                f"Colonne: Descrizione componente · Codice articolo · Quantità · Unità di misura"
            )
