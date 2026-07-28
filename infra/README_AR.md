# بنية Azure لمنصة رُشد

هذه الملفات تنشئ الأساس الخاص ببيئة رُشد باستخدام Bicep. لا تحتوي على أسرار،
ولا تنفذ نشرًا تلقائيًا بمجرد وجودها في المستودع.

## ما تنشئه النسخة الحالية

- Resource Group مستقل لكل بيئة.
- Virtual Network بثلاث شبكات فرعية منفصلة:
  - تشغيل التطبيق.
  - PostgreSQL فقط.
  - Private Endpoints فقط.
- Azure Database for PostgreSQL Flexible Server 16 دون Public Access.
- Azure Storage خاص مع:
  - `private-files`.
  - `backup-exports`.
  - Versioning وحماية حذف لمدة 30 يومًا.
- Azure Key Vault يعمل بـRBAC ودون Public Access.
- سر `postgres-admin-password` محفوظ داخل Key Vault أثناء النشر.
- Azure Container Registry من فئة Premium ودون Public Access.
- Azure Container Apps Environment متصل بالشبكة الخاصة، ويشغّل نسخة واحدة
  متعددة الحاويات تضم:
  - Nginx للويب.
  - Frappe Web/API.
  - WebSocket.
  - Worker.
  - Scheduler.
  - Redis مستقل للـCache وآخر للـQueue داخل بيئة Staging.
- Azure Files خاصة لحفظ `sites` وملفات الموقع بين إصدارات الحاويات، مع
  Private Endpoint مستقل.
- User Assigned Managed Identity لتطبيق رُشد.
- صلاحيات محدودة للهوية:
  - قراءة أسرار Key Vault.
  - قراءة وكتابة Blob.
  - سحب صور Container Registry.
- Log Analytics وApplication Insights.
- Private DNS Zones وروابطها بالشبكة.
- Diagnostic Settings للخدمات الحساسة.

حالة Staging الحالية في 27 يوليو 2026:

- موقع Frappe الداخلي: `rushd-staging.internal`.
- الصورة: `rushd:0.1.0-6b0c4fea997f`.
- Frappe `16.20.0` وصورة ERPNext `v16.22.0`.
- الرابط المؤقت:
  `https://rushd-staging-web.mangocliff-2f187d1b.uaenorth.azurecontainerapps.io`.
- أسرار إنشاء الموقع غير معروضة لحاوية التطبيق في التشغيل المعتاد
  (`bootstrapMode=false`).
- ملفات `/assets` الثابتة تُقدّم من صورة التطبيق، ولا تُنسخ إلى Azure Files؛
  المشاركة مخصصة لبيانات `sites` الدائمة.
- نجحت اختبارات عزل سجلات المستفيد وولي الأمر والمستشار، ونجح اختبار
  `/api/method/ping` وصفحة `/login`.

Redis داخل Container App في Staging مؤقت وغير دائم، وهو ليس مصدر حقيقة.
قبل Production يجب اعتماد Azure Managed Redis أو خدمة مُدارة مكافئة.

## لماذا Container Registry من فئة Premium؟

Azure Container Registry لا يدعم Private Endpoint في الفئات الأدنى. لذلك
اختيرت Premium لتحقيق العزل الشبكي، لا بسبب سعة التطبيق. يجب مراجعة تكلفتها
ضمن `what-if` وAzure Pricing قبل النشر.

## الملفات

```text
infra/
├── main.bicep
├── environments/
│   └── staging.bicepparam
├── modules/
│   ├── identity.bicep
│   ├── monitoring.bicep
│   ├── network.bicep
│   ├── postgresql.bicep
│   ├── registry.bicep
│   ├── runtime.bicep
│   ├── security.bicep
│   ├── sites-storage.bicep
│   └── storage.bicep
└── scripts/
    ├── deploy.sh
    ├── validate.sh
    └── what-if.sh
```

## قرار المنطقة

القيمة الافتراضية المؤقتة لـStaging هي `uaenorth`. هذا ليس اعتمادًا تنظيميًا.
قبل النشر يجب:

1. التحقق من توفر PostgreSQL وPrivate Link وContainer Apps وRedis في المنطقة.
2. اعتماد موقع تخزين البيانات من مالك البيانات والجهة القانونية.
3. تغيير المنطقة عبر `RUSHD_AZURE_LOCATION`.

إذا كانت `saudiarabiaeast` متاحة للاشتراك ولكل الخدمات المطلوبة واعتمدتها
الجهة، يمكن استخدامها. لا يكفي ظهور اسم المنطقة؛ توفر المنتجات داخلها هو
المعيار.

## المتطلبات

- Azure CLI حديث.
- Bicep CLI من خلال `az bicep`.
- صلاحية إنشاء Resource Group والموارد.
- صلاحية إنشاء Role Assignments مثل Owner أو User Access Administrator مع
  Contributor.
- Subscription وTenant معتمدان.
- معرفة قيمة رصيد منحة Microsoft Azure وتاريخ انتهائه لوضع ميزانية وتنبيهات.

على macOS:

```bash
brew update
brew install azure-cli
az bicep install
```

## التسجيل واختيار الاشتراك

```bash
az login
az account list --output table
export RUSHD_AZURE_SUBSCRIPTION_ID='ضع-معرّف-الاشتراك-هنا'
az account set --subscription "$RUSHD_AZURE_SUBSCRIPTION_ID"
az account show --output table
```

لا تضع Subscription ID داخل Git إذا كان تصنيف الجهة يمنع ذلك.

## تسجيل مزودي الموارد

ينفذ مرة واحدة على الاشتراك بواسطة مخول:

```bash
for provider in \
  Microsoft.App \
  Microsoft.ContainerRegistry \
  Microsoft.DBforPostgreSQL \
  Microsoft.Insights \
  Microsoft.KeyVault \
  Microsoft.ManagedIdentity \
  Microsoft.Network \
  Microsoft.OperationalInsights \
  Microsoft.Storage
do
  az provider register --namespace "$provider"
done
```

## إدخال كلمة مرور PostgreSQL دون كتابتها في الملفات

في zsh:

```bash
read -s "RUSHD_POSTGRES_ADMIN_PASSWORD?PostgreSQL bootstrap password: "
export RUSHD_POSTGRES_ADMIN_PASSWORD
echo
```

يجب أن تكون قوية وفريدة. تستخدم لإنشاء الخادم أول مرة، ثم تحفظ في Key Vault
وتدار وفق سياسة تدوير الأسرار. لا تستخدمها مباشرة كحساب التطبيق الدائم.

## التحقق المحلي

```bash
cd infra
./scripts/validate.sh
```

هذا يبني القالب وملف معلمات Staging فقط، ولا يتصل بالاشتراك لإنشاء موارد.

## معاينة ما سيتغير

```bash
export RUSHD_AZURE_LOCATION='uaenorth'
cd infra
./scripts/what-if.sh
```

راجع في الناتج:

- اسم وRegion الـResource Group.
- عدم وجود Public Access لـPostgreSQL وStorage وKey Vault وRegistry.
- عناوين الشبكات وعدم تعارضها مع شبكات الجهة.
- SKU والتكلفة المتوقعة.
- عدم وجود حذف أو تعديل لمورد خارج Resource Group الخاص برُشد.

إذا كان الاشتراك ممولًا بمنحة Microsoft، لا يعني ذلك تجاهل التكلفة. يجب إنشاء
Budget وتنبيهات عند نسب مناسبة من الرصيد، ومراجعة تاريخ انتهاء المنحة قبل
اعتماد Production. لا تنشئ القوالب Budget تلقائيًا لأن قيمة الرصيد وجهة استلام
التنبيهات لم تعتمدا بعد.

## تقدير Staging الأولي

التقدير التالي مبني على أسعار التجزئة الرسمية لـAzure في `uaenorth` بتاريخ
27 يوليو 2026. لا يشمل خصم المنحة أو ضريبتها، ولا يعد فاتورة نهائية:

| المورد | الإعداد | التقدير الشهري بالدولار |
| --- | --- | ---: |
| PostgreSQL compute | `Standard_B1ms` × 730 ساعة | 14.60 |
| PostgreSQL storage | 32GB | 4.42 |
| Container Registry | Premium، قرابة 30 يومًا | 50.00 |
| Private Endpoints | 3 × 730 ساعة | 21.90 |
| **الإجمالي الثابت التقريبي** | قبل السجلات والعمليات | **90.92** |

تكلفة Log Analytics تعتمد على الاستخدام. سعر التجزئة الظاهر للإدخال
`3.29 USD/GB`، والقالب يضع سقفًا يوميًا قدره 1GB؛ هذا سقف حماية وليس استهلاكًا
متوقعًا. Storage transactions وKey Vault operations وPrivate Link data
processing تضاف حسب الاستخدام.

لا يشمل هذا التقدير Container Apps أو Azure Files الخاصة بالموقع. Redis
الحالي حاويتان داخل مخصصات Container Apps ولا يملك فاتورة خدمة Redis منفصلة.
يجب إضافة استهلاك Container Apps وAzure Files الفعلي إلى تنبيهات الميزانية،
ثم تقدير Redis المُدار قبل Production.

## النشر

لا ينفذ قبل مراجعة `what-if`. للحماية، السكربت يرفض النشر ما لم يوجد تأكيد
صريح:

```bash
export RUSHD_CONFIRM_DEPLOY='staging'
cd infra
./scripts/deploy.sh
```

هذا ينشئ موارد مدفوعة داخل اشتراك Azure المحدد.

## النشر الآلي من GitHub

ملف `.github/workflows/deploy-staging.yml` ينشر فرع `develop` تلقائيًا إلى
بيئة Staging. يعتمد الربط على OpenID Connect وهوية Azure مخصصة؛ لا تُحفظ كلمة
مرور Azure أو كلمات مرور قاعدة البيانات داخل GitHub.

كل عملية نشر:

1. تبني صورة غير قابلة للتبديل بوسم يحتوي SHA الخاص بالـCommit داخل ACR.
2. تنسخ آخر Revision وتحدّث صورة حاويات رُشد فقط.
3. تترك حاويات Redis والبيانات الدائمة وإعدادات الشبكة دون تغيير.
4. تنتظر حتى تصبح الـRevision الجديدة سليمة.
5. تختبر `/api/method/ping` وصفحة `/login`.

يبقى الوصول العام إلى ACR معطلًا، لكن الخاصية
`networkRuleBypassAllowedForTasks` مفعلة للسماح لخدمة ACR Tasks الموثوقة
بإكمال البناء داخل Azure. لا يفتح ذلك Registry لأجهزة الإنترنت أو GitHub
Runner نفسه.

متغيرات بيئة GitHub المطلوبة:

| المتغير | الغرض |
| --- | --- |
| `AZURE_CLIENT_ID` | Client ID لهوية نشر GitHub |
| `AZURE_TENANT_ID` | Tenant الخاص بالاشتراك |
| `AZURE_SUBSCRIPTION_ID` | اشتراك Azure المستهدف |
| `AZURE_RESOURCE_GROUP` | `rushd-staging-rg` |
| `AZURE_ACR_NAME` | اسم Azure Container Registry |
| `AZURE_ACR_TASK` | مهمة البناء ذات الهوية المدارة (`rushd-build`) |
| `AZURE_CONTAINER_APP` | اسم Container App |

يجب أن تقيد الـFederated Credential بالموضوع:

```text
repo:Muhmnsor@135395607/rushd-consulting-platform@1314692173:environment:staging
```

ويجب ألا تمنح هوية النشر صلاحيات على PostgreSQL أو Key Vault أو Storage.

## تشغيل موقع جديد لأول مرة

وضع التأسيس مغلق افتراضيًا. يفتح فقط لإنشاء موقع جديد، ثم يغلق في نشر تالٍ:

```bash
export RUSHD_BOOTSTRAP_MODE='true'
export RUSHD_APPLICATION_IMAGE_TAG='ضع-وسم-الصورة'
export RUSHD_SITE_ADMIN_PASSWORD='كلمة-قوية-من-مسار-أسرار-آمن'
```

بعد نجاح `docker/create-site.sh` واختبارات الموقع:

```bash
export RUSHD_BOOTSTRAP_MODE='false'
```

لا تكتب القيم السرية في ملفات Bicep أو أوامر محفوظة في Git.

## ما لا تفعله هذه الطبقة

- لا تنقل بيانات Supabase.
- لا تنشئ Production من معلمات Staging.
- لا تنشئ نطاقات `portal` و`staff` و`admin` أو WAF.
- لا تنشئ Redis مُدارًا.
- لا تنفذ اختبار استعادة PostgreSQL أو Azure Files تلقائيًا.
- لا تفتح قواعد Firewall مؤقتة لجهاز مطور.

## ملاحظة PostgreSQL

Frappe 16 يعرض تحذيرًا صريحًا بأن دعم PostgreSQL ما زال تجريبيًا. نجح إنشاء
الموقع والترحيل واختبارات رُشد الحالية على PostgreSQL 16، لكن هذا لا يلغي
المخاطرة. قبل Production يلزم:

- فترة تشغيل Staging واختبارات أوسع لكل مسارات العمل.
- اختبار نسخ احتياطي واستعادة فعلي.
- اختبار كل ترقية Frappe على نسخة منقحة من البيانات.
- قرار معماري موثق بالاستمرار على PostgreSQL أو الانتقال إلى MariaDB مُدارة
  ذاتيًا قبل الإطلاق.

## بوابة الأمان قبل Production

- Budget وتنبيهات تتناسب مع رصيد المنحة ومدتها.
- نطاقات وTLS وWAF وفصل `portal` و`staff` و`admin`.
- Redis مُدار وخطة لاستمرار قوائم المهام.
- اختبار Restore موثق لـPostgreSQL وAzure Files.
- مراقبة وتنبيهات وRunbook وRollback.
- مراجعة أمن وخصوصية وUAT واعتماد مالك المنتج.
