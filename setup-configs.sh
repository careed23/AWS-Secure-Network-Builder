#!/bin/bash
echo "Creating clean configuration files..."
mkdir -p configs

cat > configs/prod-vpc.yaml << 'EOFPROD'
vpc_name: "prod-secure-network"
cidr: "10.0.0.0/16"
region: "us-east-1"
enable_dns_hostnames: true
enable_dns_support: true

tags:
  Environment: "Production"
  ManagedBy: "AWS-Secure-Builder"
  CostCenter: "Engineering"

subnets:
  - name: "public-web-1a"
    cidr: "10.0.1.0/24"
    type: "public"
    az: "us-east-1a"
    
  - name: "public-web-1b"
    cidr: "10.0.2.0/24"
    type: "public"
    az: "us-east-1b"
  
  - name: "private-app-1a"
    cidr: "10.0.10.0/24"
    type: "private"
    az: "us-east-1a"
    
  - name: "private-app-1b"
    cidr: "10.0.11.0/24"
    type: "private"
    az: "us-east-1b"
  
  - name: "private-db-1a"
    cidr: "10.0.20.0/24"
    type: "private"
    az: "us-east-1a"
    
  - name: "private-db-1b"
    cidr: "10.0.21.0/24"
    type: "private"
    az: "us-east-1b"

nat_gateway:
  enabled: true
  availability_zone: "us-east-1a"

security_groups:
  web_tier:
    - protocol: "tcp"
      from_port: 443
      to_port: 443
      cidr: "0.0.0.0/0"
    - protocol: "tcp"
      from_port: 80
      to_port: 80
      cidr: "0.0.0.0/0"
  
  app_tier:
    - protocol: "tcp"
      from_port: 8080
      to_port: 8080
      cidr: "10.0.0.0/16"
  
  db_tier:
    - protocol: "tcp"
      from_port: 3306
      to_port: 3306
      cidr: "10.0.10.0/23"
EOFPROD

echo "✅ Configuration files created successfully!"
