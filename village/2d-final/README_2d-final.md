# 2B Ana Yerleşim — son sürüm (kot çalışmasına geçiş öncesi)

Yeni, açıkça adlandırılmış çıktılar (orijinal v6 dosyalarına dokunulmadı):

| Dosya | İçerik |
|---|---|
| `koy-vaziyet-atolyesi_2d-final.html` | Editör + gömülü yerleşim (266 nesne) |
| `koy-yerlesim_2d-final.json` | Aynı yerleşim (HTML ile birebir aynı nesne listesi, sırası ve içeriği) |
| `harita_2d-final.png`, `onizleme_2d-final.svg` | Okunaklı harita (1600×2000) |
| `editor-ekran_2d-final.png` | HTML editörünün gerçek ekran görüntüsü (sağ panelde denetim kutuları) |
| `denetim_raporu_2d-final.txt` | Denetçilerin gerçek çıktısı |
| `../village_network_generator_2dfinal.py` | v6 üreticisinin **ayrı kopyası** (nedenleri aşağıda) |
| `../village_access_audit.py` | Yeni sıkı erişim denetimi |
Yeniden üretmek: `./build_2dfinal.sh`

## 1. Girdi notu
Mesajda adı geçen `koy-vaziyet-atolyes v6i.html`, `koy-yerlesim-koordinatlariv4.json` ve ekran görüntüsü bu oturuma **ek olarak gelmedi**. Çalışma, repodaki v6 çıktılarım (`village/koy-vaziyet-atolyesi.html`, `village/koy-yerlesim-koordinatlari.json`) üzerinde yapıldı. Bu ikisi arasında kimlik, koordinat, ölçü ve `pts` karşılaştırması yapıldı: 274 = 274 nesne, sıra aynı, **içerik farkı 0**. Senin dosyaların bunlardan farklıysa sonuçlar için yeniden çalıştırılmalı.

## 2. Denetçinin neyi gerçekten kontrol ettiği (v6 `village_semantic_linter.py`, kural 7)
- Bina-bina / bina-su / yol-bina / yol-su: örnekleme ile (yol 0,5 m adımla).
- Bağlantı: tüm çizgiler 0,8 m yakınlıkla tek bileşen mi? **Yan yana paralel çizgiler de “bağlı” sayılabilir** (gevşeklik).
- Erişim: her kapı patikasının **yalnızca SON noktası** bir L1/L2'ye ≤ 0,3 m değiyor mu? **Başlangıcın kapı düğümünde olduğu, patika boyunca engel olmadığı ve grafın köy girişine ulaştığı kontrol edilmiyordu**; 51 bina + 5 parsel tek “56” sayılıyordu.

Bu yüzden `village_access_audit.py` eklendi: kapı düğümü → patika başı (≤0,30 m) → patika boyunca bina/su/çeşme kesişimi yok → patika sonu L1/L2'ye T-bağlantı (≤0,40 m) → çizgi grafı (yalnız uç-nokta/kesişim bağlar) üzerinden `Road_L1_Arrival` başına ulaşım; **gerçek bina kapıları ve parsel girişleri ayrı** raporlanır. Ayrıca serbest uçlar, yan yana binen çizgiler, ormana giren yol uzunluğu ve köprü ağzı yığılması ölçülür.

## 3. Değişiklik listesi (v6 → 2B son) ve nedenleri
1. **Üretici kopyası** (`..._2dfinal.py`): v6'daki hata — `ON:` ile halkaya bağlanan yolların başı en yakın geçilebilir hücreye kayıyor, kavşak kopuyordu (Üst köprü yolu serbest uçlu, dolambaçlı). Uçlar artık tam kavşak noktasına oturur. Köprü uçları aynı şekilde.
2. **Köprü ağızları**: Nehir kıyısı patikası ve çiftlik yolu köprü başına yığılmaz; ana yola T-kavşakla (≈8–10 m önce) bağlanır. Alt köprü doğu ağzında yalnız `East_Trunk` kalır; çiftlik yolu ondan ayrılır. Üst köprü batı ağzında ana yol + kıyı patikası (kıyı patikası 6 m civarından geçer, kavşak ≥7 m geride).
3. **Üst köprü yolu**: `Market_Shop_03` ve `Market_Shop_11` kuzeydoğu geçidini daraltıyordu (yol 108 m dolanıyordu) → ikisi 2,7–2,9 m kaydırıldı; yol ringten köprüye doğrudan gider.
4. **Liman**: arka sıra/ön sıra +1 m, servis sokağı z=57; liman yapılarına elle ±2–6° kademe (v6'daki ±15° jitter yolları bozuyordu); alley'ler (kullanılmayan dar geçitler) kaldırıldı. Ön sıra servis sokağına, arka sıra kordona bakar.
5. **Ormana giren yol**: `Forest_West` sınırı 4 m batıya çekildi; giriş yolu orman kenarındaki açıklıktan akar. Yalnız giriş kapısında (7,196) ≈4 m `Forest_North` içinde başlar (tasarım: dağ geçidi girişi).
6. **Açık alanlar**: her alana `purpose` (işlev) metni; büyük alanlara etiket. Kuzey vadi **ortak biçme çayırı** (samanlık için yaz otu, kış otlatma) olarak tanımlandı ve doğu kıyısında `Lane_Hay_Meadow` (çayır arabası yolu) ile bağlandı. Yola >14 m uzak tarımsal dolgu (ekin/meyve/otlak) çayıra çevrilir. Bina eklenmedi.
7. Doğu mahalle: `Street_East_Mid` E_13'ün doğusundan geçip `Street_East_South`a bağlanır; `E_House_10` 3,7 m kaydı. Serbest uçlar kavşağa oturtuldu (`S2`, `S3`, `Street_Market_North`).
8. Üretilen alanlardan `elevation` alanı kaldırıldı (kot bir sonraki aşama). Orijinal statik alanlardaki `elevation` değerleri (ör. `West_Terraces: 7`) **dokunulmadan** duruyor.
Kimlikler, türler ve ayak izi ölçüleri v6'ya göre **aynı** (kayan 11 yapı: M03, M11, Dock_01–08, E_10; yalnız konum/yön). Orijinal dosyaya göre ev ölçüleri v6'da değişmişti (3,4×3,3 → 4,8–6,2×4,2–5,0 m, gerekçe: kulübe boyutu / copy-paste); bu aşamada tekrar değişmedi.

## 4. Alanların işlevi (JSON'da `purpose`)
Büyük açık alanlar: **kuzey vadi** = ortak biçme çayırı (1,4 bin m²); **göl kıyısı şeritleri** = nemli taban çayırı, yapılaşma yok (kot aşamasında su kotuna göre belirlenecek); **nehir kıyısı** = taşkın payı + yürüyüş şeridi; **pazar çevresi/doğu mahalle çayırları** = ev bahçelerini ayıran köy yeşili; **güneydoğu** = çiftlik avlusu + tarım kuşağı + otlak; **orman bölgeleri** = ağaç kümesi bölgesi (ağaçlar sonraki aşamada). Tür/işlev/alan tablosu `denetim_raporu` ile birlikte üretilebilir (JSON'dan hesaplanır).

## 5. Denetim sonuçları (gerçekten çalıştırıldı — bkz. `denetim_raporu_2d-final.txt`)
- Python mantık denetimi: **7 / 7**.
- Sıkı erişim: **gerçek bina kapıları 51 / 51**, **parsel girişleri 5 / 5**; çizgi grafı 88 çizgi, hepsi köy girişinden ulaşılır; serbest uç 1 (= giriş kapısı), gerçek ölü uç 0; doğu yakadaki 9 L1/L2 çizgisine köprü tabanı olmadan ulaşılamaz.
- Tarayıcıda (headless Chromium, Playwright) **çalıştırılıp görülenler**: sayfa hatasız açılır; sağ panel “7 / 7 Kural Geçti” ve “Yol bağlantısı olmayan bina 0 / 56”; kayıkhaneyi karaya sürükleyince 5/7 + uyarı, geri al ile 7/7; samanlığı uzağa sürükleyince 5/7 + uyarı; otomatik yenileme kapalıyken evi çayıra sürüklemek 1 / 56 + kırmızı çerçeve, “Yolları Otomatik Ör” sonrası 0 / 56; eski kayıtlı taslak varken yeni yerleşim açılır; JSON dışa/içe aktarma (v6'da). **Denenmedi**: dokunmatik/mobil, Firefox/Safari, uzun süreli sürükleme performansı.
- **Kullanılan eşikler tasarım varsayımıdır, profesyonel standart değildir**: yol/bina payı 2,5/1,6/0,9 m; kapı 1,5 m (parsel 1,2 m); 3 m kapı-yol; kıyıdan ≤4 m; otlak göle ≥12 m; samanlık ≤18 m; nalbant ≤30 m; ev ≥4,6×4,0 m; 5° açı/1,5 m kademe; çeşme 4 m; kavşak 0,4 m; “yan yana” 1,8 m.
- Sınırlar: Python ve JS denetimi aynı kurallar için ayrı yazıldı, eşitlikleri yalnız bu veride doğrulandı. Otomatik denetim tasarımın bittiği anlamına gelmez.

## 6. Kot çalışmasına hazır mı?
**Büyük ölçüde hazır; şu noktalar açık:**
1. Yan yana binme ölçümü hâlâ 3 yerde var (kordon~servis sokağı 26 m, kordon~batı bağlantı 16 m, `East_South`~`East_Mid` 19 m): görsel olarak kavşak/bitişik sokak, ama kot aşamasında birleştirilmeli veya aralanmalı.
2. Alan poligonları (`Fill_*`, `Garden_*`) grid türevidir: **kesin bir topolojik bölüm değil**, birbirine ve statik alanlara taşabilir (çizim sırasıyla çözülür). Unity'ye aktarmadan önce temizlenmeli.
3. Köprü boyları (21 m) ve iskele konumları 3B/kot kararına bağlı; değirmen çarkı suya 1,4 m girer (bilerek, kural 7'den muaf).
4. Doğu göl kıyısı (x 100–160, z 42–55) yalnız kıyı çayırı; ikinci bir iskele/sal alanı gerekip gerekmediği karar bekliyor.
5. Pazar dükkânları çeşmeye diyagonal bakıyor; kot aşamasında okunurluk gözden geçirilmeli.
6. Orijinal statik alanlardaki `elevation` değerleri doğrulanmadı.
