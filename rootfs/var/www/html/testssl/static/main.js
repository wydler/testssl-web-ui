let progressVal = 0;

function progressContinue() {
    const progressBar = document.getElementById("progress-bar");
    const progress = document.getElementById("progress");
    progressVal = Math.min(progressVal + 1, 95);
    progressBar.style.width = progressVal + "%";
    progress.setAttribute("aria-valuenow", progressVal);
    if (progressVal < 95) {
        setTimeout(progressContinue, 1000);
    }
}

function updateSingleIpOption() {
    const ipInput = document.getElementById("ip");
    const singleIp = document.getElementById("single_ip");
    const singleIpHelp = document.getElementById("single-ip-help");
    const hasManualIp = ipInput.value.trim() !== "";

    singleIp.disabled = hasManualIp;
    if (hasManualIp) {
        singleIp.checked = false;
        singleIpHelp.textContent = "A manual IP is entered, so this option does not apply. Only the entered IP will be tested.";
    } else {
        singleIpHelp.textContent = "When enabled, only the first IP returned by DNS is tested. Other servers behind the hostname will not be tested.";
    }
}

document.addEventListener("DOMContentLoaded", function() {
    const ipInput = document.getElementById("ip");
    const form = document.querySelector("form");

    ipInput.addEventListener("input", updateSingleIpOption);
    updateSingleIpOption();

    form.addEventListener("submit", function() {
        progressVal = 0;
        const progressBar = document.getElementById("progress-bar");
        progressBar.textContent = "Please wait...";
        setTimeout(progressContinue, 1000);
    });
});
