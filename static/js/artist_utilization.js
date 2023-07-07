const get_departments = () => {
    return post('get_departments/', {}).then(resp => {
        new SlimSelect({
            select: document.getElementById('select_department_id'),
            data: [{text: '', value: '', placeholder: true}].concat(resp.map(x => {
                return {text: x.name, value: x.id}
            })),
            onChange: get_data,
            placeholder: 'Select Department'
        })
    })
};

const get_data = () => {
    let department_id = document.getElementById('select_department_id').value;
    let date = document.getElementById('select_date').value;

    if (department_id && date) {
        show_loading();
        post('get_data/', {department_id: department_id, date: date}).then(resp => {
            let table = document.getElementById('employees');
            table.innerText = "";

            resp.forEach(emp => {
                let row = createElements(el('tr', {},
                    el('td', {}, emp['user__userprofile__department__name']),
                    el('td', {}, emp['user__userprofile__full_name']),
                    el('td', {}, emp['user__userprofile__team__lead__userprofile__full_name']),
                    el('td', {}, seconds_to_hhmm(emp['working_hours'])),
                    el('td', {}, seconds_to_hhmm(emp['actuals'])),
                    el('td', {}, `${parseInt(emp['actuals'] / emp['working_hours'] * 100)}%`)
                ));

                table.append(row);
            });

            document.getElementById('total_employees').innerText = `Total: ${resp.length}`;
            hide_loading();
        })
    }
};

const download_as_csv = () => {
    let date = document.getElementById('select_date').value;
    if (date != "") {
        location.href = `/artist_utilization/download_as_csv/${date}/`;
    }
};

window.onload = async () => {
    show_loading();
    await init();

    await get_departments();

    // set title
    document.title = '';
    hide_loading()
};