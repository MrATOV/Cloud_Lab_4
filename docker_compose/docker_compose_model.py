from pydantic import BaseModel
from typing import Dict, List, Optional

class ServiceConfig(BaseModel):
    image: str
    container_name: Optional[str] = None
    ports: Optional[List[str]] = None
    volumes: Optional[List[str]] = None
    environment: Optional[Dict[str, str]] = None
    networks: Optional[List[str]] = None
    depends_on: Optional[List[str]] = None
    command: Optional[str] = None
    restart: Optional[str] = "always"


class VolumeConfig(BaseModel):
    driver: Optional[str] = None
    driver: Optional[str] = None
    driver_opts: Optional[Dict[str, str]] = None
    labels: Optional[Dict[str, str]] = None
    external: Optional[bool] = None
    name: Optional[str] = None

class IPAMConfigItem(BaseModel):
    subnet: str
    gateway: Optional[str] = None

class IPAMConfig(BaseModel):
    driver: Optional[str] = None
    config: Optional[List[IPAMConfigItem]] = None

class NetworkConfig(BaseModel):
    driver: Optional[str] = None
    driver_opts: Optional[Dict[str, str]] = None
    ipam: Optional[IPAMConfig] = None
    labels: Optional[Dict[str, str]] = None
    external: Optional[bool] = None
    name: Optional[str] = None


class DockerComposeModel(BaseModel):
    version: str
    services: Dict[str, ServiceConfig]
    volumes: Optional[Dict[str, VolumeConfig]] = None
    networks: Optional[Dict[str, NetworkConfig]] = None