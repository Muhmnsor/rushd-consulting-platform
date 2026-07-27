param location string
param identityName string
param tags object

resource applicationIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: identityName
  location: location
  tags: tags
}

output identityId string = applicationIdentity.id
output identityName string = applicationIdentity.name
output clientId string = applicationIdentity.properties.clientId
output principalId string = applicationIdentity.properties.principalId
