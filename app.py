# Install: pip install streamlit pandas plotly
# Jalankan: streamlit run app.py
# CivilCalc Pro: Estimator Dinding 1/2 Batu & CMS Admin Panel

import copy
import math

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CivilCalc Pro", page_icon="🧱", layout="wide")

ADMIN_PASSWORD = "admin123"
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


def rp(x):
    return "Rp " + f"{x:,.0f}".replace(",", ".")


def num(x, d=2):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------ CSS
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp, .stMarkdown, button, input, select, textarea {
    font-family: 'Inter', system-ui, sans-serif !important;
}
.stApp { background: #f8fafc; }
.block-container { padding-top: 1.5rem; max-width: 1250px; }
.hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e3c72 100%);
    border-radius: 14px; padding: 28px 32px; color: #ffffff; margin-bottom: 22px;
    box-shadow: 0 10px 25px -5px rgba(15,23,42,0.25);
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;
}
.hero h1 { margin: 0; font-size: 1.85rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; }
.hero p { margin: 6px 0 0 0; color: #cbd5e1; font-size: 0.95rem; }
.badge { padding: 8px 16px; border-radius: 999px; font-size: 0.82rem; font-weight: 700; color: #ffffff; }
.badge-user { background: #2563eb; }
.badge-admin { background: #d97706; }
.kpi {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px 20px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); height: 100%;
}
.kpi .label { font-size: 0.74rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.6px; }
.kpi .value { font-size: 1.85rem; font-weight: 800; color: #0f172a; margin: 6px 0 4px 0; }
.kpi .detail { font-size: 0.8rem; color: #475569; }
.kpi.blue { border-top: 4px solid #2563eb; }
.kpi.green { border-top: 4px solid #10b981; }
.kpi.amber { border-top: 4px solid #d97706; }
.kpi.navy { border-top: 4px solid #1e3c72; }
.callout {
    background: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 8px;
    padding: 14px 18px; color: #1e3a8a; font-size: 0.9rem; margin: 12px 0;
}
.total-box {
    background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: #ffffff;
    border-radius: 12px; padding: 20px 26px; margin-top: 14px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);
}
.total-box .t1 { font-size: 0.8rem; font-weight: 600; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.6px; }
.total-box .t2 { font-size: 2rem; font-weight: 800; }
.section-title { font-size: 1.05rem; font-weight: 700; color: #0f172a; margin: 18px 0 8px 0; }
section[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e2e8f0; }
.stTabs [data-baseweb="tab"] { font-weight: 600; }
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

with st.sidebar:
    st.markdown("## 🧱 CivilCalc Pro")
    st.caption("Estimator Dinding 1/2 Batu")

    st.markdown("### 📐 Geometri Dinding")
    panjang_dinding = st.number_input("Panjang dinding (m)", min_value=0.1, value=10.0, step=0.5)
    tinggi_dinding = st.number_input("Tinggi dinding (m)", min_value=0.1, value=3.0, step=0.1)
    luas_bukaan = st.number_input("Luas bukaan pintu/jendela (m²)", min_value=0.0, value=3.0, step=0.5)

    st.markdown("### 🧱 Spesifikasi Material")
    mat_pilih = st.selectbox("Jenis material dinding", mat_names)
    tebal_spesi = st.slider("Tebal spesi (cm)", 0.5, 3.0, 1.5, 0.1)
    waste = st.slider("Waste / susut (%)", 0, 25, 5, 1)

    mat = next(m for m in db["materials"] if m["nama"] == mat_pilih)

    st.markdown("### 💰 Harga Satuan Material")
    st.caption("Terisi otomatis dari database Admin, bisa Anda ubah.")
    harga_bata = st.number_input(
        "Harga bata (Rp/buah)", min_value=0.0, value=float(mat["harga"]), step=50.0,
        format="%.0f", key=f"hb_{ver}_{mat_pilih}",
    )
    harga_semen = st.number_input(
        "Harga semen (Rp/sak 40kg)", min_value=0.0, value=float(db["semen_sak"]), step=1000.0,
        format="%.0f", key=f"hs_{ver}",
    )
    harga_pasir = st.number_input(
        "Harga pasir (Rp/m³)", min_value=0.0, value=float(db["pasir_m3"]), step=5000.0,
        format="%.0f", key=f"hp_{ver}",
    )

    st.markdown("---")
    st.markdown("### 🔐 Akses Admin (Owner)")
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
badge = (
    '<span class="badge badge-admin">🔓 Admin Mode Active</span>'
    if st.session_state.admin
    else '<span class="badge badge-user">👤 User Mode</span>'
)
st.markdown(
    f'<div class="hero"><div><h1>🧱 CivilCalc Pro</h1>'
    f'<p>Estimator Dinding 1/2 Batu &amp; CMS Admin Panel &mdash; hitung volume material dan RAB secara presisi</p></div>'
    f'<div>{badge}</div></div>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Dashboard Metrik Utama", "📈 Analisis Cost & RAB", "⚙️ Panel Pengaturan Admin", "📄 Formulasi Teknik Sipil & Ekspor"]
)

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
    st.markdown('<div class="section-title">Rekapitulasi Rencana Anggaran Biaya (RAB) Material</div>', unsafe_allow_html=True)
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
                color_discrete_sequence=["#2563eb", "#d97706", "#10b981"],
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
    if not st.session_state.admin:
        st.warning("🔒 Panel ini hanya dapat diakses Admin. Masuk lewat **Akses Admin (Owner)** di sidebar.")
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
                "Material", "Dimensi bata p x b x t (cm)", "Panjang dinding (m)", "Tinggi dinding (m)", "Luas gross (m2)",
                "Luas bukaan (m2)", "Luas netto (m2)", "Tebal spesi (cm)", "Waste (%)", "Rasio campuran",
                "Volume spesi (m3)", "Semen (kg)",
            ],
            "Nilai": [
                mat_pilih, f"{mat['p']:g} x {mat['b']:g} x {mat['t']:g}", f"{panjang_dinding:.2f}", f"{tinggi_dinding:.2f}",
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
