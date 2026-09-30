# İnsan testi protokolü (keşifsel; tasarım kararı değildir)

Amaç tek cümle: **oyuncu yanlış rengi seçtiğinde o anda ne olduğunu anlıyor mu?** Solver bunu ölçemez; burada yalnızca yapısal gerçek (oracle) ile oyuncunun algısı karşılaştırılır.

## Set
`levels.json` / `level_cards.md` / `shortlist.csv` — 32 seviye:
- **W01–W02:** ısınma (kuralı öğretir; analiz dışı). W01 karar içermez, W02 hafif.
- **A01–A10 (anında hata, DH≈1):** mevcut mekaniğin doğal davranışı.
- **B01–B10 (gecikmeli hata, DH_beklenen ≥ 2):** nadir bölge (56 küçük + 15 büyük aday içinden). Her B seviyesi bir A seviyesiyle **eşleştirildi** (aynı renk-haritası ailesi, benzer riskli karar sayısı/dalga/hücre/bottleneck/parçalanma).
- **C01–C10 (zarfa yakın):** puzzle-verimi seviyelerinden, *kurtarma mesafesi hariç* tüm boyutlarda filtrelenmiş benchmark zarfına en yakın olanlar.
- Her grupta 6 küçük (49–101 hücre) + 4 büyük (196–404 hücre; 200–400 kutuluk görsel hedefe yakın).

Bilinen karışıklıklar (açıkça): (1) A–B eşleşmesi kusursuz değil: B biraz daha yoğun (riskli yoğunluk 0.65 vs 0.54; tek-doğru karar 4.9 vs 3.7) ve **doğası gereği** daha zor kurtarılıyor (1-undo kurtarma 0.44 vs 0.94; bu, "gecikmeli"nin tanımının parçası). (2) B seviyeleri parçalı/katmanlı renk haritalarından (CM7/CM8/CM10) geliyor → görsel gürültü fark yaratabilir; eşleşme bunu aynı ailede tutarak azaltır, yok etmez. (3) C büyük ölçüde DH=1 (anlık hata payı ort. 0.83): A ile DH açısından örtüşür.

## Zorluk uyarısı
Bu seviyelerde *rastgele* oyuncunun undo'suz kazanma olasılığı: A ort. %6, B %2, C %14 (ısınma %86). İnsanlar rastgele oynamaz, ama **birçok oyuncu birçok seviyede başarısız olacak**. Bu yüzden:
- Başarısızlıkta seviye **yeniden başlatılabilir** (sınırsız yeniden deneme); her deneme ayrı kaydedilir.
- Seviye başına üst süre (öneri: 4 dk) ve "bırakıyorum" seçeneği; bırakma kaydedilir (bu da veridir).

## Düzen
- Her oyuncu her A/B **çiftinden yalnız birini** oynar (çift başına A veya B rastgele, dengeli dağıtılır) + 10 C seviyesi + 2 ısınma = 22 seviye. Oyuncu başına ~40–60 dk; gerekirse C'nin yarısına indir.
- Sıra: ısınmalar → karışık (A/B/C sıralı rastgele, küçük→büyük dengeli). Aynı çiftin iki üyesini aynı oyuncuya gösterme.
- **Arayüz sabit kalsın.** Erişilemez hücreleri vurgulama, "bu hamle şunu kapatır" ön izlemesi vb. hangi görsel ipucu açıksa ONU kaydedin; bu turda ipucu koşulu değiştirilmez (Decision Recovery Visibility'nin UI ayağı bir sonraki turda, tek bir değişkenle).
- Prototipin kuralları çözücüyle **birebir** aynı olmalı: sabit W, en derinden başla, dolu hücre kalıcı, 4-komşuluk. Doğrulama: her seviyenin `example_winning_sequence` dizisi prototipte kazanmalı; `safe_first_colors` ile ilk hamle güvenliği uyuşmalı.

## Kayıt (her hamle)
`player, level, attempt, t_ms, token (renk harfi | U=geri al), ui_hint_condition`. Oturum sonrası:
```
python3 human_test_oracle.py human_test/levels.json B01S A B A C U ...
```
Oracle her hamleyi `safe / latent / sealed / undo / illegal` diye etiketler, o anda güvenli renkleri verir, ilk hatadan kilitlenmeye dek **gözlenen** hamle sayısını hesaplar (`observed_horizon_moves`).

## Sorular (kısa, ölçüm başına)
1. **Hata anı (think-aloud + hamle sonrası)**: Oyuncu hatalı hamleden hemen sonra "bir şey ters gitti" diyor mu? Söylediği hamleyle oracle'ın `first_mistake_step`'i arasındaki fark = **fark etme gecikmesi**.
2. **Neden**: Kilitlenme/undo sonrası "neden oldu?" → kodla: doğru neden (hangi renk/hangi bölge) / kısmen / yanlış / bilmiyorum.
3. **Gecikmeli hata (yalnız B)**: oyuncu doomed-but-unsealed durumdayken (`latent`) kaç hamle daha "iyi gidiyor" sanarak devam etti; kilit göründüğünde "neden?" diyebildi mi, yoksa "haksızlık" mı hissetti?
4. **Adalet** (1–5), **"ben çözdüm" hissi** (1–5), **gerilim** (seviyenin hangi bölümünde: erken/orta/geç), **dalga büyüklüğü** hissi (öngörülebilir strateji / kontrol edilemeyen sel / önemsiz), **renk sayısı** ("seçimler anlamlı mıydı, rastgele mi?").
5. Undo kullanımı: kaç hamle geri aldı, hata sonrası hemen mi, birkaç hamle sonra mı.

## Analiz planı (önceden yazılı)
- Betimleyici: grup (A/B/C) × büyük/küçük × metrikler; A–B **eşli** karşılaştırma (çift başına). Oyuncu sayısı küçük olacağından **anlamlılık testi iddiası yok**; etki yönü + örnek alıntılar.
- Solver–insan karşılaştırması: `observed_horizon_moves` ve solver `dh_exp_mean`; fark etme gecikmesi ile DH arasındaki ilişki; nedeni doğru söyleme oranı A vs B.
- **Eşikleri takım testten önce yazsın** (örn. "anında kilitlenmede oyuncuların ≥ X'i nedeni söyleyemiyorsa ... "). Bu dosya eşik önermez; eşikler tasarım kararıdır.

## Bu turda yapılmayacaklar
4. renk, yeni engel, yeni level üretimi, DH'yi 3–5'e zorlama, ABC ile zorluk artırma, benchmark sayılarını hedefleme.
