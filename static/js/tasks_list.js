let ALL_TASKS = [];

class Task {
    constructor(data) {
        this.data = data;
        console.log("*:",this.data);
        this.type = 'task';

        let bids = (this.data.subtask) ? this.data.bids : this.data.bids;
        let actuals = (this.data.subtask) ? (this.data.subtask__actuals / 3600 / 8).toFixed(2) : (this.data.actuals / 3600 / 8).toFixed(2);

        this.element = createElements(
            el('tr', {},
                el('td', {'class': 'text-overflow'}, this.data.project__name),
                el('td', {'class': 'text-overflow'}, this.data.sequence__name),
                el('td', {'class': 'text-overflow'}, this.data.shot__name),
                el('td', {'class': 'text-overflow'}, this.data.name),
                el('td', {'class': 'text-overflow'}, this.data.subtask__name || '-'),
                el('td', {'class': 'text-overflow'}, this.data.type__name),
                el('td', {'class': 'align-center', 'style': 'width: 8em'}, bids || 0),
                el('td', {'class': 'align-center', 'style': 'width: 8em'}, actuals || 0),
                el('td', {
                    'class': 'align-center',
                    'style': `font-weight: bold; color:${this.data.status__fg_color}`
                }, this.data.status__name),
                el('td', {'class': 'align-center'}, this.data.assignee__userprofile__full_name)
            )
        );

        this.element.onclick = () => {
            window.open(`/task_overview/${this.data.id}/`);
        }
    }
}

const get_all_users = () => {
    post('get_all_users/', {}).then(resp => {
        // Select Client
        new SlimSelect({
            select: document.getElementById('select__user_id'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.map(x => {
                return {'value': x.id, 'text': x.userprofile__full_name}
            })),
            placeholder: "Select User",
            onChange: function (select) {
                get_user_tasks(select.value);
            }
        });
    })
};

//const get_user_tasks = (user_id = null) => {
//    show_loading();
//    post('get_user_tasks/', {user_id: user_id}).then(resp => {
//        let tasks_table = document.getElementById('user_tasks_table');
//        tasks_table.innerText = '';
//
//        let projects = [];
//        let task_statuses = [];
//
//        let filter__projects = document.getElementById('filter__projects');
//        let filter__task__status = document.getElementById('filter__task__status');
//
//        // clear filters
//        filter__projects.innerHTML = '<label class="block bold"><input type="checkbox" onchange="apply_filters(\'project__name\', this)" checked="checked"><span>Select All</span></label>';
//        filter__task__status.innerHTML = '<label class="block bold"><input type="checkbox" onchange="apply_filters(\'status_id\', this)" checked="checked"><span>Select All</span></label>';
//
//        resp.forEach(data => {
//            let task = new Task(data);
//            tasks_table.append(task.element);
//            ALL_TASKS.push(task);
//
//            if (projects.indexOf(data.project__name) == -1) {
//                projects.push(data.project__name);
//
//                let filter = createElements(
//                    el('label', {'class': 'block'},
//                        el('input', {
//                            'type': 'checkbox', 'class': 'filter', 'checked': true, 'onclick': 'apply_filters()',
//                            'data-filter_key': 'project__name', 'data-filter_value': data.project__name
//                        }),
//                        el('span', {}, data.project__name)
//                    )
//                );
//                filter__projects.appendChild(filter);
//            }
//
//            if (task_statuses.indexOf(data.status_id) == -1) {
//                task_statuses.push(data.status_id);
//
//                let filter = createElements(
//                    el('label', {'class': 'block'},
//                        el('input', {
//                            'type': 'checkbox', 'class': 'filter', 'checked': true, 'onclick': 'apply_filters()',
//                            'data-filter_key': 'status_id', 'data-filter_value': data.status_id
//                        }),
//                        el('span', {}, data.status__name)
//                    )
//                );
//                filter__task__status.appendChild(filter);
//
//            }
//        });
//
//        hide_loading();
//    })
//};

const get_user_tasks = (user_id = null) => {
    show_loading();
    post('get_user_tasks/', {user_id: user_id}).then(resp => {
        console.log("user:",user_id)
        console.log("resp:",resp)
        let tasks_table = document.getElementById('user_tasks_table');
        tasks_table.innerText = '';

        let projects = [];
        let task_statuses = [];

        let filter__projects = document.getElementById('filter__projects');
        let filter__task__status = document.getElementById('filter__task__status');

        // clear filters
        filter__projects.innerHTML = '<label class="block bold"><input type="checkbox" onchange="apply_filters(\'project__name\', this)"><span>Select All</span></label>';
        filter__task__status.innerHTML = '<label class="block bold"><input type="checkbox" onchange="apply_filters(\'status_id\', this)"><span>Select All</span></label>';

        resp.forEach(data => {
            console.log("$:",data)
            let task = new Task(data);
            tasks_table.append(task.element);
            ALL_TASKS.push(task);

            if (projects.indexOf(data.project__name) == -1) {
                projects.push(data.project__name);

                let filter = createElements(
                    el('label', {'class': 'block'},
                        el('input', {
                            'type': 'checkbox', 'class': 'filter', 'onclick': 'apply_filters()',
                            'data-filter_key': 'project__name', 'data-filter_value': data.project__name
                        }),
                        el('span', {}, data.project__name)

                    )
                );
                filter__projects.appendChild(filter);
            }

            if (task_statuses.indexOf(data.status_id) == -1) {
                task_statuses.push(data.status_id);

                let filter = createElements(
                    el('label', {'class': 'block'},
                        el('input', {
                            'type': 'checkbox', 'class': 'filter', 'onclick': 'apply_filters()',
                            'data-filter_key': 'status_id', 'data-filter_value': data.status_id
                        }),
                        el('span', {}, data.status__name)
                    )
                );
                filter__task__status.appendChild(filter);

            }
        });


        hide_loading();
    })
};

//const get_all_tasks = () => {
//    show_loading();
//    post('show_tasks/').then(resp => {
//        let tasks_table = document.getElementById('user_tasks_table');
//        tasks_table.innerText = '';
//
//        let projects = [];
//        let task_statuses = [];
//
//        let filter__projects = document.getElementById('filter__projects');
//        let filter__task__status = document.getElementById('filter__task__status');
//
//        // clear filters
//        filter__projects.innerHTML = '<label class="block bold"><input type="checkbox" onchange="apply_filters(\'project__name\', this)"><span>Select All</span></label>';
//        filter__task__status.innerHTML = '<label class="block bold"><input type="checkbox" onchange="apply_filters(\'status_id\', this)"><span>Select All</span></label>';
//
//        resp.forEach(data => {
//            let task = new Task(data);
//            tasks_table.append(task.element);
//            ALL_TASKS.push(task);
//
//            if (projects.indexOf(data.project__name) == -1) {
//                projects.push(data.project__name);
//
//                let filter = createElements(
//                    el('label', {'class': 'block'},
//                        el('input', {
//                            'type': 'checkbox', 'class': 'filter', 'onclick': 'apply_filters()',
//                            'data-filter_key': 'project__name', 'data-filter_value': data.project__name
//                        }),
//                        el('span', {}, data.project__name)
//                    )
//                );
//                filter__projects.appendChild(filter);
//            }
//
//            if (task_statuses.indexOf(data.status_id) == -1) {
//                task_statuses.push(data.status_id);
//
//                let filter = createElements(
//                    el('label', {'class': 'block'},
//                        el('input', {
//                            'type': 'checkbox', 'class': 'filter', 'onclick': 'apply_filters()',
//                            'data-filter_key': 'status_id', 'data-filter_value': data.status_id
//                        }),
//                        el('span', {}, data.status__name)
//                    )
//                );
//                filter__task__status.appendChild(filter);
//
//            }
//        });
//
//        hide_loading();
//    })
//};


const apply_filters = (key = null, input = null) => {
    base_filter(key, input, ALL_TASKS);
};

const load_departments = (resp) => {
    new SlimSelect({
        select: document.getElementById('select_department_id'),
        data: resp.map(x => {
            return {'value': x.id, 'text': x.name}
        })
    });
};

const load_task_priority = () => {
  return post('get_task_priority/', {}).then(response => {
    const selectElement = document.getElementById('select-task_priority');
    const taskPriorities = response.task_priorities;

    // Clear existing options
    selectElement.innerHTML = '';

    // Create a placeholder option
    const placeholderOption = document.createElement('option');
    placeholderOption.value = '';
    placeholderOption.text = 'Select task priority';
    placeholderOption.disabled = true;
    placeholderOption.selected = true;
    selectElement.appendChild(placeholderOption);

    // Create options for each task priority
    taskPriorities.forEach(taskPriority => {
      const option = document.createElement('option');
      option.value = taskPriority.id;
      option.text = taskPriority.name;
      selectElement.appendChild(option);
    });

    // Initialize SlimSelect
    new SlimSelect({
      select: selectElement,
      placeholder: 'Select task priority'
    });
  });
};


const get_task_status = () => {
  return post('get_task_status/', {}).then(response => {
    const selectElement = document.getElementById('select-task_statuses');
    const taskStatuses = response.task_statuses;

    // Clear existing options
    selectElement.innerHTML = '';

    // Create a placeholder option
    const placeholderOption = document.createElement('option');
    placeholderOption.value = '';
    placeholderOption.text = 'Select task status';
    placeholderOption.disabled = true;
    placeholderOption.selected = true;
    selectElement.appendChild(placeholderOption);

    // Create options for each task status
    taskStatuses.forEach(taskStatus => {
      const option = document.createElement('option');
      option.value = taskStatus.id;
      option.text = taskStatus.name;
      selectElement.appendChild(option);
    });

    // Initialize SlimSelect
    new SlimSelect({
      select: selectElement,
//      placeholder: 'Select task status'
    });
  });
};


const get_projects = (resp) => {
   return post('get_projects/', {}).then(resp => {
         new SlimSelect({
        select: document.getElementById('select_project_id'),
            data: [{text: '', value: '', placeholder: true}].concat(resp.map(r=> {
                return {'value': r.id, 'text': r.name }
            })),
            placeholder: 'Select Project'
    });

    })
};

const load_task_assign_to = (resp) => {
    return post('get_assignee/', {}).then(resp => {
        new SlimSelect({
            select: document.getElementById('select_task_assignee'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.map(x => {
                return {'value': x.id, 'text': x.userprofile__full_name}
            })),
            placeholder: 'Select Assignee',
        });
    })
};



//const add_new_task = (form) => {
//    show_loading();
//    let form_data = new FormData();
//
//    // Get the selected values from the dropdowns
//    let departmentDropdown = new SlimSelect({
//        select: document.getElementById('select-department_type')
//    });
//    let projectDropdown = new SlimSelect({
//        select: document.getElementById('select-project_name')
//    });
//    let employeeDropdown = new SlimSelect({
//        select: document.getElementById('select-emp_id')
//    });
//    let taskStatusDropdown = new SlimSelect({
//        select: document.getElementById('select-task_status')
//    });
//    let taskPriorityDropdown = new SlimSelect({
//        select: document.getElementById('select-task_priority')
//    });
//
//    // Append the selected values to the form data
//    form_data.append('department_id', departmentDropdown.selected());
//    form_data.append('project_id', projectDropdown.selected());
//    form_data.append('task_assign_id', employeeDropdown.selected());
//    form_data.append('task_status_id', taskStatusDropdown.selected());
//    form_data.append('task_priority', taskPriorityDropdown.selected());
//
//    // ... (rest of the code remains the same)
//};

// Call the function to populate the dropdowns before executing add_new_task
//populateDropdowns();
//
//const add_task = (form) => {
//    let data = formdata(form);
//    post('task_list/add_new_task/', data).then(resp => {
//        hide_modal('add_task');
//        get_all_tasks(resp.id);
//    });
//}

//const add_new_task = (form) => {
//    show_loading();
//    let form_data = new FormData();
//    form_data.append('data', JSON.stringify(formdata(form)));
    //form_data.append('thumbnail', form.thumbnail.files[0]);

//    post('add_new_task/', form_data, true).then(resp => {
//        get_projects();
//        get_user_tasks();
//        hide_modal('add_new_task');

//        hide_loading();
//        const inputFields = form.querySelectorAll('input, select, textarea');
//        inputFields.forEach(field => {
//            field.value = '';
//        });
//    })
//};
const add_new_task = (form) => {
    let form_data = new FormData();
    form_data.append('data', JSON.stringify(formdata(form)));

    post('add_new_task/', form_data, true)
        .then(resp => {
            hide_modal('add_new_task');
            const inputFields = form.querySelectorAll('input, select, textarea');
            inputFields.forEach(field => {
                field.value = '';
            });
        })
        .catch(error => {
            console.error(error);
        });
};

window.onload = async () => {-
    await init('Tasks List');
    if (has_permission('tasks_list')) {
        get_all_users();
        get_projects();
    }
    get_all_departments(load_departments);
    get_task_status(get_task_status);
    load_task_priority();
    load_task_assign_to();
//   add_task();
//    populateDropdowns();
    get_user_tasks();
    add_new_task();
    get_all_tasks();
    hide_loading()
};