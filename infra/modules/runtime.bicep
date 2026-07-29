param location string
param namePrefix string
param applicationSubnetId string
param applicationIdentityId string
param registryLoginServer string
param applicationImageTag string
param keyVaultName string
param postgresFullyQualifiedDomainName string
param postgresAdministratorLogin string
param logAnalyticsWorkspaceName string
param sitesStorageAccountName string
param sitesFileShareName string
param siteName string
param bootstrapMode bool
param tags object

var managedEnvironmentName = '${namePrefix}-apps'
var applicationName = '${namePrefix}-web'
var applicationImage = '${registryLoginServer}/rushd:${applicationImageTag}'
var sitesMountPath = '/home/frappe/frappe-bench/sites'
var runtimeScriptPath = '/home/frappe/frappe-bench/apps/consultation_center/docker'
var identity = {
  '${applicationIdentityId}': {}
}
var commonEnvironment = [
  {
    name: 'RUSHD_SITE_NAME'
    value: siteName
  }
  {
    name: 'DB_HOST'
    value: postgresFullyQualifiedDomainName
  }
  {
    name: 'DB_PORT'
    value: '5432'
  }
  {
    name: 'RUSHD_ASSET_VERSION'
    value: applicationImageTag
  }
]
var sitesVolumeMount = [
  {
    volumeName: 'sites'
    mountPath: sitesMountPath
  }
]
var bootstrapEnvironment = bootstrapMode ? [
  {
    name: 'DB_ROOT_USERNAME'
    value: postgresAdministratorLogin
  }
  {
    name: 'DB_ROOT_PASSWORD'
    secretRef: 'postgres-admin-password'
  }
  {
    name: 'SITE_ADMIN_PASSWORD'
    secretRef: 'site-admin-password'
  }
] : []

resource workspace 'Microsoft.OperationalInsights/workspaces@2025-02-01' existing = {
  name: logAnalyticsWorkspaceName
}

resource sitesStorageAccount 'Microsoft.Storage/storageAccounts@2025-01-01' existing = {
  name: sitesStorageAccountName
}

resource managedEnvironment 'Microsoft.App/managedEnvironments@2025-01-01' = {
  name: managedEnvironmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: workspace.properties.customerId
        sharedKey: workspace.listKeys().primarySharedKey
      }
    }
    vnetConfiguration: {
      infrastructureSubnetId: applicationSubnetId
      internal: false
    }
  }
}

resource sitesEnvironmentStorage 'Microsoft.App/managedEnvironments/storages@2025-01-01' = {
  parent: managedEnvironment
  name: 'frappe-sites'
  properties: {
    azureFile: {
      accountName: sitesStorageAccount.name
      accountKey: sitesStorageAccount.listKeys().keys[0].value
      shareName: sitesFileShareName
      accessMode: 'ReadWrite'
    }
  }
}

resource application 'Microsoft.App/containerApps@2025-01-01' = {
  name: applicationName
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: identity
  }
  properties: {
    managedEnvironmentId: managedEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        allowInsecure: false
        targetPort: 8080
        transport: 'auto'
      }
      registries: [
        {
          server: registryLoginServer
          identity: applicationIdentityId
        }
      ]
      secrets: [
        {
          name: 'postgres-admin-password'
          keyVaultUrl: 'https://${keyVaultName}${environment().suffixes.keyvaultDns}/secrets/postgres-admin-password'
          identity: applicationIdentityId
        }
        {
          name: 'site-admin-password'
          keyVaultUrl: 'https://${keyVaultName}${environment().suffixes.keyvaultDns}/secrets/site-admin-password'
          identity: applicationIdentityId
        }
      ]
    }
    template: {
      initContainers: [
        {
          name: 'configure'
          image: applicationImage
          command: [
            'bash'
            '${runtimeScriptPath}/configure-runtime.sh'
          ]
          env: commonEnvironment
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          volumeMounts: sitesVolumeMount
        }
      ]
      containers: [
        {
          name: 'frontend'
          image: applicationImage
          command: [
            '/usr/local/bin/nginx-entrypoint.sh'
          ]
          env: [
            {
              name: 'BACKEND'
              value: '127.0.0.1:8000'
            }
            {
              name: 'SOCKETIO'
              value: '127.0.0.1:9000'
            }
            {
              name: 'FRAPPE_SITE_NAME_HEADER'
              value: siteName
            }
            {
              name: 'UPSTREAM_REAL_IP_HEADER'
              value: 'X-Forwarded-For'
            }
            {
              name: 'UPSTREAM_REAL_IP_RECURSIVE'
              value: 'on'
            }
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          volumeMounts: sitesVolumeMount
        }
        {
          name: 'backend'
          image: applicationImage
          command: [
            'bash'
            '${runtimeScriptPath}/start-backend.sh'
          ]
          env: concat(commonEnvironment, bootstrapEnvironment)
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          volumeMounts: sitesVolumeMount
        }
        {
          name: 'websocket'
          image: applicationImage
          command: [
            'node'
            '/home/frappe/frappe-bench/apps/frappe/socketio.js'
          ]
          env: commonEnvironment
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          volumeMounts: sitesVolumeMount
        }
        {
          name: 'worker'
          image: applicationImage
          command: [
            'bench'
            'worker'
            '--queue'
            'short,default,long'
          ]
          env: commonEnvironment
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          volumeMounts: sitesVolumeMount
        }
        {
          name: 'scheduler'
          image: applicationImage
          command: [
            'bench'
            'schedule'
          ]
          env: commonEnvironment
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          volumeMounts: sitesVolumeMount
        }
        {
          name: 'redis-cache'
          image: 'redis:7.2-alpine'
          command: [
            'redis-server'
            '--save'
            ''
            '--appendonly'
            'no'
            '--port'
            '6379'
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
        {
          name: 'redis-queue'
          image: 'redis:7.2-alpine'
          command: [
            'redis-server'
            '--save'
            ''
            '--appendonly'
            'no'
            '--port'
            '6380'
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
      volumes: [
        {
          name: 'sites'
          storageName: sitesEnvironmentStorage.name
          storageType: 'AzureFile'
        }
      ]
    }
  }
}

output managedEnvironmentName string = managedEnvironment.name
output applicationName string = application.name
output applicationUrl string = 'https://${application.properties.configuration.ingress.fqdn}'
