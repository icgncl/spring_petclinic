from constructs import Construct
from cdktf_cdktf_provider_aws.route53_record import Route53Record
from utils.alb_zone_ids import get_alb_hosted_zone_id
from cdktf import TerraformProvider
from cdktf_cdktf_provider_aws.route53_zone import Route53Zone


def create_failover_record(scope: Construct, id: str, zone, tfvars: dict, alb_dns: str, is_primary: bool, provider: TerraformProvider):
    alb_zone_id = get_alb_hosted_zone_id(tfvars["region"])
    record_type = "PRIMARY" if is_primary else "SECONDARY"
    Route53Record(scope, f"{id}-failover",
        provider=provider,
        name=f"{tfvars['record_name']}.{tfvars['domain_name']}",
        type="A",
        zone_id=zone.zone_id,
        set_identifier=record_type.lower(),
        failover_routing_policy={"type": record_type},
        alias={"name": alb_dns, "zone_id": alb_zone_id, "evaluate_target_health": True}
    )


def create_latency_record(scope: Construct, id: str, zone, tfvars: dict, alb_dns: str, provider: TerraformProvider):
    alb_zone_id = get_alb_hosted_zone_id(tfvars["region"])
    
    Route53Record(scope, f"{id}-latency-{tfvars['region']}",
        provider=provider,
        name=f"{tfvars['record_name']}.{tfvars['domain_name']}",
        type="A",
        zone_id=zone.zone_id,
        set_identifier=tfvars["region"],  # must be unique for each region
        latency_routing_policy={
            "region": tfvars["region"]
        },
        alias={
            "name": alb_dns,
            "zone_id": alb_zone_id,
            "evaluate_target_health": True
        }
    )

def create_dns_zone(scope: Construct, id: str, tfvars: dict):

    zone = Route53Zone(scope, f"{id}-zone", name=tfvars["domain_name"])
    
    return zone