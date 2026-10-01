# Karar-üreten deney adayları X01–X05 (yeni mekanik/UI yok; L01–L05 değişmedi)

Amaç: üç kart başlangıçta güvenliyken seçimin geleceği değiştirdiği, sonucun birkaç hamle sonra belli olduğu, birden fazla kazanan sıranın bulunduğu küçük tahtalar. Başarı kriteri "çok parça/küçük parça/çok karar durumu" değil.
Oyna: `dist/block-image-X01.html … X05.html` (aynı oyun; kartlar 1-2-3 = soldan sağa). Resim haritası: `X0N_map.png`. Kazanan sıralar: `SOLUTIONS_SPOILER.md` (oynamadan açma).
Test için öneri: yol modunu **Kapalı** veya **İz** bırak; **Kritik** modu seçili kartın anında kilitleyeceği hücreleri gösterdiği için testi bozar.

Ortak mekanizma (hepsinde bu tek yapı çıktı): **iki kapılı oda.** Bir odaya iki parçadan (kapı) girilir. Birini koymak güvenli; ikinciyi odadan önce koymak odayı mühürler. Kapıların kuyruktaki yeri ve odanın kuyruğa nerede durduğu "şimdi mi, sonra mı" sorusunu üretiyor. Kapanma ilişkisi burada hep simetrik çıktı (A, B'yi kapatıyorsa B de A'yı kapatıyor); A→B→C→A gibi yönlü bir döngü bu denemelerde üretilemedi.

| | X01 Üç oda | X02 Taç | X03 Köprü | X04 Halka (kontrol) | X05 Üç kapı (mini) |
|---|---|---|---|---|---|
| parça / hücre | 10 / 48 | 10 / 59 | 8 / 30 | 7 / 35 | 5 / 26 |
| kuyruklar (kart 1/2/3) | 4/3/3 | 4/3/3 | 3/3/2 | 3/2/2 | 2/2/1 |
| başlangıç: 3 kart da güvenli | evet | evet | evet | evet | evet |
| başlangıç: kazandıran ilk hamle | 2/3 | 2/3 | 2/3 | 3/3 | 2/3 |
| başlangıçta her hamle başka bir kartı kapatıyor | evet (3/3) | evet (3/3) | evet (3/3) | **hayır** | evet (3/3) |
| kazanan sıra sayısı | 55 | 50 | 28 | 37 | 6 |
| yalnız "anında mühürleme"den kaçınan ajanın kazanma oranı | %58 | %53 | %67 | %53 | %50 |
| erişilebilir durum / çatal durumu* | 29 / 4 | 38 / 4 | 23 / 1 | 26 / 5 | 12 / 3 |
\*çatal: elde ≥1 kazandıran ve ≥1 "şimdi güvenli ama sonra kaybettiren" kart olan durum.

## Her adayda ilk hamle ne yapıyor? (kartlar 1-2-3)
**X01 Üç oda** — el: Kapı B · Kapı C · Kapı D. Oda 1 (A|B), Oda 2 (B|C), Oda 3 (C|D); her odanın üstünde bir tepe.
- Kapı B → sonraki el: Tepe 2 ok · **Kapı C mühürler (Oda 2)** · Kapı D ok. Kazanan 30 sıra.
- Kapı C → sonraki elde üç kart da mühürler (hemen ertesi hamlede "hepsi kötü"). Kayıp.
- Kapı D → Kapı C artık Oda 3'ü mühürler; Kapı B ok. Kazanan 25 sıra.
Fark 2. hamlede belli oluyor. Çatal: ortada 4 durum, en geç 3 hamle sonra kayıp.

**X02 Taç** — el: Üst bar · Kapı C · Kapı B. U şekilli oda (Sol sütun–Üst bar–Sağ sütun) A ve C kapılarına bağlı; iki oda + tepeleri.
- Üst bar → Kapı C artık Sağ sütunu mühürler. Kazanan 22 sıra.
- Kapı C → Kayıp; ama iki hamle daha güvenle oynanıyor, mühür 4. hamlede (Üst bar kartı Sağ sütunu mühürler). Gecikmeli.
- Kapı B → Kapı C artık Oda 2'yi mühürler. Kazanan 28 sıra.

**X03 Köprü** — el: Sağ üst · Sol üst · Sol orta. İki sütun, üstte köprü, köprünün tepesinde parça.
- Sağ üst → kayıp, iki güvenli hamle sonra (4. hamle) mühür (Köprü+Tepe). Gecikmeli.
- Sol üst → Sağ üst artık Köprü/Tepe'yi mühürler. Kazanan 21 sıra.
- Sol orta → Sağ üst artık daha fazlasını mühürler. Kazanan 7 sıra.

**X04 Halka (kontrol)** — el: Üst çubuk · Sağ üst · Sol üst. Üç kart da kazandırıyor ve hiçbiri başka kartı kapatmıyor (14/18/5 kazanan sıra). Çatışma orta oyunda (5 çatal durumu, en geç 3 hamle sonra). Amaç: açılışta çatışmasız bir tahta nasıl hissettiriyor, karşılaştırmak.

**X05 Üç kapı (mini, 5 hamle)** — el: Kapı A · Kapı C · Kapı B. İki ortak oda.
- Kapı A → Kapı B artık Oda 1'i mühürler. 3 kazanan sıra.
- Kapı C → Kapı B artık Oda 2'yi mühürler. 3 kazanan sıra.
- Kapı B → sonraki el: A ve C ikisi de mühürler; kayıp 2. hamlede.
En küçük "orta kapıyı sona bırak" dersi; büyük ihtimalle çok kolay.

## Neden gerçek oyuncu kararı olabilir / olamaz (dürüst)
- Güçlü yanı: karar, tahtadaki görünür geometriden okunuyor ("bu oda iki kapılı; ikincisini kapatmadan odayı doldur"). Resim zaten tahtada soluk görünüyor, mağdur parça görünür.
- Zayıf yanı 1: hepsi **tek ilke** (iki kapılı oda). Çeşitlilik kuyruk sırasından geliyor.
- Zayıf yanı 2: kayıp çoğunlukla 2.–4. hamlede belli oluyor; neden–sonuç mesafesi kısa. Oyuncu hatanın sebebini muhtemelen anlar, ama "birkaç hamle sonra" yerine "hemen sonra" daha doğru.
- Zayıf yanı 3: X03'te çatal durumu yalnız 1 (tahtanın kalanı serbest); X05 çok küçük; X01'de en kötü hamle ertesi hamlede belli.
- Çözüm sayıları (6–55) ezberi imkânsız kılmıyor; 5 hamlelik X05'te 6 sıra var.
- Hiçbiri insan testiyle doğrulanmadı. Sen oynayacaksın: (1) hamleden önce düşündün mü, (2) seçim diğerlerini etkiledi mi, (3) hatayı anladın mı.

## Doğrulama
- Her aday: mevcut `ref.py` kesin çözücüsüyle kazanan sıra sayısı hızlı kitle birebir (assert), parity 35/35, tarayıcı QA (kazanan/karışık/ters dizi → kazandı, tuzak yolu → mühürlendi, telefonda taşma yok, console hatası yok). Tek kasıtlı FAIL: "doğal palet" kontrolü (adaylarda her parça ayrı renk, deney okunurluğu için). `qa_hand` LEGAL OPTION kasıtlı FAIL (gecikmeli kayıp durumları) ve "piece accounting" eşiği (≥100 durum) küçük tahtalarda uygulanamaz.
- Arama: `tools/lab/` (labkit.py, search/hill/filt/redo.py). Şablonlar elle çizildi (T3, Taç, Köprü, Halka, Üç kapı); kuyruk sırası tepe-tırmanışlı aramayla seçildi. Arama kitindeki bir önbellek hatası (nesne kimliği) bulundu ve düzeltildi, adaylar düzeltilmiş kitle yeniden seçildi/doğrulandı.
