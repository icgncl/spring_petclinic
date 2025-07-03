from constructs import Construct
from cdktf_cdktf_provider_aws.cloudwatch_metric_alarm import CloudwatchMetricAlarm
from cdktf import TerraformProvider


def create_monitoring(scope: Construct, id_prefix: str, tfvars: dict, provider: TerraformProvider):
    alarms = []

    CloudwatchMetricAlarm(scope, f"{id_prefix}-ecs-cpu-alarm",
        provider=provider,
        alarm_name=f"{tfvars['name']}-ECSHighCPU",
        comparison_operator="GreaterThanThreshold",
        evaluation_periods=2,
        metric_name="CPUUtilization",
        namespace="AWS/ECS",
        period=300,
        statistic="Average",
        threshold=80,
        alarm_description="ECS CPU usage above 80%",
        dimensions={
            "ClusterName": f"{tfvars['name']}-cluster",
            "ServiceName": f"{tfvars['name']}-svc"
        }
    )

    CloudwatchMetricAlarm(scope, f"{id_prefix}-rds-lag-alarm",
        provider=provider,
        alarm_name=f"{tfvars['name']}-RDSReplicaLag",
        comparison_operator="GreaterThanThreshold",
        evaluation_periods=1,
        metric_name="AuroraReplicaLag",
        namespace="AWS/RDS",
        period=60,
        statistic="Maximum",
        threshold=30,
        alarm_description="RDS replica lag over 30 seconds",
        dimensions={
            "DBClusterIdentifier": f"{tfvars['name']}-cluster"
        }
    )
