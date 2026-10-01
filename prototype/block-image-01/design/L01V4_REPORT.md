# L01-V4 — yalnız queue değişti (L01 görseli, grid, parçalar, renkler, UI, kurallar aynı)

Dosya: `dist/block-image-L01V4.html` (L01 dosyaları dokunulmadı). Doğrulama: grid, parça kimliği/hücreleri/renkleri, `colorHex`, boyut ve stil L01 ile birebir aynı; yalnız `hand` ve ad/başlık farklı. Parity 29/29, `qa_hand` hepsi geçti (çıkmaz 0, kazanılamaz ulaşılabilir durum 0), tarayıcı QA `qa_levels l01v4` tümü geçti (kazanan/karışık/ters dizi → kazandı, tuzak yolu → mühürlendi, telefon, console).

## Kullanılan queue (slotlar soldan sağa, kartlar 1-2-3)
```
1: PAW_R · FLANK_R · EAR_L · NOSE_MOUTH · EARIN_R · EYE_R · EYE_L
2: PAW_L · MUZZLE · FACE_L · JAW · CHEST · BELLY
3: EARIN_L · TAIL · EAR_R · FOREHEAD · HAUNCH · FACE_R
```
Açılış eli: PAW_R · PAW_L · EARIN_L (üçü de güvenli). Kuyruk uzunlukları L01 ile aynı (7/6/6).

## Adayların karşılaştırması (aynı çözücü, ref ile doğrulandı; "olay" = yanlış kart seçimi)
| aday | yanlış/hamle* | 3/3 · 3/2 · 3/1 | gecikmeli tuzak | olayda kapanan alan (ort hücre) | kapanan alana ort. / medyan uzaklık (hücre) | kurbanı bitişik |
|---|---|---|---|---|---|---|
| mevcut L01 | %6.4 | 47 · 18 · 0 | 0 | 21 | 2.5 / 2.1 | %100 |
| önceki otomatik (R1) | %13.5 | 30 · 35 · 19 | 0 | **53** | 3.6 / 3.2 | %100 |
| A | %14.6 | 28 · 34 · 17 | 0 | 17 | 2.6 / 2.7 | %100 |
| **B (seçilen)** | **%22.4** | 19 · 35 · 16 | 0 | **14** | **2.0 / 1.8** | %100 |
| C | %42.8 | 12 · 35 · 21 | 0 | 13 | 1.9 / 1.0 | %100 |
\*rastgele kart seçen oyuncunun hamle başına yanlış seçme olasılığı (hayattayken). Yüzdeler kazanan yoldaki durumlarda hamle türü payı; kalanı 2 kartlı/1 kartlı hamleler.
Önceki T25 denemesi (gecikmeli tuzak içeriyordu) ve rastgele başlangıçlı aramalar elendi: ölçütler gecikmeli tuzak = 0, kopan alan küçük ve bitişik.
**Seçim gerekçesi:** hepsinde kurban bitişik; R1 kopan alan 53 hücre ile en uzak/büyük; C yerel ama hamle başına %43 yanlış ilk seviye için aşırı; B, yerellik ölçütlerinde (14 hücre, ort. 2.0 / medyan 1.8) A'dan daha iyi ve yanlış olasılığı L01'in 3.5 katı.

## B için sonuçlar
- Yanlış seçim oranı: **%6.4 → %22.4** (hamle başına). Tüm oyunu rastgele bitirme olasılığı %27.9 → **%1.0**. Önizlemede kilitleneni elemeyi bilen oyuncu yine her zaman kazanıyor (gecikmeli tuzak 0).
- Dağılım (kazanan yolda): 3/3 %19 · 3/2 %35 · 3/1 %16 · 2/2 %4 · 2/1 %6 · 1/1 %20 (L01: 47·18·0·17·6·13). Tek-doğru-iki-yanlış durumları var ama çoğunluk değil.
- Anında tuzak durumu 48 → 57, gecikmeli 0, kazanan sıra 6.2e6 → 62 922 (ezber imkânsız), karar/serbest/zorunlu durum 46/57/6 (önce 48/153/7).
- Yanlış kartlar ve kapattıkları: MUZZLE → NOSE_MOUTH %47, FACE_L → EYE_L %16, FACE_R → EARIN_R %13, FLANK_R → TAIL %11, kalan %13 diğerleri. Tümü yan yana parçalar.
- Kapanan alan uzaklığı (yerleşen parçanın hücrelerine en yakın kapanan hücre): ort 1.0, medyan 1 hücre; kapanan alanın ortalama uzaklığı 2.0, medyan 1.8; olay başına kapanan alan ort. 14 hücre.

## Oyuncu yanlışın nedenini görselden anlar mı? (çıkarım, insan testi yok)
- Ölçüm: **tüm yanlış olaylarda (%100)** kapanan parçanın tek kalan soluk komşusu yerleştirilen karttır. Yani yanlış kart, "çevresi zaten dolu/kenar olan soluk bir parçanın son açık yanı". Görsel ipucu: kartı seçince hedefi parlıyor; bitişik soluk bir parçanın öbür tarafları canlı bloklarla ya da resim kenarıyla kapalıysa o kart onu mühürler. Örnekler: gözü yüz bloğundan önce, burnu ağız/burun bölgesini saran muzzle'dan önce koy.
- Ek: sonuç uzak değil; mühür vurgusu (turuncu) kaybettiğinde bitişik soluk parçayı gösterir.
- Zayıf noktalar: (1) ipucu "soluk parçanın diğer yanlarını incelemek" gerektiriyor, bu ilk seferde kolay olmayabilir; (2) yanlışların %47'si tek ilişki (MUZZLE → NOSE_MOUTH), dolayısıyla çeşitlilik sınırlı: 4 ilişki %87; (3) sonlarda hamlelerin %20'si tek kart (zorunlu): L01'de %13'tü, slotlar farklı anlarda bitiyor (örn. 10. hamlede 1. slot boş); (4) kuyruk sırası bölgesel akıştan dağınığa kaydı (resim, pençe/kuyruk/kulak karışık kuruluyor); estetik etkisi değerlendirilmedi.
- Kritik modu açıksa bu seviye "turuncudan kaçın"a çöker; testte Kapalı/İz kullanın.

Başka level'a uygulanmadı.
