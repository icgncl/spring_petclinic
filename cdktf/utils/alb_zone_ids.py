ALB_ZONE_IDS = {
    "us-east-1": "Z35SXDOTRQ7X7K",
    "us-west-1": "Z368ELLRRE2KJ0",
    "us-west-2": "Z1H1FL5HABSF5",
    "eu-north-1": "Z3QZZZJZ2Y4X9",
    "eu-west-1": "Z32O12XQLNTSW2",
    "eu-west-2": "ZHURV8PSTC4K8",
    "eu-west-3": "Z3Q77PNBQS71R4",
    "eu-central-1": "Z215JYRZR1TBD5",
    "ap-southeast-1": "Z1LMS91P8CMLE5",
    "ap-southeast-2": "Z1GM3OXH4ZPM65",
    "ap-northeast-1": "Z14GRHDCWA56QT",
    "ap-northeast-2": "Z3W03O7B5YMIYP",
    "ap-south-1": "ZP97RAFLXTNZK",
    "ca-central-1": "ZQSVJUPU6J1EY",
    "sa-east-1": "Z2P70J7HTTTPLU",
    # Add more as needed
}

def get_alb_hosted_zone_id(region: str) -> str:
    """
    Returns the ALB hosted zone ID for the given region.
    Raises an error if the region is not supported.
    """
    if region not in ALB_ZONE_IDS:
        raise ValueError(f"ALB hosted zone ID not found for region '{region}'. "
                         f"Please add it to ALB_ZONE_IDS in constants.py.")
    return ALB_ZONE_IDS[region]
