import json
from pathlib import Path
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Ariza Ticket Analizi",
    layout="wide",
)

# VERI YUKLEME

@st.cache_data  # veriyi bir kez yukle, tekrar tekrar okuma
def veri_yukle():
    with open("analiz_sonuclari.json", encoding="utf-8") as f:
        analiz = json.load(f)

    yorumlar = {}
    if Path("llm_yorumlari.json").exists():
        with open("llm_yorumlari.json", encoding="utf-8") as f:
            yorumlar = json.load(f)

    df = None
    if Path("etiketli_ticketlar.csv").exists():
        df = pd.read_csv("etiketli_ticketlar.csv", sep=";")

    return analiz, yorumlar, df


analiz, yorumlar, df = veri_yukle()



st.title("Ariza Ticket Analiz Panosu")
st.caption("FreeBSD 15.1 uzerinde yerel LLM (Qwen 2.5) ile analiz")

ozet = analiz["ozet"]
at = analiz["ariza_turleri"]
cihaz = analiz["cihaz"]
zaman = analiz["zaman"]


k1, k2, k3, k4 = st.columns(4)
k1.metric("Toplam Ticket", f"{ozet['toplam_kayit']:,}")
k2.metric("Ariza Turu", at["toplam_tur"])
k3.metric("Toplam OLT", cihaz["toplam_olt"])
k4.metric("Gunluk Ortalama", f"{zaman['gunluk_ortalama']:.0f}")

st.divider()


# Pages

sekmeler = st.tabs([
    "Ariza Turleri",
    "Cihaz Analizi",
    "Zaman Analizi",
    "Kok Neden",
    "Ham Veri",
])


# --- SEKME 1: Ariza Turleri ---
with sekmeler[0]:
    st.header("Gelen Ariza Turleri")

    sol, sag = st.columns([3, 2])

    with sol:
        dagilim = pd.Series(at["dagilim"]).sort_values()
        st.bar_chart(dagilim, horizontal=True, height=400)

    with sag:
        tablo = pd.DataFrame({
            "Adet": pd.Series(at["dagilim"]),
            "Yuzde": pd.Series(at["yuzde"]),
        })
        st.dataframe(tablo, use_container_width=True)

    # En cok arizanin vurgusu
    st.info(
        f"En cok acilan tur: **{at['en_cok']['kategori']}** — "
        f"{at['en_cok']['adet']:,} ticket (%{at['en_cok']['yuzde']})"
    )

    # LLM yorumlari
    if yorumlar.get("soru1"):
        st.subheader("LLM Yorumu: Ariza Turleri")
        st.write(yorumlar["soru1"])

    if yorumlar.get("soru2"):
        st.subheader("LLM Yorumu: Yogunlasma")
        st.write(yorumlar["soru2"])


# --- SEKME 2: Cihaz Analizi  ---
with sekmeler[1]:
    st.header("Cihaz (OLT) Bazli Analiz")

    m1, m2, m3 = st.columns(3)
    m1.metric("Ortalama Ariza/OLT", f"{cihaz['ortalama']:.1f}")
    m2.metric("Medyan Ariza/OLT", f"{cihaz['medyan']:.0f}")
    m3.metric("En Sorunlu OLT", cihaz["en_cok"]["olt"],
              f"{cihaz['en_cok']['adet']} ariza")

    st.subheader("En Cok Ariza Alan 20 OLT")
    olt_serisi = pd.Series(cihaz["en_cok_20"]).sort_values()
    st.bar_chart(olt_serisi, horizontal=True, height=500)

    if yorumlar.get("soru3"):
        st.subheader("LLM Yorumu: Cihaz Dagilimi")
        st.write(yorumlar["soru3"])


# --- SEKME 3: Zaman Analizi ---
with sekmeler[2]:
    st.header("Zaman Bazli Analiz")

    st.caption(f"Tarih araligi: {zaman['baslangic']} — {zaman['bitis']}")

    m1, m2, m3 = st.columns(3)
    m1.metric("Gunluk Ortalama", f"{zaman['gunluk_ortalama']:.1f}")
    m2.metric("Standart Sapma", f"{zaman['gunluk_std']:.1f}")
    m3.metric("Anormal Gun", zaman["anormal_gun_sayisi"])

    # Gunluk zaman serisi grafigi (ham veriden)
    if df is not None:
        st.subheader("Gunluk Ariza Sayisi")
        df["tarih"] = pd.to_datetime(df["tarih"], errors="coerce")
        gunluk = df.groupby(df["tarih"].dt.date).size()
        gunluk.index = pd.to_datetime(gunluk.index)
        st.line_chart(gunluk, height=300)

    s1, s2 = st.columns(2)

    with s1:
        st.subheader("Saatlik Dagilim")
        saatlik = pd.Series(
            {int(k): v for k, v in zaman["saatlik"].items()}
        ).sort_index()
        st.bar_chart(saatlik, height=280)

    with s2:
        st.subheader("Aylik Dagilim")
        aylik = pd.Series(zaman["aylik"])
        st.bar_chart(aylik, height=280)

    st.subheader("En Yogun 10 Gun")
    yogun = pd.DataFrame({
        "Tarih": list(zaman["en_yogun_10_gun"].keys()),
        "Ariza": list(zaman["en_yogun_10_gun"].values()),
    })
    st.dataframe(yogun, use_container_width=True, hide_index=True)

    if yorumlar.get("soru4"):
        st.subheader("LLM Yorumu: Zaman Deseni")
        st.write(yorumlar["soru4"])


# --- SEKME 4: Kok Neden ---
with sekmeler[3]:
    st.header("Kok Neden Degerlendirmesi")

    st.caption(
        "Asagidaki degerlendirme, istatistiksel bulgular yerel LLM'e "
        "sunularak uretilmistir."
    )

    if yorumlar.get("soru5"):
        st.write(yorumlar["soru5"])
    else:
        st.warning("Kok neden yorumu bulunamadi.")

    st.divider()
    st.info(
        "**Metodolojik not:** Bu degerlendirme ticket sayilarina dayanir ve "
        "korelasyon gosterir, nedensellik kanitlamaz. Ortaya konan nedenler "
        "hipotez niteligindedir. Dogrulama icin cihaz yasi, firmware surumu ve "
        "OLT basina abone sayisi gibi ek veriler gereklidir."
    )


# --- SEKME 5: Ham Veri ---
with sekmeler[4]:
    st.header("Etiketli Veri")

    if df is None:
        st.warning("Etiketli veri dosyasi bulunamadi.")
    else:
        # Kategori filtresi
        kategoriler = ["(tumu)"] + sorted(df["kategori"].unique().tolist())
        secili = st.selectbox("Ariza turune gore filtrele", kategoriler)

        if secili == "(tumu)":
            gosterilecek = df
        else:
            gosterilecek = df[df["kategori"] == secili]

        st.caption(f"{len(gosterilecek):,} kayit")

        kolonlar = ["OLT_ADI", "ARIZA_ACILIS_TARIHI", "kategori", "ARIZA_NEDENI"]
        mevcut = [k for k in kolonlar if k in gosterilecek.columns]
        st.dataframe(
            gosterilecek[mevcut].head(500),
            use_container_width=True,
            hide_index=True,
        )
        if len(gosterilecek) > 500:
            st.caption("Ilk 500 kayit gosteriliyor.")