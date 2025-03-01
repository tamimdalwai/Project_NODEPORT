document.addEventListener('DOMContentLoaded', () => {
    // Initialize PLC lists for all pages
    const initializePLCList = async (selector) => {
        const plcList = await window.pywebview.api.get_plc_list();
        const select = document.querySelector(selector);
        plcList.forEach(plc => {
            const option = document.createElement('option');
            option.value = plc;
            option.textContent = plc;
            select.appendChild(option);
        });
    }

    // Initialize based on current page
    if (document.getElementById('plcSelect')) {
        initializePLCList('#plcSelect');
    }
    if (document.getElementById('registerPlcSelect')) {
        initializePLCList('#registerPlcSelect');
    }
    if (document.getElementById('settingsPlcSelect')) {
        initializePLCList('#settingsPlcSelect');
    }
});

// Home UI Functions
async function handleShow() {
    const selectedPlc = document.getElementById('plcSelect').value;
    const plcData = await window.pywebview.api.get_plc_data(selectedPlc);
    updateStatus(plcData);
    createTable(plcData.addresses);
}

function updateStatus({samplingFreq, changeData}) {
    document.getElementById('samplingFreq').textContent = samplingFreq || 'N/A';
    document.getElementById('changeData').textContent = changeData || 'N/A';
}

function createTable(addresses) {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';

    addresses.forEach((row, index) => {
        const tr = document.createElement('tr');

        tr.innerHTML = `
            <td>OUTPUT${index + 1}</td>
            <td>${row.coilAddress}</td>
            <td class="coil-${index}">0</td>
            <td>INPUT BIT${index + 1}</td>
            <td>${row.inputBitAddress}</td>
            <td class="input-bit-${index}">0</td>
            <td>ANALOG INPUT${index + 1}</td>
            <td>${row.analogAddress}</td>
            <td class="analog-${index}">0</td>
        `;

        tbody.appendChild(tr);
    });
}

// Register UI Functions
async function loadRegisterConfig() {
    const selectedPlc = document.getElementById('registerPlcSelect').value;
    const config = await window.pywebview.api.get_register_config(selectedPlc);
    renderRegisterForm(config);
}

function renderRegisterForm(config) {
    const table = document.getElementById('registerTable');
    table.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Output</th>
                    <th>Coil Address</th>
                    <th>State</th>
                    <th>Input Bit</th>
                    <th>Bit Address</th>
                    <th>State</th>
                    <th>Analog Input</th>
                    <th>Register Address</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody id="registerBody"></tbody>
        </table>
    `;

    // Add dynamic rows based on config
}

// Settings UI Functions
async function saveSettings() {
    const settings = {
        plc: document.getElementById('settingsPlcSelect').value,
        ip: document.getElementById('ipAddress').value,
        port: document.getElementById('port').value,
        samplingFreq: document.getElementById('samplingFreq').value,
        changeData: document.getElementById('changeData').value
    };

    await window.pywebview.api.save_settings(settings);
    refreshSettingsTable();
}

async function refreshSettingsTable() {
    const settings = await window.pywebview.api.get_all_settings();
    const tbody = document.getElementById('settingsBody');
    tbody.innerHTML = '';

    settings.forEach(plc => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${plc.name}</td>
            <td>${plc.ip}</td>
            <td>${plc.port}</td>
            <td>${plc.samplingFreq}</td>
            <td>${plc.changeData}</td>
        `;
        tbody.appendChild(tr);
    });
}