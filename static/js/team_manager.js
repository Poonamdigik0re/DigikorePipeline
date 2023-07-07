let ALL_TEAMS = [];
let ALL_EMPLOYEES = {};

class Team {
    constructor(data) {
        this.data = data;
        this.members = [];
        this.element = createElements(
            el('div', {'class': 'flex-column team-container'},
                el('div', {
                        'class': 'flex-row flex-no-shrink p5 team-name',
                    },
                    el('div', {'class': 'flex-grow'}, `${this.data.department__name}`),

                ),
                el('div', {'class': 'flex-row flex-no-shrink p5 team-lead-name'},
                    el('div', {'class': 'flex-grow'}, this.data.lead__userprofile__full_name),
                    el('div', {'class': 'members-count'}, '')
                ),
                el('ul', {
                    'data-team_id': this.data.id,
                    'class': 'flex-grow team-employees-list',
                    'ondrop': 'add_team_member(event, this)',
                    'ondragover': 'allowDrop(event)',
                })
            )
        );
        console.log(this.data.department__name);
        this.element.dataset['display'] = 'flex';

        this.element.querySelector('ul').parent = this;
    }

    update_members() {
        let list = this.element.querySelector('ul');
        list.innerText = "";
        this.members.forEach(member => {
            list.append(member.element)
        });
        this.update_count();
    }

    update_count() {
        this.element.querySelector('.members-count').innerText = this.members.length;
    }
}

class Employee {
    constructor(data) {
        this.data = data;
        this.element = createElements(el('li', {
            'draggable': true,
            'ondragstart': 'dragstart(event)',
        }, this.data.full_name));

        this.element.parent = this;
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

const load_shift = (resp) => {
    let team_shift = document.getElementById('new_team_shift');
    let shift_filter = document.getElementById('filter__shift_id');

    resp.forEach((shift) => {
        let element = createElements(el('option', {'value': shift.id}, shift.name));
        team_shift.append(element);

//        let filter = createElements(
//            el('label', {'class': 'block'},
//                el('input', {
//                    'type': 'checkbox', 'class': 'filter', 'checked': true, 'onclick': 'apply_filters()',
//                    'data-filter_key': 'shift_id', 'data-filter_value': shift.id
//                }),
//                el('span', {}, shift.name)
//            )
//        );
//        shift_filter.appendChild(filter)
    });

    new SlimSelect({
        select: team_shift,
        placeholder: "Select Shift Time"
    });
};





const load_departments = (resp) => {
    let new_team_dept = document.getElementById('new_team_department');
    let dept_filter = document.getElementById('filter__department_id');

    resp.forEach((dept) => {
        let element = createElements(el('option', {'value': dept.id}, dept.name));
        new_team_dept.append(element);

        let filter = createElements(
            el('label', {'class': 'block'},
                el('input', {
                    'type': 'checkbox', 'class': 'filter', 'checked': true, 'onclick': 'apply_filters()',
                    'data-filter_key': 'department_id', 'data-filter_value': dept.id
                }),
                el('span', {}, dept.name)
            )
        );
        dept_filter.appendChild(filter)
    });

    new SlimSelect({
        select: new_team_dept,
        placeholder: "Select Department"
    });
};

const get_all_teams = (resp) => {
    return post('get_all_teams/', {}).then(resp => {
        let all_teams = document.getElementById('all_teams');
        console.log(all_teams);
        console.log(resp);
        resp.forEach((data) => {
            let team = new Team(data);
            all_teams.append(team.element);
            ALL_TEAMS.push(team);
        });
    });
};

const get_all_employees = () => {
    return post('get_all_employees/',).then(resp => {
        let all_employees = document.getElementById('all_employees');
        let new_team_lead = document.getElementById('new_team_lead');

        resp.forEach((data) => {
            let emp = new Employee(data);

            if (data.team_id) {
                ALL_TEAMS.filter(team => {
                    if (team.data.id === data.team_id) {
                        team.members.push(emp);
                    }
                });

            } else {
                all_employees.appendChild(emp.element);
            }

            // add into new team form
            let element = createElements(el('option', {'value': data.user_id}, data.full_name));
            new_team_lead.append(element);

            ALL_EMPLOYEES[emp.data.user_id] = emp;
        });

        ALL_TEAMS.filter(team => {
            team.update_members();
        });

        new SlimSelect({
            select: new_team_lead,
            placeholder: "Select Team Lead",
        });
    });
};

const add_new_team = (form) => {
    return post('add_new_team/', {
        department_id: form.department_id.value,
        lead_id: form.lead_id.value,
        shift_id: form.shift_id.value
    }).then(resp => {
        location.reload();
    });
};



const add_team_member = (event, team) => {
    event.preventDefault();

    let user_id = event.dataTransfer.getData('user_id');
    let team_id = team.dataset['team_id'];
    let user = ALL_EMPLOYEES[user_id];

    // remove the user from existing team
    ALL_TEAMS.filter(team => {
        if (team.data.id === user.data.team_id) {
            team.members.splice(team.members.indexOf(user), 1);
            team.update_count();
        }
    });

    return post('add_team_member/', {
        team_id: team_id,
        user_id: user_id
    }).then(resp => {
        user.data.team_id = parseInt(team_id);

        // add the user to new team
        if (team_id != 0) {
            ALL_TEAMS.filter(team => {
                if (team.data.id === user.data.team_id) {
                    team.members.push(user);
                    team.update_members();
                }
            });
        } else {
            team.appendChild(user.element);
        }
    })
};

const dragstart = (event) => {
    event.dataTransfer.setData('user_id', event.target.parent.data.user_id)
};

const allowDrop = (event) => {
    event.preventDefault();
};

const apply_filters = (key = null, input = null) => {
    base_filter(key, input, ALL_TEAMS);
};

window.onload = async () => {
    await init('Team Manager');

    get_all_locations(load_locations);
    get_all_departments(load_departments);
    get_all_shifts(load_shift);
    await get_all_teams();
    await get_all_employees();

    apply_filters();

    hide_loading();
};