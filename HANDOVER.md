# HANDOVER — Block Image prototipi (devir teslim)

Hazırlanma: oturum sonu. Repo: `kucukates68/trial`, çalışma dalı `claude/festive-einstein-dba11b` (PR açılmadı; her adım commit + push edildi). Ana klasör: `prototype/block-image-01/`.
Bu dosya yeni bir Claude projesine/oturumuna **tek başına yeter** diye yazıldı. Önce bölüm 0'ı, sonra 9'u (açık kararlar) oku.

---
## 0. Bir sayfada özet
**Oyun:** Mobil tarzı "yerleştirilen parçalarla resim oluştur" bulmacası. Oyuncunun önünde 3 kart (parça) var, birini seçer, işçiler parçayı kendi sabit hedefine taşır, yerleşen bloklar **kalıcı engel** olur, resim parça parça oluşur. Karar yalnız *hangi kartı şimdi göndereceği*. Boş bir hedef hücre girişten erişilemez hâle gelirse (mühür/sealed) kaybedilir.
**Çekirdek donmuş (değişmez):** 3 slotlu el, her slotun sabit gizli kuyruğu, her parçanın tek sabit hedefi, BFS erişimi, kalıcı hücre, erişim kapanması = kayıp, worker yalnız görsel. Yeni mekanik/kaynak/booster/puan yok.
**Şu anki ana sonuç (kanıtlı):** Fail mekanizması çalışıyor; problem *yanlış seçim olasılığının düşük olması*. Zorluk parça sayısından/küçüklüğünden gelmiyor. Geometri zaten tehlikeli (rastgele sırada kalan parçaların %42–56'sı tuzak); kuyruk sıraları bu tehlikeyi siliyordu. **En etkili kaldıraç = kuyruk sırası** (kapı kartı kurbanından önce ele gelsin), geometri tavanı belirler.
**Son iki deney (oynanabilir):** `L01-V4` (L01'in yalnız queue'su değişti: yanlış/hamle %6.4→%22.4, yanlışların hepsi yerel) ve `L02-V2` (kaktüs, "yol geçişi": %28.4, dar geçit olayları %59). **İnsan testi hiç yapılmadı** — bütün "okunur/anlaşılır" iddiaları çıkarımdır.
**İlk iş (öneri):** kullanıcı L01-V4 ve L02-V2'yi oynayıp geri bildirim verecek; L03'te ne ekleneceği ancak o zaman belirlenecek (kullanıcının açık talimatı).

---
## 1. Oyun kuralları (motor: `src/engine.js`, referans: `tools/ref.py`)
- Izgara: `#` duvar, `.` zemin (kullanmıyoruz), `E` giriş, harf/`a` = hedef hücre (resmin bir bloğu). 4-komşuluk. Yürünebilir = zemin + giriş + **boş** hedef; dolu hedef kalıcı engel.
- Parça = sabit geometrik hücre kümesi = resimdeki **tek** hedefi. Oyuncu yalnız hangi parçayı göndereceğine karar verir; rotasyon/taşıma yok.
- El: 3 slot; her slotun sabit kuyruğu (level verisi). Gönderilen kartın yerine yalnız o slotun sıradaki parçası gelir. Kuyruk bitince slot boş.
- Yerleşebilir ⇔ parçanın tüm hücreleri boş ve girişten erişilebilir (BFS). `place`: hücreler en derinden başlayarak, rota = parça başı BFS en kısa yolu; sonra kalıcı engel.
- Sonra: **sealed** (boş hücre erişilemez), **stuck** (hiçbir kart yerleşemez), **won**.
- Yapısal teoremler (bu oturumda türetildi/doğrulandı): (1) durumun güvenliği yalnız yerleşen parçalar *kümesine* bağlı → farklı slotlardaki iki kart için A→B ve B→A aynı durumdan geçer ("komütasyon"); (2) kartlar "bloklu" olmaz: yasal olmayan kart durumu ulaşılamaz, kapanma = kayıp; (3) iki kapılı oda/halka yapısında dolu parçalar ring sırasında bitişik aralık olmalı.
- UI: tahtada yerleşmemiş hedefler **soluk** görünür (resmin tamamı açık), yerleşenler canlı; kart seçilince hedefi parlar + işçi izi (`İz`). `Kapalı/İz/Kritik` yol modları: **Kritik = geliştirici modu** (seçili kartın anında kilitleyeceği hücreleri turuncu gösterir) → insan testinde KAPALI/İZ kullanın, yoksa karar "turuncudan kaçın"a çöker. Kuyruk içeriği (sonraki kartlar) oyuncuya gösterilmiyor (peek yok).

## 2. Repo haritası
```
research/                 eski faz: solver/simülasyon araştırması (REPORT.md, REPORT_PHASE2.md) — değişmedi
prototype/                eski prototipler (CAT96 batch, hi-res 64×64, piece) — LEGACY, dokunma
prototype/block-image-01/
  src/engine.js           oyun çekirdeği (UI'dan bağımsız)
  src/ui.js, style.css, template.html   tek-dosya HTML UI (blok render, kartlar, işçiler)
  src/level_*.js, vectors_*.js          level verisi + parity vektörleri (build girdisi)
  dist/block-image-*.html tek dosya oynanabilir sürümler (çift tıkla aç)
  tools/ref.py            Python referans + kesin çözücü (analyse/stats/simulate)
  tools/lvlkit.py         level yazım kiti: Canvas(parça boyama), validate, Geo(bitset hızlı çözücü), analyse/report, valid_order, repair, shade
  tools/make_level_blocks.py <id>   <id>_source.json → src/level_<id>.js, vectors, tests/level_info_<id>.json (ref↔hızlı çözücü çapraz doğrular)
  tools/build.py <id>     → dist/block-image-<ID>.html
  tools/author_l0X.py     level çizimi (L02–L05, L02V2); tools/l0X_source.json üretir
  tools/preview_level.py  parça haritası PNG
  tools/human_flow.py     L01–L05 insan-akışı analizi (salt-okunur)
  tools/lab/              karar-deney kiti (X01–X05): labkit.py, search/hill/filt, make_lab.py, explain.py, report.py
  tools/analysis_archive/ oturum analiz betikleri (olduğu gibi; README'ye bak)
  tests/parity.js, qa_hand.js, qa_levels.js, qa_color.js, qa_l01.js   QA (aşağıda)
  design/*.md             tüm analiz/rapor dokümanları (bölüm 4)
```
Ortam: Python 3.11, Node 22, Playwright `/opt/node22/lib/node_modules/playwright` (chromium önkurulu; `playwright install` YAPMA). GitHub yalnız MCP araçlarıyla; PR açma (kullanıcı istemedikçe).

## 3. Çalıştırma / yeniden üretme
```
cd prototype/block-image-01
python3 tools/build.py l01v4                       # dist/block-image-L01V4.html (src/level_l01v4.js + vectors_l01v4.js gerekir)
python3 tools/make_level_blocks.py l02v2           # tools/l02v2_source.json → level + vectors + info
python3 tools/author_l02v2.py                      # kaktüs çizimi + kuyruk → l02v2_source.json
# QA (tests/ içinden):
node parity.js vectors_l02v2.json                  # JS↔Python parity (beklenen: 29/29)
node qa_hand.js ../src/level_l02v2.js level_info_l02v2.json   # el/kuyruk muhasebesi + çıkmaz denetimi
node qa_levels.js l02v2                            # tarayıcı QA (dakikalar sürer): kapsama, tek renk, kazanan/karışık/ters dizi, tuzak→sealed, telefon
```
Not: Level kimliği → dosya adı eşlemesi: `lXX` küçük harf (`l01v4`), HTML `...-L01V4.html` büyük harf. Yeni level eklerken `tests/level_info_<id>.json` içinde `win, win_mixed, win_reverse, trap_seq` olmalı (make_level_blocks üretir).
**Pratik tuzaklar:** (a) `qa_levels.js` uzun sürer; arka plana `&` ile atma (süreç öldürülüyor), `run_in_background` ile döngüyü komutun kendisi yap; (b) `qa_hand` "LEGAL OPTION CHECK" gecikmeli tuzaklı leveller için (L04) bilerek FAIL verir; küçük tahtalarda (<100 durum) "piece accounting" eşiği uygulanamaz; (c) `qa_levels` "doğal palet" kontrolü lab tahtalarında (her parça ayrı renk) bilerek FAIL.

## 4. Level envanteri (dist/*.html)
| Dosya | Ne | Hücre/parça | Yanlış/hamle* | Not |
|---|---|---|---|---|
| `block-image-01.html` | eski kedi 24×24 (rev. 6–7) | 188/25 | – | eski referans, dokunma |
| `L01.html` / `L01v3` | **L01 kedi 36×24**, ALT-2 kuyruk | 460/19 | %6.4 | p_random %27.9, 3/3 %47, gecikmeli 0; referans (kolay) |
| **`L01V4.html`** | L01, yalnız queue değişti | 460/19 | **%22.4** | p_random %1.0; 3/3 19·3/2 35·3/1 16; kazanan sıra 6.3e4; gecikmeli 0; tüm yanlışlar "tek açık yan" |
| `L02.html` Ev | ilk nesil | 472/26 | %8.5 | |
| `L03.html` Ağaç | ilk nesil | 522/34 | %8.9 | |
| `L04.html` Araba | ilk nesil; kasıtlı gecikmeli tuzak (17 durum) | 422/38 | %3.2 | `qa_hand` kasıtlı FAIL |
| `L05.html` Kuş | ilk nesil | 419/43 | %3.1 | zorluk genişlikten, tuzak kartı yalnız 2 |
| **`L02V2.html`** | **kaktüs, yol geçişi deneyi** | 346/27 | **%28.4** | 3/3 20·3/2 35·3/1 25; kazanan sıra 1.3e6; gecikmeli 0; dar geçit olayı %59 |
| `X01–X05.html` | karar-deney mini tahtalar (üç oda, taç, köprü, halka, üç kapı) | 26–59 / 5–10 | – | "iki kapılı oda" mekanizması; X serisi zemin hücresi kullanıyor (kusur) |
*Yanlış/hamle = rastgele kart seçen oyuncunun, hâlâ hayattayken, o hamlede yanlış (anında ya da gecikmeli) seçme olasılığı. İnsan rastgele oynamıyor: önizlemede kilitleneni eleyen oyuncu hepsini %98–100 kazanıyor.

## 5. Dokümanlar (design/) — ne bulundu
| Dosya | İçerik |
|---|---|
| `LEVELS_5.md` | ilk 5 level tasarım taslağı (kapı/dal/cep sözlüğü; kabul ölçütleri) |
| `LEVELS_L02_L05_REPORT.md` | L02–L05 (ilk nesil) raporu |
| `LEVEL_DESIGN_ANALYSIS_L01_L05.md` | insan-akışı analizi, "Level Design Rules v0.1" taslağı (**düzeltme içerir**: boş hedefler soluk görünür) |
| `lab/LAB_CANDIDATES.md` + `x0N_map.png` + `SOLUTIONS_SPOILER.md` | X01–X05 deney adayları |
| `PATH_RESEARCH.md` | "yol" kavramı: M1–M5 modelleri, görsel yol vs gameplay yolu, bilgi dengesi |
| `M2_GEOMETRY.md` | iki yollu oda (Kemer/At nalı/Tarak) geometri tasarımı |
| `M2_QUEUE_RESEARCH.md` | M2 + queue: gizli kuyruk yüzünden karar kumar; 1 kart peek ile okunur oluyor |
| `WRONG_CHOICE_ANALYSIS.md` | **en önemli analiz**: neden yanlış olasılığı düşük, hangi değişken etkili |
| `L01V4_REPORT.md`, `L02V2_REPORT.md` | son iki deney raporu |

## 6. Anahtar bulgular ve kararlar (kronolojik değil, önem sırasıyla)
1. **Zorluk parça sayısı/küçüklüğü değil.** L05: 43 parça, ort. 9.7 hücre, ama tuzak kartı yalnız 2 (LEG_R, WING_TOP); 318 "karar durumu" aynı iki sorunun tekrarı; "en derini önce" ya da "önizlemeye bak" ile çözülüyor. Seçenek sayısı ≠ karar kalitesi.
2. **Yanlış seçim olasılığı düşük çünkü kuyruk sırası tehlikeyi siliyor.** Geometride rastgele güvenli sırada kalan parçaların %42–56'sı tuzak (orta/son %49–71); parçaların %58–82'si bir noktada tuzak olabilir. Ama kuyruklar güvenli sıradan türetildi → kapı kartı kurbanından sonra geliyor → elde yanlış kart nadir (hamle başına %3–9). Aynı geometri + parçalarla, yalnız sıra değişerek yanlış olasılığı 2–4 katına çıkarılabiliyor, 3/3 payı %45–61 → ~%20–30, çözülebilirlik korunuyor.
3. **Gecikmeli tuzak = gizli kumar.** Kuyruk içeriği gösterilmediği için, doğru hamlesi gizli kuyruğa bağlı her çatal kumar. (Gizli dizilimleri tek tek deneyerek ölçüldü: bugünkü oyunda okunur doğru karar **sıfır**; 1 kart ileri görünürse çatallı düzenlerin ~%83–87'si okunur olur.) Karar: L01–L03 (ve yeni deneyler) gecikmeli tuzak **0**; L04–L05'te bilinçli/sınırlı olabilir. Peek (sonraki kart önizlemesi) L03+ için *onaylı ama uygulanmadı*.
4. **Yerellik:** L01'de ve V4'te tüm yanlış olaylarda (%100) kapanan parçanın tek kalan soluk komşusu yerleştirilen karttır ("çevresi dolu soluk parçanın son açık yanı"). Bu, yanlışı görselden okunur kılan ana özellik; yeni leveller bunu korumalı.
5. **Yol sistemi:** motorun "yolu" bir bağlantı değişmezidir (kalan her boş hücre girişle bağlı kalmalı), işçinin çizilen rotası yalnız bir tanıktır. Geniş lekede ("her yerden gidilebilir") yol okunmaz; dar kanal/boğaz gerekir. Zemin hücresi karara hizmet etmez → kullanma. Giriş zemin olmadan iki yol açmak için resmin alt kenarında girintiye oturmalı (en çok 3 komşu).
6. **M2 (iki yollu oda/halka):** çalışıyor ama tek başına "ikinci kapıyı erken kapatma" kuralını üretiyor; oda elde görünürse "odayı önce" çözer; sonuçlu çatallar gizli kuyruğa bağlı. Nötr üçüncü kart zemin olmadan imkânsız. M2 henüz bir level'a girmedi.
7. **Komütasyon:** "A→B ≠ B→A" bu motorda hiç olmaz (bölüm 1). Gerçek karar = hangi slotun ilerleyeceği.
8. **Düzeltmelerim (dürüstlük):** (a) ilk analizde "boş hedefler çizilmiyor" demiştim — yanlış; soluk görünüyorlar, mağdur parça görünür, görünmeyen *kapanma ilişkisi*. (b) `tools/lab/labkit.py` önbellek hatası (nesne kimliği) bulundu/düzeltildi, adaylar yeniden seçildi. (c) Zürafa denemesi (223 hücre, seyrek) elendi → kaktüs.
9. **Level Design Rules v0.1 (taslak, kanıtla güncel):** zorluk = kapı kartı sayısı/derinliği değil "kaç kart kapı ve kurbanından önce elde mi"; her level tek cümlelik kapı sorusu taşımalı; gerçek karar = elde ≥1 kaybettiren kart; gecikmeli sonuç kuyruk sırasından üretilir; gecikmeli tuzak yalnız izlenebilir kısa rota ise; parça küçüklüğü zorluk kolu değil (okunabilirlik riski); testere dişi kapı derinliğiyle kurulur.

## 7. Yeni level üretme tarifi (L02-V2'de çalıştı)
1. **Silüet seç:** tahtayı (36×24, hedef 350–520 hücre) doldurmalı, dar geçit/boğaz ve cep içermeli; zemin hücresi yok; giriş bir parçanın altında (`cv.entrance=(x,24)`). Seyrek/ince uzuvlu şekilleri (zürafa) eleme nedeni: hücre sayısı düşük.
2. **Çiz:** `tools/author_lXX.py` (Canvas: `rect/where/piece/rows`, `repair`, `shade`); parça başına tek renk, komşu parçalar farklı ton, doğal palet (tüm parçalar farklı renk değil). `python3 tools/preview_level.py tools/lXX_source.json out.png` ile bak.
3. **Kuyruk ara:** `lvlkit.valid_order` ile güvenli sıradan başla, 3 slota dağıt; hill-climb (swap/kaydır) — kısıtlar: çözülebilir, önizlemede-kilitleneni-eleyen oyuncu ≥%99,9 (gecikmeli 0), hedef yanlış olasılığı ve 3/3–3/2–3/1 dağılımı, yerellik (komşu %100, küçük kapanan alan), olay çeşitliliği. Betikler: `tools/analysis_archive/` (`s3–s6`, `l2s/l2t`, `hc3`, `loc`).
4. **Üret:** kaynak JSON'a `hand` yaz → `make_level_blocks.py <id>` → `build.py <id>` → QA (bölüm 3). Çıkış: 3 QA yeşil + `ref ↔ hızlı çözücü` eşleşmesi.
5. **Raporla:** yanlış/hamle, 3/3–3/2–3/1, gecikmeli sayısı, kapanan alan boyutu/uzaklığı, tek-açık-yan payı, kazanan sıra sayısı + dürüst zayıf noktalar. Solver metrikleri yalnız teşhis; hedef değil.

## 8. Çalışma biçimi (kullanıcıyla)
- Kullanıcı **Türkçe** konuşur. Talimatlar çoğunlukla sertleştirilmiş prompt'lar olarak gelir ("KESİNLİKLE YAPMA", "SONRA DUR", "level üretme/kod yazma" gibi). Bu sınırlara harfiyen uy; "dur" dendiğinde yeni iş açma.
- Kısa, dürüst raporlar; **sıralama ("en iyi level") yapma**; solver metriği tasarım hedefi değil; insan testi yoksa "çıkarım" de.
- Her teslimde: commit + push (dal `claude/festive-einstein-dba11b`), dosyaları `SendUserFile` ile gönder (HTML, rapor, harita). Commit sonuna `Co-Authored-By` + `Claude-Session` satırları.
- Hatayı fark edince açıkça düzelt ve raporla (bölüm 6.8 örnekleri).
- Kullanıcı başka bir danışmanla promptları iyileştirip getiriyor; onların tespitleri ("fail mekanizması çalışıyor, olasılık düşük" vb.) çoğunlukla senin ölçümlerinle uyumlu çıktı.

## 9. Açık kararlar / sıradaki adımlar (kullanıcıya ait)
1. **İnsan testi:** L01-V4 ve L02-V2'yi Kapalı/İz modunda oynat. Sorular: hamleden önce düşündün mü? Yanlışın nedenini gördün mü? Kaktüsün kolu "yol" olarak okundu mu?
2. **L03'te ne eklenecek?** Kullanıcı L02-V2'yi oynadıktan sonra karar verecek. Yeni mekanik yok; olası kolay kaldıraçlar: dağılımı değiştirmek, gecikmeli tuzak (yalnız peek ile), M2 yapısı.
3. **Peek (sonraki kart önizlemesi):** onaylı ama uygulanmadı; gecikmeli karar uzayı ancak buna bağlı (bu bir bilgi sunumu değişikliği, kural değil).
4. **"Kritik" modu oyuncuya açılsın mı?** Açılırsa karar "turuncudan kaçın"a çöker.
5. **Zemin hücreleri tamamen kaldırılsın mı?** (X serisi kullandı; prensip: karara hizmet etmeyen şey yok.)
6. **Kuyruk estetiği:** hill-climb kuyrukları bölgesel akıştan dağınık sıraya kayıyor; resmin kuruluşu insanca doğal mı? Elle düzenleme gerekebilir.
7. **Eski L02–L05'e (ilk nesil) queue iyileştirmesi uygulanacak mı?** Henüz hiçbirine uygulanmadı (yalnız L01-V4).
8. **M2'yi bir level'a koymak** (oda kartı bacaklardan sonra gelsin, ≥6 parça, kapı parçaları el başında olmasın).

## 10. Bilinen eksikler / riskler
- İnsan testi yok; okunurluk iddiaları çıkarım.
- L01-V4'te hamlelerin %20'si zorunlu (slotlar farklı anlarda bitiyor); yanlışların %47'si tek ilişki (MUZZLE → NOSE_MOUTH).
- L02-V2: kollar tek tonlu yeşil, dilim sınırları zor seçilebilir; kapanan alan bazı olaylarda 38 hücre; sağ/sol kol farklı fazlarda çıkması aramanın sonucu (tasarım değil).
- X serisi zemin kullanıyor; adaylar abstrakt (resim değil).
- Eski L02–L05 kuyrukları "güvenli sıra" kökenli; yanlış olasılıkları düşük (%3–9).
- `tools/analysis_archive` betikleri yol bağımlı (README).
- `research/` ve `prototype/` (CAT96 vb.) eski aşama; bu proje çizgisinde kullanılmıyor.

## 11. Yeni oturum için ilk 10 dakika
1. Bu dosyayı + `design/WRONG_CHOICE_ANALYSIS.md` + `design/L02V2_REPORT.md` oku.
2. `dist/block-image-L01V4.html` ve `L02V2.html`'i aç, 5 dk oyna (Kapalı/İz).
3. `cd prototype/block-image-01/tests && node parity.js vectors_l02v2.json` ve `node qa_hand.js ../src/level_l02v2.js level_info_l02v2.json` çalıştır (ortamı doğrular).
4. Kullanıcıdan test geri bildirimini iste; bölüm 9'daki kararlar gelmeden yeni level/mekanik üretme.
