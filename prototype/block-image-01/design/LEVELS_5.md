# 5 LEVEL — TASARIM DOKÜMANI (kod yok, HTML'ye dokunulmadı)

Durum: **taslak, onay bekliyor.** Hücre sayıları silüet taslaklarından sayıldı; "tasarım hedefi" yazan her şey implementasyon adımında çözücüyle doğrulanacak.
Referans çekirdek: repodaki `prototype/block-image-01` (rev. 7, `cat-02`). `block-image-11.html` repoda yok; kuralları bu koddan aldım.

## 0. Çekirdek (değişmez)
3 kartlık el · her slotun sabit kuyruğu · parçanın sabit hedefi · dolan hücre kalıcı engel · BFS erişimi · parçanın tüm hücreleri boş ve erişilebilir değilse gönderilemez · worker yalnız görsel · tüm hedefler dolunca biter. Yeni mekanik, yeni UI öğesi, yeni gadget yok.

## 1. Ortak sözlük (5 levelın bütün zorluğu bunlardan gelir)
| Terim | Anlamı |
|---|---|
| **Kapı (gate)** | Bir koridorun TÜM enine kesitini kaplayan parça. Gönderilirse arkasındaki her boş hücre kapanır. Boyutu değil **yeri** belirler (1 hücrelik kapı olabilir). |
| **Dal (branch)** | Girişten yalnız bir kapıdan erişilen bölge. |
| **Çevrili parça** | Çevresindeki parçalar dolarsa erişilemeyen parça (göz, benek). Komşularından ÖNCE gönderilmeli. |
| **İki yollu bölge** | Girişten α ve β olmak üzere iki ayrı yolla erişilen bölge. Biri kapanınca diğeri tek yol olur. |
| **Kuyruk kilidi** | Gerekli parça başka bir kartın ARKASINDA durur; ona ulaşmak için o slot ilerletilmeli. |
| **Anlık tuzak** | Yasal ama gönderilince hemen "kilitlendi" olan kart. |
| **Gecikmeli tuzak** | Gönderildiğinde hiçbir şey olmayan, ama sonra oyunu kazanılamaz yapan hamle. |

## 2. İki karar (onayına bırakıyorum)
**A. "Sıradaki kart" önizlemesi (yalnız UI, mekanik değil).** L03–L05'in tuzakları kuyruğun ilk kartından ötesini gerektiriyor. Oyuncu sıradakini göremezse bunlar ipucu değil tahmin olur ve "oyun beni kandırdı" hissi doğar. Öneri: her kartın altında sıradaki parça soluk küçük siluet. L01–L02 onsuz çalışır. Onay vermezsen L03–L05'i yeniden tasarlamam gerekir.

**B. Kural 12'nin inceltilmesi.** Şu an "hiçbir ulaşılabilir durum kazanılamaz değil" (rev. 7'de `trap_delayed = 0`). Bu, L04'teki "sahte güvenli seçenek"i imkânsız kılar: gecikmeli tuzak tanımı gereği kazanılamaz durum üretir. Öneri:
- L01–L03: gecikmeli tuzak **0** (bugünkü kural aynen).
- L04–L05: gecikmeli tuzak **bilinçli ve sınırlı**; eldeki 3 karttan en az biri yasal kalır, tuzaktan sonra hâlâ 2–5 güvenli hamle vardır (nedeni görülebilsin), kaybedince çıkmaz uyarısı + kapanan yolun vurgusu gösterilir.

## 3. Her level için kabul ölçütleri (çözücü)
`solvable` · `25/25`-tipi muhasebe (`qa_hand.js`) · exact coverage · JS↔Python parity · `qa_hand` LEGAL OPTION CHECK (L01–L03 tam, L04–L05 madde B'ye göre) · her parça en az bir kez "doğru zamanda" gönderilebilir.
İnsan testi: kaybeden oyuncu nedeni 10 sn içinde söyleyebilmeli ("şu parçayı erken koydum"). "Oyun beni kandırdı" diyen test oyuncusu = level başarısız.

---

# L01 — KEDİ · temel karar
```
  ██          ██
  ███        ███
  ██████████████
  ██████████████
  ██████████████
   ████████████
   ████████████
    ██████████
     ████████
     ████████
    ██████████ ██
    ██████████ ███
```
- **Izgara / hücre / parça:** 18×12 · **127** hücre · **17** parça. Giriş: gövdenin altı, ortada (tek).
- **Boyutlar:** 3×1 (iki göz + burun, gerçek parça) · 3×5 (iki kulak + kuyruk) · 11 parça 8–12 hücre. En büyük ≤ 14.
- **Parçalar:** earL, earR, tail, eyeL, eyeR, nose, fL, fR, mid, cL, cR, chin, neck, chest, bL, bR, base.
- **Geometrik mantık:** kulaklar en derin yaprak; gözler/burun çevrili; **chest** (göğüs) gövdenin tam enini kaplayan kapı (yüzün hepsi arkasında); **chin** yanaklar (cL, cR) ile boyun arasında kapı; **tail** yalnız bR/base sağ kenarından erişilen dal.
- **Başlangıç eli:** earL · earR · tail → üçü de güvenli.
- **Kuyruklar (6/6/5):**
  A: earL, eyeL, fL, cL, chin, bL
  B: earR, eyeR, fR, cR, neck, bR
  C: tail, nose, mid, chest, base
- **Ana karar:** "Üç karttan hangisini şimdi?" Kartın kendisine değil **yerleşeceği yere** bak: arkasında boş yüz var mı?
- **Öğrenme:** mesele parçayı doğru yere göndermek değil, doğru parçayı doğru zamanda göndermek.
- **Doğru çözüm (slot sırası):** A B A B C C A B C A B A B C A B C
  = earL, earR, eyeL, eyeR, tail, nose, fL, fR, mid, cL, cR, chin, neck, chest, bL, bR, base.
- **İlk 6 hamlede** eldeki üç kart da güvenli; ilk tuzak 7–10. hamleler arasında (mid, sonra chest) çıkıyor.
- **Yanlış ama yasal #1 (10. hamle):** eli `[cL, cR, chest]`. **chest** yasal ama yüzün altındaki kapıyı kapatır → cL, cR, chin, neck ≈ 40 hücre kapanır, "Kilitlendi". Adil çünkü yanaklar ekranda boş duruyor ve önizleme izi chest'in altından geçtiğini gösteriyor.
- **Yanlış ama yasal #2 (11. hamle):** eli `[chin, cR, chest]`; cR gönderilmeden chin gönderilirse cR kapanır (chin yanakların altındaki kapı). Slotlar arası ilk bağ: iki parçanın sırası.
- **Hedef sayılar:** kazanan sıra çok (gevşek), anlık tuzak durumları az ama okunur, **gecikmeli tuzak 0**, rastgele oyuncunun kazanma ihtimali ≥ %10.

---

# L02 — BALIK · erken kapatma
```
          █████
        █████████    ██
      ██████████████ ███
     ███████████████████
      ██████████████ ███
        █████████    ██
          █████
```
- **Izgara / hücre / parça:** 20×7 · **85** hücre · **16** parça. Giriş: karnın altı, ortada.
- **Boyutlar:** 2×1 (göz, **neck**) · tail 3 parça (5, 5, 3) · 11 gövde parçası 4–9.
- **Kritik geometri:** kuyruk, gövdeye **tek hücrelik boyundan** bağlı (13 hücrelik dal). Kuyruğun dışına açılan parçalar (tailTop, tailBot) ancak tailMid kapısından, o da neck'ten erişilir.
- **Parçalar (geçerli sıra):** tailTop, tailBot, tailMid, neck, finTop, finBot, snout, eye, headT, headB, backR, bellyR, backM, bellyM, core, base.
- **Başlangıç eli:** tailTop · **neck** · tailBot → neck yasal ama **tuzak**.
- **Kuyruklar (6/5/5):**
  A: tailTop, tailMid, finTop, headT, bellyR, core
  B: neck, snout, headB, backM, base
  C: tailBot, finBot, eye, backR, bellyM
- **Ana karar:** "Yasal olması doğru olduğu anlamına gelmez." 1 hücrelik parça masum görünür ama 13 hücreyi kapatır; **boyut değil konum önemli**.
- **Doğru çözüm:** A C A B A C B C A B C A B C A B
  = tailTop, tailBot, tailMid, neck, finTop, finBot, snout, eye, headT, headB, backR, bellyR, backM, bellyM, core, base.
- **Yanlış ama yasal #1 (1. hamle):** `neck` → kuyruk dalı (13 hücre) kapanır, "Kilitlendi". Adil: boyun tek hücre, kuyruk ekranda boş, önizleme izi boyunun üstünden değil kendisine gidiyor.
- **Yanlış ama yasal #2 (2. hamle):** eli `[tailMid, neck, tailBot]` → tailMid, tailBot'u kapatır. İki karttan ikisi yanlış → gerçek eleme.
- **Hedef sayılar:** gecikmeli tuzak 0, anlık tuzak oranı yüksek (başta eldeki kartların 2/3'ü), kuyruk kilidi: neck ilk elde ama 4. hamleye kadar bekletilmeli.

---

# L03 — MANTAR · iki hamle ileri (sıradakini düşün)
```
        ████████
      ████████████
     ██████████████
    ████████████████
    ████████████████
     ██████████████
          ████
          ████
          ████
          ████
         ██████
```
- **Izgara / hücre / parça:** 16×11 · **102** hücre · **18** parça. Giriş: sapın tabanı.
- **Boyutlar:** 3 benek 2×2 = 4 hücre (çevrili parça) · sap 3 parça (8, 8, 6) · 3 dudak (5, 4, 5) · 9 şapka parçası 5–8. Renk: benekler için yeni palet girdisi (renk veri, mekanik değil).
- **Kritik geometri:** sap tek koridor = **kapı zinciri**; şapkanın giriş noktası lipC (sapın tam üstü, 4 hücre). lipC'den önce şapkanın tamamı bitmeli. Benekler şapka içinde **çevrili**.
- **Kuyruk kilidi (asıl fikir):** benek S1 B'nin 3. sırasında, S2 C'nin 3. sırasında. Çevreleyen şapka halkası A'nın ve C'nin başında yasal ama benekler boşken tuzak.
- **Başlangıç eli (örnek):** ringA · b1 · ringC → ringA, ringC yasal ama benekleri kapatır; yalnız b1 güvenli.
- **Ana karar:** "Benek kartı hangi slotun kaçıncı sırasında? Ona ulaşmak için hangi slotu kaç kez ilerletmeliyim, bu arada halka kartlarını bekletmeliyim."
- **Öğrenme:** şimdiki hamle tek başına değil, **bir sonraki kartın gelişiyle** anlamlı.
- **Örnek doğru çözüm (özet):** B'yi iki kez ilerlet (b1, b2) → S1 gelir → S1 → ringA artık güvenli → C'yi ilerlet → S2 → ringC → lipL, lipR, lipC → sap → taban.
- **Yanlış ama yasal:** 1. hamlede ringA → S1 kapanır ("Kilitlendi"). Adil: beneğin hâlâ boş olduğu ekranda görünüyor ve önizlemede kuyruk peek'i (karar A) beneğin B'de 3. sırada olduğunu gösteriyor.
- **Hedef sayılar:** gecikmeli tuzak 0; en az 3 durumda tek güvenli kart (zorunlu hamle); karar derinliği 2–3 hamle.

---

# L04 — ÇİÇEK · sahte güvenli seçenek (ilk gerçek tuzak)
```
         █████
         █████
     █████████████
     █████████████
     █████████████
     █████████████
     ████     ████
      ███     ███
      ███████████
          ███
          ███
          ███
         █████
```
- **Izgara / hücre / parça:** 15×13 · **101** hücre · **19** parça. Giriş: sapın tabanı.
- **Kritik geometri (iki yollu bölge):** merkez (pistil, orta disk) petallere komşu; petallere yalnız iki sepalden gelinir. **α = sol sepal + sol petal, β = sağ sepal + sağ petal.** Sap ikisine de çatallanır. Disk α veya β'dan erişilebilir.
- **Parçalar:** pistil (≈ 12–15 hücre), sepalL, sepalR (3'er), petal parçaları (rightPetalLow = **P**), üst petal, sap 3, taban. Boyut 3–15.
- **Tuzak (gecikmeli):** pistil, kuyrukta **P'nin arkasında** (aynı slot). P α açıkken güvenli, α kapanınca β'nın son yolunu kapatır.
  Başlangıç eli: **sepalL** (V, güvenli görünür) · **P** (slot B başı) · x (güvenli).
- **Doğru çözüm:** P → pistil'i **önce** gönder (B, B), sonra sepalL/sepalR, petaller, sap, taban.
- **Yanlış ama yasal (1. hamle):** `sepalL` → hiçbir şey olmaz ("parça gitti"). Bundan sonra P kırmızıya döner (pistil'in son yolunu kapatır) ve pistil P'nin arkasında kilitli. 3–4 güvenli hamle sonra (A'nın sonraki kartları, C) eldeki tüm kartlar kırmızı: **çıkmaz**. Çıkmaz uyarısı + kapanan sol yol + boş pistil vurgusu gösterilir.
- **Neden adil:** (1) boş pistil ve iki ayrı yol ekranda görünür; (2) sıradaki kart önizlemesi pistil'in P'nin arkasında olduğunu gösterir; (3) sepalL gönderilince α'nın kapandığı oyuncu için gözle okunur; (4) tuzak ile sonuç arası ≤ 4 hamle, sebep tek ve tek yerde.
- **Hedef sayılar:** gecikmeli tuzak 1–3 durum (bilinçli), tuzak ufku 2–5 güvenli hamle, her zaman ≥ 1 yasal kart, `winning_orders` küçük (L03'ten az).
- **İnsan testi:** "Aa, bunu ben yaptım" = başarılı. "Oyun beni kandırdı" = başarısız → peek veya geometri düzeltilir.

---

# L05 — KÖPEK · ilk gerçek puzzle
```
                  ██
                  ███
     █           █████
     ██         ███████
     ██████████ ███████
      █████████████████
      ████████████████
      ████████████████
      ████        ████
      ████        ████
      ████        ████
     ████         █████
```
- **Izgara / hücre / parça:** 20×12 · **119** hücre · **22** parça. Giriş: karnın altı, bacaklar arasındaki boşlukta tek hücre (yanlar duvar; bacaklar yalnız karından erişilir).
- **4 anatomik bölge:** kafa (+kulak, göz, burun) · gövde (sırt, göğüs, karın) · kuyruk · bacaklar.
- **Parçalar:** eye, nose (1'er) · ear, earBase · forehead, snoutT, snoutB, cheek, jaw · tailTip, tailBase · neck · backA, backB, backC · chest, bellyA, bellyB · 4 bacak parçası. Boyut 1–10.
- **Yapı:** karın = üç dala (iki bacak, üst gövde) çıkan kapı bölgesi. Kuyruk sırtın sol ucundan, kafa boyundan dal.
- **Üç slot, üç bölge zinciri:**
  A = kafa zinciri · B = kuyruk + sırt zinciri · C = bacaklar + karın zinciri.
- **Döngüsel bağ (asıl puzzle):**
  - A'nın ilk kartı B'nin ikinci kartını güvenli kılar (A1 → B2).
  - B'nin ilk kartı C'nin yolunu değiştirir (B1 → C2'nin yolu).
  - C'nin ilk kartı A'nın ilerideki bir kartını riske sokar (C1 → A3'ü kapatabilir).
  Tutarlı sıralama saat yönü (A1, B1, C1 → …) tek veya çok az sayıda; geri kalanı gecikmeli tuzak.
- **Başlangıç eli:** A1 · B1 · C1 → üçü de yasal ve anlık güvenli.
- **Ana karar:** "Önümdeki seçenekleri en iyi hangisi bırakır?" 2–3 hamlelik plan, kafada simülasyon.
- **Yanlış ama yasal:** C1'i erken göndermek: o an hiçbir şey olmaz, 3 hamle sonra A3 kapanır (sebep: karın kapısı). Peek ile A3'ün geleceği görülür.
- **Hedef sayılar:** `winning_orders` < ~50 000, karar durumu / toplam durum yüksek, gecikmeli tuzak çok (hedef: toplam durumların ≥ %15'i kazanılamaz alt-ağaç), rastgele oyuncunun kazanma ihtimali < %1.
- **Not:** bölge sayısı 4; ama zorluk parça sayısından değil, B'ye bağlı **dönüşlü** bağlardan geliyor.

---

## Özet tablo
| Level | Resim | Piece | Ana karar | Trap | Hedeflenen düşünme derinliği |
|---|---|---|---|---|---|
| L01 | Kedi, 127 hücre | 17 | Hangi kartın yeri güvenli? | Anlık: chest, chin (geç) | 1 hamle (yerleşeceği yere bak) |
| L02 | Balık, 85 hücre | 16 | Yasal ≠ doğru; boyun kapısı | Anlık: neck (1 hücre), tailMid; başta 2/3 yanlış | 1 hamle + kapıyı ayırt etme |
| L03 | Mantar, 102 hücre | 18 | Benek hangi slotta, kaçıncı? | Anlık: halka kartları; gecikmeli yok | 2–3 hamle (slot ilerletme) |
| L04 | Çiçek, 101 hücre | 19 | α/β iki yollu bölge | Gecikmeli: sepalL (3–4 hamle sonra çıkmaz) | 3–4 hamle |
| L05 | Köpek, 119 hücre | 22 | Döngüsel A→B→C bağları | Çok gecikmeli tuzak | 4+ hamle |

## Sonraki adım (onayından sonra)
Level başına: grid → silüet → parça bölümü (kapılar tam kesit) → kuyruklar → çözücü ölçümü (`tools/ref.py`) → qa_hand/parity → insan testi. İlk L01'i birlikte inceleyelim.
