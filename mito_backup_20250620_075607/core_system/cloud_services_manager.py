#!/usr/bin/env python3
"""
Cloud Services Integration Manager for MITO Engine
Integrates with AWS, Azure, Google Cloud Platform for scalable computing and deployment
"""

import os
import json
import logging
import boto3
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, asdict
import requests
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from google.cloud import compute_v1
from google.oauth2 import service_account
import sqlite3

logger = logging.getLogger(__name__)

@dataclass
class CloudResource:
    """Represents a cloud resource"""
    id: str
    name: str
    provider: str
    resource_type: str
    region: str
    status: str
    created_at: str
    metadata: Dict[str, Any]
    cost_estimate: Optional[float] = None

@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    name: str
    provider: str
    region: str
    instance_type: str
    environment: str
    auto_scaling: bool
    load_balancer: bool
    database: bool
    storage: bool
    monitoring: bool

class CloudDatabase:
    """Database for cloud resources and deployments"""
    
    def __init__(self, db_path: str = "cloud_services.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize cloud services database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cloud_resources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                provider TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                region TEXT NOT NULL,
                status TEXT NOT NULL,
                metadata TEXT,
                cost_estimate REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                provider TEXT NOT NULL,
                config TEXT NOT NULL,
                status TEXT NOT NULL,
                deployed_at TIMESTAMP,
                resources TEXT,
                endpoint_url TEXT,
                deployment_logs TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cloud_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                credential_type TEXT NOT NULL,
                encrypted_credentials TEXT NOT NULL,
                region TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cost_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                service_type TEXT NOT NULL,
                cost_amount REAL NOT NULL,
                billing_period TEXT NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()

class AWSManager:
    """AWS cloud services manager"""
    
    def __init__(self, access_key: str = None, secret_key: str = None, region: str = 'us-east-1'):
        self.region = region
        self.session = boto3.Session(
            aws_access_key_id=access_key or os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=secret_key or os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=region
        )
        self.ec2 = self.session.client('ec2')
        self.s3 = self.session.client('s3')
        self.rds = self.session.client('rds')
        self.ecs = self.session.client('ecs')
        self.lambda_client = self.session.client('lambda')
        
    def test_connection(self) -> bool:
        """Test AWS connection"""
        try:
            self.ec2.describe_regions()
            return True
        except Exception as e:
            logger.error(f"AWS connection test failed: {e}")
            return False
            
    def create_ec2_instance(self, config: Dict[str, Any]) -> CloudResource:
        """Create EC2 instance"""
        try:
            response = self.ec2.run_instances(
                ImageId=config.get('ami_id', 'ami-0c02fb55956c7d316'),  # Amazon Linux 2
                MinCount=1,
                MaxCount=1,
                InstanceType=config.get('instance_type', 't3.micro'),
                KeyName=config.get('key_name'),
                SecurityGroupIds=config.get('security_groups', []),
                SubnetId=config.get('subnet_id'),
                UserData=config.get('user_data', ''),
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': config.get('name', 'MITO-Instance')},
                            {'Key': 'Environment', 'Value': config.get('environment', 'development')},
                            {'Key': 'Project', 'Value': 'MITO-Engine'}
                        ]
                    }
                ]
            )
            
            instance = response['Instances'][0]
            instance_id = instance['InstanceId']
            
            # Wait for instance to be running
            waiter = self.ec2.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id])
            
            # Get updated instance info
            updated_response = self.ec2.describe_instances(InstanceIds=[instance_id])
            updated_instance = updated_response['Reservations'][0]['Instances'][0]
            
            return CloudResource(
                id=instance_id,
                name=config.get('name', 'MITO-Instance'),
                provider='aws',
                resource_type='ec2_instance',
                region=self.region,
                status=updated_instance['State']['Name'],
                created_at=datetime.now().isoformat(),
                metadata={
                    'instance_type': updated_instance['InstanceType'],
                    'public_ip': updated_instance.get('PublicIpAddress'),
                    'private_ip': updated_instance.get('PrivateIpAddress'),
                    'vpc_id': updated_instance.get('VpcId'),
                    'subnet_id': updated_instance.get('SubnetId')
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create EC2 instance: {e}")
            raise
            
    def create_s3_bucket(self, bucket_name: str, config: Dict[str, Any] = None) -> CloudResource:
        """Create S3 bucket"""
        try:
            config = config or {}
            
            if self.region != 'us-east-1':
                self.s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            else:
                self.s3.create_bucket(Bucket=bucket_name)
            
            # Set bucket versioning if requested
            if config.get('versioning', False):
                self.s3.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
            
            # Set bucket encryption
            if config.get('encryption', True):
                self.s3.put_bucket_encryption(
                    Bucket=bucket_name,
                    ServerSideEncryptionConfiguration={
                        'Rules': [
                            {
                                'ApplyServerSideEncryptionByDefault': {
                                    'SSEAlgorithm': 'AES256'
                                }
                            }
                        ]
                    }
                )
            
            return CloudResource(
                id=bucket_name,
                name=bucket_name,
                provider='aws',
                resource_type='s3_bucket',
                region=self.region,
                status='active',
                created_at=datetime.now().isoformat(),
                metadata={
                    'versioning': config.get('versioning', False),
                    'encryption': config.get('encryption', True),
                    'website_url': f"https://{bucket_name}.s3.{self.region}.amazonaws.com"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create S3 bucket: {e}")
            raise
            
    def deploy_lambda_function(self, config: Dict[str, Any]) -> CloudResource:
        """Deploy Lambda function"""
        try:
            # Read function code
            with open(config['code_file'], 'rb') as f:
                code_content = f.read()
            
            response = self.lambda_client.create_function(
                FunctionName=config['function_name'],
                Runtime=config.get('runtime', 'python3.9'),
                Role=config['execution_role_arn'],
                Handler=config.get('handler', 'lambda_function.lambda_handler'),
                Code={'ZipFile': code_content},
                Description=config.get('description', 'MITO Engine Lambda Function'),
                Timeout=config.get('timeout', 30),
                MemorySize=config.get('memory_size', 128),
                Environment={
                    'Variables': config.get('environment_variables', {})
                },
                Tags={
                    'Project': 'MITO-Engine',
                    'Environment': config.get('environment', 'development')
                }
            )
            
            return CloudResource(
                id=response['FunctionArn'],
                name=config['function_name'],
                provider='aws',
                resource_type='lambda_function',
                region=self.region,
                status='active',
                created_at=datetime.now().isoformat(),
                metadata={
                    'runtime': response['Runtime'],
                    'handler': response['Handler'],
                    'memory_size': response['MemorySize'],
                    'timeout': response['Timeout'],
                    'invoke_url': f"https://lambda.{self.region}.amazonaws.com/2015-03-31/functions/{config['function_name']}/invocations"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to deploy Lambda function: {e}")
            raise
            
    def list_resources(self) -> List[CloudResource]:
        """List all AWS resources"""
        resources = []
        
        try:
            # List EC2 instances
            ec2_response = self.ec2.describe_instances()
            for reservation in ec2_response['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] != 'terminated':
                        name = next((tag['Value'] for tag in instance.get('Tags', []) 
                                   if tag['Key'] == 'Name'), instance['InstanceId'])
                        
                        resources.append(CloudResource(
                            id=instance['InstanceId'],
                            name=name,
                            provider='aws',
                            resource_type='ec2_instance',
                            region=instance['Placement']['AvailabilityZone'][:-1],
                            status=instance['State']['Name'],
                            created_at=instance['LaunchTime'].isoformat(),
                            metadata={
                                'instance_type': instance['InstanceType'],
                                'public_ip': instance.get('PublicIpAddress'),
                                'private_ip': instance.get('PrivateIpAddress')
                            }
                        ))
            
            # List S3 buckets
            s3_response = self.s3.list_buckets()
            for bucket in s3_response['Buckets']:
                try:
                    location = self.s3.get_bucket_location(Bucket=bucket['Name'])
                    region = location['LocationConstraint'] or 'us-east-1'
                    
                    resources.append(CloudResource(
                        id=bucket['Name'],
                        name=bucket['Name'],
                        provider='aws',
                        resource_type='s3_bucket',
                        region=region,
                        status='active',
                        created_at=bucket['CreationDate'].isoformat(),
                        metadata={}
                    ))
                except Exception as e:
                    logger.warning(f"Failed to get bucket location for {bucket['Name']}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to list AWS resources: {e}")
            
        return resources

class AzureManager:
    """Azure cloud services manager"""
    
    def __init__(self, subscription_id: str = None):
        self.subscription_id = subscription_id or os.environ.get('AZURE_SUBSCRIPTION_ID')
        self.credential = DefaultAzureCredential()
        self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)
        self.compute_client = ComputeManagementClient(self.credential, self.subscription_id)
        
    def test_connection(self) -> bool:
        """Test Azure connection"""
        try:
            list(self.resource_client.resource_groups.list())
            return True
        except Exception as e:
            logger.error(f"Azure connection test failed: {e}")
            return False
            
    def create_resource_group(self, name: str, location: str = 'East US') -> CloudResource:
        """Create Azure resource group"""
        try:
            resource_group = self.resource_client.resource_groups.create_or_update(
                name,
                {
                    'location': location,
                    'tags': {
                        'Project': 'MITO-Engine',
                        'CreatedBy': 'MITO-CloudManager'
                    }
                }
            )
            
            return CloudResource(
                id=resource_group.id,
                name=name,
                provider='azure',
                resource_type='resource_group',
                region=location,
                status='succeeded',
                created_at=datetime.now().isoformat(),
                metadata={
                    'provisioning_state': resource_group.properties.provisioning_state
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create Azure resource group: {e}")
            raise
            
    def create_virtual_machine(self, config: Dict[str, Any]) -> CloudResource:
        """Create Azure virtual machine"""
        try:
            vm_name = config['vm_name']
            resource_group = config['resource_group']
            
            vm_parameters = {
                'location': config.get('location', 'East US'),
                'os_profile': {
                    'computer_name': vm_name,
                    'admin_username': config['admin_username'],
                    'admin_password': config['admin_password']
                },
                'hardware_profile': {
                    'vm_size': config.get('vm_size', 'Standard_B1s')
                },
                'storage_profile': {
                    'image_reference': {
                        'publisher': 'Canonical',
                        'offer': 'UbuntuServer',
                        'sku': '18.04-LTS',
                        'version': 'latest'
                    }
                },
                'network_profile': {
                    'network_interfaces': [
                        {
                            'id': config['network_interface_id']
                        }
                    ]
                },
                'tags': {
                    'Project': 'MITO-Engine',
                    'Environment': config.get('environment', 'development')
                }
            }
            
            operation = self.compute_client.virtual_machines.begin_create_or_update(
                resource_group, vm_name, vm_parameters
            )
            vm = operation.result()
            
            return CloudResource(
                id=vm.id,
                name=vm_name,
                provider='azure',
                resource_type='virtual_machine',
                region=vm.location,
                status='running',
                created_at=datetime.now().isoformat(),
                metadata={
                    'vm_size': vm.hardware_profile.vm_size,
                    'os_type': 'Linux',
                    'provisioning_state': vm.provisioning_state
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create Azure VM: {e}")
            raise

class GCPManager:
    """Google Cloud Platform services manager"""
    
    def __init__(self, project_id: str = None, credentials_path: str = None):
        self.project_id = project_id or os.environ.get('GCP_PROJECT_ID')
        
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
        else:
            credentials = None
            
        self.compute_client = compute_v1.InstancesClient(credentials=credentials)
        self.zones_client = compute_v1.ZonesClient(credentials=credentials)
        
    def test_connection(self) -> bool:
        """Test GCP connection"""
        try:
            list(self.zones_client.list(project=self.project_id))
            return True
        except Exception as e:
            logger.error(f"GCP connection test failed: {e}")
            return False
            
    def create_compute_instance(self, config: Dict[str, Any]) -> CloudResource:
        """Create GCP Compute Engine instance"""
        try:
            instance_name = config['instance_name']
            zone = config.get('zone', 'us-central1-a')
            
            instance_config = {
                'name': instance_name,
                'machine_type': f"zones/{zone}/machineTypes/{config.get('machine_type', 'e2-micro')}",
                'disks': [
                    {
                        'boot': True,
                        'auto_delete': True,
                        'initialize_params': {
                            'source_image': 'projects/debian-cloud/global/images/family/debian-11'
                        }
                    }
                ],
                'network_interfaces': [
                    {
                        'network': 'global/networks/default',
                        'access_configs': [
                            {
                                'type': 'ONE_TO_ONE_NAT',
                                'name': 'External NAT'
                            }
                        ]
                    }
                ],
                'metadata': {
                    'items': [
                        {
                            'key': 'startup-script',
                            'value': config.get('startup_script', '')
                        }
                    ]
                },
                'labels': {
                    'project': 'mito-engine',
                    'environment': config.get('environment', 'development')
                }
            }
            
            operation = self.compute_client.insert(
                project=self.project_id,
                zone=zone,
                instance_resource=instance_config
            )
            
            # Wait for operation to complete
            while not operation.done():
                operation = self.compute_client.get(
                    project=self.project_id,
                    zone=zone,
                    operation=operation.name
                )
            
            # Get instance details
            instance = self.compute_client.get(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            
            return CloudResource(
                id=str(instance.id),
                name=instance_name,
                provider='gcp',
                resource_type='compute_instance',
                region=zone,
                status=instance.status,
                created_at=datetime.now().isoformat(),
                metadata={
                    'machine_type': instance.machine_type.split('/')[-1],
                    'zone': zone,
                    'self_link': instance.self_link
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create GCP instance: {e}")
            raise

class CloudServicesManager:
    """Main cloud services integration manager"""
    
    def __init__(self):
        self.db = CloudDatabase()
        self.providers = {}
        self.load_providers()
        
    def load_providers(self):
        """Load cloud providers based on available credentials"""
        # AWS
        if os.environ.get('AWS_ACCESS_KEY_ID') and os.environ.get('AWS_SECRET_ACCESS_KEY'):
            try:
                self.providers['aws'] = AWSManager()
                if self.providers['aws'].test_connection():
                    logger.info("AWS provider loaded successfully")
                else:
                    del self.providers['aws']
            except Exception as e:
                logger.warning(f"Failed to load AWS provider: {e}")
        
        # Azure
        if os.environ.get('AZURE_SUBSCRIPTION_ID'):
            try:
                self.providers['azure'] = AzureManager()
                if self.providers['azure'].test_connection():
                    logger.info("Azure provider loaded successfully")
                else:
                    del self.providers['azure']
            except Exception as e:
                logger.warning(f"Failed to load Azure provider: {e}")
        
        # GCP
        if os.environ.get('GCP_PROJECT_ID'):
            try:
                self.providers['gcp'] = GCPManager()
                if self.providers['gcp'].test_connection():
                    logger.info("GCP provider loaded successfully")
                else:
                    del self.providers['gcp']
            except Exception as e:
                logger.warning(f"Failed to load GCP provider: {e}")
                
    def deploy_application(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Deploy application to cloud"""
        try:
            if config.provider not in self.providers:
                raise ValueError(f"Provider {config.provider} not available")
            
            provider = self.providers[config.provider]
            deployed_resources = []
            
            # Create main compute resource
            if config.provider == 'aws':
                # Create EC2 instance
                ec2_config = {
                    'name': f"{config.name}-server",
                    'instance_type': config.instance_type,
                    'environment': config.environment
                }
                compute_resource = provider.create_ec2_instance(ec2_config)
                deployed_resources.append(compute_resource)
                
                # Create S3 bucket if storage requested
                if config.storage:
                    bucket_name = f"{config.name}-storage-{datetime.now().strftime('%Y%m%d')}"
                    storage_resource = provider.create_s3_bucket(bucket_name)
                    deployed_resources.append(storage_resource)
                    
            elif config.provider == 'azure':
                # Create resource group first
                rg_name = f"{config.name}-rg"
                rg_resource = provider.create_resource_group(rg_name, config.region)
                deployed_resources.append(rg_resource)
                
            elif config.provider == 'gcp':
                # Create compute instance
                gcp_config = {
                    'instance_name': f"{config.name}-server",
                    'machine_type': config.instance_type,
                    'zone': config.region,
                    'environment': config.environment
                }
                compute_resource = provider.create_compute_instance(gcp_config)
                deployed_resources.append(compute_resource)
            
            # Store deployment record
            deployment_id = f"deploy_{config.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self._store_deployment(deployment_id, config, deployed_resources)
            
            # Store individual resources
            for resource in deployed_resources:
                self._store_resource(resource)
            
            return {
                'deployment_id': deployment_id,
                'status': 'success',
                'resources': [asdict(r) for r in deployed_resources],
                'message': f"Successfully deployed {config.name} to {config.provider}"
            }
            
        except Exception as e:
            logger.error(f"Failed to deploy application: {e}")
            return {
                'deployment_id': None,
                'status': 'failed',
                'error': str(e)
            }
            
    def list_all_resources(self) -> Dict[str, List[CloudResource]]:
        """List resources from all providers"""
        all_resources = {}
        
        for provider_name, provider in self.providers.items():
            try:
                resources = provider.list_resources()
                all_resources[provider_name] = resources
                
                # Update database
                for resource in resources:
                    self._store_resource(resource)
                    
            except Exception as e:
                logger.error(f"Failed to list resources from {provider_name}: {e}")
                all_resources[provider_name] = []
                
        return all_resources
        
    def get_cost_estimates(self, days: int = 30) -> Dict[str, Any]:
        """Get cost estimates for cloud resources"""
        # This is a simplified cost estimation
        # In production, you'd integrate with each provider's billing API
        
        estimates = {
            'aws': {
                'ec2_instances': {'t3.micro': 8.50, 't3.small': 17.00, 't3.medium': 34.00},
                's3_storage': 0.023,  # per GB
                'lambda_requests': 0.0000002  # per request
            },
            'azure': {
                'virtual_machines': {'Standard_B1s': 7.30, 'Standard_B2s': 29.20},
                'storage': 0.045  # per GB
            },
            'gcp': {
                'compute_instances': {'e2-micro': 6.11, 'e2-small': 12.23},
                'storage': 0.020  # per GB
            }
        }
        
        return estimates
        
    def _store_resource(self, resource: CloudResource):
        """Store resource in database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO cloud_resources 
            (id, name, provider, resource_type, region, status, metadata, cost_estimate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resource.id, resource.name, resource.provider, resource.resource_type,
            resource.region, resource.status, json.dumps(resource.metadata),
            resource.cost_estimate
        ))
        
        conn.commit()
        conn.close()
        
    def _store_deployment(self, deployment_id: str, config: DeploymentConfig, resources: List[CloudResource]):
        """Store deployment record"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO deployments 
            (id, name, provider, config, status, resources)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            deployment_id, config.name, config.provider,
            json.dumps(asdict(config)), 'deployed',
            json.dumps([r.id for r in resources])
        ))
        
        conn.commit()
        conn.close()

def main():
    """Demo of cloud services integration"""
    print("Cloud Services Integration Demo")
    print("=" * 35)
    
    # Initialize cloud manager
    cloud_manager = CloudServicesManager()
    
    print(f"\nAvailable cloud providers: {list(cloud_manager.providers.keys())}")
    
    if not cloud_manager.providers:
        print("No cloud providers configured. Please set up credentials.")
        return
    
    # List existing resources
    print("\nListing existing cloud resources:")
    all_resources = cloud_manager.list_all_resources()
    
    for provider, resources in all_resources.items():
        print(f"\n{provider.upper()} Resources ({len(resources)}):")
        for resource in resources[:3]:  # Show first 3
            print(f"  - {resource.name} ({resource.resource_type}) - {resource.status}")
    
    # Demo deployment configuration
    deployment_config = DeploymentConfig(
        name="mito-demo-app",
        provider=list(cloud_manager.providers.keys())[0],  # Use first available provider
        region="us-east-1",
        instance_type="t3.micro",
        environment="development",
        auto_scaling=False,
        load_balancer=False,
        database=False,
        storage=True,
        monitoring=True
    )
    
    print(f"\nDemo deployment configuration:")
    print(f"  Provider: {deployment_config.provider}")
    print(f"  Instance: {deployment_config.instance_type}")
    print(f"  Storage: {deployment_config.storage}")
    
    # Get cost estimates
    print("\nCost estimates:")
    estimates = cloud_manager.get_cost_estimates()
    for provider, costs in estimates.items():
        if provider in cloud_manager.providers:
            print(f"  {provider.upper()}:")
            for service, cost in costs.items():
                if isinstance(cost, dict):
                    for size, price in cost.items():
                        print(f"    {service} ({size}): ${price:.2f}/month")
                else:
                    print(f"    {service}: ${cost:.4f}/unit")

if __name__ == "__main__":
    main()