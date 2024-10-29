function updateUploadStatus(input) {
    const status = document.getElementById('upload-status');
    if (input.files.length > 0) {
        status.textContent = input.files[0].name;
    } else {
        status.textContent = '';
    }
}