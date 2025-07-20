# Script to add coins to all users
# Load environment variables from .env file
$envContent = Get-Content ".env" -ErrorAction SilentlyContinue
if ($envContent) {
    foreach ($line in $envContent) {
        if ($line -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

# Get backend URL from environment or use default
$backendUrl = $env:BACKEND_URL
if (-not $backendUrl) {
    # Try to construct from DOMAIN if available
    $domain = $env:DOMAIN
    if ($domain -and $domain -ne "localhost") {
        $backendUrl = "https://$domain/api"
    } else {
        $backendUrl = "http://localhost:5000/api"
    }
}

# Ensure the URL ends with /api
if (-not $backendUrl.EndsWith("/api")) {
    if ($backendUrl.EndsWith("/")) {
        $backendUrl += "api"
    } else {
        $backendUrl += "/api"
    }
}

Write-Host "Adding coins to all users using backend: $backendUrl"

try {
    # Call API to add coins to all users
    $response = Invoke-RestMethod -Uri "$backendUrl/admin/give-coins-to-all" -Method POST -ContentType "application/json"
    
    Write-Host "Successfully added coins to all users!"
    Write-Host "Server response: $($response | ConvertTo-Json)"
    
} catch {
    Write-Host "Error adding coins: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Error details: $responseBody"
    }
} 