# M2 — İki yollu oda: geometri tasarımı (yalnız analiz; kod, level, UI, mekanik yok)

Gösterim (level verisi değil): `#` = resim dışı (çizilmez, yürünmez) · harf = hedef hücre (soluk resmin parçası) · `I` = giriş hücresi (mevcut oyundaki tek hedef-olmayan hücre; arayüzde tahtanın altında delik olarak çizilir).
Doğrulama durumu: aşağıdaki geometriler `engine.js` kuralları (satır 31–55) ve `ui.js` giriş çizimi (satır 106) okunarak elle çıkarıldı; çözücüden geçirilmedi (kod yazmama kısıtı). Elle türetilen sonuçlar açıkça belirtildi.

## 0. Önce kısıt: zemin yoksa giriş nasıl iki yol açar?

Zemin hücresi yok. Girişten (`I`) yayılma yalnız onun **dört komşusundaki hedef hücrelere** gider. Giriş tek bir komşuya bakıyorsa o komşuyu içeren parça **tek kapı**dır ve M2 olmaz (aşağıda "yanlış M2"). İki bağımsız yol ancak şöyle kurulur: **giriş resmin alt kenarında bir girintiye oturur; solunda ve sağında (gerekirse üstünde) *farklı* parçaların hücreleri vardır.** Bir girişin en fazla 3 komşusu olabilir: en çok 3 yol.
Sonuç: yol sayısı ve yolların başlangıcı doğrudan girişin etrafındaki hücre dizilimiyle belirlenir; zemin gerekmez. (`ui.js:106` deliği giriş sütununda tahtanın altına çizer; giriş satırının yanında hedef hücre olması çizimi bozmaz — doğrulanmadı, çalıştırılmadı.)

## Yanlış M2 örnekleri (tek kapı sayılır, kabul edilmez)
```
(a) ortak sap          (b) oda yalnız bir yola bağlı      (c) iki yolu çaprazlayan dolgu
 # R R R #               # R R R #                          # R R R #
 # A # B #               # A # # #                          # A X B #
 # A C B #               # A # B #                          # A X B #
 # # I # #               # A I B #                          # A I B #
```
(a) Yollar ortak bir sap parçasında (C) birleşiyor: giriş tek hücreye bakıyor, C tek kapı. (b) B yolu hiçbir yere bağlanmıyor; oda yalnız A'ya bağlı. (c) Aradaki dolgu X iki bacağı birbirine bağlıyor; yollar bağımsız değil, A yerleşince B artık "ayrı bir yol" değil.

## 1–9. En küçük anlaşılır geometri (Aday 1: **Kemer**)
```
     c0 c1 c2 c3 c4
 r0   #  R  R  R  #
 r1   #  A  #  B  #
 r2   #  A  I  B  #
```
7 hedef hücre, 3 parça.
1. **Geometri:** ters U (kemer). İki dikey bacak, üstte bunları birleştiren çatı.
2. **Giriş:** alt satırda, iki bacağın arasındaki tek hücrelik boşlukta `I` (r2,c2). Komşuları: solda A'nın (r2,c1), sağda B'nin (r2,c3); üstü resim dışı.
3. **Oda:** üst, `R` = (r0,c1..c3).
4. **İki yol:** sol bacak ve sağ bacak. Aralarında resim dışı boşluk (c2, r1) olduğu için iki yol hiçbir hücre paylaşmaz ve çapraz bağ yok.
5. **Parçalar:** A = sol bacağın tamamı, B = sağ bacağın tamamı, R = oda. Bacağı kesen parça, yolun tüm kesitini doldurmalı (burada kesit 1 hücre).
6. **Hücreler:** A = (r1,c1),(r2,c1); B = (r1,c3),(r2,c3); R = (r0,c1),(r0,c2),(r0,c3).
7. **A yerleşince B neden erişilebilir?** B'nin hücreleri girişe doğrudan bitişik (r2,c3); R, B'nin tepesi (r1,c3)→(r0,c3) üzerinden bağlı. Kalan tüm boş hücreler (B, R) hâlâ girişe bağlı.
8. **B de yerleşirse?** R'nin iki bağlantısı da dolu: (r0,c1)'in altı A, (r0,c3)'ün altı B, (r0,c2)'nin altı resim dışı → R boş ama erişilemez → mühür. Elle türetilen kural: *oda, ikinci yoldan önce doldurulmalı.* Kazanan sıralar: R-A-B, R-B-A, A-R-B, B-R-A (6 sıranın 4'ü); A-B-R ve B-A-R kaybettirir.
9. **Seçimden önce görsel ipuçları:** (i) soluk resim bir kemer: iki ayrı dikey kanal ve aralarında görünen boşluk; (ii) delik tam bu boşluğun altında; (iii) A ve B kartları aynı biçimde (dikey çubuk), R kartı yatay; (iv) kart seçilince hedefi parlıyor: "bu sol yolun tamamı". Bir şey çözülmüyor: bacağın "en yakın" olduğu için insana "önce yerden yukarı" sezgisini vermesi; bu sezgi burada yanlış (ikinci bacak kaybettirir) — hem risk hem testin işe yarayan tarafı.

## Aday 2: **At nalı (iki parçalı bacaklar)**
```
     c0 c1 c2 c3 c4 c5 c6
 r0   #  R  R  R  R  R  #
 r1   #  A2 #  #  #  B2 #
 r2   #  A2 #  #  #  B2 #
 r3   #  A1 #  #  #  B1 #
 r4   #  A1 A1 I  B1 B1 #
```
15 hücre, 5 parça (R 5; A2 2; A1 3; B2 2; B1 3). Giriş ayakların arasında; ayaklar (r4,c2),(r4,c4) girişe değiyor.
- Halka yapısı: A1–A2–R–B2–B1 ve giriş A1 ile B1'e bağlı. Elle türetilen kural: **doldurulmuş parçalar, A1-A2-R-B2-B1 sırasında hep bitişik bir aralık olmalı** (tek yerde başlar, yalnız bitişiğine uzar). Örn. {A2,B2} kaybettirir (R kopar); {A1,R} kaybettirir (A2 kopar); {A2} ve {A2,R} güvenli.
- Her parçanın iki yönlü yolu var: saat yönü ve ters yön. "Oda" kavramı bulanıklaşıyor; R'nin odalığı yalnız çatının geniş olmasıyla vurgulanıyor.

## Aday 3: **Üç yollu tarak**
```
     c0 c1 c2 c3 c4 c5 c6
 r0   #  R  R  R  R  R  #
 r1   #  A  #  C  #  B  #
 r2   #  A  #  C  #  B  #
 r3   #  A  #  C  #  B  #
 r4   #  A  A  I  B  B  #
```
18 hücre, 4 parça (A 5, B 5, C 3, R 5). Giriş üç komşuya bakıyor: sol A, üst C, sağ B. Üç ayrı kanal, iki dar resim dışı yarık.
- Kural (elle türetilen): oda, **üç yoldan sonuncusu kapanmadan** doldurulmalı; iki yol serbestçe kapatılabilir.
- Not: bu "iki yollu" değil, M2'nin n-yollu genellemesi. M2 olarak kabul etmek istemezsen çıkar; tek kapılı değil ama "iki yol" tanımına uymuyor.

## Adayların değerlendirmesi (seçim yok)

| Soru | Aday 1 Kemer | Aday 2 At nalı | Aday 3 Tarak |
|---|---|---|---|
| İlk bakışta yol görülür mü | evet (iki bacak, 7 hücre) | evet; halka okunur ama "oda" belirsiz | evet; üç kanal, fakat sayma gerekir |
| İki yol ayrışır mı | evet, aralarında tek hücre boşluk | evet, geniş boşluk | evet, yarıklar 1 hücre (ince) |
| A–B arasında gerçek ilişki | evet: ikisi birlikte odayı keser | evet: ama ilişki *tüm halka* (5 düğüm); çiftli değil | evet: üçlü; "son yol" ilişkisi |
| Sonuç yerel mi | evet (R bitişik, iki bacağın tepesi) | evet ama kopan parça (A2/R/B2) herhangi biri olabilir | evet (R) |
| Doğal görselde yer | iki bacaklı hayvan/kuş/kedi önden, kapı kemeri, köprü, at nalı, diş (iki kök) | aynı + ayaklı kuş/kemer | ahtapot/denizanası (kollar → baş), tarak, çatal, taç |
| Telefonda okunur mu | küçük kart olarak evet; 36×24 resimde bacaklar 1 hücre = ~10 px ve aradaki boşluk da 1 hücre: sınırda → bacak ve boşluğu ≥2 hücre yapmak gerekir | 5 parçada çatı/bacak ayırımı daha net; yine 2 hücre genişlik gerekir | yarıklar 1 hücre: telefonda zor, ≥2 gerekir (genişliği artırır) |
| Yeni mekanik gerekir mi | hayır (giriş girinti verisi) | hayır | hayır |
| İşçi izi olmadan anlamlı mı | evet; iki yol resimden okunuyor | evet | evet |
| Kritik olmadan anlaşılır mı | evet | büyük ölçüde; halka kuralı daha soyut | sayma yükü var |

**Avantaj / risk (seçmeden):**
- Aday 1: en berrak, "iki yol–bir oda" tanımına birebir; 3 kart hepsi elde görünür. Risk: tek başına **çok kolay** (3 hamle) ve en-derin-önce / "odayı önce" sezgisi çözer; ayrıca R elde görünüyorsa karar yok.
- Aday 2: kuyruk ve kart çatışması için malzeme (5 parça, birden çok geçerli sıra), yine de kural tek cümlede ("bitişik uzat"). Risk: oda ile yol arasındaki ayrım bulanık; ilişki çiftli değil halkasal, oyuncu kuralı çıkaramayabilir.
- Aday 3: "kalan yol sayısı" gibi yeni bir ilişki ekliyor, görsel olarak canlı (kollar). Risk: iki yollu tanımın dışına çıkıyor, yarıklar ince, sayma hamleden önce zihinde tutulması gereken ek bilgi.

## Genel uyarılar (adaydan bağımsız)
1. **Geometri tek başına karar üretmez.** Oda elde bir kart olarak görünüyorsa oyuncu önce odayı gönderip konuyu geçer. Karar, odanın kartı bacaklardan *sonra* geldiğinde doğar; bu kuyruk problemi ve bu aşamada kapsam dışı. M2 geometrisi yalnız "yol okunabilir mi" sorusunu test eder.
2. **İşçi izi yanıltabilir.** İki bacak eşit uzunlukta olduğundan en kısa yol seçimi keyfi (komşu sırası belirler); iz bir bacağı gösterir, öbürünü değil. İz yalnız feedback.
3. **"Yerden yukarı inşa" sezgisi** (bacakları önce koy) burada yanlış sonuç veriyor. Bu hem test için tuzak hem de kullanıcı hayal kırıklığı riski.
4. **Hata sonrası neden görünür:** mühürlenen oda bitişik ve tek parça; neden–sonuç mesafesi 1 hamle. Yerel ve kısa.

## "M2 çalışıyor" demek için insanın göstermesi gereken davranış
Kendiliğinden, **hamleden önce** ve **öbür yola atıf yapan** bir öngörü: "Bu bacağı şimdi koymayayım; öbür bacak da dolarsa oda kalır" ya da A yerleştikten sonra B'ye basmadan önce duraksayıp odayı seçmek. Ölçütler:
1. Kritik ve işçi izi yardımı olmadan, ikinci yol parçasına basmadan önce odayı/başka kartı seçiyor, nedenini söylerken *kalan yolu* anıyor ("öbür taraf açık kalmalı").
2. Seçimi, ikinci yolu cazip kılan bir durumda yapıyor (en yakın/en büyük kart ikinci bacaksa) — rastgele güvenli kart seçmekten ayrılması için.
3. Aynı ilişkiyi farklı bir geometride (Aday 1 → 2) yeniden uygulayabiliyor; ezber değil.
4. Hata yaparsa nedeni doğru söylüyor ve tekrar oynarken üçüncü bir deneme gerekmeden sırayı düzeltiyor.
Yeterli olmayan kanıt: yalnız kaybettikten sonra açıklama; "yerden yukarı doldururken şans eseri geçmek"; "uzaktakini önce" gibi genel bir kurala dayalı çözüm (o kural bu geometride de odayı önce koyar ve M2'yi test etmez). Gerekli mi, oyuncunun "A'yı şimdi koymayayım çünkü bu taraf kapanır" cümlesini aynen kurması? Hayır; zorunlu olan, **kalan alternatif yola dair doğru bir öngörü**. Cümle biçimi önemli değil, ama kararın "diğer yol" üzerinden gerekçelendirilmesi gerekli.
