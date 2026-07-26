# GATE-2 — Sprint 2.22.0b.149 «الوسيط الأعمى عن المساحة في الأراضي»
# blast radius + before/after (measured on the REAL apply_moj_strategy over moj_weekly.csv)
#
# CLASS: VALUE-AFFECTING — raw_land ONLY, and only where the subject's SIZE BRACKET is EMPTY.
# DIRECTION: every affected area moves UPWARD — the fix removes a systematic understatement.
# CONTROLS: the 2 live land fixtures + all 4 villa fixtures are byte-identical (bottom block).
# BASIS VALIDITY (measured): ppm2(900-1500) / ppm2(category) = 0.96 median across the 14
#   affected areas that have big-plot evidence (range 0.71-1.12) -> the new basis is ~4%
#   optimistic, against the old basis being 50-70% low. National gradient: 1500+ = 0.79x 400-600.
# DEFERRED (same defect, NOT fixed here): the VILLA pool -- 95 of 288 (area,bracket) probes
#   fall back, up to 7.07x. A villa market median feeds the b20 leadership gate + the E25 rail,
#   so it needs its own signed blast-radius.
#
# Generated 2026-07-26 — Sprint 2.22.0b.149
# PO SIGNATURE (Gate-2): ______________________   date: __________

```
========================================================================================================
  b149 — LAND: subject 1500 m² in an area with NO registered 1500+ sale (the empty-bracket fallback)
========================================================================================================
  area                         n       BEFORE        AFTER     x      ppm2   before ر.ق/قدم²   after
  فريج بن عمران                1    1,000,000    8,427,000  8.43     5,618                62     522
  جزيرة اللؤلؤة                1      938,612    6,459,000  6.88     4,306                58     400
  فريج النصر                   2    1,480,738    5,595,000  3.78     3,730                92     347
  المرقاب الجديد               1    1,922,666    6,297,000  3.28     4,198               119     390
  الهتمي الجديد                1    2,000,000    6,465,000  3.23     4,310               124     400
  سميسمة                      26    1,515,002    4,681,500  3.09     3,121                94     290
  المطار                      17    1,900,869    5,293,500  2.78     3,529               118     328
  بو فسيلة                    12    1,265,000    3,378,000  2.67     2,252                78     209
  مدينة خليفة الجنوبية        15    2,312,487    5,833,500  2.52     3,889               143     361
  دحل الحمام                   8    2,400,000    5,700,000  2.38     3,800               149     353
  الغانم الجديد                3    1,850,000    4,035,000  2.18     2,690               115     250
  مدينة الكعبان                2      717,870    1,453,500  2.02       969                44      90
  مدينة الشمال                19    1,200,000    2,415,000  2.01     1,610                74     150
  مدينة خليفة الشمالية         4    3,050,000    6,124,500  2.01     4,083               189     379
  السلطة الجديدة              22    2,766,847    5,211,000  1.88     3,474               171     323
  لبديع                        6    2,470,000    4,645,500  1.88     3,097               153     288
  لجمليه                       4      998,137    1,854,000  1.86     1,236                62     115
  الغانم العتيق 16             3    4,300,000    7,588,500  1.76     5,059               266     470
  الغانم العتيق 6              3    4,300,000    7,588,500  1.76     5,059               266     470
  الشيحانية                    6    1,700,000    2,950,500  1.74     1,967               105     183
  أم بشر                       8    2,673,000    4,495,500  1.68     2,997               166     278
  فريج المناصير                4    2,500,000    3,939,000  1.58     2,626               155     244
  معيذر الوكير                16    2,260,440    3,487,500  1.54     2,325               140     216
  لجبيلات                      5    4,400,000    6,783,000  1.54     4,522               273     420
  المعراض                     25    2,500,000    3,820,500  1.53     2,547               155     237
  الثميد                      17    3,465,000    5,277,000  1.52     3,518               215     327
  عنيزة 65                    11    3,700,000    5,571,000  1.51     3,714               229     345
  عنيزة 66                    11    3,700,000    5,571,000  1.51     3,714               229     345
  عنيزة 63                    11    3,700,000    5,571,000  1.51     3,714               229     345
  عفجة معيذر                  10    1,900,000    2,856,000  1.50     1,904               118     177
  الفروش                       1    3,500,000    5,260,500  1.50     3,507               217     326
  روضة الجهانية                1    3,222,741    4,843,500  1.50     3,229               200     300
  مبيريك                      30    1,980,000    2,964,000  1.50     1,976               123     184
  حالة اوبير                   1    2,000,000    2,982,000  1.49     1,988               124     185
  امريخ الجنوبي                3    4,000,000    5,923,500  1.48     3,949               248     367
  جريان نجيمة                  9    4,200,000    5,380,500  1.28     3,587               260     333
  فريج المرة                   3    3,000,000    3,814,500  1.27     2,543               186     236
  روضة ابا الحيران             6    3,000,000    3,750,000  1.25     2,500               186     232
  عين سنان                     1    1,538,670    1,923,000  1.25     1,282                95     119
  مسيمير                       4    5,350,000    6,577,500  1.23     4,385               331     407
  جليعة                        3    5,150,000    5,992,500  1.16     3,995               319     371

  areas moved = 41   median x = 1.68   range 1.16–8.43   (ALL upward — the fix removes an understatement)

========================================================================================================
  BYTE-IDENTITY CONTROLS — populated bracket (land) + every villa (fix is land-only)
========================================================================================================
  land fixture 55010236 (b118, 5.7M)          الوعب      fb=False  total=   5,326,000  byte-identical
  land fixture 74328443 (1.2M)                الخور      fb=False  total=   2,195,266  byte-identical
  same area, POPULATED bracket                سميسمة     fb=False  total=   1,406,000  byte-identical
  fixture 54/541/6                            مريخ       fb=False  total=   5,100,000  byte-identical
  fixture 56/647/6                            المعمورة   fb=False  total=   3,741,176  byte-identical
  fixture 55/296/13                           المعراض    fb=False  total=   2,432,778  byte-identical
  fixture 56/565/21                           بو هامور   fb=False  total=   2,357,895  byte-identical
  villa EMPTY bracket (deferred, must NOT move)المطار     fb=True   total=   2,300,000  byte-identical

  scope discipline: OK — land only
```
