"""
FileManager - Handles file operations with backup functionality.

This module provides robust file management with zero-crash policy.
All operations are wrapped in try/except blocks to ensure graceful error handling.
"""

import os
import shutil
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Constants
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
BACKUP_DIR = Path.home() / ".config" / "linux-tweaker" / "backups"
# Secure file permissions
SECURE_FILE_MODE = 0o600  # rw-------
SECURE_DIR_MODE = 0o700  # rwx------


class BackupStatus(Enum):
    """Backup operation status."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class FileManager:
    """
    Manages file operations with automatic backup functionality.
    
    Features:
    - Automatic backup before modifications
    - Restore from backups
    - Safe file operations with error handling
    - User-space only (no sudo required)
    """
    
    def __init__(self, backup_dir: Optional[Path] = None):
        """
        Initialize FileManager.
        
        Args:
            backup_dir: Directory for storing backups. Defaults to ~/.config/linux-tweaker/backups
        """
        self.home_dir = Path.home()
        
        if backup_dir is None:
            self.backup_dir = self.home_dir / ".config" / "linux-tweaker" / "backups"
        else:
            self.backup_dir = Path(backup_dir)
        
        self._errors: List[str] = []
        self._backup_history: List[Dict[str, Any]] = []
        
        # Ensure backup directory exists
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self) -> bool:
        """
        Ensure backup directory exists.
        
        Returns:
            bool: True if directory exists or was created successfully.
        """
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            return True
        except (PermissionError, OSError) as e:
            self._errors.append(f"Failed to create backup directory: {e}")
            return False
        except Exception as e:
            self._errors.append(f"Unexpected error creating backup directory: {e}")
            return False
    
    def create_backup(self, file_path: Path) -> BackupStatus:
        """
        Create a backup of a file or directory.
        
        Args:
            file_path: Path to the file or directory to backup.
            
        Returns:
            BackupStatus: Status of the backup operation.
        """
        try:
            file_path = Path(file_path)
            
            # Check if file/directory exists
            if not file_path.exists():
                return BackupStatus.SKIPPED
            
            # Generate backup name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.name}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            # Create backup
            if file_path.is_file():
                shutil.copy2(file_path, backup_path)
            elif file_path.is_dir():
                shutil.copytree(file_path, backup_path)
            else:
                return BackupStatus.SKIPPED
            
            # Record backup in history
            self._backup_history.append({
                "original_path": str(file_path),
                "backup_path": str(backup_path),
                "timestamp": timestamp,
                "type": "file" if file_path.is_file() else "directory"
            })
            
            return BackupStatus.SUCCESS
            
        except (PermissionError, OSError, shutil.Error) as e:
            self._errors.append(f"Failed to backup {file_path}: {e}")
            return BackupStatus.FAILED
        except Exception as e:
            self._errors.append(f"Unexpected error backing up {file_path}: {e}")
            return BackupStatus.ERROR
    
    def restore_backup(self, backup_path: Path, target_path: Optional[Path] = None) -> BackupStatus:
        """
        Restore a file or directory from backup.
        
        Args:
            backup_path: Path to the backup file/directory.
            target_path: Target path to restore to. If None, uses original path from history.
            
        Returns:
            BackupStatus: Status of the restore operation.
        """
        try:
            backup_path = Path(backup_path)
            
            # Check if backup exists
            if not backup_path.exists():
                self._errors.append(f"Backup not found: {backup_path}")
                return BackupStatus.FAILED
            
            # Determine target path
            if target_path is None:
                # Try to find original path from history
                for entry in self._backup_history:
                    if entry["backup_path"] == str(backup_path):
                        target_path = Path(entry["original_path"])
                        break
                
                if target_path is None:
                    # Fallback: try to reconstruct original path
                    name_parts = backup_path.name.rsplit("_", 1)
                    if len(name_parts) == 2:
                        original_name = name_parts[0]
                    else:
                        original_name = backup_path.name
                    target_path = backup_path.parent.parent / original_name
            
            target_path = Path(target_path)
            
            # Restore backup (no backup of current state to avoid conflicts)
            if backup_path.is_file():
                # Remove target first to ensure clean restore
                if target_path.exists():
                    target_path.unlink()
                shutil.copy2(backup_path, target_path)
            elif backup_path.is_dir():
                # Remove existing directory if it exists
                if target_path.exists():
                    shutil.rmtree(target_path)
                shutil.copytree(backup_path, target_path)
            
            return BackupStatus.SUCCESS
            
        except (PermissionError, OSError, shutil.Error) as e:
            self._errors.append(f"Failed to restore {backup_path}: {e}")
            return BackupStatus.FAILED
        except Exception as e:
            self._errors.append(f"Unexpected error restoring {backup_path}: {e}")
            return BackupStatus.ERROR
    
    def write_file(self, file_path: Path, content: str, create_backup: bool = True) -> BackupStatus:
        """
        Write content to a file with optional backup.
        
        Args:
            file_path: Path to the file to write.
            content: Content to write.
            create_backup: Whether to create a backup before writing.
            
        Returns:
            BackupStatus: Status of the write operation.
        """
        try:
            file_path = Path(file_path)
            
            # Validate file size before writing
            content_size = len(content.encode('utf-8'))
            if content_size > MAX_FILE_SIZE:
                self._errors.append(f"Content too large: {content_size} bytes (max {MAX_FILE_SIZE})")
                return BackupStatus.FAILED
            
            # Create backup if requested and file exists
            if create_backup and file_path.exists():
                backup_status = self.create_backup(file_path)
                if backup_status == BackupStatus.FAILED:
                    return BackupStatus.FAILED
            
            # Ensure parent directory exists with secure permissions
            file_path.parent.mkdir(parents=True, exist_ok=True, mode=SECURE_DIR_MODE)
            
            # Write content with encoding error handling
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except UnicodeEncodeError as e:
                self._errors.append(f"Encoding error writing {file_path}: {e}")
                return BackupStatus.FAILED
            
            # Set secure file permissions
            try:
                file_path.chmod(SECURE_FILE_MODE)
            except (PermissionError, OSError) as e:
                self._errors.append(f"Failed to set secure permissions: {e}")
                # Continue anyway - file was written successfully
            
            return BackupStatus.SUCCESS
            
        except (PermissionError, OSError, IOError) as e:
            self._errors.append(f"Failed to write {file_path}: {e}")
            return BackupStatus.FAILED
        except Exception as e:
            self._errors.append(f"Unexpected error writing {file_path}: {e}")
            return BackupStatus.ERROR
    
    def read_file(self, file_path: Path) -> Optional[str]:
        """
        Read content from a file.
        
        Args:
            file_path: Path to the file to read.
            
        Returns:
            Optional[str]: File content, or None if read failed.
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                self._errors.append(f"File not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except (PermissionError, OSError, IOError) as e:
            self._errors.append(f"Failed to read {file_path}: {e}")
            return None
        except UnicodeDecodeError as e:
            self._errors.append(f"Encoding error reading {file_path}: {e}")
            return None
        except Exception as e:
            self._errors.append(f"Unexpected error reading {file_path}: {e}")
            return None
    
    def copy_file(self, src: Path, dst: Path, create_backup: bool = True) -> BackupStatus:
        """
        Copy a file from source to destination.
        
        Args:
            src: Source file path.
            dst: Destination file path.
            create_backup: Whether to create a backup of destination if it exists.
            
        Returns:
            BackupStatus: Status of the copy operation.
        """
        try:
            src = Path(src)
            dst = Path(dst)
            
            # Check if source exists
            if not src.exists():
                self._errors.append(f"Source file not found: {src}")
                return BackupStatus.FAILED
            
            # Create backup if destination exists
            if create_backup and dst.exists():
                backup_status = self.create_backup(dst)
                if backup_status == BackupStatus.FAILED:
                    return BackupStatus.FAILED
            
            # Ensure destination directory exists
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(src, dst)
            
            return BackupStatus.SUCCESS
            
        except (PermissionError, OSError, shutil.Error) as e:
            self._errors.append(f"Failed to copy {src} to {dst}: {e}")
            return BackupStatus.FAILED
        except Exception as e:
            self._errors.append(f"Unexpected error copying {src} to {dst}: {e}")
            return BackupStatus.ERROR
    
    def delete_file(self, file_path: Path, create_backup: bool = True) -> BackupStatus:
        """
        Delete a file or directory with optional backup.
        
        Args:
            file_path: Path to the file or directory to delete.
            create_backup: Whether to create a backup before deleting.
            
        Returns:
            BackupStatus: Status of the delete operation.
        """
        try:
            file_path = Path(file_path)
            
            # Check if file/directory exists
            if not file_path.exists():
                return BackupStatus.SKIPPED
            
            # Create backup if requested
            if create_backup:
                backup_status = self.create_backup(file_path)
                if backup_status == BackupStatus.FAILED:
                    return BackupStatus.FAILED
            
            # Delete file or directory
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            
            return BackupStatus.SUCCESS
            
        except (PermissionError, OSError, shutil.Error) as e:
            self._errors.append(f"Failed to delete {file_path}: {e}")
            return BackupStatus.FAILED
        except Exception as e:
            self._errors.append(f"Unexpected error deleting {file_path}: {e}")
            return BackupStatus.ERROR
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups.
        
        Returns:
            List[Dict[str, Any]]: List of backup information.
        """
        try:
            backups = []
            
            if not self.backup_dir.exists():
                return backups
            
            for item in self.backup_dir.iterdir():
                if item.is_file() or item.is_dir():
                    # Extract timestamp from filename
                    name_parts = item.name.rsplit("_", 1)
                    if len(name_parts) == 2:
                        original_name = name_parts[0]
                        timestamp = name_parts[1]
                    else:
                        original_name = item.name
                        timestamp = "unknown"
                    
                    backups.append({
                        "name": item.name,
                        "original_name": original_name,
                        "timestamp": timestamp,
                        "path": str(item),
                        "type": "file" if item.is_file() else "directory"
                    })
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return backups
            
        except Exception as e:
            self._errors.append(f"Failed to list backups: {e}")
            return []
    
    def get_errors(self) -> List[str]:
        """
        Get all errors encountered during operations.
        
        Returns:
            List[str]: List of error messages.
        """
        return self._errors.copy()
    
    def get_backup_history(self) -> List[Dict[str, Any]]:
        """
        Get the backup history.
        
        Returns:
            List[Dict[str, Any]]: List of backup history entries.
        """
        return self._backup_history.copy()
