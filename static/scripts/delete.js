async function deleteService(serviceName) {
    const responce = await fetch(`/service/delete/${serviceName}`, {
        method: 'DELETE',
    });

    if (responce.ok) {
        location.reload();
    } else {
        alert("Ошибка при удалении сервиса.")
    }
}

async function deleteVolume(volumeName) {
    const responce = await fetch(`/volume/delete/${volumeName}`, {
        method: 'DELETE',
    });

    if (responce.ok) {
        location.reload();
    } else {
        alert("Ошибка при удалении сервиса.")
    }
}

async function deleteNetwork(networkName) {
    const responce = await fetch(`/network/delete/${networkName}`, {
        method: 'DELETE',
    });

    if (responce.ok) {
        location.reload();
    } else {
        alert("Ошибка при удалении сервиса.")
    }
}

async function deleteFile(path, filename) {
    const responce = await fetch(`/storage/file/delete/${path}/${filename}`, {
        method: 'DELETE',
    });

    if (responce.ok) {
        location.reload();
    } else {
        alert("Ошибка при удалении файла.")
    }
}

async function deleteFolder(path, filename) {
    const responce = await fetch(`/storage/folder/delete/${path}/${filename}`, {
        method: 'DELETE',
    });

    if (responce.ok) {
        location.reload();
    } else {
        alert("Ошибка при удалении папки.")
    }
}