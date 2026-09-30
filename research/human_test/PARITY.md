# Solver ↔ prototip eşliği (insan testinden ÖNCE)

Amaç: **solver → seviye → gerçek prototip** üçünün aynı sistemi çalıştırdığını kanıtlamak. Bu olmadan oyuncu tepkisi tasarımdan mı, sistem farkından mı geldiği ayırt edilemez.
Bu aşamada yeni renk, mekanik, engel ya da level **yoktur**.

## Durum
Ortamda gerçek 244 hücrelik ızgara ve prototip **yok** (repo yalnız `research/` içeriyor). Aşağıdaki adımlar için iki şey gerekli (en altta "Gereken girdiler"). Altyapı hazır ve sınanmış; girdiler gelince her adım tek komut.

## Adımlar ↔ komutlar
| # | Adım | Komut / çıktı |
|---|---|---|
| 1 | Gerçek 244 hücrelik ızgarayı ölç | `python3 measure_grid.py cat244.txt --W <gerçek W>` → DH, riskli karar yoğunluğu, ABC, filler, regret, greedy, rastgele kazanma, zarf bayrakları |
| 2 | W'yi gerçek oyun değerine sabitle ve kaydet | W, `human_test/levels.json` ile aynı yerde `game_config.json` olarak yazılır: `{"grid_file": "...", "W": ..., "entrances": [...], "rules": {...}}` |
| 3 | Metrikleri raporla | `measure_grid.py --csv` çıktısı + kısa rapor |
| 4 | `example_winning_sequence` prototipte kazanıyor mu | `python3 parity.py vectors --grid cat244.txt --W <W> --id CAT244 --out conformance_cat244.json`; prototip aynı renk dizilerini oynayıp iz (trace) JSON'u dışa aktarır; `python3 parity.py check conformance_cat244.json traces.json` |
| 5 | Grid / W / giriş / renk dağılımı / yerleşim kuralı farkı | `python3 parity.py grid-diff solver_grid.txt prototype_grid.txt [--map O=A,K=B,W=C]` (boyut, giriş hücreleri, duvar/zemin, renk sayıları, hücre-hücre fark) ve `check`'in tanı bölümü |
| 6 | 32 seviyelik insan test seti | `human_test/conformance_vectors.json` (32 seviye, 99 vaka) aynı `check` ile önce bu setin prototipte eşleştiği doğrulanır |

## İz (trace) biçimi — dilden bağımsız
```json
{"traces": [{"level_id": "A01S", "cases": [
   {"name": "winning", "moves": [{"color": "A", "placed": [[r,c],[r,c]], "sealed": false}]}]}]}
```
Koordinatlar ızgara metnindeki sıfır-tabanlı (satır, sütun). `placed` **prototipin yerleştirme sırasında**. `sealed` isteğe bağlı (prototip kilitlenmeyi de hesaplıyorsa karşılaştırılır).
Tek bir seviye için `{"level_id": "...", "moves": [...]}` de kabul edilir (yalnız `winning` vakası).

## `check` ne söyler
Her vaka için ilk sapmayı sınıflar: **dalga boyu farkı** · **aynı hücreler, farklı sıra** · **farklı hücreler** (erişilebilirlik/komşuluk/yerleşim kuralı) · **kilitlenme algısı farkı**.
Fark varsa 32 kural varyantını dener (4/8 komşuluk × en-derinden/en-yakından × 4 eşitlik sırası × dolu hücre engel mi) ve prototip izini hangisinin yeniden ürettiğini yüzde olarak listeler (`tests/test_parity.py`: bilinen sapmalar doğru adlandırılıyor).
Solver kuralı: 4-komşuluk, dolu hücre kalıcı engel, en derinden başla, eşitlikte küçük satır sonra küçük sütun, dalga başına tek BFS (kutu-kutu yerleştirmeyle eşdeğer; `tests/test_engine_equivalence.py`).

## Gereken girdiler
1. **244 hücrelik hedef ızgara** düz metin: `E` giriş, `#` duvar, `.` zemin, diğer her harf bir renk (hedef hücre = 1 kutu). Renk harfleri farklıysa `--map` ile eşlenir; yalnız `E` ayrılmıştır.
2. **Oyunda kullanılacak gerçek W** ve **giriş tanımı** (hangi hücrelerden/ kenardan işçiler giriyor; tek kapı mı, tüm çevre mi).
3. **Prototip**: kaynak kodu (yerleştirme ve erişilebilirlik bölümü yeterli) **veya** yukarıdaki iz biçiminde dışa aktarım. Kaynak gelirse izi ben üretip kuralı satır satır karşılaştırabilirim.
4. Kutu ↔ hücre oranı (görselde stok 120/90/70 iken 6×6 örnekte 12/14/10 idi): W hücre mi kutu mu cinsinden.
