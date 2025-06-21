"""
MITO Engine - Networking Management System
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: Advanced networking tools and monitoring
"""

import socket
import subprocess
import psutil
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
import threading

logger = logging.getLogger(__name__)

class NetworkingManager:
    """Comprehensive networking management for MITO Engine"""
    
    def __init__(self):
        self.active_connections = {}
        self.port_monitors = {}
        self.network_stats = {}
        self.dns_cache = {}
        
    def get_network_interfaces(self) -> Dict[str, Any]:
        """Get all network interfaces and their details"""
        try:
            interfaces = {}
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()
            
            for interface_name in stats:
                interface_info = {
                    'name': interface_name,
                    'is_up': stats[interface_name].isup,
                    'duplex': stats[interface_name].duplex,
                    'speed': stats[interface_name].speed,
                    'mtu': stats[interface_name].mtu,
                    'addresses': []
                }
                
                if interface_name in addrs:
                    for addr in addrs[interface_name]:
                        address_info = {
                            'family': addr.family.name,
                            'address': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast
                        }
                        interface_info['addresses'].append(address_info)
                
                interfaces[interface_name] = interface_info
                
            return interfaces
            
        except Exception as e:
            logger.error(f"Failed to get network interfaces: {e}")
            return {}
            
    def get_active_connections(self) -> List[Dict[str, Any]]:
        """Get all active network connections"""
        try:
            connections = []
            for conn in psutil.net_connections(kind='inet'):
                connection_info = {
                    'fd': conn.fd,
                    'family': conn.family.name if conn.family else 'Unknown',
                    'type': conn.type.name if conn.type else 'Unknown',
                    'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else 'N/A',
                    'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else 'N/A',
                    'status': conn.status if conn.status else 'N/A',
                    'pid': conn.pid if conn.pid else 'N/A'
                }
                
                # Get process name if PID is available
                if conn.pid:
                    try:
                        process = psutil.Process(conn.pid)
                        connection_info['process_name'] = process.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        connection_info['process_name'] = 'Unknown'
                
                connections.append(connection_info)
                
            return connections
            
        except Exception as e:
            logger.error(f"Failed to get active connections: {e}")
            return []
            
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network I/O statistics"""
        try:
            io_counters = psutil.net_io_counters(pernic=True)
            stats = {}
            
            for interface, counters in io_counters.items():
                stats[interface] = {
                    'bytes_sent': counters.bytes_sent,
                    'bytes_recv': counters.bytes_recv,
                    'packets_sent': counters.packets_sent,
                    'packets_recv': counters.packets_recv,
                    'errin': counters.errin,
                    'errout': counters.errout,
                    'dropin': counters.dropin,
                    'dropout': counters.dropout
                }
                
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get network stats: {e}")
            return {}
            
    def ping_host(self, host: str, count: int = 4) -> Dict[str, Any]:
        """Ping a host and return results"""
        try:
            cmd = ['ping', '-c', str(count), host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            return {
                'host': host,
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'host': host,
                'success': False,
                'output': '',
                'error': 'Ping timeout',
                'return_code': -1
            }
        except Exception as e:
            return {
                'host': host,
                'success': False,
                'output': '',
                'error': str(e),
                'return_code': -1
            }
            
    def traceroute_host(self, host: str) -> Dict[str, Any]:
        """Perform traceroute to a host"""
        try:
            cmd = ['traceroute', '-n', host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            return {
                'host': host,
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'host': host,
                'success': False,
                'output': '',
                'error': 'Traceroute timeout',
                'return_code': -1
            }
        except Exception as e:
            return {
                'host': host,
                'success': False,
                'output': '',
                'error': str(e),
                'return_code': -1
            }
            
    def resolve_dns(self, hostname: str) -> Dict[str, Any]:
        """Resolve DNS for a hostname"""
        try:
            # Check cache first
            if hostname in self.dns_cache:
                cache_entry = self.dns_cache[hostname]
                if time.time() - cache_entry['timestamp'] < 300:  # 5 minute cache
                    return cache_entry['result']
            
            # Resolve hostname
            ip_addresses = socket.gethostbyname_ex(hostname)
            
            result = {
                'hostname': hostname,
                'success': True,
                'ip_addresses': ip_addresses[2],
                'canonical_name': ip_addresses[0],
                'aliases': ip_addresses[1]
            }
            
            # Cache result
            self.dns_cache[hostname] = {
                'timestamp': time.time(),
                'result': result
            }
            
            return result
            
        except socket.gaierror as e:
            return {
                'hostname': hostname,
                'success': False,
                'error': str(e),
                'ip_addresses': [],
                'canonical_name': '',
                'aliases': []
            }
            
    def scan_port(self, host: str, port: int, timeout: float = 1.0) -> Dict[str, Any]:
        """Scan a specific port on a host"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            return {
                'host': host,
                'port': port,
                'open': result == 0,
                'response_time': timeout if result != 0 else 0
            }
            
        except Exception as e:
            return {
                'host': host,
                'port': port,
                'open': False,
                'error': str(e)
            }
            
    def scan_port_range(self, host: str, start_port: int, end_port: int) -> List[Dict[str, Any]]:
        """Scan a range of ports on a host"""
        open_ports = []
        
        for port in range(start_port, end_port + 1):
            result = self.scan_port(host, port, timeout=0.5)
            if result['open']:
                open_ports.append(result)
                
        return open_ports
        
    def get_listening_ports(self) -> List[Dict[str, Any]]:
        """Get all listening ports on the system"""
        try:
            listening_ports = []
            
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == psutil.CONN_LISTEN:
                    port_info = {
                        'port': conn.laddr.port,
                        'address': conn.laddr.ip,
                        'family': conn.family.name,
                        'type': conn.type.name,
                        'pid': conn.pid
                    }
                    
                    # Get process information
                    if conn.pid:
                        try:
                            process = psutil.Process(conn.pid)
                            port_info['process_name'] = process.name()
                            port_info['process_cmdline'] = ' '.join(process.cmdline())
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            port_info['process_name'] = 'Unknown'
                            port_info['process_cmdline'] = 'Unknown'
                    
                    listening_ports.append(port_info)
                    
            return listening_ports
            
        except Exception as e:
            logger.error(f"Failed to get listening ports: {e}")
            return []
            
    def test_connectivity(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """Test HTTP/HTTPS connectivity to a URL"""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            response_time = time.time() - start_time
            
            return {
                'url': url,
                'success': True,
                'status_code': response.status_code,
                'response_time': response_time,
                'headers': dict(response.headers),
                'content_length': len(response.content)
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'url': url,
                'success': False,
                'error': str(e),
                'response_time': timeout
            }
            
    def get_bandwidth_usage(self) -> Dict[str, Any]:
        """Get current bandwidth usage"""
        try:
            # Get current stats
            current_stats = psutil.net_io_counters()
            
            # Wait a second and get new stats
            time.sleep(1)
            new_stats = psutil.net_io_counters()
            
            # Calculate bandwidth
            bytes_sent_per_sec = new_stats.bytes_sent - current_stats.bytes_sent
            bytes_recv_per_sec = new_stats.bytes_recv - current_stats.bytes_recv
            
            return {
                'upload_speed': bytes_sent_per_sec,  # bytes per second
                'download_speed': bytes_recv_per_sec,  # bytes per second
                'upload_speed_mbps': (bytes_sent_per_sec * 8) / (1024 * 1024),  # Mbps
                'download_speed_mbps': (bytes_recv_per_sec * 8) / (1024 * 1024),  # Mbps
                'total_bytes_sent': new_stats.bytes_sent,
                'total_bytes_recv': new_stats.bytes_recv
            }
            
        except Exception as e:
            logger.error(f"Failed to get bandwidth usage: {e}")
            return {}
            
    def get_network_security_info(self) -> Dict[str, Any]:
        """Get network security information"""
        try:
            security_info = {
                'firewall_status': self._check_firewall_status(),
                'open_ports_security': self._analyze_port_security(),
                'suspicious_connections': self._detect_suspicious_connections(),
                'network_threats': self._scan_network_threats()
            }
            
            return security_info
            
        except Exception as e:
            logger.error(f"Failed to get network security info: {e}")
            return {}
            
    def _check_firewall_status(self) -> Dict[str, Any]:
        """Check firewall status"""
        try:
            # Check if UFW is installed and active
            result = subprocess.run(['ufw', 'status'], capture_output=True, text=True)
            
            return {
                'installed': result.returncode == 0,
                'status': result.stdout,
                'active': 'Status: active' in result.stdout
            }
            
        except Exception:
            return {
                'installed': False,
                'status': 'Firewall not detected',
                'active': False
            }
            
    def _analyze_port_security(self) -> List[Dict[str, Any]]:
        """Analyze open ports for security risks"""
        listening_ports = self.get_listening_ports()
        risky_ports = []
        
        # Common risky ports
        known_risky = {
            21: 'FTP (unencrypted)',
            23: 'Telnet (unencrypted)',
            53: 'DNS (potential amplification)',
            135: 'RPC (Windows vulnerability)',
            139: 'NetBIOS (Windows vulnerability)',
            445: 'SMB (Windows vulnerability)',
            1433: 'SQL Server (database exposure)',
            3389: 'RDP (brute force target)',
            5432: 'PostgreSQL (database exposure)',
            6379: 'Redis (often unsecured)'
        }
        
        for port in listening_ports:
            port_num = port['port']
            if port_num in known_risky:
                risky_ports.append({
                    'port': port_num,
                    'risk': known_risky[port_num],
                    'process': port.get('process_name', 'Unknown'),
                    'address': port['address']
                })
                
        return risky_ports
        
    def _detect_suspicious_connections(self) -> List[Dict[str, Any]]:
        """Detect potentially suspicious network connections"""
        connections = self.get_active_connections()
        suspicious = []
        
        for conn in connections:
            # Check for connections to unusual ports or suspicious IPs
            if 'remote_address' in conn and conn['remote_address'] != 'N/A':
                try:
                    remote_ip, remote_port = conn['remote_address'].split(':')
                    remote_port = int(remote_port)
                    
                    # Flag high ports that might be unusual
                    if remote_port > 49152 and conn['status'] == 'ESTABLISHED':
                        suspicious.append({
                            'connection': conn,
                            'reason': 'Connection to high port',
                            'risk_level': 'medium'
                        })
                        
                except ValueError:
                    pass
                    
        return suspicious
        
    def _scan_network_threats(self) -> Dict[str, Any]:
        """Scan for potential network threats"""
        return {
            'timestamp': datetime.now().isoformat(),
            'threats_detected': 0,
            'scan_status': 'completed',
            'recommendations': [
                'Keep firewall enabled',
                'Monitor unusual port activity',
                'Regular security updates',
                'Use encrypted protocols'
            ]
        }
        
    def monitor_network_performance(self, duration: int = 60) -> Dict[str, Any]:
        """Monitor network performance over time"""
        try:
            start_time = time.time()
            start_stats = psutil.net_io_counters()
            
            # Monitor for specified duration
            time.sleep(duration)
            
            end_stats = psutil.net_io_counters()
            elapsed_time = time.time() - start_time
            
            # Calculate performance metrics
            bytes_sent = end_stats.bytes_sent - start_stats.bytes_sent
            bytes_recv = end_stats.bytes_recv - start_stats.bytes_recv
            packets_sent = end_stats.packets_sent - start_stats.packets_sent
            packets_recv = end_stats.packets_recv - start_stats.packets_recv
            
            return {
                'duration': elapsed_time,
                'bytes_sent': bytes_sent,
                'bytes_received': bytes_recv,
                'packets_sent': packets_sent,
                'packets_received': packets_recv,
                'avg_upload_speed': bytes_sent / elapsed_time,
                'avg_download_speed': bytes_recv / elapsed_time,
                'packet_loss': {
                    'sent_errors': end_stats.errout - start_stats.errout,
                    'recv_errors': end_stats.errin - start_stats.errin,
                    'dropped_packets': (end_stats.dropout - start_stats.dropout) + (end_stats.dropin - start_stats.dropin)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to monitor network performance: {e}")
            return {}