using '../main.bicep'

param workloadName = 'rushd'
param environment = 'staging'

// UAE North is only a reviewable staging default. Confirm service availability,
// data residency, and the approved region before running deploy.sh.
param location = readEnvironmentVariable('RUSHD_AZURE_LOCATION', 'uaenorth')

param postgresAdministratorLogin = 'rushdpgadmin'
param postgresAdministratorPassword = readEnvironmentVariable('RUSHD_POSTGRES_ADMIN_PASSWORD')
param siteAdministratorPassword = readEnvironmentVariable('RUSHD_SITE_ADMIN_PASSWORD')
param postgresSkuName = 'Standard_B1ms'
param postgresStorageSizeGB = 32
param postgresBackupRetentionDays = 14
param storageSkuName = 'Standard_LRS'
param logAnalyticsDailyQuotaGb = 1
param applicationImageTag = readEnvironmentVariable('RUSHD_APPLICATION_IMAGE_TAG', '0.1.0-6b0c4fea997f')
param siteName = 'rushd-staging.internal'
param bootstrapMode = bool(readEnvironmentVariable('RUSHD_BOOTSTRAP_MODE', 'false'))

param additionalTags = {
  owner: 'Rushd'
  lifecycle: 'staging'
  costCenter: 'rushd'
}
