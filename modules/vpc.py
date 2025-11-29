import time
from botocore.exceptions import ClientError


class VPCManager:
    """Manages VPC creation, modification, and deletion."""
    
    def __init__(self, ec2_client, ec2_resource, logger):
        self.ec2_client = ec2_client
        self.ec2_resource = ec2_resource
        self.logger = logger
    
    def create_vpc(self, cidr_block, vpc_name, enable_dns_hostnames=True, 
                   enable_dns_support=True, tags=None):
        """Create a new VPC with specified configuration."""
        try:
            # Create VPC
            vpc = self.ec2_resource.create_vpc(CidrBlock=cidr_block)
            vpc.wait_until_available()
            
            # Enable DNS settings
            if enable_dns_hostnames:
                vpc.modify_attribute(EnableDnsHostnames={'Value': True})
            if enable_dns_support:
                vpc.modify_attribute(EnableDnsSupport={'Value': True})
            
            # Apply tags
            vpc_tags = [
                {'Key': 'Name', 'Value': vpc_name}
            ]
            
            if tags:
                for key, value in tags.items():
                    vpc_tags.append({'Key': key, 'Value': value})
            
            vpc.create_tags(Tags=vpc_tags)
            
            self.logger.info(f"VPC created with ID: {vpc.id}")
            return vpc.id
            
        except ClientError as e:
            self.logger.error(f"Failed to create VPC: {e}")
            raise
    
    def create_subnet(self, vpc_id, cidr_block, availability_zone, name, subnet_type):
        """Create a subnet within the VPC."""
        try:
            subnet = self.ec2_resource.create_subnet(
                VpcId=vpc_id,
                CidrBlock=cidr_block,
                AvailabilityZone=availability_zone
            )
            
            # Enable auto-assign public IP for public subnets
            if subnet_type == 'public':
                self.ec2_client.modify_subnet_attribute(
                    SubnetId=subnet.id,
                    MapPublicIpOnLaunch={'Value': True}
                )
            
            # Tag the subnet
            subnet.create_tags(Tags=[
                {'Key': 'Name', 'Value': name},
                {'Key': 'Type', 'Value': subnet_type}
            ])
            
            return subnet.id
            
        except ClientError as e:
            self.logger.error(f"Failed to create subnet: {e}")
            raise
    
    def create_route_table(self, vpc_id, name):
        """Create a route table for the VPC."""
        try:
            route_table = self.ec2_resource.create_route_table(VpcId=vpc_id)
            
            route_table.create_tags(Tags=[
                {'Key': 'Name', 'Value': name}
            ])
            
            return route_table.id
            
        except ClientError as e:
            self.logger.error(f"Failed to create route table: {e}")
            raise
    
    def add_route(self, route_table_id, destination_cidr, gateway_id=None, 
                  nat_gateway_id=None):
        """Add a route to a route table."""
        try:
            route_params = {
                'RouteTableId': route_table_id,
                'DestinationCidrBlock': destination_cidr
            }
            
            if gateway_id:
                route_params['GatewayId'] = gateway_id
            elif nat_gateway_id:
                route_params['NatGatewayId'] = nat_gateway_id
            
            self.ec2_client.create_route(**route_params)
            
        except ClientError as e:
            self.logger.error(f"Failed to add route: {e}")
            raise
    
    def associate_route_table(self, subnet_id, route_table_id):
        """Associate a route table with a subnet."""
        try:
            self.ec2_client.associate_route_table(
                SubnetId=subnet_id,
                RouteTableId=route_table_id
            )
        except ClientError as e:
            self.logger.error(f"Failed to associate route table: {e}")
            raise
    
    def delete_vpc(self, vpc_id):
        """Delete a VPC."""
        try:
            self.ec2_client.delete_vpc(VpcId=vpc_id)
            self.logger.info(f"VPC {vpc_id} deleted")
        except ClientError as e:
            self.logger.error(f"Failed to delete VPC: {e}")
            raise
    
    def delete_subnet(self, subnet_id):
        """Delete a subnet."""
        try:
            self.ec2_client.delete_subnet(SubnetId=subnet_id)
            self.logger.info(f"Subnet {subnet_id} deleted")
        except ClientError as e:
            self.logger.error(f"Failed to delete subnet: {e}")
            raise
    
    def delete_route_table(self, route_table_id):
        """Delete a route table."""
        try:
            self.ec2_client.delete_route_table(RouteTableId=route_table_id)
            self.logger.info(f"Route table {route_table_id} deleted")
        except ClientError as e:
            self.logger.error(f"Failed to delete route table: {e}")
            raise
