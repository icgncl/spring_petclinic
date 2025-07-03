from constructs import Construct
from cdktf import TerraformProvider
from cdktf_cdktf_provider_aws.db_subnet_group import DbSubnetGroup
from cdktf_cdktf_provider_aws.security_group_rule import SecurityGroupRule
from cdktf_cdktf_provider_aws.rds_global_cluster import RdsGlobalCluster
from cdktf_cdktf_provider_aws.rds_cluster import RdsCluster
from cdktf_cdktf_provider_aws.rds_cluster_instance import RdsClusterInstance
from cdktf_cdktf_provider_aws.db_instance import DbInstance
from cdktf_cdktf_provider_aws.rds_cluster import RdsClusterServerlessv2ScalingConfiguration
from modules.secret_manager import create_or_get_secret


def create_rds_database(scope: Construct, id: str, tfvars: dict, net: dict, sg: dict,
                        is_primary: bool, provider: TerraformProvider, shared_zone: str):
    db_port = tfvars["db_port"]
    private_subnets = [s.id for s in net["private_subnets"]]
    db_info ={}
    db_password_arn = create_or_get_secret(scope, f"{id}-db-secret", tfvars, provider)
    # Subnet Group
    subnet_group = DbSubnetGroup(scope, f"{id}-subnet-group",
        provider=provider,
        name=f"{tfvars['name']}-rds-subnet-group",
        subnet_ids=private_subnets
    )

    # Open DB Port for ECS
    for i, cidr in enumerate(tfvars["db_cidr_allow"]):
        SecurityGroupRule(scope, f"{id}-db-rule-{i}",
            provider=provider,
            type="ingress",
            security_group_id=sg["db_sg"].id,
            from_port=db_port,
            to_port=db_port,
            protocol="tcp",
            cidr_blocks=[cidr]
        )

    if is_primary:
        # Primary Multi-AZ RDS
        db = DbInstance(scope, f"{id}-rds-primary",
            provider=provider,
            identifier=f"{tfvars['name']}-primary",
            instance_class=tfvars["db_instance_class_rds"],
            engine="postgres",
            engine_version=tfvars["db_engine_version"],
            db_name=tfvars["db_name"],
            username=tfvars["db_username"],
            password=tfvars["db_password"],
            db_subnet_group_name=subnet_group.name,
            vpc_security_group_ids=[sg["db_sg"].id],
            multi_az=True,
            allocated_storage=20,
            port=db_port,
            skip_final_snapshot=True,
            publicly_accessible=False,
            lifecycle={"ignore_changes": ["password"]}
        )

        db_info = {
            "db_endpoint": db.address,
            "db_port": db_port,
            "db_name": tfvars["db_name"],
            "db_username": tfvars["db_username"],
            "db_password": tfvars["db_password"],
            "db_password_arn": db_password_arn
        }



    return db_info


def create_aurora_database(scope: Construct, id: str, tfvars: dict, net: dict, sg: dict,
                    is_primary: bool, provider: TerraformProvider, shared_zone: str):

    db_port = tfvars["db_port"]
    private_subnets = [s.id for s in net["private_subnets"]]
    db_password_arn = create_or_get_secret(scope, f"{id}-db-secret", tfvars, provider)

    # Create subnet group for the DB cluster
    subnet_group = DbSubnetGroup(scope, f"{id}-subnet-group",
        provider=provider,
        name=f"{tfvars['name']}-db-subnet-group",
        subnet_ids=private_subnets
    )

    for i, cidr in enumerate(tfvars["db_cidr_allow"]):
        SecurityGroupRule(scope, f"{id}-db-rule-{i}",
            provider=provider,
            type="ingress",
            security_group_id=sg["db_sg"].id,
            from_port=db_port,
            to_port=db_port,
            protocol="tcp",
            cidr_blocks=[cidr]
        )

    if is_primary:
        global_cluster = RdsGlobalCluster(scope, f"{id}-global",
            provider=provider,
            global_cluster_identifier=f"{tfvars['name']}-global",
            engine="aurora-postgresql",
            engine_version=tfvars["db_engine_aurora_version"]
        )

    cluster = RdsCluster(scope, f"{id}-cluster",
        provider=provider,
        cluster_identifier=f"{tfvars['name']}-cluster",
        engine="aurora-postgresql",
        engine_version=tfvars["db_engine_aurora_version"],
        master_username=tfvars["db_username"] if is_primary else None,
        master_password=tfvars["db_password"] if is_primary else None,
        database_name=tfvars["db_name"] if is_primary else None,
        db_subnet_group_name=subnet_group.name,
        vpc_security_group_ids=[sg["db_sg"].id],
        port=db_port,
        global_cluster_identifier=f"{tfvars['name']}-global",
        source_region=None if is_primary else tfvars["primary_region"],
        skip_final_snapshot=True,
        lifecycle={"ignore_changes": ["master_password"]}
    )

    instance = RdsClusterInstance(scope, f"{id}-instance",
        provider=provider,
        cluster_identifier=cluster.id,
        instance_class=tfvars["db_instance_class_aurora"],
        engine="aurora-postgresql",
        engine_version=tfvars["db_engine_aurora_version"],
        identifier=f"{tfvars['name']}-db-instance"
    )

    return {
        "db_endpoint": cluster.endpoint if is_primary else cluster.reader_endpoint,
        "db_port": db_port,
        "db_name": tfvars["db_name"],
        "db_username": tfvars["db_username"],
        "db_password": cluster.master_user_secret.get(0).secret_arn,
        "db_password_arn": db_password_arn
    }


def create_aurora_serverless_database(scope: Construct, id: str, tfvars: dict, net: dict, sg: dict,
    is_primary: bool, provider: TerraformProvider, shared_zone: str):

    db_port = tfvars["db_port"]
    private_subnets = [s.id for s in net["private_subnets"]]
    db_password_arn = create_or_get_secret(scope, f"{id}-db-secret", tfvars, provider)

    # Subnet Group
    subnet_group = DbSubnetGroup(scope, f"{id}-subnet-group",
        provider=provider,
        name=f"{tfvars['name']}-aurora-subnet-group",
        subnet_ids=private_subnets
    )

    # Security Group Rules
    for i, cidr in enumerate(tfvars["db_cidr_allow"]):
        SecurityGroupRule(scope, f"{id}-db-rule-{i}",
            provider=provider,
            type="ingress",
            security_group_id=sg["db_sg"].id,
            from_port=db_port,
            to_port=db_port,
            protocol="tcp",
            cidr_blocks=[cidr]
        )

    # Global cluster (only needed for primary region)
    if is_primary:
        RdsGlobalCluster(scope, f"{id}-global-cluster",
            provider=provider,
            global_cluster_identifier=f"{tfvars['name']}-global",
            engine="aurora-postgresql",
            engine_version=tfvars["db_engine_aurora_version"]
        )

    # Aurora Serverless v2 Cluster
    cluster = RdsCluster(scope, f"{id}-cluster",
        provider=provider,
        cluster_identifier=f"{tfvars['name']}-cluster",
        engine="aurora-postgresql",
        engine_version=tfvars["db_engine_aurora_version"],
        engine_mode="provisioned",  # REQUIRED for Serverless v2
        db_subnet_group_name=subnet_group.name,
        vpc_security_group_ids=[sg["db_sg"].id],
        port=db_port,
        master_username=tfvars["db_username"],
        master_password=tfvars["db_password"],
        database_name=tfvars["db_name"] if is_primary else None,
        global_cluster_identifier=f"{tfvars['name']}-global" if is_primary else None,
        source_region=None if is_primary else tfvars["primary_region"],
        skip_final_snapshot=True,
        serverlessv2_scaling_configuration=RdsClusterServerlessv2ScalingConfiguration(
            min_capacity=tfvars.get("aurora_min_acu", 0.5),
            max_capacity=tfvars.get("aurora_max_acu", 4.0)
        ),
        lifecycle={"ignore_changes": ["master_password"]}
    )

    # Aurora Serverless v2 still requires one cluster instance with db.serverless
    instance = RdsClusterInstance(scope, f"{id}-instance",
        provider=provider,
        cluster_identifier=cluster.id,
        instance_class="db.serverless",
        engine="aurora-postgresql",
        engine_version=tfvars["db_engine_aurora_version"],
        identifier=f"{tfvars['name']}-instance"
    )

    return {
        "db_endpoint": cluster.endpoint if is_primary else cluster.reader_endpoint,
        "db_port": db_port,
        "db_name": tfvars["db_name"],
        "db_username": tfvars["db_username"],
        "db_password_arn": db_password_arn
    }
