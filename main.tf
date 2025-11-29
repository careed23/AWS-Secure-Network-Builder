# 1. Create the VPC
resource "aws_vpc" "main_network" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = "Production-VPC"
  }
}

# 2. Create a Public Subnet
resource "aws_subnet" "public_subnet_1" {
  vpc_id            = aws_vpc.main_network.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "Public-Subnet-1"
  }
}

# 3. Create a Private Subnet (Secure)
resource "aws_subnet" "private_subnet_1" {
  vpc_id            = aws_vpc.main_network.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "Private-Subnet-1"
  }
}

# 4. Create Internet Gateway (So public subnet has internet)
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main_network.id
}

# 5. Create Route Table for Public Subnet
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main_network.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
}

# 6. Associate Route Table with Public Subnet
resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.public_subnet_1.id
  route_table_id = aws_route_table.public_rt.id
}
