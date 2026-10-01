# "Yanlış seçim olasılığı" analizi — L01–L05 (yalnız analiz; hiçbir level/dosya değişmedi)

Girdi: yüklenen `block-image-L01v3 / L02 / L03 / L04 / L05.html`. İçlerindeki level verisi repodakilerle birebir aynı (grid, parçalar, kuyruklar). Çözücü: `ref.py` ile `lvlkit` aynı sonucu verdi (p_random ve kazanan sıra sayısı eşleşti). Karşı-olgusal denemeler bellekte yapıldı, dosya yazılmadı.

Tanım: bir karta basmak **güvenli** = kazandıran hamle; **yanlış-hemen** = anında kilitliyor; **yanlış-sonra** = o an kilitlemiyor ama durum kazanılamaz hâle geliyor (birkaç hamle sonra başka parça erişilemez). Elde 3 kart var (kuyruğu biten slotta 1–2 kart kalır).

## 1. Mevcut 5 level: hamle başına güvenli/yanlış dağılımı
Kazanan yol üzerindeki durumlarda (oyuncu henüz hata yapmamışken) hamle türleri; "kart/güvenli":
| | 3/3 (hepsi güvenli) | 3/2 (1 yanlış) | 3/1 (2 yanlış) | 2/2 | 2/1 | 1/1 (zorunlu) |
|---|---|---|---|---|---|---|
| L01 | **%47** | %18 | 0 | %17 | %6 | %13 |
| L02 | **%52** | %24 | 0 | %6 | %9 | %9 |
| L03 | **%45** | %25 | %5 | %12 | %5 | %9 |
| L04 | **%61** | %12 | 0 | %10 | %5 | %11 |
| L05 | **%61** | %11 | %2 | %4 | %14 | %7 |
"Gerçek karar" (tek güvenli kart, 3/1) en çok L03'te ve %5; çoğu hamle ya hepsi güvenli ya tek yanlış.

Rastgele kart seçen oyuncunun, hâlâ hayattayken, o hamlede **yanlış seçme olasılığı**:
| | açılış | orta | son | ortalama | tüm oyunu rastgele bitirme (p_random) |
|---|---|---|---|---|---|
| L01 | %5.7 | %9.4 | %4.1 | **%6.4** | %27.9 |
| L02 | %10.9 | %2.6 | %11.7 | **%8.5** | %9.7 |
| L03 | %8.7 | %9.5 | %12.3 | **%8.9** | %2.0 |
| L04 | %2.6 | %2.8 | %5.5 | **%3.2** | %23.8 |
| L05 | **%0.0** | %2.7 | %16.3 | **%3.1** | %3.9 |
Not: hamle başına %3–9 küçük görünüyor ama 20–43 hamlede birikip tüm oyunu rastgele bitirmeyi zorlaştırıyor. Asıl mesele insan oyuncunun rastgele oynamaması: önizlemede kilitleyeni eleyen oyuncu beşini de %98–100 kazanıyor (L04 %98.0, diğerleri %100).
**Yanlışların neredeyse tamamı "yanlış-hemen".** Gecikmeli (yanlış-sonra) yalnız L04'te var ve hamle başına %0.07–0.08 (L01, L02, L03, L05'te 0). Yani bugün "yanlış seçim" = anında kilit; kısa görüşlü ama önizleme bakan oyuncu bunu görür.

## 2. Neden yanlış olasılığı düşük? (kanıt)
Geometrinin kendisi tehlikeli. Rastgele güvenli sıralarda kalan parçaların **%42–56'sı** o an tuzak (orta/son bölümde %49–71); en az bir kez tuzak olabilen parça payı L01 %58, L02 %81, L03 %76, L04 %82, L05 %79:
| | parça | en az bir kez tuzak olabilen | rastgele güvenli sırada kalanların tuzak payı (ort / açılış / orta / son) |
|---|---|---|---|
| L01 | 19 | 11 (%58) | %41.8 / %24.8 / %48.8 / %54.6 |
| L02 | 26 | 21 (%81) | %53.1 / %33.0 / %64.1 / %63.4 |
| L03 | 34 | 26 (%76) | %51.4 / %27.7 / %60.6 / %67.9 |
| L04 | 38 | 31 (%82) | %47.0 / %24.4 / %57.0 / %60.5 |
| L05 | 43 | 34 (%79) | %55.7 / %34.2 / %63.6 / %71.0 |
Yani elde rastgele bir parça olsaydı yanlış olasılığı %40–55 olurdu; gerçek oyunda %3–9. Aradaki fark **kuyruk sırasından**: kuyruklar, güvenli bir küresel sıradan türetilip her slotta derin→sığ sıralandı. Bu yüzden bir kapı kartı (tuzak olabilen parça) eline geldiğinde kurbanları çoğunlukla zaten yerleşmiş oluyor; kartlar "güvenli olduğu anda" sunuluyor. L05'in ilk üçte birinde yanlış olasılığı sıfır bu yüzden.
Parça sayısı, parça küçüklüğü ya da yeni geometri bu fark için gerekli değil: tuzak olabilen parça zaten çok.

## 3. Hangi değişken en etkili? (bellekte karşı-olgusal denemeler)
Aynı geometri, aynı parçalar, yalnız **kuyruk sırası** değiştirildi; koşullar: çözülebilir kalsın ve önizlemede kilitleyeni eleyen oyuncu hâlâ ≥%90 kazansın (gecikmeli tuzak çoğalıp kumara dönmesin).
- **Hamle başına yanlış olasılığı ayarlanabiliyor:** L01 %6.4 → %25 (hedef %25, ulaşıldı); L02 %8.5 → %25; L03 %8.9 → %21.5. Üst sınır denendiğinde L01 %44, L02 %67'ye çıkıyor, ama o durumda hamlelerin %26–92'si "tek güvenli, iki yanlış" oluyor: istediğin "her hamlede tek doğru cevap" olmasın kuralına aykırı; reddedildi.
- **Hedef dağılım** (3 kartlı hamlelerde ≈%30 hepsi güvenli, ≈%35 bir yanlış, ≈%20 iki yanlış; kalan sonlar 1–2 kartlı) beş levelde de elde edildi (kuyruk sırası tek değişken, ref ile doğrulandı):
| | yanlış/hamle önce → sonra | 3/3 → | 3/2 → | 3/1 → | önizleme bakan oyuncu kazanma | kazanan sıra | gecikmeli tuzak durumu |
|---|---|---|---|---|---|---|---|
| L01 | %6.4 → %13.5 | %47 → %30 | %18 → %35 | %0 → %19 | 1.00 | 6.2e6 → 1.7e5 | 0 → 0 |
| L02 | %8.5 → %10.9 | %52 → %30 | %24 → %35 | %0 → %20 | 1.00 → 0.98 | 3.5e9 → 4.6e7 | 0 → 3 |
| L03 | %8.9 → %10.1 | %45 → %30 | %25 → %35 | %5 → %20 | 1.00 → 0.96 | 3.3e12 → 1.5e10 | 0 → 22 |
| L04 | %3.2 → %7.7 | %61 → %30 | %12 → %35 | %0 → %23 | 0.98 → 0.995 | 3.8e14 → 1.5e11 | 17 → 2 |
| L05 | %3.1 → %7.2 | %61 → %29 | %11 → %34 | %2 → %20 | 1.00 | 8.2e15 → 2.9e12 | 0 → 0 |
Kazanan sıra sayısı 2–4 büyüklük mertebesi düşse de ezberlenemeyecek kadar büyük kalıyor. (Dağılım hedefe göre ayarlandığı için "yanlış/hamle" mutlak değeri bu satırlarda hedef deneyinden daha düşük; ayrı hedefli deneyde %25'e ulaşılabildi.)
**Sonuç:** en etkili değişken kuyruk sırası; özellikle **kapı kartlarının, kurbanları henüz yerleşmemişken ele gelmesi.** Parça geometrisi tavanı belirliyor (tuzak olabilen parça payı %58–82); parça sayısı/boyutu etkisiz.

## 4. Üç soru

**1) Şu an yanlış seçim olasılığı neden düşük?** Geometri tehlikeli (rastgele sırada kalan parçaların ~%40–55'i tuzak) ama kuyruklar bu tehlikeyi siliyor: her slot güvenli sıradan türetilmiş, kapı kartları kurbanlardan sonra geliyor. Sonuç: tüm hamlelerin %45–61'inde 3 kart da güvenli, hamle başına rastgele yanlış olasılığı %3–9, yanlışların neredeyse tamamı anında kilit (L04 hariç gecikmeli yok).

**2) Artırmak için hangi değişken en etkili?** Kuyruk/el düzeni: kapı kartları kurbanlarından önce, tercihen birden fazlası aynı anda elde olacak şekilde sıralanmalı. Aynı geometri ve parçalarla yanlış olasılığını 2–4 katına, 3/3 payını %45–61'den ~%30'a, 3/1 payını ~%20'ye çekmek mümkün ve çözülebilirlik/önizleme-bakan-oyuncu kazanma oranı korunuyor.

**3) "3–4 seçenekten birini seç → resim oluşsun" yapısı korunur mu?** Evet; kural, kartlar, çözücü, UI aynı. Dikkat edilecekler (kanıtsız olanlar işaretli):
- Kuyruklar bölgesel akıştan dağınık sıraya kayıyor (denemelerde 17–37 parça yer değiştirdi). Resmin görsel olarak nasıl oluştuğu (estetik) değerlendirilmedi.
- Gecikmeli tuzak payı düşük tutulmalı (≥%90 ölçütü): yoksa karar, gizli kuyruğa bağlı kumara dönüyor (önceki M2 + queue bulgusu).
- Yanlışın nedeni görünür olmalı: tuzaklarda kopan alan ortalama 21–132 hücre ve çoğu zaman uzakta; sıklık artsa da "neden yanlıştı?" okunmayabilir. Okunurluk ayrı bir değişken (tuzakların yerelliği = parça/kapı geometrisi), bu analizde ölçülmedi.
- Bu kuyruklar hill-climb ile bulundu, tasarlanmadı; bir level'a dönüştürmek için elle okunabilirlik/yerellik kontrolü gerekir.
