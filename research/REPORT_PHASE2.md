# Faz 1 + Faz 2: Gemini benchmark analizinin ayıklanması, solver metrik yükseltmesi ve profil karşılaştırması

Kapsam: yalnız solver/simülasyon. Yeni level taraması **yapılmadı**: daha önceki `broad` (4320) ve `size` (1152) adayları *aynı ızgaralarla* yeni metriklerle yeniden çözüldü (eski sayılar birebir tutuyor: max |Δ| ≈ 1e-16, greedy farkı 0).
Oyun tasarımı kararı verilmedi; benchmark sayıları hedef olarak solver'a sabitlenmedi.

---
## 1. Gemini raporunun ayıklanması (`benchmark_reference.json`)
Raporun kendisi üç oyun için de "gözlemsel tersine mühendislik" diyor: telemetri yok, kesin veri yok. Bu yüzden her iddia güven sınıfına ve **bizim modele taşınabilirliğe** göre ayrıldı.

| Kullanım | İddialar |
|---|---|
| **Referans zarfı, A (ağırlık 1.0)** | etkin eylem uzayı 3–8 · kritik karar/seviye 6–12 · hata farkındalığı 3–5 hamle sonra · "anında ölüm yok" (sayısal sınır bizim operasyonelleştirmemiz, raporda sayı yok) |
| **Referans zarfı, B (0.5)** | toplam hamle 15–80 · dolgu oranı ~%70–80 · tuzak zamanı %40–60 |
| **Bağlam / henüz ölçülmedi** | renk sayısı ilerlemesi (3→4–5→5–6) · bağımlılık zinciri derinliği 4–7 · 20–30. seviyede yeni mekanik · rastgele kazanma eğrileri |
| **Hipotez, insan testi şart (C)** | tersine akış (inşa "pozitif" görünür → yol kapamayı fark etme gecikir mi) · sabit dalga hissi · iskele/buffer gömme |
| **Taşınamaz, dışarıda** | tampon 5–7 slot, **Buffer Saturation Index**, üssel hata maliyeti (bizde tampon yok) |

İşaretlenen iç tutarsızlıklar: (i) "ideal H = 3–5" aynı raporun *gözlenen* gecikmesidir; gözlemden normatif ideale geçiş döngüsel → normatif değil karşılaştırma zarfı. (ii) Üç oyunun sayıları farklı eylem birimlerini karıştırıyor (nesne / konveyör yuvası / serbest blok; bizde eylem = renk ≤ 3). (iii) "~%75", "~8/45" gibi değerler nokta tahmindir.
Zarf: çekirdek [lo, hi]; toleranslı = her uçta genişliğin %25'i (boyuta özgü asgari pay ile). Hiçbir sayı kabul/ret eşiği değildir.

## 2. Eklenen metrikler (tanımlar ve dürüst karşılıklar)
Beklentiler, güvenli hamleler arasında tekdüze oynayan yol (kütle π) üzerinden; hata ağırlığı = π(s)/|yasal(s)| (başka türlü güvenli oynayan oyuncunun orada yanlış seçme olasılığı).

1. **Deadlock Horizon (DH)** — hatalı hamle dahil, kilitlenmenin (erişilemez hücre) belirdiği hamle sayısı. `dh_min` (en hızlı), `dh_exp` (rastgele devam altında beklenen), `dh_max`; `dh_instant_share` (DH=1 hata payı), `dh_band35_share`.
2. **Path / Construction Pressure** — *Buffer Saturation'ın karşılığı değildir.* Tanım: boş hedef hücrelerin **kilitli payı** (doldurulursa başka bir boş hedefi koparan hücreler / boş hücre): `pp_locked_mean/max`, ilerlemeyle korelasyon. Kullanıcı tanımı ("%40 tamamlandı, kritik geçitlerin %80'i kapanmış") ayrıca ölçüldü: `closure_at_40pct`.
3. **Meaningful Branching Factor** — görünür seçenek (yasal renk), güvenli seçenek, *anlamlı* seçenek (güvenli hamlelerin gelecek-risk olasılığı ≥0.05 farkla kümelenmesi), kritik durumlarda Critical Path Ratio = güvenli/yasal.
4. **Active Bottleneck Count (ABC)** — Cooper-Harvey-Kennedy baskınlığıyla canlı dar boğazlar: başka bir boş hedefe giden tüm girişlerin geçtiği boş hedef hücre sayısı. Ayrıca eşzamanlılık (≥3 payı), yol başına farklı dar boğaz sayısı, erken/orta/geç profil. **Kaba kuvvetle doğrulandı** (`tests/test_dominators.py`: 2781 durumda 0 uyuşmazlık).
5. **Filler-to-Decision** — `filler_ratio = 1 − riskli/toplam hamle`, `filler_strict = (FREE+FORCED)/hamle`, `filler_to_decision`.
6. **Decision Recovery Visibility — yalnızca yapısal vekiller** (UI'yi ölçmez): `dh_instant_share` (tehlike aynı hamlede görünür mü), `blind_progress` (hatadan kilitlenmenin görünmesine dek tamamlanan resim payı), `latent_doom_mass` (oyun başına beklenen gecikmeli-hata sayısı).

İstenen seviye-başı çıktılar: `results/phase2_per_level.csv.gz` (48 sütun: total waves, meaningful/critical/forced/risky, deadlock horizon, max path pressure, ABC, filler, regret, greedy, + yukarıdakiler).

## 3. Faz 1 sonuçları (3921 çözülebilir aday)
| Metrik | ortalama | medyan (p10–p90) | puzzle-verimi adaylarında (n=640) |
|---|---:|---|---:|
| görünür / güvenli / anlamlı seçenek | 2.36 / 2.07 / 1.60 | görünür 2.43 | 2.51 / 1.82 / 1.43 |
| CPR (kritik durumlarda güvenli/yasal) | 0.56 | — | 0.53 |
| **DH beklenen** | **1.07** | 1.00 (1.00–1.20) | 1.29 |
| hata kütlesinin **aynı hamlede** kilitlenen payı | **0.913** | 1.00 (0.87–1.0) | 0.85 |
| kör ilerleme (hata→kilit görünene dek resim %) | 0.087 | 0.082 | 0.110 |
| ABC ort / tepe | 1.41 / 7.1 | ort 1.21 | 2.20 / 9.5 |
| eşzamanlı ≥3 dar boğaz payı | 0.20 | 0.16 | 0.33 |
| yol başına farklı dar boğaz | 7.4 | 6.9 | 11.0 |
| kilitli pay tepe (path pressure) | 0.40 | 0.39 | 0.44 |
| dolgu oranı | 0.767 | **0.82 (0.46–1.00)** | 0.47 |
| riskli karar / oyun | 3.08 | 2.23 | 6.64 |

**Bulgular**
- **Hata gecikmesi bizde neredeyse yok:** hata kütlesinin %91'i aynı hamlede kilitlenme üretiyor; DH_exp ∈ [3,5] olan hata payı %1; bu bantta ≥%10 kütlesi olan aday %3.2. Gecikmeli hata (%8.7) ağırlıkla parçalı/derinlik-katmanlı renk haritalarında (latent_doom/oyun: CM5 1.16, CM7 0.49, CM8 0.24; diğerleri ≈0). DH'nin sürücüsü renk haritası (η² 0.16–0.21), erişim değil (0.03).
- **"Kör ilerleme" hatalı dalganın kendi ilerlemesi:** kör ilerleme ≈ 1/dalga (Spearman 0.84; ortalama fark +0.006). Yani tersine-akış hipotezinin yapısal kısmı (inşa ederken tehlike gecikmeli görünür) çoğu hatada geçerli değil: tehlike aynı hamlede oluşuyor. Geriye kalan soru **algısal**: oyuncu o anda bunu *anlıyor mu* (UI); solver bunu ölçemez.
- **Kapanış (kullanıcı tanımı) kazanan yolda yapısal olarak sıfır:** `closure_at_40pct` = 0, `closure_lead_max` = 0. Kritik geçit, bağımlıları dolmadan kapanırsa zaten kilitlenme (kayıp) demektir; dolayısıyla "%40 ilerleme, %80 geçit kapalı" ancak *hatalı dalda* vardır ve orada anında kilitlenme olarak görünür. Anlamlı ölçü: `latent_doom_mass` ve `blind_progress`.
- **Path pressure (kilitli pay)** ilerlemeyle artıyor (corr medyan 0.50) ve **ölçekle bağımlı** (normalize payda boş hücre sayısı: hücre arttıkça 0.11 → 0.01). Ölçek karşılaştırmasında sayı olan **ABC** kullanılmalı (hücreyle corr 0.11). Hazard–ilerleme korelasyonu zayıf (medyan 0.12; %65 pozitif): gerilim birikimi çoğu seviyede belirgin değil.
- **ABC bir geometri metriği:** η²: erişim 0.34, silüet 0.15, renk 0.15 (karar yoğunluğunda ise renk 0.55, erişim 0.15). OPEN 0.50, BOTTLENECK 2.04, SPLIT+BOTT. 1.98. Orta-oyun tepesi: erken/orta/geç = 0.62/2.12/1.50 (Gemini'nin %40–60 tuzak gözlemiyle niteliksel uyumlu).
- **"Dallanma/bottleneck belirliyor" çıkarımı kısmen düzeltilmeli:** ABC tek başına (erişim ailesiyle) dens_risky'nin R²'sini 0.09 → 0.33 yapar (ρ=0.61), ama **renk yapısı bilindikten sonra yalnız +0.015** (riskli sayı +0.02; greedy başarısızlığı +0.014). Bottleneck sayısı kararlarla ilişkili ama onları belirleyen, bu dar boğazların *hangi renklerle* çakıştığıdır (renk yapısı/sıra sıkılığı). Örnek: OPEN×CM5'te ABC ≈ 0.5 iken riskli karar 7.2. "Kutu sayısı değil yapı belirliyor" kısmı ise doğrulandı (sabit dalgada hücre ×4 → ABC değişmiyor, riskli karar +0.4).
- **Filler oranı iki modlu:** ortalama 0.767 zarfa (0.70–0.80) tesadüfen denk ama p10 0.46 / p90 1.00: adayların ~%40'ı neredeyse hiç karar içermiyor (filler ≈ 1), puzzle-verimi adaylarında 0.47. **Ortalama zarf içinde olması seviyelerin zarf içinde olduğu anlamına gelmez.**
- **Metrik örtüşmesi:** `dh_instant_share ≡ rec1` (Spearman 1.00); `filler_ratio = 1 − dens_risky` (tanım gereği −1.00) → Filler-to-Decision yeni bilgi eklemiyor, karar yoğunluğunun takma adı. ABC/pp_locked/abc_ge3 birbirine 0.87–0.96. 13 metrikte %90 varyans için 5 bileşen: bağımsız bilgi ≈ {karar yoğunluğu, gecikme(DH), bottleneck geometrisi, dallanma kalitesi (MBF/CPR), ~1/dalga olan kör ilerleme}.

## 4. Faz 2: bizim profil ↔ filtrelenmiş zarf (hedef değil)
| Boyut (sınıf) | bizim medyan (p10–p90) | çekirdek payı | toleranslı payı |
|---|---|---:|---:|
| eylem uzayı (A) `visible_mean` | 2.43 (1.8–2.6) | 0.000 | 0.92 |
| kritik karar (A) `e_risky` | 2.23 (0–7.3) | 0.16 | 0.28 |
| kurtarma mesafesi (A) `dh_exp` | 1.00 (1.0–1.2) | 0.002 | **0.018** |
| anında kayıp yok (A) `dh_instant` | 1.00 | 0.002 | 0.002 |
| toplam hamle (B) `e_moves` | 13 (9–18) | 0.35 | (zarf geniş) |
| dolgu (B) | 0.82 (0.46–1.0) | 0.11 | 0.25 |
| tuzak zamanı (B) | 0.54 (0.38–0.69) | 0.57 | 0.76 |

- Üç A boyutunun **hepsi** toleranslı zarfta: **50 aday (%1.3)**. Kurtarma-mesafesi hariç tutulursa %27.6 (1083 aday). Yani profili zarftan ayıran tek baskın boyut **hata gecikmesi**.
- Eylem uzayı yapısal olarak ≤3 (renk sayısı); toleranslı %92 payı zarfın genişliğinden, çekirdekte (3–8) hiçbir aday yok. Anlamlı kıyas Pixel Flow 2–4 yuvasıdır.
- **Zarfa yakınlık yine renk yapısıyla belirleniyor:** toleranslı kapsama CM7 0.53, CM8 0.52, CM5 0.50 … CM3 0.22; erişim aileleri 0.41–0.44, silüetler 0.41–0.45, dalga kovaları 0.41–0.44. Puzzle verimi adaylarında kapsama 0.52 (A-toleranslı 0.45; kritik karar zarfta %73, DH zarfta %9, dolgu zarfta %15, tuzak zamanı zarfta %88).
- Tuzak zamanı medyanı 0.54 (zarf içinde) ama son üçte birde hâlâ %32 riskli durum var (Gemini'ye göre son %20'de tuzak yok; bizim üçte-bir bölmemizle birebir kıyas değil).
- **DH ≥ 2 olan yalnız 61 aday (%1.8)**: CM7/CM10/CM8 × SPLIT+BOTTLENECK/MULTI; ortalaması riskli karar 6.96, yoğunluk 0.61, greedy başarısızlığı 0.95, rec1 0.47. Yani uzun gecikme parçalı/katmanlı renkler + çok-cepheli erişimde nadiren doğuyor; şu anki üretim uzayı bunu **rutin olarak üretmiyor**.

**"Hamle 7 → 11" örneği ve iki aşırılık:** "anında fail çok sert, 14 hamle sonra fail çok kopuk" sezgisi için veri: mevcut aile ağırlıkla ilk uçta (hata kütlesinin %91'i anında) ve undo=1 hataların %96'sını kurtarıyor (`rec1`). Uzun hata yolları *mevcut* ama düşük olasılıklı: adayların %24'ünde en az bir hata yolu ≥3 hamle, %11'inde ≥6, %2'sinde ≥10 hamlede kilitleniyor; fakat hata kütlesiyle ağırlıklandırınca ortalama en-uzun-yol ≥3 olan aday yalnız %1.6. Orta bölge (3–5 beklenen) ~%1. Bu bir "yanlış" değil, bir *konum tespiti*: hangi bölgenin oyuncu için iyi olduğu insan testi sorusudur.

## 5. 244 kutuluk kedi için
Prototipin ızgarası elimizde yok; en yakın proxy kedi ×2 (216 hücre, n=24): riskli karar 3.54 (54 hücrede 3.88), ABC 1.40 (1.73), DH 1.31 (1.09), dolgu 0.66 (0.64). **Hücre sayısı (54→216) hiçbir metriği anlamlı değiştirmiyor** (sabit dalga kovasında: hücre 40→500 arası riskli karar 1.4→3.6 yavaş artış, ABC ≈ 1.5 sabit). Prototip ızgarası verilirse doğrudan aynı metriklerle ölçülür.

## 6. Kullanıcı çıkarımlarının durumu
1. *"Yüzlerce kutu problem değil; karar dallanma/bottleneck yapısıyla belirleniyor"* — **büyük ölçüde destekleniyor**, bir düzeltmeyle: yapı = renk yapısı × erişim; ABC tek başına belirleyici değil (renk yapısı bilinince +%1.5).
2. *"Her wave karar olmak zorunda değil"* — destekleniyor; ama filler dağılımı iki modlu (%40 seviye ≈ karar yok), ortalama yanıltıcı.
3. *"Asıl tehlike ilerlerken yolu kapamak"* — **yapısal kısmı çoğu hata için desteklenmiyor** (%91 aynı hamlede kilitlenme; kör ilerleme = hatalı dalganın kendisi). **Algısal kısmı** (oyuncu hemen fark edip nedenini anlıyor mu) ölçülmedi ve solver ölçemez → insan testi.
4. *"Yeni 5000 level taraması yerine metrik yükseltmesi"* — yapıldı; yeni bilgi büyük: DH ve ABC ayrı bilgi taşıyor.
5. *"3 renk kalsın"* — bu çalışmada renk sayısı değişmedi; önceki bulgu (4. renk yapıdan bağımsız ek karar getirmiyor) geçerli.
6. *"Solver'ın farklı demesi insanın farklı hissettiği değildir"* — katılıyoruz; Faz 1 yeni metrikler çeşitlilik *kapasitesini* artırmıyor, yalnızca ölçüm boyutu ekliyor.

## 7. İnsan testi için (tasarım kararı değil, ölçülecek şeyler)
Verimli adaylardan (greedy başarısız, riskli yoğunluk ≥0.25) **DH'ye göre katmanlı** 20–30 level: (a) DH=1 baskın, (b) `latent_doom` > 0 (n=61), (c) zarfa en yakın. Her hatada sorulacak: hata anında neyi fark etti, nedenini söyleyebildi mi, kaç hamle sonra; "ilerliyorum" hissi ile kilit arasındaki çelişki; undo kullanımı. Bu, Decision Recovery Visibility'nin UI ayağını ilk kez ölçer.

## 8. Sınırlar
- Tüm DH/kilit tanımları **geometrik**; oyuncunun algısını ölçmez. DH "erişilemez hücre oluşması" demektir (UI bunu göstermeyebilir/erken gösterebilir).
- Zarf gözlemsel ve farklı eylem birimleri; toleranslı pay zarfın genişliğine ve asgari paylarına bağlı. `total_moves` toleransı anlamsız derecede geniş (alt sınır negatif) → o boyut bilgi taşımıyor.
- `closure` tanımı kazanan yolda yapısal olarak sıfır; bu bir bulgu, ama kullanıcının kavramını başka bir ölçüyle (blind_progress/latent_doom) değiştirmek zorunda kaldık.
- pp_locked ölçek-bağımlı; ölçek kıyaslarında ABC (sayı) kullanılmalı.
- Seçilen 10 renk haritası/8 silüet/18 erişim uzayı dışı genelleme yok; bağımlılık zinciri derinliği (Gemini §7) henüz ölçülmedi.
