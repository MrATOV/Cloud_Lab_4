function addField(containerId, list) {
    const container = document.getElementById(containerId);
    const inputContainer = document.createElement("div");
    inputContainer.className = "dynamic-field";

    const input = document.createElement("input");
    input.type = "text";
    input.name = containerId;
    if (list) {
        input.setAttribute('list', list);
    }

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.textContent = "Удалить";
    removeButton.onclick = function() {
        container.removeChild(inputContainer);
    };

    inputContainer.appendChild(input);
    inputContainer.appendChild(removeButton);
    container.appendChild(inputContainer);
}

function addDoubleField(containerId, list) {
    const container = document.getElementById(containerId);
    const inputContainer = document.createElement("div");
    inputContainer.className = "dynamic-field";

    const input = document.createElement("input");
    input.type = "text";
    input.name = containerId + "_key";
    if (list) {
        input.setAttribute('list', list);
    }

    const input2 = document.createElement("input");
    input2.type = "text";
    input2.name = containerId + "_value";

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.textContent = "Удалить";
    removeButton.onclick = function() {
        container.removeChild(inputContainer);
    };

    inputContainer.appendChild(input);
    inputContainer.appendChild(input2);
    inputContainer.appendChild(removeButton);
    container.appendChild(inputContainer);
}

function fillServiceDetails(services) {
    const selectedService = document.getElementById('service_select').value;
    const service = services[selectedService];

    if (service) {
        document.getElementById('new_service_name').value = selectedService;
        document.getElementById('image').value = service.image || '';
        document.getElementById('container_name').value = service.container_name || '';
        
        const portsDiv = document.getElementById('ports');
        portsDiv.innerHTML = '';
        (service.ports || []).forEach(port => {
            const div = document.createElement('div');
            div.className = "dynamic-field";
            div.innerHTML = `<input type="text" name="ports" value="${port}"><button type="button" onclick="this.parentElement.remove()">Удалить</button>`;
            portsDiv.appendChild(div);
        });

        const volumesDiv = document.getElementById('volumes');
        volumesDiv.innerHTML = '';
        (service.volumes || []).forEach(volume => {
            const div = document.createElement('div');
            div.className = "dynamic-field";
            const [key, value] = volume.split(':');
            div.innerHTML = `<input type="text" name="volumes_key" value="${key}" list="volumes_list"><input type="text" name="volumes_value" value="${value}"><button type="button" onclick="this.parentElement.remove()">Удалить</button>`;
            volumesDiv.appendChild(div);
        });

        const envDiv = document.getElementById('environment');
        envDiv.innerHTML = '';
        for (const [key, value] of Object.entries(service.environment || {})) {
            const div = document.createElement('div');
            div.className = "dynamic-field";
            div.innerHTML = `<input type="text" name="environment_key" value="${key}"><input type="text" name="environment_value" value="${value}"><button type="button" onclick="this.parentElement.remove()">Удалить</button>`;
            envDiv.appendChild(div);
        }

        const networksDiv = document.getElementById('networks');
        networksDiv.innerHTML = '';
        (service.networks || []).forEach(network => {
            const div = document.createElement('div');
            div.className = "dynamic-field";
            div.innerHTML = `<input type="text" name="networks" value="${network}" list="networks_list"><button type="button" onclick="this.parentElement.remove()">Удалить</button>`;
            networksDiv.appendChild(div);
        });

        const dependsOnDiv = document.getElementById('depends_on');
        dependsOnDiv.innerHTML = '';
        (service.depends_on || []).forEach(dependency => {
            const div = document.createElement('div');
            div.className = "dynamic-field";
            div.innerHTML = `<input type="text" name="depends_on" value="${dependency}" list="depends_on_list"><button type="button" onclick="this.parentElement.remove()">Удалить</button>`;
            dependsOnDiv.appendChild(div);
        });

        document.getElementById('command').value = service.command || '';
        document.getElementById('restart').value = service.restart || 'no';
    }
}