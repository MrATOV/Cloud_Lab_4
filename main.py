from fastapi import FastAPI, HTTPException, Request, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import json
import shutil
from starlette.middleware.sessions import SessionMiddleware
from docker_compose.docker_compose import *

DOCKER_COMPOSE_FILE = "docker-compose.yml"
STORAGE_DIR = "storage"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret_key")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def create_storage():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR, exist_ok=True)
        if not os.path.exists(DOCKER_COMPOSE_FILE):
            with open(DOCKER_COMPOSE_FILE, 'w') as file:
                file.write('')
        docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
        for service_name in docker_compose.services:
            os.makedirs(os.path.join(STORAGE_DIR, service_name), exist_ok=True)

create_storage()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    load_containers = {}#get_load_containers(DOCKER_COMPOSE_FILE)

    message = request.session.get("message")
    request.session.pop("message", None)
    return templates.TemplateResponse("index.html", {"request": request, "docker_compose": docker_compose, "load_containers": load_containers, "message": message})

@app.get("/service/open/{port}")
async def service_page_open(request: Request, port: int = None):
    host = request.headers.get("host")
    
    url = f"http://{host.split(':')[0]}:{port}/"

    return RedirectResponse(url)

@app.get("/service/{service_name}", response_class=HTMLResponse)
async def service_page_read(request: Request, service_name: str = None):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    if service_name in docker_compose.services:
        service = docker_compose.services[service_name]
        return templates.TemplateResponse("service_read.html", {"request": request, "service_name": service_name, "service": service})

@app.get("/service/edit/{service_name}", response_class=HTMLResponse)
async def service_page_write(request: Request, service_name: str = None):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    service = None
    services_json = None
    if service_name and service_name in docker_compose.services:
        service = docker_compose.services[service_name]
    else:
        with open('./data/services.json', 'r', encoding='utf-8') as file:
            services_json = json.load(file)
    service_names = docker_compose.services.keys() if docker_compose.services else {}
    network_names = docker_compose.networks.keys() if docker_compose.networks else {}
    volume_names = docker_compose.volumes.keys() if docker_compose.volumes else {}

    return templates.TemplateResponse("service_write.html", {"request": request, 
                                                       "service_name": service_name, 
                                                       "service": service, 
                                                       "service_json": services_json,
                                                       "service_names": service_names,
                                                       'network_names': network_names,
                                                       'volume_names': volume_names
                                                       })

@app.post("/service/create")
async def create_service_post(request: Request, new_service_name: str = Form(...),
                              image: str = Form(...), 
                              container_name: Optional[str] = Form(None), 
                              ports: Optional[List[str]] = Form([]), 
                              volumes_key: Optional[List[str]] = Form([]), 
                              volumes_value: Optional[List[str]] = Form([]), 
                              environment_key: Optional[List[str]] = Form([]), 
                              environment_value: Optional[List[str]] = Form([]), 
                              networks: Optional[List[str]] = Form([]), 
                              depends_on: Optional[List[str]] = Form([]), 
                              command: Optional[str] = Form(None), 
                              restart: Optional[str] = Form("always")
):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    
    if new_service_name in docker_compose.services:
        raise HTTPException(status_code=400, detail="Сервис с таким именем уже существует")

    storage_path = os.path.join(STORAGE_DIR, new_service_name)
    os.makedirs(storage_path)
    docker_compose.services[new_service_name] = ServiceConfig(
        image=image,
        container_name=container_name,
        ports=ports,
        volumes=[f"{key}:{value}" for key, value in zip(volumes_key, volumes_value)],
        environment={key: value for key, value in zip(environment_key, environment_value)},
        networks=networks,
        depends_on=depends_on,
        command=command,
        restart=restart
    )
    save_docker_compose(docker_compose, DOCKER_COMPOSE_FILE)
    request.session["message"] = f"Сервис {new_service_name} создан"
    return RedirectResponse("/", status_code=303)

@app.post("/service/update/{service_name}")
async def update_service(request: Request, service_name: str,
                         new_service_name: str = Form(...),
                         image: str = Form(...), 
                         container_name: Optional[str] = Form(None), 
                         ports: Optional[List[str]] = Form([]), 
                         volumes_key: Optional[List[str]] = Form([]), 
                         volumes_value: Optional[List[str]] = Form([]), 
                         environment_key: Optional[List[str]] = Form([]), 
                         environment_value: Optional[List[str]] = Form([]), 
                         networks: Optional[List[str]] = Form([]), 
                         depends_on: Optional[List[str]] = Form([]), 
                         command: Optional[str] = Form(None), 
                         restart: Optional[str] = Form("always")):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    if service_name in docker_compose.services:
        service = docker_compose.services[service_name]
        service.image = image
        service.container_name = container_name
        
        service.ports = ports if ports else []
        service.volumes = [f"{key}:{value}" for key, value in zip(volumes_key, volumes_value)] if volumes_key else []
        service.environment = {key: value for key, value in zip(environment_key, environment_value)} if environment_key else {}
        
        service.networks = networks if networks else []
        service.depends_on = depends_on if depends_on else []
        service.command = command
        service.restart = restart
        
        if service_name != new_service_name:
            docker_compose.services[new_service_name] = docker_compose.services.pop(service_name)
            old_path = os.path.join(STORAGE_DIR, service_name)
            new_path = os.path.join(STORAGE_DIR, new_service_name)
            os.rename(old_path, new_path)

        save_docker_compose(docker_compose, DOCKER_COMPOSE_FILE)
        request.session["message"] = f"Сервис {service_name} обновлен"
        return RedirectResponse("/", status_code=303)
    raise HTTPException(status_code=404, detail="Сервис не найден")

@app.delete("/service/delete/{service_name}")
async def delete_service(service_name: str):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    if service_name in docker_compose.services:
        del docker_compose.services[service_name]
        save_docker_compose(docker_compose, DOCKER_COMPOSE_FILE)
        folder_path = os.path.join(STORAGE_DIR, service_name)
        if os.path.isdir(folder_path):
            import shutil
            shutil.rmtree(folder_path) 
            remove_docker_compose(service_name)
            return {"message": "Том удален"}
        else:
            raise HTTPException(status_code=404, detail="Директория не найдена")
    raise HTTPException(status_code=404, detail="Сервис не найден")

@app.get("/volume/{volume_name}", response_class=HTMLResponse)
async def volumes_page_read(request: Request, volume_name: str = None):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    if volume_name in docker_compose.volumes:
        volume = docker_compose.volumes[volume_name]
        return templates.TemplateResponse("volume_read.html", {"request": request, "volume_name": volume_name, "volume": volume})

@app.get("/volume/edit/{volume_name}", response_class=HTMLResponse)
async def service_page_write(request: Request, volume_name: str = None):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    volume = None
    if volume_name and volume_name in docker_compose.volumes:
        volume = docker_compose.volumes[volume_name]
    
    return templates.TemplateResponse("volume_write.html", {"request": request, 
                                                       "volume_name": volume_name, 
                                                       "volume": volume
                                                       })

@app.post("/volume/create")
async def create_volume_post(request: Request, new_volume_name: str = Form(...),
                              driver: str = Form(...), 
                              driver_opts_key: Optional[List[str]] = Form([]), 
                              driver_opts_value: Optional[List[str]] = Form([]),
                              labels_key: Optional[List[str]] = Form([]), 
                              labels_value: Optional[List[str]] = Form([]), 
                              external: Optional[bool] = Form(None),
                              name: Optional[str] = Form(None)):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    
    if new_volume_name in docker_compose.volumes:
        raise HTTPException(status_code=400, detail="Том с таким именем уже существует")

    
    docker_compose.volumes[new_volume_name] = VolumeConfig(
        driver=driver,
        driver_opts={key: value for key, value in zip(driver_opts_key, driver_opts_value)},
        labels={key: value for key, value in zip(labels_key, labels_value)},
        external=external,
        name=name
    )
    save_docker_compose(docker_compose, DOCKER_COMPOSE_FILE)
    request.session["message"] = f"Том {new_volume_name} создан"
    return RedirectResponse("/", status_code=303)

@app.post("/volume/update/{volume_name}")
async def update_volume_post(request: Request, volume_name: str,
                             new_volume_name: str = Form(...),
                             driver: str = Form(...), 
                             driver_opts_key: Optional[List[str]] = Form([]), 
                             driver_opts_value: Optional[List[str]] = Form([]),
                             labels_key: Optional[List[str]] = Form([]), 
                             labels_value: Optional[List[str]] = Form([]), 
                             external: Optional[bool] = Form(None),
                             name: Optional[str] = Form(None)):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    if volume_name in docker_compose.volumes:
        volume = docker_compose.volumes[volume_name]
        volume.driver = driver
        volume.driver_opts = {key: value for key, value in zip(driver_opts_key, driver_opts_value)}
        volume.labels = {key: value for key, value in zip(labels_key, labels_value)}
        volume.external = external
        volume.name = name
        
        if volume_name != new_volume_name:
            docker_compose.volumes[new_volume_name] = docker_compose.volumes.pop(volume_name)

        save_docker_compose(docker_compose, DOCKER_COMPOSE_FILE)
        request.session["message"] = f"Том {volume_name} обновлен"
        return RedirectResponse("/", status_code=303)
    
    raise HTTPException(status_code=404, detail="Сервис не найден")

@app.delete("/volume/delete/{volume_name}")
async def delete_volume(volume_name: str):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    if volume_name in docker_compose.volumes:
        del docker_compose.volumes[volume_name]
        save_docker_compose(docker_compose, DOCKER_COMPOSE_FILE)
        return {"message": "Том удален"}
    raise HTTPException(status_code=404, detail="Том не найден")

@app.get("/network/{network_name}", response_class=HTMLResponse)
async def networks_page_read(request: Request, network_name: str = None):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    if network_name in docker_compose.networks:
        network = docker_compose.networks[network_name]
        return templates.TemplateResponse("network_read.html", {"request": request, "network_name": network_name, "network": network})

@app.get("/network/edit/{network_name}", response_class=HTMLResponse)
async def service_page_write(request: Request, network_name: str = None):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    network = None
    if network_name and network_name in docker_compose.networks:
        network = docker_compose.networks[network_name]
    
    return templates.TemplateResponse("network_write.html", {
        "request": request, 
        "network_name": network_name, 
        "network": network
    })

@app.post("/network/create")
async def create_network_post(request: Request,
    network_name: str = Form(...),
    driver: str = Form(...), 
    driver_opts_key: Optional[List[str]] = Form([]), 
    driver_opts_value: Optional[List[str]] = Form([]),
    labels_key: Optional[List[str]] = Form([]), 
    labels_value: Optional[List[str]] = Form([]), 
    external: Optional[bool] = Form(None),
    ipam_subnet: Optional[List[str]] = Form([]),
    ipam_gateway: Optional[List[str]] = Form([])
):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    
    if network_name in docker_compose.networks:
        raise HTTPException(status_code=400, detail="Сеть с таким именем уже существует")

    docker_compose.networks[network_name] = NetworkConfig(
        driver=driver,
        driver_opts={key: value for key, value in zip(driver_opts_key, driver_opts_value)},
        labels={key: value for key, value in zip(labels_key, labels_value)},
        external=external,
        ipam={
            "driver": "default",
            "config": [{"subnet": subnet, "gateway": gateway} for subnet, gateway in zip(ipam_subnet, ipam_gateway)]
        }
    )
    save_docker_compose(docker_compose, DOCKER_COMPOSE_FILE)
    request.session["message"] = f"Сеть {network_name} создана"
    return RedirectResponse("/", status_code=303)

@app.post("/network/update/{network_name}")
async def update_network_post(request: Request,
    network_name: str,
    new_network_name: str = Form(...),
    driver: str = Form(...), 
    driver_opts_key: Optional[List[str]] = Form([]), 
    driver_opts_value: Optional[List[str]] = Form([]),
    labels_key: Optional[List[str]] = Form([]), 
    labels_value: Optional[List[str]] = Form([]), 
    external: Optional[bool] = Form(None),
    ipam_subnet: Optional[List[str]] = Form([]),
    ipam_gateway: Optional[List[str]] = Form([])
):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    if network_name in docker_compose.networks:
        network = docker_compose.networks[network_name]
        network.driver = driver
        network.driver_opts = {key: value for key, value in zip(driver_opts_key, driver_opts_value)}
        network.labels = {key: value for key, value in zip(labels_key, labels_value)}
        network.external = external
        network.ipam = {
            "driver": "default",
            "config": [{"subnet": subnet, "gateway": gateway} for subnet, gateway in zip(ipam_subnet, ipam_gateway)]
        }
        
        if network_name != new_network_name:
            docker_compose.networks[new_network_name] = docker_compose.networks.pop(network_name)

        save_docker_compose(docker_compose, DOCKER_COMPOSE_FILE)
        request.session["message"] = f"Сеть {network_name} обновлена"
        return RedirectResponse("/", status_code=303)
    
    raise HTTPException(status_code=404, detail="Сеть не найдена")

@app.delete("/network/delete/{network_name}")
async def delete_network(network_name: str):
    docker_compose = read_docker_compose(DOCKER_COMPOSE_FILE)
    if network_name in docker_compose.networks:
        del docker_compose.networks[network_name]
        save_docker_compose(docker_compose, DOCKER_COMPOSE_FILE)
        return {"message": "Сеть удалена"}
    raise HTTPException(status_code=404, detail="Сеть не найдена")

@app.get("/storage/{path:path}", response_class=HTMLResponse)
async def read_root(request: Request, path: str = ""):
    current_dir = os.path.join(STORAGE_DIR, path)
    items = os.listdir(current_dir) if os.path.exists(current_dir) else []
    directories = [d for d in items if os.path.isdir(os.path.join(current_dir, d))]
    files = [f for f in items if os.path.isfile(os.path.join(current_dir, f))]

    message = request.session.get("message")
    request.session.pop("message", None)

    return templates.TemplateResponse("storage.html", {"request": request, "directories": directories, "files": files, "current_path": path, "message": message})

@app.post("/storage/file/add/{path:path}")
async def upload_file(request: Request, path: str, file: UploadFile = File(...)):
    current_dir = os.path.join(STORAGE_DIR, path)
    os.makedirs(current_dir, exist_ok=True)
    file_location = os.path.join(current_dir, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    request.session["message"] = f"Файл {file.filename} загружен"
    return RedirectResponse(f"/storage/{path}", status_code=303)

@app.post("/storage/folder/add/{path:path}")
async def create_folder(request: Request, path: str, folder_name: str = Form(...)):
    current_dir = os.path.join(STORAGE_DIR, path)
    folder_path = os.path.join(current_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    request.session["message"] = f"Директория {folder_name} создана"

    return RedirectResponse(f"/storage/{path}", status_code=303)

@app.delete("/storage/file/delete/{path:path}/{filename}")
async def delete_file(request: Request, path: str, filename: str):
    file_location = os.path.join(STORAGE_DIR, path, filename)
    if os.path.isfile(file_location):
        os.remove(file_location)
        return RedirectResponse(f"/storage/{path}", status_code=303)
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.delete("/storage/folder/delete/{path:path}/{foldername}")
async def delete_folder(request: Request, path: str, foldername: str):
    folder_path = os.path.join(STORAGE_DIR, path, foldername)
    if os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
        return RedirectResponse(f"/storage/{path}", status_code=303)
    else:
        raise HTTPException(status_code=404, detail="Folder not found")

@app.get("/docker_compose/run")
async def run_docker_compose(request: Request):
    up_docker_compose()
    request.session["message"] = "Все сервисы запущены"
    return RedirectResponse("/", status_code=303)

@app.get("/docker_compose/run/{service_name}")
async def run_docker_compose_service(request: Request, service_name: str):
    up_docker_compose(service_name)
    request.session["message"] = f"Сервис {service_name} запущен"
    return RedirectResponse("/", status_code=303)

@app.get("/docker_compose/stop")
async def stop_docker_compose(request: Request):
    down_docker_compose()
    request.session["message"] = "Все сервисы остановлены"
    return RedirectResponse("/", status_code=303)

@app.get("/docker_compose/stop/{service_name}")
async def stop_docker_compose_service(request: Request, service_name: str):
    down_docker_compose(service_name)
    request.session["message"] = f"Сервис {service_name} остановлен"
    return RedirectResponse("/", status_code=303)

@app.get("/docker_compose/delete")
async def delete_docker_compose(request: Request):
    remove_docker_compose()
    request.session["message"] = "Все образы удалены"
    return RedirectResponse("/", status_code=303)

@app.get("/docker_compose/restart")
async def restart_docker_compose_endpoint(request: Request):
    restart_docker_compose()
    request.session["message"] = "Все сервисы перезапущены"
    return RedirectResponse("/", status_code=303)

@app.get("/docker_compose/restart/{service_name}")
async def restart_docker_compose_service_endpoint(request: Request, service_name: str):
    restart_docker_compose(service_name)
    request.session["message"] = f"Сервис {service_name} перезапущен"
    return RedirectResponse("/", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)