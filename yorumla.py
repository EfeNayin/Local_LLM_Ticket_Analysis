import json
import ollama

MODEL = "qwen2.5:3b"


def sonuclari_oku():
    with open("analiz_sonuclari.json", encoding="utf-8") as f:
        return json.load(f)


def tablo(sozluk, limit=12):
    satirlar = []
    for i, (k, v) in enumerate(sozluk.items()):
        if i >= limit:
            break
        satirlar.append(f"  {k}: {v}")
    return "\n".join(satirlar)


def llm_sor(baslik, prompt):
    print(f"  -> {baslik} ... ", end="", flush=True)
    yanit = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.3},
    )
    metin = yanit["message"]["content"].strip()
    print(f"tamam ({len(metin)} karakter)")
    return metin


# =====================================================================
# SORU 1 — Gelen arıza türleri nelerdir?
# =====================================================================

def soru1(s):
    at = s["ariza_turleri"]
    prompt = f"""You are a fiber optic network operations analyst.

Below is the fault type distribution from {s['ozet']['toplam_kayit']:,} support tickets:

{tablo(at['dagilim'])}

Percentages:
{tablo(at['yuzde'])}

TASK: Write a summary in TURKISH describing the fault types in this network.
Group related types where sensible. State which types dominate and which are
marginal. Be factual. Maximum 180 words. Write only the analysis, no preamble."""
    return llm_sor("Soru 1: Ariza turleri", prompt)


# =====================================================================
# SORU 2 — En çok hangi arıza türü?
# =====================================================================

def soru2(s):
    at = s["ariza_turleri"]
    prompt = f"""You are a network operations analyst.

The most common fault type is:
  {at['en_cok']['kategori']} — {at['en_cok']['adet']:,} tickets ({at['en_cok']['yuzde']}%)

Full distribution:
{tablo(at['dagilim'])}

Total distinct fault types: {at['toplam_tur']}

TASK: Write a short analysis in TURKISH. Is the distribution dominated by one
type or spread across many? What does this mean for where the operations team
should focus? Maximum 130 words. Write only the analysis, no preamble."""
    return llm_sor("Soru 2: En cok tur", prompt)


# =====================================================================
# SORU 3 — Hangi cihaz?
# =====================================================================

def soru3(s):
    c = s["cihaz"]
    prompt = f"""You are a network operations analyst examining OLT device faults.

Total OLT devices: {c['toplam_olt']}
Average faults per device: {c['ortalama']}
Median faults per device: {c['medyan']}

Most affected device: {c['en_cok']['olt']} with {c['en_cok']['adet']} faults
({c['en_cok']['yuzde']}% of all tickets)

Top devices:
{tablo(c['en_cok_20'], limit=10)}

TASK: Write an analysis in TURKISH. Note that the mean and median are almost
equal ({c['ortalama']} vs {c['medyan']}) and even the worst device holds under
1% of tickets. What does this say about fault distribution across devices — is
it concentrated or homogeneous? Maximum 160 words. Write only the analysis."""
    return llm_sor("Soru 3: Cihaz", prompt)


# =====================================================================
# SORU 4 — Yoğun tarih?
# =====================================================================

def soru4(s):
    z = s["zaman"]
    prompt = f"""You are a network operations analyst examining fault timing.

Date range: {z['baslangic']} to {z['bitis']}
Daily average: {z['gunluk_ortalama']} faults, standard deviation: {z['gunluk_std']}

Busiest 10 days:
{tablo(z['en_yogun_10_gun'])}

Monthly totals:
{tablo(z['aylik'])}

Anomaly threshold (mean + 2 std): {z['anomali_esigi']} faults/day
Days above threshold: {z['anormal_gun_sayisi']}

TASK: Write an analysis in TURKISH. The standard deviation ({z['gunluk_std']})
is small relative to the mean ({z['gunluk_ortalama']}), and only
{z['anormal_gun_sayisi']} days exceed the anomaly threshold. Does the data show
temporal clustering or is it homogeneous? Is there a crisis period? Maximum 180
words. Write only the analysis, no preamble."""
    return llm_sor("Soru 4: Zaman", prompt)


# =====================================================================
# SORU 5 — Kök neden değerlendirmesi
# =====================================================================

def soru5(s):
    at = s["ariza_turleri"]
    c = s["cihaz"]
    z = s["zaman"]
    prompt = f"""You are a senior network operations analyst writing a root cause
assessment for management.

KEY FINDINGS:

Fault types ({at['toplam_tur']} categories, {s['ozet']['toplam_kayit']:,} tickets):
{tablo(at['dagilim'], limit=10)}
Dominant: {at['en_cok']['kategori']} at {at['en_cok']['yuzde']}%

Devices: {c['toplam_olt']} OLTs, mean {c['ortalama']} / median {c['medyan']} faults each.
Distribution is homogeneous — worst device holds only {c['en_cok']['yuzde']}%.

Timing: {z['baslangic']} to {z['bitis']}, daily average {z['gunluk_ortalama']}
(std {z['gunluk_std']}). Only {z['anormal_gun_sayisi']} anomalous days.
No temporal clustering.

TASK: Write a root cause assessment in TURKISH covering:
1. What could explain the dominance of {at['en_cok']['kategori']} faults?
2. Given faults are spread evenly across devices AND time (no hotspots, no
   crisis periods), what does this suggest about the nature of the faults —
   systemic/structural versus incident-driven?
3. Three concrete recommendations for the operations team.

IMPORTANT: Frame causes as HYPOTHESES, not conclusions. Ticket data shows
correlation, not causation. Note what additional data (device age, firmware,
subscriber count per OLT) would be needed to confirm. Maximum 400 words.
Write only the assessment, no preamble."""
    return llm_sor("Soru 5: Kok neden", prompt)



# Main Flow

if __name__ == "__main__":
    print("LLM yorumlama basliyor...")
    print(f"Model: {MODEL} (CPU, her soru 1-3 dk surebilir)\n")

    s = sonuclari_oku()

    yorumlar = {
        "soru1": soru1(s),
        "soru2": soru2(s),
        "soru3": soru3(s),
        "soru4": soru4(s),
        "soru5": soru5(s),
    }

    with open("llm_yorumlari.json", "w", encoding="utf-8") as f:
        json.dump(yorumlar, f, ensure_ascii=False, indent=2)

    print("\nTamamlandi -> llm_yorumlari.json\n")

    basliklar = {
        "soru1": "1. GELEN ARIZA TURLERI",
        "soru2": "2. EN COK ARIZA TURU",
        "soru3": "3. CIHAZ ANALIZI",
        "soru4": "4. ZAMAN ANALIZI",
        "soru5": "5. KOK NEDEN DEGERLENDIRMESI",
    }
    for anahtar, baslik in basliklar.items():
        print("=" * 60)
        print(baslik)
        print("=" * 60)
        print(yorumlar[anahtar])
        print()
