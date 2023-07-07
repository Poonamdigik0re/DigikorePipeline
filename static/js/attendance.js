const load_shifts = (resp) => {
    new SlimSelect({
        select: document.getElementById('select_shift_id'),
        data: [{'text': '', 'placeholder': true}].concat(resp.map(r => {
            return {text: r.name, value: r.id}
        })),
        placeholder: 'Select Shift',
        allowDeselect: true,
    })
};

const load_departments = (resp) => {
    new SlimSelect({
        select: document.getElementById('select_department_id'),
        data: [{'text': '', 'placeholder': true}].concat(resp.map(r => {
            return {text: r.name, value: r.id}
        })),
        placeholder: 'Select Department',
        allowDeselect: true,
    })
};

const load_designations = (resp) => {
    new SlimSelect({
        select: document.getElementById('select_designation_id'),
        data: [{'text': '', 'placeholder': true}].concat(resp.map(r => {
            return {text: r.name, value: r.id}
        })),
        placeholder: 'Select Designations',
        allowDeselect: true,
    })
};

const get_attendance = (key = null, input = null) => {
    let filters = {};
    if (key != null && input != null) filters = {key: key, value: input.value};

    let selected_month = document.getElementById('select_month').value;
    let [year, month] = selected_month.split('-');

    if (year != undefined && month != undefined) {
        post('get_attendance/', filters).then(resp => {

        })
    }
};

window.onload = async () => {
    show_loading();
    await init();

    get_all_shifts(load_shifts);
    get_all_departments(load_departments);
    get_all_designations(load_designations);


    // set title
    document.title = '';
    hide_loading()
};