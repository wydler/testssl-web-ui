function getDocHeight() {
    const D = document;
    return Math.max(
        Math.max(D.body.scrollHeight, D.documentElement.scrollHeight),
        Math.max(D.body.offsetHeight, D.documentElement.offsetHeight),
        Math.max(D.body.clientHeight, D.documentElement.clientHeight)
    );
}

let autoScroll = true;
let scroller = setInterval(function() {
    document.documentElement.scrollTop = getDocHeight();
}, 100);

function stopAutoScroll() {
    autoScroll = false;
    if (scroller !== null && scroller !== undefined) {
        clearInterval(scroller);
        scroller = null;
    }
}

function abortTest() {
    stopAutoScroll();
    document.getElementById("pagetitle").textContent = "Test aborted";
    document.querySelectorAll(".new-test").forEach(function(newTestLink) {
        newTestLink.classList.remove("d-none");
    });
    setTimeout(function() {
        window.stop();
    }, 100);
}

document.addEventListener("keydown", function(event) {
    if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        abortTest();
    } else if (["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End", " "].includes(event.key)) {
        stopAutoScroll();
    }
}, true);
window.addEventListener("wheel", stopAutoScroll, { passive: true });
window.addEventListener("touchstart", stopAutoScroll, { passive: true });
window.addEventListener("pointerdown", stopAutoScroll);

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("pagetitle").textContent = "Test done";
    document.querySelectorAll(".new-test").forEach(function(newTestLink) {
        newTestLink.classList.remove("d-none");
    });
    document.querySelectorAll(".download-result").forEach(function(downloadButton) {
        downloadButton.classList.remove("d-none");
        downloadButton.addEventListener("click", function() {
            const output = document.getElementById("result-output").innerText.trim();
            const host = downloadButton.dataset.host;
            const date = new Date();
            const dateString = [
                date.getFullYear(),
                String(date.getMonth() + 1).padStart(2, "0"),
                String(date.getDate()).padStart(2, "0")
            ].join("-");
            const timeString = [
                String(date.getHours()).padStart(2, "0"),
                String(date.getMinutes()).padStart(2, "0"),
                String(date.getSeconds()).padStart(2, "0")
            ].join("-");
            const blob = new Blob([output + "\n"], { type: "text/plain;charset=utf-8" });
            const downloadUrl = URL.createObjectURL(blob);
            const link = document.createElement("a");

            link.href = downloadUrl;
            link.download = `testssl_${host}_${dateString}_${timeString}.txt`;
            link.click();
            setTimeout(function() {
                URL.revokeObjectURL(downloadUrl);
            }, 1000);
        });
    });
    document.getElementById("result").classList.remove("d-none");
    if (autoScroll) {
        document.documentElement.scrollTop = getDocHeight();
    }
    clearInterval(scroller);
    scroller = null;
});
