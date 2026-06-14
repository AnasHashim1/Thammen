# DRAFT — a24 Privacy-Notice update for the report-copy memory (Track A operator-copy + Track B user-copy)

> **Status:** DRAFT — pending PO sign-off + a Qatari-counsel nod on the lawful basis. **NOT deployed.**
> Produced 2026-06-14 by the `a24-notice-report-copy-update` workflow (6 agents, 4 review lenses: PDPPL ·
> plain-Arabic clarity · internal-honesty · AR↔EN parity). Live state when drafted: b42.2 / Heroku v216;
> the operator report-copy is ACTIVE for all current traffic (config vars set), while the live a24 notice
> still says «لا يُخزَّن» — so this update is the governance gate for any REAL-user traffic.

## Why
The report-copy feature (b42) makes the live Terms §3/§6 claims FALSE: «الأداة لا تُخزّن أي بيانات … يُعالَج
آنياً ثم يُهمَل … لا نُخزّنه» / "stores nothing … processed in-memory and discarded … we do not store it."
We now KEEP a copy of every report (address + full JSON) in the operator's inbox + Resend. §3 + §6 (AR+EN)
must be rewritten truthfully; §1 must be softened (the auto-copy has no opt-out).

## 🔴 Two governance items that gate beta-wide (caught by the review, confirmed independently)
1. **Lawful basis — owner ≠ user → needs a Qatari-counsel eye.** PDPPL (Law 13/2016) defaults to the data
   subject's consent, but the property OWNER is frequently NOT the beta user clicking «أوافق» → neither
   consent nor a legitimate-interest balancing test cleanly covers a third party's address. The draft anchors
   on user-consent + an honest owner-interest acknowledgement (defensible + truthful), but the gap is a
   genuine legal question, not a copy question. **Confirm with counsel before beta-wide launch** (this is the
   same threshold as the a15 capture activation — RISK_REGISTER R11 / DPIA §9 review trigger).
2. **Ship gate — do NOT add the Track B (user-copy) bullet to the notice until Track B is actually built.**
   Verified in code: `report_mailer` routes only to `REPORT_COPY_EMAIL` (the operator); there is no user-email
   field in `index.html` and no user-recipient send path. Promising it now = the inverse falsehood. Build
   Track B first; then add its bullet.

## §3 «بياناتك في هذه النسخة» — REVISED (AR, 5 bullets; Latin/number tokens wrapped `<span dir="ltr">…</span>`)
1. نحتفظ الآن بنسخة من كل تقرير: عند كل تقييم تصل نسخة تلقائية إلى مُشغّل الأداة (أنس) وحده، عبر `Resend` (خدمة
   إرسال بريد). تتضمّن النسخة ملخّص التقرير، وعنوان العقار (المنطقة/الشارع/المبنى أو رقم القسيمة)، وملف النتيجة
   الكامل بصيغة `JSON` مُرفقاً.
2. الغرض محدّد: حفظ سجلّات المُشغّل وتحسين دقّة التقدير فقط. لا نبيع بياناتك ولا نستخدمها للتسويق، ولا نشاركها مع
   أي طرف ثالث؛ ويمرّ البريد عبر خدمة `Resend` فقط لإيصاله نيابةً عنّا.
3. يمكنك طلب الاطّلاع على بياناتك أو تصحيحها أو حذفها، أو الاعتراض على معالجتها، في أي وقت بالتواصل مع المُشغّل عبر
   واتساب `+974 70177761`.
4. أين تُحفظ ولِكم: في بريد المُشغّل خلال فترة البيتا (نحذفها عند انتهائها أو عند طلبك، أيّهما أسبق)، وفي سجلّات
   الإرسال لدى `Resend` وفق سياستها. الاستضافة والمعالجة تبقى خارج قطر (الولايات المتحدة/أوروبا، عبر `Heroku` و
   `Cloudflare`، و`Resend` للبريد).
5. أساس المعالجة هو موافقتك عند استخدامك للأداة وقبولك هذه الشروط؛ وإذا كان العقار يخصّ مالكاً آخر فأنت تُقرّ بأن
   لك صفة في الاستعلام عنه. يحمي القانون القطري لحماية خصوصية البيانات الشخصية (رقم `13` لسنة `2016`) عنوانك،
   ونحتفظ به فقط للغرضين أعلاه.

## §3 — REVISED (EN mirror, 5 bullets)
1. We now keep a copy of every report: each valuation automatically sends a copy to the tool's operator (Anas)
   alone, via `Resend` (an email-sending service). The copy contains a report summary, the property address
   (zone/street/building or plot number), and the full result file attached as `JSON`.
2. Purpose is limited: the operator's records and improving estimate accuracy only. We do not sell your data or
   use it for marketing, and we do not share it with any third party; email passes through `Resend` only to
   deliver it on our behalf.
3. You may request access, correction, deletion, or object to the processing of your data at any time by
   contacting the operator on WhatsApp `+974 70177761`.
4. Where it is kept and for how long: in the operator's mailbox for the duration of the beta (we delete it when
   the beta ends or on your request, whichever is sooner), and in `Resend`'s sending logs per its policy.
   Hosting and processing remain outside Qatar (US/EU, via `Heroku` and `Cloudflare`, and `Resend` for email).
5. The basis for processing is your consent when you use the tool and accept these Terms; if the property
   belongs to another owner, you confirm you have a legitimate interest in querying it. Qatar's Personal Data
   Privacy Protection Law (No. `13` of `2016`) protects your address, and we keep it only for the two purposes
   above.

## §6 «الأمان والإبلاغ» — REVISED
**AR:** نحتفظ في هذه النسخة بنسخة من كل تقرير (تشمل عنوان العقار وملف النتيجة الكامل) في بريد المُشغّل ولدى خدمة
`Resend`؛ لذا يشمل سطح الخطر هذه النسخ إضافةً إلى المعالجة المؤقتة وقناة ملاحظاتك. وفي حال وقوع حادث جوهري يمسّ
بياناتك، نلتزم بإبلاغك خلال `72` ساعة.

**EN:** In this beta we keep a copy of every report (including the property address and the full result file) in
the operator's mailbox and at the `Resend` service; the risk surface therefore covers these copies in addition
to transient processing and your feedback channel. If a material incident affecting your data occurs, we commit
to notifying you within `72` hours.

## §1 — softening (the auto-copy has no opt-out; the live «المشاركة اختيارية» now contradicts §3)
**AR:** استخدام الأداة اختياري؛ وعند استخدامها تُحفَظ نسخة من تقريرك كما هو موضّح في البند 3.
**EN:** Using the tool is optional; when you do, a copy of your report is retained as described in section 3.

## Also to update (not the Terms modal)
- **`docs/DPIA_AI_impact_beta_v1.md`** — now-inaccurate lines: §2 («NOT stored»), §4 («nothing stored»),
  §5 («address not stored … residual near-zero»; «nothing stored, so residency/SCC does not bite» → now we
  STORE cross-border via Resend), §8 («Retention: N/A (nothing stored)» → state the beta-duration retention).
- Code comments in index.html (412 / 802 / 854 / 3085) say «stores nothing» but describe the CLIENT-side gate/
  identity storage (still true) — NOT the report data; no change needed.

## Recommended sequence
1. Build **Track B** (result-screen «📧 أرسل نسخة إلى بريدي» → a rate-limited send endpoint reusing
   `report_mailer.build_email` with the user as recipient). Reversible, no deploy.
2. Merge the notice to cover BOTH copies (add the Track-B bullet) + apply §1 + update the DPIA.
3. PO sign-off on the copy (verbatim or edited).
4. 🔴 Qatari-counsel nod on the owner≠user lawful basis (the binding beta-wide gate).
5. Deploy beta-wide.

> Until then: the operator-copy is live for current traffic; with no invites sent, that is effectively the
> operator's own testing. The notice update + counsel are the gate before real invited users.
