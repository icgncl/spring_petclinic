from constructs import Construct
from cdktf_cdktf_provider_aws.vpc import Vpc
from cdktf_cdktf_provider_aws.subnet import Subnet
from cdktf_cdktf_provider_aws.internet_gateway import InternetGateway
from cdktf_cdktf_provider_aws.route_table import RouteTable
from cdktf_cdktf_provider_aws.route import Route
from cdktf_cdktf_provider_aws.route_table_association import RouteTableAssociation
from cdktf import Fn, TerraformProvider
from cdktf_cdktf_provider_aws.eip import Eip
from cdktf_cdktf_provider_aws.nat_gateway import NatGateway


def create_network(scope: Construct, id: str, tfvars: dict, provider: TerraformProvider):
    vpc = Vpc(scope, f"{id}-vpc",
        provider=provider,
        cidr_block=tfvars["vpc_cidr"],
        enable_dns_support=True,
        enable_dns_hostnames=True
    )

    igw = InternetGateway(scope, f"{id}-igw",
        provider=provider,
        vpc_id=vpc.id
    )

    # Public Route Table
    public_rt = RouteTable(scope, f"{id}-public-rt",
        provider=provider,
        vpc_id=vpc.id
    )

    Route(scope, f"{id}-public-route",
        provider=provider,
        route_table_id=public_rt.id,
        destination_cidr_block="0.0.0.0/0",
        gateway_id=igw.id
    )

    # Private Route Table (no IGW)
    private_rt = RouteTable(scope, f"{id}-private-rt",
        provider=provider,
        vpc_id=vpc.id
    )

    public_subnets = []
    private_subnets = []
    
    for i in range(2):
        az = tfvars["availability_zones"][i]

        # Public subnet
        pub = Subnet(scope, f"{id}-pub-{i}",
            provider=provider,
            vpc_id=vpc.id,
            cidr_block=tfvars["public_subnet_cidrs"][i],
            availability_zone=az,
            map_public_ip_on_launch=True
        )
        RouteTableAssociation(scope, f"{id}-pub-rta-{i}",
            provider=provider,
            subnet_id=pub.id,
            route_table_id=public_rt.id
        )
        public_subnets.append(pub)

        # Private subnet
        priv = Subnet(scope, f"{id}-priv-{i}",
            provider=provider,
            vpc_id=vpc.id,
            cidr_block=tfvars["private_subnet_cidrs"][i],
            availability_zone=az,
            map_public_ip_on_launch=False
        )
        RouteTableAssociation(scope, f"{id}-priv-rta-{i}",
            provider=provider,
            subnet_id=priv.id,
            route_table_id=private_rt.id
        )
        private_subnets.append(priv)



    # NAT Gateway setup
    nat_eip = Eip(scope, f"{id}-nat-eip",
        provider=provider,
        tags={"Name": f"{tfvars['name']}-nat-eip"}
    )
    nat_gateway = NatGateway(scope, f"{id}-nat-gateway",
        provider=provider,
        subnet_id=public_subnets[0].id,
        allocation_id=nat_eip.id,
        tags={"Name": f"{tfvars['name']}-nat-gw"}
    )
    Route(scope, f"{id}-private-default-route",
        provider=provider,
        route_table_id=private_rt.id,
        destination_cidr_block="0.0.0.0/0",
        nat_gateway_id=nat_gateway.id
    )

    return {
        "vpc_id": vpc.id,
        "public_subnets": public_subnets,
        "private_subnets": private_subnets,
        "public_route_table_id": public_rt.id,
        "private_route_table_id": private_rt.id,
    }
