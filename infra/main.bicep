param location string = resourceGroup().location
param containerAppName string = 'ca-orbit-campaign-nabi'
param environmentName string = 'cae-orbit-campaign-nabi'
param image string
param managedIdentityResourceId string = '/subscriptions/b40df2e4-08d5-4a67-8ef3-d4f393b599ee/resourcegroups/rg-orbit-campaign-nabi/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-orbit-campaign-nabi'
param managedIdentityClientId string
param storageAccountName string = 'stcampnabi'
param keyVaultName string = 'kv-orbit-camp-nabi'
param publicBaseUrl string = 'https://nabi.campaigns.wakaorbit.com'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-orbit-campaign-nabi'
  location: location
  properties: { retentionInDays: 30 }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-orbit-campaign-nabi'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityResourceId}': {}
    }
  }
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'api'
          image: image
          env: [
            { name: 'AZURE_CLIENT_ID', value: managedIdentityClientId }
            { name: 'CAMPAIGN_ID', value: '91b22035-842f-4290-8c31-9f0fa9f26de5' }
            { name: 'CAMPAIGN_SLUG', value: 'nabi' }
            { name: 'AZURE_RESOURCE_GROUP', value: resourceGroup().name }
            { name: 'STORAGE_ACCOUNT_NAME', value: storageAccountName }
            { name: 'STORAGE_TABLE_ENDPOINT', value: 'https://${storageAccountName}.table.core.windows.net' }
            { name: 'STORAGE_BLOB_ENDPOINT', value: 'https://${storageAccountName}.blob.core.windows.net' }
            { name: 'KEY_VAULT_NAME', value: keyVaultName }
            { name: 'PUBLIC_BASE_URL', value: publicBaseUrl }
            { name: 'SHARED_MAILBOX_ADDRESS', value: 'campaign-nabi@wakacomvoice.onmicrosoft.com' }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
          ]
          resources: { cpu: json('0.5'), memory: '1Gi' }
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
}

output fqdn string = app.properties.configuration.ingress.fqdn
