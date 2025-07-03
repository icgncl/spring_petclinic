from constructs import Construct
from cdktf_cdktf_provider_aws.security_group import SecurityGroup, SecurityGroupIngress, SecurityGroupEgress
from cdktf import TerraformProvider


def create_security_groups(scope: Construct, id: str, tfvars: dict, vpc_id: str, provider: TerraformProvider):
    alb_sg = SecurityGroup(scope, f"{id}-alb",
        provider=provider,
        name=f"{tfvars['environment']}-alb-sg",
        vpc_id=vpc_id,
        ingress=[
            SecurityGroupIngress(from_port=tfvars["alb_listener_port"], to_port=tfvars["alb_listener_port"], protocol="tcp", cidr_blocks=tfvars["alb_sg_ingress_cidrs"]),
            SecurityGroupIngress(from_port=tfvars["alb_test_listener_port"], to_port=tfvars["alb_test_listener_port"], protocol="tcp", cidr_blocks=tfvars["alb_sg_ingress_cidrs"]),
            SecurityGroupIngress(from_port=tfvars["container_port"], to_port=tfvars["container_port"], protocol="tcp", cidr_blocks=tfvars["alb_sg_ingress_cidrs"])
        ],
        egress=[SecurityGroupEgress(from_port=0, to_port=0, protocol="-1", cidr_blocks=["0.0.0.0/0"])]
    )

    ecs_sg = SecurityGroup(scope, f"{id}-ecs",
        provider=provider,
        name=f"{tfvars['environment']}-ecs-sg",
        vpc_id=vpc_id,
        ingress=[SecurityGroupIngress(from_port=tfvars["container_port"], to_port=tfvars["container_port"], protocol="tcp", security_groups=[alb_sg.id])],
        egress=[SecurityGroupEgress(from_port=0, to_port=0, protocol="-1", cidr_blocks=["0.0.0.0/0"])]
    )

    db_sg = SecurityGroup(scope, f"{id}-db",
        provider=provider,
        name=f"{tfvars['environment']}-db-sg",
        vpc_id=vpc_id,
        ingress=[SecurityGroupIngress(from_port=5432, to_port=5432, protocol="tcp", security_groups=[ecs_sg.id])]
    )

    return {
        "alb_sg": alb_sg,
        "ecs_sg": ecs_sg,
        "db_sg": db_sg
    }
