from constructs import Construct
from cdktf import TerraformProvider, Token
from cdktf_cdktf_provider_aws.vpc_endpoint import VpcEndpoint
from cdktf_cdktf_provider_aws.security_group import SecurityGroup, SecurityGroupIngress, SecurityGroupEgress

def create_vpc_endpoints(scope: Construct, id: str, tfvars: dict, sg: dict, vpc_id: str, private_subnet_ids: list, route_table_id: str, provider: TerraformProvider):
    # Security Group for VPC Interface Endpoints (ECR access)
    endpoint_sg = SecurityGroup(scope, f"{id}-vpce-sg",
        provider=provider,
        name=f"{tfvars['name']}-vpce-sg",
        vpc_id=vpc_id,
        ingress=[SecurityGroupIngress(
            from_port=443,
            to_port=443,
            protocol="tcp",
            security_groups=[sg["ecs_sg"].id]
        )],
        egress=[SecurityGroupEgress(
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"]
        )]
    )

    # ECR API endpoint (Interface)
    VpcEndpoint(scope, f"{id}-ecr-api",
        provider=provider,
        vpc_id=vpc_id,
        service_name=f"com.amazonaws.{tfvars['region']}.ecr.api",
        vpc_endpoint_type="Interface",
        subnet_ids=Token.as_list([s.id for s in private_subnet_ids]),
        security_group_ids=[endpoint_sg.id]
    )

    # ECR DKR endpoint (Interface)
    VpcEndpoint(scope, f"{id}-ecr-dkr",
        provider=provider,
        vpc_id=vpc_id,
        service_name=f"com.amazonaws.{tfvars['region']}.ecr.dkr",
        vpc_endpoint_type="Interface",
        subnet_ids=Token.as_list([s.id for s in private_subnet_ids]),
        security_group_ids=[endpoint_sg.id]
    )

    # S3 endpoint (Gateway)
    VpcEndpoint(scope, f"{id}-s3",
        provider=provider,
        vpc_id=vpc_id,
        service_name=f"com.amazonaws.{tfvars['region']}.s3",
        vpc_endpoint_type="Gateway",
        route_table_ids=[route_table_id]
    )

    return {
        "vpce_sg": endpoint_sg
    }
