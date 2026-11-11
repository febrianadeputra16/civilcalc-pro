# Install: pip install streamlit pandas plotly
# Jalankan: streamlit run app.py
# CivilCalc Pro: Estimator Dinding 1/2 Batu & CMS Admin Panel

import copy
import html
import math

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CivilCalc Pro", page_icon="🧱", layout="wide", initial_sidebar_state="expanded")

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
        "pasir_m3": 280000.0,
        "mortar": {"ratio": "1:4", "semen_kg_m3": 325.0, "pasir_m3_m3": 0.60},
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

# Fitur admin hanya muncul jika link dibuka dengan ?owner=<OWNER_KEY>
admin_available = bool(OWNER_KEY) and bool(ADMIN_PASSWORD) and st.query_params.get("owner") == OWNER_KEY
is_admin = admin_available and st.session_state.admin


def rp(x):
    return "Rp " + f"{x:,.0f}".replace(",", ".")


def num(x, d=2):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


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
section[data-testid="stSidebar"] div[data-baseweb="input"], section[data-testid="stSidebar"] div[data-baseweb="base-input"], section[data-testid="stSidebar"] div[data-baseweb="select"] > div { background: rgba(255,255,255,0.10) !important; border-color: rgba(255,255,255,0.18) !important; border-radius: 12px !important; }
section[data-testid="stSidebar"] input { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
section[data-testid="stSidebar"] div[data-baseweb="select"] * { color: #ffffff !important; }
section[data-testid="stSidebar"] [data-testid="stNumberInputStepDown"], section[data-testid="stSidebar"] [data-testid="stNumberInputStepUp"] { background: transparent !important; color: #ffffff !important; }
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
ver = st.session_state.ver
mat_names = [m["nama"] for m in db["materials"]]
V = st.session_state.setdefault("vals", {})
for _k, _v in {"p": 10.0, "t": 3.0, "buk": 3.0, "spesi": 1.5, "waste": 5}.items():
    V.setdefault(_k, _v)
if V.get("mat") not in mat_names:
    V["mat"] = mat_names[0]
    st.session_state.pop("w_mat", None)
if st.session_state.get("w_mat") not in (None, *mat_names):
    st.session_state.pop("w_mat", None)
st.session_state.setdefault("menu", "geo")
proyek = st.session_state.get("proyek", "")


def set_menu(k):
    st.session_state.menu = None if st.session_state.menu == k else k


def ganti_proyek():
    st.session_state.proyek_last = st.session_state.get("proyek", "")
    st.session_state.proyek = ""


def price_state():
    m = next(x for x in db["materials"] if x["nama"] == V["mat"])
    kb, ks, kp = f"hb_{ver}_{V['mat']}", f"hs_{ver}", f"hp_{ver}"
    V.setdefault(kb, float(m["harga"]))
    V.setdefault(ks, float(db["semen_sak"]))
    V.setdefault(kp, float(db["pasir_m3"]))
    return m, kb, ks, kp


def field(sec, kind, key, label, **kw):
    # Widget hanya digambar saat menunya terbuka; nilainya selalu tersimpan di V
    if proyek and st.session_state.menu == sec:
        wk = "w_" + key
        st.session_state.setdefault(wk, V[key])
        fn = {"num": st.number_input, "sel": st.selectbox, "sld": st.slider}[kind]
        V[key] = fn(label, key=wk, **kw)
    return V[key]


with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-logo">🧱</div><div><div class="brand-t">CivilCalc Pro</div>'
        '<div class="brand-s">Estimator Dinding 1/2 Batu</div></div></div>',
        unsafe_allow_html=True,
    )
    if proyek:
        st.markdown(f'<div class="side-proj"><span>PROYEK</span>{html.escape(proyek)}</div>', unsafe_allow_html=True)
        for k, ic, lb in (("geo", "📐", "Geometri Dinding"), ("mat", "🧱", "Spesifikasi Material"), ("hrg", "💰", "Harga Satuan Material")):
            st.button(
                f"{ic}  {lb}", key=f"nav_{k}", on_click=set_menu, args=(k,), use_container_width=True,
                type="primary" if st.session_state.menu == k else "secondary",
            )
            if k == "geo":
                field("geo", "num", "p", "Panjang dinding (m)", min_value=0.1, step=0.5)
                field("geo", "num", "t", "Tinggi dinding (m)", min_value=0.1, step=0.1)
                field("geo", "num", "buk", "Luas bukaan pintu/jendela (m²)", min_value=0.0, step=0.5)
            elif k == "mat":
                field("mat", "sel", "mat", "Jenis material dinding", options=mat_names)
                field("mat", "sld", "spesi", "Tebal spesi (cm)", min_value=0.5, max_value=3.0, step=0.1)
                field("mat", "sld", "waste", "Waste / susut (%)", min_value=0, max_value=25, step=1)
            else:
                _, kb, ks, kp = price_state()
                if st.session_state.menu == "hrg":
                    st.caption("Terisi otomatis dari database Admin, bisa Anda ubah.")
                field("hrg", "num", kb, "Harga bata (Rp/buah)", min_value=0.0, step=50.0, format="%.0f")
                field("hrg", "num", ks, "Harga semen (Rp/sak 40kg)", min_value=0.0, step=1000.0, format="%.0f")
                field("hrg", "num", kp, "Harga pasir (Rp/m³)", min_value=0.0, step=5000.0, format="%.0f")
        st.button("✏️  Ganti Nama Proyek", key="nav_ren", on_click=ganti_proyek, use_container_width=True)
    else:
        st.caption("Isi nama proyek di halaman utama untuk mulai menghitung.")

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

mat_pilih = V["mat"]
mat, _kb, _ks, _kp = price_state()
panjang_dinding, tinggi_dinding, luas_bukaan = V["p"], V["t"], V["buk"]
tebal_spesi, waste = V["spesi"], V["waste"]
harga_bata, harga_semen, harga_pasir = V[_kb], V[_ks], V[_kp]

# ------------------------------------------------------------------ CORE ENGINE
p = mat["p"] / 100.0
b = mat["b"] / 100.0
t = mat["t"] / 100.0
s = tebal_spesi / 100.0

luas_gross = panjang_dinding * tinggi_dinding
a_netto = max(0.0, luas_gross - luas_bukaan)
p_ef = p + s
t_ef = t + s
area_unit_ef = p_ef * t_ef
unit_teoritis = a_netto / area_unit_ef
n_total = math.ceil(unit_teoritis * (1 + waste / 100.0))
vol_dinding = a_netto * b
vol_unit_murni = unit_teoritis * (p * b * t)
v_spesi = max(0.0, vol_dinding - vol_unit_murni)
semen_kg = v_spesi * db["mortar"]["semen_kg_m3"]
semen_sak = math.ceil(semen_kg / SAK_KG)
pasir_m3 = round(v_spesi * db["mortar"]["pasir_m3_m3"], 2)

biaya_bata = n_total * harga_bata
biaya_semen = semen_sak * harga_semen
biaya_pasir = pasir_m3 * harga_pasir
biaya_total = biaya_bata + biaya_semen + biaya_pasir

rab = pd.DataFrame(
    {
        "Uraian Material": [f"{mat_pilih} ({mat['p']:g}x{mat['b']:g}x{mat['t']:g} cm)", "Semen Portland (sak 40 kg)", "Pasir Pasang (m³)"],
        "Volume": [n_total, semen_sak, pasir_m3],
        "Satuan": ["buah", "sak", "m³"],
        "Harga Satuan (Rp)": [harga_bata, harga_semen, harga_pasir],
        "Subtotal (Rp)": [biaya_bata, biaya_semen, biaya_pasir],
    }
)

# ------------------------------------------------------------------ HERO
chip = f'<span class="chip">📁 {html.escape(proyek)}</span>' if proyek else ''
badge = (
    '<span class="badge badge-admin">🔓 Admin Mode Active</span>'
    if is_admin
    else '<span class="badge badge-user">👤 User Mode</span>'
)
st.markdown(
    f'<div class="hero"><div><h1>🧱 CivilCalc Pro</h1>'
    f'<p>Estimator Dinding 1/2 Batu &amp; CMS Admin Panel &mdash; hitung volume material dan RAB secara presisi</p></div>'
    f'<div class="hero-r">{chip}{badge}</div></div>',
    unsafe_allow_html=True,
)

if not proyek:
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown(
            '<div class="gate"><div class="gate-ic">🏗️</div><h2>Mulai Proyek Baru</h2>'
            '<p>Isi nama proyek terlebih dahulu sebelum memasukkan data dinding. '
            'Nama ini akan tampil di dashboard, RAB, dan laporan ekspor.</p></div>',
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

if is_admin:
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Dashboard Metrik Utama", "📈 Analisis Cost & RAB", "⚙️ Panel Pengaturan Admin", "📄 Formulasi Teknik Sipil & Ekspor"]
    )
else:
    # Pengunjung biasa: tab admin tidak dibuat sama sekali
    tab1, tab2, tab4 = st.tabs(
        ["📊 Dashboard Metrik Utama", "📈 Analisis Cost & RAB", "📄 Formulasi Teknik Sipil & Ekspor"]
    )
    tab3 = st.container()

# ------------------------------------------------------------------ TAB 1
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        kpi("Luas Netto Dinding", f"{num(a_netto)} m²", f"Gross {num(luas_gross)} m² − bukaan {num(luas_bukaan)} m²", "blue"),
        unsafe_allow_html=True,
    )
    c2.markdown(
        kpi("Total Kebutuhan Unit", f"{n_total:,} buah".replace(",", "."), f"Teoritis {num(unit_teoritis, 1)} + waste {waste}%", "amber"),
        unsafe_allow_html=True,
    )
    c3.markdown(
        kpi("Kebutuhan Semen", f"{semen_sak} sak", f"{num(semen_kg, 1)} kg &bull; rasio {db['mortar']['ratio']}", "navy"),
        unsafe_allow_html=True,
    )
    c4.markdown(
        kpi("Kebutuhan Pasir", f"{num(pasir_m3)} m³", f"{num(db['mortar']['pasir_m3_m3'])} m³ per m³ spesi", "green"),
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Ringkasan Spesifikasi Teknis Pasangan 1/2 Batu</div>', unsafe_allow_html=True)
    d1, d2, d3, d4 = st.columns(4)
    d1.markdown(kpi("Volume Spesi", f"{num(v_spesi, 3)} m³", f"Dinding {num(vol_dinding, 3)} m³ − bata {num(vol_unit_murni, 3)} m³", "blue"), unsafe_allow_html=True)
    d2.markdown(kpi("Tebal Dinding Murni", f"{mat['b']:g} cm", "Lebar bata (pasangan 1/2 batu)", "navy"), unsafe_allow_html=True)
    d3.markdown(kpi("Dimensi Efektif Unit", f"{p_ef*100:.1f} × {t_ef*100:.1f} cm", f"Ukuran bata + spesi {tebal_spesi:g} cm", "amber"), unsafe_allow_html=True)
    d4.markdown(kpi("Luas Efektif / Unit", f"{area_unit_ef*10000:.1f} cm²", f"≈ {num(1/area_unit_ef, 1)} unit per m²", "green"), unsafe_allow_html=True)

    callout(
        f"<b>Catatan:</b> Perhitungan memakai bata <b>{mat_pilih}</b> dengan campuran spesi <b>{db['mortar']['ratio']}</b> "
        f"(semen {num(db['mortar']['semen_kg_m3'], 0)} kg/m³, pasir {num(db['mortar']['pasir_m3_m3'])} m³/m³ spesi). "
        "Hasil bersifat estimasi awal; sesuaikan dengan kondisi lapangan dan standar proyek."
    )

# ------------------------------------------------------------------ TAB 2
with tab2:
    st.markdown(f'<div class="section-title">Rekapitulasi RAB Material &mdash; {html.escape(proyek)}</div>', unsafe_allow_html=True)
    tampil = rab.copy()
    tampil["Volume"] = [f"{n_total:,}".replace(",", "."), str(semen_sak), num(pasir_m3)]
    tampil["Harga Satuan (Rp)"] = tampil["Harga Satuan (Rp)"].map(rp)
    tampil["Subtotal (Rp)"] = tampil["Subtotal (Rp)"].map(rp)
    st.dataframe(tampil, use_container_width=True, hide_index=True)

    col_a, col_b = st.columns([3, 2])
    with col_a:
        if biaya_total > 0:
            fig = px.pie(
                names=["Bata", "Semen", "Pasir"],
                values=[biaya_bata, biaya_semen, biaya_pasir],
                hole=0.55,
                color_discrete_sequence=["#115569", "#f6c453", "#2fc29b"],
                title="Proporsi Alokasi Biaya Material",
            )
            fig.update_traces(textinfo="percent+label", hovertemplate="%{label}: Rp %{value:,.0f}<extra></extra>")
            fig.update_layout(
                font_family="Inter", margin=dict(t=50, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=-0.05),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Masukkan dimensi dinding untuk melihat grafik biaya.")
    with col_b:
        st.markdown(
            f'<div class="total-box"><div class="t1">Total Biaya Material Dinding</div>'
            f'<div class="t2">{rp(biaya_total)}</div></div>',
            unsafe_allow_html=True,
        )
        per_m2 = biaya_total / a_netto if a_netto > 0 else 0
        st.markdown(
            kpi("Biaya Material per m²", rp(per_m2), f"Bata {rp(biaya_bata)} &bull; Semen {rp(biaya_semen)} &bull; Pasir {rp(biaya_pasir)}", "blue"),
            unsafe_allow_html=True,
        )

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
    st.markdown("**4. Kebutuhan semen**")
    st.latex(r"Semen_{kg} = V_{spesi} \times K_{semen}, \qquad Semen_{sak} = \left\lceil \frac{Semen_{kg}}{40} \right\rceil")
    st.markdown("**5. Kebutuhan pasir**")
    st.latex(r"Pasir_{m^3} = \mathrm{round}\left(V_{spesi} \times K_{pasir},\; 2\right)")
    callout(
        "Keterangan: <b>p</b> = panjang bata (m), <b>b</b> = lebar bata/tebal dinding (m), <b>t</b> = tinggi bata (m), "
        "<b>s</b> = tebal spesi (m), <b>W</b> = waste (%), <b>K_semen</b> = kebutuhan semen per m³ spesi, "
        "<b>K_pasir</b> = kebutuhan pasir per m³ spesi."
    )

    st.markdown('<div class="section-title">Substitusi Nilai Saat Ini</div>', unsafe_allow_html=True)
    st.code(
        f"A_netto  = {luas_gross:.2f} - {luas_bukaan:.2f} = {a_netto:.2f} m2\n"
        f"p_ef x t_ef = {p_ef:.4f} x {t_ef:.4f} = {area_unit_ef:.5f} m2\n"
        f"Unit teoritis = {unit_teoritis:.2f}  ->  N_total = {n_total} buah\n"
        f"V_spesi  = {vol_dinding:.4f} - {vol_unit_murni:.4f} = {v_spesi:.4f} m3\n"
        f"Semen    = {semen_kg:.2f} kg = {semen_sak} sak\n"
        f"Pasir    = {pasir_m3:.2f} m3\n"
        f"Total    = {rp(biaya_total)}",
        language="text",
    )

    st.markdown('<div class="section-title">Ekspor Laporan Rekapitulasi</div>', unsafe_allow_html=True)
    params = pd.DataFrame(
        {
            "Parameter": [
                "Nama proyek", "Material", "Dimensi bata p x b x t (cm)", "Panjang dinding (m)", "Tinggi dinding (m)", "Luas gross (m2)",
                "Luas bukaan (m2)", "Luas netto (m2)", "Tebal spesi (cm)", "Waste (%)", "Rasio campuran",
                "Volume spesi (m3)", "Semen (kg)",
            ],
            "Nilai": [
                proyek, mat_pilih, f"{mat['p']:g} x {mat['b']:g} x {mat['t']:g}", f"{panjang_dinding:.2f}", f"{tinggi_dinding:.2f}",
                f"{luas_gross:.2f}", f"{luas_bukaan:.2f}", f"{a_netto:.2f}", f"{tebal_spesi:.1f}", f"{waste}",
                db["mortar"]["ratio"], f"{v_spesi:.4f}", f"{semen_kg:.2f}",
            ],
        }
    )
    rab_export = rab.copy()
    rab_export.loc[len(rab_export)] = ["TOTAL BIAYA MATERIAL", "", "", "", biaya_total]

    def build_csv(sep):
        return (
            "LAPORAN CIVILCALC PRO - ESTIMASI DINDING 1/2 BATU\n\n"
            "PARAMETER\n" + params.to_csv(index=False, sep=sep)
            + "\nREKAPITULASI RAB\n" + rab_export.to_csv(index=False, sep=sep)
        ).encode("utf-8-sig")

    e1, e2 = st.columns(2)
    e1.download_button("⬇️ Unduh CSV (pemisah koma)", build_csv(","), "laporan_civilcalc.csv", "text/csv", use_container_width=True)
    e2.download_button("⬇️ Unduh CSV Excel (pemisah titik koma)", build_csv(";"), "laporan_civilcalc_excel.csv", "text/csv", use_container_width=True)
    st.caption("Gunakan versi titik koma bila Excel Anda memakai pengaturan regional Indonesia.")
