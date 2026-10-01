# block-image-01 — "küçük blokları doğru sırada göndererek bir pixel-art resmi oluştur"

Bağımsız prototip (CAT96 / batch / piece kodundan türemedi). Tek dosya: **`dist/block-image-01.html`** (çift tıkla aç). Yeniden üretmek: `python3 tools/make_level.py blocks2 && python3 tools/build.py`.

## Görsel dil (rev. 2)
- Resmin dışı yerleştirilebilir değil ve çizilmiyor (beyaz oyun tahtası kartı yok); yalnız resim alanı var, grid çizgisi/hücre aralığı yok.
- **Parça rengi (rev. 4, kesin):** her parçanın level verisinde kendi `color` değeri var (turuncu 6 · mavi 6 · kırmızı 6 · yeşil 7); hedef resimden TÜRETİLMEZ, slota ve çözüme bağlı değildir, mekanik değildir. Kart, taşınan kutular = tek renk `piece.color`; yerleşince hedef resmin gerçek renklerine dönüşür. İlk el turuncu · mavi · kırmızı. Otomatik QA: `node tests/qa_color.js` (pieceColorMode / 25/25 monochrome pieces / targetColorIndependent).
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
