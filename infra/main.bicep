targetScope = 'subscription'

metadata name = 'Rushd Azure foundation'
metadata description = 'Private staging/production foundation for the Rushd youth consultation platform.'

@description('Short workload name used in Azure resource names.')
@minLength(3)
@maxLength(12)
param workloadName string = 'rushd'

@description('Deployment environment.')
@allowed([
  'staging'
  'production'
])
param environment string

@description('Azure region approved for this environment.')
param location string

@description('PostgreSQL administrator login. This is a bootstrap account, not the application account.')
@minLength(3)
param postgresAdministratorLogin string = 'rushdpgadmin'

@description('PostgreSQL bootstrap administrator password. Supply it from RUSHD_POSTGRES_ADMIN_PASSWORD; never commit it.')
@secure()
@minLength(12)
param postgresAdministratorPassword string

@description('Initial Frappe Administrator password for the staging site. Supply it from RUSHD_SITE_ADMIN_PASSWORD; never commit it.')
@secure()
@minLength(12)
param siteAdministratorPassword string

@description('PostgreSQL compute SKU.')
param postgresSkuName string = 'Standard_B2s'

@description('PostgreSQL storage size in GiB.')
@minValue(32)
param postgresStorageSizeGB int = 64

@description('PostgreSQL point-in-time backup retention in days.')
@minValue(7)
@maxValue(35)
param postgresBackupRetentionDays int = 14

@description('Storage replication SKU. Staging defaults to LRS; production parameters must select the approved durability.')
@allowed([
  'Standard_LRS'
  'Standard_ZRS'
  'Standard_GRS'
  'Standard_GZRS'
])
param storageSkuName string = 'Standard_LRS'

@description('Maximum Log Analytics ingestion per day in GiB. Use -1 for no cap.')
param logAnalyticsDailyQuotaGb int = 1

@description('Immutable Rushd application image tag already present in Azure Container Registry.')
param applicationImageTag string

@description('Frappe site name used internally by the reverse proxy.')
param siteName string = 'rushd-staging.internal'

@description('Expose database bootstrap secrets only while creating the first site.')
param bootstrapMode bool = false

@description('Extra Azure resource tags.')
param additionalTags object = {}

var resourceGroupName = '${workloadName}-${environment}-rg'
var namePrefix = '${workloadName}-${environment}'
var uniqueSuffix = take(uniqueString(subscription().subscriptionId, resourceGroupName), 6)
var compactName = take(toLower(replace('${workloadName}${environment}${uniqueSuffix}', '-', '')), 20)
var commonTags = union({
  application: 'Rushd'
  workload: workloadName
  environment: environment
  managedBy: 'Bicep'
  dataClassification: 'Confidential'
}, additionalTags)

resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' = {
  name: resourceGroupName
  location: location
  tags: commonTags
}

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring-${environment}'
  scope: resourceGroup
  params: {
    location: location
    namePrefix: namePrefix
    dailyQuotaGb: logAnalyticsDailyQuotaGb
    tags: commonTags
  }
}

module network 'modules/network.bicep' = {
  name: 'network-${environment}'
  scope: resourceGroup
  params: {
    location: location
    namePrefix: namePrefix
    tags: commonTags
  }
}

module applicationIdentity 'modules/identity.bicep' = {
  name: 'identity-${environment}'
  scope: resourceGroup
  params: {
    location: location
    identityName: '${namePrefix}-app-identity'
    tags: commonTags
  }
}

module security 'modules/security.bicep' = {
  name: 'security-${environment}'
  scope: resourceGroup
  params: {
    location: location
    keyVaultName: take('kv-${compactName}', 24)
    privateEndpointSubnetId: network.outputs.privateEndpointSubnetId
    virtualNetworkId: network.outputs.virtualNetworkId
    applicationPrincipalId: applicationIdentity.outputs.principalId
    postgresAdministratorPassword: postgresAdministratorPassword
    siteAdministratorPassword: siteAdministratorPassword
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    tags: commonTags
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage-${environment}'
  scope: resourceGroup
  params: {
    location: location
    storageAccountName: take('st${compactName}', 24)
    storageSkuName: storageSkuName
    privateEndpointSubnetId: network.outputs.privateEndpointSubnetId
    virtualNetworkId: network.outputs.virtualNetworkId
    applicationPrincipalId: applicationIdentity.outputs.principalId
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    tags: commonTags
  }
}

module registry 'modules/registry.bicep' = {
  name: 'registry-${environment}'
  scope: resourceGroup
  params: {
    location: location
    registryName: take('cr${compactName}', 50)
    privateEndpointSubnetId: network.outputs.privateEndpointSubnetId
    virtualNetworkId: network.outputs.virtualNetworkId
    applicationPrincipalId: applicationIdentity.outputs.principalId
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    tags: commonTags
  }
}

module database 'modules/postgresql.bicep' = {
  name: 'postgresql-${environment}'
  scope: resourceGroup
  params: {
    location: location
    serverName: take('pg-${namePrefix}-${uniqueSuffix}', 63)
    delegatedSubnetId: network.outputs.databaseSubnetId
    privateDnsZoneId: network.outputs.postgresPrivateDnsZoneId
    administratorLogin: postgresAdministratorLogin
    administratorLoginPassword: postgresAdministratorPassword
    skuName: postgresSkuName
    storageSizeGB: postgresStorageSizeGB
    backupRetentionDays: postgresBackupRetentionDays
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    tags: commonTags
  }
}

module sitesStorage 'modules/sites-storage.bicep' = {
  name: 'sites-storage-${environment}'
  scope: resourceGroup
  params: {
    location: location
    storageAccountName: take('fs${compactName}', 24)
    privateEndpointSubnetId: network.outputs.privateEndpointSubnetId
    virtualNetworkId: network.outputs.virtualNetworkId
    tags: commonTags
  }
}

module runtime 'modules/runtime.bicep' = {
  name: 'runtime-${environment}'
  scope: resourceGroup
  params: {
    location: location
    namePrefix: namePrefix
    applicationSubnetId: network.outputs.applicationSubnetId
    applicationIdentityId: applicationIdentity.outputs.identityId
    registryLoginServer: registry.outputs.loginServer
    applicationImageTag: applicationImageTag
    keyVaultName: security.outputs.keyVaultName
    postgresFullyQualifiedDomainName: database.outputs.fullyQualifiedDomainName
    postgresAdministratorLogin: postgresAdministratorLogin
    logAnalyticsWorkspaceName: monitoring.outputs.logAnalyticsWorkspaceName
    sitesStorageAccountName: sitesStorage.outputs.storageAccountName
    sitesFileShareName: sitesStorage.outputs.fileShareName
    siteName: siteName
    bootstrapMode: bootstrapMode
    tags: commonTags
  }
}

output environmentName string = environment
output resourceGroupName string = resourceGroup.name
output virtualNetworkName string = network.outputs.virtualNetworkName
output applicationIdentityName string = applicationIdentity.outputs.identityName
output keyVaultName string = security.outputs.keyVaultName
output storageAccountName string = storage.outputs.storageAccountName
output containerRegistryName string = registry.outputs.registryName
output postgresServerName string = database.outputs.serverName
output postgresFullyQualifiedDomainName string = database.outputs.fullyQualifiedDomainName
output logAnalyticsWorkspaceName string = monitoring.outputs.logAnalyticsWorkspaceName
output applicationInsightsName string = monitoring.outputs.applicationInsightsName
output sitesStorageAccountName string = sitesStorage.outputs.storageAccountName
output containerAppsEnvironmentName string = runtime.outputs.managedEnvironmentName
output applicationName string = runtime.outputs.applicationName
output applicationUrl string = runtime.outputs.applicationUrl
