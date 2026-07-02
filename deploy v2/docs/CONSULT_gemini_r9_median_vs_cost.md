# CONSULT — Gemini round 9: median (market) vs cost — user-confusion framing

**Date:** 2026-07-02 · **Live:** b99 / Heroku v271 · **Trigger:** PO asked «ما الفرق بين سعر الوسيط وبين سعر التكلفة، وهل يحدث إرباك؟» → CC measured the 3 cases live → residual confusion confirmed on the cost-led result screen → PO: «دعنا نستشير جيميناي».

## ⚠️ Correction (PO challenge, 2026-07-02) — the first prompt overclaimed «فاخر» as fact
The PO caught a **methodological overreach**: «هل لديك إثبات أنّ العقارات المُباعة بنحو 5M فاخرة، أم تخمين؟». Measured verdict:
- The engine is **built-type/condition BLIND (R7)** — MoJ transactions carry **no** finish / build-year / condition field.
- `stock_strata` classifies each comp **by price-to-land ratio only** (its own methodology field says so: «هذه النسبة تفصل بين فئات العمر والتشطيب … فيلا فاخرة جديدة (نسبة ~2.3+)»). Measured for Marikh (n=29, land ref 3,212/m²): land_priced 3.4% · aging 6.9% · modern (1.5–2.2×) 37.9% · **luxury_new (≥2.2×) 51.7%** = the «52%».
- So **«فاخر / حديث البناء» is an INFERENCE from a high price-ratio, NOT an observed attribute.** A ≥2.2× ratio can also come from a bigger plot, more floors, a corner, a better micro-location, or a stronger buyer — the ratio conflates all price drivers into one "luxury/new" label.
- **The live copy overclaims it as fact** — short report §١ line 2198 «أغلب ما بيع غالياً … **كان فللاً جديدة فاخرة**» + line 2364 «ما تبيعه **الفلل الجديدة الفاخرة** حولك». Same class as the r7 dishonest label we rejected — now on our own copy.
- **Important nuance:** the VALUE (2.4M cost-led) is sound — it rests on the **measured** pool-unreliability (dispersion 0.62 > 0.30 + thin sample), NOT on the "luxury" label. Only the **explanatory copy** over-specifies the CAUSE. So the fix is copy-only / value-invariant.

The prompt below is the **corrected** version: it asks about the **defensible** claim (a higher PRICE class, finish unknown), never asserts finish, and adds the R7 guardrail.

**Measured facts (v271):** Marikh 54/541/6 → cost_led, amount 2,400,000 (=low), high 5,400,000 = market.median, value_stack.cost 2,378,094, pool dispersion 0.62, 51.7% of 29 comps priced ≥2.2× land · Abu Hamour 56/565/21 → matched, amount 2,400,000 = median, cost 2,194,070 (−8.6%, distinct «نهج DRC» line) · Land 55010236 → 7,100,000, no cost/median split, «لا مكوّن بناء» (b97).

**CC's proposed direction (copy-only, value-invariant):** describe the MEASURED price class + a SOFT inference («بيعت بأعلى من ٢٫٢× قيمة الأرض — فئة سعريّة أعلى، قد تكون أحدث/أكبر/أرقى») instead of asserting «فاخرة»; and qualify the bare «وسيط ٥٫٤م» basis line so it doesn't sit unqualified beside the «التقييم السوقي ٢٫٤م» headline.

---

## The prompt sent to Gemini (self-contained — Gemini is stateless — CORRECTED)

**استشارة تصميم/تقييم — عرض «الوسيط السوقيّ» مقابل «الكلفة» دون إرباكٍ ولا تجاوزٍ منهجيّ**

أنت مستشار خبير في UX التطبيقات الماليّة + التقييم العقاريّ (معايير RICS). أجب بإيجاز عمليّ، بتوصية واحدة واضحة لكلّ سؤال، وبصياغة عربيّة جاهزة للاستخدام حين تقترح نصّاً.

**السياق:** «ثمّن» أداة تقييم سوقيّ آليّ (AVM) للعقارات في قطر، وفق RICS. تستخدم منهجين:
- **الوسيط السوقيّ** = وسيط صفقات وزارة العدل المسجّلة لعقارات مماثلة (المنهج الأساس).
- **الكلفة (DRC)** = قيمة الأرض + البناء المُهلَك (منهج ثانويّ، يُستخدم كـ«أرضية» سعريّة).

**قاعدة القيادة:** الرقم المعروض للمستخدم **واحد فقط**، يُختار حسب جودة الأدلّة. حين يكون حوض المقارنة **غير موثوق إحصائيّاً** (عيّنة رقيقة + **تشتّت أسعار عالٍ**) تقود **الكلفة**، ويُعرض وسيط الحوض **مكتوماً كسقف أعلى**.

**قيود الصدق (غير قابلة للتفاوض — لا تقترح ما يخالفها):**
- المحرّك **أعمى عن التشطيب والعمر الفعليّ لكلّ صفقة** — بيانات وزارة العدل لا تحمل هذه الحقول. لذلك أيّ وصف كـ«فاخر/حديث» هو **استنتاجٌ من نسبة سعر الصفقة إلى قيمة الأرض**، لا معاينة. **لا تُقدّم استنتاج التشطيب كأنّه حقيقة مرصودة.**
- لا نعرض سعر الطلب/الإعلان كأنّه صفقة. الكلفة **أرضية** لا تُطارد السوق صعوداً أبداً.
- كلّ رقم «تقديريّ» و«ليس تقييماً معتمداً». هُويّة المنتج «تقييم سوقيّ آليّ».
- لا نُخفي رقماً بطريقة تُضلّل.

**الحالة المقيسة (فيلا امريخ):** الرقم مقودٌ بالكلفة = **٢٫٤م**، **لأنّ حوض المقارنة غير موثوق إحصائيّاً** (تشتّت الأسعار ٠٫٦٢ وهو ضعف الحدّ ٠٫٣٠ + عيّنة رقيقة) — لا لأيّ سببٍ يتعلّق بالتشطيب. وسيط الحوض = **٥٫٤م**.
**الحقيقة الوحيدة المقيسة عن الحوض:** نحو **٥٢٪ من الصفقات بيعت بأكثر من ٢٫٢× قيمة الأرض** (نسبة سعرٍ عالية = **فئة سعريّة أعلى**؛ استنتاجاً قد تكون أحدث أو أكبر أو أرقى تشطيباً — لكن هذا **غير مُقاس**، فقد ترفع السعرَ قطعةٌ أكبر أو أدوارٌ أكثر أو زاوية أو موقع، لا التشطيب حصراً).

على **شاشة النتيجة** يرى المستخدم العنوان «**التقييم السوقي: ٢٬٤٠٠٬٠٠٠**»، وتحته ٥٫٤م **أربع مرّات**: «السقف السوقي ٥٫٤م» · «بِيعت بيوتٌ في منطقتك بنحو ٥٫٤م» · «حوض المقارنات: **وسيط ٥٬٤٠٠٬٠٠٠**» · حدّ النطاق الأعلى. **الخطر المزدوج:**
1. **إرباك:** المستخدم يقرأ «الوسيط السوقيّ ٥٫٤م، لكنّهم يعطونني ٢٫٤م» → تناقض ظاهريّ.
2. **تجاوز منهجيّ (الأهمّ):** نصّنا الحاليّ يقول «كان فللاً **جديدة فاخرة**» — أي يجزم بتشطيبٍ لم نقِسه. يجب إصلاح هذا.

**اتجاهي المقترَح:** نصف **المقيس** لا **السبب المُستنتَج**: «بيعت بأسعارٍ أعلى بكثير من قيمة الأرض (**فئة سعريّة أعلى** — قد تكون أحدث/أكبر/أرقى)» بدل «فاخرة»؛ ونُبقي الرسالة المفيدة «هذه فئة أعلى، غالباً ليست فئة عقارك».

**أسئلتي:**
1. **الأهمّ:** ما **أصدق صياغة عربيّة** لوصف هذه الفئة الأعلى سعراً — بحيث (أ) لا تجزم بتشطيبٍ/عمرٍ لم نُعاينه، (ب) وتُبقي قوّة التوضيح للمستخدم «هذه فئة أعلى، ليست فئة عقارك»؟ أعطِ الجملة الجاهزة.
2. هل الإرباك (٥٫٤م بجوار عنوان ٢٫٤م) حقيقيّ ويستحقّ الإصلاح، أم المُلطِّفات الحاليّة كافية؟
3. سطر الأساس المجرّد «حوض المقارنات: وسيط ٥٫٤م» بجوار «التقييم السوقي ٢٫٤م» — كيف أؤهّله بصدق (مع مراعاة أنّ ٥٫٤م وسيطٌ لفئةٍ أعلى، والرقم الأدقّ لعقارك هو ٢٫٤م)؟
4. العنوان المقود-بالكلفة: أُبقيه «التقييم السوقي» (مع سطر توضيح) أم أُغيّره إلى «مرتكز التكلفة»؟ ما مخاطر كلٍّ؟
5. هل ٤ تكرارات لرقم ٥٫٤م كثيرة؟ أحذف بعضها؟ أيّها الأجدر بالبقاء؟

أعطِ توصية واحدة واضحة لكلّ سؤال + سببها بإيجاز.

---

## ⚙️ v2 (the DEEPER, MEASURED consult — the one actually sent)

The r9-v1 prompt (above) was never sent — the PO pushed further: «امريخ قريبة من الوعب، ولدينا أرض بالوعب ~7م — هل نفقد شيئاً؟ ادمج أسعار أرض مريخ + خذ الوسيط + أضف تكلفة الإهلاك — هل يحلّ؟». Measured on the live CSV + `/api/evaluate/details`:
- **Al-Waab land validated:** 55010236 = الوعب, 1,219 m², engine 7.1M ≈ PO's ~7M. ✓
- **Marikh vs Al-Waab are NOT the same market:** Al-Waab land 600-900 = 4,951/m² vs Marikh 3,212/m² (~54% pricier) → the engine is RIGHT to keep them separate (GIS-name discipline; pooling would over-value Marikh). We lose nothing by separating.
- **The PO's proposal = the current cost method:** «Marikh land median + depreciated cost» = the live 2.4M (land 1,851,260 + depreciated building 526,834). It does NOT solve it — it IS the source.
- **DRC is a structural FLOOR (the decisive live proof):** even `condition=excellent` (ordinary finish) only reaches **2.6M**; `excellent+luxury` reaches **3.0M**; `good`=2.44M; age input does not move it (E26). The ordinary depreciated building maxes ~0.74M, while the market pays ~1.4M for the building of a modern Marikh villa (~2× gap). The cost approach under-prices functional buildings in an appreciating land market (textbook RICS: comparison primary, cost weakest for established residential).
- **The market strata already hold the answer (measured, reliable):** Marikh villa → land-priced 2.25M · **modern (1.5-2.2×, n=11, reliable) 3.36M** · luxury (≥2.2×, n=15, reliable) 5.27M. A normal 17yr maintained villa ≈ the modern stratum **3.36M** — a reliable *market* number the engine already computes but does not lead with.

**Two paths put to Gemini:** **A (durable / B-2)** = when the subject's class is confirmed (condition input or GT), lead with the matching *market stratum* (3.36M) instead of the cost floor — a Gate-2 value-affecting change (guarded against teardown over-valuation by requiring the condition signal). **B (interim / value-invariant)** = stop headlining the bare floor on cost-led cases; show the honest strata *menu* the engine already has («فلل مثل حجمك: قديمة ~2.4م · حديثة ~3.4م · فاخرة ~5.3م — أين تقع فيلتك؟») — no single misleading number, no unmeasured-finish claim.

### The prompt sent to Gemini (v2, self-contained)

**استشارة منهجيّة — «قاع الكلفة» يُبخّس فيلا قائمة؛ أيّ مسار؟**

أنت مستشار خبير في التقييم العقاريّ (RICS/IVS) + UX. أجب بإيجاز، بتوصيةٍ واحدة واضحة لكلّ سؤال، وصياغةٍ عربيّةٍ جاهزة حين تقترح نصّاً.

**السياق:** «ثمّن» أداة تقييم سوقيّ آليّ (AVM) للفلل والأراضي في قطر. الأساس **المقارنة** (وسيط صفقات وزارة العدل)؛ والثانويّ **الكلفة (DRC)** = قيمة الأرض + البناء المُهلَك. الرقم المعروض واحدٌ فقط، يُختار حسب جودة الأدلّة؛ وحين يكون حوض المقارنة **غير موثوق إحصائيّاً** (عيّنة رقيقة + تشتّت عالٍ) تقود الكلفة.

**قيود صدق (غير قابلة للتفاوض):** المحرّك **أعمى عن التشطيب/العمر الفعليّ لكلّ صفقة** (بيانات العدل لا تحملها) → أيّ وصف كـ«فاخر» استنتاجٌ من نسبة السعر إلى الأرض، لا معاينة، ولا يُقدَّم كحقيقة. الكلفة **أرضيّة** لا تُطارد السوق صعوداً. كلّ رقم «تقديريّ، ليس تقييماً معتمداً». لا نُخفي رقماً بتضليل.

**المشكلة المقيسة (فيلا مريخ ٦١٣ م²، عمر ١٧ سنة، حالة غير معلومة):**
- المحرّك يقود بالكلفة = **٢٫٤م** (أرض ١٫٨٥م + بناء مُهلَك ٠٫٥٣م)، لأنّ حوض المقارنة غير موثوق (تشتّت ٠٫٦٢).
- **الكلفة أرضيّةٌ بنيويّاً:** حتى بحالة «ممتازة» (تشطيب عاديّ) لا يتجاوز ٢٫٦م؛ والبناء العاديّ المُهلَك يبلغ ٠٫٧م كحدّ أقصى، بينما **السوق يدفع ~١٫٤م لبناء فيلا حديثة مماثلة** (ضعف تقريباً). منهج الكلفة يُبخّس البناء القائم في سوقٍ ترتفع أرضه.
- **بيانات السوق تحمل الجواب (مقيسة، موثوقة):** فلل مريخ بحجمه → قديمة ٢٫٢٥م · **حديثة جيّدة (n=11 موثوق) ٣٫٣٦م** · فاخرة (n=15) ٥٫٢٧م. **فيلا ١٧-سنة عاديّة مُصانة ≈ الحديثة الجيّدة ٣٫٣٦م** — رقم سوقيّ موثوق يملكه المحرّك لكنّه لا يقوده به.
- **النتيجة:** المحرّك يُصدّر **القاع (٢٫٤م)** كعنوان، فيُبخّس فيلا عاديّة قيمتها المُدافَع عنها ~٣٫٤م. (ويُظهر ٥٫٤م — وسيط الحوض المشوّه — أربع مرّات، ما يُربك أيضاً.)

**مساران:**
- **A (دائم):** حين تُؤكَّد حالة العقار (مُدخَل المستخدم أو بيانات مُثبَتة)، يقود المحرّك **بالطبقة السوقيّة المطابِقة (٣٫٣٦م)** لا بقاع الكلفة. تغيير قيمة-متأثّر (Gate-2)، محميّ من مبالغة الفيلا المتهالكة باشتراط إشارة الحالة.
- **B (فوريّ، لا يغيّر أيّ رقم محسوب):** نتوقّف عن تصدير القاع كرقمٍ وحيد، ونعرض **قائمة الطبقات الصادقة** التي نملكها: «فلل مثل حجمك في منطقتك: قديمة ~٢٫٤م · حديثة ~٣٫٤م · فاخرة ~٥٫٣م — أين تقع فيلتك؟» — بلا رقمٍ مُضلّلٍ واحد، وبلا ادّعاء تشطيب.

**أسئلتي:**
1. أيّ مسار تبدأ به ولماذا؟ وهل «القائمة» (B، بلا عنوانٍ رقميٍّ واحد) سليمةٌ منهجيّاً ومقبولةٌ للمستخدم العاديّ، أم أنّ غياب رقمٍ وحيد يضرّ الثقة/الوضوح؟
2. للمسار A: هل قيادةُ الطبقة السوقيّة (٣٫٣٦م) بدل قاع الكلفة — عند تأكيد الحالة — سليمةٌ وفق RICS؟ وما الضمانة ضدّ مبالغة الفيلا المتهالكة؟
3. أصدق صياغة عربيّة لـ«القائمة/الطبقات» دون جزمٍ بتشطيبٍ لم نُعاينه (بدل «فاخرة»)؟
4. العنوان في الحالة المقودة-بالكلفة: «التقييم السوقي» (مع توضيح) أم «مرتكز التكلفة»؟
5. هل ثمّة مسارٌ ثالثٌ أغفلناه؟

أعطِ توصيةً واحدةً واضحةً لكلّ سؤال + سببها.

---

## Gemini's response (received 2026-07-02) — condensed
1. **Path:** build A (durable) but keep a MODIFIED B as the immediate UI — do NOT remove the single number (a bare menu «kills the AVM 5-second value prop → a price bulletin»). Show 2.4M reframed as a "baseline" + strata as an "upgrade path".
2. **A is RICS-sound & preferred** (market > cost when data exists; strata = weighted comparison). Guard: 2.4M stays the BLIND default; move to 3.36M only on an **active opt-in** attesting condition + a disclaimer «the number depends on the accuracy of the user's statement».
3. **Price-position labels (not specs):** الشريحة الأساسية (تتمركز حول قيمة الأرض) / الشريحة المتوسّطة (الأعلى تداولاً) / الشريحة العُليا (أعلى التسعير الموثّق).
4. **Keep «القيمة السوقية التقديرية»** (DRC is a math tool to REACH market value, not a parallel value) + a subline «مُحتسبة وفق الحدّ الأدنى المحافظ … لانعدام البيانات المؤكّدة حول الحالة».
5. **Path C — «النطاق التفاعليّ المقفل» (🔒):** «القيمة الأساسية ٢٫٤م 🔒 (قد تصل إلى ٣٫٤م إذا كان البناء محدثاً — أكّد لفتح التقييم الدقيق)». Closing Q: one-click claim vs a 3-question modal?

## CC adjudication (Rule #54) — ACCEPT with 2 corrections + 1 reality-check
- **ACCEPT:** Q1 keep-single-headline (corrects CC's Path-B over-reach of removing the number) · Q2 market-stratum-lead on active opt-in (matches E25/R7; the blind default stays the floor) · Q3 price-position labels (the honesty fix) · Q4 keep «القيمة السوقية» + honest subline.
- **🔴 CORRECT #1 (Q3):** «الأعلى تداولاً» for the middle stratum is **factually wrong** (luxury n=15 > modern n=11) → replace with a measured position only: «الشريحة المتوسّطة (مضاعف أرض ١٫٥–٢٫٢×)». Do not swap one unverified claim for another.
- **🔴 CORRECT #2 (Q5):** the 🔒 "unlock your higher value" framing is a **dark pattern that corrupts the condition signal** — dangling a higher number for an attestation makes users over-claim «modern» → biased condition data → over-valuation (the exact failure we avoid). The opt-in must be **neutral**: «أكّد حالة عقارك — قد يرتفع الرقم أو ينخفض».
- **⚙️ REALITY-CHECK:** Path C's «3.4M» is **not deliverable by the cost path** (measured cap: excellent-ordinary 2.6M, luxury 3.0M). 3.4M requires Path A (opt-in leads the market *stratum*). So **C = the UI for A**, sequenced after an honest-display sprint.
- **Bottom line:** a normal villa cannot be safely auto-raised without a condition signal; the safe blind move is the honest reframe. Plan: **Sprint 1 = honest display (value-invariant): 2.4M headline + conservative subline + strata menu (corrected labels) + kill «فاخرة»-as-fact.** **Sprint 2 = A/C neutral opt-in (Gate-2, needs sign-off + calibration; stratum lead is «indicative» at n=11).**

## CC's reply sent back to Gemini (2026-07-02)
شكراً — نتّفق على الجوهر (رقم رئيسيّ واحد · لا رفع إلا بإقرار إيجابيّ · تسميات الموقع السعريّ · إبقاء «القيمة السوقية التقديرية»). ثلاثة تصحيحات لازمة: **(١)** رفض تأطير «القفل لفتح قيمتك الأعلى» — يُفسد إشارة الحالة (المستخدم يدّعي «محدَث» ليفتح الأعلى → مبالغة)؛ الإقرار محايدٌ: «قد يرتفع أو ينخفض». **(٢)** «الأعلى تداولاً» غير دقيق (الفاخرة n=15 > المتوسّطة n=11) → «مضاعف أرض ١٫٥–٢٫٢×». **(٣)** C ليس مستقلّاً — قِسنا حيّاً أنّ مسار الكلفة يسقُف عند ٢٫٦م/٣٫٠م لا ٣٫٤م؛ فالوصول لـ٣٫٤م يتطلّب المسار A. **جواب سؤاله:** نافذة **٣ أسئلة محايدة** لا نقرة واحدة (النقرة تحيّز «نعم» وتُفسد الإشارة؛ الأسئلة الثلاث إقرارٌ قابل للدفاع RICS + تصلح للمعايرة): عمر تقريبيّ [نطاقات] · حالة عامّة (جيّدة/متوسّطة/تحتاج ترميماً) · مستوى تشطيب (عاديّ/راقٍ) + سطر «قد ترفع الرقم أو تخفضه، وهي إقرارٌ منك والتقدير يبقى غير معتمد». هذه الحقول موجودة في شاشة «التحسين» — المطلوب سطحُها محايداً + ربطُها بقيادة الطبقة (A).
