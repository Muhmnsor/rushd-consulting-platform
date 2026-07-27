### رُشد

منصة رُشد للاستشارات الشبابية.

هذا المستودع هو التطبيق المستقل المملوك لرُشد. يعتمد على Frappe Framework
كطبقة تشغيل، ولا يغيّر نواة Frappe.

المرجع التنفيذي للمشروع:

- [الدليل التنفيذي لمنصة رُشد](docs/IMPLEMENTATION_GUIDE_AR.md)
- [القرارات المعمارية](docs/adr)
- [بنية Azure وطريقة التحقق والنشر](infra/README_AR.md)

بيئة Staging الحالية:

`https://rushd-staging-web.mangocliff-2f187d1b.uaenorth.azurecontainerapps.io`

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app consultation_center
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/consultation_center
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
