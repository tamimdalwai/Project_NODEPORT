// Common functions
function handleError(error) {
    console.error('Error:', error);
}

// Selection window logic
function initSelectWindow() {
    if (document.getElementById('plcSelect')) {
        pywebview.api.get_plc_list()
            .then(populatePLCSelect)
            .catch(handleError);
    }
}

function populatePLCSelect(plcs) {
    const select = document.getElementById('plcSelect');
    plcs.forEach(plc => {
        const option = document.createElement('option');
        option.value = plc;
        option.textContent = plc;
        select.appendChild(option);
    });
}

function loadPLC() {
    const plc = document.getElementById('plcSelect').value;
    if (plc) {
        pywebview.api.create_data_window(plc);
    }
}

// Data window logic
function initDataWindow() {
    if (document.getElementById('tableBody')) {
        pollData();
    }
}

function updateTable(data) {
    /* Same updateTable implementation as before */
}

async function pollData() {
    try {
        const data = await pywebview.api.get_plc_data();
        updateTable(data);
        setTimeout(pollData, 1000);
    } catch (error) {
        handleError(error);
    }
}

// Initialize appropriate scripts based on page
document.addEventListener('DOMContentLoaded', () => {
    initSelectWindow();
    initDataWindow();
});


// Add error handling
function handleError(error) {
    console.error('Error:', error);
    alert('An error occurred: ' + error.message);
}

// Initialize with error handling
document.addEventListener('DOMContentLoaded', () => {
    try {
        if (document.getElementById('plcSelect')) {
            pywebview.api.get_plc_list()
                .then(plcs => {
                    const select = document.getElementById('plcSelect');
                    plcs.forEach(plc => {
                        const option = document.createElement('option');
                        option.value = plc;
                        option.textContent = plc;
                        select.appendChild(option);
                    });
                })
                .catch(handleError);
        }

        if (document.getElementById('tableBody')) {
            const pollData = () => {
                pywebview.api.get_plc_data()
                    .then(data => {
                        // Update table logic
                    })
                    .catch(handleError)
                    .finally(() => setTimeout(pollData, 1000));
            };
            pollData();
        }
    } catch (error) {
        handleError(error);
    }
});