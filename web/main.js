document.addEventListener('DOMContentLoaded', async () => {
    // Initialize PLC list
    const plcList = await window.pywebview.api.get_plc_list();
    const plcSelect = document.getElementById('plcSelect');
    plcList.forEach(plc => {
        const option = document.createElement('option');
        option.value = plc;
        option.textContent = plc;
        plcSelect.appendChild(option);
    });

    // Event listeners
    document.getElementById('showBtn').addEventListener('click', async () => {
        const selectedPlc = plcSelect.value;
        const plcData = await window.pywebview.api.get_plc_data(selectedPlc);
        updateStatus(plcData);
        createTable(plcData);
    });

    document.getElementById('startBtn').addEventListener('click', () => {
        const selectedPlc = plcSelect.value;
        window.pywebview.api.start_modbus(selectedPlc);
    });
});

function updateStatus({samplingFreq, changeData}) {
    document.getElementById('samplingFreq').textContent = samplingFreq || 'N/A';
    document.getElementById('changeData').textContent = changeData || 'N/A';
}

function createTable(plcData) {
    const table = document.createElement('table');
    // Create table headers
    const headers = [
        'PLC OUTPUT NO', 'MODBUS ADDRESS (Coils)', 'States (Coils)',
        'INPUT BIT NO', 'MODBUS ADDRESS (Input Bits)', 'States (Input Bits)',
        'PLC ANALOG INPUT SLOT', 'MODBUS ADDRESS (Analog Inputs)', 'Values'
    ];

    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headers.forEach(headerText => {
        const th = document.createElement('th');
        th.textContent = headerText;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create table body
    const tbody = document.createElement('tbody');
    plcData.addresses.forEach((row, index) => {
        const tr = document.createElement('tr');

        // Add cells for each column
        [
            `OUTPUT${index + 1}`, row.coilAddress, `<span class="coil-${index}">0</span>`,
            `INPUT BIT${index + 1}`, row.inputBitAddress, `<span class="input-bit-${index}">0</span>`,
            `ANALOG INPUT${index + 1}`, row.analogAddress, `<span class="analog-${index}">0</span>`
        ].forEach(text => {
            const td = document.createElement('td');
            td.innerHTML = text;
            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    const container = document.getElementById('dataTable');
    container.innerHTML = '';
    container.appendChild(table);
}

// Called from Python to update values
function updateValues(type, index, value) {
    const elements = document.getElementsByClassName(`${type}-${index}`);
    if (elements.length > 0) {
        elements[0].textContent = value;
    }
}