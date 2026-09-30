# Renk Yerleştirme — oynanabilir prototip v0

Araştırma klasöründen (`../research`) **ayrı**. Çalıştırılabilir tek dosya: **`dist/colorbuild.html`** (bağımlılık yok; çift tıkla aç).
İlk hedef "güzel oyun" değil; **oynanabilir ve ölçülebilir dikey dilim**. Yeni mekanik yok: solver'ın kuralları aynen korundu.

## 1. Nasıl oynanır (5 madde)
1. Tahtada hedef resmin (216 kutuluk renkli kedi) **hayalet** hâli durur: her boş hücre kendi hedef renginin soluk tonunda. Sol kenardaki **DEPO/kapı** tek girişidir.
2. Altta 3 renk düğmesi vardır. Bir renge **bir kez bas → önizleme** (o dalganın dolduracağı hücreler, **arkadan öne** numaralı: 1 = girişe en uzak); **aynı renge ya da Gönder'e tekrar bas → dalga gider**.
3. Dalga = sabit **W kutu** (seviye parametresi; sen miktar seçmezsin). İşçiler kutuları depodan hedef hücrelere yürüyerek taşır ve bırakır; bırakılan kutu **kalıcı engeldir**.
4. Bir boş hücreye girişten yol kalmazsa **seviye kaybedilir**: erişilemeyen hücreler kırmızı X ile işaretlenir, panel "Kilitlendi" der. **Yeniden başlat (R)** sınırsızdır; geri al yalnızca araştırma ayarıyla (`?undo=N`) açılır.
5. Tüm hücreler dolunca resim ortaya çıkar. Panelde her renk için **kalan kutu, ≈dalga sayısı, şu an erişilebilir kutu sayısı** görünür; erişilemez kutu varsa ⚠ gösterilir. Klavye: `1/2/3` renk, `Enter` gönder, `Z` geri al, `R` yeniden başlat.

## 2. Solver ile birebir olan kurallar
Kaynak: `src/engine.js` (saf mantık; arayüzden bağımsız) ↔ `research/puzzle_engine.py`.

| Kural | Prototip | Solver |
|---|---|---|
| Izgara | `E` giriş, `#` duvar, `.` zemin, harf = hedef hücre (1 kutu) | aynı |
| Hareket | 4-komşuluk; zemin + giriş + **boş** hedef hücreler üzerinden | aynı |
| Dolu hücre | kalıcı engel | aynı |
| Oyuncu kararı | yalnız **renk**; miktar seviye başına sabit **W** | aynı |
| Dalga | dalga başında erişilebilir boş hücreler; sıra (uzaklık ↓, satır ↑, sütun ↑); ilk **W** (yetmezse erişilebilir kadarı); hiç yoksa hamle yasadışı | aynı |
| Atomiklik | mantıksal durum **tıklamada** anında değişir; animasyon kozmetik | aynı (dalga tek geçiş) |
| Kayıp | boş hedef hücreye girişten yol yok ⇒ `sealed` | aynı |
| Kazanma | tüm hedef hücreler dolu | aynı |
| Renk sırası | harflerin alfabetik sırası = renk indeksi | aynı |

**Kanıt (3 katman):**
1. `tests/parity_node.js` + `research/parity.py check`: solver'ın ürettiği 35 seviye × 107 vaka (kazanan / hatalı / rastgele diziler) — **yerleşen hücreler sırasıyla ve kilit durumu dahil TAM UYUM**.
2. Sayfadaki **"Parity testi"** düğmesi aynı vektörleri (Python'dan gömülü) tarayıcıdaki `engine.js` ile çalıştırır: **107 / 107 vaka birebir**.
3. `research/tests`: Python motoru ↔ kutu-kutu yerleştirme eşitliği; bağımsız simülatör ↔ motor (32 seviye).

Kozmetik (solver'da modellenmeyen) olanlar: işçi yürüyüşü/animasyon (rota = dalga başı BFS'inden en kısa yol; **varış sırası = yerleştirme sırası**, bu yüzden hiçbir işçi dolmuş kutunun içinden geçmez), önizleme numaraları, kilit göstergesinin dalga **bittikten sonra** görünmesi, panel, kayıt. Dalga sürerken giriş kilitlidir (bir dalga bir anda; solver ile aynı sıralı model).

## 3. Henüz TASARIM KARARI olanlar (prototipte geçici seçim; solver bunları dayatmaz)
1. **Hero seviyesi ve zorluğu:** aynı 216 hücreli kedi, 3 konfigürasyon: `HERO1` kolay (üst kapı, W=26, 9 dalga), `HERO2` orta (sol kapı, W=21, 12 dalga; **varsayılan**), `HERO3` gecikmeli hata (alt kapı, W=24, 10 dalga). Seçimler solver ölçümüne dayanır (`tools/hero_search.py`), "hangisi iyi" kararı değildir. W/kapı sabitlenmesi gerçek oyun için ayrıca verilmeli.
2. **Hayalet renk** (hedef renklerini soluk göster) varsayılan açık; "yalnız silüet" (`?ghost=0`) araştırma seçeneği. Brief "silüet" diyor, ama renksiz silüette plan yapmak imkânsıza yakın.
3. **İpucu seviyesi** (`?hint=`): 0 = tek dokunuş gönderir; **1 = önizleme (varsayılan)**; 2 = önizleme + "bu dalga N hücreyi erişilemez yapar" uyarısı. **Seviye 2 neredeyse cevabı verir** (araştırmada hataların %91'i aynı hamlede kilitliyordu) — oyuna girmeli mi kararı açık; varsayılan kapalı.
4. **İki adımlı gönderme** (önizle → onayla) mı, tek dokunuş mu.
5. **Bir dalga bir anda** (animasyon sürerken giriş kilitli). Üst üste binen gerçek-zamanlı dalgalar solver modelini değiştirir; yapılmadı.
6. **Kayıp gösterimi:** dalga bittikten sonra. *Gecikmeli (latent) kayıp* oyun tarafından **bilinemez/gösterilmez** (solver gerektirir); yalnız ölçülür.
7. **Geri al / yeniden başlat:** yeniden başlat sınırsız; geri al varsayılan 0 (`?undo=N`). Araştırma: 2 geri al kısa oyunlarda zorluğu büyük ölçüde siler.
8. **Durum paneli içeriği:** kalan/≈dalga/erişilebilir + önizleme. Gösterilmeyenler: dar boğaz/bağımlılık bilgisi, solver tavsiyesi. Ne kadar bilgi "yeterli" insan testiyle belirlenmeli.
9. **Hız:** ×1 ≈ dalga başına 4–6 sn (net izlenebilir); ×2/×4 kozmetik; çoğu ölçüm için ×1 önerilir ve kaydedilir.
10. **Görsel kalite:** 16×16 el yapımı kedi (3 renk); gerçek sanat, ses, efekt yok. Depo/kapı çizimi tek girişli seviyeler içindir (≤3 giriş hücresinde depo çizilir).
11. **Stok gösterimi** kutu cinsinden (kalan, ≈dalga); "kutu/hücre" oranı 1:1 (görseldeki 120/90/70 stok sayıları bu prototipte kullanılmadı).

## 4. Çalıştırma
```
open dist/colorbuild.html                       # varsayılan: HERO2
dist/colorbuild.html?level=HERO3&hint=1&speed=1  # seviye, ipucu, hız
dist/colorbuild.html?mode=test&levels=W01S,A03S,B03S&player=p1   # insan testi modu
```
`mode=test`: seviye seçici, geliştirici paneli, ipucu/hayalet/geri-al ayarları **gizli**; nötr başlık ("Seviye 2 / 5"), "Bu seviyeyi bırak / Sonraki seviye"; grup etiketi (A/B/C) oyuncuya gösterilmez. **Kaydı indir** düğmesi tüm hamleleri verir: her dalga için `token` (renk harfi), `decide_ms` (önceki hazır olma → dokunuş), `preview_switches` (gönderene dek kaç kez farklı renk önizledi), `placed`, `sealed_after`; deneme sonucu `won/sealed/abandon/restart`. Token dizileri `research/human_test_oracle.py` ile çözücü gerçeğine karşı etiketlenir.

Geliştirici: `python3 tools/make_levels.py` (seviye + vektör verisi; `../research` içe aktarır) → `python3 tools/build.py` (tek HTML). Testler: `node tests/parity_node.js …`, `node tests/browser_qa.js` (headless Chromium: yükle, önizle, animasyon, tam kazanma, kilitlenme, ipucu-2, geri al, test modu, parity paneli).

## 5. Bilinen sınırlar
- İşçi yürüyüşü tek giriş için tasarlandı; çok girişli test seti seviyelerinde çalışır ama depo çizilmez/dağınık görünür.
- Dar ekran düzeni temel düzeydedir (tahta küçülür).
- Oyun içinde solver yoktur (yalnız `engine.js`'in yerel BFS'i: önizleme ve kilit gösterimi). Gecikmeli hata, dar boğaz, "neden" bilgisi oyuncuya gösterilmez.
- Test seti seviyeleri (A/B/C) araştırma kümesinden; hero dışındaki görseller soyut renk haritalarıdır (resim gibi görünmez).
