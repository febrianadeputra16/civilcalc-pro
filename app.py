# Install: pip install streamlit pandas plotly
# Jalankan: streamlit run app.py
# Tata Bata: Estimator Dinding 1/2 Batu & CMS Admin Panel

import base64
import copy
import html
import json
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def _ikon():
    try:
        from PIL import Image, ImageDraw
        k = 4
        im = Image.new("RGBA", (64 * k, 64 * k), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, 64 * k - 1, 64 * k - 1), radius=14 * k, fill="#c1583c")
        pts = [(0, 0), (64, 0), (64, 20), (46, 20), (46, 64), (18, 64), (18, 20), (0, 20)]
        d.polygon([((x * 0.62 + 12.3) * k, (y * 0.62 + 12.3) * k) for x, y in pts], fill="#fbeee8")
        return im.resize((64, 64), Image.LANCZOS)
    except Exception:
        return "🧱"


st.set_page_config(page_title="Tata Bata", page_icon=_ikon(), layout="wide", initial_sidebar_state="expanded")

def get_secret(key):
    try:
        return str(st.secrets[key])
    except Exception:
        return None


# Atur di Streamlit Cloud: Settings -> Secrets (lihat panduan). Jika kosong, fitur admin nonaktif.
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD")
OWNER_KEY = get_secret("OWNER_KEY")
SAK_KG = 40.0

RATIO_PRESETS = {
    "1:3": {"semen": 400.0, "pasir": 0.55},
    "1:4": {"semen": 325.0, "pasir": 0.60},
    "1:5": {"semen": 275.0, "pasir": 0.65},
    "1:6": {"semen": 230.0, "pasir": 0.70},
}


# ------------------------------------------------------------------ STATE
def default_db():
    return {
        "materials": [
            {"nama": "Bata Merah Standar", "p": 23.0, "b": 11.0, "t": 5.0, "harga": 850.0},
            {"nama": "Bata Merah Press", "p": 22.0, "b": 10.5, "t": 5.5, "harga": 1000.0},
            {"nama": "Bata Ringan 7.5cm", "p": 60.0, "b": 7.5, "t": 20.0, "harga": 9500.0},
            {"nama": "Bata Ringan 10cm", "p": 60.0, "b": 10.0, "t": 20.0, "harga": 12500.0},
            {"nama": "Bata Interlock", "p": 30.0, "b": 14.0, "t": 10.0, "harga": 3500.0},
        ],
        "semen_sak": 70000.0,
        "semen_sak50": 87500.0,
        "air_liter": 20.0,
        "perekat_sak": 80000.0,
        "pasir_m3": 280000.0,
        "mortar": {"ratio": "1:4", "semen_kg_m3": 325.0, "pasir_m3_m3": 0.60, "fas": 0.5},
    }


def init_state():
    if "db" not in st.session_state:
        st.session_state.db = default_db()
    if "admin" not in st.session_state:
        st.session_state.admin = False
    if "ver" not in st.session_state:
        st.session_state.ver = 0


init_state()
db = st.session_state.db
db.setdefault("semen_sak50", 87500.0)
db.setdefault("air_liter", 20.0)
db.setdefault("perekat_sak", 80000.0)
db["mortar"].setdefault("fas", 0.5)

# Fitur admin hanya muncul jika link dibuka dengan ?owner=<OWNER_KEY>
admin_available = bool(OWNER_KEY) and bool(ADMIN_PASSWORD) and st.query_params.get("owner") == OWNER_KEY
is_admin = admin_available and st.session_state.admin


def rp(x):
    return "Rp " + f"{x:,.0f}".replace(",", ".")


def num(x, d=2):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 110 110"><defs><clipPath id="c"><path d="M0 0H64V20H46V64H18V20H0Z"/></clipPath></defs>'
    '<rect width="110" height="110" rx="24" fill="#c1583c"/><g transform="translate(20,20) scale(1.1)">'
    '<path d="M0 0H64V20H46V64H18V20H0Z" fill="#fbeee8"/><g clip-path="url(#c)"><g fill="#f3d9cf">'
    '<rect x="21" y="0" width="22" height="10"/><rect x="32" y="10" width="21.3" height="10"/>'
    '<rect x="18" y="31" width="7" height="11"/><rect x="32" y="42" width="14" height="11"/></g>'
    '<path d="M0 10H64M0 20H64M18 31H46M18 42H46M18 53H46M21 0V10M43 0V10M10.7 10V20M32 10V20M53.3 10V20M32 20V31M25 31V42M39 31V42M32 42V53M25 53V64M39 53V64" fill="none" stroke="#c1583c" stroke-width="1.4"/>'
    '</g></g></svg>'
)
LOGO_URI = "data:image/svg+xml;base64," + base64.b64encode(LOGO_SVG.encode()).decode()


# ------------------------------------------------------------------ CSS
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp, .stMarkdown, button, input, select, textarea { font-family: 'Inter', system-ui, sans-serif !important; }
.stApp {
    background: radial-gradient(circle at 88% 8%, #dcdff3 0%, transparent 38%),
                radial-gradient(circle at 4% 96%, #f2e7e3 0%, transparent 38%),
                linear-gradient(135deg, #e9eff3 0%, #d3e5ee 100%);
}
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stAppDeployButton"], [data-testid="stDeployButton"], [data-testid="stMainMenu"], [data-testid="stToolbarActions"], #MainMenu, footer { display: none !important; visibility: hidden !important; }
[data-testid="stToolbar"] { visibility: hidden !important; }
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] { display: flex !important; visibility: visible !important; background: #115569; border-radius: 12px; }
[data-testid="stExpandSidebarButton"] *, [data-testid="stSidebarCollapsedControl"] *, [data-testid="collapsedControl"] * { visibility: visible !important; color: #ffffff !important; fill: #ffffff !important; }
.block-container { padding-top: 1.5rem; max-width: 1250px; }

/* ---------- SIDEBAR (menu ala dashboard) ---------- */
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #115569 0%, #0d3d4a 100%); border-right: none; border-radius: 0 28px 28px 0; }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] .stMarkdown p, section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #cfe6ec !important; }
.brand { display: flex; align-items: center; gap: 12px; margin: 4px 0 18px 0; }
.brand-logo { width: 44px; height: 44px; border-radius: 14px; background: linear-gradient(135deg, #34d3a0, #1c8fb5); display: flex; align-items: center; justify-content: center; font-size: 1.4rem; }
.brand-t { color: #ffffff; font-weight: 800; font-size: 1.1rem; line-height: 1.2; }
.brand-s { color: #9cc7d2; font-size: 0.75rem; }
.side-proj { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 14px; padding: 10px 14px; color: #ffffff; font-weight: 600; font-size: 0.9rem; margin-bottom: 14px; }
.side-proj span { display: block; font-size: 0.65rem; letter-spacing: 1px; color: #7fd8c0; font-weight: 700; }
.side-h { color: #ffffff; font-weight: 700; margin: 18px 0 6px 0; }
section[data-testid="stSidebar"] .stButton > button { justify-content: flex-start; text-align: left; border-radius: 16px; border: none; padding: 0.7rem 1rem; font-weight: 600; background: rgba(255,255,255,0.07); color: #d7ebf0; margin-top: 6px; }
section[data-testid="stSidebar"] .stButton > button p { color: inherit !important; }
section[data-testid="stSidebar"] .stButton > button:hover { background: rgba(255,255,255,0.15); color: #ffffff; }
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"], section[data-testid="stSidebar"] button[kind="primary"] { background: #ffffff !important; color: #0d3d4a !important; box-shadow: 0 6px 16px rgba(0,0,0,0.18); }
section[data-testid="stSidebar"] div[data-baseweb="input"], section[data-testid="stSidebar"] div[data-baseweb="base-input"], section[data-testid="stSidebar"] div[data-baseweb="select"] > div { background: #f4fafb !important; border-color: transparent !important; border-radius: 12px !important; }
section[data-testid="stSidebar"] input { color: #0d3d4a !important; -webkit-text-fill-color: #0d3d4a !important; }
section[data-testid="stSidebar"] div[data-baseweb="select"] * { color: #0d3d4a !important; }
section[data-testid="stSidebar"] [data-testid="stNumberInputStepDown"], section[data-testid="stSidebar"] [data-testid="stNumberInputStepUp"] { background: transparent !important; color: #0d3d4a !important; }
section[data-testid="stSidebar"] [data-testid="stSliderThumbValue"], section[data-testid="stSidebar"] [data-testid="stTickBarMin"], section[data-testid="stSidebar"] [data-testid="stTickBarMax"] { color: #7fd8c0 !important; }

/* ---------- HERO, CARD, TAB ---------- */
.hero { background: linear-gradient(135deg, #115569 0%, #0b3a47 100%); border-radius: 22px; padding: 26px 32px; color: #ffffff; margin-bottom: 22px; box-shadow: 0 14px 30px -8px rgba(11,58,71,0.35); border: 1px solid rgba(255,255,255,0.15); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px; }
.hero h1 { margin: 0; font-size: 1.8rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; }
.hero p { margin: 6px 0 0 0; color: #b9dbe3; font-size: 0.95rem; }
.hero-r { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.chip { background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.25); padding: 8px 14px; border-radius: 999px; font-size: 0.82rem; font-weight: 600; color: #ffffff; }
.badge { padding: 8px 16px; border-radius: 999px; font-size: 0.82rem; font-weight: 700; color: #ffffff; }
.badge-user { background: #1c8fb5; }
.badge-admin { background: #d97706; }
.kpi { background: rgba(255,255,255,0.72); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.95); border-radius: 20px; padding: 18px 20px; box-shadow: 0 8px 24px rgba(15,80,100,0.08); height: 100%; }
.kpi .label { font-size: 0.74rem; font-weight: 600; color: #5b7c86; text-transform: uppercase; letter-spacing: 0.6px; }
.kpi .value { font-size: 1.85rem; font-weight: 800; color: #0d3d4a; margin: 6px 0 4px 0; }
.kpi .detail { font-size: 0.8rem; color: #5b7c86; }
.kpi.blue { border-top: 4px solid #1c8fb5; }
.kpi.green { border-top: 4px solid #2fc29b; }
.kpi.amber { border-top: 4px solid #f6c453; }
.kpi.navy { border-top: 4px solid #115569; }
.callout { background: rgba(255,255,255,0.65); border-left: 4px solid #1c8fb5; border-radius: 14px; padding: 14px 18px; color: #0d3d4a; font-size: 0.9rem; margin: 12px 0; }
.total-box { background: linear-gradient(135deg, #115569 0%, #2fc29b 100%); color: #ffffff; border-radius: 20px; padding: 20px 26px; margin-top: 14px; box-shadow: 0 10px 24px rgba(17,85,105,0.25); }
.total-box .t1 { font-size: 0.8rem; font-weight: 600; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.6px; }
.total-box .t2 { font-size: 2rem; font-weight: 800; }
.section-title { font-size: 1.05rem; font-weight: 700; color: #0d3d4a; margin: 18px 0 8px 0; }
.gate { background: rgba(255,255,255,0.75); backdrop-filter: blur(10px); border: 1px solid #ffffff; border-radius: 24px; padding: 28px 30px 8px 30px; text-align: center; box-shadow: 0 12px 30px rgba(15,80,100,0.10); }
.gate h2 { margin: 6px 0 4px 0; color: #0d3d4a; font-weight: 800; }
.gate p { color: #5b7c86; font-size: 0.92rem; }
.gate-ic { font-size: 2.4rem; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; background: rgba(255,255,255,0.55); padding: 6px; border-radius: 16px; }
.stTabs [data-baseweb="tab"] { border-radius: 12px; padding: 8px 16px; font-weight: 600; }
.stTabs [aria-selected="true"] { background: #115569; }
.stTabs [aria-selected="true"] p { color: #ffffff !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
div[data-testid="stMain"] [data-testid^="stBaseButton-primary"] { background: #0b5563; border: none; border-radius: 12px; font-weight: 700; letter-spacing: 0.5px; }
div[data-testid="stMain"] [data-testid^="stBaseButton-primary"]:hover { background: #115569; }
div[data-testid="stDataFrame"] { border-radius: 16px; overflow: hidden; }
.stApp [data-testid^="stBaseButton-primary"], .stApp button[kind="primary"], .stApp button[kind="primaryFormSubmit"] { background: #0b5563 !important; border: none !important; border-radius: 12px !important; color: #ffffff !important; font-weight: 700 !important; }
.gate { border-radius: 24px 24px 0 0; margin-bottom: -1rem; }
div[data-testid="stForm"] { background: rgba(255,255,255,0.75); border: 1px solid #ffffff; border-top: none; border-radius: 0 0 24px 24px; }
:root { color-scheme: light; }
.kpi { height: 158px; padding: 16px 18px !important; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; box-sizing: border-box; }
.kpi .value { font-size: 1.45rem !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin: 4px 0 !important; }
.kpi .label { font-size: 0.68rem !important; letter-spacing: 0.4px !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kpi .detail { font-size: 0.76rem; line-height: 1.35; }
div[data-testid="stMain"] p, div[data-testid="stMain"] label, div[data-testid="stMain"] [data-testid="stWidgetLabel"] p, div[data-testid="stMain"] [data-testid="stCaptionContainer"] { color: #0d3d4a; }
.hero p { color: #d6edf2 !important; }
.kpi .label { color: #1f3b45 !important; font-weight: 700; }
.kpi .detail { color: #2b4650 !important; }
.callout, .callout b { color: #0d3d4a !important; }
.stTabs [data-baseweb="tab"] p { color: #0d3d4a !important; font-weight: 700; }
.stTabs [aria-selected="true"] p { color: #ffffff !important; }
[data-testid="InputInstructions"], [data-testid="stHeaderActionElements"] { display: none !important; }
.hero-brand { display: flex; align-items: center; gap: 18px; }
.hero-logo { width: 72px; height: 72px; border-radius: 18px; flex-shrink: 0; box-shadow: 0 6px 16px rgba(0,0,0,0.25); }
.brand-img { width: 48px; height: 48px; border-radius: 13px; flex-shrink: 0; }
.hero-t { margin: 0; font-size: 1.8rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; }
.gate { padding: 18px 30px 4px 30px; }
.gate-ic { font-size: 4.5rem; line-height: 1.1; }
.gate-t { font-size: 2rem; font-weight: 800; color: #0d3d4a; margin: 4px 0 8px 0; }
@media (max-width: 768px) {
    .block-container { padding: 1rem 0.8rem; }
    .hero { padding: 18px; } .hero-logo { width: 52px; height: 52px; } .hero-t { font-size: 1.3rem; }
    .kpi .value { font-size: 1.4rem; } .gate-ic { font-size: 3.5rem; } .gate-t { font-size: 1.5rem; }
}
</style>
""",
    unsafe_allow_html=True,
)


def kpi(label, value, detail, color):
    return (
        f'<div class="kpi {color}"><div class="label">{label}</div>'
        f'<div class="value">{value}</div><div class="detail">{detail}</div></div>'
    )


def callout(text):
    st.markdown(f'<div class="callout">{text}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ SIDEBAR
def g(x):
    return f"{x:.4f}".rstrip("0").rstrip(".").replace(".", ",")


ver = st.session_state.ver
mat_names = [m["nama"] for m in db["materials"]]
V = st.session_state.setdefault("vals", {})
for _k, _v in {"p": 10.0, "t": 3.0, "buk": 3.0, "spesi": 1.5, "waste": 5, "sak": 40, "fas": 0.5}.items():
    V.setdefault(_k, _v)
if V.get("mat") not in mat_names:
    V["mat"] = mat_names[0]
    st.session_state.pop("w_mat", None)
if st.session_state.get("w_mat") not in (None, *mat_names):
    st.session_state.pop("w_mat", None)
st.session_state.setdefault("page", "home")
proyek = st.session_state.get("proyek", "")
PEREKAT_CM, PEREKAT_KG_M3, PEREKAT_SAK_KG = 0.3, 1700.0, 40.0


def set_page(k):
    # Nilai sudah tersimpan di V; ingatan widget dibersihkan agar halaman berikutnya memuat ulang dari V
    for _w in [w for w in st.session_state if str(w).startswith("w_")]:
        del st.session_state[_w]
    st.session_state.page = k


def price_state():
    m = next(x for x in db["materials"] if x["nama"] == V["mat"])
    kb, ks, kp, km = f"hb_{ver}_{V['mat']}", f"hs{V['sak']}_{ver}", f"hp_{ver}", f"hm_{ver}"
    V.setdefault(kb, float(m["harga"]))
    V.setdefault(ks, float(db["semen_sak"] if V["sak"] == 40 else db["semen_sak50"]))
    V.setdefault(kp, float(db["pasir_m3"]))
    V.setdefault(km, float(db["perekat_sak"]))
    V.setdefault(f"hw_{ver}", float(db["air_liter"]))
    return m, kb, ks, kp, km


def field(sec, kind, key, label, **kw):
    # Widget hanya digambar di halamannya; nilai selalu tersimpan di V
    if proyek and st.session_state.page == sec:
        wk = "w_" + key

        def _sync(wk=wk, key=key):
            V[key] = st.session_state[wk]  # simpan seketika saat pengguna mengubah nilai

        if kind == "sel":
            kw["index"] = kw["options"].index(V[key])
        else:
            kw["value"] = V[key]
        fn = {"num": st.number_input, "sel": st.selectbox, "sld": st.slider}[kind]
        V[key] = fn(label, key=wk, on_change=_sync, **kw)
    return V[key]


with st.sidebar:
    st.markdown(
        f'<div class="brand"><img class="brand-img" src="{LOGO_URI}"><div><div class="brand-t">Tata Bata</div>'
        '<div class="brand-s">Estimator Dinding 1/2 Batu</div></div></div>',
        unsafe_allow_html=True,
    )
    if proyek:
        _nm = st.text_input("PROYEK", value=proyek, key="proyek_input")
        if _nm.strip() and _nm.strip() != proyek:
            st.session_state.proyek = _nm.strip()
            st.rerun()
        for k, ic, lb in (("home", "📊", "Dashboard"), ("geo", "📐", "Geometri Dinding"), ("mat", "🧱", "Spesifikasi Material"), ("hrg", "💰", "Harga Satuan Material"), ("air", "💧", "Pengaturan Air (FAS)")):
            st.button(f"{ic}  {lb}", key=f"nav_{k}", on_click=set_page, args=(k,), use_container_width=True,
                      type="primary" if st.session_state.page == k else "secondary")
    if admin_available:
        st.markdown('<div class="side-h">🔐 Akses Admin (Owner)</div>', unsafe_allow_html=True)
        if st.session_state.admin:
            st.success("Admin Mode aktif")
            if st.button("Keluar dari Admin", use_container_width=True):
                st.session_state.admin = False
                st.rerun()
        else:
            pw = st.text_input("Password", type="password", key="pw_input")
            if st.button("Masuk", use_container_width=True):
                if pw == ADMIN_PASSWORD:
                    st.session_state.admin = True
                    st.rerun()
                else:
                    st.error("Password salah.")

# ------------------------------------------------------------------ CORE ENGINE
mat_pilih = V["mat"]
mat, _kb, _ks, _kp, _km = price_state()
is_ringan, is_merah = "ringan" in mat_pilih.lower(), "merah" in mat_pilih.lower()
sak_kg = float(V["sak"])
panjang_dinding, tinggi_dinding, luas_bukaan, waste = V["p"], V["t"], V["buk"], V["waste"]
tebal_spesi = PEREKAT_CM if is_ringan else V["spesi"]
harga_bata, harga_semen, harga_pasir, harga_perekat = V[_kb], V[_ks], V[_kp], V[_km]
harga_air = V[f"hw_{ver}"]
fas = V["fas"]
p, b, t, s = mat["p"] / 100.0, mat["b"] / 100.0, mat["t"] / 100.0, tebal_spesi / 100.0
luas_gross = panjang_dinding * tinggi_dinding
a_netto = max(0.0, luas_gross - luas_bukaan)
p_ef, t_ef = p + s, t + s
area_unit_ef = p_ef * t_ef
unit_teoritis = a_netto / area_unit_ef
vol_dinding = a_netto * b
vol_unit_murni = unit_teoritis * (p * b * t)


def hitung(net):
    teo = net / area_unit_ef
    vs = max(0.0, net * b - teo * (p * b * t))
    r = {"n": math.ceil(teo * (1 + waste / 100.0)), "vs": vs, "semen_kg": 0.0, "sak": 0, "pasir": 0.0, "per_kg": 0.0, "per_sak": 0, "air": 0.0}
    if is_ringan:
        r["per_kg"] = vs * PEREKAT_KG_M3
        r["per_sak"] = math.ceil(r["per_kg"] / PEREKAT_SAK_KG)
    else:
        r["semen_kg"] = vs * db["mortar"]["semen_kg_m3"]
        r["sak"] = math.ceil(r["semen_kg"] / sak_kg)
        r["pasir"] = round(vs * db["mortar"]["pasir_m3_m3"], 2)
        if is_merah:
            r["air"] = r["semen_kg"] * fas
    return r


R = hitung(a_netto)
n_total, v_spesi, semen_kg, semen_sak, pasir_m3 = R["n"], R["vs"], R["semen_kg"], R["sak"], R["pasir"]
per_kg, per_sak, air_l = R["per_kg"], R["per_sak"], R["air"]
rows = [(f"{mat_pilih} ({g(mat['p'])}×{g(mat['b'])}×{g(mat['t'])} cm)", n_total, "buah", harga_bata, "Bata")]
if is_ringan:
    rows.append(("Mortar Perekat Bata Ringan (sak 40 kg)", per_sak, "sak", harga_perekat, "Mortar Perekat"))
else:
    rows.append((f"Semen Portland (sak {g(sak_kg)} kg)", semen_sak, "sak", harga_semen, "Semen"))
    rows.append(("Pasir Pasang", pasir_m3, "m³", harga_pasir, "Pasir"))
    if is_merah:
        rows.append((f"Air Adukan (FAS {g(fas)})", air_l, "liter", harga_air, "Air"))
rab = pd.DataFrame([{"Uraian Material": r[0], "Volume": r[1], "Satuan": r[2], "Harga Satuan (Rp)": r[3], "Subtotal (Rp)": r[1] * r[3], "Ringkas": r[4]} for r in rows])
biaya_total = float(rab["Subtotal (Rp)"].sum())

# ------------------------------------------------------------------ HERO
chip = f'<span class="chip">📁 {html.escape(proyek)}</span>' if proyek else ''
badge = (
    '<span class="badge badge-admin">🔓 Admin Mode Active</span>'
    if is_admin
    else '<span class="badge badge-user">👤 User Mode</span>'
)
st.markdown(
    f'<div class="hero"><div class="hero-brand"><img class="hero-logo" src="{LOGO_URI}"><div><div class="hero-t">Tata Bata</div>'
    f'<p>Hitung Volume Material dan RAB Secara Presisi</p></div></div>'
    f'<div class="hero-r">{chip}</div></div>',
    unsafe_allow_html=True,
)

if not proyek:
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown(
            '<div class="gate"><div class="gate-ic">🏗️</div><div class="gate-t">Mulai Proyek Baru</div></div>'
            '<style>[data-testid="stAppViewContainer"], [data-testid="stMain"] { overflow: hidden !important; }'
            '.block-container { padding-top: 1rem !important; padding-bottom: 0 !important; }'
            '.hero { margin-bottom: 12px; padding: 18px 28px; }</style>',
            unsafe_allow_html=True,
        )
        with st.form("form_proyek"):
            nm = st.text_input("Nama proyek", value=st.session_state.get("proyek_last", ""),
                               placeholder="contoh: Rumah Pak Budi - Dinding Lantai 1")
            if st.form_submit_button("MULAI HITUNG", type="primary", use_container_width=True):
                if nm.strip():
                    st.session_state.proyek = nm.strip()
                    st.rerun()
                else:
                    st.error("Nama proyek wajib diisi.")
    st.stop()

if st.session_state.page != "home":
    _pg = st.session_state.page
    _titles = {"geo": "📐 Geometri Dinding", "mat": "🧱 Spesifikasi Material", "hrg": "💰 Harga Satuan Material", "air": "💧 Pengaturan Air (FAS)"}
    st.markdown(f'<div class="section-title">{_titles[_pg]}</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if _pg == "geo":
        with c1:
            field("geo", "num", "p", "Panjang dinding (m)", min_value=0.1, step=0.5)
        with c2:
            field("geo", "num", "t", "Tinggi dinding (m)", min_value=0.1, step=0.1)
        with c3:
            field("geo", "num", "buk", "Luas bukaan pintu/jendela (m²)", min_value=0.0, step=0.5)
    elif _pg == "mat":
        with c1:
            field("mat", "sel", "mat", "Jenis material dinding", options=mat_names)
        with c2:
            if "ringan" in V["mat"].lower():
                st.info("Bata ringan memakai mortar perekat tipis 0,3 cm, jadi tebal spesi tidak dipakai.")
            else:
                field("mat", "sld", "spesi", "Tebal spesi (cm)", min_value=0.5, max_value=3.0, step=0.1)
        with c3:
            field("mat", "sld", "waste", "Waste / susut bata (%)", min_value=0, max_value=30, step=1)
    elif _pg == "air":
        with c1:
            if "merah" in V["mat"].lower():
                field("air", "sld", "fas", "Faktor air-semen (FAS)", min_value=0.45, max_value=0.60, step=0.01)
                st.caption("Default 0,50. Air adukan (liter) = kebutuhan semen (kg) × FAS.")
            else:
                st.info("Air hanya dihitung untuk bata merah standar dan bata merah press.")
    else:
        with c1:
            field("hrg", "sel", "sak", "Ukuran sak semen", options=[40, 50], format_func=lambda x: f"{x} kg")
        _, kb_, ks_, kp_, km_ = price_state()
        with c2:
            field("hrg", "num", kb_, "Harga bata (Rp/buah)", min_value=0.0, step=50.0, format="%.0f")
        with c3:
            field("hrg", "num", ks_, f"Harga semen (Rp/sak {V['sak']} kg)", min_value=0.0, step=1000.0, format="%.0f")
        d1, d2, d3 = st.columns(3)
        with d1:
            field("hrg", "num", kp_, "Harga pasir (Rp/m³)", min_value=0.0, step=5000.0, format="%.0f")
        with d2:
            field("hrg", "num", km_, "Harga mortar perekat (Rp/sak 40 kg)", min_value=0.0, step=1000.0, format="%.0f")
        with d3:
            if "merah" in V["mat"].lower():
                field("hrg", "num", f"hw_{ver}", "Harga air (Rp/liter)", min_value=0.0, step=5.0, format="%.0f")
        st.caption("Harga bata mengikuti material yang dipilih. Mortar perekat hanya untuk bata ringan, harga air hanya untuk bata merah.")
    st.button("📊 Lihat Hasil di Dashboard", on_click=set_page, args=("home",), type="primary")
    st.stop()

if is_admin:
    tab1, tab2, tab_sim, tab3, tab4 = st.tabs(
        ["📊 Dashboard Metrik Utama", "📈 Analisis Cost & RAB", "🎬 Simulasi Pemasangan", "⚙️ Panel Pengaturan Admin", "📄 Formulasi Teknik Sipil & Ekspor"]
    )
else:
    # Pengunjung biasa: tab admin tidak dibuat sama sekali
    tab1, tab2, tab_sim, tab4 = st.tabs(
        ["📊 Dashboard Metrik Utama", "📈 Analisis Cost & RAB", "🎬 Simulasi Pemasangan", "📄 Formulasi Teknik Sipil & Ekspor"]
    )
    tab3 = st.container()

# ------------------------------------------------------------------ TAB 1
with tab1:
    cards = [
        kpi("Luas Netto Dinding", f"{num(a_netto)} m²", f"Gross {num(luas_gross)} m² − bukaan {num(luas_bukaan)} m²", "blue"),
        kpi("Kebutuhan Unit", f"{num(n_total, 0)} buah", f"Teoritis {num(unit_teoritis, 1)} + waste {num(waste, 0)}%", "amber"),
    ]
    if is_ringan:
        cards.append(kpi("Mortar Perekat", f"{num(per_sak, 0)} sak", f"{num(per_kg, 1)} kg · sak {g(PEREKAT_SAK_KG)} kg", "navy"))
    else:
        cards.append(kpi("Kebutuhan Semen", f"{num(semen_sak, 0)} sak", f"{num(semen_kg, 1)} kg · sak {g(sak_kg)} kg · rasio {db['mortar']['ratio']}", "navy"))
        cards.append(kpi("Kebutuhan Pasir", f"{num(pasir_m3)} m³", f"{num(db['mortar']['pasir_m3_m3'])} m³ per m³ spesi", "green"))
    if is_merah:
        cards.append(kpi("Kebutuhan Air", f"{num(air_l, 0)} liter", f"{num(air_l / 1000)} m³ · FAS {g(fas)}", "blue"))
    for col, card in zip(st.columns(len(cards)), cards):
        col.markdown(card, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Ringkasan Spesifikasi Teknis Pasangan 1/2 Batu</div>', unsafe_allow_html=True)
    d1, d2, d3, d4 = st.columns(4)
    d1.markdown(kpi("Volume Spesi" if not is_ringan else "Volume Perekat", f"{num(v_spesi, 3)} m³", f"Dinding {num(vol_dinding, 3)} m³ − bata {num(vol_unit_murni, 3)} m³", "blue"), unsafe_allow_html=True)
    d2.markdown(kpi("Tebal Dinding Murni", f"{g(mat['b'])} cm", "Lebar bata (pasangan 1/2 batu)", "navy"), unsafe_allow_html=True)
    d3.markdown(kpi("Dimensi Efektif Unit", f"{num(p_ef * 100, 1)} × {num(t_ef * 100, 1)} cm", f"Ukuran bata + {'perekat' if is_ringan else 'spesi'} {g(tebal_spesi)} cm", "amber"), unsafe_allow_html=True)
    d4.markdown(kpi("Luas Efektif / Unit", f"{num(area_unit_ef * 10000, 1)} cm²", f"≈ {num(1 / area_unit_ef, 1)} unit per m²", "green"), unsafe_allow_html=True)
    callout(
        f"<b>Catatan:</b> bata <b>{mat_pilih}</b>"
        + (" dipasang dengan mortar perekat tipis, tanpa semen-pasir." if is_ringan else f", campuran spesi <b>{db['mortar']['ratio']}</b>.")
        + (" Kebutuhan air adalah air adukan saja (belum termasuk air untuk membasahi bata)." if is_merah else "")
        + " Hasil berupa estimasi awal; sesuaikan dengan kondisi lapangan."
    )

# ------------------------------------------------------------------ TAB 2
with tab2:
    st.markdown(f'<div class="section-title">Rekapitulasi RAB Material &mdash; {html.escape(proyek)}</div>', unsafe_allow_html=True)
    tampil = rab.drop(columns="Ringkas").copy()
    tampil["Volume"] = [num(v, 2 if u == "m³" else 0) for v, u in zip(rab["Volume"], rab["Satuan"])]
    tampil["Harga Satuan (Rp)"] = [rp(h) for h in rab["Harga Satuan (Rp)"]]
    tampil["Subtotal (Rp)"] = [rp(h) for h in rab["Subtotal (Rp)"]]
    st.dataframe(tampil, use_container_width=True, hide_index=True)

    LAY = dict(font_family="Inter", font_color="#0d3d4a", separators=",.", paper_bgcolor="rgba(0,0,0,0)",
               plot_bgcolor="rgba(255,255,255,0.55)", margin=dict(t=50, b=10, l=10, r=10))
    PAL = ["#115569", "#f6c453", "#2fc29b", "#1c8fb5"]
    bi = rab[rab["Subtotal (Rp)"] > 0]
    col_a, col_b = st.columns([3, 2])
    with col_a:
        if biaya_total > 0:
            fig = px.pie(names=bi["Ringkas"], values=bi["Subtotal (Rp)"], hole=0.55, color_discrete_sequence=PAL, title="Proporsi Alokasi Biaya Material")
            fig.update_traces(textinfo="percent+label", hovertemplate="%{label}: Rp %{value:,.0f}<extra></extra>")
            fig.update_layout(legend=dict(orientation="h", y=-0.05), **LAY)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Masukkan dimensi dinding untuk melihat grafik biaya.")
    with col_b:
        st.markdown(f'<div class="total-box"><div class="t1">Total Biaya Material Dinding</div><div class="t2">{rp(biaya_total)}</div></div>', unsafe_allow_html=True)
        per_m2 = biaya_total / a_netto if a_netto > 0 else 0
        st.markdown(kpi("Biaya Material per m²", rp(per_m2), "Total biaya ÷ luas netto dinding", "blue"), unsafe_allow_html=True)

    if biaya_total > 0:
        fb = px.bar(x=bi["Ringkas"], y=bi["Subtotal (Rp)"], color=bi["Ringkas"], color_discrete_sequence=PAL, text_auto=",.0f",
                    title="Diagram Batang: Biaya per Komponen", labels={"x": "", "y": "Rupiah"})
        fb.update_layout(showlegend=False, **LAY)
        st.plotly_chart(fb, use_container_width=True)

        items = [("Bata", "n", "buah")]
        items += [("Mortar Perekat", "per_sak", "sak")] if is_ringan else [("Semen", "sak", "sak"), ("Pasir", "pasir", "m³")]
        items += [("Air", "air", "liter")] if is_merah else []
        xs = [round(a_netto * f / 10, 2) for f in range(1, 21)]
        hs = [hitung(x) for x in xs]
        st.markdown('<div class="section-title">Diagram Garis: Kebutuhan Material vs Luas Dinding</div>', unsafe_allow_html=True)
        fl = go.Figure()
        for i, (nm_, key, unit) in enumerate(items):
            pts = [(x, h[key]) for x, h in zip(xs, hs) if h[key] > 0]
            if pts:
                fl.add_trace(go.Scatter(x=[q[0] for q in pts], y=[q[1] for q in pts], mode="lines+markers", name=f"{nm_} ({unit})",
                                        line=dict(color=PAL[i % 4], width=3),
                                        hovertemplate=f"{nm_}: %{{y:,.2f}} {unit}<br>Luas: %{{x:,.1f}} m²<extra></extra>"))
        fl.add_vline(x=a_netto, line_dash="dash", line_color="#d97706", annotation_text="Saat ini")
        fl.update_layout(yaxis_type="log", yaxis_title="Jumlah (satuan sesuai legenda)", xaxis_title="Luas netto dinding (m²)",
                         legend=dict(orientation="h", y=-0.25), **LAY)
        st.plotly_chart(fl, use_container_width=True)
        st.caption("Skala vertikal logaritmik dipakai agar material dengan satuan berbeda bisa tampil dalam satu grafik.")

# ------------------------------------------------------------------ SIMULASI
SIM_HTML = r'''
<div style="font-family:Inter,system-ui,sans-serif;color:#0d3d4a">
<canvas id="cv" style="display:block;margin:0 auto;border-radius:16px;background:linear-gradient(#dff0f7,#f4fafc)"></canvas>
<div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;gap:10px;flex-wrap:wrap"><b id="tx"></b><span><button onclick="play()">▶ Mulai</button> <button onclick="reset()">↺ Ulang</button></span></div>
<div id="lg" style="font-size:14px;font-weight:600;color:#2b4650;margin-top:6px"></div></div>
<style>button{background:#0b5563;color:#fff;border:0;border-radius:10px;padding:8px 14px;font-weight:600;cursor:pointer}</style>
<script>
const C=__CFG__,cv=document.getElementById("cv"),x=cv.getContext("2d");
const L=C.L,H=C.H,rise=Math.min(2.2,Math.max(0.8,L*0.15)),Dp=0.7,B=0.15,M=0.9;
const Wm=L+2*M,Hm=0.25+rise+B+H+B+Dp+0.1;
let S,X0,GY,WB,WT;
function layout(){const w=Math.max(280,Math.min(1100,(document.documentElement.clientWidth||innerWidth)-8));
 S=Math.min(w/Wm,540/Hm);cv.width=Math.round(Wm*S);cv.height=Math.round(Hm*S);
 X0=M*S;GY=(0.25+rise+B+H+B)*S;WB=GY-B*S;WT=WB-H*S;}
layout();
const pe=C.p+C.s,te=C.t+C.s,rows=Math.ceil(H/te),BR=[];
C.ops.forEach(o=>{const y0=Math.floor(o.y/te+1e-6)*te,y1=Math.round((o.y+o.h)/te)*te;o.y=y0;o.h=Math.max(te,y1-y0);});
for(let r=0;r<rows;r++){const y=r*te,off=(r%2)?pe/2:0;
 for(let c=-1;c*pe+off<L;c++){const a=Math.max(0,c*pe+off),e=Math.min(L,c*pe+off+C.p),h=Math.min(C.t,H-y);
  if(e-a<0.02||h<0.01)continue;
  let segs=[[a,e]];
  C.ops.forEach(o=>{if(y<o.y+o.h-1e-6&&y+h>o.y+1e-6){const nx=[];
   segs.forEach(s=>{if(s[1]<=o.x||s[0]>=o.x+o.w){nx.push(s);}else{if(s[0]<o.x)nx.push([s[0],o.x]);if(s[1]>o.x+o.w)nx.push([o.x+o.w,s[1]]);}});segs=nx;}});
  segs.forEach(s=>{if(s[1]-s[0]>=0.015)BR.push([s[0],y,s[1]-s[0],h]);});}}
const m=Math.max(2,Math.round(L/3.5)+1),KC=[];
for(let i=0;i<m;i++){let cx=i*(L-0.15)/(m-1);const o=C.ops.find(o=>cx<o.x+o.w&&cx+0.15>o.x);if(o)cx=(o.x-0.2>=0)?o.x-0.2:o.x+o.w+0.05;KC.push(cx);}
const R=(c,px,py,w,h)=>{x.fillStyle=c;x.fillRect(px,py,w,h);};
const cl=(t,a,d)=>Math.min(1,Math.max(0,(t-a)/d));
let t=0,tm=null;
function draw(t){
 x.clearRect(0,0,cv.width,cv.height);
 R("#cdbf9f",0,GY,cv.width,cv.height-GY);R("#7fb069",0,GY-2,cv.width,3);
 x.save();x.beginPath();x.rect(0,GY,cv.width,Dp*S*cl(t,0,15));x.clip();x.fillStyle="#8d8f86";x.beginPath();
 x.moveTo(X0-0.25*S,GY);x.lineTo(X0+(L+0.25)*S,GY);x.lineTo(X0+(L+0.45)*S,GY+Dp*S);x.lineTo(X0-0.45*S,GY+Dp*S);x.closePath();x.fill();x.restore();
 R("#98a4aa",X0,GY-B*S,L*S*cl(t,15,15),B*S);
 const n=Math.floor(BR.length*cl(t,55,120)),g=C.s*S;
 for(let i=0;i<n;i++){const b=BR[i],bx=X0+b[0]*S,by=WB-(b[1]+b[3])*S;R("#c9d3d7",bx-g/2,by-g/2,b[2]*S+g,b[3]*S+g);R(C.color,bx,by,b[2]*S,b[3]*S);}
 const p3=cl(t,30,25);KC.forEach(cx=>R("#7f8b91",X0+cx*S,WB-H*S*p3,0.15*S,H*S*p3));
 if(t>=150)C.ops.forEach(o=>{const ox=X0+o.x*S,oy=WB-(o.y+o.h)*S,w=o.w*S,h=o.h*S;
  if(o.d){R("#8b5e3c",ox,oy,w,h);R("#6f4a2e",ox+w*0.1,oy+h*0.08,w*0.8,h*0.38);R("#6f4a2e",ox+w*0.1,oy+h*0.52,w*0.8,h*0.4);}
  else{R("#e9eef0",ox-2,oy-2,w+4,h+4);R("#bfe3f2",ox,oy,w,h);R("#e9eef0",ox+w/2-1,oy,2,h);R("#e9eef0",ox,oy+h/2-1,w,2);}});
 R("#98a4aa",X0-0.05*S,WT-B*S,(L+0.1)*S*cl(t,175,10),B*S);
 const p6=cl(t,185,30),nr=Math.max(4,Math.ceil(rise/0.22)),rh=rise*S/nr,base=WT-B*S,hw=(L/2+0.45)*S,cm=X0+L*S/2;
 for(let i=0;i<nr*p6;i++){const ya=base-i*rh,yb=ya-rh,wa=hw*(1-i/nr),wb=hw*(1-(i+1)/nr);
  x.fillStyle=i%2?"#b5532f":"#a64a29";x.beginPath();x.moveTo(cm-wa,ya);x.lineTo(cm+wa,ya);x.lineTo(cm+wb,yb);x.lineTo(cm-wb,yb);x.closePath();x.fill();x.strokeStyle="#7a2f17";x.lineWidth=1;x.stroke();}
 document.getElementById("tx").textContent=t<15?"Memasang pondasi batu kali":t<30?"Mengecor sloof":t<55?"Mendirikan kolom":t<175?"Memasang bata ±"+Math.round(n/BR.length*C.N)+" / "+C.N+" buah":t<185?"Mengecor ring balok":t<215?"Memasang atap genteng":"Selesai ✔";
}
function reset(){clearInterval(tm);t=0;draw(0);}
function play(){reset();tm=setInterval(()=>{t++;draw(t);if(t>=220)clearInterval(tm);},45);}
document.getElementById("lg").textContent=C.info;
addEventListener("resize",()=>{layout();draw(t);});
[150,700].forEach(ms=>setTimeout(()=>{layout();draw(t);},ms));
play();
</script>'''

with tab_sim:
    st.markdown('<div class="section-title">Simulasi Pemasangan Dinding</div>', unsafe_allow_html=True)
    _ops, _rest = [], luas_bukaan
    if _rest >= 1.9:
        _hd = max(0.5, min(2.1, tinggi_dinding - 0.2))
        _ops.append({"d": 1, "w": 0.9, "h": _hd, "y": 0.0})
        _rest -= 0.9 * _hd
    if _rest > 0.25:
        _nw = max(1, math.ceil(_rest / 1.5))
        _ops += [{"d": 0, "w": _rest / _nw, "h": 1.0, "y": max(0.1, min(0.9, tinggi_dinding - 1.2))} for _ in range(_nw)]
    _sw = sum(o["w"] for o in _ops)
    if _ops and _sw > 0.8 * panjang_dinding:
        _f = 0.8 * panjang_dinding / _sw
        for o in _ops:
            o["w"] *= _f
            o["h"] = min(max(0.5, tinggi_dinding - 0.3), o["h"] / _f)
            o["y"] = min(o["y"], max(0.0, tinggi_dinding - o["h"] - 0.1))
    for _i, o in enumerate(_ops):
        _cx = (_i + 0.5) * panjang_dinding / len(_ops)
        o["x"] = max(0.3, min(panjang_dinding - o["w"] - 0.3, _cx - o["w"] / 2))
        for _k in ("x", "y", "w", "h"):
            o[_k] = round(o[_k], 3)
    _nd, _nj = sum(1 for o in _ops if o["d"]), sum(1 for o in _ops if not o["d"])
    _bk = "Tanpa bukaan." if not _ops else "Bukaan: " + " dan ".join(x for x in (f"{_nd} pintu" if _nd else "", f"{_nj} jendela" if _nj else "") if x) + "."
    _cfg = {
        "L": panjang_dinding, "H": tinggi_dinding, "p": p, "t": t, "s": s,
        "color": "#cfd8dc" if is_ringan else "#c1583c", "N": int(n_total), "ops": _ops,
        "info": f"Panjang dinding {g(panjang_dinding)} m · Tinggi dinding {g(tinggi_dinding)} m · Luas bukaan {g(luas_bukaan)} m². " + _bk + " Posisi dan ukuran bukaan bersifat ilustrasi.",
    }
    st.components.v1.html(SIM_HTML.replace("__CFG__", json.dumps(_cfg)), height=700)
    callout("Ukuran dinding dan jumlah bata pada simulasi mengikuti hitungan aplikasi. Pola bata <b>running bond</b>, bata di sekitar bukaan dan ujung dinding dipotong sesuai kebutuhan.")

# ------------------------------------------------------------------ TAB 3
with tab3:
    if not is_admin:
        pass
    else:
        callout("Perubahan di panel ini tersimpan di <b>session state</b> dan langsung memperbarui seluruh kalkulasi aplikasi.")

        # --- Form harga default
        st.markdown('<div class="section-title">💰 Edit Harga Satuan Default</div>', unsafe_allow_html=True)
        with st.form("form_harga"):
            f1, f2 = st.columns(2)
            new_semen = f1.number_input("Harga semen default (Rp/sak 40kg)", min_value=0.0, value=float(db["semen_sak"]), step=1000.0, format="%.0f")
            new_pasir = f2.number_input("Harga pasir default (Rp/m³)", min_value=0.0, value=float(db["pasir_m3"]), step=5000.0, format="%.0f")
            st.caption("Harga bata diatur per jenis material pada tabel preset di bawah.")
            if st.form_submit_button("💾 Simpan Harga Default", type="primary"):
                db["semen_sak"] = float(new_semen)
                db["pasir_m3"] = float(new_pasir)
                st.session_state.ver += 1
                st.rerun()

        with st.form("form_extra"):
            e1, e2, e3 = st.columns(3)
            n50 = e1.number_input("Harga semen sak 50 kg (Rp)", min_value=0.0, value=float(db["semen_sak50"]), step=1000.0, format="%.0f")
            nper = e2.number_input("Harga mortar perekat sak 40 kg (Rp)", min_value=0.0, value=float(db["perekat_sak"]), step=1000.0, format="%.0f")
            nair = e3.number_input("Harga air default (Rp/liter)", min_value=0.0, value=float(db["air_liter"]), step=5.0, format="%.0f")
            if st.form_submit_button("💾 Simpan Harga & Parameter Tambahan", type="primary"):
                db["semen_sak50"], db["perekat_sak"], db["air_liter"] = float(n50), float(nper), float(nair)
                st.session_state.ver += 1
                st.rerun()

        # --- Preset material (edit tabel)
        st.markdown('<div class="section-title">🧱 Edit Preset Material Dinding</div>', unsafe_allow_html=True)
        st.caption("Edit sel langsung, tambah baris di bagian bawah tabel, atau hapus baris. Dimensi dalam cm.")
        df_mat = pd.DataFrame(db["materials"]).rename(
            columns={"nama": "Nama Material", "p": "Panjang (cm)", "b": "Lebar (cm)", "t": "Tinggi (cm)", "harga": "Harga (Rp/buah)"}
        )
        edited = st.data_editor(df_mat, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"editor_{ver}")
        if st.button("💾 Simpan Perubahan Tabel Material", type="primary"):
            clean = edited.dropna(subset=["Nama Material"]).copy()
            clean["Nama Material"] = clean["Nama Material"].astype(str).str.strip()
            clean = clean[clean["Nama Material"] != ""]
            num_cols = ["Panjang (cm)", "Lebar (cm)", "Tinggi (cm)", "Harga (Rp/buah)"]
            problem = None
            if clean.empty:
                problem = "Minimal harus ada satu material."
            elif clean["Nama Material"].duplicated().any():
                problem = "Nama material tidak boleh kembar."
            elif clean[num_cols].isna().any().any():
                problem = "Semua kolom angka harus terisi."
            elif (clean[["Panjang (cm)", "Lebar (cm)", "Tinggi (cm)"]] <= 0).any().any() or (clean["Harga (Rp/buah)"] < 0).any():
                problem = "Dimensi harus > 0 dan harga tidak boleh negatif."
            if problem:
                st.error(problem)
            else:
                db["materials"] = [
                    {"nama": r["Nama Material"], "p": float(r["Panjang (cm)"]), "b": float(r["Lebar (cm)"]),
                     "t": float(r["Tinggi (cm)"]), "harga": float(r["Harga (Rp/buah)"])}
                    for _, r in clean.iterrows()
                ]
                st.session_state.ver += 1
                st.success("Preset material diperbarui.")
                st.rerun()

        with st.expander("➕ Tambah Jenis Material Baru (form cepat)"):
            with st.form("form_tambah", clear_on_submit=True):
                n1, n2 = st.columns(2)
                nm = n1.text_input("Nama material", placeholder="contoh: Bata Interlock Jumbo")
                hg = n2.number_input("Harga (Rp/buah)", min_value=0.0, value=1000.0, step=50.0, format="%.0f")
                z1, z2, z3 = st.columns(3)
                np_ = z1.number_input("Panjang (cm)", min_value=0.1, value=23.0, step=0.5)
                nb_ = z2.number_input("Lebar (cm)", min_value=0.1, value=11.0, step=0.5)
                nt_ = z3.number_input("Tinggi (cm)", min_value=0.1, value=5.0, step=0.5)
                if st.form_submit_button("Tambahkan Material"):
                    nm = nm.strip()
                    if not nm:
                        st.error("Nama material wajib diisi.")
                    elif nm in [m["nama"] for m in db["materials"]]:
                        st.error("Nama material sudah ada.")
                    else:
                        db["materials"].append({"nama": nm, "p": float(np_), "b": float(nb_), "t": float(nt_), "harga": float(hg)})
                        st.session_state.ver += 1
                        st.rerun()

        # --- Parameter mortar
        st.markdown('<div class="section-title">🧪 Edit Parameter Campuran Spesi / Mortar</div>', unsafe_allow_html=True)
        with st.form("form_mortar"):
            opsi = list(RATIO_PRESETS.keys()) + ["Kustom"]
            cur = db["mortar"]["ratio"]
            idx = opsi.index(cur) if cur in opsi else len(opsi) - 1
            m1, m2, m3 = st.columns(3)
            ratio_sel = m1.selectbox("Rasio semen : pasir", opsi, index=idx,
                                     help="Pilih preset (nilai di bawah diabaikan) atau 'Kustom' untuk memakai nilai manual.")
            semen_in = m2.number_input("Semen (kg per m³ spesi)", min_value=1.0, value=float(db["mortar"]["semen_kg_m3"]), step=5.0)
            pasir_in = m3.number_input("Pasir (m³ per m³ spesi)", min_value=0.01, value=float(db["mortar"]["pasir_m3_m3"]), step=0.01)
            st.caption("Nilai preset adalah estimasi umum (1:4 = 325 kg semen & 0,60 m³ pasir). Sesuaikan dengan standar proyek Anda.")
            if st.form_submit_button("💾 Simpan Parameter Mortar", type="primary"):
                if ratio_sel == "Kustom":
                    db["mortar"] = {"ratio": "Kustom", "semen_kg_m3": float(semen_in), "pasir_m3_m3": float(pasir_in)}
                else:
                    pr = RATIO_PRESETS[ratio_sel]
                    db["mortar"] = {"ratio": ratio_sel, "semen_kg_m3": pr["semen"], "pasir_m3_m3": pr["pasir"]}
                st.session_state.ver += 1
                st.rerun()

        # --- Reset
        st.markdown('<div class="section-title">♻️ Reset Data</div>', unsafe_allow_html=True)
        if st.button("🔄 Reset ke Default SNI"):
            st.session_state.db = default_db()
            st.session_state.ver += 1
            st.rerun()

# ------------------------------------------------------------------ TAB 4
with tab4:
    st.markdown('<div class="section-title">Formulasi Rekayasa Sipil</div>', unsafe_allow_html=True)
    st.markdown("**1. Luas netto dinding**")
    st.latex(r"A_{netto} = \max\left(0,\; P_{dinding} \times T_{dinding} - A_{bukaan}\right)")
    st.markdown("**2. Total unit bata (termasuk waste)**")
    st.latex(r"N_{total} = \left\lceil \frac{A_{netto}}{(p+s)(t+s)} \times \left(1+\frac{W}{100}\right) \right\rceil")
    st.markdown("**3. Volume spesi / mortar**")
    st.latex(r"V_{spesi} = \max\left(0,\; A_{netto}\cdot b \;-\; \frac{A_{netto}}{(p+s)(t+s)}\,(p\cdot b\cdot t)\right)")
    st.markdown("**4. Semen dan pasir (bata merah, interlock)**")
    st.latex(r"Semen_{kg} = V_{spesi} \times K_{semen}, \qquad Semen_{sak} = \left\lceil \frac{Semen_{kg}}{" + g(sak_kg) + r"} \right\rceil")
    st.latex(r"Pasir_{m^3} = \mathrm{round}\left(V_{spesi} \times K_{pasir},\; 2\right)")
    st.markdown("**5. Mortar perekat (bata ringan)**")
    st.latex(r"Perekat_{kg} = V_{perekat} \times 1700, \qquad Perekat_{sak} = \left\lceil \frac{Perekat_{kg}}{40} \right\rceil")
    st.markdown("**6. Air adukan (bata merah standar dan press)**")
    st.latex(r"Air_{liter} = Semen_{kg} \times FAS")
    callout("Keterangan: <b>p, b, t</b> = panjang, lebar, tinggi bata (m); <b>s</b> = tebal spesi atau perekat (m); <b>W</b> = waste (%); <b>K</b> = kebutuhan material per m³ spesi.")

    st.markdown('<div class="section-title">Ekspor Laporan ke Excel</div>', unsafe_allow_html=True)
    params = [("Nama proyek", proyek, ""), ("Material dinding", mat_pilih, ""),
              ("Dimensi bata p × b × t", f"{g(mat['p'])} × {g(mat['b'])} × {g(mat['t'])}", "cm"),
              ("Panjang dinding", panjang_dinding, "m"), ("Tinggi dinding", tinggi_dinding, "m"), ("Luas gross", luas_gross, "m²"),
              ("Luas bukaan", luas_bukaan, "m²"), ("Luas netto", a_netto, "m²"),
              ("Tebal perekat" if is_ringan else "Tebal spesi", tebal_spesi, "cm"), ("Waste bata", waste, "%"),
              ("Volume spesi/perekat", v_spesi, "m³")]
    if is_ringan:
        params.append(("Kebutuhan mortar perekat", per_kg, "kg"))
    else:
        params += [("Rasio campuran", db["mortar"]["ratio"], ""), ("Ukuran sak semen", sak_kg, "kg"), ("Kebutuhan semen", semen_kg, "kg")]
    if is_merah:
        params.append(("Kebutuhan air", air_l, "liter"))
    df_par = pd.DataFrame(params, columns=["Parameter", "Nilai", "Satuan"])
    df_rab = rab.drop(columns="Ringkas")
    st.dataframe(df_par.assign(Nilai=[num(v, 2) if isinstance(v, (int, float)) else v for v in df_par["Nilai"]]), use_container_width=True, hide_index=True)

    def buat_xlsx():
        from io import BytesIO
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.worksheet.table import Table, TableStyleInfo
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as xw:
            df_par.to_excel(xw, sheet_name="Ringkasan", index=False, startrow=3)
            df_rab.to_excel(xw, sheet_name="RAB", index=False, startrow=3)
            thin = Side(style="thin", color="B8C4C9")
            for ws, title, widths in ((xw.sheets["Ringkasan"], "RINGKASAN PROYEK", (30, 30, 12)), (xw.sheets["RAB"], "RENCANA ANGGARAN BIAYA MATERIAL", (46, 14, 10, 20, 22))):
                ws["A1"] = f"{title} - {proyek}"
                ws["A1"].font = Font(bold=True, size=14, color="115569")
                ws["A2"] = "Tata Bata"
                ws["A2"].font = Font(italic=True, color="5B7C86")
                last = ws.max_row
                ncol = len(widths)
                for c, w in enumerate(widths, 1):
                    ws.column_dimensions[chr(64 + c)].width = w
                    h = ws.cell(row=4, column=c)
                    h.font = Font(bold=True, color="FFFFFF")
                    h.fill = PatternFill("solid", fgColor="115569")
                    h.alignment = Alignment(horizontal="center", vertical="center")
                for r in range(4, last + 1):
                    for c in range(1, ncol + 1):
                        ws.cell(row=r, column=c).border = Border(top=thin, bottom=thin, left=thin, right=thin)
                tb = Table(displayName="T" + ws.title, ref=f"A4:{chr(64 + ncol)}{last}")
                tb.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=True)
                ws.add_table(tb)
                if ws.title == "RAB":
                    for r in range(5, last + 1):
                        ws.cell(row=r, column=2).number_format = "#,##0.00"
                        ws.cell(row=r, column=4).number_format = '"Rp" #,##0'
                        ws.cell(row=r, column=5).number_format = '"Rp" #,##0'
                    ws.cell(row=last + 2, column=4, value="TOTAL BIAYA MATERIAL").font = Font(bold=True)
                    tot = ws.cell(row=last + 2, column=5, value=f"=SUM(E5:E{last})")
                    tot.font = Font(bold=True, color="FFFFFF")
                    tot.fill = PatternFill("solid", fgColor="2FC29B")
                    tot.number_format = '"Rp" #,##0'
                else:
                    for r in range(5, last + 1):
                        ws.cell(row=r, column=2).number_format = "#,##0.00"
                        ws.cell(row=r, column=2).alignment = Alignment(horizontal="left")
        return buf.getvalue()

    nama_file = "".join(ch if ch.isalnum() else "_" for ch in proyek)[:40] or "proyek"
    try:
        st.download_button("⬇️ Unduh Laporan Excel (.xlsx)", buat_xlsx(), f"RAB_{nama_file}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.caption("Berisi 2 sheet berformat tabel: Ringkasan dan RAB, lengkap dengan total biaya.")
    except Exception:
        st.warning("Fitur Excel butuh paket openpyxl. Tambahkan baris `openpyxl` ke requirements.txt, lalu deploy ulang.")
        st.download_button("⬇️ Unduh CSV (cadangan)", df_rab.to_csv(index=False, sep=";").encode("utf-8-sig"), f"RAB_{nama_file}.csv", "text/csv")
