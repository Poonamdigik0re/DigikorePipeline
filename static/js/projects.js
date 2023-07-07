let PROJECT;
let SLIDER;
let RELOAD_TIMELINE_EVENT;
let FILTERS = [];

let TOTAL = {
    'shots': 0,
    'tasks': 0,
    'total_bids': 0,
    'total_actuals': 0,
};

// class ContextMenu {
//     constructor(event, parent) {
//         event.preventDefault();
//         let left = event.clientX;
//         let top = event.clientY;
//         let offset = 5;
//
//         switch (parent.type) {
//             case "project":
//                 this.element = createElements(
//                     el('div', {'class': 'context-menu', 'onmouseleave': 'this.remove()'},
//                         el('div', {'class': 'add-model', 'data-type': 'assetgroup'}, 'Add Asset Group'),
//                         el('div', {'class': 'add-model', 'data-type': 'sequence'}, 'Add Sequence'),
//                     )
//                 );
//                 break;
//             case "shot":
//                 this.element = createElements(
//                     el('div', {'class': 'context-menu', 'onmouseleave': 'this.remove()'},
//                         el('div', {'class': 'add-model', 'data-type': 'task'}, 'Add Task'),
//                         el('div', {'class': 'add-model', 'data-type': 'assetgroup'}, 'Add Asset Group'),
//                     )
//                 );
//                 break;
//             case "task":
//                 this.element = createElements(
//                     el('div', {'class': 'context-menu', 'onmouseleave': 'this.remove()'},
//                         el('div', {'class': 'add-model', 'data-type': 'task'}, 'Add Task'),
//                         el('div', {'class': 'add-model', 'data-type': 'assetgroup'}, 'Add Asset Group'),
//                     )
//                 );
//                 break;
//         }
//
//         // connect the onclick event
//         this.element.querySelectorAll('.add-model').forEach(button => {
//             button.onclick = () => {
//                 add_model(parent, button.dataset['type']);
//             }
//         });
//
//         // append to document body
//         document.body.appendChild(this.element);
//
//         // position the element;
//         (left + this.element.offsetWidth >= window.innerWidth) ?
//             this.element.style.left = left - this.element.offsetWidth - offset + 'px' :
//             this.element.style.left = left - offset + 'px';
//
//         (top + this.element.offsetHeight >= window.innerHeight) ?
//             this.element.style.top = top - this.element.offsetHeight - offset + 'px' :
//             this.element.style.top = top - offset + 'px';
//     }
// }

/* MODELS */

class BaseProjectClass {
    constructor() {
        this.collapsed = false;
        this.visible = true;
        this.selected = false;
    }

    collapse() {
        this.element.querySelector(`.${this.type}-caret`).className = (this.collapsed) ? `${this.type}-caret icon caret-down` : `${this.type}-caret icon caret-right`;
        this.element.querySelectorAll(`.${this.type} > .model-group`).forEach(group => {
            group.style.display = (this.collapsed) ? 'block' : 'none';
        });

        this.timeline.querySelector(`.${this.type}-caret`).className = (this.collapsed) ? `${this.type}-caret icon caret-down` : `${this.type}-caret icon caret-right`;
        this.timeline.querySelectorAll(`.${this.type} > .model-group`).forEach(group => {
            group.style.display = (this.collapsed) ? 'block' : 'none';
        });

        this.collapsed = !this.collapsed;
    }

    post_callbacks() {
        // connect the collapse button
        if (this.element.querySelector(`.${this.type}-caret`) != null) {
            this.element.querySelector(`.${this.type}-caret`).onclick = () => {
                this.collapse()
            };
            this.timeline.querySelector(`.${this.type}-caret`).onclick = () => {
                this.collapse()
            };
        }

        // connect the slider
        [this.element, this.timeline].forEach(elem => {
            elem.querySelector('.clickable').onclick = () => {
                SLIDER.set_parent(this);
                SLIDER.element.querySelector('.parent_name').innerText = this.data.name || this.data.type__name;
                SLIDER.show();
            };
        });

        // show the context menu for all except Asset and Task
        // if (['task'].indexOf(this.type) == -1) {
        //     // connect the context menu
        //     this.element.querySelector('.row').oncontextmenu = (event) => {
        //         new ContextMenu(event, this);
        //     };
        // }

        // connect the edit button
        let edit_button = this.element.querySelector('.item.edit');
        if (edit_button != null) {
            edit_button.onclick = () => {
                post('/base/get_model_info/', {
                    parent_type: this.type,
                    parent_id: this.data.id
                }).then(resp => {
                    let form = document.forms[`add_${this.type}`];
                    for (let key in resp) {
                        if (form.hasOwnProperty(key)) {
                            form[key].value = resp[key];
                            if (form[key].tagName === 'SELECT') {
                                let event = new Event('change');
                                form[key].dispatchEvent(event);
                            }
                        }
                    }
                    add_model(this.parent, this.type, this)
                });
            };
        }

        // // connect the change log button
        // this.element.querySelector('.item.change_log').onclick = () => {
        //     this.get_change_logs();
        //     show_modal('change_logs');
        // };

        // // connect the reload timeline event
        // document.addEventListener('reload_timeline', () => {
        //     this.update_timeline()
        // });

        // // connect websocket add-model event
        // document.addEventListener('wss_add_model', (event) => {
        //     if (event.data.parent_type == this.type && event.data.parent_id == this.data.id) {
        //         load_model(this, event.data, `${event.data.model_type}s`);
        //     }
        // });

        // // connect websocket add-model event
        // document.addEventListener('wss_edit_model', (event) => {
        //     if (event.data.model_type == this.type && event.data.id == this.data.id) {
        //         let row = this.element.querySelector('.row:first-child');
        //
        //         for (let key in event.data) {
        //             let item = row.querySelector(`.${this.type}-${key}`);
        //
        //             if (item) {
        //                 item.innerText = event.data[key] || '-';
        //
        //                 if (key === 'status__name') {
        //                     item.style.backgroundColor = event.data.status__bg_color;
        //                     item.style.color = event.data.status__fg_color;
        //                 }
        //                 if (key == 'end_date' || key == 'start_date') {
        //                     item.innerText = local_date(event.data[key]);
        //                 }
        //             }
        //             // update instance
        //             this.data[key] = event.data[key];
        //         }
        //
        //         // update timeline
        //         this.update_timeline();
        //         // update totals
        //         update_totals();
        //     }
        // });
    }

    update_timeline() {
        if (DATE_RANGE.length === 0) {
            get_date_range();
        }

        let _old = this.timeline.querySelector('.date-ranges');
        let _new = createElements(el('div', {'class': 'flex-grow flex-row date-ranges'},
            ...DATE_RANGE.map((date, index) => {
                let classname = '';

                if (this.data.end_date) {
                    if (datestring(this.data.end_date) == date) {
                        classname += ' end_date';
                    }
                }
                if (this.data.start_date) {
                    if (datestring(this.data.start_date) == date) {
                        classname += ' start-date';
                    }
                }

                if (WEEKENDS.indexOf(date) >= 0) {
                    classname += ' weekend';
                }
                if (HOLIDAYS.indexOf(date) >= 0) {
                    classname += ' holiday';
                }

                return el('div', {'class': classname}, index + 1);
            }))
        );

        this.timeline.querySelector('.row').replaceChild(_new, _old);
    };

    get_change_logs() {
        post('/base/get_change_logs/', {
            parent_type: this.type,
            parent_id: this.data.id
        }).then(resp => {
            let all_change_logs = document.getElementById('all_change_logs');
            all_change_logs.innerHTML = '';

            resp.forEach(data => {
                let logs = createElements(
                    el('tr', {},
                        el('td', {}, data.key),
                        el('td', {}, data.value),
                        el('td', {}, data.created_by__userprofile__full_name),
                        el('td', {}, local_datetime(data.created_on)),
                    )
                );
                all_change_logs.append(logs);
            })
        })
    }
}

class Project extends BaseProjectClass {
    constructor(data) {
        super();
        this.data = data;
        this.type = 'project';

        this.element = createElements(
            el('div', {'class': 'project'},
                el('div', {"class": "row flex-row"},
                    el('div', {'class': 'wp25'},
                        el('div', {'class': 'project-name clickable inline'}, this.data.name),
                    ),
                    el('div', {'class': 'flex-grow'}, ''),
                    el('div', {'class': 'wp5 dropdown align-right'},
                        // el('div', {'class': 'icon list'}, ''),
                        // el('div', {'class': 'menu'},
                        //     el('div', {'class': 'item change_log'}, 'View Changes'),
                        // )
                    ),
                ),
                el('div', {'class': 'model-group shots'}, ''),
            )
        );

        this.timeline = createElements(
            el('div', {'class': 'project'},
                el('div', {"class": "row flex-row"},
                    el('div', {'class': 'wp25'},
                        el('div', {'class': 'project-name clickable inline'}, this.data.name),
                    ),
                    el('div', {'class': 'flex-grow'}, '')
                ),
                el('div', {'class': 'model-group shots'}, ''),
            )
        );

        document.getElementById('project_name').innerText = this.data.name;

        // post callbacks
        this.post_callbacks();

        this.shots = [];

        load_model(this, this.data.shots, 'shots');
    }
}

class Shot extends BaseProjectClass {
    constructor(parent, data) {
        super();
        this.parent = parent;
        this.data = data;
        this.type = 'shot';

        this.element = createElements(
            el('div', {'class': 'shot'},
                el('div', {'class': 'row flex-row'},
                    el('div', {'class': 'wp15 flex-row'},
                        el('div', {'class': 'shot-caret icon caret-down'}, ''),
                        el('div', {'class': 'shot-name clickable'}, this.data.name)
                    ),
                    el('div', {'class': 'wp10 align-center'}, this.data.department),
                    el('div', {'class': 'wp10 align-center'}, 'Shot'),
                    el('div', {
                        'class': 'shot-status__name wp10',
                        'style': `background-color:${this.data.status__bg_color}; color:${this.data.status__fg_color}`
                    }, this.data.status__name),
                    el('div', {'class': 'flex-grow'}, ''),
                    el('div', {'class': 'wp10 dropdown align-right'},
                        // el('div', {'class': 'icon list'}, ''),
                        // el('div', {'class': 'menu'},
                        //     el('div', {'class': 'item edit'}, 'Edit'),
                        //     el('div', {'class': 'item change_log'}, 'View Changes'),
                        // )
                    ),
                ),
                el('div', {'class': 'model-group assetgroups'}, ''),
                el('div', {'class': 'model-group tasks'}, '')
            )
        );

        this.timeline = createElements(
            el('div', {'class': 'shot'},
                el('div', {'class': 'row flex-row'},
                    el('div', {'class': 'wp25 flex-row'},
                        el('div', {'class': 'shot-caret icon caret-down'}, ''),
                        el('div', {'class': 'shot-name clickable'}, this.data.name)
                    ),
                    el('div', {'class': 'flex-grow flex-row date-ranges'}, '')
                ),
                el('div', {'class': 'model-group assetgroups'}, ''),
                el('div', {'class': 'model-group tasks'}, ''),
            )
        );
        // create timeline
        this.update_timeline();
        // run post callback
        this.post_callbacks();

        this.tasks = [];
        this.assetgroups = [];

        load_model(this, this.data.tasks, 'tasks');

        // update search_shots_datalist
        document.getElementById('search_shot_datalist').append(createElements(el('option', {'value': this.data.name}, '')))
    }
}

class Department extends BaseProjectClass {
    constructor(parent, data) {
        super();
        this.parent = parent;
        this.data = data;
        this.type = 'department';
        this.selected = false;
        console.log("ok")

        this.element = createElements(
            el('div', {'class': 'department'},
                el('div', {'class': 'row flex-row'},
                    el('div', {'class': 'wp25'},
                        el('div', {'class': 'department-name clickable inline'}, this.data.name),
                    ),
                    // Add other department-specific elements here
                ),
            )
        );

        // Add any necessary event listeners or functionality here

        // Run post callback if needed
        this.post_callbacks();
    }
}

class Task extends BaseProjectClass {
    constructor(parent, data) {
        super();
        this.parent = parent;
        this.data = data;
        this.type = 'task';
        this.selected = false;

        let actuals = (this.data.actuals > 0) ? (this.data.actuals / 3600 / 8).toFixed(2) : 0;

        this.element = createElements(
            el('div', {'class': 'task'},
                el('div', {'class': 'row flex-row'},
                    el('div', {'class': 'wp25'},
                        // el('input', {'type': 'checkbox', 'class': 'task-selected'}, ''),
                        el('div', {'class': 'task-name clickable inline'}, this.data.name),
                    ),
                    el('div', {
                        'class': 'align-center wp10',
                        'style': `background-color:${this.data.type__bg_color}; color:${this.data.type__fg_color}`
                    }, this.data.type__name),
                    el('div', {
                        'class': 'task-status__name wp10',
                        'style': `background-color:${this.data.status__bg_color}; color:${this.data.status__fg_color}`
                    }, this.data.status__name),
                    el('div', {'class': 'task-bids align-center wp5'},
                        (this.data.bids > 0) ? this.data.bids.toFixed(1) : '-'),
                    el('div', {
                        'class': `task-actuals align-center wp5 ${(actuals > this.data.bids) ? 'color-red bold' : ''}`,
                        'title': seconds_to_hhmm(this.data.actuals)
                    }, actuals),
                    el('div', {'class': 'task-start_date align-center wp10'}, local_date(this.data.start_date)),
                    el('div', {'class': 'task-end_date align-center wp10'}, local_date(this.data.end_date)),
                    el('div', {'class': 'task-assignee__userprofile__full_name align-center wp15'},
                        this.data.assignee__userprofile__full_name || '-'),

                    el('div', {'class': 'wp10 flex-row flex-reverse'},
                        el('div', {'class': 'dropdown align-right'},
                            // el('div', {'class': 'icon list'}, ''),
                            // el('div', {'class': 'menu'},
                            //     el('div', {'class': 'item edit'}, 'Edit'),
                            //     el('div', {'class': 'item change_log'}, 'View Changes'),
                            // )
                        ),
                        el('a', {'href': `/task_overview/${this.data.id}`, 'target': '_blank'},
                            el('div', {'class': 'icon open'}, '')
                        ),
                    ),
                ),
            )
        );

        this.timeline = createElements(
            el('div', {'class': 'task'},
                el('div', {'class': 'row flex-row'},
                    el('div', {'class': 'wp25'},
                        // el('input', {'type': 'checkbox', 'class': 'task-selected'}, ''),
                        el('div', {'class': 'task-name clickable inline'}, this.data.name),
                    ),
                    el('div', {'class': 'flex-grow flex-row date-ranges'}, '')
                ),
            )
        );

        // this.element.querySelector('.task-selected').onclick = (event) => {
        //     this.selected = event.target.checked;
        //
        //     if (this.selected) {
        //         this.element.querySelector('.row').classList.add('highlighted');
        //         document.getElementById('toggle_selected_tasks').checked = true;
        //     } else {
        //         this.element.querySelector('.row').classList.remove('highlighted');
        //     }
        // };

        // create timeline
        this.update_timeline();
        // run post callback
        this.post_callbacks();
    }
}

class Filter {
    constructor(model, action, key, operation, value) {
        console.log(model, action, key, operation, value);

        let filter_keys = {
            'shot': [
                {'value': '', 'text': '', 'placeholder': true},
                {'value': 'sequence', 'text': 'Sequence'},
                {'value': 'status__name', 'text': 'Status'},
                {'value': 'reel', 'text': 'Reel'},
                {'value': 'source_type__name', 'text': 'Source Type'},
                {'value': 'source_status__name', 'text': 'Source Status'}
            ],
            'task': [
                {'value': '', 'text': '', 'placeholder': true},
                {'value': 'type__name', 'text': 'Type'},
                {'value': 'status__name', 'text': 'Status'},
                {'value': 'complexity__name', 'text': 'Complexity'},
                {'value': 'priority__name', 'text': 'Priority'},
                {'value': 'assignee__userprofile__full_name', 'text': 'Assignee'},
                {'value': 'bids', 'text': 'Bids'},
                {'value': 'start_date', 'text': 'Start Date'},
                {'value': 'end_date', 'text': 'End Date'}
            ]
        };

        this.element = createElements(
            el('tr', {},
                el('td', {},
                    el('select', {'name': 'action'}, '')
                ),
                el('td', {},
                    el('select', {'name': 'model'}, '')
                ),
                el('td', {},
                    el('select', {'name': 'key'}, '')
                ),
                el('td', {},
                    el('select', {'name': 'operation'}, '')
                ),
                el('td', {},
                    el('select', {'name': 'value'}, '')
                ),
                el('td', {},
                    el('div', {'class': 'icon trash'}, '')
                )
            )
        );

        this.select_action = new SlimSelect({
            select: this.element.querySelector('select[name="action"]'),
            data: [
                {'text': 'AND', 'value': 'AND'},
                {'text': 'OR', 'value': 'OR'}
            ],
        });

        this.select_model = new SlimSelect({
            select: this.element.querySelector('select[name="model"]'),
            data: [
                {'text': '', 'value': '', 'placeholder': true},
                {'text': 'Task', 'value': 'task'},
                {'text': 'Shot', 'value': 'shot'},
            ],
            placeholder: 'Select Model',
            onChange: (select) => {
                this.select_key.setData(filter_keys[select.value]);
                this.get_values();
            }
        });

        this.select_key = new SlimSelect({
            select: this.element.querySelector('select[name="key"]'),
            placeholder: 'Select Key',
            onChange: (select) => {
                this.get_values(value);
            }
        });

        this.select_operation = new SlimSelect({
            select: this.element.querySelector('select[name="operation"]'),
            data: [
                {'text': 'Equals to', 'value': '='},
                {'text': 'Not Equals to', 'value': '!='},
                {'text': 'Greater than', 'value': '>'},
                {'text': 'Less than', 'value': '<'},
            ],
        });

        this.select_value = new SlimSelect({
            select: this.element.querySelector('select[name="value"]'),
        });

        this.element.querySelector('.icon.trash').onclick = () => {
            this.element.remove();
            FILTERS.splice(FILTERS.indexOf(this), 1);
        };

        if (action != null) this.select_action.set(action);
        if (model != null) this.select_model.set(model);
        if (key != null) this.select_key.set(key);
        if (operation != null) this.select_operation.set(operation);
        if (value != null) this.select_value.set(value);

        document.getElementById('tbody_filters').append(this.element);
    }

    get_values(value = null) {
        let model = this.select_model.selected();
        let key = this.select_key.selected();

        if (model != '' && key != '') {
            post('get_filter_values/', {'model': model, 'key': key}).then(resp => {
                this.select_value.setData(resp.map(x => {
                    return {'text': x, 'value': x}
                }));

                if (value) this.select_value.set(value)
            });
        }
    }
}

const load_model = (parent, data, model_type) => {
    if (data.constructor === Object) data = [data];

    data.forEach(d => {
        let model;
        switch (model_type) {
            case "tasks":
                model = new Task(parent, d);
                break;
            case "shots":
                model = new Shot(parent, d);
                break;
        }
        parent.element.querySelector(`.${parent.type} > .${model_type}`).appendChild(model.element);
        parent.timeline.querySelector(`.${parent.type} > .${model_type}`).appendChild(model.timeline);
        parent[model_type].push(model);
    })
};

const update_model = (parent, type, instance = null) => {
    /*
     Add new model
     parent = parent element's class
     type = type of current model, string
     instance = instance of the current model when updating;
    */

    show_modal(`add_${type}`);
    let form = document.forms[`add_${type}`];

    // add, update model
    form.onsubmit = (event) => {
        event.preventDefault();

        let data = formdata(form);
        data['parent_id'] = parent.data.id;
        data['parent_type'] = parent.type;
        data['project_id'] = PROJECT.data.id;
        // set model value
        data['model_type'] = type;
        data['model_id'] = (instance) ? instance.data.id : '';

        post('update_model/', data).then(resp => {
            hide_modal(`add_${type}`);
        });
    }
};

const toggle_view = (input) => {
    if (input.checked) {
        let top = document.getElementById('container').scrollTop;
        document.getElementById('project_view').style.display = 'none';
        document.getElementById('timeline_view').style.display = 'flex';

        document.getElementById('timeline').scrollTop = top;

    } else {
        let top = document.getElementById('timeline').scrollTop;
        document.getElementById('project_view').style.display = 'flex';
        document.getElementById('timeline_view').style.display = 'none';

        document.getElementById('container').scrollTop = top;
    }
};

const get_data = (queries = {}) => {
    return post('get_data/', {queries: queries}).then(resp => {
        let btn_vault_url = document.getElementById('vault_url');
        if (resp.vault_url != null) {
            btn_vault_url.disabled = false;
            btn_vault_url.onclick = () => {
                window.open(resp.vault_url)
            }
        } else {
            btn_vault_url.disabled = true;
        }

        let container = document.getElementById('container');
        let timeline = document.getElementById('timeline');

        // clean shot search list
        document.getElementById('search_shot_datalist');

        container.innerText = '';
        timeline.innerText = '';

        PROJECT = new Project(resp);
        container.appendChild(PROJECT.element);
        timeline.appendChild(PROJECT.timeline);

        // apply the queries
        if (Object.keys(queries).length != 0) {
            hide_blanks();
        }

        // set title;
        document.title = `Project: ${resp.name}`;
        update_totals();
    })
};

const get_defaults = () => {
    return post('get_defaults/', {}).then(resp => {
        // update status
        ['project_status', 'shot_status', 'task_complexity', 'task_priority', 'task_status', 'task_type'].map(type => {
            let select = document.getElementById(`select_${type}`);
            if (select) {
                new SlimSelect({
                    select: select,
                    data: resp[type].map(x => {
                        return {'value': x.id, 'text': x.name, 'selected': x.default || false};
                    }),
                });
            }
        });

        // for updating multiple
        ['task_complexity', 'task_priority', 'task_status', 'task_type'].map(type => {
            let select = document.getElementById(`multi_select_${type}`);
            if (select) {
                new SlimSelect({
                    select: select,
                    data: [{'text': '', 'value': '', 'placeholder': true}].concat(resp[type].map(x => {
                        return {'value': x.id, 'text': x.name};
                    })),
                });
            }
        });

        /*
        set task assignee
        */
        new SlimSelect({
            select: document.getElementById('select_task_assignee'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.users.map(x => {
                return {'value': x.id, 'text': x.userprofile__full_name}
            })),
            placeholder: 'Select Assignee',
        });

        /*
        set task assignee / for edit multiple
        */
        new SlimSelect({
            select: document.getElementById('multi_select_task_assignee'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.users.map(x => {
                return {'value': x.id, 'text': x.userprofile__full_name}
            })),
            placeholder: 'Select Assignee',
        });

        /*
        set task vendor
        */
        new SlimSelect({
            select: document.getElementById('select_task_vendor'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.vendors.map(x => {
                return {'value': x.id, 'text': x.name}
            })),
            placeholder: 'Select Vendor',
        });

        /*
       set task vendor / for edit multiple
       */
        new SlimSelect({
            select: document.getElementById('multi_select_task_vendor'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.vendors.map(x => {
                return {'value': x.id, 'text': x.name}
            })),
            placeholder: 'Select Vendor',
        });

        // update company holidays;
        resp.holidays.forEach(date => {
            HOLIDAYS.push(datestring(date));
        })
    });
};

// const upload_csv = () => {
//     show_loading();
//     let csv_selector = document.getElementById('csv_selector');
//     csv_selector.click();
//
//     csv_selector.onchange = (event) => {
//         event.preventDefault();
//         let form_data = new FormData();
//         form_data.append('csv', csv_selector.files[0]);
//
//         post('upload_csv_template/', form_data, true).then(resp => {
//             location.reload();
//         });
//     }
// };

// const update_selected_tasks = (form) => {
//     let selected_tasks = [];
//
//     // get all selected tasks
//     PROJECT.sequences.forEach(sequence => {
//         sequence.shots.forEach(shot => {
//             shot.tasks.forEach(task => {
//                 if (task.selected) {
//                     selected_tasks.push(task.data.id);
//                 }
//             })
//         })
//     });
//
//     if (selected_tasks.length > 0) {
//         if (confirm(`Are you sure you want to update ${selected_tasks.length} tasks?`)) {
//             let data = formdata(form);
//             data['task_ids'] = selected_tasks;
//             post('update_selected_tasks/', data).then(resp => {
//                 hide_modal('update_selected_tasks');
//             });
//         }
//     } else {
//         alert('Nothing is selected')
//     }
// };

// const toggle_selected_tasks = (input) => {
//     // get all selected tasks
//     PROJECT.sequences.forEach(sequence => {
//         sequence.shots.forEach(shot => {
//             shot.tasks.forEach(task => {
//                 if (shot.visible) {
//                     task.selected = input.checked;
//                     task.element.querySelector('.task-selected').checked = input.checked;
//                     if (task.selected) {
//                         task.element.querySelector('.row').classList.add('highlighted');
//                     } else {
//                         task.element.querySelector('.row').classList.remove('highlighted');
//                     }
//                 } else {
//                     task.selected = false;
//                     task.element.querySelector('.task-selected').checked = false;
//                     task.element.querySelector('.row').classList.remove('highlighted');
//                 }
//             })
//         })
//     });
// };

/*
    COLLAPSE / EXPAND
*/

const toggle_shot = (parent, value) => {
    parent.shots.forEach(shot => {
        shot.collapsed = value;
        shot.collapse();
    });
};
const expand_all = () => {
    toggle_shot(PROJECT, true);
};
const collapse_all = () => {
    toggle_shot(PROJECT, false);
};

/* UPDATE TOTALS */

const total_tasks = (parent) => {
    parent.tasks.forEach(task => {
        if (task.visible) {
            ++TOTAL['tasks'];
            TOTAL['total_bids'] += task.data.bids;
            TOTAL['total_actuals'] += task.data.actuals;
        }
    });
};

const total_shots = (parent) => {
    parent.shots.forEach(shot => {
        if (shot.visible) {
            ++TOTAL['shots'];
            total_tasks(shot);
            // total_assetgroups(shot);
        }
    })
};
const update_totals = () => {
    TOTAL = {
        'shots': 0,
        'tasks': 0,
        'total_bids': 0,
        'total_actuals': 0,
    };
    total_shots(PROJECT);

    let actuals = TOTAL['total_actuals'] / 3600 / 8;

    document.getElementById('total_count').innerText = `Shots:${TOTAL['shots']} / Tasks:${TOTAL['tasks']}`;
    document.getElementById('total_bids').innerText = (TOTAL['total_bids']).toFixed(2);
    document.getElementById('total_actuals').innerText = (actuals).toFixed(2);

    if (actuals > TOTAL['total_bids']) {
        document.getElementById('total_actuals').style.color = 'red';
    } else {
        document.getElementById('total_actuals').style.color = 'black';
    }
};

const hide_blanks = () => {
    PROJECT.shots.forEach(shot => {
        if (shot.tasks.length == 0 || shot.tasks.filter(task => {
            return task.visible == true
        }).length == 0) {
            shot.element.style.display = 'none';
            shot.timeline.style.display = 'none';
            shot.visible = false;
        }
    });
    update_totals();
};

const apply_filters = async (clear = false) => {
    let filters = {};
    if (!clear) {
        FILTERS.forEach(x => {
            let model = x.select_model.selected();
            let action = x.select_action.selected();
            let key = x.select_key.selected();
            let operation = x.select_operation.selected();
            let value = x.select_value.selected();
            if (model != "" && action != "" && key != "" && operation != "" && value != "") {
                if (filters[model] == undefined) filters[model] = [];

                filters[model].push([
                    x.select_action.selected(),
                    x.select_key.selected(),
                    x.select_operation.selected(),
                    x.select_value.selected()
                ]);
            }
        });
    }
    window.search['queries'] = filters;
    location.hash = encodeURIComponent(JSON.stringify(window.search));
    await get_data(queries = filters);
    // hide modal
    hide_modal('filters');
};

const add_filter = (model = null, action = null, key = null, operation = null, value = null) => {
    let filter = new Filter(model, action, key, operation, value);
    FILTERS.push(filter);
};

const load_search_queries = () => {
    let queries = window.search.queries;
    for (let model in queries) {
        queries[model].forEach(query => {
            add_filter(model, ...query);
        });
    }
};

window.onload = async () => {
    await init();
    // init_websocket();

    RELOAD_TIMELINE_EVENT = new Event('reload_timeline');

    // add slider
    SLIDER = new Slider();
    document.getElementById('modals').append(SLIDER.element);

    // set current month into calendar view
    let select__month = document.getElementById('select__month');
    select__month.value = new Date().toISOString().substr(0, 7);
    select__month.addEventListener('change', () => {
        load_timeline_header();
        document.dispatchEvent(RELOAD_TIMELINE_EVENT);
    });

    // setup the search shot input
    let search_shot = document.getElementById('search_shot');
    search_shot.onchange = () => {
        let search_text = search_shot.value.split(' ');

        // start by showing everything
        PROJECT.shots.forEach(shot => {
            shot.element.style.display = 'block';
            shot.timeline.style.display = 'block';
            shot.visible = true;
        });

        if (search_text instanceof Array) {
            if (search_text[0] != "") {
                PROJECT.shots.forEach(shot => {
                    if (search_text.indexOf(shot.data.name) == -1) {
                        shot.element.style.display = 'none';
                        shot.timeline.style.display = 'none';
                        shot.visible = false;
                    }
                });
                hide_blanks();
            }
        }
    };

    // load the query builder
    let queries = window.search['queries'] || {};

    // get some data
    await get_defaults();
    await get_data(queries);
    await load_search_queries();

    load_timeline_header();
    hide_loading();
};
