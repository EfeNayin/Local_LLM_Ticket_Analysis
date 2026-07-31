import pandas as pd

pd.set_option("display.max_colwidth", None)

df = pd.read_csv("20k_ariza_ticket.csv", sep=";")
metin = df["ARIZA_NEDENI"].str.lower()

print("TARIH ORNEKLERI:", df["ARIZA_ACILIS_TARIHI"].head(10).to_list())

kategoriler = [
    ("OLT Donanim", r"lt\d+ kart|lt kart|kartı|kartın|kartına|uplink|"
                    r"sıcaklık|°c|servis dışı|güç ünitesi|"
                    r"olt'sine erişilemiyor|olt'ye erişilemiyor|"
                    r"yönetim ip|rx/tx"),
    ("Enerji/Guc", r"enerji kesinti|güç kaynağı|saha dolab|elektrik|jeneratör|akü"),
    ("Optik Seviye", r"optik|dbm|sinyal seviye|los durumu|rx seviye"),
    ("IPTV/Yayin", r"iptv|multicast|igmp|kanal|yayın|televizyon"),
    ("VoIP/Ses", r"voip|sip|ses |sesi|telefon|register|arama kuruluyor"),
    ("VLAN/Konfigurasyon", r"vlan|profil|eşleşmiyor|uyuşmuyor|konfigür"),
    ("Hiz/Performans", r"hız|mbps|paket kaybı|gecikme"),
    ("Internet Erisim", r"pppoe|padi|dhcp|ip alamıyor|ip alamadığı|"
                        r"ip tahsis|ip alma|ip atanamıyor|oturum|internet"),
    ("ONT Cihaz", r"ont|omci|esn|seri numara|modem|reboot|cpe|alcl|"
                  r"yazılım|offline|erişilemez|kayıt olmuyor|"
                  r"yeniden başlama"),
]

df["kategori"] = "Diger"

for ad, desen in kategoriler:
    etiketsiz = df["kategori"] == "Diger"
    eslesme = metin.str.contains(desen, na=False)
    df.loc[etiketsiz & eslesme, "kategori"] = ad


# ---------------------------------------------------------------- ÇIKTI

print("KATEGORI DAGILIMI")
print("-" * 50)
dagilim = df["kategori"].value_counts()

for kat, adet in dagilim.items():
    yuzde = adet / len(df) * 100
    print(f"{kat:<22} {adet:>6,}  %{yuzde:>5.1f}")

print(f"\nToplam: {len(df):,} kayit")

diger_orani = (df['kategori'] == 'Diger').sum() / len(df) * 100

print(f"Siniflandirilamayan: %{diger_orani:.1f}")


print("\n\nKATEGORI ORNEKLERI")
print("=" * 100)

for kat in dagilim.index:
    print(f"\n--- {kat} ---")
    ornekler = df[df["kategori"] == kat]["ARIZA_NEDENI"].sample(
        min(3, (df["kategori"] == kat).sum()), random_state=1
    )
    for o in ornekler:
        print(f"  • {o[:130]}")



print("=" * 60)
print("SORU 3 — CIHAZ (OLT) ANALIZI")
print("=" * 60)
 
# value_counts() bir kolondaki her değerin kaç kez geçtiğini sayar
# ve çoktan aza sıralar. Yani en çok arıza alan OLT en üstte olur.
olt_dagilimi = df["OLT_ADI"].value_counts()
 
# Kaç farklı OLT var? nunique() = number of unique (benzersiz sayısı)
print(f"\nToplam OLT sayisi: {df['OLT_ADI'].nunique()}")
 
# OLT başına ortalama ve medyan arıza — dağılımın dengeli olup
# olmadığını anlamak için. Ortalama medyandan çok büyükse, birkaç
# OLT çok arıza alıyor demektir (çarpık dağılım).
print(f"OLT basina ortalama ariza: {olt_dagilimi.mean():.1f}")
print(f"OLT basina medyan ariza  : {olt_dagilimi.median():.0f}")
 
# En çok arıza alan 15 OLT
print("\nEn cok ariza alan 15 OLT:")
print("-" * 40)
for olt, adet in olt_dagilimi.head(15).items():
    yuzde = adet / len(df) * 100
    print(f"  {olt:<28} {adet:>5}  %{yuzde:.1f}")
 
# En çok arıza alan tek OLT (soru 3'ün doğrudan cevabı)
en_cok = olt_dagilimi.index[0]
print(f"\n>> En cok ticket gelen cihaz: {en_cok} ({olt_dagilimi.iloc[0]} ariza)")
 
 
# =====================================================================
# SORU 4 — Arızalarda yoğunlaşan bir tarih var mı?
# =====================================================================
 
print("\n\n" + "=" * 60)
print("SORU 4 — ZAMAN ANALIZI")
print("=" * 60)
 
# Tarih kolonu şu an metin (string). Üzerinde tarih işlemi yapabilmek
# için gerçek tarih tipine çeviriyoruz. format, verinin nasıl yazıldığını
# söyler: %d gün, %m ay, %Y yıl, %H saat, %M dakika, %S saniye.
# errors="coerce": çevrilemeyen değer olursa hata verme, boş (NaT) yap.
df["tarih"] = pd.to_datetime(
    df["ARIZA_ACILIS_TARIHI"],
    format="%d.%m.%Y %H:%M",
    errors="coerce",
)
 
# Kaç kayıt çevrilemedi? Boş tarih sayısını kontrol et.
cozulemedi = df["tarih"].isna().sum()
if cozulemedi:
    print(f"\nUYARI: {cozulemedi} kaydin tarihi cozulemedi")
 
# Tarih aralığı: en eski ve en yeni arıza
print(f"\nTarih araligi: {df['tarih'].min()} - {df['tarih'].max()}")
 
# --- Günlük dağılım ---
# .dt tarih parçalarına erişim sağlar. .dt.date sadece günü verir
# (saati atar). groupby ile aynı güne düşenleri grupluyoruz,
# size() her grupta kaç kayıt olduğunu sayıyor.
gunluk = df.groupby(df["tarih"].dt.date).size()
 
print(f"\nGunluk ortalama ariza: {gunluk.mean():.1f}")
print(f"Gunluk standart sapma: {gunluk.std():.1f}")
 
# En yoğun 10 gün. nlargest(10) en büyük 10 değeri getirir.
print("\nEn yogun 10 gun:")
print("-" * 30)
for tarih, adet in gunluk.nlargest(10).items():
    print(f"  {tarih}   {adet} ariza")
 
# --- Anormal günler ---
# İstatistikte "ortalama + 2 standart sapma" üzerini anormal sayarız.
# Bu eşiği geçen günler rutin akıştan sapma, muhtemelen bir olay.
esik = gunluk.mean() + 2 * gunluk.std()
anormal = gunluk[gunluk > esik]
print(f"\nAnormal yogunluk esigi: {esik:.0f} ariza/gun")
print(f"Bu esigi asan gun sayisi: {len(anormal)}")
 
# --- Aylık dağılım ---
# to_period("M") tarihi aya yuvarlar (2026-01 gibi). Hangi ay yoğun?
aylik = df.groupby(df["tarih"].dt.to_period("M")).size()
print("\nAylik dagilim:")
print("-" * 30)
for ay, adet in aylik.items():
    print(f"  {ay}   {adet} ariza")
 
# --- Saatlik dağılım ---
# .dt.hour saati verir (0-23). Arızalar günün hangi saatinde yoğun?
saatlik = df.groupby(df["tarih"].dt.hour).size()
print("\nEn yogun 5 saat:")
print("-" * 30)
for saat, adet in saatlik.nlargest(5).items():
    print(f"  Saat {saat:02d}:00   {adet} ariza")
 
# --- Haftanın günleri ---
# .dt.dayofweek: 0=Pazartesi ... 6=Pazar
gun_adlari = ["Pazartesi", "Sali", "Carsamba", "Persembe",
              "Cuma", "Cumartesi", "Pazar"]
haftalik = df.groupby(df["tarih"].dt.dayofweek).size()
print("\nHaftanin gunlerine gore:")
print("-" * 30)
for gun_no, adet in haftalik.items():
    print(f"  {gun_adlari[gun_no]:<12} {adet} ariza")