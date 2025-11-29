import logging
import sys
import ipaddress
import yaml
from pathlib import Path


def setup_logging(verbose=False):
    """Configure logging for the application."""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'builder.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger('AWSNetworkBuilder')


def validate_cidr(cidr_block):
    """Validate CIDR block format."""
    try:
        ipaddress.IPv4Network(cidr_block)
        return True
    except ValueError:
        return False


def load_config(config_path):
    """Load and parse YAML configuration file."""
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required fields
    required_fields = ['vpc_name', 'cidr', 'region', 'subnets']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field in config: {field}")
    
    return config
