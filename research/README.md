# Renk-yerleştirme puzzle'ı: karar motorunu hangi değişkenler üretiyor?

Solver / simülasyon / level-üretimi **araştırma** kodu. Oyun kodu (Unity vb.) değildir ve oyun tasarımını değiştirmez.
Sonuçların yorumu için `REPORT.md`.

## Referans model (değişmedi)
Grid hedef; `E` giriş, `#` duvar, `.` zemin, harf = renkli hedef hücre. İşçi 4-komşulukla hareket eder, dolan hücre kalıcı engel olur.
Oyuncu **renk** seçer; sabit **W** kutu **en derinden başlayarak** yerleşir; erişilemez hedef hücre = kayıp (`sealed`).
Oyuncu miktar seçmez; W level parametresidir. Ana deneyler 3 renk, A/B deneyi 3 vs 4.

## Dosyalar
| Dosya | İçerik |
|---|---|
| `puzzle_engine.py` | tam (exact) solver + metrikler. Dalga başına tek BFS (eski kutu-kutu uygulamayla `tests/` içinde eşitlik testi). |
| `puzzle_shapes.py` | 8 silüet **maskesi** (yalnız geometri) + sentetik kare desenler. |
| `puzzle_colormaps.py` | CM1–CM10 algoritmik renk haritaları (k=3/4), renk-yapısı tanımlayıcıları, bölge-boyama ablasyonu. |
| `puzzle_access.py` | 18 erişim düzeni (OPEN, CORRIDOR, BOTTLENECK, SPLIT, SPLIT+BOTTLENECK, MULTI) + genel `P:TWIDE,BDA` düzenleri. |
| `run_experiments.py` | paralel taramalar: `broad, ab4, synth, size, wsweep, region, refine, refine_layout`. |
| `add_dep_descriptors.py`, `add_order_descriptors.py` | W'den bağımsız yapısal tanımlayıcılar (baskınlık, tüm-renk-sırası sıkılığı) → `results/dep_descriptors.csv`. |
| `an_*.py` | analizler; çıktıları `results/summary/logs/*.txt`, tablolar `results/summary/*.csv`. |
| `export_results.py`, `fix_bigints.py` | jsonl → csv.gz; büyük tamsayıları JSON-güvenli yapar. |
| `results/*.csv.gz` | **ham aday tabloları** (her satır = silüet × renk haritası × erişim × W). |
| `results/summary.json` | başlık sayıları (η², çözülebilirlik, en az/çok karar üreten kombinasyonlar). |

## Yeniden üretme
```
pip install numpy pandas scipy statsmodels scikit-learn
python3 tests/test_engine_equivalence.py        # motor doğrulaması (0 uyuşmazlık beklenir)
python3 run_experiments.py broad                # 4320 aday, ~1 dk (4 çekirdek) -> results/broad.jsonl
python3 fix_bigints.py && python3 export_results.py
python3 add_dep_descriptors.py && python3 add_order_descriptors.py
python3 an_anova.py                             # vb.; analiz betikleri csv.gz'yi de okur
```
Duyarlılık: `PUZZLE_DELTA=0.10 PUZZLE_TAG=_delta0.10 python3 run_experiments.py broad`.

## Ham tablo sütunları (seçilmiş)
Kimlik: `exp, src (silüet | syn:desen | reg:silüet:R:idx), cm, k (renk sayısı), layout, family, bin, W, scale, cells, waves_nominal`.
Çözüm: `solv, seq_raw, seq_canon (komütasyon-normal form, üst sınır), log10_seq_*, greedy_deep, greedy_stock`.
Rastgele oyuncu: `rnd0 (tam), risk (hamle başına), win_undo0/1/2`.
**Karar sınıfları** (kazanan DAG'deki durumlar; beklenen sayılar "güvenli hamleler arasında tekdüze" politikayla, yollar boyunca):
`e_forced` (tek yasal hamle), `e_free` (kayıp yok, gelecek riski farkı < δ), `e_meansafe` (kayıp yok ama δ ≥ 0.05 fark),
`e_trap` (≥2 güvenli + ≥1 kaybettiren), `e_crit` (tek güvenli, ≥1 kaybettiren); `e_meaningful = meansafe+trap+crit`; `e_risky = trap+crit`;
`dens_* = e_* / e_moves`; `forced_free_ratio`.
Tuzak: `trap_timing` (riskli durumların ort. ilerlemesi), `trap_sharp` (kaybettiren seçenek payı), `crit_share`, `first_trap`, `risky_early/mid/late`.
Pişmanlık: `regret_mean/max` (hata sonrası kaç undo gerekir), `rec1/rec2` (hataların 1/2 undo ile kurtarılma payı).
Renk yapısı: `cm_counts, cm_dominant, cm_entropy(_norm), cm_comp_total (ayrı parça), cm_trans_sp, cm_clustering, ring_*`.
Giriş-derinlik: `ent_trans(_per_cell/_per_wave), ent_wtrans, ent_runs, ent_mean_run, deep_colors/entropy`.
Yapısal (ayrı dosya): `ord_valid_frac` (her renk tek seferde gönderilirse geçerli renk sırası payı), `ord_first_safe`, `dep_*` (tek-hücre baskınlık).

## Bilinen sınırlar
Silüetler elle parametrize; renk haritaları algoritmik ama 10 aile; deepest-first tek yerleşim kuralı; eşikler (δ, imza kovaları) araştırmacı seçimi;
çözülebilir adaylarla sınırlı koşullu analizler (çözülemeyen yüksek-geçişli haritalar dışarıda kalır); istatistikler açıklayıcı, nedensel kanıt değil
(tek istisna: bölge-boyama ablasyonu, parçalanmışlığı sabit tutar).
