output "vpc_id" {
  description = "The ID of the VPC"
  value       = try(aws_vpc.main.id, "no-vpc-created")
}
