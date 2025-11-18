# PowerShell script to test the admin reset-images endpoint on Render
# Usage: .\test_reset_images_curl.ps1 -Username "CmSCMU" -Password "your_password"

param(
    [string]$Username = "CmSCMU",
    [string]$Password
)

if (-not $Password) {
    Write-Host "Usage: .\test_reset_images_curl.ps1 -Username 'CmSCMU' -Password 'your_password'" -ForegroundColor Red
    exit 1
}

$BaseUrl = "https://oxfordevents.onrender.com"
$CookieJar = [System.IO.Path]::GetTempFileName()

Write-Host "Step 1: Logging in to get session cookie..." -ForegroundColor Cyan

# Login and save cookies
$loginBody = @{
    username = $Username
    password = $Password
    next = "/admin/dashboard"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-WebRequest -Uri "$BaseUrl/admin/login" `
        -Method POST `
        -Body (@{
            username = $Username
            password = $Password
            next = "/admin/dashboard"
        }) `
        -ContentType "application/x-www-form-urlencoded" `
        -SessionVariable session `
        -MaximumRedirection 5 `
        -ErrorAction Stop

    Write-Host "Login successful!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Login failed" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host ""
Write-Host "Step 2: Calling reset-images endpoint..." -ForegroundColor Cyan

try {
    $resetResponse = Invoke-RestMethod -Uri "$BaseUrl/api/admin/reset-images" `
        -Method POST `
        -WebSession $session `
        -ContentType "application/json" `
        -ErrorAction Stop

    Write-Host "HTTP Status: 200" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Cyan
    $resetResponse | ConvertTo-Json -Depth 5

    Write-Host ""
    Write-Host "SUCCESS: Images reset successfully!" -ForegroundColor Green
    exit 0
} catch {
    Write-Host "ERROR: Reset failed" -ForegroundColor Red
    Write-Host "HTTP Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody" -ForegroundColor Red
    }
    exit 1
}

