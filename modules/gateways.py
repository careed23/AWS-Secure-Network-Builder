import time
from botocore.exceptions import ClientError


class GatewayManager:
    """Manages Internet Gateways and NAT Gateways."""
    
    def __init__(self, ec2_client, logger):
        self.ec2_client = ec2_client
        self.logger = logger
    
    def create_internet_gateway(self, vpc_id, name):
        """Create and attach an Internet Gateway."""
        try:
            # Create IGW
            response = self.ec2_client.create_internet_gateway()
            igw_id = response['InternetGateway']['InternetGatewayId']
            
            # Tag the IGW
            self.ec2_client.create_tags(
                Resources=[igw_id],
                Tags=[{'Key': 'Name', 'Value': name}]
            )
            
            # Attach to VPC
            self.ec2_client.attach_internet_gateway(
                InternetGatewayId=igw_id,
                VpcId=vpc_id
            )
            
            self.logger.info(f"Internet Gateway created and attached: {igw_id}")
            return igw_id
            
        except ClientError as e:
            self.logger.error(f"Failed to create Internet Gateway: {e}")
            raise
    
    def create_nat_gateway(self, subnet_id, name):
        """Create a NAT Gateway with Elastic IP."""
        try:
            # Allocate Elastic IP
            eip_response = self.ec2_client.allocate_address(Domain='vpc')
            allocation_id = eip_response['AllocationId']
            elastic_ip = eip_response['PublicIp']
            
            # Create NAT Gateway
            response = self.ec2_client.create_nat_gateway(
                SubnetId=subnet_id,
                AllocationId=allocation_id
            )
            
            nat_gateway_id = response['NatGateway']['NatGatewayId']
            
            # Tag the NAT Gateway
            self.ec2_client.create_tags(
                Resources=[nat_gateway_id],
                Tags=[{'Key': 'Name', 'Value': name}]
            )
            
            # Wait for NAT Gateway to become available
            self.logger.info(f"Waiting for NAT Gateway to become available...")
            waiter = self.ec2_client.get_waiter('nat_gateway_available')
            waiter.wait(NatGatewayIds=[nat_gateway_id])
            
            self.logger.info(
                f"NAT Gateway created: {nat_gateway_id} with IP {elastic_ip}"
            )
            return nat_gateway_id, elastic_ip
            
        except ClientError as e:
            self.logger.error(f"Failed to create NAT Gateway: {e}")
            raise
    
    def delete_internet_gateway(self, igw_id, vpc_id):
        """Detach and delete an Internet Gateway."""
        try:
            # Detach from VPC
            self.ec2_client.detach_internet_gateway(
                InternetGatewayId=igw_id,
                VpcId=vpc_id
            )
            
            # Delete IGW
            self.ec2_client.delete_internet_gateway(InternetGatewayId=igw_id)
            self.logger.info(f"Internet Gateway {igw_id} deleted")
            
        except ClientError as e:
            self.logger.error(f"Failed to delete Internet Gateway: {e}")
            raise
    
    def delete_nat_gateway(self, nat_gateway_id):
        """Delete a NAT Gateway."""
        try:
            # Get NAT Gateway details to find EIP
            response = self.ec2_client.describe_nat_gateways(
                NatGatewayIds=[nat_gateway_id]
            )
            
            allocation_id = None
            if response['NatGateways']:
                nat = response['NatGateways'][0]
                if nat.get('NatGatewayAddresses'):
                    allocation_id = nat['NatGatewayAddresses'][0].get('AllocationId')
            
            # Delete NAT Gateway
            self.ec2_client.delete_nat_gateway(NatGatewayId=nat_gateway_id)
            self.logger.info(f"NAT Gateway {nat_gateway_id} deletion initiated")
            
            # Wait for deletion
            time.sleep(10)  # Give it some time to start deleting
            
            # Release Elastic IP if found
            if allocation_id:
                try:
                    self.ec2_client.release_address(AllocationId=allocation_id)
                    self.logger.info(f"Elastic IP {allocation_id} released")
                except ClientError as e:
                    self.logger.warning(f"Could not release EIP: {e}")
            
        except ClientError as e:
            self.logger.error(f"Failed to delete NAT Gateway: {e}")
            raise
