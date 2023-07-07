class Employee {
    constructor(data) {
        this.data = data;
        this.element = createElements(el('tr', {},
            el('td', {}, this.data.empid),
            el('td', {}, this.data.full_name),
            el('td', {}, this.data.team__shift__intime),
            el('td', {}, this.data.department__name),
            el('td', {}, this.data.gender),
            el('td', {}, this.data.phone),
            el('td', {}, this.data.current_address),
            el('td', {}, this.data.permanent_address),
            el('td', {}, this.data.emergency_contact),
            el('td', {}, this.data.emergency_phone),
        ))
    }
}

const get_employees = () => {
    let employees_list = document.getElementById('employees_list');

    return post('get_employees/', {}).then(resp => {
        resp.forEach(data => {
            let employee = new Employee(data);
            employees_list.append(employee.element);
        });

        document.getElementById('total_employees').innerText = resp.length;
    })
};

window.onload = async () => {
    show_loading();
    await init();

    get_employees();

    // set title
    document.title = 'Transportation';
    hide_loading()
};