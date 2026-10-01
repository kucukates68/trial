# M2 + queue/hand karar araştırması (yalnız analiz; level, HTML, kod, mevcut dosyalara değişiklik yok)

Yöntem: ölçümler geçici çözücü betiklerle (depoya eklenmedi) yapıldı; mevcut `labkit` (daha önce `ref.py` ile çapraz doğrulandı) çağrıldı. Mevcut kurallar aynen: 3 kartlık el, sabit geometri, tek hedef, BFS erişimi, kalıcı hücre, kapanma = kayıp.

**Kapsam notu (önemli):** Kemer'in 3 parçası var (A, R, B). Slotlar yer değiştirdiğinde tek bir düzen kalıyor (kuyruk değişkeni yok). Queue'nun anlam kazanması için ≥4 parça gerekir. Bu yüzden **aynı 7 hücrelik Kemer silüetini** koruyup yalnız parça sınırlarını böldüm (hücreler değişmedi; yani oyuncunun gördüğü soluk resim aynı). Ring sırası: `A1 – A2 – R(çatı) – B2 – B1`, giriş A1 ve B1'e bitişik. Bunu "geometri sabit" kısıtının yorumu olarak seçtim; aksini istersen söyle.
```
 # R  R  R  #        7 hücre ring:  (2,1) (1,1) (0,1) (0,2) (0,3) (1,3) (2,3)
 # A2 #  B2 #        k parçaya her bölünüş = ring'in k bitişik dilimi
 # A1 I  B1 #
```
Tarananlar: k3 Kemer (1 düzen), k4 (12), k5 (120 → 90 çözülebilir), k6 (1200 → 556), k7 (12 600 → 3108). Her slot başta dolu.

## 1. M2'nin mevcut sınırı
Üç **yapısal** sonuç (motor kurallarından türetildi, taramayla doğrulandı):
1. **Durumun güvenliği yalnız yerleşen parçalar kümesine bağlı.** Yerleşme sırası farkı sonucu değiştirmez. İki farklı slotun kartı x, y ikisi de tek başına güvenliyse x→y ve y→x aynı durumdan geçer: ikisi de güvenli ya da ikisi de kaybettirir. **"A→B başka, B→A başka sonuç" bu motorda hiç oluşmaz.** Farklı olan, hangi *slotun ilerlediği* (farklı durumlar), sıra değil.
2. **İlk hamle her zaman serbest.** Ring'de tek bir parça hep güvenli; başlangıçta 3 kartın 3'ü de güvenli (taranan her çözülebilir düzende).
3. **Ring kuralı:** dolu parçalar ring sırasında hep bitişik bir aralık olmalı; tek yerden başlar, yalnız bitişiğine uzar. Bu yüzden ilk hamleden sonra güvenli kart sayısı ortalama ~1 (k3 1.33, k4 1.17, k5 1.07, k6 1.01, k7 0.97). Erişilebilir durumların çoğu zorunlu (k6: ort. 10.3 durumun 5.9'u zorunlu, 2.1 serbest, 0.7 çatal, 1.5 ölü).
Ayrıca: iki yollu oda ring'in özel hâli; "nötr C" yok. Zemin olmadığı için her ek hücre girişin iki komşusundan birine asılı bir parçaya bağlanır; yani asılan parça bir kurban/bekçi olur. Elde "ring ile ilişkisiz üçüncü kart" tasarlanamıyor.

## 2. Queue değişiminin etkisi (çözülebilir düzenler)
| | k3 Kemer | k4 | k5 | k6 | k7 |
|---|---|---|---|---|---|
| düzen / çözülebilir | 1 / 1 | 12 / 12 | 120 / 90 | 1200 / 556 | 12600 / 3108 |
| başta 3 kart güvenli | hepsi | hepsi | hepsi | hepsi | hepsi |
| ilk hamlede kazandıran sayısı 1 / 2 / 3 | 0/0/1 | 2/4/6 | 24/36/30 | 180/232/144 | 1112/1312/684 |
| **çatalsız** düzen (sonuçlu karar yok) | %100 | %50 | %33 | %26 | %22 |
| çatallı düzen (güvenli ama sonra kaybeden hamle var) | %0 | %50 | %67 | %74 | %78 |
| tek kazanan sıralı düzen | 0 | 2 | 18 | 110 | 570 |
| derin-önce kuralı her koşuda kazanıyor (düzen payı) | %100 | %67 | %47 | %39 | %30 |
| kazanan sıraların derin-önce ile açıklanan payı* | %50 | %31 | %35 | %23 | %23 |
| çatışan çift / birlikte güvenli çift (durum×çift) | 1 / 3 | 18 / 34 | 158 / 256 | 1056 / 1652 | 6172 / 9852 |
\*derin-önce: her adımda (mevcut durumda) en uzak hücresi en derin olan kart. Eşitlikte tüm dallar sayıldı.
Çatal sonrası "kayıp ne zaman belli": güvenle oynanabilen hamle sayısı k5: 0→46, 1→28, 2→10; k6: 0→340, 1→166, 2→64, 3→22 (çoğu 0–1 hamle, yani yakın).

## 3. Gerçek karar üreten queue yapıları
Önce **tanım**: "okunur karar" = elde ≥2 güvenli kart var, aralarında kazandıran ve (bu durumdan sonra) kaybettiren var, ve doğru olan, oyuncunun **o an görebildiği** bilgiyle ayırt edilebiliyor.
Oyuncunun görebildiği: tahtadaki dolu/soluk hücreler (hangi parçaların kaldığı) ve 3 kartın başı. Görmediği: kuyruk kuyrukları (hangi kart hangi kartın altında). Ölçüm: durumun tüm olası gizli kuyruk dizilimlerini (çözülebilir olanları) dolaştım; bir hamle **tüm** dizilimlerde kazandırıyorsa "okunur doğru".
- **Bugünkü oyun (kuyruk gizli):** okunur doğru karar **sıfır**. Her çatal durum bir **kumar** (k5: 60/60 çatallı düzenin hepsi; k6: 412/412). Çatal olmayan (serbest) durumlarda her güvenli seçim zaten kazandırıyor.
- **Bir sonraki kart görünür olsa (her slotun 2. kartı):** çatallı düzenlerin k5'te 52/60'ı, k6'da 340/412'si okunur oluyor. Bunların içinde **derin-önce kuralı yanlış çıkan** durumlar var: k5 12/60, k6 126/412 düzen. 2 kart görünürse k5 60/60, k6 402/412 okunur (derin-önce yanlış: 12 / 136).
- Bu yanlış-derin-önce durumları "gerçek karar"a en yakın olanlar. Ama çoğunda tek kazanan sıra var (k5'te ≥4 kazanan sıralı olan **0**; k6'da **24/556**, ≈%4). Yani doğru karar çoğunlukla tek ezber sıra olarak çıkıyor.
**Örnek (k6, silüet aynı; kuyruklar `[A1] · [A2, R-sol] · [R-sağ, B2, B1]`, 6 kazanan sıra, derin-önce hiçbirini üretmiyor):**
```
 # Rsol Rsol Rsağ #      el: A1 · A2 · Rsağ (üçü de güvenli)
 # A2   #    B2   #      Rsağ → güvenli ama sonra kaybeder: sağ tarafı tamamlayınca
 # A1   I    B1   #      sol kol (A2 sonra Rsol sırası) içeriden dışarı dolamaz
```
En derin kart Rsağ olduğu için derin-önce kuralı tam bu hamleyi seçer (doğrudan çatala girer). Kazandıran başlangıçlar A1 ve A2 (sol kolu açmak); Rsağ ölü bölgeye sokuyor. Bunu görmek için A2'nin altında Rsol'un olduğu bilinmeli: yalnız bir kart ileriyi gören oyuncu çözebilir.

## 4. Bariz sıralama üreten ama gerçek puzzle olmayan yapılar
- **Kemer (k3)** kendisi: 3 kart hep elde, kazanan 4/6; tek akıl "iki bacağı birlikte kapatma". 1 hamlelik güvenlik kontrolü kazandırır.
- **Çatalsız düzenler:** k5'te 30/90, k6'da 144/556 (%26), k7'de %22. Kart seçimi sonuç doğurmuyor.
- **R'nin el başında olması** (k5): R el başında + girişe bitişik parça (A1/B1) elde yok → çatal 0/12, ort. 8.5 kazanan sıra (tamamen serbest). R el başında + A1/B1'den biri elde → 22/40 çatallı, ort. 5.2 sıra.
- **R kuyrukta 2. sırada** (k5): 26/26 düzen çatallı, ort. kazanan sıra 2.9; **R 3. sırada:** 4/4 çatallı, tek sıra (1.0) → zorunlu zincir.
- **A1 ve B1 ikisi de el başında** (iki giriş kapısı yan yana): k5'te 18 düzen, hepsi çatallı; bunlardan R de elde olan 8'inin 6'sı tek kazanan sıralı (ort. 1.5 sıra), R elde olmayan 10'unun 2'si tek sıralı (ort. 2.6). k6'da 46 düzenin %48'i tek sıralı, ort. 2.0 sıra. Kapılar elde ise bulmaca "ikinci kapıyı erken kapama"ya çöküyor ve zorunlu hâle geliyor.
- **A ve B aynı slotta arka arkaya** (ör. `[A1, B1]`): zorunlu zincir; seçim yok.
- k6'da bile düzenlerin %20'si tek kazanan sıralı (110/556), k7'de %18 (570/3108).

## 5. Gatekeeper parçaların rolü
Her parça için "yerleşirse, o an güvenli bir durumdan kaç ve hangi parçayı mühürler" (tüm güvenli durumlar):
- **Kemer:** A yalnız R'yi mühürler (B doluyken); B yalnız R'yi; **R kimseyi mühürlemez** (şifacı/oda). A ve B ortak bekçi.
- **k5:** A1 {A2, R, B2}'yi, A2 {R, B2}'yi, R {A2, B2}'yi, B2 {A2, R}'yi, B1 {A2, R, B2}'yi mühürleyebilir. Ring'de **her parça bir bekçi**; oda ile yol ayrımı bulanıyor.
Geometriden öngörülebilir mi? Mühürlenen alan her zaman **soluk bir dilim, iki ucu da dolu bloklarla çevrili**. Hamleden önce görsel ipucu: "bu kart yerleşirse soluk bir kol iki taraftan dolu blokla kuşatılıyor". Ring küçükken (k3–k5) izlenebilir; büyüdükçe zihinde yol takibi gerekiyor. Burada işçi izi ve Kritik kullanılmadığı varsayıldı.

## 6. Commute eden / etmeyen seçimler
- Tek başına güvenli iki kart için iki sıra **hiçbir zaman farklı sonuç vermiyor** (bölüm 1). Çatışan çiftler (ikisi birlikte kaybettirir) toplam çiftlerin ~%35–40'ı (k5: 158/414, k6: 1056/2708, k7: 6172/16024). Çatışma "A ve B'yi birlikte koyma"; iki sıra da aynı biçimde kaybeder → bu kendini "önce biri, ardından R" olarak çözer, bir yönde seçim doğurmaz.
- Gerçek ayrım **hangi slotun ilerlediği**: farklı kuyrukları açar. Örnek k6 durumunda A1/A2 mi yoksa Rsağ mı: üç farklı kuyruğa farklı ilerleme.
- Dolayısıyla "komütasyon testi" doğru soruyu "iki hamle aynı yere varıyor mu?"dan "o hamle ölü bölgeye mi giriyor?"ya çeviriyor. Ölü bölgeye girişin görünürlüğü kuyruk bilgisine bağlı.

## 7. İnsan oyuncunun gerçekten düşünmesi gereken durumun tanımı
Şu üçü birlikte: (1) elde ≥2 güvenli kart; (2) bunlardan biri kazandırıyor, biri kaybettiriyor; (3) doğru olan, oyuncunun **görebildiği** bilgiden ve tahtanın soluk resminden çıkarılabiliyor, ve **derin-önce gibi genel bir kuralla bulunamıyor.**
Bugünkü oyunda (3) sağlanmıyor: gizli kuyruk yüzünden çatal durumlar kumar. 1 kart ileriyi görme eklenirse (k6'da) çatallı düzenlerin ~%30'u (126/412) bu tanıma giriyor, ama yalnız ~%4'ü ≥4 kazanan sıralı.
"Sadece bir ilke mi uyguluyor?" için gözlenebilir ölçüt: derin-önce kuralı **yanlış** olan bir durumda doğru kartı seçmesi, nedenini kuyruk bilgisiyle açıklaması.

## 8. M2 + queue yeterli olsaydı hangi koşullarda kullanılırdı
Bugünkü kurallarla yeterli değil (bölüm 9). Yeterli olacağı koşullar (bu çalışmadan çıkarım, hepsi karşılanmadan "yeterli" denmez):
- Kuyruk bilgisi en az 1 kart ileri görünür (bu, mekanik değil bilgi sunumu; daha önce onaylanan "sonraki kart önizlemesi").
- Parça sayısı ≥6 (k6 ve üstü); k5'te kayda değer örnek çıkmadı.
- R el başında olmamalı (R 2.–3. sırada) ve girişe bitişik iki parça aynı anda el başında olmamalı; yoksa bulmaca zorunlu zincire/çatalsıza düşüyor.
- Düzen, ≥4 kazanan sıra ve derin-önce kuralının yanlış çıktığı en az bir durum içermeli.
- Taramada bu koşulları sağlayan düzen oranı k6'da %4 (24/556); yani koşullu araştırma hacmi küçük ama sıfır değil.

## 9. Yeterli değilse: mevcut mekanikler değişmeden kalan temel eksik
1. **Kuyruk bilgisinin görünmezliği.** Sonuçlu kararların hepsi (k5 60/60, k6 412/412) gizli kuyruğa bağlı; oyuncu geometriden doğru kararı çıkaramıyor. Bu, M2 geometrisinin değil kart sunumunun eksiği: karar bilgisi ekranda yok.
2. **Ring'in daralması.** Her ilk hamleden sonra ortalama 1 güvenli kart kalıyor; durumların >%55'i zorunlu. Karar yalnız açılışta ve nadir çatallarda; "A/B/C arasından sürekli seçim" üretmiyor.
3. **Derin-önce ile kısmi örtüşme.** k4–k7'de kural düzenlerin %30–67'sinde tek başına kazandırıyor; %22–50 çatalsız. Kural-yanıltan durum yalnız ≥6 parçada ve az.

## En önemli soru
*"Oyuncu A/B/C arasından seçim yaparken sadece genel bir 'önce derindeki parçayı koy' kuralını mı uyguluyor, yoksa mevcut duruma bakarak gerçekten farklı bir karar mı veriyor?"*

**Bugünkü oyunda (kuyruk gizli) ikisi de değil.** Sonuçlu çatallarda doğru hamle gizli kuyruğa bağlı olduğu için oyuncu duruma bakarak ayırt edemiyor: derin-önce kuralı ya da 1 hamlelik güvenlik kontrolü uygulayıp şansa kalıyor (derin-önce kuralı yanlış çıkabiliyor: k6 düzenlerinin %37'sinde yanlış-kural durumu var). Çatalsız düzenlerde (%22–50) kural zaten fazlalık, seçimin sonucu yok.
**Bir kart ileri görünürse** ve düzen seçilirse oyuncu duruma bakarak kuralı yenen kararlar verebilir (örnek: k6 `[A1]·[A2,Rsol]·[Rsağ,B2,B1]`); ama bu düzenler taranan uzayın küçük bir bölümü ve çoğunda tek kazanan sıra var.
**Karar:** M2 geometrisi tek başına "ikinci kapıyı erken kapama" kuralını üretiyor ve bu kuralın etrafındaki karar bilgisi kuyruk gizliliği yüzünden okunmuyor. M2 + queue, bugünkü bilgiyle gerçek karar kuramıyor; bir kart ileri görünürse ve parça ≥6 olursa dar ama gerçek bir karar uzayı açılıyor.
