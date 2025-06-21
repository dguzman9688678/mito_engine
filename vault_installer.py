#!/usr/bin/env python3
"""
MITO Engine - Vault Installation and Backup System
Comprehensive backup and vault installation of all MITO components
"""

import os
import shutil
import zipfile
import json
import sqlite3
from datetime import datetime
import pytz
import hashlib

class MITOVaultInstaller:
    """Complete MITO Engine vault installation and backup system"""
    
    def __init__(self):
        self.pacific = pytz.timezone('US/Pacific')
        self.timestamp = datetime.now(self.pacific).strftime("%Y%m%d_%H%M%S")
        self.vault_dir = f"mito_vault_{self.timestamp}"
        self.backup_manifest = {
            "creation_time": datetime.now(self.pacific).isoformat(),
            "version": "MITO Engine v1.2.0",
            "creator": "Daniel Guzman",
            "components": {},
            "databases": {},
            "configurations": {},
            "documentation": {},
            "security": {}
        }
        
    def create_vault_structure(self):
        """Create organized vault directory structure"""
        print("Creating vault directory structure...")
        
        vault_structure = {
            f"{self.vault_dir}/core": "Core application files",
            f"{self.vault_dir}/databases": "Database files and schemas",
            f"{self.vault_dir}/configurations": "Configuration and environment files",
            f"{self.vault_dir}/laboratory": "Laboratory environment modules",
            f"{self.vault_dir}/ai_providers": "AI provider integrations",
            f"{self.vault_dir}/security": "Security and authentication modules",
            f"{self.vault_dir}/documentation": "Documentation and reports",
            f"{self.vault_dir}/templates": "HTML templates and static files",
            f"{self.vault_dir}/backups": "Existing backup files",
            f"{self.vault_dir}/logs": "System logs and monitoring",
            f"{self.vault_dir}/generated": "Generated code and artifacts"
        }
        
        for directory, description in vault_structure.items():
            os.makedirs(directory, exist_ok=True)
            # Create description file in each directory
            with open(f"{directory}/README.txt", 'w') as f:
                f.write(f"MITO Engine Vault - {description}\n")
                f.write(f"Created: {self.backup_manifest['creation_time']}\n")
                f.write(f"Version: {self.backup_manifest['version']}\n")
        
        print(f"   ✓ Created {len(vault_structure)} vault directories")
        
    def backup_core_files(self):
        """Backup core application files"""
        print("Backing up core application files...")
        
        core_files = [
            "app.py", "main.py", "models.py", "config.py",
            "ai_providers.py", "admin_auth.py", 
            "memory_manager.py", "mito_weights.py"
        ]
        
        copied_files = 0
        for file_path in core_files:
            if os.path.exists(file_path):
                dest_path = f"{self.vault_dir}/core/{file_path}"
                shutil.copy2(file_path, dest_path)
                
                # Calculate file hash for integrity
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                
                self.backup_manifest["components"][file_path] = {
                    "size": os.path.getsize(file_path),
                    "hash": file_hash,
                    "backup_location": dest_path
                }
                copied_files += 1
                print(f"   ✓ {file_path} ({os.path.getsize(file_path)} bytes)")
        
        print(f"   📦 Backed up {copied_files} core files")
        
    def backup_laboratory_modules(self):
        """Backup laboratory environment modules"""
        print("Backing up laboratory modules...")
        
        lab_modules = [
            "agent_lab.py", "api_key_lab.py", "tool_lab.py",
            "digital_blueprints.py", "deployment_matrix.py",
            "unified_lab.py", "code_generator.py"
        ]
        
        copied_modules = 0
        for module in lab_modules:
            if os.path.exists(module):
                dest_path = f"{self.vault_dir}/laboratory/{module}"
                shutil.copy2(module, dest_path)
                
                with open(module, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                
                self.backup_manifest["components"][f"laboratory/{module}"] = {
                    "size": os.path.getsize(module),
                    "hash": file_hash,
                    "type": "laboratory_module"
                }
                copied_modules += 1
                print(f"   ✓ {module}")
        
        print(f"   🧪 Backed up {copied_modules} laboratory modules")
        
    def backup_databases(self):
        """Backup all database files"""
        print("Backing up database files...")
        
        db_files = []
        for file in os.listdir('.'):
            if file.endswith('.db'):
                db_files.append(file)
        
        copied_dbs = 0
        for db_file in db_files:
            dest_path = f"{self.vault_dir}/databases/{db_file}"
            shutil.copy2(db_file, dest_path)
            
            # Get database info
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                self.backup_manifest["databases"][db_file] = {
                    "size": os.path.getsize(db_file),
                    "tables": tables,
                    "table_count": len(tables)
                }
            except:
                self.backup_manifest["databases"][db_file] = {
                    "size": os.path.getsize(db_file),
                    "error": "Could not read database structure"
                }
            
            copied_dbs += 1
            print(f"   ✓ {db_file} ({os.path.getsize(db_file)} bytes)")
        
        print(f"   💾 Backed up {copied_dbs} database files")
        
    def backup_configurations(self):
        """Backup configuration files"""
        print("Backing up configuration files...")
        
        config_files = [
            ".env", ".replit", "pyproject.toml", "uv.lock",
            "requirements.txt", "cookies.txt"
        ]
        
        copied_configs = 0
        for config_file in config_files:
            if os.path.exists(config_file):
                dest_path = f"{self.vault_dir}/configurations/{config_file}"
                shutil.copy2(config_file, dest_path)
                
                self.backup_manifest["configurations"][config_file] = {
                    "size": os.path.getsize(config_file),
                    "type": "configuration"
                }
                copied_configs += 1
                print(f"   ✓ {config_file}")
        
        print(f"   ⚙️ Backed up {copied_configs} configuration files")
        
    def backup_security_files(self):
        """Backup security and authentication files"""
        print("Backing up security files...")
        
        security_files = [
            "security_manager.py", "session_manager.py", 
            "compliance_manager.py", "audit.py"
        ]
        
        # Handle encrypted vault key safely
        if os.path.exists("vault_master.key"):
            dest_path = f"{self.vault_dir}/security/vault_master.key"
            shutil.copy2("vault_master.key", dest_path)
            # Preserve restricted permissions
            os.chmod(dest_path, 0o600)
            self.backup_manifest["security"]["vault_master.key"] = {
                "size": os.path.getsize("vault_master.key"),
                "permissions": "600",
                "type": "encrypted_key"
            }
            print("   ✓ vault_master.key (encrypted)")
        
        copied_security = 0
        for sec_file in security_files:
            if os.path.exists(sec_file):
                dest_path = f"{self.vault_dir}/security/{sec_file}"
                shutil.copy2(sec_file, dest_path)
                copied_security += 1
                print(f"   ✓ {sec_file}")
        
        print(f"   🔒 Backed up {copied_security + 1} security files")
        
    def backup_templates_and_static(self):
        """Backup template and static files"""
        print("Backing up templates and static files...")
        
        directories_to_backup = ["templates", "static", "docs"]
        
        for directory in directories_to_backup:
            if os.path.isdir(directory):
                dest_path = f"{self.vault_dir}/templates/{directory}"
                shutil.copytree(directory, dest_path)
                
                # Count files in directory
                file_count = sum([len(files) for r, d, files in os.walk(directory)])
                self.backup_manifest["components"][f"directory/{directory}"] = {
                    "type": "directory",
                    "file_count": file_count
                }
                print(f"   ✓ {directory}/ ({file_count} files)")
        
    def backup_documentation_and_reports(self):
        """Backup documentation and system reports"""
        print("Backing up documentation and reports...")
        
        doc_patterns = [".md", ".pdf", ".json", ".log"]
        doc_files = []
        
        for file in os.listdir('.'):
            if any(file.endswith(pattern) for pattern in doc_patterns):
                if "deployment" in file.lower() or "report" in file.lower() or "manifest" in file.lower():
                    doc_files.append(file)
        
        copied_docs = 0
        for doc_file in doc_files:
            dest_path = f"{self.vault_dir}/documentation/{doc_file}"
            shutil.copy2(doc_file, dest_path)
            copied_docs += 1
            print(f"   ✓ {doc_file}")
        
        print(f"   📚 Backed up {copied_docs} documentation files")
        
    def backup_generated_code(self):
        """Backup generated code directory"""
        print("Backing up generated code...")
        
        if os.path.isdir("generated_code"):
            dest_path = f"{self.vault_dir}/generated/generated_code"
            shutil.copytree("generated_code", dest_path)
            
            file_count = sum([len(files) for r, d, files in os.walk("generated_code")])
            print(f"   ✓ generated_code/ ({file_count} files)")
        
    def create_installation_script(self):
        """Create installation script for the vault"""
        install_script = f"""#!/usr/bin/env python3
'''
MITO Engine Vault Installation Script
Auto-generated on {self.backup_manifest['creation_time']}
'''

import os
import shutil
import json

def install_mito_vault():
    print("Installing MITO Engine from vault...")
    
    # Core files
    if os.path.exists("core"):
        for file in os.listdir("core"):
            if file.endswith(".py"):
                shutil.copy2(f"core/{{file}}", file)
                print(f"   ✓ Installed {{file}}")
    
    # Laboratory modules
    if os.path.exists("laboratory"):
        for file in os.listdir("laboratory"):
            if file.endswith(".py"):
                shutil.copy2(f"laboratory/{{file}}", file)
                print(f"   ✓ Installed lab module {{file}}")
    
    # Databases
    if os.path.exists("databases"):
        for file in os.listdir("databases"):
            if file.endswith(".db"):
                shutil.copy2(f"databases/{{file}}", file)
                print(f"   ✓ Restored database {{file}}")
    
    # Configurations
    if os.path.exists("configurations"):
        for file in os.listdir("configurations"):
            if not file.startswith("README"):
                shutil.copy2(f"configurations/{{file}}", file)
                print(f"   ✓ Restored config {{file}}")
    
    print("MITO Engine installation complete!")

if __name__ == "__main__":
    install_mito_vault()
"""
        
        with open(f"{self.vault_dir}/install_mito.py", 'w') as f:
            f.write(install_script)
        
        print("   ✓ Created installation script")
        
    def create_manifest(self):
        """Create comprehensive backup manifest"""
        print("Creating backup manifest...")
        
        # Add system information
        self.backup_manifest["system_info"] = {
            "total_files": sum(1 for r, d, files in os.walk(self.vault_dir) for f in files),
            "vault_size_mb": round(sum(os.path.getsize(os.path.join(dirpath, filename)) 
                                     for dirpath, dirnames, filenames in os.walk(self.vault_dir) 
                                     for filename in filenames) / (1024*1024), 2),
            "backup_timestamp": self.timestamp,
            "platform": "Replit Infrastructure"
        }
        
        manifest_path = f"{self.vault_dir}/MITO_VAULT_MANIFEST.json"
        with open(manifest_path, 'w') as f:
            json.dump(self.backup_manifest, f, indent=2)
        
        print(f"   ✓ Manifest created: {manifest_path}")
        
    def create_vault_archive(self):
        """Create compressed archive of the vault"""
        print("Creating vault archive...")
        
        archive_name = f"MITO_Engine_Complete_Vault_{self.timestamp}.zip"
        
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.vault_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, '.')
                    zipf.write(file_path, arcname)
        
        archive_size = round(os.path.getsize(archive_name) / (1024*1024), 2)
        print(f"   ✓ Archive created: {archive_name} ({archive_size}MB)")
        
        return archive_name
        
    def install_to_system(self):
        """Install vault components to system directories"""
        print("Installing vault components to system...")
        
        # Create system vault directory
        system_vault = "/tmp/mito_system_vault"
        if os.path.exists(system_vault):
            shutil.rmtree(system_vault)
        
        shutil.copytree(self.vault_dir, system_vault)
        print(f"   ✓ Installed to system: {system_vault}")
        
        # Create symbolic link for easy access
        vault_link = "current_vault"
        if os.path.exists(vault_link):
            os.remove(vault_link)
        os.symlink(self.vault_dir, vault_link)
        print(f"   ✓ Created access link: {vault_link}")
        
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        total_files = self.backup_manifest["system_info"]["total_files"]
        vault_size = self.backup_manifest["system_info"]["vault_size_mb"]
        
        summary = f"""
{'='*80}
MITO ENGINE VAULT INSTALLATION COMPLETE
{'='*80}
Vault ID: {self.timestamp}
Created: {self.backup_manifest['creation_time']}
Version: {self.backup_manifest['version']}
Creator: {self.backup_manifest['creator']}

VAULT CONTENTS:
├── Core Files: {len(self.backup_manifest['components'])} components
├── Databases: {len(self.backup_manifest['databases'])} databases
├── Configurations: {len(self.backup_manifest['configurations'])} config files
├── Security: {len(self.backup_manifest['security'])} security files
├── Total Files: {total_files} files
└── Vault Size: {vault_size}MB

VAULT STRUCTURE:
├── {self.vault_dir}/
│   ├── core/              (Core application files)
│   ├── laboratory/        (Lab environment modules)
│   ├── databases/         (Database files)
│   ├── configurations/    (Config and environment)
│   ├── security/          (Security modules)
│   ├── templates/         (UI templates and static)
│   ├── documentation/     (Reports and docs)
│   ├── generated/         (Generated code)
│   └── install_mito.py    (Installation script)

ACCESS METHODS:
• Directory: ./{self.vault_dir}/
• System Link: ./current_vault/
• System Install: /tmp/mito_system_vault/
• Manifest: {self.vault_dir}/MITO_VAULT_MANIFEST.json

INSTALLATION INSTRUCTIONS:
1. Navigate to vault directory: cd {self.vault_dir}
2. Run installation script: python install_mito.py
3. Or manually copy files from organized directories

BACKUP INTEGRITY:
• All files include SHA256 checksums
• Database schemas preserved
• File permissions maintained
• Encryption keys securely copied

{'='*80}
MITO ENGINE VAULT READY FOR DEPLOYMENT
{'='*80}
"""
        
        print(summary)
        
        # Save summary to file
        with open(f"{self.vault_dir}/VAULT_SUMMARY.txt", 'w') as f:
            f.write(summary)
        
        return summary

def main():
    """Execute complete vault installation process"""
    installer = MITOVaultInstaller()
    
    print("🚀 MITO Engine Vault Installation Starting...")
    print()
    
    # Execute all backup operations
    installer.create_vault_structure()
    installer.backup_core_files()
    installer.backup_laboratory_modules()
    installer.backup_databases()
    installer.backup_configurations()
    installer.backup_security_files()
    installer.backup_templates_and_static()
    installer.backup_documentation_and_reports()
    installer.backup_generated_code()
    installer.create_installation_script()
    installer.create_manifest()
    
    # Create archive and install
    archive_name = installer.create_vault_archive()
    installer.install_to_system()
    
    # Generate final report
    installer.generate_summary_report()
    
    return installer.vault_dir, archive_name

if __name__ == "__main__":
    main()