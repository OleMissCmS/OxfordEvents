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

Write-Host "Step 1: Logging in to get session cookie..." -ForegroundColor Cyan

try {
    # First load the login page to get CSRF token
    $loginPage = Invoke-WebRequest `
        -Uri "$BaseUrl/admin/login" `
        -Method GET `
        -SessionVariable session `
        -ErrorAction Stop

    # Try multiple regex patterns to find CSRF token (attribute order may vary)
    $csrfPatterns = @(
        'name="csrf_token"[^>]*value="([^"]+)"',
        'value="([^"]+)"[^>]*name="csrf_token"',
        'csrf_token"[^>]*value="([^"]+)"'
    )
    
    $csrfToken = $null
    foreach ($pattern in $csrfPatterns) {
        $csrfMatch = [regex]::Match($loginPage.Content, $pattern)
        if ($csrfMatch.Success) {
            $csrfToken = $csrfMatch.Groups[1].Value
            break
        }
    }
    
    if (-not $csrfToken) {
        Write-Host "DEBUG: Login page content (first 2000 chars):" -ForegroundColor Yellow
        Write-Host $loginPage.Content.Substring(0, [Math]::Min(2000, $loginPage.Content.Length)) -ForegroundColor Yellow
        throw "Could not find CSRF token on login page."
    }

    # Extract next field (if present)
    $nextPattern = 'name="next"[^>]*value="([^"]*)"'
    $nextMatch = [regex]::Match($loginPage.Content, $nextPattern)
    $nextValue = "/admin/dashboard"
    if ($nextMatch.Success) {
        $nextValue = $nextMatch.Groups[1].Value
    }

    # Post login with CSRF token
    $headers = @{
        "Content-Type" = "application/x-www-form-urlencoded"
        "Referer" = "$BaseUrl/admin/login"
        "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PowerShellScript"
    }

    $loginResponse = Invoke-WebRequest -Uri "$BaseUrl/admin/login" `
        -WebSession $session `
        -Method POST `
        -Body (@{
            username = $Username
            password = $Password
            csrf_token = $csrfToken
            next = $nextValue
        }) `
        -Headers $headers `
        -MaximumRedirection 5 `
        -ErrorAction Stop

    Write-Host "Login successful!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Login failed" -ForegroundColor Red
    Write-Host $_.Exception.Message
    if ($_.Exception.Response) {
        Write-Host ("HTTP Status: {0}" -f $_.Exception.Response.StatusCode.value__) -ForegroundColor Yellow
        Write-Host ("Status Description: {0}" -f $_.Exception.Response.StatusDescription) -ForegroundColor Yellow
    }
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response body:" -ForegroundColor Yellow
        Write-Host $responseBody
    }
    exit 1
}

Write-Host ""
Write-Host "Step 2: Calling reset-images endpoint..." -ForegroundColor Cyan

try {
    $resetResponse = Invoke-RestMethod -Uri "$BaseUrl/api/admin/reset-images" `
        -Method POST `
        -WebSession $session `
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

