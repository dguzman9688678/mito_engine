#!/usr/bin/env python3
"""
Search Engine Package Manager
Comprehensive package management system for the search engine with dependency resolution,
version control, and automatic installation capabilities.
"""

import os
import sys
import json
import sqlite3
import subprocess
import requests
import hashlib
import zipfile
import tarfile
import shutil
import tempfile
import importlib
import pkg_resources
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
import logging
from urllib.parse import urlparse
import semver
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Package:
    """Represents a package with metadata"""
    name: str
    version: str
    description: str
    author: str
    license: str
    dependencies: List[str]
    install_path: str
    homepage: str = ""
    keywords: List[str] = None
    entry_points: Dict[str, str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.entry_points is None:
            self.entry_points = {}

@dataclass
class PackageSource:
    """Represents a package source/repository"""
    name: str
    url: str
    priority: int
    auth_token: str = ""
    trusted: bool = True

class PackageDatabase:
    """Database for package management"""
    
    def __init__(self, db_path: str = "package_manager.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize package database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Installed packages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS installed_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                version TEXT NOT NULL,
                description TEXT,
                author TEXT,
                license TEXT,
                install_path TEXT NOT NULL,
                installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                dependencies TEXT,
                checksum TEXT,
                auto_installed BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Package sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS package_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                auth_token TEXT,
                trusted BOOLEAN DEFAULT TRUE,
                last_updated TIMESTAMP,
                enabled BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Package cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS package_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                source TEXT NOT NULL,
                metadata TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, version, source)
            )
        """)
        
        # Installation history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS installation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                package_name TEXT NOT NULL,
                version TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN NOT NULL,
                error_message TEXT
            )
        """)
        
        # Default package sources
        cursor.execute("SELECT COUNT(*) FROM package_sources")
        if cursor.fetchone()[0] == 0:
            default_sources = [
                ("pypi", "https://pypi.org/simple/", 10, "", True),
                ("search-engine-plugins", "https://packages.searchengine.dev/", 5, "", True),
                ("github", "https://github.com/", 1, "", True)
            ]
            
            cursor.executemany("""
                INSERT INTO package_sources (name, url, priority, auth_token, trusted)
                VALUES (?, ?, ?, ?, ?)
            """, default_sources)
        
        conn.commit()
        conn.close()
        logger.info("Package database initialized")

class DependencyResolver:
    """Dependency resolution engine"""
    
    def __init__(self, db: PackageDatabase):
        self.db = db
        
    def resolve_dependencies(self, package_specs: List[str]) -> Tuple[List[str], List[str]]:
        """
        Resolve dependencies for given package specifications
        Returns: (install_order, conflicts)
        """
        resolved = {}
        conflicts = []
        
        for spec in package_specs:
            try:
                self._resolve_package(spec, resolved, conflicts, set())
            except Exception as e:
                conflicts.append(f"Error resolving {spec}: {e}")
                
        # Topological sort for installation order
        install_order = self._topological_sort(resolved)
        
        return install_order, conflicts
        
    def _resolve_package(self, spec: str, resolved: Dict[str, Package], 
                        conflicts: List[str], visiting: Set[str]):
        """Recursively resolve a single package and its dependencies"""
        name, version_spec = self._parse_package_spec(spec)
        
        if name in visiting:
            conflicts.append(f"Circular dependency detected: {name}")
            return
            
        if name in resolved:
            # Check version compatibility
            existing_version = resolved[name].version
            if not self._is_version_compatible(existing_version, version_spec):
                conflicts.append(f"Version conflict for {name}: {existing_version} vs {version_spec}")
            return
            
        visiting.add(name)
        
        # Find best version
        available_versions = self._get_available_versions(name)
        best_version = self._select_best_version(available_versions, version_spec)
        
        if not best_version:
            conflicts.append(f"No compatible version found for {name} {version_spec}")
            visiting.remove(name)
            return
            
        # Get package metadata
        package = self._get_package_metadata(name, best_version)
        if not package:
            conflicts.append(f"Failed to get metadata for {name} {best_version}")
            visiting.remove(name)
            return
            
        resolved[name] = package
        
        # Resolve dependencies
        for dep in package.dependencies:
            self._resolve_package(dep, resolved, conflicts, visiting)
            
        visiting.remove(name)
        
    def _parse_package_spec(self, spec: str) -> Tuple[str, str]:
        """Parse package specification like 'package>=1.0.0'"""
        operators = ['>=', '<=', '==', '>', '<', '~=']
        
        for op in operators:
            if op in spec:
                name, version = spec.split(op, 1)
                return name.strip(), f"{op}{version.strip()}"
                
        return spec.strip(), ""
        
    def _is_version_compatible(self, version: str, spec: str) -> bool:
        """Check if version satisfies specification"""
        if not spec:
            return True
            
        try:
            return semver.match(version, spec)
        except:
            # Fallback to string comparison
            if ">=" in spec:
                return version >= spec.replace(">=", "")
            elif "<=" in spec:
                return version <= spec.replace("<=", "")
            elif "==" in spec:
                return version == spec.replace("==", "")
            return True
            
    def _get_available_versions(self, package_name: str) -> List[str]:
        """Get available versions for a package"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT version FROM package_cache 
            WHERE name = ? ORDER BY version DESC
        """, (package_name,))
        
        versions = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not versions:
            # Try to fetch from remote sources
            versions = self._fetch_remote_versions(package_name)
            
        return versions
        
    def _fetch_remote_versions(self, package_name: str) -> List[str]:
        """Fetch available versions from remote sources"""
        # This would implement fetching from PyPI API, GitHub releases, etc.
        # For now, return a simple fallback
        return ["1.0.0"]
        
    def _select_best_version(self, versions: List[str], spec: str) -> Optional[str]:
        """Select the best version matching the specification"""
        if not versions:
            return None
            
        compatible = [v for v in versions if self._is_version_compatible(v, spec)]
        return compatible[0] if compatible else None
        
    def _get_package_metadata(self, name: str, version: str) -> Optional[Package]:
        """Get package metadata"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT metadata FROM package_cache 
            WHERE name = ? AND version = ?
        """, (name, version))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            metadata = json.loads(result[0])
            return Package(**metadata)
            
        return None
        
    def _topological_sort(self, packages: Dict[str, Package]) -> List[str]:
        """Topological sort for installation order"""
        in_degree = {name: 0 for name in packages}
        
        # Calculate in-degrees
        for package in packages.values():
            for dep_spec in package.dependencies:
                dep_name = self._parse_package_spec(dep_spec)[0]
                if dep_name in in_degree:
                    in_degree[dep_name] += 1
                    
        # Queue for packages with no dependencies
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # Reduce in-degree for dependents
            for dep_spec in packages[current].dependencies:
                dep_name = self._parse_package_spec(dep_spec)[0]
                if dep_name in in_degree:
                    in_degree[dep_name] -= 1
                    if in_degree[dep_name] == 0:
                        queue.append(dep_name)
                        
        return result

class PackageInstaller:
    """Package installation and management"""
    
    def __init__(self, db: PackageDatabase, install_root: str = "packages"):
        self.db = db
        self.install_root = Path(install_root)
        self.install_root.mkdir(exist_ok=True)
        self.resolver = DependencyResolver(db)
        
    def install_package(self, package_spec: str, force: bool = False) -> bool:
        """Install a package and its dependencies"""
        try:
            logger.info(f"Installing package: {package_spec}")
            
            # Resolve dependencies
            install_order, conflicts = self.resolver.resolve_dependencies([package_spec])
            
            if conflicts and not force:
                logger.error(f"Dependency conflicts found: {conflicts}")
                return False
                
            # Install packages in dependency order
            for package_name in install_order:
                if not self._install_single_package(package_name):
                    logger.error(f"Failed to install {package_name}")
                    return False
                    
            logger.info(f"Successfully installed {package_spec}")
            return True
            
        except Exception as e:
            logger.error(f"Installation failed: {e}")
            self._log_installation(package_spec, "install", False, str(e))
            return False
            
    def _install_single_package(self, package_name: str) -> bool:
        """Install a single package"""
        try:
            # Check if already installed
            if self._is_package_installed(package_name):
                logger.info(f"Package {package_name} already installed")
                return True
                
            # Download package
            package_path = self._download_package(package_name)
            if not package_path:
                return False
                
            # Extract and install
            install_path = self.install_root / package_name
            install_path.mkdir(exist_ok=True)
            
            if package_path.suffix == '.zip':
                with zipfile.ZipFile(package_path, 'r') as zip_file:
                    zip_file.extractall(install_path)
            elif package_path.suffix in ['.tar', '.gz']:
                with tarfile.open(package_path, 'r:*') as tar_file:
                    tar_file.extractall(install_path)
            else:
                # Copy single file
                shutil.copy2(package_path, install_path)
                
            # Register installation
            self._register_installation(package_name, install_path)
            
            # Run post-install scripts
            self._run_post_install_scripts(install_path)
            
            logger.info(f"Installed {package_name} to {install_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install {package_name}: {e}")
            return False
            
    def _is_package_installed(self, package_name: str) -> bool:
        """Check if package is already installed"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM installed_packages WHERE name = ?", (package_name,))
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
        
    def _download_package(self, package_name: str) -> Optional[Path]:
        """Download package from sources"""
        # This would implement downloading from various sources
        # For now, create a mock package
        temp_dir = Path(tempfile.mkdtemp())
        package_file = temp_dir / f"{package_name}.zip"
        
        # Create a simple package structure
        package_dir = temp_dir / package_name
        package_dir.mkdir()
        
        # Create package.json
        package_json = {
            "name": package_name,
            "version": "1.0.0",
            "description": f"Mock package for {package_name}",
            "main": "main.py",
            "dependencies": []
        }
        
        with open(package_dir / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
            
        # Create main.py
        with open(package_dir / "main.py", "w") as f:
            f.write(f"""#!/usr/bin/env python3
# {package_name} package
print("Hello from {package_name}!")
""")
        
        # Create zip file
        with zipfile.ZipFile(package_file, 'w') as zip_file:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    zip_file.write(file_path, file_path.relative_to(temp_dir))
                    
        return package_file
        
    def _register_installation(self, package_name: str, install_path: Path):
        """Register package installation in database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Read package metadata
        package_json_path = install_path / "package.json"
        if package_json_path.exists():
            with open(package_json_path) as f:
                metadata = json.load(f)
        else:
            metadata = {"name": package_name, "version": "1.0.0"}
            
        cursor.execute("""
            INSERT OR REPLACE INTO installed_packages 
            (name, version, description, author, license, install_path, dependencies, checksum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            package_name,
            metadata.get("version", "1.0.0"),
            metadata.get("description", ""),
            metadata.get("author", ""),
            metadata.get("license", ""),
            str(install_path),
            json.dumps(metadata.get("dependencies", [])),
            self._calculate_checksum(install_path)
        ))
        
        conn.commit()
        conn.close()
        
    def _calculate_checksum(self, path: Path) -> str:
        """Calculate checksum for installed package"""
        hasher = hashlib.sha256()
        
        for file_path in path.rglob('*'):
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
                    
        return hasher.hexdigest()
        
    def _run_post_install_scripts(self, install_path: Path):
        """Run post-installation scripts"""
        script_path = install_path / "post_install.py"
        if script_path.exists():
            try:
                subprocess.run([sys.executable, str(script_path)], 
                             cwd=install_path, check=True)
                logger.info(f"Executed post-install script for {install_path.name}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Post-install script failed: {e}")
                
    def _log_installation(self, package_name: str, action: str, success: bool, error: str = ""):
        """Log installation action"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO installation_history 
            (package_name, version, action, success, error_message)
            VALUES (?, ?, ?, ?, ?)
        """, (package_name, "unknown", action, success, error))
        
        conn.commit()
        conn.close()
        
    def uninstall_package(self, package_name: str, remove_deps: bool = False) -> bool:
        """Uninstall a package"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Get package info
            cursor.execute("""
                SELECT install_path, auto_installed FROM installed_packages 
                WHERE name = ?
            """, (package_name,))
            
            result = cursor.fetchone()
            if not result:
                logger.warning(f"Package {package_name} not found")
                return False
                
            install_path, auto_installed = result
            
            # Check for dependents
            cursor.execute("""
                SELECT name FROM installed_packages 
                WHERE dependencies LIKE ?
            """, (f'%{package_name}%',))
            
            dependents = [row[0] for row in cursor.fetchall()]
            
            if dependents and not remove_deps:
                logger.error(f"Cannot uninstall {package_name}. Required by: {dependents}")
                return False
                
            # Remove package files
            install_path_obj = Path(install_path)
            if install_path_obj.exists():
                shutil.rmtree(install_path_obj)
                
            # Remove from database
            cursor.execute("DELETE FROM installed_packages WHERE name = ?", (package_name,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Uninstalled {package_name}")
            self._log_installation(package_name, "uninstall", True)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to uninstall {package_name}: {e}")
            self._log_installation(package_name, "uninstall", False, str(e))
            return False
            
    def list_installed_packages(self) -> List[Dict]:
        """List all installed packages"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, version, description, install_path, installed_at 
            FROM installed_packages 
            ORDER BY name
        """)
        
        packages = []
        for row in cursor.fetchall():
            packages.append({
                "name": row[0],
                "version": row[1],
                "description": row[2],
                "install_path": row[3],
                "installed_at": row[4]
            })
            
        conn.close()
        return packages
        
    def update_package(self, package_name: str) -> bool:
        """Update a package to latest version"""
        try:
            # Get current version
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT version FROM installed_packages WHERE name = ?", (package_name,))
            result = cursor.fetchone()
            
            if not result:
                logger.error(f"Package {package_name} not installed")
                return False
                
            current_version = result[0]
            conn.close()
            
            # Check for newer version
            available_versions = self.resolver._get_available_versions(package_name)
            if not available_versions or available_versions[0] <= current_version:
                logger.info(f"Package {package_name} is already up to date")
                return True
                
            # Uninstall current version
            if not self.uninstall_package(package_name):
                return False
                
            # Install latest version
            return self.install_package(package_name)
            
        except Exception as e:
            logger.error(f"Failed to update {package_name}: {e}")
            return False

class PackageManager:
    """Main package manager interface"""
    
    def __init__(self, config_path: str = "package_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.db = PackageDatabase(self.config.get("database_path", "package_manager.db"))
        self.installer = PackageInstaller(self.db, self.config.get("install_root", "packages"))
        
    def _load_config(self) -> Dict:
        """Load package manager configuration"""
        default_config = {
            "database_path": "package_manager.db",
            "install_root": "packages",
            "sources": [
                {"name": "pypi", "url": "https://pypi.org/simple/", "priority": 10},
                {"name": "local", "url": "file://./local_packages", "priority": 5}
            ],
            "auto_update": False,
            "verify_signatures": True
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path) as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
                
        return default_config
        
    def install(self, package_spec: str, force: bool = False) -> bool:
        """Install a package"""
        return self.installer.install_package(package_spec, force)
        
    def uninstall(self, package_name: str, remove_deps: bool = False) -> bool:
        """Uninstall a package"""
        return self.installer.uninstall_package(package_name, remove_deps)
        
    def update(self, package_name: str = None) -> bool:
        """Update packages"""
        if package_name:
            return self.installer.update_package(package_name)
        else:
            # Update all packages
            packages = self.installer.list_installed_packages()
            success = True
            
            for pkg in packages:
                if not self.installer.update_package(pkg["name"]):
                    success = False
                    
            return success
            
    def list_packages(self, installed_only: bool = True) -> List[Dict]:
        """List packages"""
        if installed_only:
            return self.installer.list_installed_packages()
        else:
            # List available packages (would query remote sources)
            return []
            
    def search(self, query: str) -> List[Dict]:
        """Search for packages"""
        # This would implement searching across package sources
        return []
        
    def get_info(self, package_name: str) -> Optional[Dict]:
        """Get package information"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM installed_packages WHERE name = ?
        """, (package_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
            
        return None
        
    def verify_installation(self, package_name: str) -> bool:
        """Verify package installation integrity"""
        package_info = self.get_info(package_name)
        if not package_info:
            return False
            
        install_path = Path(package_info["install_path"])
        if not install_path.exists():
            return False
            
        # Verify checksum
        current_checksum = self.installer._calculate_checksum(install_path)
        stored_checksum = package_info["checksum"]
        
        return current_checksum == stored_checksum
        
    def cleanup(self) -> bool:
        """Clean up orphaned packages and cache"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Remove orphaned auto-installed packages
            cursor.execute("""
                DELETE FROM installed_packages 
                WHERE auto_installed = TRUE 
                AND name NOT IN (
                    SELECT DISTINCT json_extract(value, '$') 
                    FROM installed_packages, json_each(dependencies)
                    WHERE auto_installed = FALSE
                )
            """)
            
            orphaned_count = cursor.rowcount
            
            # Clean old cache entries
            cursor.execute("""
                DELETE FROM package_cache 
                WHERE cached_at < datetime('now', '-30 days')
            """)
            
            cache_cleaned = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleanup completed: {orphaned_count} orphaned packages, {cache_cleaned} cache entries removed")
            return True
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return False

def main():
    """CLI interface for package manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Search Engine Package Manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install a package')
    install_parser.add_argument('package', help='Package specification')
    install_parser.add_argument('--force', action='store_true', help='Force installation')
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall a package')
    uninstall_parser.add_argument('package', help='Package name')
    uninstall_parser.add_argument('--remove-deps', action='store_true', help='Remove dependencies')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update packages')
    update_parser.add_argument('package', nargs='?', help='Package name (all if not specified)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List packages')
    list_parser.add_argument('--all', action='store_true', help='List all available packages')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search packages')
    search_parser.add_argument('query', help='Search query')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show package information')
    info_parser.add_argument('package', help='Package name')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify package installation')
    verify_parser.add_argument('package', help='Package name')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up orphaned packages')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    pm = PackageManager()
    
    if args.command == 'install':
        success = pm.install(args.package, args.force)
        sys.exit(0 if success else 1)
        
    elif args.command == 'uninstall':
        success = pm.uninstall(args.package, args.remove_deps)
        sys.exit(0 if success else 1)
        
    elif args.command == 'update':
        success = pm.update(args.package)
        sys.exit(0 if success else 1)
        
    elif args.command == 'list':
        packages = pm.list_packages(not args.all)
        for pkg in packages:
            print(f"{pkg['name']} {pkg.get('version', 'unknown')} - {pkg.get('description', '')}")
            
    elif args.command == 'search':
        results = pm.search(args.query)
        for pkg in results:
            print(f"{pkg['name']} {pkg.get('version', 'unknown')} - {pkg.get('description', '')}")
            
    elif args.command == 'info':
        info = pm.get_info(args.package)
        if info:
            for key, value in info.items():
                print(f"{key}: {value}")
        else:
            print(f"Package {args.package} not found")
            sys.exit(1)
            
    elif args.command == 'verify':
        valid = pm.verify_installation(args.package)
        if valid:
            print(f"Package {args.package} is valid")
        else:
            print(f"Package {args.package} verification failed")
            sys.exit(1)
            
    elif args.command == 'cleanup':
        success = pm.cleanup()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()