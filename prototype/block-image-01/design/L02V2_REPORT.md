# L02-V2 — Yol geçişi deneyi (kaktüs)

Dosya: `dist/block-image-L02V2.html` (eski L02 "Ev" dosyalarının üzerine yazılmasın diye V2). Harita: `design/L02V2_map.png`. L01/L01-V4 ve motor/UI/kurallar değişmedi; yeni mekanik, UI, path göstergesi, NEXT, gatekeeper yok.
Doğrulama: parity 29/29; `qa_hand` hepsi geçti (çıkmaz 0, kazanılamaz ulaşılabilir durum 0); tarayıcı QA tümü geçti (kazanan/karışık/ters dizi → kazandı, tuzak yolu → mühürlendi, telefon, console); ref ↔ hızlı çözücü birebir.

## 1. Görsel ne?
Saksıda kaktüs, 36×24, 346 hücre, 27 parça (ort. 12.8, min 2, max 48 hücre). Hayvan değil bitki. İlk denediğim zürafa elendi: ince uzuvlar tahtayı doldurmadı (223 hücre, seyrek).

## 2. Doğal geçiş nerede?
Resmin kendi negatif alanı: iki kol dirsekli (gövdeden yatay çıkıp yukarı dönüyor), kolun gövdeyle birleştiği yer **3 hücre yüksekliğinde dar bir bağlantı**, kolun içi 4 hücre genişliğinde dikey koridor; kolların altındaki ve içindeki boşluk resmin dışı (zemin hücresi yok). Üst çiçeğin gövdeye bağlandığı boyun 4 hücre. Giriş saksının orta gövdesinin altında.

## 3. Hangi parçalar bu geçişi kullanıyor?
- Sol kol: `ARM_L_CON` (3×3 bağlantı) → `ARM_L_ELB` (dirsek) → `ARM_L_UP` (dikey) → `FLOWER_L` (+ `SPINE_7` cebi).
- Sağ kol (daha yukarıda): `ARM_R_CON` → `ARM_R_ELB` → `ARM_R_UP` → `FLOWER_R` (+ `SPINE_8`).
- Gövde dilimleri `TR_1…TR_4` (kolların girişine bitişik olanlar `TR_2`, `TR_3`), `TR_1` ← `FLOWER_T`; saksı `POT_C` (girişin üstü) → `RIM_*`/`POT_*`.
- 8 diken (2 hücrelik krem çizgi) gövde/kol parçalarının içinde cep.

## 4. Hangi parçanın yerleşimi geçişi kapatabiliyor? (yanlış seçimlerin payı)
- Kolun içindeki parça kendi ötesini kapatır: `ARM_L_UP` → `FLOWER_L` %17; `ARM_L_ELB` → `ARM_L_UP`+`FLOWER_L` %9; `ARM_R_ELB` → `ARM_R_UP` %5; `ARM_L_CON` → dirsek+dikey kol %4–8 (38 hücre).
- Gövde dilimi kolun girişini kapatır: `TR_3` → `ARM_L_CON` (+dirsek) %10; `TR_2` → `TR_1` (üstü) %7.
- Cepler ve saksı: `ARM_R_UP` → `SPINE_8` %7, `RIM_C` → `TR_4` %4, …
Çeşitli: en sık tek ilişki %17; yanlış olayların %71'i kolla ilgili.

## 5. Oyuncu bunu görsel olarak anlayabilir mi? (çıkarım; insan testi yok)
Ölçüm: tüm yanlış olaylarda (%100) kapanan bölgenin tek kalan soluk komşusu yerleştirilen kart; kapanan alanla kart arasındaki temas çoğunlukla dar (olayların **%59'unda ≤4 hücre**, medyan 4; L01-V4'te %24, medyan 6) ve olayların %38'inde kapanan bölge birden fazla parça (L01-V4'te %5): "kolun içini/ötesini tıkıyorum". Görsel ipucu: kolun soluk koridoru ve ucundaki çiçek; kartın hedefi o koridorda bir dar boğazı dolduruyorsa ötesi (soluk) kapanır. BFS/hesap gerekmez; ancak "koridorun ötesini" görmek için kartın hedefini kol üzerinde izlemek gerekiyor.
Zayıf noktalar: kollar yeşil tonlarda, dilimler arasındaki sınırlar tek bakışta zor seçilebilir; 4 hücrelik koridorun "yol" olarak algılanması test edilmedi; kapanan alan bazı olaylarda büyük (38 hücre) ama bitişik.

## 6. Queue nasıl düzenlendi?
```
1: FLOWER_R · SPINE_3 · ARM_R_ELB · FLOWER_T · ARM_R_CON · TR_2 · FLOWER_L · ARM_L_CON · TR_4
2: SPINE_2 · SPINE_8 · SPINE_4 · SPINE_7 · RIM_L · POT_R · TR_1 · ARM_L_ELB · SPINE_5
3: ARM_R_UP · RIM_R · SPINE_1 · POT_L · ARM_L_UP · TR_3 · SPINE_6 · RIM_C · POT_C
```
Mantık: her kol uçtan tabana (çiçek → dikey → dirsek → bağlantı) sırayla geliyor ama parçalar üç slota dağıtılmış; sağ kol açılışta, sol kol orta/son fazda. Seçim yöntemi: geometri sabit, yalnız sıra; bellekte hill-climb ile hamle başına yanlış ≈%28, hedef dağılım, **gecikmeli tuzak 0**, kapanma bitişik ve kol/geçit olaylarının payı yüksek olacak şekilde; sonra ref ile doğrulandı. Gizli kumar yok: önizlemede anında kilitleyeni eleyen oyuncu her zaman kazanıyor. Açılış eli `FLOWER_R · SPINE_2 · ARM_R_UP`: ilk kart `ARM_R_UP` yanlış (çiçeği ve cebi kapatır), diğer ikisi güvenli.

## 7. Solver'a göre güvenli/yanlış dağılımı (kazanan yolda hamle türleri; kart/güvenli)
| | yanlış/hamle* | 3/3 | 3/2 | 3/1 | 2/1 | 1/1 | gecikmeli | kazanan sıra |
|---|---|---|---|---|---|---|---|---|
| L01-V4 | %22.4 | 19 | 35 | 16 | 6 (+2/2: 4) | 20 | 0 | 6.3e4 |
| **L02-V2** | **%28.4** | 20 | 35 | **25** | 12 | 7 | **0** | 1.3e6 |
\*rastgele kart seçen oyuncunun hamle başına yanlış seçme olasılığı. Karar/serbest/zorunlu durum 85/53/2; anında tuzak durumu 106. Tüm oyunu rastgele bitirme olasılığı ~5e-6 (insan rastgele oynamıyor; önizleme bakan oyuncu %100 kazanıyor).

## 8. Yanlış seçimde kapanan bölge ne kadar yakın?
Kapanan alana en yakın hücre: ort. 1.0, medyan 1 hücre (her olayda bitişik). Kapanan alanın yerleştirilen parçaya ortalama uzaklığı **2.5, medyan 2.0** hücre (L01-V4: 2.0 / 1.8). Olay başına kapanan alan ort. 19 hücre (L01-V4: 14); en uzun örnek kol bağlantısı `ARM_L_CON` → dirsek+dikey kol: 38 hücre, ortalama uzaklık 5.2. Yani "bir kademe" fark: daha büyük ve daha çok parçalı kapanış, hâlâ bitişik.

## Dürüst notlar
- L02-V2, L01-V4'ten bir kademe zor: yanlış/hamle %22→%28, 3/1 %16→%25, geçit olayları %24→%59. Hâlâ tek doğru cevaplı değil (3/3 %20, 3/2 %35).
- Test: Kritik modunu kapatın; açıksa karar "turuncudan kaçın"a çöker.
- Tasarım hill-climb ile bulundu; okunurluk ve resmin kuruluş estetiği (kuyruk dağınık) insanla doğrulanmadı.
- Sol/sağ kol farklı fazlarda ortaya çıkıyor; bu "farklı faz" tasarım gereği değil, aramanın sonucu.
