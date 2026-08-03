# Local LLM Ticket Analysis

FreeBSD üzerinde çalışan yerel bir büyük dil modeli (LLM) kullanarak fiber optik şebeke arıza ticket'larını analiz eden ve yorumlayan bir proje. 20.000 ticket'lık serbest metin veri seti üzerinde arıza türü, cihaz ve zaman analizi yapar; sonuçları yerel LLM ile yorumlar ve bir dashboard üzerinde görselleştirir.

Bu proje bir staj görevi kapsamında geliştirilmiştir.

## Ne Yapar

Serbest metin halinde yazılmış arıza kayıtlarını alır ve şu sorulara cevap üretir:

- Gelen arıza türleri nelerdir?
- En çok hangi arıza türünden ticket açılmaktadır?
- Hangi cihazda (OLT) daha çok arıza gelmiştir?
- Arızalarda yoğunlaşan bir tarih var mı?
- Yukarıdaki analizlere dayanarak olası kök nedenler nelerdir?

Sayısal analiz pandas ile yapılır, yorumlama ise yerel LLM'e bırakılır.

## Mimari

Projenin temel tasarım kararı, deterministik hesaplama ile dil modeli yorumlamasını ayırmaktır. 20.000 kaydın tamamı doğrudan modele gönderilmez; bunun yerine pandas ile hesaplanan özet sonuçlar modele sunulur. Bunun iki nedeni vardır: modelin bağlam penceresi sınırlıdır ve dil modelleri büyük listelerde sayma işlemini güvenilir yapmaz.

```
20k_ariza_ticket.csv
        |
   [analiz.py]  ->  pandas ile kategorize et, say, tarih analizi
        |
   analiz_sonuclari.json
        |
   [yorumla.py]  ->  Ollama / Qwen 2.5 ile yorumla (5 soru)
        |
   llm_yorumlari.json
        |
   [dashboard.py]  ->  Streamlit dashboard
```

| İş | Yöntem |
|---|---|
| Dosya okuma, sayma, gruplama | pandas |
| Kategori tespiti | anahtar kelime eşleştirme |
| Kök neden yorumlama | LLM (Qwen 2.5) |
| Görselleştirme | Streamlit |

## Kullanılan Teknolojiler

- **İşletim sistemi:** FreeBSD 15.1 (VirtualBox üzerinde sanal makine)
- **LLM altyapısı:** Ollama
- **Model:** Qwen 2.5 (7B)
- **Dil:** Python 3.12
- **Kütüphaneler:** pandas, streamlit, ollama

## Kurulum

FreeBSD üzerinde gerekli paketler:

```sh
pkg install python312 py312-pandas py312-streamlit ollama py312-ollama
```

Ollama'yı başlat ve modeli indir:

```sh
ollama serve &
ollama pull qwen2.5:7b
```

## Çalıştırma

Scriptler sırayla çalıştırılır. Her biri bir sonraki adımın kullandığı çıktı dosyasını üretir.

```sh
# 1. Analiz: CSV'yi işler, istatistikleri hesaplar
python analiz.py

# 2. Yorumlama: özet sonuçları LLM'e yorumlatır (CPU'da ~25 dk)
python yorumla.py

# 3. Dashboard: sonuçları görselleştirir
streamlit run dashboard.py --server.address 0.0.0.0 --server.port 9000
```

Dashboard tarayıcıdan `http://localhost:9000` adresiyle açılır.

## Dosya Yapısı

```
analiz.py             CSV analizi, kategorizasyon, JSON çıktısı üretimi
yorumla.py            LLM ile kök neden ve yorumlama
dashboard.py          Streamlit dashboard
analiz_sonuclari.json Sayısal analiz sonuçları (uretilir)
llm_yorumlari.json    LLM yorumları (uretilir)
```

Not: Ticket verisi (`.csv`) ve üretilen JSON dosyaları müşteri bilgisi içerebileceğinden versiyon kontrolüne dahil edilmemiştir.

## Model Seçimi

Yorumlama için önce qwen2.5:3b denenmiş ancak Türkçe üretiminde dilbilgisi hataları ve yabancı karakterler gözlemlenmiştir. qwen2.5:7b modeline geçildiğinde çıktı kalitesi belirgin şekilde iyileşmiştir. İşlem süresi CPU üzerinde artmış olsa da, yorumlama tek seferlik bir işlem olduğundan ve sonuçlar kaydedildiğinden bu tercih edilmiştir.

## Yöntemin Sınırları

Kategorizasyon anahtar kelime eşleştirmesine dayanır; cümlenin anlamını değil, içindeki terimleri kontrol eder. Bir cümlede birden fazla kategori terimi geçtiğinde öncelik sırasıyla çözülür. Ayrıca "arıza nedeni" alanı çoğu zaman kesin kök nedeni değil, gözlemlenen belirtiyi içerir. Daha kesin sınıflandırma için bağlam-duyarlı analiz veya LLM ile tek tek etiketleme yapılabilir, ancak 20.000 kayıt için bu ölçeklenebilirlik açısından uygun değildir.