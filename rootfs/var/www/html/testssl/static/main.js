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

function updateIpOptions() {
    const ipInput = document.getElementById("ip");
    const dnsSelect = document.getElementById("dns_ip");
    const dnsButton = document.getElementById("load-dns-addresses");
    const dnsStatus = document.getElementById("dns-address-status");
    const singleIp = document.getElementById("single_ip");
    const singleIpHelp = document.getElementById("single-ip-help");
    const hasManualIp = ipInput.value.trim() !== "";
    const hasSelectedDnsIp = dnsSelect.value !== "";
    const hasDnsAddresses = dnsSelect.dataset.loadedHost !== "";

    dnsSelect.disabled = hasManualIp || !hasDnsAddresses;
    dnsButton.disabled = hasManualIp;
    singleIp.disabled = hasManualIp;
    if (hasManualIp || hasSelectedDnsIp) {
        singleIp.checked = false;
    }

    if (hasManualIp) {
        dnsSelect.value = "";
        singleIp.disabled = true;
        singleIpHelp.textContent = "A manual IP is entered, so this option does not apply. Only the entered IP will be tested.";
    } else {
        singleIpHelp.textContent = "When enabled, only the first IP returned by DNS is tested. Other servers behind the hostname will not be tested.";
    }

    if (hasSelectedDnsIp) {
        singleIp.disabled = true;
        singleIpHelp.textContent = "A specific DNS address is selected, so only that IP will be tested.";
    }

    if (hasManualIp && dnsStatus) {
        dnsStatus.textContent = "A manual IP is entered, so the DNS address selection is unavailable.";
    }
}

function clearDnsAddresses(statusMessage) {
    const dnsSelect = document.getElementById("dns_ip");
    dnsSelect.replaceChildren(new Option("Use normal DNS resolution", ""));
    dnsSelect.dataset.loadedHost = "";
    dnsSelect.disabled = true;
    document.getElementById("dns-address-status").textContent = statusMessage;
    updateIpOptions();
}

async function loadDnsAddresses() {
    const hostInput = document.getElementById("host");
    const dnsButton = document.getElementById("load-dns-addresses");
    const dnsSelect = document.getElementById("dns_ip");
    const dnsStatus = document.getElementById("dns-address-status");
    const host = hostInput.value.trim();

    if (!host) {
        dnsStatus.textContent = "Enter a hostname first.";
        hostInput.focus();
        return;
    }

    dnsButton.disabled = true;
    dnsStatus.textContent = "Loading DNS addresses...";
    try {
        const url = new URL(dnsButton.dataset.resolveUrl, window.location.href);
        url.searchParams.set("host", host);
        const response = await fetch(url, { headers: { Accept: "application/json" } });
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Unable to load DNS addresses.");
        }
        if (hostInput.value.trim() !== host) {
            clearDnsAddresses("The hostname changed. Load its DNS addresses again.");
            return;
        }

        dnsSelect.replaceChildren(new Option("Use normal DNS resolution", ""));
        result.addresses.forEach(function(address) {
            const option = new Option(
                `${address.address} (IPv${address.version})`,
                address.address
            );
            dnsSelect.add(option);
        });
        dnsSelect.dataset.loadedHost = host;
        dnsStatus.textContent = result.addresses.length
            ? `${result.addresses.length} unique DNS address(es) found. Select one to test that server only.`
            : "No IP addresses were found for this hostname.";
        updateIpOptions();
    } catch (error) {
        console.error("Unable to load DNS addresses.", error);
        clearDnsAddresses(error.message || "Unable to load DNS addresses.");
    } finally {
        dnsButton.disabled = document.getElementById("ip").value.trim() !== "";
    }
}

document.addEventListener("DOMContentLoaded", function() {
    const ipInput = document.getElementById("ip");
    const hostInput = document.getElementById("host");
    const dnsSelect = document.getElementById("dns_ip");
    const dnsButton = document.getElementById("load-dns-addresses");
    const form = document.querySelector("form");

    ipInput.addEventListener("input", function() {
        if (ipInput.value.trim()) {
            dnsSelect.value = "";
        } else if (dnsSelect.dataset.loadedHost) {
            const count = dnsSelect.options.length - 1;
            dnsStatus.textContent = `${count} unique DNS address(es) loaded. Select one to test that server only.`;
        } else {
            dnsStatus.textContent = "Load the DNS addresses to test a specific server behind the hostname.";
        }
        updateIpOptions();
    });
    hostInput.addEventListener("input", function() {
        if (dnsSelect.dataset.loadedHost && hostInput.value.trim() !== dnsSelect.dataset.loadedHost) {
            clearDnsAddresses("The hostname changed. Load its DNS addresses again.");
        }
    });
    dnsSelect.addEventListener("change", updateIpOptions);
    dnsButton.addEventListener("click", loadDnsAddresses);
    updateIpOptions();

    form.addEventListener("submit", function() {
        progressVal = 0;
        const progressBar = document.getElementById("progress-bar");
        progressBar.textContent = "Please wait...";
        setTimeout(progressContinue, 1000);
    });
});
