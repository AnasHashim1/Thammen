# Sprint 1 — Operational Stability

## ما تم إنجازه

### 1. ✅ CORS مقيّد على thammen.qa
- `allow_origins=["*"]` → `["https://thammen.qa", "https://www.thammen.qa"]`
- HTTP methods محدّدة: GET, POST, OPTIONS فقط
- Headers محدّدة: Content-Type, Accept, Authorization

### 2. ✅ Rate Limiting
- 10 طلبات/دقيقة لكل IP على endpoints التقييم
- يمنع الـ abuse ويحمي APIs الحكومية من الإفراط
- خطأ 429 واضح إذا تم تجاوز الحد

### 3. ✅ Environment Variables
- ALLOWED_ORIGINS, RATE_LIMIT, LOG_LEVEL, MOJ_CSV_PATH, MOJ_DB_PATH
- تكوين النظام بدون تعديل الكود
- ملف `.env.example` للتوثيق

### 4. ✅ Logging محسّن
- استبدال `print()` بـ `logger.info/warning/error`
- مع stack traces للأخطاء (`exc_info=True`)
- format موحّد مع timestamps

### 5. ✅ In-Memory MoJ Cache
- CSV يُقرأ مرة واحدة عند أول طلب
- يُعاد استخدامه لكل الطلبات (توفير ~200ms/طلب)
- يكتشف تغيير الملف تلقائياً عبر mtime

## الملفات المُحدّثة

1. `api.py` — التحسينات الرئيسية
2. `evaluate_unified.py` — MoJ cache
3. `requirements.txt` — إضافة slowapi
4. `.env.example` — توثيق المتغيرات

## خطوات النشر

### 1. نسخ الملفات إلى `C:\Thammen\deploy v2`
- api.py
- evaluate_unified.py
- requirements.txt
- .env.example (اختياري — للتوثيق)

### 2. ضبط Environment Variables على Heroku

```
heroku config:set ALLOWED_ORIGINS="https://thammen.qa,https://www.thammen.qa" --app thammen-app-123
heroku config:set RATE_LIMIT="10/minute" --app thammen-app-123
heroku config:set LOG_LEVEL="INFO" --app thammen-app-123
```

### 3. التحقّق من الإعدادات

```
heroku config --app thammen-app-123
```

### 4. النشر

```
git add api.py evaluate_unified.py requirements.txt .env.example
git commit -m "Sprint 1: CORS, rate limit, env vars, logging, MoJ cache"
git push heroku master
```

## التحقّق بعد النشر

### Health Check
```
curl https://thammen-app-123-227a7106a67a.herokuapp.com/api/health
```

يجب أن ترى:
```json
{
  "version": "3.1.0-sprint1",
  "security": {
    "cors_locked": true,
    "rate_limit": "10/minute"
  }
}
```

### اختبار CORS
من متصفح موقع آخر (ليس thammen.qa)، يجب أن يفشل CORS.

### اختبار Rate Limit
أرسل 11 طلبات متتالية. الطلب الـ 11 يجب أن يُعيد 429.

## المهام المتبقية في Sprint 1

### 6. ⏳ Redis Caching (يحتاج تفعيل add-on)
```
heroku addons:create heroku-redis:mini --app thammen-app-123
```
ثم تحديث الكود لاستخدامه.

### 7. ⏳ تحميل GIS data عند الإقلاع
يحتاج refactor أكبر لـ qatar_gis.py.

## ملاحظات

- النسخة الحالية تعمل كاملة بدون Redis (in-memory cache كافٍ للبداية)
- استخدام Redis مهم عندما يكون عدد الـ dynos > 1 (لمشاركة الـ cache)
- حالياً dyno واحد، in-memory يكفي
