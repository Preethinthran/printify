document.getElementById("converterForm").addEventListener("submit", function (e) {
    e.preventDefault();
    const files = document.getElementById("file").files;
    if (files.length === 0) {
        alert("Please select at least one file.");
        return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append("files", files[i]);
    }

    fetch("/convert", {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Conversion failed.");
        }
        return response.blob();
    })
    .then(blob => {
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = "converted.pdf";
        a.click();
        URL.revokeObjectURL(downloadUrl);
        document.getElementById("downloadArea").innerHTML = `<p class="text-success">PDF downloaded successfully!</p>`;
    })
    .catch(error => {
        console.error(error);
        alert("Error: " + error.message);
    });
});
