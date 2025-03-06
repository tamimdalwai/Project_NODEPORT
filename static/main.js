document.addEventListener('DOMContentLoaded', () => {
    const plcSelect = document.getElementById('plcSelect');
    const showButton = document.getElementById('showButton');
    const dataBodyCoils = document.getElementById('data-body-coils');
    const dataBodyBits = document.getElementById("data-body-input-states");
    const dataBodyRegister = document.getElementById("data-body-registers");
    let updateInterval;

    // Function to check if pywebview API is available
    function isPyWebViewApiReady() {
        return window.pywebview && window.pywebview.api;
    }

    // Function to wait for pywebview API to be available
    async function waitForPyWebViewApi() {
        return new Promise((resolve) => {
            const checkInterval = setInterval(() => {
                if (isPyWebViewApiReady()) {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 100);
        });
    }

    if (plcSelect && showButton) {
        async function loadPlcList() {
            try {
                await waitForPyWebViewApi(); // Wait for API to be available
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
                    await waitForPyWebViewApi(); // Wait for API to be available
                    await window.pywebview.api.create_plc_window(plcName);
                } catch (error) {
                    console.error('Failed to create window:', error);
                }
            }
        }

        plcSelect.addEventListener('focus', loadPlcList);
         showButton.addEventListener('click', handleShow);
        // document.querySelector('button').addEventListener('click', handleShow);

    }

    // Data Page Logic
    if (dataBodyCoils) {
        const urlParams = new URLSearchParams(window.location.search);
        const plcName = urlParams.get('plc');
        const plcNameElement = document.getElementById('plc-name');
        let isUpdating = false;

        // Set initial UI state
        plcNameElement.textContent = plcName || 'Unknown PLC';
        dataBodyCoils.innerHTML = '<tr><td colspan="9" class="loading">Loading data...</td></tr>';

        function createCell(content, type = '') {
            const td = document.createElement('td');
            td.className = type;
            td.textContent = content;
            return td;
        }

        function createStatusCell(state) {
            const td = document.createElement('td');
            td.innerHTML = `<span class="status ${state ? 'ON' : 'OFF'}">${state ? '1' : '0'}</span>`;
            return td;
        }

        async function updateData() {
            if (isUpdating) return;
            isUpdating = true;

            try {
                await waitForPyWebViewApi(); // Wait for API to be available
                const data = await window.pywebview.api.get_plc_data(plcName);
                const fragmentCoils = document.createDocumentFragment();
                const fragmentBits = document.createDocumentFragment();
                const fragmentRegisters = document.createDocumentFragment();

                // // Process Coils
                // Object.entries(data.coils || {}).forEach(([address, state]) => {
                //     const tr = document.createElement('tr');
                //     tr.append(
                //         createCell(`OUTPUT${address}`),
                //         createCell(formatCoilAddress(address)),
                //         createStatusCell(state),
                //         ...Array(6).fill().map(() => createCell('')) // 6 additional cells for spacing
                //     );
                //     fragmentCoils.appendChild(tr);
                // });
                //
                // // Process Input Bits
                // Object.entries(data.input_bits || {}).forEach(([address, state]) => {
                //     const tr = document.createElement('tr');
                //     tr.append(
                //         createCell(`INPUT BIT${address}`),
                //         createCell(formatInputBitAddress(address)),
                //         createStatusCell(state),
                //         ...Array(3).fill().map(() => createCell('')) // 3 additional cells for spacing
                //     );
                //     fragmentBits.appendChild(tr);
                // });
                // Process Coils (without additional empty cells)
                Object.entries(data.coils || {}).forEach(([address, state]) => {
                    const tr = document.createElement('tr');
                    tr.append(
                        createCell(`OUTPUT${address}`), // OUTPUT{address}
                        createCell(formatCoilAddress(address)), // Formatted address with leading zeros
                        createStatusCell(state) // 0 or 1 depending on the value
                    );
                    fragmentCoils.appendChild(tr);
                });

// Process Input Bits (without additional empty cells)
                Object.entries(data.input_bits || {}).forEach(([address, state]) => {
                    const tr = document.createElement('tr');
                    tr.append(
                        createCell(`INPUT BIT${address}`), // INPUT BIT{address}
                        createCell(formatInputBitAddress(address)), // Formatted address with leading zeros
                        createStatusCell(state) // 0 or 1 depending on the value
                    );
                    fragmentBits.appendChild(tr);
                });
                // Process Registers
                Object.entries(data.registers || {}).forEach(([address, value]) => {
                    const tr = document.createElement('tr');
                    tr.append(
                        createCell(`ANALOG INPUT${address}`),
                        createCell(formatRegisterAddress(address)),
                        createCell(value, 'value')
                    );
                    fragmentRegisters.appendChild(tr);
                });

                // Update the tables
                dataBodyCoils.innerHTML = '';
                dataBodyCoils.appendChild(fragmentCoils);

                dataBodyBits.innerHTML = '';
                dataBodyBits.appendChild(fragmentBits);

                dataBodyRegister.innerHTML = '';
                dataBodyRegister.appendChild(fragmentRegisters);

            } catch (error) {
                console.error('Update failed:', error);
                dataBodyCoils.innerHTML = '<tr><td colspan="9" class="error">Failed to load data</td></tr>';
            } finally {
                isUpdating = false;
            }
        }

        // Helper functions for formatting addresses
        function formatCoilAddress(address) {
            return String(address).padStart(5, '0');
        }

        function formatInputBitAddress(address) {
            return `1${String(address).padStart(4, '0')}`;
        }

        function formatRegisterAddress(address) {
            return `3${String(address).padStart(4, '0')}`;
        }

        // Wait for API to be available before initializing data updates
        waitForPyWebViewApi().then(() => {
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
        });
    }
});







// document.addEventListener('DOMContentLoaded', () => {
//     const plcSelect = document.getElementById('plcSelect');
//     const dataBodyCoils = document.getElementById('data-body-coils');
//     const dataBodyBits = document.getElementById("data-body-input-states")
//     const dataBodyRegister = document.getElementById("data-body-registers")
//     let updateInterval;
//
//     // Function to check if pywebview API is available
//     function isPyWebViewApiReady() {
//         return window.pywebview && window.pywebview.api;
//     }
//
//     // Function to wait for pywebview API to be available
//     async function waitForPyWebViewApi() {
//         return new Promise((resolve) => {
//             const checkInterval = setInterval(() => {
//                 if (isPyWebViewApiReady()) {
//                     clearInterval(checkInterval);
//                     resolve();
//                 }
//             }, 100);
//         });
//     }
//
//
//     if (plcSelect) {
//         async function loadPlcList() {
//             try {
//                 await waitForPyWebViewApi(); // Wait for API to be available
//                 const plcs = await window.pywebview.api.get_plc_list();
//                 plcSelect.innerHTML = '<option value="">Select PLC</option>';
//                 plcs.forEach(plc => {
//                     plcSelect.add(new Option(`${plc}`, plc));
//                 });
//             } catch (error) {
//                 console.error('Failed to load PLC list:', error);
//             }
//         }
//
//         async function handleShow() {
//             const plcName = plcSelect.value;
//             if (plcName) {
//                 try {
//                     await waitForPyWebViewApi(); // Wait for API to be available
//                     await window.pywebview.api.create_plc_window(plcName);
//                 } catch (error) {
//                     console.error('Failed to create window:', error);
//                 }
//             }
//         }
//
//         plcSelect.addEventListener('focus', loadPlcList);
//         document.querySelector('button').addEventListener('click', handleShow);
//     }
//
//     // Data Page Logic
//     if (dataBodyCoils) {
//         const urlParams = new URLSearchParams(window.location.search);
//         const plcName = urlParams.get('plc');
//         const plcNameElement = document.getElementById('plc-name');
//         let isUpdating = false;
//
//         // Set initial UI state
//         plcNameElement.textContent = plcName || 'Unknown PLC';
//         dataBodyCoils.innerHTML = '<tr><td colspan="9" class="loading">Loading data...</td></tr>';
//
//         function createCell(content, type = '') {
//             const td = document.createElement('td');
//             td.className = type;
//             td.textContent = content;
//             return td;
//         }
//
//         function createStatusCell(state) {
//             const td = document.createElement('td');
//             td.innerHTML = `<span class="status ${state ? 1 : 0}">${state ? 1 : 0}</span>`;
//             return td;
//         }
//
//         async function updateData() {
//             if (isUpdating) return;
//             isUpdating = true;
//
//             try {
//                 await waitForPyWebViewApi(); // Wait for API to be available
//                 const data = await window.pywebview.api.get_plc_data(plcName);
//                 const fragmentCoils = document.createDocumentFragment();
//                 function formatCoilAddress(address) {
//     // Convert address to string
//     const addressStr = String(address);
//
//     // Pad with leading zeros based on length
//     if (addressStr.length === 1) {
//         return `0000${addressStr}`; // 0-9 → 0000{address}
//     } else if (addressStr.length === 2) {
//         return `000${addressStr}`; // 10-99 → 000{address}
//     } else if (addressStr.length === 3) {
//         return `00${addressStr}`; // 100-999 → 00{address}
//     } else if (addressStr.length === 4) {
//         return `0${addressStr}`; // 1000-9999 → 0{address}
//     } else {
//         return addressStr; // No padding for addresses with 5 or more digits
//     }
// }
//
// // Example usage in your code
// Object.entries(data.coils || {}).forEach(([address, state]) => {
//     const tr = document.createElement('tr');
//     tr.append(
//         createCell(`OUTPUT${address}`), // OUTPUT{address}
//         createCell(formatCoilAddress(address)), // Formatted address with leading zeros
//         createStatusCell(state), // 0 or 1 depending on the value
//         ...Array(6).fill().map(() => createCell('')) // Empty cells for spacing
//     );
//     fragmentCoils.appendChild(tr);
// });
//
//             function formatInputBitAddress(address) {
//     // Convert address to a number
//     const addressNum = Number(address);
//
//     // Map the address to the range 30001-39999
//     if (addressNum >= 1 && addressNum <= 9) {
//         return `3000${addressNum}`; // 1-9 → 30001-30009
//     } else if (addressNum >= 10 && addressNum <= 99) {
//         return `300${addressNum}`; // 10-99 → 30010-30099
//     } else if (addressNum >= 100 && addressNum <= 999) {
//         return `30${addressNum}`; // 100-999 → 30100-30999
//     } else if (addressNum >= 1000 && addressNum <= 9999) {
//         return `3${addressNum}`; // 1000-9999 → 31000-39999
//     } else {
//         return String(addressNum).padStart(5, '0'); // Fallback for invalid addresses
//     }
// }
//
//                 const fragmentBits = document.createDocumentFragment();
//                 // Process Input Bits
//                 Object.entries(data.input_bits || {}).forEach(([address, state]) => {
//                     const tr = document.createElement('tr');
//                     tr.append(
//                         // ...Array(3).fill().map(() => createCell('')),
//                         createCell(`INPUT BIT${address}`),
//                         createCell(formatInputBitAddress(address)),
//                         createStatusCell(state),
//                         ...Array(3).fill().map(() => createCell(''))
//                     );
//                     fragmentBits.appendChild(tr);
//                 });
//                 function formatRegisterAddress(address) {
//     // Convert address to a number
//     const addressNum = Number(address);
//
//     // Map the address to the range 40001-49999
//     if (addressNum >= 1 && addressNum <= 9) {
//         return `4000${addressNum}`; // 1-9 → 40001-40009
//     } else if (addressNum >= 10 && addressNum <= 99) {
//         return `400${addressNum}`; // 10-99 → 40010-40099
//     } else if (addressNum >= 100 && addressNum <= 999) {
//         return `40${addressNum}`; // 100-999 → 40100-40999
//     } else if (addressNum >= 1000 && addressNum <= 9999) {
//         return `4${addressNum}`; // 1000-9999 → 41000-49999
//     } else {
//         return String(addressNum).padStart(5, '0'); // Fallback for invalid addresses
//     }
// }
//
//                 const fragmentRegisters = document.createDocumentFragment();
//                 // Process Registers
//                 Object.entries(data.registers || {}).forEach(([address, value]) => {
//                     const tr = document.createElement('tr');
//                     tr.append(
//                         // ...Array(6).fill().map(() => createCell('')),
//                         createCell(`ANALOG INPUT${address}`),
//                         createCell(formatRegisterAddress(address)),
//                         createCell(value, 'value')
//                     );
//                     fragmentRegisters.appendChild(tr);
//                 });
//
//                 dataBodyCoils.innerHTML = '';
//                 dataBodyCoils.appendChild(fragmentCoils);
//
//                 dataBodyBits.innerHTML = '';
//                 dataBodyBits.appendChild(fragmentBits);
//
//                 dataBodyRegister.innerHTML = '';
//                 dataBodyRegister.appendChild(fragmentRegisters)
//
//
//             } catch (error) {
//                 console.error('Update failed:', error);
//                 dataBodyCoils.innerHTML = '<tr><td colspan="9" class="error">Failed to load data</td></tr>';
//             } finally {
//                 isUpdating = false;
//             }
//         }
//
//         // Wait for API to be available before initializing data updates
//         waitForPyWebViewApi().then(() => {
//             // Initial update
//             updateData();
//
//             // Smart update interval with visibility check
//             updateInterval = setInterval(() => {
//                 if (!document.hidden) updateData();
//             }, 1000);
//
//             // Cleanup on window close
//             window.addEventListener('beforeunload', () => {
//                 clearInterval(updateInterval);
//             });
//         });
//     }
// });
//
