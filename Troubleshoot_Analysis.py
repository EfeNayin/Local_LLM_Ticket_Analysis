import pandas as pd

df = pd.read_csv("20k_ariza_ticket.csv", sep=";")
metin = df["ARIZA_NEDENI"].str.lower()

kategoriler = {
    "Optik Seviye":       "optik|dbm|sinyal",
    "IPTV/Yayin":         "iptv|multicast|igmp|kanal|yayın|televizyon",
    "VoIP/Ses":           "voip|sip|ses|telefon|çevir|register|arama",
    "Internet Erisim":    "pppoe|padi|dhcp|internet|gecikme",
    "Hiz/Performans":     "hız|mbps",
    "VLAN/Konfigurasyon": "vlan|profil|eşleşmiyor|uyuşmuyor|konfigür",
    "OLT Donanim":        "olt|kart|uplink|°c|sıcaklık|servis dışı",
    "ONT Cihaz":          "ont|modem|omci|esn|seri|reboot|online",
}

df["kategori"] = "Diger"
for ad, desen in kategoriler.items():
    df.loc[metin.str.contains(desen, na=False), "kategori"] = ad

print(df["kategori"].value_counts())
print()
print("Sınıflandırılamayan örnekler:")
print(df[df["kategori"] == "Diger"]["ARIZA_NEDENI"].head(10).to_string())