# app.py
# -*- coding: utf-8 -*-
"""
Pizza Dough Wizard Web-App (Streamlit)

Upgrade v2:
- Fix für f-string Formatierungsfehler (keine Formatbedingung im Format-Spec)
- ⚙️ Einstellungsrad (Sidebar):
  - Sprache: Deutsch/Englisch
  - Tag-/Nachtmodus (Light/Dark mit Symbol)
  - Experten-Modus:
    • Esser-Typen + Faktoren bearbeitbar/erweiterbar
    • Rezeptparameter (Hefe/Salz pro kg Mehl) anpassbar
    • Referenzgewicht einer Standard‑Pizza (Normalesser) anpassbar
    • Einstellungen werden in der Session gespeichert und können als JSON exportiert/importiert
- Responsives, minimalistisches UI mit sanften Animationen
- "Gabriel"-Regel: Wenn aktiv, keine Reste
"""

import json
import math
from dataclasses import asdict, dataclass


import pandas as pd
import streamlit as st

# Optional: editable dark-themed grid (fallback to st.data_editor if unavailable)
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    AGGRID_AVAILABLE = True
except Exception:
    AGGRID_AVAILABLE = False

# Safe check: only touch session_state when a Streamlit context exists
try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx  # available in newer Streamlit
    def _has_ctx():
        try:
            return get_script_run_ctx() is not None
        except Exception:
            return False
except Exception:
    def _has_ctx():
        return False

if _has_ctx():
    if "printed_start" not in st.session_state:
        print("Starting App...")
        st.session_state.printed_start = True
else:
    # Running without Streamlit (e.g., `python app.py`) – print once.
    print("Starting App...")

# ---------- Page config ----------
st.set_page_config(
    page_title="Pizza Dough – Rechner",
    page_icon="🍕",
    layout="wide",
)

# ---------- Streamlit theme (primary color) ----------
def _apply_streamlit_theme():
    """Force Streamlit's primary color so active UI states (e.g., segmented control) use our accent.
    Safe no-op if the option isn't available in this Streamlit build."""
    try:
        st._config.set_option("theme.primaryColor", "#ff4b4b")
    except Exception:
        # Streamlit build doesn't support setting this at runtime; ignore.
        pass

_apply_streamlit_theme()

# ---------- i18n ----------
STRINGS = {
    "de": {
        "title": "🍕 Pizza Dough Wizard",
        "badge": "Schnell • Minimal • Genau",
        "settings": "Einstellungen",
        "lang": "Sprache",
        "theme": "Modus",
        "light": "Tag",
        "dark": "Nacht",
        "expert": "Experten‑Modus",
        "import": "Konfiguration importieren",
        "export": "Konfiguration exportieren",
        "eaters": "Esser‑Typen & Faktoren",
        "eaters_caption": "• Füge Zeilen hinzu oder passe Faktoren an. 'Gabriel' ist separat um Reste zu deaktivieren.",
        "add_row": "Zeile hinzufügen",
        "delete_selected": "Ausgewählte löschen",
        "recipe": "Rezeptparameter",
        "normal_weight": "Referenzgewicht pro Standard‑Pizza (Normalesser, g)",
        "yeast_per_kg": "Hefe pro 1 kg Mehl (g)",
        "salt_per_kg": "Salz pro 1 kg Mehl (g)",
        "hydration": "Hydrationslevel",
        "weak_eaters": "Wenig‑Esser",
        "normal_eaters": "Normal‑Esser",
        "heavy_eaters": "Viel‑Esser",
        "gabriel": "Gabriel Modus",
        "gabriel_help": "Gabriel ist anwesend – er isst alle Reste auf (keine Reste).",
        "note": "Hinweis: Ergebnisse sind Näherungswerte. Dichteunterschiede bei Mehl/Wasser können leichte Abweichungen erzeugen.",
        "prep_title": "Zubereitung",
        "prep_text": (
            "Nimm etwas von dem Wasser und löse das Salz darin. Löse in dem restlichen Wasser die Hefe hauf. "
            "Gib das Mehl in eine Schüssel. Gib nun die aufgelöste Hefe hinzu und verknete die Masse kurz. "
            "Gib dann das restliche Wasser mit dem aufgelösten Salz hinzu. Verknete den Teig nun ca. 10 Min. händisch "
            "(oder ca. 5 Min. in einer Knetmaschine). Lasse den Teig dann 30 Min. bei Zimmertemperatur ruhen und bedecke "
            "ihn mit einem feuchten Tuch. Portiniere den Teig anschließend. Lasse den Teig nach dem Portionieren 24-72 Stunden "
            "im Kühlschrank ziehen. Zuletzt: Genieße deine Pizza!"
        ),
        "result": "Deine Zutaten",
        "need_pizzas": "Benötigte Pizzen (äquivalent)",
        "make_pizzas": "Pizzen, die wir machen",
        "leftovers": "Reste (Pizzen)",
        "no_leftovers": "Reste (Pizzen)",
        "hydration_metric": "Hydration",
        "flour": "Mehl",
        "water": "Wasser",
        "yeast": "Hefe",
        "salt": "Salz",
        "teig_hint": "≈ Gesamtteig: {dough} g • Referenzgewicht pro Standard‑Pizza: {std} g",
        "details": "Details & Formel‑Herkunft",
        "details_md": (
            "- Basis: **1 kg Mehl** ⇒ **{pizzas_per_kg:.0f}** Standard‑Pizzen. Hefe **{yeast} g**, Salz **{salt} g** pro **1 kg Mehl**.\n"
            "- Hydration = Wasser/Mehl. Beispiel 60 % ⇒ 600 ml Wasser auf 1 kg Mehl.\n"
            "- Bedarf in Standard‑Pizzen = faktorbasierte Summe der Esser‑Typen.\n"
            "- Ohne *Gabriel*: Pizzen werden auf **ganze** Stücke aufgerundet ⇒ mögliche Reste.\n"
            "- Mit *Gabriel*: wir produzieren **exakt** den Bedarf ⇒ **keine Reste**."
        ),
        "toast": "Berechnung aktualisiert",
        "upload_cfg": "JSON hochladen",
    },
    "en": {
        "title": "🍕 Pizza Dough Wizard",
        "badge": "Fast • Minimal • Precise",
        "settings": "Settings",
        "lang": "Language",
        "theme": "Theme",
        "light": "Light",
        "dark": "Dark",
        "expert": "Expert Mode",
        "import": "Import configuration",
        "export": "Export configuration",
        "eaters": "Eater types & factors",
        "eaters_caption": "• Add rows or adjust factors. 'Gabriel' is separate to disable leftovers.",
        "add_row": "Add row",
        "delete_selected": "Delete selected",
        "recipe": "Recipe parameters",
        "normal_weight": "Reference weight per standard pizza (normal eater, g)",
        "yeast_per_kg": "Yeast per 1 kg flour (g)",
        "salt_per_kg": "Salt per 1 kg flour (g)",
        "hydration": "Hydration level",
        "weak_eaters": "Light eaters",
        "normal_eaters": "Normal eaters",
        "heavy_eaters": "Big eaters",
        "gabriel": "Gabriel joins (no leftovers)",
        "gabriel_help": "Gabriel is present – he eats any leftovers (no leftovers).",
        "note": "Note: Results are approximations. Density differences in flour/water may cause slight deviations.",
        "prep_title": "Preparation",
        "prep_text": (
            "Take some of the water and dissolve the salt in it. Dissolve the yeast in the remaining water. "
            "Put the flour in a bowl. Add the dissolved yeast and knead briefly. Then add the remaining water with the "
            "dissolved salt. Knead the dough for about 10 minutes by hand (or about 5 minutes in a mixer). Let the dough rest "
            "for 30 minutes at room temperature and cover it with a damp cloth. Portion the dough afterwards. Let the dough rest "
            "in the fridge for 24–72 hours. Finally: enjoy your pizza!"
        ),
        "result": "Your ingredients",
        "need_pizzas": "Required pizzas (equivalent)",
        "make_pizzas": "Pizzas we make",
        "leftovers": "Leftovers (pizzas)",
        "no_leftovers": "Leftovers (pizzas)",
        "hydration_metric": "Hydration",
        "flour": "Flour",
        "water": "Water",
        "yeast": "Yeast",
        "salt": "Salt",
        "teig_hint": "≈ Total dough: {dough} g • Reference weight per standard pizza: {std} g",
        "details": "Details & formulas",
        "details_md": (
            "- Base: **1 kg flour** ⇒ **{pizzas_per_kg:.0f}** standard pizzas. Yeast **{yeast} g**, salt **{salt} g** per **1 kg flour**.\n"
            "- Hydration = water/flour. Example 60% ⇒ 600 ml water per 1 kg flour.\n"
            "- Demand in standard pizzas = factor-based sum of eater types.\n"
            "- Without *Gabriel*: pizzas are rounded **up** to whole pieces ⇒ possible leftovers.\n"
            "- With *Gabriel*: we produce **exact** demand ⇒ **no leftovers**."
        ),
        "toast": "Calculation updated",
        "upload_cfg": "Upload JSON",
    },
}


def T(key):
    # Robust gegen fehlende/temporär None Sprache während Reruns
    lang = st.session_state.get("lang") or "de"
    lang_dict = STRINGS.get(lang, STRINGS["de"])  # Fallback zu Deutsch
    return lang_dict.get(key, key)  # Fallback: Schlüsselname anzeigen

# ---------- Defaults & session ----------
@dataclass
class Recipe:
    pizzas_per_kg: float = 6.0
    yeast_per_kg: float = 7.0
    salt_per_kg: float = 32.0
    normal_pizza_g: float = 273.1667


def init_state():
    if "recipe" not in st.session_state:
        st.session_state.recipe = Recipe()
    if "eater_df" not in st.session_state:
        st.session_state.eater_df = pd.DataFrame([
            {"name": "Wenig-Esser", "factor": 0.5},
            {"name": "Normal-Esser", "factor": 1.0},
            {"name": "Viel-Esser", "factor": 1.5},
        ])
    if "lang" not in st.session_state:
        st.session_state.lang = "de"
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    if "expert" not in st.session_state:
        st.session_state.expert = False
        
# --- Localization helper for eater names (only known defaults) ---
def _localize_eater_names_to(lang: str):
    if "eater_df" not in st.session_state:
        return
    mapping_de_to_en = {"Wenig-Esser": "Weak-Eater", "Normal-Esser": "Normal-Eater", "Viel-Esser": "Heavy-Eater"}
    mapping_en_to_de = {v: k for k, v in mapping_de_to_en.items()}
    df = st.session_state.eater_df.copy()
    if "name" in df.columns:
        if lang == "en":
            df["name"] = df["name"].replace(mapping_de_to_en)
        else:
            df["name"] = df["name"].replace(mapping_en_to_de)
        st.session_state.eater_df = df

init_state()


# ---------- Minimal styles & theme toggle ----------
BASE_CSS = """
<style>
:root {
  --page-bg: #ffffff;
  --text: #0b0f14;
  --panel-bg: #ffffff;
  --panel-border: rgba(0,0,0,.06);
  --accent: #ff4b4b;
  --muted: #6b7280;
  --header-bg: #ffffff;
  --header-text: #0b0f14;
  --sidebar-bg: #f8fafc;
  --sidebar-text: #0b0f14;
  --metric-text: #0b0f14;
}

/* App container */
[data-testid="stAppViewContainer"] { background: var(--page-bg); color: var(--text); }

/* Top header */
[data-testid="stHeader"] { background: var(--header-bg); color: var(--header-text); }
[data-testid="stHeader"] * { color: var(--header-text); }

/* Sidebar */
[data-testid="stSidebar"] { background: var(--sidebar-bg); }
[data-testid="stSidebar"] * { color: var(--sidebar-text); }

/* Panels */
.panel { background: var(--panel-bg); border:1px solid var(--panel-border); border-radius:14px; padding:.9rem 1rem; }

/* Layout tweaks */
section.main > div { padding-top:.5rem; }
.badge { display:inline-flex; gap:.5rem; align-items:center; padding:.4rem .7rem; border-radius:999px; background: rgba(255,75,75,.12); color: var(--accent); font-weight:600; font-size:.85rem; animation: popIn .4s ease-out both; }
@keyframes popIn { from { transform: scale(.95); opacity:0;} to { transform: scale(1); opacity:1;} }

/* Metrics: make values readable in dark mode via variable */
[data-testid="stMetricValue"] { color: var(--metric-text) !important; }
[data-testid="stMetricLabel"] { color: var(--muted) !important; }
/* Widget labels (number inputs, sliders, toggles): use muted text for consistency */
[data-testid="stWidgetLabel"] label,
[data-testid="stWidgetLabel"] * {
  color: var(--muted) !important;
}
/* Extra safety for select_slider containers */
div[data-testid="stSelectSlider"] label { color: var(--muted) !important; }

/* Segmented control – improve contrast for unselected options (default dark style) */
[data-testid="stSegmentedControl"] button[aria-pressed="false"] {
  background: rgba(255,255,255,.06) !important;
  color: var(--muted) !important;
  border-color: rgba(255,255,255,.12) !important;
}

/* Sidebar widgets and expanders: align to theme variables */
[data-testid="stSidebar"] [data-testid="stExpander"] {
  background: var(--panel-bg) !important;
  border: 1px solid var(--panel-border) !important;
  border-radius: 12px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary,
[data-testid="stSidebar"] [data-testid="stExpander"] * {
  color: var(--sidebar-text) !important;
}
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] select {
  background: var(--panel-bg) !important;
  color: var(--sidebar-text) !important;
  border-color: var(--panel-border) !important;
}
</style> 
"""

st.markdown(BASE_CSS, unsafe_allow_html=True)
if st.session_state.theme == "dark":
    THEME_CSS = """
    <style>
    :root {
      --page-bg: #0b0f14;
      --text: #e6edf3;
      --panel-bg: #0b1117;
      --panel-border: rgba(255,255,255,.10);
      --header-bg: #0b0f14;
      --header-text: #e6edf3;
      --sidebar-bg: #10151c;
      --sidebar-text: #e6edf3;
      --metric-text: #f5f7fa;
      --accent: #ff4b4b;
      --primary-color: var(--accent);
      --color-primary: var(--accent);
    }

    /*
      Dark mode – streamlined
      NOTE: Streamlit's st.data_editor isn't fully themeable; we avoid heavy overrides.
    */

    /* Segmented control container */
    [data-testid="stSegmentedControl"] > div,
    [data-testid="stSidebar"] [data-testid="stSegmentedControl"] > div {
      background: #16202b !important;
      border: 1px solid rgba(255,255,255,.12) !important;
      border-radius: 9999px !important;
      box-shadow: none !important;
    }
    
    /* All segmented control buttons - basic styling */
    [data-testid="stSegmentedControl"] button {
      background: transparent !important;
      box-shadow: none !important;
      outline: none !important;
    }
    
    /* Unselected segmented control buttons */
    [data-testid="stSegmentedControl"] button[aria-pressed="false"] {
      background: #16202b !important;
      color: var(--text) !important;
      border: 1px solid var(--panel-border) !important;
    }
    
    /* Selected segmented control buttons - COMPREHENSIVE FIX */
    /* Try multiple selectors to catch different Streamlit implementations */
    [data-testid="stSegmentedControl"] button[aria-pressed="true"],
    [data-testid="stSegmentedControl"] button[aria-selected="true"],
    [data-testid="stSegmentedControl"] button.selected,
    [data-testid="stSegmentedControl"] button:active,
    [data-testid="stSegmentedControl"] button[data-selected="true"],
    [data-testid="stSegmentedControl"] button[role="tab"][aria-selected="true"],
    [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button[aria-pressed="true"],
    [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button[aria-selected="true"],
    [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button.selected,
    [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button:active,
    [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button[data-selected="true"],
    [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button[role="tab"][aria-selected="true"] {
      background: var(--accent) !important;
      color: #ffffff !important;
      border-color: var(--accent) !important;
      box-shadow: none !important;
    }
    
    /* Force override any competing styles for selected state */
    [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button:not([aria-pressed="false"]):not([aria-selected="false"]) {
      background: var(--accent) !important;
      color: #ffffff !important;
      border-color: var(--accent) !important;
    }

    /* Panels & expanders */
    [data-testid="stExpander"] {
      background: var(--panel-bg) !important;
      border: 1px solid var(--panel-border) !important;
      border-radius: 12px !important;
      box-shadow: none !important;
    }
    [data-testid="stExpander"] summary { 
      color: var(--text) !important; 
    }
    [data-testid="stExpander"] summary:hover { 
      background: #121a24 !important; 
    }
    
    /* Fix for expanded expander headers - comprehensive approach */
    [data-testid="stExpander"][aria-expanded="true"] summary,
    [data-testid="stExpander"].expanded summary,
    [data-testid="stExpander"] details[open] summary,
    [data-testid="stExpander"] summary[aria-expanded="true"] {
      background: #0e1319 !important;
      color: var(--text) !important;
    }
    
    /* Sidebar specific expander fixes */
    [data-testid="stSidebar"] [data-testid="stExpander"][aria-expanded="true"] summary,
    [data-testid="stSidebar"] [data-testid="stExpander"].expanded summary,
    [data-testid="stSidebar"] [data-testid="stExpander"] details[open] summary,
    [data-testid="stSidebar"] [data-testid="stExpander"] summary[aria-expanded="true"] {
      background: #0e1319 !important;
      color: var(--sidebar-text) !important;
    }
    
    /* Force override any white background on expanded state */
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:not([aria-expanded="false"]) {
      background: #0e1319 !important;
    }

    /* Sidebar buttons (incl. uploader/download) */
    [data-testid="stSidebar"] button {
      background: #0e1319 !important;
      color: var(--text) !important;
      border: 1px solid var(--panel-border) !important;
      box-shadow: none !important;
    }
    [data-testid="stSidebar"] button:hover { background: #121a24 !important; }
    [data-testid="stFileUploaderDropzone"] {
      background: var(--panel-bg) !important;
      border: 1px dashed var(--panel-border) !important;
      border-radius: 12px !important;
    }

    /* Number inputs (± steppers) */
    [data-testid="stNumberInput"] input {
      background: var(--panel-bg) !important;
      color: var(--text) !important;
      border: 1px solid var(--panel-border) !important;
    }
    [data-testid="stNumberInput"] button {
      background: #0e1319 !important;
      color: var(--text) !important;
      border: 1px solid var(--panel-border) !important;
    }
    [data-testid="stNumberInput"] button:hover { background: #121a24 !important; }

    /* Override sidebar button styling for segmented control buttons specifically */
    [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button[aria-pressed="true"] {
      background: var(--accent) !important;
      color: #ffffff !important;
      border-color: var(--accent) !important;
    }
    [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button[aria-pressed="false"] {
      background: #16202b !important;
      color: var(--text) !important;
      border: 1px solid var(--panel-border) !important;
    }

    /* Ensure SegmentedControl inherits the primary color */
    [data-testid="stSegmentedControl"] {
      --primary-color: var(--accent) !important;
      --color-primary: var(--accent) !important;
    }
    </style>
    """
else:
    THEME_CSS = """
    <style>
    :root {
      --page-bg: #ffffff;
      --text: #0b0f14;
      --panel-bg: #ffffff;
      --panel-border: rgba(0,0,0,.06);
      --header-bg: #ffffff;
      --header-text: #0b0f14;
      --sidebar-bg: #f8fafc;
      --sidebar-text: #0b0f14;
      --metric-text: #0b0f14;
    }
    /* Light mode tweak for segmented control (unselected) */
    [data-testid="stSegmentedControl"] button[aria-pressed="false"] {
      background: #f2f4f7 !important;
      color: #475467 !important;
      border-color: rgba(0,0,0,.08) !important;
    }
    </style>
    """
st.markdown(THEME_CSS, unsafe_allow_html=True)

# ---------- Sidebar (settings gear) ----------
st.sidebar.header("⚙️ " + T("settings"))

# Language
curr_lang = st.session_state.get("lang", "de")
prev_lang = curr_lang

if hasattr(st.sidebar, "segmented_control"):
    lang_choice = st.sidebar.segmented_control(
        T("lang"),
        options=["de", "en"],
        format_func=lambda x: "Deutsch" if x == "de" else "English",
        default=curr_lang,
        key="lang_selector",
    )
else:
    lang_choice = st.sidebar.radio(
        T("lang"),
        options=["de", "en"],
        format_func=lambda x: "Deutsch" if x == "de" else "English",
        index=0 if curr_lang == "de" else 1,
        key="lang_selector",
    )

# Nur aktualisieren, wenn der Wert gültig ist (None ignorieren)
if lang_choice in ("de", "en") and lang_choice != curr_lang:
    st.session_state.lang = lang_choice
    st.rerun()
    
# If language changed since last render, localize eater names for known defaults
if st.session_state.get("_last_lang") != st.session_state.lang:
    _localize_eater_names_to(st.session_state.lang)
    st.session_state._last_lang = st.session_state.lang

# Theme
prev_theme = st.session_state.theme
theme_choice = st.sidebar.toggle(T("theme") + " 🌙/☀️", value=(st.session_state.theme=="dark"))
st.session_state.theme = "dark" if theme_choice else "light"
if st.session_state.theme != prev_theme:
    st.rerun()

# Expert mode
prev_expert = st.session_state.expert
st.session_state.expert = st.sidebar.toggle(T("expert"), value=st.session_state.expert)
if st.session_state.expert != prev_expert:
    st.rerun()

# Config import/export
with st.sidebar.expander("🧩 Config"):
    up = st.file_uploader(T("upload_cfg"), type=["json"], label_visibility="collapsed")
    if up is not None:
        data = json.load(up)
        # Load recipe
        r = data.get("recipe", {})
        st.session_state.recipe = Recipe(**{**asdict(st.session_state.recipe), **r})
        # Load eaters
        eaters = data.get("eaters")
        if eaters:
            st.session_state.eater_df = pd.DataFrame(eaters)
        st.rerun()

    export_payload = {
        "recipe": asdict(st.session_state.recipe),
        "eaters": st.session_state.eater_df.to_dict(orient="records"),
        "lang": st.session_state.lang,
        "theme": st.session_state.theme,
    }
    st.download_button(T("export"), data=json.dumps(export_payload, indent=2), file_name="pizza_cfg.json", mime="application/json")

# Expert editors
if st.session_state.expert:
    with st.sidebar.expander("👥 " + T("eaters"), expanded=False):
        st.caption(T("eaters_caption"))
        name_label = "Name"  # same in DE/EN
        factor_label = "Factor" if st.session_state.lang == "en" else "Faktor"

        if AGGRID_AVAILABLE:
            # Configure AgGrid with dark theme support and editing
            df = st.session_state.eater_df.copy()
            gob = GridOptionsBuilder.from_dataframe(df)
            gob.configure_default_column(editable=True, resizable=True)
            gob.configure_column("name", header_name=name_label)
            gob.configure_column(
                "factor",
                header_name=factor_label,
                type=["numericColumn", "numberColumnFilter"],
                valueParser="Number(params.newValue)",
            )
            gob.configure_selection("multiple", use_checkbox=True)
            grid_options = gob.build()

            theme = "alpine-dark" if st.session_state.theme == "dark" else "alpine"
            grid_resp = AgGrid(
                df,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.VALUE_CHANGED,
                theme=theme,
                fit_columns_on_grid_load=True,
                allow_unsafe_jscode=True,
                height=220,
            )

            # Toolbar actions
            c_add, c_del = st.columns([1,1])
            with c_add:
                if st.button("➕ " + T("add_row")):
                    st.session_state.eater_df = pd.concat([
                        pd.DataFrame([{"name": name_label, "factor": 1.0}]),
                        pd.DataFrame(grid_resp["data"]) if isinstance(grid_resp.get("data"), list) else pd.DataFrame(grid_resp["data"])  # keep edits
                    ], ignore_index=True)
            with c_del:
                if st.button("🗑️ " + T("delete_selected")):
                    sel = grid_resp.get("selected_rows", [])
                    if sel:
                        sel_df = pd.DataFrame(sel)
                        current = pd.DataFrame(grid_resp["data"]) if isinstance(grid_resp.get("data"), list) else pd.DataFrame(grid_resp["data"]) 
                        st.session_state.eater_df = current.merge(sel_df.drop_duplicates(), how="outer", indicator=True)
                        st.session_state.eater_df = st.session_state.eater_df[st.session_state.eater_df["_merge"] == "left_only"].drop(columns=["_merge"]).reset_index(drop=True)
            # Persist edits if no toolbar action
            if "eater_df" in st.session_state and grid_resp.get("data") is not None:
                st.session_state.eater_df = pd.DataFrame(grid_resp["data"]) if isinstance(grid_resp.get("data"), list) else pd.DataFrame(grid_resp["data"]) 
        else:
            # If dark mode and AgGrid not available, render a custom editor (fully dark-stylable)
            if st.session_state.theme == "dark":
                st.caption("")
                df = st.session_state.eater_df.reset_index(drop=True).copy()
                new_rows = []
                deleted = set()

                for i, row in df.iterrows():
                    c1, c2, c3 = st.columns([2, 1, 0.6])
                    with c1:
                        name_val = st.text_input(f"{name_label} {i+1}", value=str(row.get("name", "")), key=f"eater_name_{i}")
                    with c2:
                        factor_val = st.number_input(
                            factor_label,
                            min_value=0.0,
                            max_value=10.0,
                            step=0.1,
                            value=float(row.get("factor", 1.0)),
                            key=f"eater_factor_{i}"
                        )
                    with c3:
                        if st.button("🗑️", key=f"del_eater_{i}"):
                            deleted.add(i)
                    if i not in deleted:
                        new_rows.append({"name": name_val, "factor": float(factor_val)})

                c_add, c_sp = st.columns([1, 3])
                with c_add:
                    if st.button("➕ " + T("add_row"), key="add_eater_row"):
                        new_rows.append({"name": name_label, "factor": 1.0})

                # Persist edits
                st.session_state.eater_df = pd.DataFrame(new_rows)
            else:
                # Light mode fallback: Streamlit data_editor is fine here
                st.session_state.eater_df = st.data_editor(
                    st.session_state.eater_df,
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "name": st.column_config.TextColumn(name_label),
                        "factor": st.column_config.NumberColumn(factor_label, min_value=0.0, step=0.1, format="%.2f"),
                    },
                    hide_index=True,
                )

    with st.sidebar.expander("🧪 " + T("recipe"), expanded=False):
        r = st.session_state.recipe
        r.yeast_per_kg = st.number_input(T("yeast_per_kg"), min_value=0.0, max_value=50.0, value=float(r.yeast_per_kg), step=0.5)
        r.salt_per_kg = st.number_input(T("salt_per_kg"), min_value=0.0, max_value=80.0, value=float(r.salt_per_kg), step=0.5)
        r.normal_pizza_g = st.number_input(T("normal_weight"), min_value=100.0, max_value=600.0, value=float(r.normal_pizza_g), step=5.0)
        st.session_state.recipe = r

# ---------- Helpers ----------
def compute_requirements(eaters_selection: dict, hydration_pct: int, gabriel_on: bool, recipe: Recipe):
    """Berechnet Zutaten und Pizza-Anzahl.

    - Bedarf in "Standard‑Pizzen" = Summe(count * factor)
    - Ohne Gabriel: Auf ganze Pizzen aufrunden ⇒ evtl. Reste
    - Mit Gabriel: exakt benötigte Menge ⇒ keine Reste
    - Zutaten linear zur Mehlmenge (Hefe/Salz pro 1 kg Mehl)
    """
    need_equiv_pizzas = sum(count * factor for factor, count in eaters_selection.values())

    # Always make whole pizzas; Gabriel only affects leftovers (he eats them)
    pizzas_to_make = math.ceil(need_equiv_pizzas)

    # Mehl-Basis: 1 kg Mehl ⇒ recipe.pizzas_per_kg Standard‑Pizzen ⇒ pro Pizza 1000/recipe.pizzas_per_kg g Mehl
    flour_per_pizza_g = 1000.0 / recipe.pizzas_per_kg
    total_flour_g = flour_per_pizza_g * pizzas_to_make

    hydration = hydration_pct / 100.0
    total_water_g = total_flour_g * hydration

    total_yeast_g = recipe.yeast_per_kg * (total_flour_g / 1000.0)
    total_salt_g = recipe.salt_per_kg * (total_flour_g / 1000.0)

    leftover_pizzas = 0.0 if gabriel_on else (pizzas_to_make - need_equiv_pizzas)

    total_dough_g = total_flour_g + total_water_g + total_yeast_g + total_salt_g

    return {
        "need_equiv_pizzas": need_equiv_pizzas,
        "pizzas_to_make": pizzas_to_make,
        "leftover_pizzas": leftover_pizzas,
        "flour_g": total_flour_g,
        "water_ml": total_water_g,
        "yeast_g": total_yeast_g,
        "salt_g": total_salt_g,
        "dough_g": total_dough_g,
    }

# ---------- Header ----------
col_title, col_badge = st.columns([0.8, 0.2])
with col_title:
    st.markdown(f"<h1 style='margin:0'>{T('title')}</h1>", unsafe_allow_html=True)
with col_badge:
    st.markdown(f"<div class='badge'>{T('badge')}</div>", unsafe_allow_html=True)

# ---------- Inputs ----------
left, right = st.columns([1, 1])

with left:
    st.subheader(T("settings"))

    # Build dynamic eater counters from eater_df
    eaters = {}
    c1, c2, c3 = st.columns(3)
    cols = [c1, c2, c3]
    for i, row in st.session_state.eater_df.reset_index(drop=True).iterrows():
        col = cols[i % 3]
        with col:
            count = st.number_input(f"{row['name']}", min_value=0, max_value=500, value=0, step=1, key=f"eater_{i}")
            eaters[row['name']] = (float(row['factor']), int(count))

    gabriel_on = st.toggle(T("gabriel"), value=False, help=T("gabriel_help"))

    hydration = st.select_slider(
        T("hydration"),
        options=list(range(50, 101, 5)),
        value=60,
        help="Wasseranteil in % bezogen auf die Mehlmenge.",
    )

with right:
    st.subheader(T("prep_title"))
    st.markdown(f"<div class='panel'>{T('prep_text')}</div>", unsafe_allow_html=True)

st.divider()

# ---------- Berechnung ----------
res = compute_requirements(
    eaters_selection=eaters,
    hydration_pct=hydration,
    gabriel_on=gabriel_on,
    recipe=st.session_state.recipe,
)

# ---------- Ergebnisse ----------
st.subheader(T("result"))

m1, m2, m3, m4 = st.columns(4)

m1.metric(T("need_pizzas"), f"{res['need_equiv_pizzas']:.2f}")
# Always display integer number of pizzas (whole pizzas made)
make_val = f"{int(res['pizzas_to_make'])}"
m2.metric(T("make_pizzas"), make_val)
if gabriel_on:
    m3.metric(T("no_leftovers"), "0.00")
else:
    m3.metric(T("leftovers"), f"{res['leftover_pizzas']:.2f}")
m4.metric(T("hydration_metric"), f"{hydration}%")

st.write("")
i1, i2, i3, i4 = st.columns(4)
i1.metric(T("flour"), f"{res['flour_g']:.0f} g")
i2.metric(T("water"), f"{res['water_ml']:.0f} ml")
i3.metric(T("yeast"), f"{res['yeast_g']:.1f} g")
i4.metric(T("salt"), f"{res['salt_g']:.1f} g")

st.caption(T("teig_hint").format(dough=f"{res['dough_g']:.0f}", std=f"{st.session_state.recipe.normal_pizza_g:.1f}"))

with st.expander(T("details")):
    st.markdown(
        T("details_md").format(
            pizzas_per_kg=st.session_state.recipe.pizzas_per_kg,
            yeast=st.session_state.recipe.yeast_per_kg,
            salt=st.session_state.recipe.salt_per_kg,
        )
    )


st.markdown(f"<div class='small' style='opacity:.8'>{T('note')}</div>", unsafe_allow_html=True)

if _has_ctx():
    if "printed_ok" not in st.session_state:
        print("...App started successfully. Visit locally at: http://localhost:8501")
        st.session_state.printed_ok = True
else:
    print("...App started successfully. Visit locally at: http://localhost:8501")
