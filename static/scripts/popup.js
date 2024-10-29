window.onload = function() {
    const message = "{{ message }}";
    if (message) {
        const popup = document.getElementById("popup");
        popup.style.display = "block";
        setTimeout(() => {
            popup.style.display = "none";
        }, 3000);
    }
};