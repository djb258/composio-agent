# Composio Agent Gateway - Post-Deploy Validation Script (PowerShell)
# Comprehensive validation including /invoke, latency, and service checks

param(
    [string]$BaseUrl = "https://composio-imo-creator-url.onrender.com",
    [string]$ServiceId = "srv-d3b7ikje5dus73cba2ng",
    [string]$RenderApiKey = ""
)

$ErrorActionPreference = "Continue"
$TotalTests = 0
$PassedTests = 0
$FailedTests = 0

# Print header
Write-Host "============================================" -ForegroundColor Blue
Write-Host "Composio Agent - Post-Deploy Validation" -ForegroundColor Blue
Write-Host "============================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Service URL: $BaseUrl"
Write-Host "Service ID: $ServiceId"
Write-Host "Timestamp: $((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))"
Write-Host ""

# Function to run test
function Run-Test {
    param(
        [string]$Name,
        [scriptblock]$Test
    )

    $script:TotalTests++
    Write-Host "[$script:TotalTests] $Name" -ForegroundColor Cyan

    try {
        $result = & $Test
        if ($result) {
            Write-Host "✓ PASS" -ForegroundColor Green
            Write-Host ""
            $script:PassedTests++
            return $true
        } else {
            Write-Host "✗ FAIL" -ForegroundColor Red
            Write-Host ""
            $script:FailedTests++
            return $false
        }
    } catch {
        Write-Host "✗ FAIL - $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        $script:FailedTests++
        return $false
    }
}

# Test 1: Health Check
Run-Test "Health Check (/status)" {
    $response = Invoke-RestMethod -Uri "$BaseUrl/status" -Method Get
    return ($response.status -eq "ok" -and $response.service -eq "composio-agent")
}

# Test 2: Schema Availability
Run-Test "Schema Availability (/schema)" {
    $response = Invoke-RestMethod -Uri "$BaseUrl/schema" -Method Get
    return ($response.tools.Count -gt 0)
}

# Test 3: Response Time - Status
Run-Test "Response Time - /status (< 2s)" {
    $start = Get-Date
    Invoke-WebRequest -Uri "$BaseUrl/status" -Method Get -UseBasicParsing | Out-Null
    $end = Get-Date
    $latency = ($end - $start).TotalMilliseconds
    Write-Host "  Latency: $([int]$latency)ms"
    return ($latency -lt 2000)
}

# Test 4: Response Time - Schema
Run-Test "Response Time - /schema (< 3s)" {
    $start = Get-Date
    Invoke-WebRequest -Uri "$BaseUrl/schema" -Method Get -UseBasicParsing | Out-Null
    $end = Get-Date
    $latency = ($end - $start).TotalMilliseconds
    Write-Host "  Latency: $([int]$latency)ms"
    return ($latency -lt 3000)
}

# Test 5: Invoke Validation - Missing agent_id
Run-Test "Invoke Validation - Missing agent_id" {
    $body = @{
        tool = "firebase_read"
        data = @{}
    } | ConvertTo-Json

    try {
        Invoke-RestMethod -Uri "$BaseUrl/invoke" -Method Post -Body $body -ContentType "application/json"
        return $false
    } catch {
        return ($_.Exception.Response.StatusCode.value__ -eq 400 -and $_.ErrorDetails.Message -match "agent_id")
    }
}

# Test 6: Invoke Validation - Missing process_id
Run-Test "Invoke Validation - Missing process_id" {
    $body = @{
        tool = "firebase_read"
        data = @{ agent_id = "test" }
    } | ConvertTo-Json

    try {
        Invoke-RestMethod -Uri "$BaseUrl/invoke" -Method Post -Body $body -ContentType "application/json"
        return $false
    } catch {
        return ($_.Exception.Response.StatusCode.value__ -eq 400 -and $_.ErrorDetails.Message -match "process_id")
    }
}

# Test 7: Invoke Validation - Missing blueprint_id
Run-Test "Invoke Validation - Missing blueprint_id" {
    $body = @{
        tool = "firebase_read"
        data = @{ agent_id = "test"; process_id = "test" }
    } | ConvertTo-Json

    try {
        Invoke-RestMethod -Uri "$BaseUrl/invoke" -Method Post -Body $body -ContentType "application/json"
        return $false
    } catch {
        return ($_.Exception.Response.StatusCode.value__ -eq 400 -and $_.ErrorDetails.Message -match "blueprint_id")
    }
}

# Test 8: Invoke Validation - Missing timestamp_last_touched
Run-Test "Invoke Validation - Missing timestamp_last_touched" {
    $body = @{
        tool = "firebase_read"
        data = @{ agent_id = "test"; process_id = "test"; blueprint_id = "test" }
    } | ConvertTo-Json

    try {
        Invoke-RestMethod -Uri "$BaseUrl/invoke" -Method Post -Body $body -ContentType "application/json"
        return $false
    } catch {
        return ($_.Exception.Response.StatusCode.value__ -eq 400 -and $_.ErrorDetails.Message -match "timestamp_last_touched")
    }
}

# Test 9: HTTPS Certificate
Run-Test "HTTPS Certificate Valid" {
    try {
        $response = Invoke-WebRequest -Uri "$BaseUrl/status" -Method Get -UseBasicParsing
        return ($response.StatusCode -eq 200)
    } catch {
        return $false
    }
}

# Test 10: No Error Pages
Run-Test "No Error Pages (404/500)" {
    $response = Invoke-WebRequest -Uri "$BaseUrl/status" -Method Get -UseBasicParsing
    return ($response.StatusCode -eq 200)
}

# Test 11: Tool Definitions Present
Run-Test "Tool Definitions Present" {
    $response = Invoke-RestMethod -Uri "$BaseUrl/schema" -Method Get
    $tools = $response.tools | Where-Object { $_.name -in @("firebase_read", "firebase_write", "send_email") }
    return ($tools.Count -ge 3)
}

# Test 12: Response Headers Check
Run-Test "Response Headers Valid" {
    $response = Invoke-WebRequest -Uri "$BaseUrl/status" -Method Get -UseBasicParsing
    return ($response.StatusCode -eq 200 -and $response.Headers["Content-Type"] -match "application/json")
}

# Test 13: Kill Switch Check
Run-Test "Kill Switch Status" {
    $response = Invoke-RestMethod -Uri "$BaseUrl/status" -Method Get
    return ($response.kill_switch -eq $false)
}

# Latency Analysis
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Latency Analysis (10 requests)" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

$latencies = @()
for ($i = 1; $i -le 10; $i++) {
    $start = Get-Date
    Invoke-WebRequest -Uri "$BaseUrl/status" -Method Get -UseBasicParsing | Out-Null
    $end = Get-Date
    $latency = [int]($end - $start).TotalMilliseconds
    $latencies += $latency
    Write-Host "Request $i: ${latency}ms"
}

$avgLatency = [int](($latencies | Measure-Object -Average).Average)
Write-Host ""
Write-Host "Average Latency: ${avgLatency}ms"
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Validation Summary" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Total Tests: $TotalTests"
Write-Host "Passed: $PassedTests" -ForegroundColor Green
Write-Host "Failed: $FailedTests" -ForegroundColor Red
Write-Host ""

if ($FailedTests -eq 0) {
    Write-Host "✓✓✓ All validations passed! Deployment successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Service is ready for production use." -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "✗✗✗ Some validations failed. Please review." -ForegroundColor Red
    Write-Host ""
    Write-Host "Recommended Actions:" -ForegroundColor Yellow
    Write-Host "1. Check Render Dashboard logs"
    Write-Host "2. Verify environment variables"
    Write-Host "3. Test endpoints manually"
    Write-Host "4. Review error messages above"
    exit 1
}
