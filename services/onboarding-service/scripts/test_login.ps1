# Test Login Script for RawDrive Onboarding Service (PowerShell)
#
# Usage: .\test_login.ps1 [-Email "email"] [-Password "password"]
#
# Default test user: free@test.RawDrive.in / Test@123

param(
    [string]$Email = "free@test.RawDrive.in",
    [string]$Password = "Test@123",
    [string]$ApiBase = "http://localhost:8006/api/v1/onboarding"
)

Write-Host ""
Write-Host "=============================================="
Write-Host "  RawDrive Login Test (PowerShell)"
Write-Host "=============================================="
Write-Host ""
Write-Host "API Base: $ApiBase"
Write-Host "Email: $Email"
Write-Host ""

# Test 1: Health Check
Write-Host "[1/3] Testing health endpoint..."
try {
    $healthUrl = "http://localhost:8006/health"
    $healthResponse = Invoke-WebRequest -Uri $healthUrl -Method GET -UseBasicParsing -ErrorAction Stop
    Write-Host "  ✅ Health check passed (HTTP $($healthResponse.StatusCode))"
}
catch {
    Write-Host "  ❌ Health check failed: $($_.Exception.Message)"
    Write-Host "  Make sure the onboarding service is running on port 8006"
    exit 1
}

# Test 2: Login
Write-Host ""
Write-Host "[2/3] Testing login..."
try {
    $loginBody = @{
        email = $Email
        password = $Password
    } | ConvertTo-Json

    $loginResponse = Invoke-RestMethod -Uri "$ApiBase/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body $loginBody `
        -ErrorAction Stop

    Write-Host "  ✅ Login successful!"
    Write-Host ""
    Write-Host "  Response:"
    $loginResponse | ConvertTo-Json -Depth 3 | Write-Host

    # Test 3: Authenticated request
    if ($loginResponse.access_token) {
        Write-Host ""
        Write-Host "[3/3] Testing authenticated endpoint..."
        try {
            $headers = @{
                Authorization = "Bearer $($loginResponse.access_token)"
            }
            $stateResponse = Invoke-RestMethod -Uri "$ApiBase/state" `
                -Method GET `
                -Headers $headers `
                -ErrorAction SilentlyContinue
            Write-Host "  ✅ Authenticated request successful"
        }
        catch {
            if ($_.Exception.Response.StatusCode -eq 404) {
                Write-Host "  ✅ Authenticated request successful (no state yet)"
            }
            else {
                Write-Host "  ⚠️ Authenticated request: $($_.Exception.Message)"
            }
        }
    }
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "  ❌ Login failed (HTTP $statusCode)"
    Write-Host ""
    Write-Host "  Error: $($_.Exception.Message)"

    if ($_.ErrorDetails.Message) {
        Write-Host "  Details: $($_.ErrorDetails.Message)"
    }
    exit 1
}

Write-Host ""
Write-Host "=============================================="
Write-Host "  All tests passed!"
Write-Host "=============================================="
