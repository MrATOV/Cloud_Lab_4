import yaml
import docker
import subprocess
from docker_compose.docker_compose_model import *

def read_docker_compose_services(file_path: str) -> List[str]:
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return list(data.get('services', {}).keys())

def get_load_containers(file_path: str) -> List[bool]:
    client = docker.from_env()
    containers = client.containers.list()
   
    running_container_names = [container.name for container in containers]
    service_names = read_docker_compose_services(file_path)
    return {service_name: any(service_name in container_name for container_name in running_container_names) for service_name in service_names}

def environment_dict(env_list: List[str]) -> Dict[str, str]:
    env_dict = {}
    for item in env_list:
        key, value = item.split('=', 1)
        env_dict[key.strip()] = value.strip()
    return env_dict

def environment_list(env_dict: Dict[str, str]) -> List[str]:
    return [f"{key}={value}" for key, value in env_dict.items()]

def replace_relative_paths(config: Dict, service_name: str) -> None:
    if 'volumes' in config:
        config['volumes'] = [v.replace(f'./storage/{service_name}/', './') for v in config['volumes']]

    if 'command' in config and isinstance(config['command'], str):
        config['command'] = config['command'].replace(f'./storage/{service_name}/', './')

def read_docker_compose(file_path: str) -> DockerComposeModel:
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    services = {}
    for name, config in data.get('services', {}).items():
        if 'environment' in config and isinstance(config['environment'], list):
            config['environment'] = environment_dict(config['environment'])
        
        replace_relative_paths(config, name)
        
        services[name] = ServiceConfig(**config)

    volumes = {}
    if 'volumes' in data:
        for name, config in data['volumes'].items():
            volumes[name] = VolumeConfig(**config)

    networks = {}
    if 'networks' in data:
        for name, config in data['networks'].items():
            if 'ipam' in config and isinstance(config['ipam'], dict):
                ipam_config = config['ipam']
                ipam_items = ipam_config.get('config', [])
                ipam_config_items = [IPAMConfigItem(**item) for item in ipam_items]
                config['ipam'] = IPAMConfig(driver=ipam_config.get('driver'), config=ipam_config_items)
            networks[name] = NetworkConfig(**config)

    return DockerComposeModel(
        version=data.get('version', ''),
        services=services,
        volumes=volumes,
        networks=networks
    )

def save_docker_compose(docker_compose: DockerComposeModel, file_path: str) -> None:
    def filter_empty(data):
        if isinstance(data, dict):
            return {k: filter_empty(v) for k, v in data.items() if v not in (None, '', {}, [])}
        elif isinstance(data, list):
            return [filter_empty(item) for item in data if item not in (None, '', {}, [])]
        return data

    data = {
        'version': docker_compose.version,
        'services': {name: filter_empty(config.model_dump(exclude_none=True)) for name, config in docker_compose.services.items()},
        'volumes': {name: filter_empty(config.model_dump(exclude_none=True)) for name, config in docker_compose.volumes.items()} if docker_compose.volumes else {},
        'networks': {name: filter_empty(config.model_dump(exclude_none=True)) for name, config in docker_compose.networks.items()} if docker_compose.networks else {}
    }
    
    for service_name, service_config in data['services'].items():
        if 'environment' in service_config:
            service_config['environment'] = environment_list(service_config['environment'])

        if 'volumes' in service_config:
            service_config['volumes'] = [
                f"./storage/{service_name}" + vol.split(':')[0][1:] + (':' + vol.split(':')[1] if ':' in vol else '') 
                if vol.startswith('./') else vol
                for vol in service_config['volumes']
            ]

        if 'command' in service_config and isinstance(service_config['command'], str):
            cmd = service_config['command']
            if './' in cmd:
                service_config['command'] = cmd.replace('./', f"./storage/{service_name}/") + '/'

    data = filter_empty(data)

    with open(file_path, 'w') as file:
        yaml.dump(data, file, default_flow_style=False, sort_keys=False)

def up_docker_compose(service_name=None):
    try:
        if service_name:
            subprocess.run(['docker-compose', 'up', '-d', service_name], check=True)
            print(f"Сервис '{service_name}' успешно запущен.")
        else:
            subprocess.run(['docker-compose', 'up', '-d'], check=True)
            print("Все сервисы успешно запущены.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при запуске docker-compose: {e}")

def down_docker_compose(service_name=None):
    try:
        if service_name:
            subprocess.run(['docker-compose', 'stop', service_name], check=True)
            print(f"Сервис '{service_name}' успешно остановлен.")
        else:
            subprocess.run(['docker-compose', 'down'], check=True)
            print("Все сервисы успешно остановлены.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при остановке сервиса '{service_name}': {e}")

def restart_docker_compose(service_name=None):
    try:
        if service_name:
            subprocess.run(['docker-compose', 'restart', service_name], check=True)
            print(f"Сервис '{service_name}' успешно перезапущен.")
        else:
            subprocess.run(['docker-compose', 'restart'], check=True)
            print("Все сервисы успешно перезапущены.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при перезапуске сервиса '{service_name}': {e}")

def remove_docker_compose(service_name=None):
    try:
        if service_name:
            subprocess.run(['docker-compose', 'rm', '-f', service_name], check=True)
            print(f"Сервис '{service_name}' удален.")
        else:
            subprocess.run(['docker-compose', 'down', '-v', '--rmi', 'all', '--remove-orphans'], check=True)
            print("Все сервисы удалены.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при удалении сервиса '{service_name}': {e}")