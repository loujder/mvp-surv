# Script to add coins to all users
Write-Host "Adding coins to all users..."

try {
    # Call API to add coins to all users
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/admin/give-coins-to-all" -Method POST -ContentType "application/json"
    
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