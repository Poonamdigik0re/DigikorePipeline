let ALL_USERS = [];

class User {
    constructor(data) {
        this.data = data;
        this.visible = true;

        this.element = createElements(
            el('tr', {},
                el('td', {}, this.data.full_name),
                el('td', {}, this.data.department__name),
                el('td', {}, this.data.designation__name),
                el('td', {},
                    el('input', {'type': 'checkbox', 'class': 'font-lg'}, '')
                )
            )
        );

        let input_element = this.element.querySelector('input');
        input_element.checked = this.data.checked;
        input_element.onchange = (input) => {
            this.data.checked = !input.checked;
        }
    }
}

const load_departments = (resp) => {
    new SlimSelect({
        select: document.getElementById('select__department_id'),
        data: [{'placeholder': true, 'text': '', 'value': ''}].concat(resp.map(x => {
            return {'value': x.id, 'text': x.name}
        })),
        allowDeselect: true,
        onChange: function () {
            apply_filters();
        },
        placeholder: "Select Department"
    });
};

const load_designations = (resp) => {
    new SlimSelect({
        select: document.getElementById('select__designation_id'),
        data: [{'placeholder': true, 'text': '', 'value': ''}].concat(resp.map(x => {
            return {'value': x.id, 'text': x.name}
        })),
        allowDeselect: true,
        onChange: function () {
            apply_filters();
        },
        placeholder: "Select Department"
    });
};

const get_users = () => {
    return post('get_users/', {}).then(resp => {
        let all_users = document.getElementById('all_users');
        all_users.innerText = "";
        ALL_USERS = [];

        resp.forEach(data => {
            let user = new User(data);
            all_users.append(user.element);

            ALL_USERS.push(user);
        })
    })
};

const select_all_users = (input) => {
    ALL_USERS.forEach(user => {
        if (user.visible) {
            user.element.querySelector('input').checked = input.checked;
            user.data.checked = input.checked;
        }
    })
};

const save_permissions = () => {
    let users = ALL_USERS.filter(user => user.data.checked).map(user => user.data.user_id);

    show_loading();
    post('save_permissions/', {'users': users}).then(resp => {
        hide_loading();
    });
};

apply_filters = () => {
    let name = document.getElementById('select__name').value;
    let department_id = document.getElementById('select__department_id').value;
    let designation_id = document.getElementById('select__designation_id').value;

    ALL_USERS.forEach(user => {
        user.element.style.display = 'table-row';
        user.visible = true;

        if (name && user.data.full_name.toLowerCase().indexOf(name.toLowerCase()) == -1) {
            user.element.style.display = 'none';
            user.visible = false;
        }
        if (department_id && user.data.department_id != department_id) {
            user.element.style.display = 'none';
            user.visible = false;
        }
        if (designation_id && user.data.designation_id != designation_id) {
            user.element.style.display = 'none';
            user.visible = false;
        }
    });

    document.getElementById('select_all_users').checked = false;
};

window.onload = async () => {
    await init('Project Permission');
    get_all_departments(load_departments);
    get_all_designations(load_designations);
    await get_users();

    hide_loading()
};