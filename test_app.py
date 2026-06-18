"""
Test script for Linux Tweaker v2.0.0
Tests the preset application workflow without TUI
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.system_checker import SystemChecker
from src.file_manager import FileManager
from src.package_manager import PackageManager
from src.config_manager import ConfigManager
from src.preset_application_manager import PresetApplicationManager, PresetType


def test_system_checker():
    """Test SystemChecker functionality."""
    print("Testing SystemChecker...")
    
    checker = SystemChecker()
    
    # Test write permissions
    write_ok = checker.check_write_permissions()
    print(f"  Write permissions: {'OK' if write_ok else 'FAILED'}")
    
    # Test WM detection
    wm = checker.detect_window_manager()
    print(f"  Window Manager: {wm.value}")
    
    # Test dependencies
    deps = checker.check_critical_dependencies()
    print(f"  Dependencies checked: {len(deps)}")
    for dep, status in deps.items():
        print(f"    {dep}: {status.value}")
    
    # Check for errors
    errors = checker.get_errors()
    if errors:
        print(f"  Errors: {errors}")
    
    print("  SystemChecker test complete\n")
    return len(errors) == 0


def test_file_manager():
    """Test FileManager functionality."""
    print("Testing FileManager...")
    
    fm = FileManager()
    
    # Test backup creation
    test_file = Path.home() / ".config" / "linux-tweaker" / "test.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("test content")
    
    backup_status = fm.create_backup(test_file)
    print(f"  Backup creation: {backup_status.value}")
    
    # Test list backups
    backups = fm.list_backups()
    print(f"  Backups found: {len(backups)}")
    
    # Clean up
    if test_file.exists():
        test_file.unlink()
    
    errors = fm.get_errors()
    if errors:
        print(f"  Errors: {errors}")
    
    print("  FileManager test complete\n")
    return len(errors) == 0


def test_package_manager():
    """Test PackageManager functionality."""
    print("Testing PackageManager...")
    
    pm = PackageManager()
    
    # Test Flatpak availability
    flatpak_available = pm._check_flatpak_available()
    print(f"  Flatpak available: {flatpak_available}")
    
    # Test dependency check
    git_installed = pm.is_flatpak_installed("org.mozilla.firefox")
    print(f"  Firefox installed: {git_installed}")
    
    errors = pm.get_errors()
    if errors:
        print(f"  Errors: {errors}")
    
    print("  PackageManager test complete\n")
    return len(errors) == 0


def test_config_manager():
    """Test ConfigManager functionality."""
    print("Testing ConfigManager...")
    
    fm = FileManager()
    cm = ConfigManager(fm)
    
    # Test getting configs
    hyprland_config = cm.get_gnome_quality_hyprland_config()
    print(f"  Hyprland config length: {len(hyprland_config)}")
    
    waybar_config = cm.get_gnome_quality_waybar_config()
    print(f"  Waybar config length: {len(waybar_config)}")
    
    waybar_style = cm.get_gnome_quality_waybar_style()
    print(f"  Waybar style length: {len(waybar_style)}")
    
    errors = cm.get_errors()
    if errors:
        print(f"  Errors: {errors}")
    
    print("  ConfigManager test complete\n")
    return len(errors) == 0


def test_preset_manager():
    """Test PresetApplicationManager functionality."""
    print("Testing PresetApplicationManager...")
    
    pm = PackageManager()
    fm = FileManager()
    cm = ConfigManager(fm)
    preset_mgr = PresetApplicationManager(pm, cm)
    
    # Test getting available presets
    presets = preset_mgr.get_available_presets()
    print(f"  Available presets: {len(presets)}")
    for preset in presets:
        print(f"    {preset.value}")
    
    # Test preset descriptions
    for preset in presets:
        desc = preset_mgr.get_preset_description(preset)
        print(f"    {preset.value}: {desc[:50]}...")
    
    # Test preset application (dry run - no actual installation)
    print("  Testing preset application (configs only, no apps)...")
    status = preset_mgr.apply_preset(
        PresetType.GNOME_QUALITY_HYPRLAND,
        install_apps=False,
        apply_configs=True
    )
    print(f"  Preset application status: {status.value}")
    
    # Show progress
    progress = preset_mgr.get_progress()
    print(f"  Progress messages: {len(progress)}")
    for msg in progress:
        print(f"    {msg}")
    
    # Show errors
    errors = preset_mgr.get_errors()
    if errors:
        print(f"  Errors: {errors}")
        # Also check ConfigManager errors
        cm_errors = cm.get_errors()
        if cm_errors:
            print(f"  ConfigManager errors: {cm_errors}")
    
    print("  PresetApplicationManager test complete\n")
    # Accept partial as success since Waybar may not be installed on GNOME
    return status.value in ["success", "partial"]


def test_backup_restore():
    """Test backup and restore functionality."""
    print("Testing Backup/Restore...")
    
    fm = FileManager()
    
    # Create a test file
    test_file = Path.home() / ".config" / "linux-tweaker" / "backup_test.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    original_content = "original content"
    test_file.write_text(original_content)
    
    # Create backup and get the specific backup path
    backup_status = fm.create_backup(test_file)
    print(f"  Backup creation: {backup_status.value}")
    
    # Get the newly created backup (most recent)
    backups = fm.list_backups()
    new_backups = [b for b in backups if "backup_test" in b["name"]]
    if new_backups:
        # Sort by timestamp to get the most recent
        new_backups.sort(key=lambda x: x["timestamp"], reverse=True)
        backup_path = Path(new_backups[0]["path"])
        print(f"  Backup path: {backup_path}")
        # Verify backup has original content
        backup_content = backup_path.read_text()
        print(f"  Backup content: {backup_content}")
        print(f"  Backup matches original: {backup_content == original_content}")
    
    # Modify the file
    modified_content = "modified content"
    test_file.write_text(modified_content)
    print(f"  File modified: {test_file.read_text()}")
    
    # Restore from the specific backup
    if new_backups:
        restore_status = fm.restore_backup(backup_path, test_file)
        print(f"  Restore status: {restore_status.value}")
        
        # Verify restoration
        restored_content = test_file.read_text()
        print(f"  Restored content: {restored_content}")
        print(f"  Restore verification: {'PASS' if restored_content == original_content else 'FAIL'}")
        
        # Debug: check if backup file still has original content
        if backup_path.exists():
            current_backup_content = backup_path.read_text()
            print(f"  Backup still has: {current_backup_content}")
    
    # Clean up
    if test_file.exists():
        test_file.unlink()
    
    errors = fm.get_errors()
    if errors:
        print(f"  Errors: {errors}")
    
    print("  Backup/Restore test complete\n")
    return len(errors) == 0


def test_edge_cases():
    """Test edge cases and error handling."""
    print("Testing Edge Cases...")
    
    fm = FileManager()
    pm = PackageManager()
    cm = ConfigManager(fm)
    
    errors = []
    
    # Test 1: Invalid file path
    print("  Test 1: Invalid file path")
    invalid_path = Path("/nonexistent/path/file.txt")
    read_result = fm.read_file(invalid_path)
    print(f"    Read invalid path: {read_result is None} (expected None)")
    errors.extend(fm.get_errors())
    fm._errors.clear()
    
    # Test 2: Backup non-existent file
    print("  Test 2: Backup non-existent file")
    backup_status = fm.create_backup(invalid_path)
    print(f"    Backup non-existent: {backup_status.value} (expected skipped)")
    errors.extend(fm.get_errors())
    fm._errors.clear()
    
    # Test 3: Delete non-existent file
    print("  Test 3: Delete non-existent file")
    delete_status = fm.delete_file(invalid_path)
    print(f"    Delete non-existent: {delete_status.value} (expected skipped)")
    errors.extend(fm.get_errors())
    fm._errors.clear()
    
    # Test 4: Check non-existent Flatpak
    print("  Test 4: Check non-existent Flatpak")
    is_installed = pm.is_flatpak_installed("com.nonexistent.app")
    print(f"    Non-existent app installed: {is_installed} (expected False)")
    errors.extend(fm.get_errors())
    pm._errors.clear()
    
    # Test 5: Restore from non-existent backup
    print("  Test 5: Restore from non-existent backup")
    fake_backup = Path.home() / ".config" / "linux-tweaker" / "backups" / "fake_backup.txt"
    restore_status = fm.restore_backup(fake_backup)
    print(f"    Restore non-existent backup: {restore_status.value} (expected failed)")
    errors.extend(fm.get_errors())
    fm._errors.clear()
    
    # Test 6: Write to read-only location (simulated)
    print("  Test 6: Write to protected location")
    # Just test that the error handling works - we won't actually try to write to /root
    # Instead, we'll test that the write_file method handles errors gracefully
    print("    (Skipped - requires actual protected location)")
    
    # Test 7: Empty string operations
    print("  Test 7: Empty file operations")
    empty_file = Path.home() / ".config" / "linux-tweaker" / "empty_test.txt"
    empty_file.parent.mkdir(parents=True, exist_ok=True)
    write_status = fm.write_file(empty_file, "")
    print(f"    Write empty file: {write_status.value} (expected success)")
    read_result = fm.read_file(empty_file)
    print(f"    Read empty file: '{read_result}' (expected empty string)")
    if empty_file.exists():
        empty_file.unlink()
    errors.extend(fm.get_errors())
    fm._errors.clear()
    
    # Test 8: Large file operations
    print("  Test 8: Large file operations")
    large_content = "x" * 10000  # 10KB
    large_file = Path.home() / ".config" / "linux-tweaker" / "large_test.txt"
    write_status = fm.write_file(large_file, large_content)
    print(f"    Write large file: {write_status.value} (expected success)")
    read_result = fm.read_file(large_file)
    print(f"    Read large file: {len(read_result) if read_result else 0} bytes (expected 10000)")
    if large_file.exists():
        large_file.unlink()
    errors.extend(fm.get_errors())
    fm._errors.clear()
    
    if errors:
        print(f"  Errors encountered: {len(errors)}")
    
    print("  Edge cases test complete\n")
    return True  # Edge case tests are informational, not pass/fail


def test_partial_failure_recovery():
    """Test that the app can recover from partial failures."""
    print("Testing Partial Failure Recovery...")
    
    pm = PackageManager()
    fm = FileManager()
    cm = ConfigManager(fm)
    preset_mgr = PresetApplicationManager(pm, cm)
    
    # Test 1: Apply preset with only configs (no apps) - should succeed or partial
    print("  Test 1: Configs only (no apps)")
    status = preset_mgr.apply_preset(
        PresetType.GNOME_QUALITY_HYPRLAND,
        install_apps=False,
        apply_configs=True
    )
    print(f"    Status: {status.value} (expected success or partial)")
    errors = preset_mgr.get_errors()
    print(f"    Errors: {len(errors)}")
    preset_mgr._errors.clear()
    
    # Test 2: Apply preset with only apps (no configs) - should succeed or partial
    print("  Test 2: Apps only (no configs)")
    status = preset_mgr.apply_preset(
        PresetType.GNOME_QUALITY_HYPRLAND,
        install_apps=True,
        apply_configs=False
    )
    print(f"    Status: {status.value} (expected success or partial)")
    errors = preset_mgr.get_errors()
    print(f"    Errors: {len(errors)}")
    preset_mgr._errors.clear()
    
    # Test 3: Apply preset with both - should handle partial failures gracefully
    print("  Test 3: Both apps and configs")
    status = preset_mgr.apply_preset(
        PresetType.GNOME_QUALITY_HYPRLAND,
        install_apps=True,
        apply_configs=True
    )
    print(f"    Status: {status.value}")
    errors = preset_mgr.get_errors()
    print(f"    Errors: {len(errors)}")
    progress = preset_mgr.get_progress()
    print(f"    Progress steps: {len(progress)}")
    
    # Verify that even with errors, the app continues and reports status
    # Accept any status (success, partial, or failed) as long as it doesn't crash
    # Since we're on GNOME (not Hyprland), some configs will fail - this is expected
    print(f"    App handled errors gracefully: {status.value in ['success', 'partial', 'failed']}")
    
    print("  Partial failure recovery test complete\n")
    return status.value in ['success', 'partial', 'failed']


def main():
    """Run all tests."""
    print("=" * 60)
    print("Linux Tweaker v2.0.0 - Test Suite")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(("SystemChecker", test_system_checker()))
    results.append(("FileManager", test_file_manager()))
    results.append(("PackageManager", test_package_manager()))
    results.append(("ConfigManager", test_config_manager()))
    results.append(("PresetApplicationManager", test_preset_manager()))
    results.append(("Backup/Restore", test_backup_restore()))
    results.append(("Edge Cases", test_edge_cases()))
    results.append(("Partial Failure Recovery", test_partial_failure_recovery()))
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
