# L02–L05 seviye raporu (L01 dokunulmadı; mekanik değişmedi)

Solver metrikleri **yalnız teşhis**; tasarım hedefi değil. Hepsi: 36×24, 3 slot sabit kuyruk, her parça tek renk (`piece.color`), 400+ fiziksel küçük blok.
Üretim: `tools/author_lXX.py` → `tools/lXX_source.json` → `tools/make_level_blocks.py lXX` → `tools/build.py lXX` → `dist/block-image-LXX.html`.

| | L02 Ev | L03 Ağaç | L04 Araba | L05 Kuş |
|---|---|---|---|---|
| hücre | 472 | 522 | 422 | 419 |
| parça | 26 | 34 | 38 | 43 |
| ort / min / max hücre | 18.2 / 2 / 40 | 15.4 / 4 / 26 | 11.1 / 2 / 22 | 9.7 / 1 / 28 |
| kuyruk (A/B/C) | 9/9/8 | 10/10/14 | 12/12/14 | 12/18/13 |
| karar noktası (≥2 seçenek, ≥1 yasal) | 101 | 193 | 168 | 318 |
| zorunlu durum | 8 | 6 | 14 | 13 |
| ptr-durum sayısı | 511 | 585 | 1403 | 2191 |
| p_random (rastgele kazanma) | %9.7 | %2.0 | %23.8 | %3.9 |
| ilk anlık tuzak (hamle) | 2 | 4 | 5 | 11 |
| gecikmeli tuzak durumu | 0 | 0 | 17 (+26 kazanılamaz, 3 çıkmaz) | 0 |
| en kısa kilitlenen yol | 2 | 4 | 5 | 11 |
| kazanan hat | A9 B9 C8 | karışık | A12 B12 C14 | A12 B18 C13 |

QA: `tests/qa_levels.js lXX` (kapsama %100, çift/eksik hedef 0, tüm kartlar tek renk, hayalet/yerleşen/yük tek renk, kazanan+karışık+ters dizi → won, tuzak yolu → sealed, telefon, console), `tests/parity.js vectors_lXX.json` (29/29), `tests/qa_hand.js`.
`qa_hand` L04'te **bilerek** FAIL: 3 çıkmaz + 26 kazanılamaz durum = kontrollü gecikmeli tuzak (yalnız L04–L05'te izinli; hiçbir el sessizce hepsi-kilitli değil — kart gönderince `sealed/stuck` açıkça görünür).

Dürüst bulgular
- L02: cep mantığı (cam/kasa, tokmak/kapı) var ama p_random %9.7 bir rastgele oyuncuyu hızlı cezalandırıyor; "kolay" olması tuzakların ilk hamlede görülür olmasından, karar derinliğinden değil.
- L03: gövde tek geçit (kapalı kuyruk), son 8–10 hamle fiilen zorunlu; elmalar kuyrukta geç → cep kuralı gerçek karar veriyor.
- L04: tek gerçek "sonradan anlaşılan" tuzak seviyesi (tavan bandı TRUNK/DECK/HOOD kuyruğun sonunda, camlar ondan önce dolmazsa kilit).
- L05: parça sayısı/küçüklük en yüksek ama **gecikmeli tuzak yok**; zorluk genişlikten (318 karar) geliyor, derinlikten değil. İlk 10 hamle güvenli. EYE_HI 1 hücre; bacaklar 2 hücre genişliğinde — okunabilirlik sınırında.
- Peek (sonraki kart önizlemesi) uygulanmadı.
- L05'te tek aynı-renk komşu: BODY_04 / HEAD_3 (aynı mavi hex).
