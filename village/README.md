# Köy Vaziyet Atölyesi — Prosedürel Yol ve Alan Ağı

| Dosya | Ne işe yarar |
|---|---|
| `koy-vaziyet-atolyesi.html` | Güncellenmiş editör. 56 yapı, yeni yol ağı ve doldurulmuş alanlar `DEFAULT_OBJECTS` içine gömülü; tarayıcıda açman yeter. |
| `village_network_generator.py` | Yol/alan üreticisi (yalnız standart kütüphane, Python ≥ 3.9). |
| `koy-yerlesim-koordinatlari.json` | Üreticinin çıktısı; editörde “JSON yükle” ile açılır. |
| `onizleme.svg` | Aynı yerleşimin statik önizlemesi. |
| `tools/patch_html_editor.py`, `tools/editor_block.js` | Orijinal HTML'e üç “yol mantığı” özelliğini ekleyen yama. |
| `build.sh` | Orijinal HTML'den iki dosyayı baştan üretir. |
| `input/koy-vaziyet-atolyesi.orig.html` | Girdi (değiştirilmemiş orijinal). |

Yeniden üretmek: `./build.sh` · yalnız üretici: `python3 village_network_generator.py --html <html|json> --out-json cikti.json --inject-html cikti.html --preview onizleme.svg`
Üretici kendi çıktısı üzerinde tekrar çalıştırılabilir (idempotent: aynı sonucu verir).

## Üreticinin yaptığı

1. **Maliyet ızgarası (1×1 m)**: bina taban alanları (döndürülmüş dikdörtgene tam mesafe), göl, nehir, parseller. Yol sınıfına göre güvenlik payı: L1 2,5 m · L2 1,6 m · L3 0,9 m (+ planlama payı). Nehir geçilemez; köprü/iskele tabanı ve kıyıya inen 3 m'lik rampa geçilebilir ⇒ batı↔doğu geçişi **yalnız `Bridge_Upper` / `Bridge_Lower` uçlarından** olur.
2. **Kapı düğümü**: cephenin 1,5 m dışı (`rot` dikkate alınır; `rot=0` ⇒ kapı güneye bakar; parsellerde 1,2 m “giriş”).
3. **Hiyerarşi**: L1 `road` (3,8–4,5 m) → L2 `path` (2,2–2,8 m) → L3 `path` (1,2 m, `Access_<id>`, `forId` alanlı). Rotalar A\* / Dijkstra → görüş-hattı sadeleştirme → **Chaikin** köşe kesme; yumuşatılmış hat tekrar çarpışma testinden geçer, geçemezse daha az yumuşatılır.
4. **Yön optimizasyonu**: binalar en yakın sokağa paralel döner (pazar yapıları meydana bakar); L3'ü 9 m'den uzun kalan evler/ahırlar (dükkân ve liman yapıları hariç) en çok 6 m yaklaştırılır. Parseller 90° adımlarla döner (`w`/`d` yer değiştirir, ayak izi aynı kalır).
5. **Boş alan doldurucu**: her yapıya bahçe/avlu (`courtyard`/`meadow`), kalan ölü hücreler en-büyük-dikdörtgen yöntemiyle orman · teras · çayır · ekin · otlak · meyve bahçesi. Ölü alan 11.669 m² → 2.084 m² (harita 32.000 m²); kalan, küçük ve dar artıklardır.

## Üretici doğrulaması (her çalıştırmada yazdırılır)

yol-bina çakışması **0** · yol-su çakışması **0** · yapı çakışması **0** · ağ **tek bileşen** · 56 yapının 56'sının kapı patikası ana ağa değiyor · en uzun kapı patikası 7,8 m.

## Yerleşimde yapılan (bilinçli) değişiklikler

Tüm ID'ler ve türler korunur (56/56). Konum değişenler üretici çıktısında “konum / yaklaştırıldı” satırlarıyla listelenir. Başlıcaları:

- **Köprüler**: merkezler aynı; boy 18/14 m → 21 m, yön −25° → −12°. Eski Alt köprü nehri aşamıyordu (batı ucu suyun içinde kalıyordu).
- **İskeleler**: göl kıyısına oturtuldu; İskele 4 nehir ağzındaydı → x = 50 / 62 / 74 / 86.
- **Liman**: yapı sıraları z = 60,5 ve 49,5'e alındı (kordon – arka sıra – servis sokağı – ön sıra sığsın diye). `Market_Shop_08/09`, `Boat_House_01/02` buna göre kaydı; `Boat_House_01` batı kıyıya taşındı.
- Pazar: `Stall_A/B` meydan çaprazını boş bırakacak köşelere; `Watermill_01` nehre biraz yaklaştı; `W_House_06`, `E_House_02`, `E_House_14` sokağa oturtuldu.

## Editördeki yeni özellikler

1. **Yolları Otomatik Ör / Yenile** (üst bar): tüm kapı patikalarını bina içinden ve nehir üstünden geçmeden, en yakın ana sokağa yeniden hesaplar. “sürükleyince yenile” açıkken bir yapıyı bırakınca yalnız onun patikası yenilenir (tek geri-al adımı). “kapıyı yola çevir” yapıyı en yakın sokağa paralel döndürür.
2. **Kapı yönü + snap**: her yapıda turuncu eşik/ok kapının yönünü gösterir. Yol/patika çizerken (ve düğüm sürüklerken) imleç yol düğümüne (yeşil), bina kapısına (turuncu), yol kenarına (mavi) 2,5 m içinde yapışır.
3. **Bağlantı denetimi**: sağ panelde “Yol bağlantısı olmayan bina: X / 56”. Kapısı yola 3 m'den uzak **veya** ana ağdan kopuk yapı kırmızı çerçeve alır.

Not: kayıt anahtarı `village-layout-studio-v3` olarak değişti; tarayıcıda kayıtlı eski (v2) taslak yeni haritanın üstüne binmez. İstersen eski taslağı “JSON indir / JSON yükle” ile taşıyabilirsin.
