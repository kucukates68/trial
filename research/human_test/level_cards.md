# İnsan testi seviye kartları
Izgara: `E` giriş, `#` duvar, `.` zemin, `A/B/C` renkli hedef hücreler. Metrikler çözücüden (hedef değil).

## A01S  (grup A, eş 1) — car / CM7 / SPB3 — 70 hücre, W=4, 18 dalga
```
######E###########
######.###########
##...AAAAAAAA...##
##...AAAAAAAB...##
##AAAABCCCCCABBB.E
##ABBCCBBBACCAAB##
##CCBCBCCCBBCBBB##
##..CBC....BBB..##
##..CCC....CBB..##
##################
##################
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACABACBBCCBCACBABA
- DH beklenen 1.064, anlık hata payı 0.959, gecikmeli-hata/oyun 0.184, kör ilerleme 0.059
- riskli karar/oyun 9.709 (tek-doğru 4.408), filler 0.461, ABC 3.108, rastgele kazanma undo0/1/2 0.005/0.033/0.073

## A02S  (grup A, eş 2) — cat / CM7 / SPB2 — 54 hücre, W=5, 12 dalga
```
############
############
##.AA..AA.##
##.ACAAAB.##
E.ACBAABAB##
##ACBBBCAB##
##CBCCCCAB##
##CBCCCCAB.E
##.CBBAAB.##
##.CCCBBB.##
############
############
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACABACCBBCAB
- DH beklenen 1.013, anlık hata payı 0.991, gecikmeli-hata/oyun 0.031, kör ilerleme 0.065
- riskli karar/oyun 6.738 (tek-doğru 4.563), filler 0.439, ABC 4.11, rastgele kazanma undo0/1/2 0.007/0.037/0.118

## A03S  (grup A, eş 3) — car / CM10 / BOT2 — 70 hücre, W=4, 18 dalga
```
###########E######
###########.######
##...AAAAAAAA...##
##...AAAABBBB...##
##BBBBBBBBCCCCCC##
##CCCCCAAAAAAAAA##
##AAABBBBBBBBBBB##
##..BCC....CCC..##
##..CCC....CCC..##
##################
##################
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACABABCCCBABCBACBA
- DH beklenen 1.14, anlık hata payı 0.929, gecikmeli-hata/oyun 0.422, kör ilerleme 0.06
- riskli karar/oyun 12.024 (tek-doğru 6.316), filler 0.332, ABC 3.749, rastgele kazanma undo0/1/2 0.0/0.003/0.018

## A04S  (grup A, eş 4) — cat / CM10 / SPB3 — 54 hücre, W=5, 12 dalga
```
####E#######
####.#######
##.AA..AA.##
##.AAAAAB.##
##BBBBBBBB.E
##CCCCCCCC##
##CAAAAAAA##
##AABBBBBB##
##.BBBCCC.##
##.CCCCCC.##
############
############
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACACBCBBAACB
- DH beklenen 1.0, anlık hata payı 1.0, gecikmeli-hata/oyun 0.0, kör ilerleme 0.075
- riskli karar/oyun 7.612 (tek-doğru 4.624), filler 0.366, ABC 2.229, rastgele kazanma undo0/1/2 0.003/0.013/0.062

## A05S  (grup A, eş 5) — car / CM10 / MUL5 — 70 hücre, W=8, 9 dalga
```
######E###########
######.###########
##...AAAAAAAA...##
##...AAAABBBB...##
E.BBBBBBBBCCCCCC##
##CCCCCAAAAAAAAA##
##AAABBBBBBBBBBB##
##..BCC....CCC..##
##..CCC....CCC..##
##.......#########
##EEEEEEE#########
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: AABACCCBB
- DH beklenen 1.071, anlık hata payı 0.947, gecikmeli-hata/oyun 0.084, kör ilerleme 0.122
- riskli karar/oyun 3.666 (tek-doğru 1.982), filler 0.593, ABC 3.806, rastgele kazanma undo0/1/2 0.204/0.485/0.724

## A06S  (grup A, eş 6) — cat / CM8 / BOT2 — 54 hücre, W=6, 9 dalga
```
#######E####
#######.####
##.AA..AA.##
##.ABAABA.##
##ABCBBCBA##
##ABCCCCBA##
##BCCCCCBA##
##BCCCCCBA##
##.BCCBBA.##
##.BBBAAA.##
############
############
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: AABBCCCBA
- DH beklenen 1.079, anlık hata payı 0.921, gecikmeli-hata/oyun 0.221, kör ilerleme 0.12
- riskli karar/oyun 5.596 (tek-doğru 3.293), filler 0.378, ABC 2.33, rastgele kazanma undo0/1/2 0.062/0.158/0.275

## A07L  (grup A, eş 7) — bird / CM8 / COR1 — 196 hücre, W=16, 13 dalga
```
##########################
##########################
##..........AA..........##
##..........AA..........##
##....AAAAAABBAAAAAA....##
##....AAAAAABBAAAAAA....##
##....AABBBBCCBBBBBBAAAA##
##....AABBBBCCBBBBBBAAAA##
##..AABBCCCCCCCCCCBBAA..##
##..AABBCCCCCCCCCCBBAA..##
##BBCCCCCCCCCCCCCCAA....##
##BBCCCCCCCCCCCCCCAA....##
##BBBBBBBBCCCCCCAAAA....##
##BBBBBBBBCCCCCCAAAA....##
##........BBBBAA........##
##........BBBBAA........##
##........BB..AA........##
##........BB..AA........##
##......................##
##EEEEEEEEEEEEEEEEEEEEEE##
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACBBABBACCCAA
- DH beklenen 1.0, anlık hata payı 1.0, gecikmeli-hata/oyun 0.0, kör ilerleme 0.082
- riskli karar/oyun 5.367 (tek-doğru 2.231), filler 0.587, ABC 1.16, rastgele kazanma undo0/1/2 0.125/0.376/0.633

## A08L  (grup A, eş 8) — landscape / CM8 / MUL1 — 404 hücre, W=33, 14 dalga
```
##EEEEEEEEEEEEEEEE##################
##................##################
##......AA................AA..AAAA##
##......AA................AA..AAAA##
##....AABBAA..........AAAABBAABBAA##
##....AABBAA..........AAAABBAABBAA##
##..AABBCCBBAA......AABBBBCCCCCCAA##
##..AABBCCBBAA......AABBBBCCCCCCAA##
##..AABBCCCCBBAA....AABBCCCCCCCCAA##
##..AABBCCCCBBAA....AABBCCCCCCCCAA##
##..AABBCCCCBBAA....AACCCCCCCCCCAA##
E...AABBCCCCBBAA....AACCCCCCCCCCAA##
E...BBCCCCCCCCBB......AAAACCAAAA..##
E...BBCCCCCCCCBB......AAAACCAAAA..##
E...BBCCCCCCCCBB..........AA.......E
E...BBCCCCCCCCBB..........AA......##
E.BBCCCCCCCCCCCCBBBBBBBBAACCAAAAAA##
E.BBCCCCCCCCCCCCBBBBBBBBAACCAAAAAA##
E.BBBBBBBBBBBBBBBBBBBBBBBBBBAAAAAA##
E.BBBBBBBBBBBBBBBBBBBBBBBBBBAAAAAA##
########################.###########
########################E###########
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: AABACCBCBCABBA
- DH beklenen 1.0, anlık hata payı 1.0, gecikmeli-hata/oyun 0.0, kör ilerleme 0.073
- riskli karar/oyun 7.885 (tek-doğru 3.787), filler 0.437, ABC 2.599, rastgele kazanma undo0/1/2 0.044/0.124/0.298

## A09L  (grup A, eş 9) — tree / CM7 / SPB1 — 256 hücre, W=20, 14 dalga
```
#######E##############
#######.##############
##........AA........##
##........AA........##
##....AAAAAAAAAA....##
##....AAAAAAAAAA....##
##..AAAAAABBAAAAAA..##
##..AAAAAABBAAAAAA..##
##AAAABBBBCCBBBBAAAA##
##AAAABBBBCCBBBBAAAA##
##AACCBBCCCCCCCCAABB##
##AACCBBCCCCCCCCAABB##
##AACCBBBBCCCCCCAABB##
##AACCBBBBCCCCCCAABB##
##..CCBBBBCCCCAABB..##
##..CCBBBBCCCCAABB..##
##....CCCCBBAABB....##
##....CCCCBBAABB....##
##........CCBB......##
##........CCBB......##
##........CCBB......##
##........CCBB......##
##........CCBB......##
##........CCBB......##
##........CCBB......##
##........CCBB......##
##......CCBBBBBB....##
##......CCBBBBBB....##
##############.#######
##############E#######
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACBCBCCAABBBAA
- DH beklenen 1.064, anlık hata payı 0.967, gecikmeli-hata/oyun 0.121, kör ilerleme 0.082
- riskli karar/oyun 7.767 (tek-doğru 4.931), filler 0.445, ABC 2.494, rastgele kazanma undo0/1/2 0.009/0.061/0.182

## A10L  (grup A, eş 10) — human / CM7 / COR1 — 284 hücre, W=23, 14 dalga
```
####################
####################
##......AABBBB....##
##......AABBBB....##
##AA..AABBBBBBBB..##
##AA..AABBBBBBBB..##
##AA..AAAACCBBBB..##
##AA..AAAACCBBBB..##
##..AAAAAACCBBBB..##
##..AAAAAACCBBBB..##
##..AA..AABBBB....##
##..AA..AABBBB....##
##..AAAAAACCBBBBBB##
##..AAAAAACCBBBBBB##
##....AAAACCCCBBBB##
##....AAAACCCCBBBB##
##....AACCCCCCBBBB##
##....AACCCCCCBBBB##
##....AACCBBCCBBBB##
##....AACCBBCCBBBB##
##....AACCCCBBBB..##
##....AACCCCBBBB..##
##....AAAA..CCCC..##
##....AAAA..CCCC..##
##....AACC..CCCC..##
##....AACC..CCCC..##
##....AACC..CCCC..##
##....AACC..CCCC..##
##....AACC..CCCC..##
##....AACC..CCCC..##
##................##
##EEEEEEEEEEEEEEEE##
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACABABBBCBAACC
- DH beklenen 1.0, anlık hata payı 1.0, gecikmeli-hata/oyun 0.0, kör ilerleme 0.081
- riskli karar/oyun 6.045 (tek-doğru 0.826), filler 0.568, ABC 0.602, rastgele kazanma undo0/1/2 0.113/0.343/0.616

## B01S  (grup B, eş 1) — tree / CM7 / COR1 — 64 hücre, W=4, 17 dalga
```
#############
#############
##....A....##
##..AAAAA..##
##.AAABAAA.##
##AABBCBBAA##
##ACBCCCCAB##
##ACBBCCCAB##
##.CBBCCAB.##
##..CCBAB..##
##....CB...##
##....CB...##
##....CB...##
##....CB...##
##...CBBB..##
##.........##
##EEEEEEEEE##
```
- ilk hamlede güvenli renkler: ['B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: BBCBBBBACCCACAAAA
- DH beklenen 4.031, anlık hata payı 0.397, gecikmeli-hata/oyun 2.667, kör ilerleme 0.251
- riskli karar/oyun 9.48 (tek-doğru 4.52), filler 0.442, ABC 3.564, rastgele kazanma undo0/1/2 0.004/0.019/0.018

## B02S  (grup B, eş 2) — landscape / CM7 / BOT1 — 101 hücre, W=9, 12 dalga
```
####################
####################
##...A........A.AA##
##..AAA.....AAAAAB##
##.AACAA...AAACBBB##
##.AACCAA..AACCCBB##
##.AACCAA..BBBCBBB##
##.ACCCCA...BBBBB.##
##.ABCCBC.....B...##
##ABBBBBBCCCCBBBBB##
##ACCCCCCCCCCCCBBB##
######.#############
######E#############
```
- ilk hamlede güvenli renkler: ['A', 'B'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ABBBBCCAAACC
- DH beklenen 3.623, anlık hata payı 0.491, gecikmeli-hata/oyun 2.062, kör ilerleme 0.312
- riskli karar/oyun 7.703 (tek-doğru 5.828), filler 0.358, ABC 5.416, rastgele kazanma undo0/1/2 0.004/0.022/0.029

## B03S  (grup B, eş 3) — house / CM10 / SPB1 — 81 hücre, W=5, 18 dalga
```
#####E########
#####.########
##....A..AA.##
##...AAA.AA.##
##..AAAAA...##
##.ABBBBBBB.##
##BBBBBBCCCC##
##CCCCCCCCCC##
##AAAAAAAAAA##
##AAABBBBBBB##
##BBBBBBBCCC##
##CCCCCCCCCC##
########.#####
########E#####
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACACACCCAAABBBBBBC
- DH beklenen 3.364, anlık hata payı 0.482, gecikmeli-hata/oyun 2.681, kör ilerleme 0.192
- riskli karar/oyun 11.257 (tek-doğru 5.98), filler 0.375, ABC 5.507, rastgele kazanma undo0/1/2 0.005/0.012/0.022

## B04S  (grup B, eş 4) — car / CM10 / SPB2 — 70 hücre, W=6, 12 dalga
```
##################
##################
##...AAAAAAAA...##
##...AAAABBBB...##
E.BBBBBBBBCCCCCC##
##CCCCCAAAAAAAAA##
##AAABBBBBBBBBBB.E
##..BCC....CCC..##
##..CCC....CCC..##
##################
##################
```
- ilk hamlede güvenli renkler: ['A'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: AAAACBBCBCCB
- DH beklenen 3.241, anlık hata payı 0.529, gecikmeli-hata/oyun 2.667, kör ilerleme 0.275
- riskli karar/oyun 10.0 (tek-doğru 10.0), filler 0.167, ABC 2.333, rastgele kazanma undo0/1/2 0.0/0.002/0.004

## B05S  (grup B, eş 5) — car / CM10 / MUL1 — 70 hücre, W=8, 9 dalga
```
##EEEEEEE#########
##.......#########
##...AAAAAAAA...##
##...AAAABBBB...##
##BBBBBBBBCCCCCC##
E.CCCCCAAAAAAAAA##
E.AAABBBBBBBBBBB.E
E...BCC....CCC..##
E...CCC....CCC..##
###########.######
###########E######
```
- ilk hamlede güvenli renkler: ['A', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: AACACCBBB
- DH beklenen 3.214, anlık hata payı 0.173, gecikmeli-hata/oyun 1.635, kör ilerleme 0.361
- riskli karar/oyun 5.328 (tek-doğru 1.203), filler 0.408, ABC 4.344, rastgele kazanma undo0/1/2 0.089/0.152/0.154

## B06S  (grup B, eş 6) — cat / CM8 / MUL5 — 54 hücre, W=6, 9 dalga
```
####E#######
####.#######
##.AA..AA.##
##.ABAABA.##
E.ABCBBCBA##
##ABCCCCBA##
##BCCCCCBA##
##BCCCCCBA##
##.BCCBBA.##
##.BBBAAA.##
##....######
##EEEE######
```
- ilk hamlede güvenli renkler: ['B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: BBCCCBAAA
- DH beklenen 3.172, anlık hata payı 0.176, gecikmeli-hata/oyun 2.24, kör ilerleme 0.352
- riskli karar/oyun 6.0 (tek-doğru 2.875), filler 0.333, ABC 2.389, rastgele kazanma undo0/1/2 0.026/0.034/0.028

## B07L  (grup B, eş 7) — cat / CM8 / MUL1 — 216 hücre, W=24, 9 dalga
```
##EEEEEEEE##########
##........##########
##..AAAA....AAAA..##
##..AAAA....AAAA..##
##..AABBAAAABBAA..##
##..AABBAAAABBAA..##
##AABBCCBBBBCCBBAA##
##AABBCCBBBBCCBBAA##
##AABBCCCCCCCCBBAA##
##AABBCCCCCCCCBBAA##
E.BBCCCCCCCCCCBBAA##
E.BBCCCCCCCCCCBBAA##
E.BBCCCCCCCCCCBBAA##
E.BBCCCCCCCCCCBBAA.E
E...BBCCCCBBBBAA..##
E...BBCCCCBBBBAA..##
E...BBBBBBAAAAAA..##
E...BBBBBBAAAAAA..##
#############.######
#############E######
```
- ilk hamlede güvenli renkler: ['B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: BBCCCBAAA
- DH beklenen 2.599, anlık hata payı 0.304, gecikmeli-hata/oyun 1.958, kör ilerleme 0.289
- riskli karar/oyun 6.0 (tek-doğru 3.25), filler 0.333, ABC 0.764, rastgele kazanma undo0/1/2 0.02/0.05/0.061

## B08L  (grup B, eş 8) — car / CM8 / SPB1 — 280 hücre, W=23, 13 dalga
```
##########E#####################
##########.#####################
##......AAAAAAAAAAAAAAAA......##
##......AAAAAAAAAAAAAAAA......##
##......AABBBBBBBBBBBBAA......##
##......AABBBBBBBBBBBBAA......##
##AAAAAABBCCCCCCCCCCCCBBAAAAAA##
##AAAAAABBCCCCCCCCCCCCBBAAAAAA##
##BBCCCCCCCCCCCCCCBBCCCCBBBBAA##
##BBCCCCCCCCCCCCCCBBCCCCBBBBAA##
##BBBBCCCCCCBBBBBBAACCCCCCAAAA##
##BBBBCCCCCCBBBBBBAACCCCCCAAAA##
##....BBCCBB........AACCAA....##
##....BBCCBB........AACCAA....##
##....BBBBBB........BBAAAA....##
##....BBBBBB........BBAAAA....##
#####################.##########
#####################E##########
```
- ilk hamlede güvenli renkler: ['A', 'B'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: AABBBBACCCCAA
- DH beklenen 2.589, anlık hata payı 0.486, gecikmeli-hata/oyun 2.792, kör ilerleme 0.21
- riskli karar/oyun 10.879 (tek-doğru 7.941), filler 0.163, ABC 2.814, rastgele kazanma undo0/1/2 0.001/0.007/0.012

## B09L  (grup B, eş 9) — tree / CM7 / BOT1 — 256 hücre, W=20, 14 dalga
```
######################
######################
##........AA........##
##........AA........##
##....AAAAAAAAAA....##
##....AAAAAAAAAA....##
##..AAAAAABBAAAAAA..##
##..AAAAAABBAAAAAA..##
##AAAABBBBCCBBBBAAAA##
##AAAABBBBCCBBBBAAAA##
##AACCBBCCCCCCCCAABB##
##AACCBBCCCCCCCCAABB##
##AACCBBBBCCCCCCAABB##
##AACCBBBBCCCCCCAABB##
##..CCBBBBCCCCAABB..##
##..CCBBBBCCCCAABB..##
##....CCCCBBAABB....##
##....CCCCBBAABB....##
##........CCBB......##
##........CCBB......##
##........CCBB......##
##........CCBB......##
##........CCBB......##
##........CCBB......##
##........CCBB......##
##........CCBB......##
##......CCBBBBBB....##
##......CCBBBBBB....##
#######.##############
#######E##############
```
- ilk hamlede güvenli renkler: ['B'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: BBBACCBCBAACAA
- DH beklenen 2.552, anlık hata payı 0.501, gecikmeli-hata/oyun 2.0, kör ilerleme 0.199
- riskli karar/oyun 8.233 (tek-doğru 4.598), filler 0.412, ABC 1.899, rastgele kazanma undo0/1/2 0.003/0.009/0.024

## B10L  (grup B, eş 10) — human / CM7 / COR1 — 284 hücre, W=32, 9 dalga
```
####################
####################
##......AABBBB....##
##......AABBBB....##
##AA..AABBBBBBBB..##
##AA..AABBBBBBBB..##
##AA..AAAACCBBBB..##
##AA..AAAACCBBBB..##
##..AAAAAACCBBBB..##
##..AAAAAACCBBBB..##
##..AA..AABBBB....##
##..AA..AABBBB....##
##..AAAAAACCBBBBBB##
##..AAAAAACCBBBBBB##
##....AAAACCCCBBBB##
##....AAAACCCCBBBB##
##....AACCCCCCBBBB##
##....AACCCCCCBBBB##
##....AACCBBCCBBBB##
##....AACCBBCCBBBB##
##....AACCCCBBBB..##
##....AACCCCBBBB..##
##....AAAA..CCCC..##
##....AAAA..CCCC..##
##....AACC..CCCC..##
##....AACC..CCCC..##
##....AACC..CCCC..##
##....AACC..CCCC..##
##....AACC..CCCC..##
##....AACC..CCCC..##
##................##
##EEEEEEEEEEEEEEEE##
```
- ilk hamlede güvenli renkler: ['A', 'B'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ABBBCCCAA
- DH beklenen 2.551, anlık hata payı 0.308, gecikmeli-hata/oyun 1.708, kör ilerleme 0.287
- riskli karar/oyun 4.812 (tek-doğru 3.062), filler 0.465, ABC 0.604, rastgele kazanma undo0/1/2 0.046/0.092/0.085

## C01S  (grup C) — landscape / CM10 / MUL2 — 101 hücre, W=6, 18 dalga
```
######E#############
######.#############
##...A........A.AA.E
##..AAA.....AAAAAA.E
##.AAAAB...BBBBBBB.E
##.BBBBBB..BBBCCCC.E
##.CCCCCC..CCCCCCC##
##.AAAAAA...AAAAA.##
E..AAAAAA.....B...##
##BBBBBBBBBBBBBBBB##
##CCCCCCCCCCCCCCCC##
######.#############
######E#############
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACABABCCCBAABACCBB
- DH beklenen 1.415, anlık hata payı 0.75, gecikmeli-hata/oyun 0.615, kör ilerleme 0.076
- riskli karar/oyun 6.226 (tek-doğru 1.903), filler 0.654, ABC 3.077, rastgele kazanma undo0/1/2 0.139/0.297/0.369

## C02S  (grup C) — bird / CM8 / SPL3 — 49 hücre, W=3, 18 dalga
```
##EEEEE########
##.....########
##.....A.....##
##..AAABAAA..##
##..ABBCBBBAA##
##.ABCCCCCBA.##
##BCCCCCCCA..##
##BBBBCCCAA..##
##....BBA....##
##....B.A....##
#######......##
#######EEEEEE##
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACABBCCCCBBBABCAAA
- DH beklenen 1.117, anlık hata payı 0.927, gecikmeli-hata/oyun 0.187, kör ilerleme 0.066
- riskli karar/oyun 6.209 (tek-doğru 2.08), filler 0.655, ABC 0.856, rastgele kazanma undo0/1/2 0.118/0.297/0.481

## C03S  (grup C) — human / CM7 / MUL1 — 71 hücre, W=4, 18 dalga
```
##EEEE######
##....######
##...ABB..##
##A.ABBBB.##
##A.AACBB.##
##.AAACBB.##
##.A.ABB..##
##.AAACBBB##
##..AACCBB##
E...ACCCBB##
E...ACBCBB##
E...ACCBB..E
E...AA.CC.##
E...AC.CC.##
E...AC.CC.##
E...AC.CC.##
#######.####
#######E####
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACABABBBCCAACBCCBA
- DH beklenen 1.004, anlık hata payı 0.998, gecikmeli-hata/oyun 0.006, kör ilerleme 0.057
- riskli karar/oyun 6.029 (tek-doğru 1.297), filler 0.665, ABC 1.163, rastgele kazanma undo0/1/2 0.143/0.337/0.565

## C04S  (grup C) — bird / CM8 / MUL1 — 49 hücre, W=3, 18 dalga
```
##EEEEE########
##.....########
##.....A.....##
##..AAABAAA..##
##..ABBCBBBAA##
##.ABCCCCCBA.##
E.BCCCCCCCA..##
E.BBBBCCCAA...E
E.....BBA....##
E.....B.A....##
#########.#####
#########E#####
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACABABBCCBCCACBABA
- DH beklenen 1.05, anlık hata payı 0.954, gecikmeli-hata/oyun 0.107, kör ilerleme 0.062
- riskli karar/oyun 5.369 (tek-doğru 2.011), filler 0.702, ABC 0.591, rastgele kazanma undo0/1/2 0.164/0.335/0.49

## C05S  (grup C) — cat / CM3 / COR3 — 54 hücre, W=3, 18 dalga
```
##EEEE######
##....######
##.AA..CC.##
##.AAACCC.##
##AAABAACA##
##AAABAAAA##
##AABBBAAA##
##AAABAAAA##
##.AAAAAA.##
##.AAAAAA.##
############
############
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACABABAAAAAAAACAAA
- DH beklenen 1.0, anlık hata payı 1.0, gecikmeli-hata/oyun 0.0, kör ilerleme 0.056
- riskli karar/oyun 4.995 (tek-doğru 4.864), filler 0.722, ABC 1.598, rastgele kazanma undo0/1/2 0.402/0.419/0.486

## C06S  (grup C) — car / CM2 / SPB2 — 70 hücre, W=4, 18 dalga
```
##################
##################
##...AAAAAAAA...##
##...AAAAAAAB...##
E.AAAAAAAAABBBBB##
##CCCCCCCBBBBBBB##
##CCCCCCCCBBBBBB.E
##..CCC....BBB..##
##..CCC....CCB..##
##################
##################
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACACABBBCAACBCCABB
- DH beklenen 1.0, anlık hata payı 1.0, gecikmeli-hata/oyun 0.0, kör ilerleme 0.057
- riskli karar/oyun 4.577 (tek-doğru 1.053), filler 0.746, ABC 2.677, rastgele kazanma undo0/1/2 0.253/0.504/0.694

## C07L  (grup C) — human / CM8 / SPB1 — 284 hücre, W=23, 14 dalga
```
######E#############
######.#############
##......AAAAAA....##
##......AAAAAA....##
##AA..AACCCCCCAA..##
##AA..AACCCCCCAA..##
##AA..AABBCCCCAA..##
##AA..AABBCCCCAA..##
##..AAAABBCCCCAA..##
##..AAAABBCCCCAA..##
##..AA..AACCAA....##
##..AA..AACCAA....##
##..AAAABBCCCCAAAA##
##..AAAABBCCCCAAAA##
##....AABBCCCCCCAA##
##....AABBCCCCCCAA##
##....BBCCCCCCCCAA##
##....BBCCCCCCCCAA##
##....BBCCCCCCCCAA##
##....BBCCCCCCCCAA##
##....BBCCBBCCAA..##
##....BBCCBBCCAA..##
##....BBBB..BBBB..##
##....BBBB..BBBB..##
##....BBBB..BBBB..##
##....BBBB..BBBB..##
##....BBBB..BBBB..##
##....BBBB..BBBB..##
##....BBBB..BBBB..##
##....BBBB..BBBB..##
#############.######
#############E######
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACABACCCBBABAB
- DH beklenen 1.344, anlık hata payı 0.746, gecikmeli-hata/oyun 0.567, kör ilerleme 0.097
- riskli karar/oyun 4.592 (tek-doğru 2.746), filler 0.672, ABC 2.029, rastgele kazanma undo0/1/2 0.11/0.287/0.417

## C08L  (grup C) — cat / CM8 / COR1 — 216 hücre, W=18, 12 dalga
```
####################
####################
##..AAAA....AAAA..##
##..AAAA....AAAA..##
##..AABBAAAABBAA..##
##..AABBAAAABBAA..##
##AABBCCBBBBCCBBAA##
##AABBCCBBBBCCBBAA##
##AABBCCCCCCCCBBAA##
##AABBCCCCCCCCBBAA##
##BBCCCCCCCCCCBBAA##
##BBCCCCCCCCCCBBAA##
##BBCCCCCCCCCCBBAA##
##BBCCCCCCCCCCBBAA##
##..BBCCCCBBBBAA..##
##..BBCCCCBBBBAA..##
##..BBBBBBAAAAAA..##
##..BBBBBBAAAAAA..##
##................##
##EEEEEEEEEEEEEEEE##
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: AABABCCCBCBA
- DH beklenen 1.811, anlık hata payı 0.569, gecikmeli-hata/oyun 1.757, kör ilerleme 0.151
- riskli karar/oyun 8.077 (tek-doğru 4.671), filler 0.327, ABC 0.382, rastgele kazanma undo0/1/2 0.042/0.086/0.126

## C09L  (grup C) — bird / CM5 / OPEN — 196 hücre, W=16, 13 dalga
```
EEEEEEEEEEEEEEEEEEEEEEEEEE
E........................E
E...........BB...........E
E...........BB...........E
E.....CCBBAACCBBAACC.....E
E.....CCBBAACCBBAACC.....E
E.....AACCBBAACCBBAACCBB.E
E.....AACCBBAACCBBAACCBB.E
E...CCBBAACCBBAACCBBAA...E
E...CCBBAACCBBAACCBBAA...E
E.BBAACCBBAACCBBAACC.....E
E.BBAACCBBAACCBBAACC.....E
E.CCBBAACCBBAACCBBAA.....E
E.CCBBAACCBBAACCBBAA.....E
E.........CCBBAA.........E
E.........CCBBAA.........E
E.........AA..BB.........E
E.........AA..BB.........E
E........................E
EEEEEEEEEEEEEEEEEEEEEEEEEE
```
- ilk hamlede güvenli renkler: ['A', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACBABCBABBCAC
- DH beklenen 1.463, anlık hata payı 0.674, gecikmeli-hata/oyun 1.556, kör ilerleme 0.117
- riskli karar/oyun 9.667 (tek-doğru 5.417), filler 0.256, ABC 0.582, rastgele kazanma undo0/1/2 0.001/0.009/0.018

## C10L  (grup C) — bird / CM5 / SPB1 — 196 hücre, W=16, 13 dalga
```
########E#################
########.#################
##..........BB..........##
##..........BB..........##
##....CCBBAACCBBAACC....##
##....CCBBAACCBBAACC....##
##....AACCBBAACCBBAACCBB##
##....AACCBBAACCBBAACCBB##
##..CCBBAACCBBAACCBBAA..##
##..CCBBAACCBBAACCBBAA..##
##BBAACCBBAACCBBAACC....##
##BBAACCBBAACCBBAACC....##
##CCBBAACCBBAACCBBAA....##
##CCBBAACCBBAACCBBAA....##
##........CCBBAA........##
##........CCBBAA........##
##........AA..BB........##
##........AA..BB........##
#################.########
#################E########
```
- ilk hamlede güvenli renkler: ['B'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: BBBBBCACACACA
- DH beklenen 1.781, anlık hata payı 0.659, gecikmeli-hata/oyun 2.333, kör ilerleme 0.144
- riskli karar/oyun 12.0 (tek-doğru 12.0), filler 0.077, ABC 1.231, rastgele kazanma undo0/1/2 0.0/0.001/0.0

## W01S  (grup W) — bird / CM1 / OPEN — 49 hücre, W=6, 9 dalga
```
EEEEEEEEEEEEEEE
E.............E
E......A......E
E...BBBAAAA...E
E...BBBAAAAAA.E
E..BBBBCCAAA..E
E.BBBBCCCCA...E
E.BBBBCCCCC...E
E.....CCC.....E
E.....C.C.....E
E.............E
EEEEEEEEEEEEEEE
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: ACABACCBB
- DH beklenen None, anlık hata payı None, gecikmeli-hata/oyun 0.0, kör ilerleme None
- riskli karar/oyun 0.0 (tek-doğru 0.0), filler 1.0, ABC 0.0, rastgele kazanma undo0/1/2 1.0/1.0/1.0

## W02S  (grup W) — tree / CM3 / BOT1 — 64 hücre, W=8, 8 dalga
```
#############
#############
##....A....##
##..AAAAA..##
##.AAABAAA.##
##AAABBBAAA##
##AAABBBAAA##
##AAAABAAAA##
##.AAAAAAA.##
##..AAAAA..##
##....AA...##
##....AC...##
##....AC...##
##....CC...##
##...CCCC..##
####.########
####E########
```
- ilk hamlede güvenli renkler: ['A', 'B', 'C'] (yasal: ['A', 'B', 'C']) | örnek kazanan dizi: AABACAAA
- DH beklenen 1.0, anlık hata payı 1.0, gecikmeli-hata/oyun 0.0, kör ilerleme 0.125
- riskli karar/oyun 0.801 (tek-doğru 0.449), filler 0.9, ABC 0.907, rastgele kazanma undo0/1/2 0.719/0.938/0.994
