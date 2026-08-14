import json
import ollama

MODEL = "qwen2.5:3b"

def read_results():
    with open("analiz_sonuclari.json", encoding="utf-8") as f:
        return json.load(f)


def format_table(dictionary, limit=12):
    rows = []
    for i, (k, v) in enumerate(dictionary.items()):
        if i >= limit:
            break
        rows.append(f"  {k}: {v}")
    return "\n".join(rows)


def ask_llm(title, prompt):
    print(f"  -> {title} ... ", end="", flush=True)
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.3},
    )
    text = response["message"]["content"].strip()
    print(f"done ({len(text)} characters)")
    return text


# =====================================================================
# QUESTION 1 — What are the incoming fault types?
# =====================================================================

def question1(s):
    ft = s["ariza_turleri"]
    prompt = f"""You are a fiber optic network operations analyst.

Below is the fault type distribution from {s['ozet']['toplam_kayit']:,} support tickets:

{format_table(ft['dagilim'])}

Percentages:
{format_table(ft['yuzde'])}

TASK: Write a summary in ENGLISH describing the fault types in this network.
Group related types where sensible. State which types dominate and which are
marginal. Be factual. Maximum 180 words. Write only the analysis, no preamble."""
    return ask_llm("Question 1: Fault types", prompt)


# =====================================================================
# QUESTION 2 — Which fault type is the most common?
# =====================================================================

def question2(s):
    ft = s["ariza_turleri"]
    prompt = f"""You are a network operations analyst.

The most common fault type is:
  {ft['en_cok']['kategori']} — {ft['en_cok']['adet']:,} tickets ({ft['en_cok']['yuzde']}%)

Full distribution:
{format_table(ft['dagilim'])}

Total distinct fault types: {ft['toplam_tur']}

TASK: Write a short analysis in ENGLISH. Is the distribution dominated by one
type or spread across many? What does this mean for where the operations team
should focus? Maximum 130 words. Write only the analysis, no preamble."""
    return ask_llm("Question 2: Most common type", prompt)


# =====================================================================
# QUESTION 3 — Which device?
# =====================================================================

def question3(s):
    d = s["cihaz"]
    prompt = f"""You are a network operations analyst examining OLT device faults.

Total OLT devices: {d['toplam_olt']}
Average faults per device: {d['ortalama']}
Median faults per device: {d['medyan']}

Most affected device: {d['en_cok']['olt']} with {d['en_cok']['adet']} faults
({d['en_cok']['yuzde']}% of all tickets)

Top devices:
{format_table(d['en_cok_20'], limit=10)}

TASK: Write an analysis in ENGLISH. Note that the mean and median are almost
equal ({d['ortalama']} vs {d['medyan']}) and even the worst device holds under
1% of tickets. What does this say about fault distribution across devices — is
it concentrated or homogeneous? Maximum 160 words. Write only the analysis."""
    return ask_llm("Question 3: Device analysis", prompt)


# =====================================================================
# QUESTION 4 — Busiest dates?
# =====================================================================

def question4(s):
    t = s["zaman"]
    prompt = f"""You are a network operations analyst examining fault timing.

Date range: {t['baslangic']} to {t['bitis']}
Daily average: {t['gunluk_ortalama']} faults, standard deviation: {t['gunluk_std']}

Busiest 10 days:
{format_table(t['en_yogun_10_gun'])}

Monthly totals:
{format_table(t['aylik'])}

Anomaly threshold (mean + 2 std): {t['anomali_esigi']} faults/day
Days above threshold: {t['anormal_gun_sayisi']}

TASK: Write an analysis in ENGLISH. The standard deviation ({t['gunluk_std']})
is small relative to the mean ({t['gunluk_ortalama']}), and only
{t['anormal_gun_sayisi']} days exceed the anomaly threshold. Does the data show
temporal clustering or is it homogeneous? Is there a crisis period? Maximum 180
words. Write only the analysis, no preamble."""
    return ask_llm("Question 4: Time analysis", prompt)


# =====================================================================
# QUESTION 5 — Root cause assessment
# =====================================================================

def question5(s):
    ft = s["ariza_turleri"]
    d = s["cihaz"]
    t = s["zaman"]
    prompt = f"""You are a senior network operations analyst writing a root cause
assessment for management.

KEY FINDINGS:

Fault types ({ft['toplam_tur']} categories, {s['ozet']['toplam_kayit']:,} tickets):
{format_table(ft['dagilim'], limit=10)}
Dominant: {ft['en_cok']['kategori']} at {ft['en_cok']['yuzde']}%

Devices: {d['toplam_olt']} OLTs, mean {d['ortalama']} / median {d['medyan']} faults each.
Distribution is homogeneous — worst device holds only {d['en_cok']['yuzde']}%.

Timing: {t['baslangic']} to {t['bitis']}, daily average {t['gunluk_ortalama']}
(std {t['gunluk_std']}). Only {t['anormal_gun_sayisi']} anomalous days.
No temporal clustering.

TASK: Write a root cause assessment in ENGLISH covering:
1. What could explain the dominance of {ft['en_cok']['kategori']} faults?
2. Given faults are spread evenly across devices AND time (no hotspots, no
   crisis periods), what does this suggest about the nature of the faults —
   systemic/structural versus incident-driven?
3. Three concrete recommendations for the operations team.

IMPORTANT: Frame causes as HYPOTHESES, not conclusions. Ticket data shows
correlation, not causation. Note what additional data (device age, firmware,
subscriber count per OLT) would be needed to confirm. Maximum 400 words.
Write only the assessment, no preamble."""
    return ask_llm("Question 5: Root cause", prompt)


# Main Flow

if __name__ == "__main__":
    print("LLM interpretation is starting...")
    print(f"Model: {MODEL} (CPU, each question may take 1-3 mins)\n")

    s = read_results()

    analyses = {
        "question1": question1(s),
        "question2": question2(s),
        "question3": question3(s),
        "question4": question4(s),
        "question5": question5(s),
    }

    with open("llm_analyses.json", "w", encoding="utf-8") as f:
        json.dump(analyses, f, ensure_ascii=False, indent=2)

    print("\nCompleted -> llm_analyses.json\n")

    headers = {
        "question1": "1. INCOMING FAULT TYPES",
        "question2": "2. MOST COMMON FAULT TYPE",
        "question3": "3. DEVICE ANALYSIS",
        "question4": "4. TIME ANALYSIS",
        "question5": "5. ROOT CAUSE ASSESSMENT",
    }
    
    for key, header in headers.items():
        print("=" * 60)
        print(header)
        print("=" * 60)
        print(analyses[key])
        print()