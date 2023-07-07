let ALL_EMPLOYEES = [];

class Employee {
    constructor(data) {
        this.data = data;
        this.element = createElements(
            el('div', {'style': 'width: 150px; margin: 0 4em 4em 0;'},
                el('img', {'src': data.profile_picture, 'width': '150px', 'style': 'border-radius:10em'}),
                el('div', {'class': 'align-center bold'}, data.full_name),
                el('div', {'class': 'align-center p5'}, data.department__name),
                el('div', {'class': 'align-center'}, data.designation__name)
            )
        )
    }
}

const load_locations = (resp) => {
    new SlimSelect({
        select: document.getElementById('filter_location_id'),
        allowDeselect: true,
        data: [{value: '', text: '', placeholder: true}].concat(resp.map(x => {
            return {'value': x.id, 'text': x.name}
        })),
        placeholder: 'Filter Location',
        onChange: apply_filters
    });
};

const load_departments = (resp) => {
    new SlimSelect({
        select: document.getElementById('filter_department_id'),
        allowDeselect: true,
        data: [{value: '', text: '', placeholder: true}].concat(resp.map(x => {
            return {'value': x.id, 'text': x.name}
        })),
        placeholder: 'Filter Department',
        onChange: apply_filters
    });
};

const load_designations = (resp) => {
    new SlimSelect({
        select: document.getElementById('filter_designation_id'),
        allowDeselect: true,
        data: [{value: '', text: '', placeholder: true}].concat(resp.map(x => {
            return {'value': x.id, 'text': x.name}
        })),
        placeholder: 'Filter Designation',
        onChange: apply_filters
    });
};

const get_all_employees = () => {
    return post('get_all_employees/', {}).then(resp => {
        let all_employees = document.getElementById('all_employees');

        resp.forEach(data => {
            let employee = new Employee(data);
            all_employees.append(employee.element);

            ALL_EMPLOYEES.push(employee);
        });
        document.getElementById('total').innerText = `Total: ${ALL_EMPLOYEES.length}`;
    });
};

const apply_filters = () => {
    let location_id = document.getElementById('filter_location_id').value;
    let department_id = document.getElementById('filter_department_id').value;
    let designation_id = document.getElementById('filter_designation_id').value;
    let count = ALL_EMPLOYEES.length;

    ALL_EMPLOYEES.forEach(employee => {
        employee.element.style.display = 'block';
        let hide = false;

        if (location_id != "" && employee.data.location_id != location_id) hide = true;
        if (department_id != "" && employee.data.department_id != department_id) hide = true;
        if (designation_id != "" && employee.data.designation_id != designation_id) hide = true;

        if (hide) {
            employee.element.style.display = 'none';
            --count;
        }
    });

    document.getElementById('total').innerText = `Total: ${count}`;
};

window.onload = async () => {
    await init('digikore Team');

    get_all_locations(load_locations);
    get_all_departments(load_departments);
    get_all_designations(load_designations);

    await get_all_employees();

    hide_loading()
};
