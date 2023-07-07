let ALL_EMPLOYEES = [];

class Employee extends BaseClass {
    constructor(data) {
        super('userprofile', data);

        this.element = createElements(
            el('tr', {'class': 'highlight'},
                el('td', {}, this.data.empid),
                el('td', {}, this.data.full_name),
                el('td', {}, this.data.user__username),
                el('td', {}, this.data.gender),
                el('td', {}, this.data.department__name),
                el('td', {}, this.data.designation__name),
                el('td', {}, this.data.confirmation_status),
                el('td', {}, local_date(this.data.date_of_joining)),
                el('td', {},
                    el('div', {'class': 'dropdown'},
                        el('div', {'class': 'icon list'}, ''),
                        el('div', {'class': 'menu'},
                            el('a', {'class': 'item edit-employee'}, 'Edit'),
                            el('a', {'class': 'item add-attachments'}, 'Documents'),
                        ),
                    )
                )
            )
        );

        // connect edit-documents
        this.element.querySelector('.edit-employee').onclick = () => {
        show_modal('add_new_employee');
        let form = document.forms['add_new_employee'];
        form.user_id.value = this.data.id;
        form.first_name.value = this.data.user__first_name;
        form.last_name.value = this.data.user__last_name;
        form.username.value = this.data.user__username;
        form.emp_id.value = this.data.empid;

        post('get_employee_profile/', {'user_id': this.data.id}).then(resp => {
        console.log(resp);
        for (let k in resp) {
        console.log(k, resp[k]);
            if (form.hasOwnProperty(k)) {
                form[k].value = resp[k];
                this.data[k] = resp[k];

                // Update the multiple select
                if (form[k].tagName == 'SELECT' && form[k].multiple) {
                    for (let i = 0; i < form[k].children.length; i++) {
                        let child = form[k].children[i];
                        // Convert to int because it doesn't compare string to int
                        if (resp[k].indexOf(parseInt(child.value)) != -1) {
                            child.selected = true;
                        }
                    }
                }
                form[k].dispatchEvent(new Event('change'));
            }
        }
    });

};

        // connect documents upload
        this.element.querySelector('.add-attachments').onclick = () => {
            show_modal('add_attachments');
            this.get_attachments();
            document.querySelector('#upload_attachments').onclick = () => {
                this.add_attachments();
            }
        };
    }
}

const load_locations = (resp) => {
    let location_filter = document.getElementById('filter__location_id');

    if (location_filter != null) {
        resp.forEach((loc) => {
            let options = {
                'type': 'checkbox',
                'class': 'filter',
                'onclick': 'apply_filters()',
                'data-filter_key': 'location_id',
                'data-filter_value': loc.id
            };
            // show only user's location
            if (window.user.location_id == loc.id) options['checked'] = 'checked';

            let filter = createElements(
                el('label', {'class': 'block'},
                    el('input', options),
                    el('span', {}, loc.name)
                )
            );
            location_filter.appendChild(filter);
        });

        new SlimSelect({
            select: document.getElementById('select_location_id'),

            data: resp.map(x => {

                return {value: x.id, text: x.name}
            })
        })
    }
};

const load_username = (resp) => {
    let dept_filter = document.getElementById('filter__department_id');
    console.log("username:",resp)
    new SlimSelect({
        select: document.getElementById('username'),
        data: resp.map(x => {
        console.log("username:",x)
            return {'value': x.id, 'text': x.name}
        })
    });
};





const load_departments = (resp) => {
    let dept_filter = document.getElementById('filter__department_id');

    resp.forEach((dept) => {
        let filter = createElements(
            el('label', {'class': 'block'},
                el('input', {
                    'type': 'checkbox', 'class': 'filter', 'checked': true, 'onclick': 'apply_filters()',
                    'data-filter_key': 'department_id', 'data-filter_value': dept.id
                }),
                el('span', {}, dept.name)
            )
        );
        dept_filter.appendChild(filter);
    });
    new SlimSelect({
        select: document.getElementById('select_department_id'),
        data: resp.map(x => {
            return {'value': x.id, 'text': x.name}
        })
    });
};

const load_designations = (resp) => {
    let desg_filter = document.getElementById('filter__designation_id');

    resp.forEach((desg) => {
        let filter = createElements(
            el('label', {'class': 'block'},
                el('input', {
                    'type': 'checkbox', 'class': 'filter', 'checked': true, 'onclick': 'apply_filters()',
                    'data-filter_key': 'designation_id', 'data-filter_value': desg.id
                }),
                el('span', {}, desg.name)
            )
        );
        desg_filter.appendChild(filter);
    });
    new SlimSelect({
        select: document.getElementById('select_designation_id'),
        data: resp.map(x => {
            return {'value': x.id, 'text': x.name}
        })
    });
};

const load_skills = (resp) => {
    new SlimSelect({
        select: document.getElementById('select_skills_id'),
        data: resp.map(x => {
            return {'value': x.id, 'text': x.name}
        })
    });
};

const load_confirmation_status = (resp) => {
    let visible = ['pending', 'confirmed', 'notice_period'];
    let confirmation_status = document.getElementById('filter__confirmation_status');

    resp.forEach((x) => {
        let options = {
            'type': 'checkbox',
            'class': 'filter',
            'onclick': 'apply_filters()',
            'data-filter_key': 'confirmation_status', 'data-filter_value': x
        };
        if (visible.indexOf(x) != -1) options['checked'] = 'checked';
        let filter = createElements(
            el('label', {'class': 'block'},
                el('input', options),
                el('span', {}, x)
            )
        );
        confirmation_status.appendChild(filter);
    });
};

const get_all_employees = () => {
    return post('get_all_employees/', {}).then(resp => {
        let table = document.getElementById('all_employees');
        table.innerText = "";
        ALL_EMPLOYEES.forEach(employee => {
        console.log(ALL_EMPLOYEES);
            employee.element.remove();

        });
        ALL_EMPLOYEES = [];

        resp.forEach((emp) => {
            let employee = new Employee(emp);
            table.appendChild(employee.element);

            ALL_EMPLOYEES.push(employee);
        });

        document.getElementById('total_employees').innerText = resp.length;
        apply_filters();
    });
};

const add_new_employee = (form) => {
    let form_data = new FormData();

    form_data.append('data', JSON.stringify(formdata(form)));
    form_data.append('profile_picture', form.profile_picture.files[0]);

    post('add_new_employee/', form_data, true).then(resp => {
        hide_modal('add_new_employee');
        get_all_employees();
    })
};

const update_total_count = () => {
    document.getElementById('total_employees').innerText = ALL_EMPLOYEES.filter(employee => {
        return employee.element.style.display !== 'none'
    }).length;
};

const apply_filters = (key = null, input = null) => {
    base_filter(key, input, ALL_EMPLOYEES, update_total_count);
};

window.onload = async () => {
    await init('Employee Manager');

    get_all_locations(load_locations);
    get_all_departments(load_departments);
    get_all_designations(load_designations);
    get_all_skills(load_skills);
    get_all_confirmation_status(load_confirmation_status);
    await get_all_employees();

    hide_loading();
};
