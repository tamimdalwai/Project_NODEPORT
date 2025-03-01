document.addEventListener('DOMContentLoaded', () => {
    // Initialize PLC lists for all pages
    const initializePLCList = async (selector) => {
        try {
            const plcList = await window.pywebview.api.get_plc_list();
            const select = document.querySelector(selector);
            if (select) {
                select.innerHTML = '<option value="">Select PLC</option>'; // Reset options
                plcList.forEach(plc => {
                    const option = document.createElement('option');
                    option.value = plc;
                    option.textContent = plc;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading PLC list:', error);
            alert('Error loading PLC list');
        }
    };

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
    if (!selectedPlc) {
        alert('Please select a PLC');
        return;
    }

    try {
        const plcData = await window.pywebview.api.get_plc_data(selectedPlc);
        updateStatus(plcData);
        createTable(plcData.register_data);
    } catch (error) {
        console.error('Error loading PLC data:', error);
        alert('Error loading PLC data');
    }
}

function updateStatus({ sampling_frequency, change_in_data }) {
    document.getElementById('samplingFreq').textContent = sampling_frequency || 'N/A';
    document.getElementById('changeData').textContent = change_in_data || 'N/A';
}

function createTable(addresses) {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';

    addresses.forEach((row, index) => {
        const tr = document.createElement('tr');

        tr.innerHTML = `
            <td>${row['PLC OUTPUT NO'] || ''}</td>
            <td>${row['MODBUS ADDRESS (Coils)'] || ''}</td>
            <td class="coil-${index}">${row['States (Coils)'] || '0'}</td>
            <td>${row['INPUT BIT NO'] || ''}</td>
            <td>${row['MODBUS ADDRESS (Input Bits)'] || ''}</td>
            <td class="input-bit-${index}">${row['States (Input Bits)'] || '0'}</td>
            <td>${row['PLC ANALOG INPUT SLOT'] || ''}</td>
            <td>${row['MODBUS ADDRESS (Analog Inputs)'] || ''}</td>
            <td class="analog-${index}">${row['Values'] || '0'}</td>
        `;

        tbody.appendChild(tr);
    });
}

// Register UI Functions
async function loadRegisterConfig() {
    const selectedPlc = document.getElementById('registerPlcSelect').value;
    if (!selectedPlc) {
        alert('Please select a PLC');
        return;
    }

    try {
        const config = await window.pywebview.api.get_register_config(selectedPlc);
        renderRegisterForm(config);
    } catch (error) {
        console.error('Error loading register config:', error);
        alert('Error loading register config');
    }
}

function renderRegisterForm(config) {
    const table = document.getElementById('registerTable');
    if (!table) return;

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

    const tbody = document.getElementById('registerBody');
    if (!tbody) return;

    config.forEach((row, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row.output || ''}</td>
            <td>${row.coilAddress || ''}</td>
            <td class="coil-${index}">${row.coilState || '0'}</td>
            <td>${row.inputBit || ''}</td>
            <td>${row.bitAddress || ''}</td>
            <td class="input-bit-${index}">${row.bitState || '0'}</td>
            <td>${row.analogInput || ''}</td>
            <td>${row.registerAddress || ''}</td>
            <td class="analog-${index}">${row.value || '0'}</td>
        `;
        tbody.appendChild(tr);
    });
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

    if (!settings.plc || !settings.ip || !settings.port) {
        alert('Please fill in all required fields');
        return;
    }

    try {
        await window.pywebview.api.save_settings(settings);
        refreshSettingsTable();
    } catch (error) {
        console.error('Error saving settings:', error);
        alert('Error saving settings');
    }
}

async function refreshSettingsTable() {
    try {
        const settings = await window.pywebview.api.get_all_settings();
        const tbody = document.getElementById('settingsBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        settings.forEach(plc => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${plc.name || ''}</td>
                <td>${plc.ip || ''}</td>
                <td>${plc.port || ''}</td>
                <td>${plc.samplingFreq || ''}</td>
                <td>${plc.changeData || ''}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error refreshing settings table:', error);
        alert('Error refreshing settings table');
    }
}








// document.addEventListener('DOMContentLoaded', () => {
//     // Initialize PLC lists for all pages
//     const initializePLCList = async (selector) => {
//         const plcList = await window.pywebview.api.get_plc_list();
//         const select = document.querySelector(selector);
//         plcList.forEach(plc => {
//             const option = document.createElement('option');
//             option.value = plc;
//             option.textContent = plc;
//             select.appendChild(option);
//         });
//     }
//
//     // Initialize based on current page
//     if (document.getElementById('plcSelect')) {
//         initializePLCList('#plcSelect');
//     }
//     if (document.getElementById('registerPlcSelect')) {
//         initializePLCList('#registerPlcSelect');
//     }
//     if (document.getElementById('settingsPlcSelect')) {
//         initializePLCList('#settingsPlcSelect');
//     }
// });
//
// // Home UI Functions
// async function handleShow() {
//     const selectedPlc = document.getElementById('plcSelect').value;
//     const plcData = await window.pywebview.api.get_plc_data(selectedPlc);
//     updateStatus(plcData);
//     createTable(plcData.addresses);
// }
//
// function updateStatus({samplingFreq, changeData}) {
//     document.getElementById('samplingFreq').textContent = samplingFreq || 'N/A';
//     document.getElementById('changeData').textContent = changeData || 'N/A';
// }
//
// function createTable(addresses) {
//     const tbody = document.getElementById('tableBody');
//     tbody.innerHTML = '';
//
//     addresses.forEach((row, index) => {
//         const tr = document.createElement('tr');
//
//         tr.innerHTML = `
//             <td>OUTPUT${index + 1}</td>
//             <td>${row.coilAddress}</td>
//             <td class="coil-${index}">0</td>
//             <td>INPUT BIT${index + 1}</td>
//             <td>${row.inputBitAddress}</td>
//             <td class="input-bit-${index}">0</td>
//             <td>ANALOG INPUT${index + 1}</td>
//             <td>${row.analogAddress}</td>
//             <td class="analog-${index}">0</td>
//         `;
//
//         tbody.appendChild(tr);
//     });
// }
//
// // Register UI Functions
// async function loadRegisterConfig() {
//     const selectedPlc = document.getElementById('registerPlcSelect').value;
//     const config = await window.pywebview.api.get_register_config(selectedPlc);
//     renderRegisterForm(config);
// }
//
// function renderRegisterForm(config) {
//     const table = document.getElementById('registerTable');
//     table.innerHTML = `
//         <table>
//             <thead>
//                 <tr>
//                     <th>Output</th>
//                     <th>Coil Address</th>
//                     <th>State</th>
//                     <th>Input Bit</th>
//                     <th>Bit Address</th>
//                     <th>State</th>
//                     <th>Analog Input</th>
//                     <th>Register Address</th>
//                     <th>Value</th>
//                 </tr>
//             </thead>
//             <tbody id="registerBody"></tbody>
//         </table>
//     `;
//
//     // Add dynamic rows based on config
// }
//
// // Settings UI Functions
// async function saveSettings() {
//     const settings = {
//         plc: document.getElementById('settingsPlcSelect').value,
//         ip: document.getElementById('ipAddress').value,
//         port: document.getElementById('port').value,
//         samplingFreq: document.getElementById('samplingFreq').value,
//         changeData: document.getElementById('changeData').value
//     };
//
//     await window.pywebview.api.save_settings(settings);
//     refreshSettingsTable();
// }
//
// async function refreshSettingsTable() {
//     const settings = await window.pywebview.api.get_all_settings();
//     const tbody = document.getElementById('settingsBody');
//     tbody.innerHTML = '';
//
//     settings.forEach(plc => {
//         const tr = document.createElement('tr');
//         tr.innerHTML = `
//             <td>${plc.name}</td>
//             <td>${plc.ip}</td>
//             <td>${plc.port}</td>
//             <td>${plc.samplingFreq}</td>
//             <td>${plc.changeData}</td>
//         `;
//         tbody.appendChild(tr);
//     });
// }