from modules.network import create_network
from modules.security import create_security_groups
from modules.database import create_aurora_database, create_rds_database, create_aurora_serverless_database
from modules.load_balancer import create_alb
from modules.ecs_compute import create_compute
from modules.dns import create_failover_record, create_latency_record
from modules.monitoring import create_monitoring
from modules.vpc_endpoints import create_vpc_endpoints


def create_region_stack(scope, id, tfvars, is_primary, shared_roles, shared_zone, provider):
    # Create Network and Security Groups
    net = create_network(scope, f"{id}-net", tfvars, provider)
    sg = create_security_groups(scope, f"{id}-sg", tfvars, net["vpc_id"], provider)

    # Initialize Database Information
    db_info = {}
    if tfvars["db_enabled"]:
        if tfvars["use_aurora_serverless"]:
            db_info = create_aurora_serverless_database(scope, f"{id}-rds", tfvars, net, sg, is_primary, provider, shared_zone)
        elif tfvars["use_rds"]:
            db_info = create_rds_database(scope, f"{id}-rds", tfvars, net, sg, is_primary, provider, shared_zone)
        elif tfvars["use_aurora"]:
            db_info = create_aurora_database(scope, f"{id}-aurora", tfvars, net, sg, is_primary, provider, shared_zone)

    # Create Load Balancer
    alb_info = create_alb(scope, f"{id}-alb", tfvars, net, sg, provider)

    # Create Compute Resources (ECS)
    compute_info = create_compute(
        scope, f"{id}-ecs", tfvars, net, sg, alb_info,
        shared_roles, provider, is_primary, db_info
    )

    # Create VPC Endpoints
    create_vpc_endpoints(
        scope, f"{id}-vpc-endpoints", tfvars, sg, net["vpc_id"],
        net["private_subnets"], net["public_route_table_id"], provider
    )

    # Create DNS Records based on DB configuration
    if tfvars["db_enabled"]:
        create_failover_record(scope, f"{id}-failover-dns", shared_zone, tfvars, alb_info["alb_dns_name"], is_primary, provider)
    else:
        create_latency_record(scope, f"{id}-dns", shared_zone, tfvars, alb_info["alb_dns_name"], provider)

    # Create Monitoring
    create_monitoring(scope, f"{id}-monitoring", tfvars, provider)

    # Return All Resources
    return {
        "network": net,
        "security_groups": sg,
        "database": db_info,
        "load_balancer": alb_info,
        "compute": compute_info
    }