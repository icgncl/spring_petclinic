import hcl2

def load_tfvars(path: str) -> dict:
    with open(path, 'r') as f:
        return hcl2.load(f)
