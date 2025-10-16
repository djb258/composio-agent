# Composio Agent Gateway - Endpoint Testing Script (PowerShell)
# Tests all endpoints to verify deployment

param(
    [string]$BaseUrl = "https://composio-imo-creator-url.onrender.com",
    [switch]$Verbose
)

# Configuration
$ErrorActionPreference = "Continue"
$TestsPassed = 0
$TestsFailed = 0

# Print header
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Composio Agent Gateway - Endpoint Tests" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Testing service at: $BaseUrl"
Write-Host "Timestamp: $((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))"
Write-Host ""

# Function to print test result
function Print-Result {
    param(
        [string]$TestName,
        [string]$Status,
        [string]$Message = ""
    )

    if ($Status -eq "PASS") {
        Write-Host "✓ PASS" -ForegroundColor Green -NoNewline
        Write-Host " - $TestName"
        if ($Verbose -and $Message) {
            Write-Host "  $Message" -ForegroundColor Gray
        }
        $script:TestsPassed++
    } else {
        Write-Host "✗ FAIL" -ForegroundColor Red -NoNewline
        Write-Host " - $TestName"
        Write-Host "  $Message" -ForegroundColor Red
        $script:TestsFailed++
    }
}

# Test 1: Status Endpoint
Write-Host "Testing /status endpoint..." -ForegroundColor Yellow
try {
    $StatusResponse = Invoke-WebRequest -Uri "$BaseUrl/status" -Method Get -UseBasicParsing
    $StatusCode = $StatusResponse.StatusCode
    $StatusBody = $StatusResponse.Content

    if ($StatusCode -eq 200) {
        Print-Result -TestName "/status returns 200" -Status "PASS" -Message "Response: $StatusBody"
    } else {
        Print-Result -TestName "/status returns 200" -Status "FAIL" -Message "Expected 200, got $StatusCode"
    }

    # Test 2: Status Response Contains Required Fields
    if ($StatusBody -match '"status"') {
        Print-Result -TestName "/status contains 'status' field" -Status "PASS"
    } else {
        Print-Result -TestName "/status contains 'status' field" -Status "FAIL" -Message "Missing 'status' field"
    }

    if ($StatusBody -match '"service":"composio-agent"') {
        Print-Result -TestName "/status service is 'composio-agent'" -Status "PASS"
    } else {
        Print-Result -TestName "/status service is 'composio-agent'" -Status "FAIL" -Message "Service field incorrect or missing"
    }
} catch {
    Print-Result -TestName "/status endpoint" -Status "FAIL" -Message $_.Exception.Message
}

# Test 3: Schema Endpoint
Write-Host ""
Write-Host "Testing /schema endpoint..." -ForegroundColor Yellow
try {
    $SchemaResponse = Invoke-WebRequest -Uri "$BaseUrl/schema" -Method Get -UseBasicParsing
    $SchemaCode = $SchemaResponse.StatusCode
    $SchemaBody = $SchemaResponse.Content

    if ($SchemaCode -eq 200) {
        Print-Result -TestName "/schema returns 200" -Status "PASS" -Message "Response length: $($SchemaBody.Length) chars"
    } else {
        Print-Result -TestName "/schema returns 200" -Status "FAIL" -Message "Expected 200, got $SchemaCode"
    }

    # Test 4: Schema Contains Tools
    if ($SchemaBody -match '"tools"') {
        Print-Result -TestName "/schema contains 'tools' field" -Status "PASS"
    } else {
        Print-Result -TestName "/schema contains 'tools' field" -Status "FAIL" -Message "Missing 'tools' field"
    }

    # Test 5: Schema Contains Expected Tools
    if ($SchemaBody -match '"firebase_read"') {
        Print-Result -TestName "/schema contains 'firebase_read' tool" -Status "PASS"
    } else {
        Print-Result -TestName "/schema contains 'firebase_read' tool" -Status "FAIL" -Message "Missing firebase_read tool"
    }

    if ($SchemaBody -match '"firebase_write"') {
        Print-Result -TestName "/schema contains 'firebase_write' tool" -Status "PASS"
    } else {
        Print-Result -TestName "/schema contains 'firebase_write' tool" -Status "FAIL" -Message "Missing firebase_write tool"
    }
} catch {
    Print-Result -TestName "/schema endpoint" -Status "FAIL" -Message $_.Exception.Message
}

# Test 6: Invoke Endpoint (Validation Test - Missing Fields)
Write-Host ""
Write-Host "Testing /invoke endpoint validation..." -ForegroundColor Yellow
try {
    $InvokeBody = @{
        tool = "firebase_read"
        data = @{}
    } | ConvertTo-Json

    $InvokeResponse = Invoke-WebRequest -Uri "$BaseUrl/invoke" -Method Post -Body $InvokeBody -ContentType "application/json" -UseBasicParsing -ErrorAction SilentlyContinue
    $InvokeCode = $InvokeResponse.StatusCode
} catch {
    $InvokeCode = $_.Exception.Response.StatusCode.value__
    $InvokeResponseBody = $_.Exception.Response | ConvertFrom-Json
}

if ($InvokeCode -eq 400) {
    Print-Result -TestName "/invoke validates required fields" -Status "PASS" -Message "Correctly rejects invalid request"
} else {
    Print-Result -TestName "/invoke validates required fields" -Status "FAIL" -Message "Expected 400 for missing fields, got $InvokeCode"
}

# Test 7: Response Time Check
Write-Host ""
Write-Host "Testing response time..." -ForegroundColor Yellow
try {
    $StartTime = Get-Date
    Invoke-WebRequest -Uri "$BaseUrl/status" -Method Get -UseBasicParsing | Out-Null
    $EndTime = Get-Date
    $ResponseTime = ($EndTime - $StartTime).TotalMilliseconds

    if ($ResponseTime -lt 3000) {
        Print-Result -TestName "Response time < 3s" -Status "PASS" -Message "$([int]$ResponseTime)ms"
    } else {
        Print-Result -TestName "Response time < 3s" -Status "FAIL" -Message "$([int]$ResponseTime)ms (too slow)"
    }
} catch {
    Print-Result -TestName "Response time check" -Status "FAIL" -Message $_.Exception.Message
}

# Test 8: HTTPS Check
Write-Host ""
Write-Host "Testing HTTPS..." -ForegroundColor Yellow
if ($BaseUrl -like "https://*") {
    Print-Result -TestName "Service uses HTTPS" -Status "PASS"
} else {
    Print-Result -TestName "Service uses HTTPS" -Status "FAIL" -Message "URL should use HTTPS"
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Test Summary" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Passed: $TestsPassed" -ForegroundColor Green
Write-Host "Failed: $TestsFailed" -ForegroundColor Red
Write-Host "Total: $($TestsPassed + $TestsFailed)"
Write-Host ""

if ($TestsFailed -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Some tests failed" -ForegroundColor Red
    exit 1
}
