const calculate_eta = () => {
    let speed = parseInt(document.getElementById('eta_speed').value) / 10; // internet speed, 1 Giga bits to Giga bytes;
    let efficiency = parseInt(document.getElementById('eta_efficiency').value) / 100;
    let size = parseInt(document.getElementById('eta_size').value);
    let seconds = size / (speed * efficiency);
    let eta = seconds_to_time(seconds);

    document.getElementById('calculated_eta').innerText = `${eta[0]} Hours ${eta[1]} Minutes`;
};

const get_status_breakdown = (location) => {
    let table = document.getElementById(`${location}_status_breakdown`);
    table.innerText = "";

    post(`get_status_breakdown/${location}/`, {}).then(resp => {
        resp.forEach(d => {
            let row = createElements(
                el('tr', {},
                    el('td', {}, d.status),
                    el('td', {}, d.count),
                    el('td', {}, file_size(d.size || 0)),
                )
            );
            table.append(row)
        })
    })
};

const get_project_breakdown = (location) => {
    let table = document.getElementById(`${location}_project_breakdown`);
    table.innerText = "";

    post(`get_project_breakdown/${location}/`, {}).then(resp => {
        resp.forEach(d => {
            let row = createElements(
                el('tr', {},
                    el('td', {}, d.project),
                    el('td', {}, d.count),
                    el('td', {}, file_size(d.size || 0)),
                )
            );
            table.append(row)
        })
    })
};

const fix_sig_submitted = () => {
    if (confirm("Are you sure?")) {
        post('fix_sig_submitted/', {}).then(() => {
            reload();
        })
    }
};

const reload = () => {
    get_status_breakdown('pnq');
    get_status_breakdown('lax');
    get_project_breakdown('pnq');
    get_project_breakdown('lax');
};

window.onload = async () => {
    await init('Site Sync');
    reload();

    // reload in every 5 minutes
    setInterval(reload, 300000);

    hide_loading()
};