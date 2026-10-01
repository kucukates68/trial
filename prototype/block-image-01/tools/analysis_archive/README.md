# analysis_archive — oturum sırasında yazılan tek seferlik analiz betikleri (olduğu gibi arşivlendi)

Bunlar ürün kodu değil; bulguların (design/*.md) üretildiği araçlar. **Doğrudan çalışması garanti değil**: yollar oturum klasörlerine göre yazıldı (`sys.path` ve `*_up.json` dosyaları). Yeniden kullanmak için önce `ext.py` ile `dist/block-image-L0X.html` içindeki level verisini `l0X_up.json`'a çıkarın ve `sys.path.insert` satırlarını bu klasöre göre düzeltin. Doğrulanmış çekirdekler `tools/lvlkit.py`, `tools/ref.py`, `tools/lab/labkit.py`, `tools/human_flow.py` (bunlar repoda ve test edildi).

## wr/ (kök) — "yanlış seçim olasılığı", L01-V4, L02-V2
| Dosya | Ne yapar |
|---|---|
| `ext.py` | yüklenen/dist HTML'lerinden `window.BI_LEVEL` verisini çıkarır (`*_up.json`) ve repodakiyle karşılaştırır |
| `an.py` | `load(key)`: level JSON → lvlkit `Geo`; `forward` yardımcıları |
| `an2.py` | hamle türü dağılımı (kart/güvenli), hamle başına yanlış olasılığı (rastgele / önizleme bakan oyuncu), faz özeti |
| `loc.py` | yanlış olayların yerelliği: kapanan alan boyutu, en yakın/ortalama uzaklık, kurban parça komşu mu (`events`, `evsum`) |
| `hc.py`, `hc2.py`, `hc3.py` | kuyruk hill-climb (yalnız sıra): hedef yanlış olasılığı / hedef 3/3-3/2-3/1 dağılımı, kısıt: çözülebilir + önizleme-bakan oyuncu ≥ eşik |
| `geoc.py` | geometrinin kendi tuzak payı (rastgele güvenli sıralarda kalan parçaların tuzak oranı) |
| `s3.py … s6.py` | L01 için yerellik amaçlı arama (aday kuyruklar), `cmp.py` aday karşılaştırma tablosu, `door.py` "tek açık yan" testi |
| `l2.py`, `l2s.py`, `l2t.py`, `l2d.py`, `fin.py` | L02-V2 (kaktüs): geo kurulumu, kuyruk araması (kol/geçit olayı payı hedefli), olay dökümü, final sayılar |
| `*.json` | aday kuyruklar (`l01_T22.json` = seçilen L01-V4 kuyruğu, `l02v2_c_A.json` = seçilen L02-V2 kuyruğu) |

## m2q/ — M2 (iki yollu oda) + queue araştırması
`kit.py` (Kemer silüeti ring parçalama, `board_for`, `assignments`), `metr.py` (durum/çatal/derin-önce ölçüleri), `sweep.py` (k3…k7 tarama), `hid.py`/`hid2.py` (gizli kuyruk varsayımlarıyla "okunur karar", peek derinliği 0/1/2), `tab.py`, `summ.py`, `good.py`, `ex.py`, `more.py`, `cat.py`, `k4.py`.
