"""
MITO Engine - AI Agent & Tool Creator
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: AI Agent & Tool Creator
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class APIUsageTracker:
    """Track API usage and costs across different providers"""
    
    def __init__(self, log_file: str = 'api_usage.log'):
        self.log_file = log_file
        self.pricing = {
            'openai': {
                'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},  # per 1K tokens
                'gpt-4': {'input': 0.03, 'output': 0.06},
                'dall-e-3': {'image': 0.04}  # per image
            },
            'llama': {
                'llama-3-70b-8192': {'input': 0.0008, 'output': 0.0008}  # Groq pricing
            },
            'claude': {
                'claude-3-opus': {'input': 0.015, 'output': 0.075}
            }
        }
        
        # Initialize log file if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write('')
    
    def log_usage(self, provider: str, model: str, usage: Dict[str, Any], 
                  request_type: str = 'chat', custom_data: Optional[Dict] = None):
        """Log API usage with cost calculation"""
        try:
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            
            cost = self._calculate_cost(provider, model, prompt_tokens, completion_tokens)
            
            entry = {
                'timestamp': datetime.now().isoformat(),
                'provider': provider,
                'model': model,
                'request_type': request_type,
                'usage': usage,
                'cost': cost,
                'custom_data': custom_data or {}
            }
            
            self._write_log_entry(entry)
            
        except Exception as e:
            logger.error(f"Usage logging error: {e}")
    
    def _calculate_cost(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int):
        """Calculate cost based on token usage"""
        try:
            pricing = self.pricing.get(provider, {}).get(model, {})
            
            input_cost = (prompt_tokens / 1000) * pricing.get('input', 0)
            output_cost = (completion_tokens / 1000) * pricing.get('output', 0)
            
            return round(input_cost + output_cost, 6)
            
        except Exception:
            return 0.0
    
    def _write_log_entry(self, entry: Dict[str, Any]):
        """Write log entry to file"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Log write error: {e}")
    
    def get_usage_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get usage summary for the last N days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            total_requests = 0
            total_cost = 0.0
            provider_breakdown = {}
            
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            entry_date = datetime.fromisoformat(entry['timestamp'])
                            
                            if entry_date >= cutoff_date:
                                total_requests += 1
                                total_cost += entry.get('cost', 0)
                                
                                provider = entry['provider']
                                if provider not in provider_breakdown:
                                    provider_breakdown[provider] = {
                                        'requests': 0,
                                        'cost': 0.0,
                                        'tokens': {'input': 0, 'output': 0}
                                    }
                                
                                provider_breakdown[provider]['requests'] += 1
                                provider_breakdown[provider]['cost'] += entry.get('cost', 0)
                                
                                usage = entry.get('usage', {})
                                provider_breakdown[provider]['tokens']['input'] += usage.get('prompt_tokens', 0)
                                provider_breakdown[provider]['tokens']['output'] += usage.get('completion_tokens', 0)
                                
                        except (json.JSONDecodeError, ValueError):
                            continue
            
            return {
                'period_days': days,
                'total_requests': total_requests,
                'total_cost': round(total_cost, 4),
                'average_cost_per_request': round(total_cost / max(total_requests, 1), 6),
                'provider_breakdown': provider_breakdown
            }
            
        except Exception as e:
            logger.error(f"Usage summary error: {e}")
            return {
                'period_days': days,
                'total_requests': 0,
                'total_cost': 0.0,
                'average_cost_per_request': 0.0,
                'provider_breakdown': {}
            }
    
    def get_cost_breakdown(self, days: int = 30) -> Dict[str, Any]:
        """Get detailed cost breakdown"""
        try:
            summary = self.get_usage_summary(days)
            
            return {
                'daily_costs': [],  # Could implement daily breakdown
                'provider_costs': summary['provider_breakdown'],
                'total_cost': summary['total_cost'],
                'projected_monthly': round(summary['total_cost'] * (30 / days), 2)
            }
            
        except Exception as e:
            logger.error(f"Cost breakdown error: {e}")
            return {
                'daily_costs': [],
                'provider_costs': {},
                'total_cost': 0.0,
                'projected_monthly': 0.0
            }
    
    def get_pricing_info(self) -> Dict[str, Any]:
        """Get current pricing information for all providers"""
        return self.pricing
    
    def estimate_cost(self, provider: str, model: str, estimated_prompt_tokens: int, 
                     estimated_completion_tokens: int) -> Dict[str, float]:
        """Estimate cost for a request before making it"""
        cost = self._calculate_cost(provider, model, estimated_prompt_tokens, estimated_completion_tokens)
        
        return {
            'estimated_cost': cost,
            'input_tokens': estimated_prompt_tokens,
            'output_tokens': estimated_completion_tokens,
            'provider': provider,
            'model': model
        }
    
    def clear_logs(self, days_to_keep: int = 90):
        """Clear old log entries, keeping only recent ones"""
        try:
            if not os.path.exists(self.log_file):
                return
                
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            kept_entries = []
            
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_date = datetime.fromisoformat(entry['timestamp'])
                        
                        if entry_date >= cutoff_date:
                            kept_entries.append(line.strip())
                            
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            with open(self.log_file, 'w') as f:
                for entry in kept_entries:
                    f.write(entry + '\n')
                    
            logger.info(f"Cleaned usage logs, kept {len(kept_entries)} entries")
            
        except Exception as e:
            logger.error(f"Log cleanup error: {e}")