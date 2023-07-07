const get_my_attendance = () => {
    let table = document.getElementById("attendance_table");
    table.innerText = "";

    let [year, month] = document.getElementById('select__month').value.split('-');

    return post('get_my_attendance/', {year: year, month: month}).then(resp => {
        resp.forEach(att => {
            let row = createElements(el('tr', {'class': 'align-center'},
                el('td', {'class': 'align-left'}, local_date(att.date)),
                el('td', {'class': `attendance ${att.type}`}, att.type),
                el('td', {}, local_datetime(att.intime)),
                el('td', {}, local_datetime(att.outtime)),
                el('td', {}, seconds_to_hhmm(att.working_hours)),
                el('td', {}, seconds_to_hhmm(att.actuals))
            ));

            table.append(row);
        })
    })
};


window.onload = async () => {
    show_loading();
    await init();

    let today = new Date();
    let select__month = document.getElementById('select__month');
    select__month.value = `${today.getFullYear()}-${(today.getMonth() + 1).toString().padStart(2, "0")}`;

    get_my_attendance();

    // set title
    document.title = '';
    hide_loading()
};