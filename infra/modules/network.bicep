@description('Azure region.')
param location string

@description('Resource name prefix.')
param namePrefix string

@description('Resource tags.')
param tags object

@description('Virtual network CIDR.')
param virtualNetworkAddressPrefix string = '10.42.0.0/16'

@description('Dedicated Container Apps infrastructure subnet CIDR.')
param applicationSubnetPrefix string = '10.42.0.0/23'

@description('Dedicated PostgreSQL Flexible Server subnet CIDR.')
param databaseSubnetPrefix string = '10.42.2.0/24'

@description('Private endpoints subnet CIDR.')
param privateEndpointSubnetPrefix string = '10.42.3.0/24'

var virtualNetworkName = '${namePrefix}-vnet'
var applicationSubnetName = 'snet-app'
var databaseSubnetName = 'snet-data-postgres'
var privateEndpointSubnetName = 'snet-private-endpoints'
var postgresPrivateDnsZoneName = '${namePrefix}.postgres.database.azure.com'

resource virtualNetwork 'Microsoft.Network/virtualNetworks@2025-05-01' = {
  name: virtualNetworkName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        virtualNetworkAddressPrefix
      ]
    }
    subnets: [
      {
        name: applicationSubnetName
        properties: {
          addressPrefix: applicationSubnetPrefix
          delegations: [
            {
              name: 'container-apps-delegation'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
          privateEndpointNetworkPolicies: 'Enabled'
        }
      }
      {
        name: databaseSubnetName
        properties: {
          addressPrefix: databaseSubnetPrefix
          delegations: [
            {
              name: 'postgres-flexible-server-delegation'
              properties: {
                serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers'
              }
            }
          ]
          privateEndpointNetworkPolicies: 'Enabled'
        }
      }
      {
        name: privateEndpointSubnetName
        properties: {
          addressPrefix: privateEndpointSubnetPrefix
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

resource postgresPrivateDnsZone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: postgresPrivateDnsZoneName
  location: 'global'
  tags: tags
  properties: {}
}

resource postgresDnsVirtualNetworkLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: postgresPrivateDnsZone
  name: '${namePrefix}-postgres-vnet-link'
  location: 'global'
  tags: tags
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetwork.id
    }
  }
}

output virtualNetworkId string = virtualNetwork.id
output virtualNetworkName string = virtualNetwork.name
output applicationSubnetId string = resourceId('Microsoft.Network/virtualNetworks/subnets', virtualNetwork.name, applicationSubnetName)
output databaseSubnetId string = resourceId('Microsoft.Network/virtualNetworks/subnets', virtualNetwork.name, databaseSubnetName)
output privateEndpointSubnetId string = resourceId('Microsoft.Network/virtualNetworks/subnets', virtualNetwork.name, privateEndpointSubnetName)
output postgresPrivateDnsZoneId string = postgresPrivateDnsZone.id
