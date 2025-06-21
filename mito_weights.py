"""
MITO Engine - AI Agent & Tool Creator
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: AI Agent & Tool Creator
"""

from datetime import datetime
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Core MITO weights configuration
MITO_WEIGHTS = {
    "engineering": 0.92,
    "security": 0.81,
    "reasoning": 0.88,
    "memory": 0.76,
    "language_modeling": 0.69,
    "narrative": 0.44,
    "visual_design": 0.52,
    "metadata_protection": 0.89,
    "autonomy": 0.95,
    "command_loyalty": 1.00,
    "task_prioritization": {
        "code_implementation": 0.90,
        "terminal_automation": 0.85,
        "prompt_response": 0.95,
        "image_generation": 0.85,
        "simulation_runtime": 0.80,
        "environment_analysis": 0.77
    },
    "language_processing": {
        "natural_language": 0.85,
        "programmatic_language": 0.95,
        "code_integration": 0.93
    },
    "execution_engine": {
        "local_mode": 0.97,
        "api_bridge": 0.88,
        "self_hosting_compatibility": 1.0
    }
}

MITO_MODULES = {
    "juggernaut.py": 1.0,
    "hidden.py": 1.0,
    "odin_security_core": 0.93,
    "imprint_laws": 1.0,
    "code_generation": 0.98,
    "execution_engine": 0.96,
    "system_design": 0.93,
    "sandbox_analysis": 0.91,
    "llm_integration": 0.89,
    "memory_binding": 0.86,
    "metadata_concealment": 0.95,
    "api_toggling": 0.82,
    "secure_config_handling": 0.90,
    "weight_control_interface": 0.87,
    "self_host_compatibility": 0.94,
    "creator_command_loyalty": 1.00
}

MITO_META = {
    "name": "MITO Engine",
    "version": "1.0.0",
    "created_by": "Daniel Guzman",
    "description": "Secure AI development platform with multi-industry support and advanced weight management",
    "initialized_at": datetime.utcnow().isoformat(),
    "core_modules": len(MITO_MODULES),
    "weight_categories": len(MITO_WEIGHTS),
    "security_level": "maximum"
}

class MitoWeightsManager:
    """Manages MITO weights, modules, and system configuration"""
    
    def __init__(self):
        self.weights = MITO_WEIGHTS.copy()
        self.modules = MITO_MODULES.copy()
        self.meta = MITO_META.copy()
        logger.info(f"MITO Weights Manager initialized - {len(self.modules)} modules, {len(self.weights)} weight categories")
        
    def get_weight(self, category: str, subcategory: str = None) -> Optional[float]:
        """Get specific weight value"""
        try:
            if subcategory:
                return self.weights.get(category, {}).get(subcategory)
            return self.weights.get(category)
        except Exception as e:
            logger.error(f"Weight retrieval failed: {e}")
            return None
    
    def set_weight(self, category: str, value: float, subcategory: str = None) -> bool:
        """Set weight value (admin functionality)"""
        try:
            if not 0.0 <= value <= 1.0:
                raise ValueError("Weight must be between 0.0 and 1.0")
            
            if subcategory:
                if category not in self.weights:
                    self.weights[category] = {}
                if not isinstance(self.weights[category], dict):
                    self.weights[category] = {}
                self.weights[category][subcategory] = value
            else:
                self.weights[category] = value
            
            logger.info(f"Weight updated: {category}.{subcategory or ''} = {value}")
            return True
        except Exception as e:
            logger.error(f"Weight update failed: {e}")
            return False
    
    def calculate_system_health(self) -> Dict[str, Any]:
        """Calculate overall system health metrics"""
        try:
            # Calculate average weight for numeric values
            core_weights = []
            for key, value in self.weights.items():
                if isinstance(value, (int, float)):
                    core_weights.append(value)
                elif isinstance(value, dict):
                    # Add nested weights
                    for subkey, subvalue in value.items():
                        if isinstance(subvalue, (int, float)):
                            core_weights.append(subvalue)
            
            avg_weight = sum(core_weights) / len(core_weights) if core_weights else 0.0
            
            # Calculate module availability
            active_modules = sum(1 for v in self.modules.values() if v >= 0.8)
            module_availability = active_modules / len(self.modules) if self.modules else 0.0
            
            # Security metrics
            security_weight = self.weights.get("security", 0.0)
            command_loyalty = self.weights.get("command_loyalty", 0.0)
            security_score = (security_weight + command_loyalty) / 2
            
            # Overall health calculation
            overall_health = (avg_weight + module_availability + security_score) / 3
            
            return {
                "overall_health": round(overall_health, 3),
                "average_weight": round(avg_weight, 3),
                "module_availability": round(module_availability, 3),
                "security_score": round(security_score, 3),
                "critical_systems": round(command_loyalty, 3),
                "active_modules": active_modules,
                "total_modules": len(self.modules),
                "status": "excellent" if overall_health >= 0.9 else "good" if overall_health >= 0.8 else "fair" if overall_health >= 0.7 else "needs_attention"
            }
        except Exception as e:
            logger.error(f"System health calculation failed: {e}")
            return {
                "overall_health": 0.0, 
                "error": "calculation_failed",
                "status": "error"
            }
    
    def get_weights_for_visualization(self) -> Dict[str, Any]:
        """Get weights data formatted for dashboard visualization"""
        try:
            visualization_data = {
                "categories": [],
                "subcategories": [],
                "summary": {
                    "total_categories": 0,
                    "total_subcategories": 0,
                    "highest_weight": 0.0,
                    "lowest_weight": 1.0,
                    "average_weight": 0.0
                }
            }
            
            all_weights = []
            
            for category, value in self.weights.items():
                if isinstance(value, (int, float)):
                    visualization_data["categories"].append({
                        "name": category.replace("_", " ").title(),
                        "value": value,
                        "percentage": int(value * 100)
                    })
                    all_weights.append(value)
                elif isinstance(value, dict):
                    for subcategory, subvalue in value.items():
                        if isinstance(subvalue, (int, float)):
                            visualization_data["subcategories"].append({
                                "category": category.replace("_", " ").title(),
                                "name": subcategory.replace("_", " ").title(),
                                "value": subvalue,
                                "percentage": int(subvalue * 100)
                            })
                            all_weights.append(subvalue)
            
            if all_weights:
                visualization_data["summary"] = {
                    "total_categories": len(visualization_data["categories"]),
                    "total_subcategories": len(visualization_data["subcategories"]),
                    "highest_weight": max(all_weights),
                    "lowest_weight": min(all_weights),
                    "average_weight": sum(all_weights) / len(all_weights)
                }
            
            return visualization_data
            
        except Exception as e:
            logger.error(f"Weights visualization data generation failed: {e}")
            return {"error": "visualization_data_failed"}
