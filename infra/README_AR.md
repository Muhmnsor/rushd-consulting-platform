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
- User Assigned Managed Identity لتطبيق رُشد.
- صلاحيات محدودة للهوية:
  - قراءة أسرار Key Vault.
  - قراءة وكتابة Blob.
  - سحب صور Container Registry.
- Log Analytics وApplication Insights.
- Private DNS Zones وروابطها بالشبكة.
- Diagnostic Settings للخدمات الحساسة.

لم تُضف Container Apps أو Redis بعد؛ تضاف في خطوة تشغيل التطبيق بعد اعتماد
الـRegion ونجاح `what-if` لهذه الطبقة.

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
│   ├── security.bicep
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

لا يشمل هذا التقدير Container Apps أو Redis لأنهما لم يضافا بعد. يجب إعادة
تقدير التكلفة قبل إضافتهما.

## النشر

لا ينفذ قبل مراجعة `what-if`. للحماية، السكربت يرفض النشر ما لم يوجد تأكيد
صريح:

```bash
export RUSHD_CONFIRM_DEPLOY='staging'
cd infra
./scripts/deploy.sh
```

هذا ينشئ موارد مدفوعة داخل اشتراك Azure المحدد.

## ما لا تفعله هذه الطبقة

- لا تنقل بيانات Supabase.
- لا تنشر تطبيق رُشد بعد.
- لا تنشئ مستخدم تطبيق PostgreSQL النهائي.
- لا تضع أسرارًا داخل Key Vault؛ الوصول العام للقبو مغلق، وتعبئة الأسرار ستتم
  من مسار خاص أو Pipeline معتمد، باستثناء كلمة مرور PostgreSQL الأولية التي
  ينشئها القالب مباشرة كسر `postgres-admin-password`.
- لا تفتح قواعد Firewall مؤقتة لجهاز مطور.
- لا تنشئ Production من معلمات Staging.

## بوابة الأمان قبل المرحلة التالية

لا نضيف Container Apps أو Redis حتى يتحقق الآتي:

- نجاح Build للقالب بلا أخطاء.
- اعتماد Subscription وRegion.
- مراجعة `what-if`.
- اعتماد نطاقات الشبكة.
- تأكيد ميزانية موارد Staging.
- نجاح نشر الأساس.
- إثبات DNS الخاص والوصول من داخل VNet.
- تسجيل نتيجة النشر في سجل التنفيذ.
