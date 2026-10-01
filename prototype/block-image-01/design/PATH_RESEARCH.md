# YOL sistemi tasarım araştırması (yalnız analiz; kod, level, mekanik değişmedi)

Kaynaklar: `src/engine.js`, `src/ui.js`, L01–L05 ve X01–X05 verisi, önceki analiz raporları. Sayılar, başlangıç durumunda salt-okunur ölçümdür (bu rapor için tek seferlik; depoya eklenmedi).

## A. Mevcut problemin tanımı

**Kodda "yol/erişim" ne?** `engine.js` `bfs` (satır 31–43): girişten 4-komşulukla, duvar olmayan ve **boş** hedef hücreler ile zemin üzerinden yayılan bağlantı kümesi. Bir parça yerleşebilir ⇔ tüm hücreleri boş ve bu kümede (`feasible`, satır 45). Yerleşince hücreler kalıcı engel olur; sonra boş bir hedef bu kümenin dışında kalırsa kayıp (`sealedCells`, `place`, satır 47–55). Yani oyunun "yolu" **bağlantı değişmezi**: *kalan her boş hücrenin girişle bağlı kalması.* İşçinin çizilen rotası (`place` içindeki parça başı BFS en kısa yolu) bunun sadece bir tanığı; kuralı o rota belirlemiyor, "herhangi bir rota var mı" belirliyor.

**Neden doğal bir yol gibi görünmüyor?**
1. Yol, resmin kendisi. L01–L05'te zemin hücresi yok (L04'te 4); yürünen yer = henüz boş olan resim. Resim geniş bir lekedir, çizgi değil. Ölçüm (başlangıç): tek hücre dolunca başka hedefi kopartan "boğaz hücresi" payı L01 %1, L02 %2, L03 %0, L04 %0, L05 %2. Tahta pratikte "her yerden gidilebilir".
2. Gösterilen rota yanıltıcı. Seçili kartın işçi izi (`drawTrail`, ui.js:108) arada seçilmiş tek bir en kısa yol; rotaların birleşimi hedef hücrelerin %35–57'sini örtüyor. Oyuncu "benim yolum şurası" diye öğreniyor ama kural "herhangi bir yol"u soruyor; en kısa yolun kapanması çoğu zaman hiçbir şey demek değil.
3. Sonuç yerel değil, küresel. Hata bir parçanın yerleşmesiyle, ama kopan alan başka yerde: kayıpta ortalama kopan hücre L01 31, L02 107, L03 31, L04 21, L05 132. Neden (kapıyı kapatan parça) ile sonuç (uzaktaki alan) arasında görsel bağ yok.
4. Görünmeyenler: zemin/duvar çizilmiyor; hangi hücrelerin boğaz olduğu, bir kartın neyi koparacağı (yalnız geliştirici modu "Kritik" turuncu gösteriyor, ui.js:156), kuyruktaki sonraki kartlar.

**Oyuncu ne görüyor?** Yerleşen canlı bloklar; yerleşmemiş resim soluk (hayalet, ui.js:147); seçili kartın hedefi ve işçi izi (kartı seçmek göndermeden önce bir önizleme adımı); giriş deliği. **Ne göremiyor?** Bağlantı yapısı: hangi parça hangi geçidin tek kapısı, hangi bölgenin iki girişi var, bir hamlenin hangi alanı keseceği.

Sonuç: erişim-kapanma sistemi var ve çalışıyor (tüm tuzaklar ondan), ama zorluk üretmiyor çünkü oyuncu tahtayı "yollu bir dünya" olarak değil "dolacak bir resim" olarak okuyor; kapanma kuralı resmin şeklinden okunamıyor.

L01–L05 ile ilişki: tuzak kartı sayısı 3/19, 5/26, 9/34, 7/38, **2/43**. En çok parçalı level en az tuzak kartlı. Kapanmanın var olduğu yerler (bacak, basamak, bant) zaten **dar geçitler**; zorluk genişlikte değil dar yerde.

## B. Aday yol modelleri

Ortak ön tespit: yol, yeni nesne olmamalı; **hedef hücrelerin oluşturduğu boş kanal** olmalı (zemin yok sayılır), yoksa "kararın bir parçası" olmaz.

**M1 — Dar kanal (tek yol / kapı).** Resmin bir uzvu/boğazı (bacak, gövde, ayak, sap) arkasındaki bölgenin tek girişi. *Algı:* soluk resimde ince bir geçit. *Doğal yerleşim:* hayvan bacakları, ağaç gövdesi, araba kolonu. *Gerekçe:* arkasını bitirmeden kapatma. *Etki:* parça yerleşince geçit dolar. *Tahmin:* kolay (yerel, görünür). *Dekorasyon riski:* düşük. *Uygulanabilir:* şu an var (L01, L02, L05'in özü). *Zorluk potansiyeli:* tek başına düşük, çünkü "en yakını en sona" sezgisi çözüyor (en-derin-önce ilkesi L02 ve L05'i kazandırıyor).

**M2 — İki yollu oda (halka / ortak oda).** Bir bölgeye iki farklı parçanın bulunduğu iki yoldan girilir. *Algı:* resimde halka, kulp, çerçeve, kemer; iki ayrı boş koridor. *Doğal:* kupa kulpu, lastik, simit, pencere çerçevesi, köprü. *Gerekçe:* bir yolu kapatmak serbest, ikinciyi odadan önce kapatmak yasak. *Etki:* A'yı koymak B'yi tehlikeli yapıyor — **iki kart arası çatışma**. *Tahmin:* orta; iki yolu aynı anda izlemek gerekir. *Risk:* düşük (X01–X05 bu yapıyı çalıştırdı; 6–55 kazanan sıra, ajan %50–67). *Mevcut mekanikle uygulanabilir.* *Zorluk:* ilk model ki gerçek A/B/C çatışması üretiyor.

**M3 — Ortak gövde + dallar (ağaç).** Bir koridor birden fazla dalın tek girişi. *Algı:* gövde/dal ağacı, nehir deltası, çatallı bitki. *Gerekçe:* dallar bitmeden gövde kapanmamalı; dallar kendi içinde de yol paylaşabilir. *Etki:* bir dalın kapanması başka dalı etkilemez (bağımsız) ya da etkiler (ortak alt-gövde). *Tahmin:* iyi, ağaç şekli sezgisel. *Risk:* dallar bağımsızsa tek kapı yapısına döner (kolay; L03 benzeri). *Zorluk:* dalların sırası kuyruklarla çakışınca.

**M4 — Bölge→bölge bağlantı (oda grafiği).** Resim odalardan oluşur (ev planı, kale, gemi güvertesi); odaları küçük geçit parçaları (kapı) birleştirir. *Algı:* odalar belirgin, kapılar küçük ve fark edilir. *Gerekçe:* kapı parçası iki bölgeyi bağlar; bir odayı bitirmeden kapıyı kapatma. *Etki:* graf bağlantısı. *Tahmin:* çok iyi; kapılar görünür düğümler. *Risk:* küçük kapı parçaları okunabilirlik sınırında; oda grafiği çok bağımsızsa serbest. *Mevcut mekanikle uygulanabilir.* *Zorluk:* en yüksek tasarım kontrolü; kuyruk sırasıyla gecikmeli sonuç üretilebilir.

**M5 — Görselin kendi yapısından yol (negatif alan).** Yol ayrı bir şey değil; resmin boşlukları (kolların arası, bacak arası, pencere ile kapı arası) kanalı oluşturur. *Algı:* "silüetin içindeki dar boşluk". *Gerekçe:* zorluğu görsel şekil taşır. *Etki:* parçaların şekli kanalı belirler (L şeklinde parça kanalı keser). *Tahmin:* orta. *Risk:* görsel kalitesi ile bulmaca ihtiyacı çakışır (okunur bir kedi/kuş yapmak kanalları serbest bırakmayabilir). *Mevcut mekanikle uygulanabilir ama tasarım zor.* M1–M4'ün "doğal yerleşim" biçimi sayılabilir, ayrı model olmayabilir.

Elenen: **açık fiziksel koridor/yol çizgisi** (zemin hücresi çizip gösterme). Zemin hücresi kararı etkilemiyor (içinden geçilen ama doldurulmayan alan), yani "oyuncunun kararına hizmet etmeyen şey". X-serisinde ben zemin kullandım (9–12 görünmez hücre); bu bir kusur: işçi rotasının yarısı görünmez zeminden geçiyor.

## C. Avantaj / dezavantaj (özet)
| | Avantaj | Dezavantaj |
|---|---|---|
| M1 dar kanal | okunur, mevcut | tek ilke, sezgiyle çözülüyor |
| M2 iki yollu oda | gerçek kart çatışması, simetrik kapanma | iki yolu izlemek zihinsel yük; aynı ilke tekrar |
| M3 ağaç | doğal şekil, ortak yol | dallar bağımsızsa tek kapıya döner |
| M4 oda grafiği | görünür düğümler, en kontrollü | küçük kapı parçaları okunabilirlik riski |
| M5 negatif alan | görsel ile birleşik | görsel kalite ile çatışır |

## D. Mevcut çekirdekle uyum
M1–M5'in hepsi yalnız geometri + parça şekli + kuyruk sırasıyla kurulur; yeni mekanik/kaynak yok. M2 ve M4 uygulanabilirliği X-serisiyle gösterildi. Zemin hücresi kullanımı çekirdeği bozmaz ama prensibe aykırı (karara hizmet etmiyor).

## E. Gerçek oyuncu kararına dönüşme potansiyeli
**A/B/C kararının anlamlı olması için yolun özellikleri** (L01–L05 + X-serisinden çıkarım):
1. **Okunur kanal:** yol, soluk resimde ayırt edilen dar boş bölge olmalı (hedef hücrelerden oluşmalı).
2. **Dar:** kapanması için az hücre yetmeli (boğaz genişliği ~1–3 hücre). Geniş leke = hiç kapanmaz (L01–L05'te boğaz hücre %0–2).
3. **Az alternatif:** 0 alternatif = tek kapı (sezgiyle çözülür), çok alternatif = kapanmaz; 1–2 alternatif karar üretiyor (X-serisi).
4. **Yerel ve komşu:** kapatılan alan, kapatan parçanın bitişiğinde/görünür yakınında olmalı. Bugünkü küresel kopmalar (ortalama 21–132 hücre) öngörülemez.
5. **Paylaşım:** en az iki eldeki kart aynı kanala bağlı olmalı; birini koymak diğerini tehlikeli yapmalı. Tek kartı ilgilendiren kanal karar değil, kural.
6. **Kısa gecikme:** sonuç 1–3 hamlede belli olmalı; neden ile sonuç yakın.
7. **Sonuç gösterilmemeli ama çıkarılabilmeli.** "Kritik" modu açıksa karar "turuncudan kaçın"a çöker (1 hamlelik kontrol beşi de kazandırıyor); kapalıysa çıkarım resmin şeklinden yapılmalı. Bu denge tasarım problemi.

Neden doğru: oyuncu A'yı göndermeden önce (seçim önizlemesi var) A'nın hedefini, bitişik boş kanalları ve B'nin aynı kanala bağlı olduğunu soluk resimde görebiliyorsa "A koyarsam B'nin yolu kapanır" çıkarımı yapabilir. Bu zinciri bozan her halka (geniş leke, uzak sonuç, görünmeyen zemin, 5+ hamle gecikme) kararı rastgele basmaya çevirir.

## "Görsel yol" ile "gameplay yolu"
- **Görsel yol (feedback):** işçi izi ve animasyon. Karar girdisi değil; sonucu anlatıyor ve arbitrary bir en kısa yol. Mevcut haliyle dekoratif.
- **Gameplay yolu:** boş hücrelerin girişle bağlantı yapısı (bağlantı değişmezi). Bu, karar girdisi olur yalnız şunlar doğruysa: (a) yapı resimde kanal olarak seçilebiliyor, (b) seçimden önce erişilebilir.
- Dar kanallarda ikisi birleşir (tek yol = en kısa yol): işçi izi gerçekten "yol" olur. Geniş lekede ayrışırlar. Bu, M1–M4'ün ortak avantajı.
- Zemin hücreleri ne görsel ne gameplay: kaldırılmalı.

## Zorluk katmanları ve oyuncunun düşüncesi
| Katman | Düşünce |
|---|---|
| tek yol | "Bu geçit kapanmadan arkasını bitirmeliyim." (L01, L02, L05 — aynı soru) |
| iki yol | "Bir yol kapansa öbürü var; ikincisini odadan önce kapatamam." (X-serisi) |
| ortak yol | "Bu koridor üç dalın girişi; dalların hepsi bitmeden kapanamaz." (ağaç) |
| dar boğaz | "Bu 1–2 hücrelik geçit tek; dolmadan arkası bitmeli." |
| dallanma | "Hangi dalı önce bitirirsem diğerinin yolu sağlam kalır?" (dallar yol paylaşıyorsa) |
| yol sıralaması | "Kuyruk sırası ile açık kalan yol örtüşüyor mu?" (L04'ün gecikmeli tuzağı) |
| bir parça başkasının yolunu kapatır | "Bu kart B'nin kapısı; B'den önce yok." |
| aynı bölgeden çok parça | "Üç kart da aynı geçide bağlı; hangi sırayla?" (en güçlü çatışma) |

## Sahte zorluklar (L01–L05 kanıtları)
- Daha fazla parça: L05 43 parça, tuzak kartı 2; 1 hamlelik güvenlik kontrolü beşi de kazandırıyor.
- Daha küçük parça: ortalama hücre 24→10 düşerken tuzak kartı çeşidi 3→2; okunabilirlik riski arttı, zorluk artmadı.
- Daha fazla decision state: L05 318, hepsi aynı iki kartın tekrarı; ilk üçte birde eller %98 serbest.
- Daha fazla renk / karmaşık görsel: görsel yükü artırıyor; kapanma yapısı değişmiyor.
- Daha fazla hamle: ilk 10 hamle güvenli, son bölüm aynı kapıların son kartları.

## F. Açık sorular
1. Sonuç (kritik alan) oyunculara hiç gösterilmeli mi? Gösterilirse karar basitleşir, gösterilmezse çıkarım resimden yapılmalı.
2. Zemin/duvar hücreleri tamamen kaldırılsın mı (prensip: karara hizmet etmeyen şey yok)? Giriş çıkıntısı hariç.
3. "Herhangi bir kopan hücre = kayıp" kuralı küresel; level tasarımında kopan alanı kapatan parçaya bitişik tutmak (yerel sonuç) yeterli mi, yoksa kuralın kendisi mi sorun? (Mekanik değişikliği değil, tasarım kısıtı olarak.)
4. İşçi izi korunsun mu? Yanıltıcı en kısa yol yerine ne gösterilmeli (hiçbir şey?).
5. Hangi görseller doğal olarak halka/ağaç/oda yapısı taşıyor ve okunur kalıyor (kupa, ağaç, ev planı, köprü)?
6. Telefon ölçeğinde 1–3 hücre genişliğindeki kanal algılanıyor mu? Eşik ölçülmedi.
7. Gecikmeli sonuç hedefi 1–3 hamle mi? Hata sonrası nedeni görme (ör. kopan alan vurgusu zaten var) yeterli mi?

## G. Sonraki deney için önerilen en küçük test (level üretme yok)
Tek değişkeni izole et: **"Sonuç gösterilmesi" (bilgi dengesi).** Mevcut X01 (ve X05) aynı tahtada, yalnız yol modunu değiştirerek iki kez oynanır: **Kapalı/İz** ve **Kritik**. Soru: Kritik açıkken karar "turuncudan kaçın"a çöküyor mu, kapalıyken resimden çıkarım yapılabiliyor mu? Yeni tahta, kod, level gerekmez.
İkinci adımda (ayrı onayla), yine tek değişken: **kanal genişliği** (aynı iki yollu oda topolojisi, kapı genişliği 1 hücre vs geniş), geri kalan her şey sabit.
