#!/usr/bin/env python3
"""
AWS Secure Network Builder - Main Execution Script
Automates the deployment of secure, multi-tier AWS network infrastructure
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
import yaml
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from modules.vpc import VPCManager
from modules.security import SecurityManager
from modules.gateways import GatewayManager
from modules.utils import setup_logging, validate_cidr, load_config


class AWSNetworkBuilder:
    """Main orchestrator for AWS network infrastructure deployment."""
    
    def __init__(self, config_path, dry_run=False, verbose=False):
        self.config_path = config_path
        self.dry_run = dry_run
        self.verbose = verbose
        self.state = {
            'vpc_id': None,
            'subnets': {},
            'security_groups': {},
            'route_tables': {},
            'gateways': {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Setup logging
        self.logger = setup_logging(verbose)
        
        # Load configuration
        self.config = load_config(config_path)
        self.logger.info(f"Loaded configuration from {config_path}")
        
        # Initialize AWS session
        try:
            self.session = boto3.Session(region_name=self.config['region'])
            self.ec2_client = self.session.client('ec2')
            self.ec2_resource = self.session.resource('ec2')
            self.logger.info(f"✅ AWS credentials validated for region {self.config['region']}")
        except NoCredentialsError:
            self.logger.error("❌ AWS credentials not found. Run 'aws configure' first.")
            sys.exit(1)
        
        # Initialize managers
        self.vpc_manager = VPCManager(self.ec2_client, self.ec2_resource, self.logger)
        self.security_manager = SecurityManager(self.ec2_client, self.logger)
        self.gateway_manager = GatewayManager(self.ec2_client, self.logger)
    
    def deploy(self):
        """Execute the full deployment workflow."""
        self.logger.info("🚀 Starting AWS Secure Network Builder deployment...")
        
        if self.dry_run:
            self.logger.info("🔍 Running in DRY-RUN mode - no resources will be created")
            return self._dry_run_validation()
        
        try:
            # Step 1: Create VPC
            self._create_vpc()
            
            # Step 2: Create Internet Gateway
            self._create_internet_gateway()
            
            # Step 3: Create Route Tables
            self._create_route_tables()
            
            # Step 4: Create Subnets
            self._create_subnets()
            
            # Step 5: Create NAT Gateway if needed
            self._create_nat_gateway()
            
            # Step 6: Apply Security Groups
            self._apply_security_groups()
            
            # Step 7: Export state
            self._export_state()
            
            self.logger.info("✅ Deployment completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Deployment failed: {str(e)}")
            self.logger.exception("Full traceback:")
            return False
    
    def _create_vpc(self):
        """Create VPC with specified configuration."""
        self.logger.info(f"Creating VPC: {self.config['vpc_name']}")
        
        vpc_id = self.vpc_manager.create_vpc(
            cidr_block=self.config['cidr'],
            vpc_name=self.config['vpc_name'],
            enable_dns_hostnames=self.config.get('enable_dns_hostnames', True),
            enable_dns_support=self.config.get('enable_dns_support', True),
            tags=self.config.get('tags', {})
        )
        
        self.state['vpc_id'] = vpc_id
        self.logger.info(f"✅ VPC created: {vpc_id}")
    
    def _create_internet_gateway(self):
        """Create and attach Internet Gateway."""
        self.logger.info("Creating Internet Gateway...")
        
        igw_id = self.gateway_manager.create_internet_gateway(
            vpc_id=self.state['vpc_id'],
            name=f"{self.config['vpc_name']}-igw"
        )
        
        self.state['gateways']['internet_gateway'] = igw_id
        self.logger.info(f"✅ Internet Gateway created: {igw_id}")
    
    def _create_route_tables(self):
        """Create public and private route tables."""
        self.logger.info("Creating route tables...")
        
        # Public route table
        public_rt = self.vpc_manager.create_route_table(
            vpc_id=self.state['vpc_id'],
            name=f"{self.config['vpc_name']}-public-rt"
        )
        
        # Add route to Internet Gateway
        self.vpc_manager.add_route(
            route_table_id=public_rt,
            destination_cidr='0.0.0.0/0',
            gateway_id=self.state['gateways']['internet_gateway']
        )
        
        self.state['route_tables']['public'] = public_rt
        
        # Private route table
        private_rt = self.vpc_manager.create_route_table(
            vpc_id=self.state['vpc_id'],
            name=f"{self.config['vpc_name']}-private-rt"
        )
        
        self.state['route_tables']['private'] = private_rt
        self.logger.info("✅ Route tables created")
    
    def _create_subnets(self):
        """Create all configured subnets."""
        self.logger.info("Creating subnets...")
        
        for subnet_config in self.config['subnets']:
            subnet_id = self.vpc_manager.create_subnet(
                vpc_id=self.state['vpc_id'],
                cidr_block=subnet_config['cidr'],
                availability_zone=subnet_config['az'],
                name=subnet_config['name'],
                subnet_type=subnet_config['type']
            )
            
            # Associate with appropriate route table
            rt_id = self.state['route_tables'].get(subnet_config['type'])
            if rt_id:
                self.vpc_manager.associate_route_table(subnet_id, rt_id)
            
            self.state['subnets'][subnet_config['name']] = {
                'id': subnet_id,
                'cidr': subnet_config['cidr'],
                'az': subnet_config['az'],
                'type': subnet_config['type']
            }
            
            self.logger.info(f"✅ Subnet created: {subnet_config['name']} ({subnet_id})")
    
    def _create_nat_gateway(self):
        """Create NAT Gateway if enabled."""
        nat_config = self.config.get('nat_gateway', {})
        
        if not nat_config.get('enabled', False):
            self.logger.info("⏭️ NAT Gateway disabled in config")
            return
        
        self.logger.info("Creating NAT Gateway...")
        
        # Find a public subnet for NAT Gateway
        public_subnet = None
        for subnet_name, subnet_data in self.state['subnets'].items():
            if subnet_data['type'] == 'public':
                public_subnet = subnet_data['id']
                break
        
        if not public_subnet:
            self.logger.warning("⚠️ No public subnet found for NAT Gateway")
            return
        
        nat_id, eip = self.gateway_manager.create_nat_gateway(
            subnet_id=public_subnet,
            name=f"{self.config['vpc_name']}-nat"
        )
        
        # Add route to private route table
        self.vpc_manager.add_route(
            route_table_id=self.state['route_tables']['private'],
            destination_cidr='0.0.0.0/0',
            nat_gateway_id=nat_id
        )
        
        self.state['gateways']['nat_gateway'] = {
            'id': nat_id,
            'elastic_ip': eip
        }
        self.logger.info(f"✅ NAT Gateway created: {nat_id}")
    
    def _apply_security_groups(self):
        """Create and configure security groups."""
        sg_config = self.config.get('security_groups', {})
        
        if not sg_config:
            self.logger.info("⏭️ No security groups defined in config")
            return
        
        self.logger.info("Creating security groups...")
        
        for sg_name, rules in sg_config.items():
            sg_id = self.security_manager.create_security_group(
                vpc_id=self.state['vpc_id'],
                name=sg_name,
                description=f"Security group for {sg_name}"
            )
            
            # Add ingress rules
            for rule in rules:
                self.security_manager.add_ingress_rule(
                    security_group_id=sg_id,
                    protocol=rule['protocol'],
                    from_port=rule['from_port'],
                    to_port=rule['to_port'],
                    cidr=rule['cidr']
                )
            
            self.state['security_groups'][sg_name] = sg_id
            self.logger.info(f"✅ Security group created: {sg_name} ({sg_id})")
    
    def _export_state(self):
        """Export deployment state to JSON file."""
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        state_file = output_dir / f"{self.config['vpc_name']}-state.json"
        
        with open(state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
        
        self.logger.info(f"💾 State exported to: {state_file}")
    
    def _dry_run_validation(self):
        """Validate configuration without creating resources."""
        self.logger.info("Validating configuration...")
        
        # Validate CIDR blocks
        if not validate_cidr(self.config['cidr']):
            self.logger.error(f"❌ Invalid VPC CIDR: {self.config['cidr']}")
            return False
        
        for subnet in self.config['subnets']:
            if not validate_cidr(subnet['cidr']):
                self.logger.error(f"❌ Invalid subnet CIDR: {subnet['cidr']}")
                return False
        
        self.logger.info("✅ Configuration is valid")
        return True
    
    def teardown(self, state_file):
        """Remove all resources defined in state file."""
        self.logger.info("🗑️ Starting infrastructure teardown...")
        
        with open(state_file) as f:
            state = json.load(f)
        
        try:
            # Delete in reverse order
            self._delete_nat_gateways(state)
            self._delete_internet_gateways(state)
            self._delete_subnets(state)
            self._delete_route_tables(state)
            self._delete_security_groups(state)
            self._delete_vpc(state)
            
            self.logger.info("✅ Teardown completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Teardown failed: {str(e)}")
            return False
    
    def _delete_nat_gateways(self, state):
        """Delete NAT Gateways."""
        if 'nat_gateway' in state.get('gateways', {}):
            nat_id = state['gateways']['nat_gateway']['id']
            self.logger.info(f"Deleting NAT Gateway: {nat_id}")
            self.gateway_manager.delete_nat_gateway(nat_id)
    
    def _delete_internet_gateways(self, state):
        """Delete Internet Gateways."""
        if 'internet_gateway' in state.get('gateways', {}):
            igw_id = state['gateways']['internet_gateway']
            self.logger.info(f"Deleting Internet Gateway: {igw_id}")
            self.gateway_manager.delete_internet_gateway(igw_id, state['vpc_id'])
    
    def _delete_subnets(self, state):
        """Delete all subnets."""
        for subnet_name, subnet_data in state.get('subnets', {}).items():
            self.logger.info(f"Deleting subnet: {subnet_name}")
            self.vpc_manager.delete_subnet(subnet_data['id'])
    
    def _delete_route_tables(self, state):
        """Delete route tables."""
        for rt_name, rt_id in state.get('route_tables', {}).items():
            self.logger.info(f"Deleting route table: {rt_name}")
            self.vpc_manager.delete_route_table(rt_id)
    
    def _delete_security_groups(self, state):
        """Delete security groups."""
        for sg_name, sg_id in state.get('security_groups', {}).items():
            self.logger.info(f"Deleting security group: {sg_name}")
            self.security_manager.delete_security_group(sg_id)
    
    def _delete_vpc(self, state):
        """Delete VPC."""
        vpc_id = state.get('vpc_id')
        if vpc_id:
            self.logger.info(f"Deleting VPC: {vpc_id}")
            self.vpc_manager.delete_vpc(vpc_id)


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description='AWS Secure Network Builder - Automate VPC deployments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy infrastructure
  python3 builder.py --config configs/prod-vpc.yaml
  
  # Validate configuration without deploying
  python3 builder.py --config configs/prod-vpc.yaml --dry-run
  
  # Deploy with verbose logging
  python3 builder.py --config configs/prod-vpc.yaml --verbose
  
  # Teardown infrastructure
  python3 builder.py --teardown --state-file output/prod-secure-network-state.json
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to YAML configuration file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate configuration without creating resources'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--teardown',
        action='store_true',
        help='Delete all resources from state file'
    )
    parser.add_argument(
        '--state-file',
        type=str,
        help='Path to state file for teardown'
    )
    
    args = parser.parse_args()
    
    # Handle teardown mode
    if args.teardown:
        if not args.state_file:
            print("Error: --state-file required for teardown")
            print("Example: python3 builder.py --teardown --state-file output/vpc-state.json")
            sys.exit(1)
        
        # Create a dummy builder just for teardown
        builder = AWSNetworkBuilder(
            config_path=args.config if args.config else 'configs/prod-vpc.yaml',
            verbose=args.verbose
        )
        success = builder.teardown(args.state_file)
        sys.exit(0 if success else 1)
    
    # Handle deployment mode
    if not args.config:
        print("Error: --config required for deployment")
        print("Example: python3 builder.py --config configs/prod-vpc.yaml")
        sys.exit(1)
    
    builder = AWSNetworkBuilder(
        config_path=args.config,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    
    success = builder.deploy()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
