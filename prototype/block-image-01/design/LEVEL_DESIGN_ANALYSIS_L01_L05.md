# L01–L05 oynanış analizi + LEVEL DESIGN RULES v0.1 (taslak)

Kapsam: yalnız analiz. Seviye verisi, mekanik, UI değişmedi. Yeni level yok.
Yöntem: `tools/human_flow.py` (salt-okunur) — oyuncunun görebileceği tüm durumlar (anında kilitlemeyen hamlelerle ulaşılan), faz = yerleşen parçaların üçte biri. Ek olarak basit oyuncu-ilkeleri simülasyonu ve L04 gecikmeli tuzağın dökümü.
**Sınır:** hiç insan oyun testi yapılmadı. "İnsan okuyabilir" iddiaları kod/ekran görüntüsü çıkarımıdır, ölçüm değil.

## 0. Yapısal bulgu (her şeyi etkiliyor)
- Kartlar asla "bloklu" olmuyor: oyuncunun ulaşabildiği hiçbir durumda yasal olmayan kart yok (blocked = 0, tüm leveller). Erişim kapanması kartı kapatmaz; **mühürleyerek oyunu bitirir**. Yani her elde seçim = "3 karttan hangisi güvenli?".
- Boş (yerleşmemiş) hedefler tahtada çizilmiyor; oyuncu yalnız yerleşmiş blokları ve **seçtiği kartın** hedefini görüyor. Mühürlenecek/kapanacak parça (mağdur) ekranda görünmüyor; oyuncu resmi tahmin etmek zorunda.

## 1. Oyuncu karar akışı (faz = ilk/orta/son üçte bir; serbest = 3 kart da güvenli; tuzaklı = ≥1 kart kaybettiriyor)
| | L01 | L02 | L03 | L04 | L05 |
|---|---|---|---|---|---|
| ilk 3 hamle: tuzaklı durum | 1/10 | 3/9 | 0/10 | 0/10 | 0/10 |
| serbest oran (faz1/2/3) | .78/.76/.60 | .70/.86/.59 | .75/.62/.62 | .90/.89/.68 | **.98**/.82/.55 |
| tuzaklı el oranı (faz1/2/3) | .22/.23/.26 | .30/.14/.32 | .25/.38/.31 | .10/.10/.25 | **.02**/.18/.37 |
| yumuşak bağımlılık* (faz2) | .37 | .43 | .38 | .45 | .52 |
| son %25: tuzaklı / seçimli durum | 8/19 | 14/36 | 11/54 | 21/65 | 16/48 |
\*seçim, kalan kazanma yollarını ≥3× değiştiriyor ama kaybettirmiyor.

A) İlk 3 hamle: L03, L04, L05'te üç kart da güvenli (tuzak 0). Seçim var ama sonuçsuz: açılış karar değil, ısınma. Yalnız L02 (3/9) açılışta gerçek bir cezayla başlıyor.
B) Orta: serbest oran %62–89; çoğu elde "uygun kartı gönder" yetiyor. Gerçek karar (tuzaklı el) L03'te en yüksek (%38).
C) Son: tuzaklı el oranı hepsinde artıyor (L05 %37). Son bölümde karar azalmıyor, aynı kapıların son kartları kalıyor; saf cleanup yok (zorunlu durum ≤ %14).
D) Hata: anında mühür = hemen belli (L01, L02, L03, L05 tamamı; L04'te çoğu). Tek gecikmeli kaynak L04 (aşağıda).

Oyuncu-ilkesi simülasyonu (deterministik tek oyun): "en derin kartı gönder" → L02 ve L05'i **kazanıyor**, L01/L03/L04'ü kaybediyor. "Önizleme mühürlüyorsa gönderme, yoksa en derini gönder" → **beşini de kazanıyor**. Güvenli-rastgele ajan: L01–L03, L05 %100, L04 %98. Yani bugünkü leveller 1-hamle kontrolü (önizleme bir şeyi kapatıyor mu?) ile çözülüyor; planlama derinliği gerektiren tek level L04.

## 2. "Küçük parça = zor" hipotezi
- A görsel karmaşıklık: monoton artıyor (19→26→34→38→43 parça; ort. hücre 24.2→18.2→15.4→11.1→9.7).
- B seçim karmaşıklığı: kart sayısı sabit 3; artan olan **durum sayısı** (208→511→585→1403→2191), seçim değil.
- C gelecek bağımlılığı: tuzak kartı çeşidi 3 / 5 / 9 / 7 / **2**; mağdur çeşidi 12/17/24/19/30. L05'te 43 parçadan yalnız 2'si (LEG_R, WING_TOP) tuzak kart; 318 "karar durumu" aynı iki soruyu tekrar ediyor.
- D gecikmeli sonuç: yalnız L04 (17 hamle).
**Sonuç:** küçük parça ekranda daha kalabalık, zorluğu artırmıyor. L05 en küçük parçalı ve en az karar çeşitli. Hipotez desteklenmedi.

## 3. L05
Oyuncu gerçekten düşünmek zorunda değil: ilk üçte birde elin %98'i tamamen serbest, ikinci üçte birde %82. Düşünme son üçte birde (%37 tuzaklı) bacak/kanat kapısında geliyor; "deliğe en yakın kartı en sona bırak" sezgisi ve en-derin-önce ilkesi levelı tek başına kazandırıyor. Mühürlenen alan çok büyük (tuzakta ortalama 132 hücre) — hata cezası ağır ama sebebi bacaktan gövdeye kapıyı kapatmak; tek ders.

## 4. L04 gecikmeli tuzak
- 17 gecikmeli tuzak hamlesi, 16'sı DECK_L, 1'i DECK_R; derinlik 19–28. Mağdur: TRUNK (10), HOOD (7). Kapanma: DECK_L ortadan bir yolu keser; TRUNK/HOOD kuyruk sonunda beklerken REAR_UP / DECK_R / FRONT_UP kalan tek yolu da kapatır.
- Gecikme: en erken 1 hamle sonra, en geç 11 hamle sonra (tek yoldan çıkış yok); 3 çıkmaz durumda tüm kartlar kaybettiriyor.
- İnsan okunabilirliği: **şu an solver'a ait ilişki.** TRUNK/HOOD tahtada çizilmediği için oyuncu "bunu koyarsam şu kapanır" diyemez; yalnız arabanın şeklini bilirse tahmin eder. Ayrıca kayıp, sebepten 1–11 hamle sonra görüldüğü için hata DECK_L'ye değil son karta atfedilir. Oynayarak doğrulanmalı.
- Aynı geometri, farklı kuyruk sırasıyla (TRUNK/DECK/HOOD erken↔geç) gecikmeli tuzak 0 ↔ 17: gecikmeyi yaratan şey kuyruk sırası.

## 5. Her levelın temel puzzle sorusu
- L01: "Alın/yüz (FOREHEAD, 24) kulaklar dolmadan gönderilmemeli" — 3 kapı kartı.
- L02: "Basamak/zemin bandı (STEP, tuzaklı ellerin 65/101'inde) duvar ve temel bitmeden kapanmamalı" — tek baskın kapı (+ cam çerçeve cebi).
- L03: "Hangi yaprak kümesi komşularının ve dalın yolunu kapatıyor?" — 9 kart, dağınık kapılar; en çeşitli.
- L04: "Gövde bantları (SILL/DECK) camları ve bagaj/kaputu kapatmadan kapanmamalı" — anında (SILL→cam) + gecikmeli (DECK→TRUNK/HOOD).
- L05: "Bacak/kanat üstü (LEG_R, WING_TOP) en sona" — tek kapı, L01/L02 ile aynı soru.
**Aynı soruyu soranlar:** L01, L02 ve L05 (tek/az kapı, en-derin-önce kazandırır). Gerçekten farklı sorular: L03 (çok kapı, dağınık), L04 (anında+gecikmeli).

## 6. Zorluk faktörleri — kanıt durumu (sıralama yok)
- Parça boyutu: kısmi kanıt (görsel yükü artırıyor; zorluğa etkisi kanıtlanmadı, L05 ters yönde).
- Parça sayısı: kısmi kanıt (durum sayısını artırıyor, karar çeşidini değil).
- 3 kart arasındaki seçim: kısmi kanıt (3 sabit; belirleyici olan elde kaç kartın güvenli olduğu).
- Erişim kapanması: kanıt var (bütün tuzaklar buradan; bloklu kart yok, kapanma = mühür).
- Gecikmeli sonuç: kısmi kanıt (yalnız L04, yalnız yapısal; insan okunabilirliği henüz kanıt yok).
- Görsel karmaşıklık: kanıt var (artıyor), zorluk etkisi henüz yok.
- Kuyruk sırası: kanıt var (aynı geometride gecikmeli tuzak 0→17; L05 kuyruğunda p_random %0.65→%3.9).
- Küçük parça okunabilirliği: henüz kanıt yok (insan testi yok; telefonda blok ≈10 px, L05'te 1 hücrelik EYE_HI).

## LEVEL DESIGN RULES v0.1 (taslak, yalnız L01–L05 gözleminden)
1. Zorluk, parça sayısından değil "kaç kart kapı (tuzak) ve ne kadarını kapatıyor"dan okunur (L05: 43 parça/2 kapı; L03: 34/9).
2. Her level tek cümlelik bir kapı sorusu taşımalı; iki level aynı soruyu soruyorsa biri başka bir soruya dönüştürülmeli (L01=L02=L05).
3. Gerçek karar = elinde ≥1 kaybettiren kart olan el; ilk üçte birde serbest oran ~%90'ı aşan açılış (L05 %98) karar sayılmaz.
4. Seçim genişliği (3 kart) sabit; zorluk "3 karttan kaçı güvenli" ve bunun ne sıklıkla değiştiğiyle ayarlanır.
5. Gecikmeli sonuç geometriden değil kuyruk sırasından üretilir (L04: aynı parçalar, 0→17).
6. Gecikmeli tuzak yalnız mağdur ve kapanan yol oyuncuya görünür/tahmin edilebilirse sayılır; şu an boş hedefler çizilmediği için doğrulanmadı.
7. Planlama gerektiren (≥2 hamle ileri) derinlik şu an yalnız L04'te; "zor/peak" seviye bunu taşımalı, parça küçültmek tek başına taşımıyor.
8. Parça küçüklüğü okunabilirlik riskidir (1 hücrelik parça, 2 hücrelik kulp); eşik insan testiyle belirlenecek, o zamana dek yeni zorluk kolu olarak kullanılmaz.
9. Testere dişi, parça sayısı değil kapı sayısı/derinliği (anında vs gecikmeli) ile kurulmalı; L02→L05 sırası bugün bunu yansıtmıyor.
10. Son bölüm aynı kapıların son kartlarıdır (tuzaklı el %25–37); cleanup'a düşmüyor — bu korunabilir.
