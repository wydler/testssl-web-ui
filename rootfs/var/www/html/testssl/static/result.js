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
    document.getElementById("new-test").classList.remove("d-none");
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
    document.getElementById("new-test").classList.remove("d-none");
    document.getElementById("result").classList.remove("d-none");
    if (autoScroll) {
        document.documentElement.scrollTop = getDocHeight();
    }
    clearInterval(scroller);
    scroller = null;
});
