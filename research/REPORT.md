# Rapor: 3 renkli formation/building puzzle'ında karar derinliğini hangi değişkenler üretiyor?

Kapsam: yalnız solver / simülasyon / level-üretimi araştırması. Oyun tasarımı kararı yoktur; "4 renk daha iyi" veya "kedi iyi, ev kötü" türü bir sonuç **çıkarılmamıştır**.
Model aynı: grid, `E` giriş, `#` duvar, 4-komşuluk, kalıcı dolu hücre, renk seçimi, sabit W, en-derinden-başla yerleşim, tüm hücreleri doldurma.

## Deney seti (tümü paralel; `results/*.csv.gz`)
| Deney | İş | Ne izole ediyor |
|---|---:|---|
| `broad` | 4320 | 8 silüet × **10 renk haritası** × 18 erişim düzeni × 3 dalga kovası (7–10 / 11–15 / 16–20) — dengeli faktöriyel |
| `region` | 4152 | **ablasyon**: silüeti R bölgeye böl, komşu bölgelere farklı renk veren *tüm* boyamalar → parçalanmışlık (R) sabitken yalnız renk sırası değişir |
| `synth` | 4032 | 14 sentetik 8×8/6×6 desen × 18 erişim × W=1…16 (aynı geometri, yalnız renk yapısı) |
| `wsweep` | 3360 | gerçek silüetler, W=1…24 tam tarama |
| `size` | 1152 | aynı renk topolojisi, 16→256 hücre (tam sayı büyütme) |
| `ab4` | 4320 | 3 vs 4 renk, aynı (silüet, CM, erişim, dalga kovası) |
| `refine`, `refine_layout` | 1536+1485 | geniş taramanın en verimli 48/24 bölgesinde W=1…32 ve tek-port erişim komşulukları |
| `broad_delta*` | 3×4320 | MEANINGFUL-SAFE eşiği δ∈{0.02,0.10,0.20} duyarlılığı |

Renk haritaları (algoritmik, rastgele değil): CM1 büyük bitişik bölgeler · CM2 dengeli · CM3 tek baskın + küçük yamalar · CM4 az geçiş (dikey bantlar) ·
CM5 çok geçiş (her komşu farklı) · CM6 aynı renk ≥2 ayrı ada · CM7 halka-derinlikte sıra değişken · CM8 halka-derinlikte sıra sabit · CM9/CM10 satır-derinliğinde sabit/değişken.
Her harita için: renk sayıları, bileşen sayısı, komşuluk, geçiş yoğunluğu, baskın oran, entropi, kümelenme, giriş-derinliği geçişleri, ortalama koşu uzunluğu, derinlik-ağırlıklı geçiş, en derin bölge renk çeşitliliği.

**Karar sınıfları** (kazanan DAG'deki her durum): FORCED (tek yasal hamle) · FREE (kayıp seçenek yok, gelecek riski pratikte aynı) · MEANINGFUL-SAFE (kayıp yok ama seçimler farklı gelecek riski verir, δ=0.05) ·
TRAP (≥2 güvenli + ≥1 kaybettiren) · CRITICAL (tek güvenli, ≥1 kaybettiren). `riskli = TRAP + CRITICAL` (δ'dan bağımsız), `anlamlı = MEANINGFUL-SAFE + TRAP + CRITICAL`.
Beklenenler, güvenli hamleler arasında tekdüze oynayan bir oyuncunun yolu boyunca hesaplanır (yol-sayısı ağırlığı yok → permütasyon şişmesinden arınık). **Karar yoğunluğu** = beklenen sınıf hamleleri / beklenen hamle.
**Puzzle verimi** = greedy ("en derin hücrenin rengini gönder") başarısız **ve** riskli yoğunluk ≥ 0.25 (eşik araştırmacı seçimidir, benchmark değildir).

Doğrulama: motor, eski kutu-kutu uygulamayla 400 rastgele düzende 0 uyuşmazlık; kedi sonuçları önceki doğrulanmış sayılarla birebir.

---

## 1. En güçlü bulgu
**Karar yoğunluğunu asıl belirleyen silüet değil, renk haritasının yapısıdır; erişim geometrisi ise onu etkinleştirir/yükseltir.** (`broad`, çözülebilir n=3921, η²: toplam varyans payı)

| Yanıt | renk haritası | erişim düzeni | silüet | dalga kovası | CM×erişim |
|---|---:|---:|---:|---:|---:|
| riskli karar yoğunluğu | **0.55** | 0.15 | 0.04 | 0.01 | 0.08 |
| anlamlı karar yoğunluğu | 0.24 | 0.22 | 0.01 | 0.00 | 0.20 |
| riskli karar sayısı/oyun | 0.52 | 0.13 | 0.03 | 0.03 | 0.07 |
| greedy başarısızlığı | 0.13 | 0.09 | 0.01 | 0.01 | 0.07 |
| puzzle verimi | 0.23 | 0.07 | 0.01 | 0.01 | 0.09 |

**Nüans (iki rejim):** renk etkisi üç uç haritadan (CM5, CM7, CM8) geliyor. Bunlar çıkarılınca ("ılımlı" haritalar CM1-4,6,9,10; n=3005) riskli yoğunlukta **erişim düzeni baskın olur** (η² 0.32; renk 0.11; CM×erişim 0.16; silüet 0.06).
Yani: (a) parçalı/derinlik-katmanlı haritalar açık meydanda bile karar üretir; (b) bitişik-bölgeli haritalar ancak dar erişimle karar üretir.

**Yapısal aracı değişken:** her rengin tamamı tek seferde gönderildiğinde (W=∞) kaç renk sırasının çözdüğü (`ord_valid_frac`) riskli yoğunlukla r = **−0.79**; yalnız bu ölçü + erişim ailesi R² 0.66 verir (renk istatistikleri 0.59; ikisi 0.77; tüm tanımlayıcılar 0.80).
Sıra sıkılığı: hiçbir sıra çözmüyor → riskli yoğunluk 0.58 (greedy başarısız %51); hepsi geçerli → 0.06 (%8).

## 2. En şaşırtıcı bulgular
1. **Bölge-boyama ablasyonu:** parçalanmışlık (bölge sayısı R) sabitken, renklerin giriş-derinliği boyunca sıralanışı riskli yoğunluğu **değiştirmiyor** (grup-içi r = −0.003, ΔR² = 0.001, n=3211). R = 3 → 16: riskli yoğunluk 0.12 → 0.39, greedy başarısızlığı %9 → ~%40–46.
2. **Bu, sentetik derinlik-katmanlı desenlerle çelişmiyor, daha kesin tanımlıyor:** `rings → rings_alt` (parça sayısı 3.0 → 3.6): 0.14 → 0.37; `rows3 → rows_alt`: 0.25 → 0.41. Belirleyici, geçiş sayısı değil, **aynı rengin derinlikte ayrı yerlerde tekrar etmesi** (renk-sırası sıkılığı 0.17 → 0.06).
3. **Statik tek-hücre baskınlık (dominator) bunu açıklamıyor:** hiçbir renk-seviyesi döngü oluşmuyor, tek başına R² 0.14. Kapanma çok-hücreli (alternatif yolların birlikte kapanması).
4. **Yüksek karar yoğunluğu ≠ puzzle:** dens_risky ≥ 0.25 olan adayların **%59.5'i greedy ile çözülüyor** (CM8'de 229, CM7'de 161 aday). Yoğunluk tek başına yanıltıcı.
5. **Ham çözüm sayısı ~10²·⁶ kat şişiyor** (medyan log10(ham/kanonik) = 2.59; ham medyan 10³·⁸, komütasyon-normal medyan 10¹·¹). Ham≥1000 olanların %32'sinde kanonik ≤10.
6. **Çözülebilirlik de renk yapısının işlevi:** CM5 adayların yalnız %26'sı çözülebilir (W=1'de %94, W≥10'da %0); sentetik `checker3/diag3` %32–34, `mrf0` %52.

## 3. Geometrinin (erişim) etkisi
Aile ortalamaları (çözülebilir): riskli yoğunluk / greedy başarısızlığı — BOTTLENECK 0.35/%33 · SPLIT+BOTTLENECK 0.27/%36 · CORRIDOR 0.27/%19 · MULTI 0.18/%21 · SPLIT 0.18/%12 · **OPEN 0.12/%3**.
Etkileşim (riskli yoğunluk):

| | OPEN | CORRIDOR | BOTTLENECK | SPLIT | SPLIT+BOTT. | MULTI |
|---|---:|---:|---:|---:|---:|---:|
| CM1 (bitişik bölgeler) | 0.00 | 0.17 | 0.33 | 0.04 | 0.16 | 0.07 |
| CM3 (tek baskın) | 0.02 | 0.05 | 0.15 | 0.03 | 0.09 | 0.04 |
| CM7 (derinlikte değişken) | 0.39 | 0.54 | 0.55 | 0.46 | 0.53 | 0.48 |
| CM8 (derinlikte sabit) | 0.37 | 0.46 | 0.53 | 0.40 | 0.46 | 0.41 |
| CM5 (her komşu farklı) | 0.45 | 0.81 | 0.78 | 0.63 | 0.69 | 0.67 |

Dar erişim sıkıcı bir haritayı kurtarabilir (CM1: 0.00 → 0.33) ama zengin bir haritanın tavanına ulaştırmaz. Erişim komşuluk taraması (`refine_layout`): en iyi 24 bölgenin tek-port değişimlerinde verim ort. %72; BOTTLENECK %95, SPLIT+BOTT. %90, CORRIDOR %81, MULTI %74, SPLIT %65.

## 4. Renk haritasının etkisi
| CM | riskli yoğunluk | greedy başarısız | çözülebilir | baskın karar sınıfı payı |
|---|---:|---:|---:|---|
| CM5 | 0.66 | 46% | 26% | crit .40 + trap .26 |
| CM7 | 0.50 | 49% | 86% | crit .28 + trap .22 |
| CM8 | 0.44 | 44% | 100% | trap .22, crit .22, meansafe .32 |
| CM10 | 0.25 | 29% | 96% | — |
| CM6 (ayrı adalar) | 0.16 | 18% | 100% | meansafe .41 |
| CM9 / CM2 / CM1 / CM4 | 0.16 / 0.16 / 0.14 / 0.14 | ~%10–11 | 100% | free ~.36–.39 |
| CM3 (tek baskın) | 0.065 | 19% | 100% | **forced .54** |

## 5. Renk geçişinin etkisi
Ham geçiş istatistikleri (giriş-derinliğinde geçiş/hücre, derinlik-ağırlıklı geçiş, koşu uzunluğu) riskli yoğunlukla ilişkili (geçiş/hücre için r = 0.38) ama **parçalanmışlık bilindiğinde ΔR² ≈ 0.03**, bölge-ablasyonunda grup-içi r ≈ 0. Yani "geçiş sayısı" nedensel değişken değil; asıl mekanizma aynı rengin ayrı derinliklerde tekrarıdır (madde 2.2) ve `ord_valid_frac` ile ölçülür. Ön-bilgi: bu ikisini tam ayıran tasarım (renk-sırası sıkılığını doğrudan hedefleyen ters tasarım) henüz yapılmadı.

## 6. Renk kümelenmesinin (parçalanmışlığın) etkisi
Tüm tanımlayıcılar birlikte: en büyük tek-tek-çıkarma ΔR² `cm_clustering` (std β −0.89; 0.09); gradient boosting permütasyon önemi `comp_per_cell` > `cm_clustering` > `ent_meandepth`.
Doz-yanıt: bölge sayısı R=3/4/6/8/12/16 → riskli yoğunluk 0.12/0.18/0.18/0.26/0.36/0.39; riskli karar sayısı 1.3/2.0/1.9/2.9/3.9/4.2; greedy başarısızlığı %9/20/12/28/47/40. Sentetik MRF (yumuşatma 0→8): parça 22.9 → 2.7, riskli yoğunluk 0.58 → 0.18, çözülebilirlik 0.52 → 0.99.
**Bedeli:** parçalanma arttıkça çözülebilirlik düşer (R=16: %89).

## 7. W'nin etkisi
- **W=1'de greedy her zaman çözer** (n=205, hiçbir istisna; W=1 her zaman çözülebilir). Miktar serbest olsaydı optimal strateji bu olurdu → W sabit olmalı (oyun kararına dokunmadan, araştırma bulgusu).
- Ortalama yoğunluk W ile artar (0.16 → 0.36) ama **oyun başına riskli karar sayısı düşer** (11.2 → 1.6): yoğunluk–sayı değiş-tokuşu.
- **Monoton değil:** 210 (silüet,CM,erişim) serisinin %90'ı W boyunca ≥1, %86'sı ≥2 yön değiştirir; yalnız %31'i tam monoton artan; medyan Spearman 0.90. Çözülebilirlik de monoton değil (çözülebilir→çözümsüz 115, geri dönüş 72 geçiş). CM5: W=1'de %94 çözülebilir, W≥10'da %0; CM3 tersine W ile artar (0.05 → 0.20).
- Etkileşim: CM×W η² 0.07; erişim×W 0.003; silüet×W 0.006.
- **Dalga normalizasyonu** (W'den bağımsız kıyas): dalga ≤6 / 7–10 / 11–15 / 16–20 / 21–30 / 31–60 / >60 → riskli yoğunluk 0.36 / 0.28 / 0.30 / 0.29 / 0.27 / 0.22 / 0.16; riskli karar sayısı 1.9 / 2.4 / 4.0 / 5.2 / 6.5 / 8.6 / 12.6. Uzun oyunlar yoğunluğu seyreltir ama sayıyı artırır.
- Yüksek çözünürlük (`refine`, 48 bölge × W=1…32): her bölgede greedy'nin başarısız olduğu W var (%100); verimli W penceresi medyan 11 W geniş; pencere içinde ortalama 0.88 "delik" (%62 bölgede delik yok). Zirve riskli karar sayısı genelde küçük W'de (medyan W=3) ve uzun oyunda (medyan 22 dalga). *Seçilmiş bölgeler olduğundan iyimser (winner's curse).*

## 8. Görüntü boyutunun etkisi
- **Sabit dalga sayısında** hücre ×4: riskli karar +0.43 (p<1e-16), riskli yoğunluk +0.027, FREE −0.15 (anlamsız), **greedy başarısızlığı +0.20** (%29 → %48). Sentetik 16 → 256 hücre (8 dalga): anlamlı karar 3.6 → 3.4 (değişmez), riskli 1.38 → 1.61.
- **Sabit W'de** hücre 51 → 101: riskli karar 4.1 → 6.1 ama FREE 3.5 → 8.2; yoğunluk 0.23–0.34 bandında, hücreyle monoton artmıyor (W=4'te en büyük sınıf 0.23). Yani hem karar hem serbest hamle artıyor, serbest hamle daha hızlı.
- log-log regresyon (riskli karar): esneklik hücre **−0.27**, dalga sayısı **+0.65**. Sonuç: karar sayısını belirleyen hamle (dalga) sayısıdır; resmin büyümesi tek başına karar eklemez, sabit dalgada yalnız hafif risk ve greedy başarısızlığı ekler.

## 9. 3 vs 4 renk (eşleşmiş 1906 çift, aynı dalga kovası)
| | k=3 | k=4 | fark (%95 GA) |
|---|---:|---:|---|
| riskli karar/oyun | 2.97 | 4.15 | +1.18 (1.11–1.25) |
| TRAP | 1.44 | 2.60 | +1.16 |
| CRITICAL | 1.53 | 1.55 | +0.015 (−0.03–0.06) |
| riskli yoğunluk | 0.224 | 0.311 | +0.087 |
| FORCED / FREE / MEANSAFE | 2.59 / 3.71 / 4.03 | 2.15 / 3.32 / 3.80 | −0.45 / −0.39 / −0.23 |
| rastgele kazanma | 0.49 | 0.40 | −0.09 |
| greedy başarısızlığı | 0.21 | 0.31 | +0.10 |
| max regret | 1.17 | 1.40 | +0.23 |
| rec2 | 0.995 | 0.995 | 0 |
| çözülebilirlik | 0.904 | 0.895 | |

**Yorum (sınırlı):** ölçülen artış, aynı algoritmaların 4 renkte daha parçalı/sıkı haritalar üretmesinden geliyor: renk yapısı + sıra sıkılığı kontrol edilince k etkisi riskli karar için +0.07 (p=0.34), TRAP için +0.34, CRITICAL için **−0.27**. 4. renk esas olarak "yanlış seçenek" (TRAP) ekliyor, "tek doğru" (CRITICAL) eklemiyor. Bunun oyuncu açısından daha anlamlı karar olduğuna dair veri **yok**; "4 renk daha iyi" sonucu çıkarılmamıştır. Erişime göre fark: BOTTLENECK +1.81, CORRIDOR +1.31, SPLIT+BOTT. +1.24, MULTI +0.97, SPLIT +0.73, OPEN +0.65 riskli karar.

## 10. Hangi kombinasyonlar gerçekten puzzle üretiyor?
Puzzle verimi (greedy başarısız & riskli yoğunluk ≥ 0.25), genel %16.3:

| | BOTTLENECK | CORRIDOR | MULTI | OPEN | SPLIT | SPLIT+BOTT. |
|---|---:|---:|---:|---:|---:|---:|
| CM5 | 0.80 | 0.71 | 0.62 | 0.00 | 0.29 | 0.40 |
| CM7 | 0.62 | 0.49 | 0.39 | 0.08 | 0.40 | **0.78** |
| CM8 | 0.68 | 0.44 | 0.45 | 0.12 | 0.24 | 0.47 |
| CM10 | 0.44 | 0.19 | 0.13 | 0.00 | 0.00 | 0.58 |
| CM1/2/3/4/9 | ≤0.15 | ≤0.06 | ≤0.03 | 0 | ≤0.04 | ≤0.17 |

Verimli adaylarda (n=640): medyan 6.0 riskli karar/oyun, yoğunluk 0.50, ilk-hamle-tuzağı %13, regret≥3 %25; rastgele oyuncu undo 0/1/2 ile %8.6 / %21 / %34 kazanır. Tüm adaylarda: ilk-hamle-tuzağı %2.6, rec1 0.96, rec2 0.994, regret≥3 %6.9 → tuzaklar çoğunlukla hemen görünür.

## 11. "Çok hücre ama az karar"
- **OPEN × {CM1, CM2, CM3, CM4, CM9, CM10}:** ortalama 73 hücrede riskli karar 0.04–0.30/oyun (yoğunluk ≤0.02). ≥90 hücrede (tavşan, manzara) OPEN: CM1 0.20, CM9 0.00, CM3 0.12 — aynı boyutta OPEN×CM5 **8.6**, CM7 4.2.
- SPLIT/MULTI × CM1–CM3: ~0.4–1.0 riskli karar; CM3'te hamlelerin **%54'ü FORCED**.
- Hücre sayısı tek başına karar vermez (madde 8); karar sayısını dalga sayısı ve renk yapısı belirler.

## 12. Level-üretici ana eksenleri olabilecek değişkenler (veri destekli)
1. **Renk yapısı** — parçalanmışlık (ayrı parça sayısı/hücre) ve **renk-sırası sıkılığı** (W=∞'da geçerli sıra payı). En büyük etki; ters tasarımla doğrudan hedeflenebilir (henüz denenmedi).
2. **Erişim ailesi/port geometrisi** — özellikle ılımlı renk haritalarında belirleyici (η² 0.32); BOTTLENECK ve SPLIT+BOTTLENECK en verimli.
3. **Dalga sayısı (W'nin resim boyutuna göre türetilmiş hâli)** — karar *sayısını* ve oyun uzunluğunu belirler; W tek başına monoton değil, çözümle solver seçmeli.
4. **Çözülebilirlik bekçisi** — parçalanmış haritalarda W küçük olmalı; her (harita, erişim) için geçerli W aralığı solver'la bulunmalı.
5. (Belirsiz) renk sayısı — etkisi yapı kontrolüyle zayıflıyor (madde 9).

## 13. Dekoratif / düşük etkili değişkenler
Silüet kimliği (η² 0.04; puzzle veriminde 0.014; aynı CM+erişim+bin'de silüet değişince ortalama aralık 0.29 ama **yeni davranış türü eklemiyor**, madde 14) · dalga kovası (yoğunlukta η² 0.009; sayılarda 0.19) · sabit dalgada hücre sayısı · ham geçiş sayısı (parçalanma bilinince) · ham çözüm sayısı (şişmiş) · eşik δ (riskli yoğunluk δ'dan **bağımsız**; anlamlı yoğunluk 0.56 → 0.39 değişir, η² sıralaması korunur, r = 0.90).

## 14. 100+ level kapasitesine ne kadar güveniyoruz? — **orta–düşük güven, tanım-koşullu**
- Ham sayı: 3921 çözülebilir adayda **461 farklı bileşik davranış imzası** (etkin sayı 158, Chao1 ≈ 680). Ama boyutlara göre çeşitlilik küçük: karar profili 43 (etkin 20.6), tuzak zamanı 6 (3.5), regret 6 (3.3), çözüm-sırası 3 (3.0). Bileşik sayı bu küçük boyutların çarpımıdır.
- **Rarefaction doymuyor:** 25 → 21, 100 → 67, 400 → 164, 1600 → 322, 3200 → 426 imza. Yalnız kedi ile (aynı örnek büyüklüğünde) tüm silüetler kadar imza elde edilir (161 vs 164 @400) → **silüetler yeni davranış türü eklemiyor**, yalnız yeni örnek ekliyor. Yalnız OPEN erişim en düşük çeşitlilik (etkin 25).
- ε-paketleme (14 özellikli davranış vektörü, PCA: %90 için 6 bileşen): ε=0.9 → ~123 temsilci, ε=0.4 → ~930 (yarı örnekte 650; doymamış). Silüet sayısı 1→8 iken ε=0.4 temsilci 203 → 932 (azalan getiri); renk haritası sayısı 1→10 iken 107 → 932; erişim düzeni 1→18 iken 74 → 932.
- Tek faktör değişirken (diğerleri sabit) bağlam başına farklı imza: erişim 12.4 · renk haritası 8.3 · W 7.2 · silüet 6.2 · dalga kovası 2.3.
- İmza sayısı bucket şemasına çok duyarlı (aynı veride şemaya göre 143 / 313 / 461). Bu yüzden **"100+ kesin" denemez**. Savunulabilir olan: renk-yapısı × erişim × W eksenlerinde, kaba çözünürlükte (ε=0.9) yüzlerce solver-ayırt edilebilir davranış var; bunların **oyuncu tarafından** farklı algılandığı test edilmedi; silüet tek başına çeşitlilik kaynağı değil; faktörlerin bağımsız davranış ürettiği gösterilmedi (etkileşimler büyük: CM×erişim 0.08–0.20).

## 15. Sonraki deney önerisi
1. **Ters tasarım:** renk haritasını doğrudan hedef (parçalanmışlık, `ord_valid_frac`) değerlerine göre üret (örn. tavlama) ve hedefin tutturulma oranını + karar yoğunluğunu ölç → "renk yapısı ana eksen" iddiasını doğrudan sına.
2. **Çok-hücreli (cut-set) baskınlık** tanımlayıcısı: tek-hücre baskınlığın kaçırdığı yol-kapanma yapısını ölç; `ord_valid_frac`'in neden çalıştığını açıkla.
3. **Erişim × renk dik ablasyonu:** aynı renk-sırası sıkılığında erişim ailesini değiştir.
4. **İnsan testi** (en önemli): verimli adaylar (n=640) içinden farklı imzalardan 20–30 level; "farklı mı hissettirdi?" ve greedy-dışı çözüm.
5. 4 renk: eşleştirilmiş *yapı* (aynı parçalanma ve sıra sıkılığı) altında tekrar; TRAP/CRITICAL bileşimini ve oyuncu-ayırt edilebilirliğini ölç.
6. Undo yalnızca simülasyon parametresi kalsın: bulgu olarak, verimli adaylarda rastgele oyuncu için 0/1/2 undo = %8.6/%21/%34; kısa oyunlarda etkisi daha büyük.

---
## Sınırlar ve kapsam dışı
Silüetler elle parametrize, tek maske başına; renk haritaları 10 algoritmik aile; tek yerleşim kuralı (deepest-first); koşullu analizler çözülebilir adaylarla sınırlı (CM5'in %74'ü dışarıda); imza/verim eşikleri (δ=0.05, dens≥0.25, bucket'lar) araştırmacı seçimi;
regresyonlar açıklayıcıdır — nedensel kanıt yalnız bölge-boyama ablasyonu ve sentetik kontrastlardadır. `seq_canon` komütasyon-normal form sayısıdır (iz-sınıfı sayısının üst sınırı). "Regret" = hata sonrası kaç undo gerektiği; oyuncunun hatayı fark edebilirliği ölçülmedi.
