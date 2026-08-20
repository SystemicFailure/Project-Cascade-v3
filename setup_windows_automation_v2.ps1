# Windows Setup for Project Cascade File Watcher Auto-Sync
# Run this in PowerShell as Administrator

Write-Host "=" * 60
Write-Host "PROJECT CASCADE - FILE WATCHER SETUP"
Write-Host "=" * 60

$cascadePackagePath = "C:\Users\Dr. Strangelove\cascade_app_package"

Write-Host "`n📋 SETUP CHECKLIST:"
Write-Host "`n1. Install Python watchdog library:"
Write-Host "   pip install watchdog --break-system-packages"

Write-Host "`n2. Create shortcut to start file watcher:"
Write-Host "   Location: $cascadePackagePath\Start_AutoSync.bat"

$batContent = @"
@echo off
echo Project Cascade - Auto-Sync File Watcher
echo =========================================
cd /d "$cascadePackagePath"
python3 file_watcher_auto_sync.py
pause
"@

$batPath = "$cascadePackagePath\Start_AutoSync.bat"
Set-Content -Path $batPath -Value $batContent
Write-Host "   ✅ Batch file created: $batPath"

Write-Host "`n3. Create Windows Task to run file watcher on startup:"

$trigger = New-ScheduledTaskTrigger -AtStartup
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c $batPath"
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "Cascade_FileWatcher_AutoSync" `
    -TaskPath "Project Cascade" `
    -Trigger $trigger `
    -Action $action `
    -Principal $principal `
    -Settings $settings `
    -Force

Write-Host "   ✅ Task created: Cascade_FileWatcher_AutoSync"

Write-Host "`n" + "=" * 60
Write-Host "SETUP COMPLETE!"
Write-Host "=" * 60

Write-Host "`n🚀 EVENT-DRIVEN SYNC WORKFLOW:"
Write-Host "   1. File created/modified in cascade_app_package"
Write-Host "   2. File watcher detects change (instantly)"
Write-Host "   3. Sync triggered: Windows → Google Drive"
Write-Host "   4. Sync triggered: Google Drive → GitHub"
Write-Host "   5. GitHub webhook triggers Streamlit redeploy"
Write-Host "   6. Live update in 1-2 minutes`n"

Write-Host "📝 NEXT STEPS:"
Write-Host "   1. Run: pip install watchdog --break-system-packages"
Write-Host "   2. Files placed in cascade_app_package will auto-sync"
Write-Host "   3. Or manually start: $batPath"
Write-Host "   4. Check Task Scheduler to verify task runs on startup`n"

Write-Host "✅ Ready for real-time auto-sync!`n"
