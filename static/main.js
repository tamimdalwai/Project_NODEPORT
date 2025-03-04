
document.addEventListener('DOMContentLoaded', () => {
    const plcSelect = document.getElementById('plcSelect');
    const dataBody = document.getElementById('data-body');
    let updateInterval;

    // Home Page Logic
    if (plcSelect) {
        async function loadPlcList() {
            try {
                const plcs = await window.pywebview.api.get_plc_list();
                plcSelect.innerHTML = '<option value="">Select PLC</option>';
                plcs.forEach(plc => {
                    plcSelect.add(new Option(`${plc}`, plc));
                });
            } catch (error) {
                console.error('Failed to load PLC list:', error);
            }
        }

        async function handleShow() {
            const plcName = plcSelect.value;
            if (plcName) {
                try {
                    await window.pywebview.api.create_plc_window(plcName);
                    // Focus the new window if needed
                } catch (error) {
                    console.error('Failed to create window:', error);
                }
            }
        }

        plcSelect.addEventListener('focus', loadPlcList);
        document.querySelector('button').addEventListener('click', handleShow);
    }

    // Data Page Logic
    if (dataBody) {
        const urlParams = new URLSearchParams(window.location.search);
        const plcName = urlParams.get('plc');
        const plcNameElement = document.getElementById('plc-name');
        let isUpdating = false;

        // Set initial UI state
        plcNameElement.textContent = plcName || 'Unknown PLC';
        dataBody.innerHTML = '<tr><td colspan="9" class="loading">Loading data...</td></tr>';

        function createCell(content, type = '') {
            const td = document.createElement('td');
            td.className = type;
            td.textContent = content;
            return td;
        }

        function createStatusCell(state) {
            const td = document.createElement('td');
            td.innerHTML = `<span class="status ${state ? 'ON' : 'OFF'}">${state ? 'ON' : 'OFF'}</span>`;
            return td;
        }

        async function updateData() {
            if (isUpdating) return;
            isUpdating = true;

            try {
                const data = await window.pywebview.api.get_plc_data(plcName);
                const fragment = document.createDocumentFragment();

                // Process Coils
                Object.entries(data.coils || {}).forEach(([address, state]) => {
                    const tr = document.createElement('tr');
                    tr.append(
                        createCell(address),
                        createCell(address),
                        createStatusCell(state),
                        ...Array(6).fill().map(() => createCell(''))
                    );
                    fragment.appendChild(tr);
                });

                // Process Input Bits
                Object.entries(data.input_bits || {}).forEach(([address, state]) => {
                    const tr = document.createElement('tr');
                    tr.append(
                        ...Array(3).fill().map(() => createCell('')),
                        createCell(address),
                        createCell(address),
                        createStatusCell(state),
                        ...Array(3).fill().map(() => createCell(''))
                    );
                    fragment.appendChild(tr);
                });

                // Process Registers
                Object.entries(data.registers || {}).forEach(([address, value]) => {
                    const tr = document.createElement('tr');
                    tr.append(
                        ...Array(6).fill().map(() => createCell('')),
                        createCell(address),
                        createCell(address),
                        createCell(value, 'value')
                    );
                    fragment.appendChild(tr);
                });

                dataBody.innerHTML = '';
                dataBody.appendChild(fragment);

            } catch (error) {
                console.error('Update failed:', error);
                dataBody.innerHTML = '<tr><td colspan="9" class="error">Failed to load data</td></tr>';
            } finally {
                isUpdating = false;
            }
        }

        // Initial update
        updateData();

        // Smart update interval with visibility check
        updateInterval = setInterval(() => {
            if (!document.hidden) updateData();
        }, 1000);

        // Cleanup on window close
        window.addEventListener('beforeunload', () => {
            clearInterval(updateInterval);
        });
    }
});











// document.addEventListener('DOMContentLoaded', () => {
//     const plcSelect = document.getElementById('plcSelect');
//
//     async function loadPlcList() {
//         const plcs = await window.pywebview.api.get_plc_list();
//
//         // Preserve first option, remove others
//         while (plcSelect.options.length > 1) {
//             plcSelect.remove(1);
//         }
//
//         // Add new options
//         plcs.forEach(plc => {
//             const option = new Option(plc, plc);
//             plcSelect.add(option);
//         });
//     }
//
//     async function handleShow() {
//         const plcName = plcSelect.value;
//         if (!plcName) return;
//
//         window.pywebview.api.create_plc_window(plcName);
//     }
//
//     // Event listeners
//     plcSelect.addEventListener('focus', loadPlcList);
//     document.querySelector('button').addEventListener('click', handleShow);
//
//     window.addEventListener('pywebviewready', () => {
//         window.pywebview.api.onClosed(() => {
//             console.log('Window closed');
//         });
//     });
// });