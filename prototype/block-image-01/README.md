# block-image-01 — "küçük blokları doğru sırada göndererek bir pixel-art resmi oluştur"

Bağımsız prototip (CAT96 / batch / piece kodundan türemedi). Tek dosya: **`dist/block-image-01.html`** (çift tıkla aç). Yeniden üretmek: `python3 tools/make_level.py blocks2 && python3 tools/build.py`.

## CAT ART PASS (rev. 6) — kedi = 25 renkli parçanın birleşmiş hâli
- **Silüet yeniden çizildi** (`tools/make_level.py` içindeki `ART`; her hücre sahibi parçanın harfiyle yazılı, elle): 2 üçgen kulak, geniş baş, **2 göz (1 hücrelik gerçek parça, `dark`)**, **burun (1 hücrelik gerçek parça, `dark`)**, boyun, gövde, iki pati ve gövdeden ayrışan, **3 parçalık kıvrımlı kuyruk (25 hücre)**. Toplam **188 hücre / 25 parça**, her hücre tam bir parçaya ait, her parça bağlı.
- **Renkler:** turuncu 7 · mavi 5 · kırmızı 4 · yeşil 6 · dark 3 (göz×2, burun). Bitişik parçalar farklı renk (4-boyama; aynı renkli komşu çift = 0), kulaklar farklı renk, her kuyrukta ≥ 3 renk, ilk el farklı 3 renk. Renk bir kural değil; grid çizgisi yok, sınırlar renkten okunur.
- **Dekoratif çizim yok:** gözler/burun/kuyruk canvas'a çizilmiyor; kedi yalnız hedef hücreler + parçalar + `piece.color`'dan oluşuyor (QA: hedef olmayan 358 hücrenin hiçbirinde çizim yok).
- **Mekanik değişmedi** (engine/ref aynı). Yeni seviye için solver yeniden çalıştırıldı: çözülebilir; 2.65×10⁸ kazanan sıra; 113 karar durumu, 121 anında + 4 gecikmeli tuzak; rasgele el oyunuyla kazanma ≈ %0.34; kazanan hatlar boyunca ortalama ≈ 14 anlamlı karar (min 5, maks 21). Parity 16/16.
- **QA:** `node tests/qa_color.js` → `targetPieceColorParity: 188/188 PASS`, `25/25 pieces monochrome: PASS`, `pieceToTargetColorParity: PASS`, `finalCatColorSource: piece.color`, `catFeatureCoverage: PASS`.
- Eski otomatik-bölme üreticisi `tools/make_level_auto_v1.py` (referans); animasyon hızı biraz artırıldı (blok ≈ 0.8–1 sn).

## Görsel dil (rev. 2)
- Resmin dışı yerleştirilebilir değil ve çizilmiyor (beyaz oyun tahtası kartı yok); yalnız resim alanı var, grid çizgisi/hücre aralığı yok.
- **Renk sistemi (rev. 5, kesin):** her parçanın level verisinde kendi `color`ı var (turuncu 6 · mavi 6 · kırmızı 6 · yeşil 7); hedef resimden türetilmez, slota/çözüme bağlı değil, mekanik değil. **Kedi = 25 parçanın birleşmiş hâli:** `targetColor[cell] = owningPiece.color`; eski kedi renk listesi (`colors[]`/`palette`) level verisinde uyumluluk için duruyor ama render'da kullanılmaz. Kart, taşınan kutu, hayalet/önizleme (açık ton + glow) ve yerleşmiş hücreler aynı renk dilini taşır; yerleşince renk değişmez. Otomatik QA: `node tests/qa_color.js` (targetPieceColorParity 188/188, 25/25 pieces monochrome, pieceToTargetColorParity, finalCatColorSource: piece.color).
- **Seçince:** hedef, gerçek renklerin açık bir silüeti + kart renginde glow/çerçeve (tam renkle doldurulmaz); işçi izi ve taşınan kutular kart renginde; yerleşince bloklar gerçek resim rengine dönüşür.
- Mekanik, motor, el/kuyruk, hedef, erişilebilirlik, solver ve parity değişmedi (16/16).

## Oyun döngüsü
GÖR (3 blok) → SEÇ (kart: hedef bloğu resimde belirir; göndermez) → GÖNDER → işçiler taşır → blok yerine oturur → resim büyür → o slota yeni blok gelir.
- **Kartlar:** blokların kendi pixel-art renkleriyle şekli. Bir karta bas = o bloğun resimdeki TEK hedefi pulse + çerçeveyle belirir; aynı karta/Gönder'e bas = gönder. Üç hedef aynı anda gösterilmez.
- **İz (A):** seçili bloğun işçilerinin **gerçek** rotası (motorun hesapladığı BFS yolları) ışık noktalarıyla. "Kritik" (B) geliştirici modu: yerleşince erişilemeyecek hücreler (oyuncuya varsayılan olarak söylenmez). "Kapalı": bilgi yok.
- **İşçiler:** blok başına ≈ 5–10 işçi (hücre başına 1), her biri küçük bir blok parçası taşır; bir blok ×1 hızda ≈ 1 sn'de oturur (`Hız` ×2/×4).
- **Engel:** yerleşen bloklar kalıcı; işçiler yalnız boş hücrelerden yürür. Bir boş hücreye yol kapanırsa **kilitlenir** (sealed); elindeki hiçbir bloğa yol yoksa **sıkışır** (stuck).

## Sayılar (bu seviye, elle hazırlanmış tek seviye)
- **Grid:** 24×24 (kedi 20×20 blok resmi + kenar boşluğu + giriş), **188 dolu hücre**, **25 blok** (5–10 hücre, 24 farklı şekil), 3'lü el, kuyruklar 9/8/8.
- **Resim:** `tools/art_source_cat96.json` (önceki 96×96 pixel-art kedi) → `tools/downsample.py` ile 20×20'ye indirilmiş renkli bloklar; çözüm düzeni yok, resim bloklara bölünüyor (`tools/make_level.py`: satır-ana, kompakt büyütme, tek sabit tohum).
- **El davranışı:** 3 slot, her birinin elle seçilmiş sabit kuyruğu (örüntü `blocks2`). Gönderilen kartın yerine yalnız o slotun sıradaki bloğu gelir. Kuyruklar, "girişten blok-komşuluk BFS'inin tersi" geçerli sıranın alt dizisi ⇒ seviye çözülebilir.
- **Örnek çözüm (slot dizisi, 25 gönderi):** `0 0 0 0 0 1 1 1 0 0 1 1 1 1 1 2 2 2 2 0 2 2 2 2 0` (slot 0 = ilk kart…). Slotlar arası serpiştirilmiş başka kazanan hat: `0 1 2` tekrarı (`tests/level_info.json`).
- **Karar yoğunluğu (kesin DP, 363 durum):** çözülebilir; kazanan hatlar boyunca ortalama **≈ 10 anlamlı karar** (bir kart güvenliyken bir diğeri kilitliyor; 400 rasgele kazanan hatta min 3, maks 21; ilk karar ≈ 6. adım). Rasgele el oyunuyla kazanma ≈ %1.9. Bu **eğlence/zorluk kanıtı değil**, "tüm sıralar kazanmaz" ölçüsü.
- **Tahmini oyun süresi:** 25 gönderi × ≈ 1 sn animasyon + karar süresi ≈ **1–1.5 dk** (karşılaştırarak oynarsan daha uzun).

## Motor / parity
`src/engine.js` (temiz çekirdek) ↔ `tools/ref.py` (Python referansı + kesin çözücü). `node tests/parity.js`: 16/16 vaka birebir (yerleşen hücre sırası, kart durumları, rota uzunluğu + imzası, sealed/stuck/won; sentetik `TOY` seviyeleri sealed/yerleşemez kuralını sınar). Sayfadaki **Parity** düğmesi aynı vektörleri tarayıcıda çalıştırır.

## Bilinen sınırlar
- Her blok sabit hedefli (blok başına tek geçerli konum); "bu blok ya da şu yer" seçimi yok — karar yalnız hangi bloğu şimdi göndereceğin.
- Resim 20×20'lik bir indirgeme; kedi okunuyor ama küçük detaylar (ağız, bıyık) yok. Blok sınırları rastgele-ama-sabit bölme sonucu, elle çizilmedi.
- Blok boyları 5–10 hücre (istenen 3–6 aralığına sığmıyor: 25 yerleştirme × 3–6 hücre ≈ 100–150 hücre eder; 188 hücreli resim için 5–10 seçildi).
- İlk el güvenli; ilk gerçek tuzak ≈ 6. adımda belirir.

## Rev. 7 — EL / KUYRUK hata düzeltmesi
- **Bulgu:** 19/25 durumunda `ptr=(7,8,4)`: 2. slotun kuyruğu (8 parça) bitmişti → kart *kaybolmadı*, kuyruk tükenmişti (turuncu parça önceden gönderilmişti). Kalan 6 parça yalnız 1. ve 3. kuyrukta; ikisi de gönderilince resmi kapatıyordu. Eski `blocks2` kuyruk düzeninde 4 "gecikmeli tuzak" (önceki hamle bayraksız, sonraki durum kazanılamaz) vardı.
- **Düzeltme (yalnız seviye verisi: kuyruk dağılımı; mekanik/sanat/geometri/renk aynı):** `tools/safe_hand.json` (çözücüyle seçildi: gecikmeli tuzak 0, 427 durum, karar durumu 164). Kuyruk uzunlukları 8/9/8.
- **UI:** boş slot artık görünür yuva ("kuyruk bitti"); yerleşemeyen kart gizlenmez, soluk + "yol kapalı" + basınca açıklama; çıkmaz uyarısı (`L.diagnose`); `CBGAME.handDiag()` + `console.debug('[el]')` kuyruk/işaretçi/el kaydı.
- **QA:** `node tests/qa_hand.js` (eski düzende FAIL, yenide PASS).

## Rev. 8 — L01: 36×24 piksel-art kedi (oynanabilir)
- **Dosya:** `dist/block-image-L01.html` (`python3 tools/build.py l01`); cat-02 (`dist/block-image-01.html`) aynen duruyor. Mekanik (engine.js) değişmedi.
- **Veri:** 36×24, **460 hücre, 19 parça** (kafa/alın 64 · haunch 50 · çene/bel gate'i 36 · göğüs 36 · kuyruk 35 · … · gözler 9 · burun+ağız 8), giriş (x18, y24), kuyruklar **ALT-2**:
  A: FACE_L FACE_R FOREHEAD MUZZLE JAW CHEST BELLY · B: EAR_L EARIN_L EYE_L NOSE_MOUTH HAUNCH PAW_L · C: EAR_R EARIN_R EYE_R TAIL PAW_R FLANK_R.
  Kaynak: `tools/l01_source.json` (hücre→parça, piksel-art rengi, kimlik rengi, kuyruklar) → `python3 tools/make_l01.py` → `src/level_l01.js`, `src/vectors_l01.js`, `tests/vectors_l01.json`, `tests/level_info_l01.json` (Python referansıyla kesin çözücü: winning_orders 6 172 752, rastgele kazanma %27,9, gecikmeli tuzak 0, ilk anlık tuzak 3. el).
- **Görünüm (Rev. 8b):** 19 parça = oynanış, **460 küçük fiziksel blok = render**. Resim modunda (varsayılan, `?colors=art`) her hücre ayrı kutu: aralık, alt/yan gölge, üst ışık, hafif bevel, hedef hücrenin gerçek kedi rengi; tek tek "tak" ile oturur (küçük düşme + pop + kıvılcım; büyük parçada dağılım ≤0,6 sn); hayalet = ince aralıklı soluk küçük kareler; kartlar da parçanın küçük bloklarından; işçi yükü = hedef hücrenin bloğu. Düz yüzey/boyanmış resim görünümü yok. kimlik rengi (`piece.color`) işçi yükü ve önizleme çerçevesinde. Başlıkta **Resim / Parça** düğmesi (`?colors=piece`: eski tek-renk parça görünümü). Büyük parçalarda işçi dalgası kısaltıldı (≤0,45 sn dağılım), hız 64 hücre/sn.
- **QA:** `node tests/parity.js tests/vectors_l01.json` (19/19, rota imzaları dahil) · `node tests/qa_hand.js ../src/level_l01.js level_info_l01.json` (19/19 muhasebe, çıkmaz/kazanılamaz durum 0) · `node tests/qa_l01.js` (tarayıcı: 19 hamlede önizleme=yerleşim, kazanma, 3. elde FOREHEAD tuzağı → sealed, renk modu, telefon taşması, süre, console).
- **Henüz yok (bilerek):** sıradaki kart önizlemesi (L03+ için onaylı), yeni level, yeni mekanik.

## Rev. 8c — L01: her gameplay parçası TEK RENK (piece.color)
- **Kural:** bir parçanın bütün küçük blokları aynı renk; renk kaynağı yalnız `piece.color`. `piece.art` (hücre bazlı resim renkleri) veride duruyor ama **render'da kullanılmıyor**. Kedinin çok renkliliği parçalar ARASINDA oluşur: 6 doğal ton (orange, amber, brown, cream, pink, dark), komşu parçalar farklı renkte. Palet seviye verisinde (`palette`), `style: "blocks"` 460 küçük fiziksel blok render'ını açar.
- Kart, hayalet, önizleme dolgusu, yerleşen bloklar ve işçi yükü hep o parçanın tek rengi (hayalet = açık ton, seçim çerçevesi = koyulaştırılmış ton). Resim panosu (koyu bej) krem/pembe blokların seçilmesi için. "Resim/Parça" renk düğmesi kaldırıldı.
- **QA (`node tests/qa_l01.js`):** 19 parçanın tek `piece.color`'ı, komşular farklı renk, 19/19 kart tek renk, 19/19 hayalet tek renk, ilk 18 parçanın her hücresi tahtada piece.color, FOREHEAD (64 işçi) ve HAUNCH işçi yükü tek renk, 460 hücrenin render rengi parça başına tek ve kedi ≥5 renkli, blok aralığı/üst ışık/alt gölge, tuzak, telefon, console.
