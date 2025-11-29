from botocore.exceptions import ClientError


class SecurityManager:
    """Manages Security Groups and Network ACLs."""
    
    def __init__(self, ec2_client, logger):
        self.ec2_client = ec2_client
        self.logger = logger
    
    def create_security_group(self, vpc_id, name, description):
        """Create a security group."""
        try:
            response = self.ec2_client.create_security_group(
                GroupName=name,
                Description=description,
                VpcId=vpc_id
            )
            
            sg_id = response['GroupId']
            
            # Tag the security group
            self.ec2_client.create_tags(
                Resources=[sg_id],
                Tags=[{'Key': 'Name', 'Value': name}]
            )
            
            self.logger.info(f"Security group created: {sg_id}")
            return sg_id
            
        except ClientError as e:
            self.logger.error(f"Failed to create security group: {e}")
            raise
    
    def add_ingress_rule(self, security_group_id, protocol, from_port, to_port, cidr):
        """Add an ingress rule to a security group."""
        try:
            self.ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[{
                    'IpProtocol': protocol,
                    'FromPort': from_port,
                    'ToPort': to_port,
                    'IpRanges': [{'CidrIp': cidr}]
                }]
            )
            
            self.logger.info(
                f"Added ingress rule: {protocol} {from_port}-{to_port} from {cidr}"
            )
            
        except ClientError as e:
            if 'InvalidPermission.Duplicate' in str(e):
                self.logger.warning(f"Rule already exists, skipping...")
            else:
                self.logger.error(f"Failed to add ingress rule: {e}")
                raise
    
    def add_egress_rule(self, security_group_id, protocol, from_port, to_port, cidr):
        """Add an egress rule to a security group."""
        try:
            self.ec2_client.authorize_security_group_egress(
                GroupId=security_group_id,
                IpPermissions=[{
                    'IpProtocol': protocol,
                    'FromPort': from_port,
                    'ToPort': to_port,
                    'IpRanges': [{'CidrIp': cidr}]
                }]
            )
            
            self.logger.info(
                f"Added egress rule: {protocol} {from_port}-{to_port} to {cidr}"
            )
            
        except ClientError as e:
            if 'InvalidPermission.Duplicate' in str(e):
                self.logger.warning(f"Rule already exists, skipping...")
            else:
                self.logger.error(f"Failed to add egress rule: {e}")
                raise
    
    def delete_security_group(self, security_group_id):
        """Delete a security group."""
        try:
            self.ec2_client.delete_security_group(GroupId=security_group_id)
            self.logger.info(f"Security group {security_group_id} deleted")
        except ClientError as e:
            self.logger.error(f"Failed to delete security group: {e}")
            raise
