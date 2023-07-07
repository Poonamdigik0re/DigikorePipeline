let PROJECT;
let SLIDER;
let FILERECORDS = [];

const add_subtask = (parent, type, instance = null) => {
    show_modal(`add_${type}`);
    let form = document.forms[`add_${type}`];

    // add, update model
    form.onsubmit = (event) => {
        event.preventDefault();

        let data = formdata(form);
        // set model value
        data['project_id'] = PROJECT.data.id;
        data['parent_type'] = parent.type;
        data['parent_id'] = parent.data.id;
        data['model_id'] = (instance) ? instance.data.id : '';

        post('add_subtask/', data).then(resp => {
            if (instance) {
                let row = instance.element.querySelector('.row:first-child');
                for (let key in resp) {
                    let item = row.querySelector(`.${instance.type}-${key}`);

                    if (item) {
                        item.innerText = resp[key] || '-';

                        if (key === 'status__name') {
                            item.style.backgroundColor = resp.status__bg_color;
                            item.style.color = resp.status__fg_color;
                        }
                    }
                    // update instance
                    instance.data[key] = resp[key];
                }

            } else {
                let subtask = new Subtask(resp, parent);
                parent.element.querySelector('.subtasks').append(subtask.element);
            }
            hide_modal(`add_${type}`);
        });
    }
};


class Video {
    constructor(project, name, version) {
        this.element = createElements(
            el('form', {'class': 'modal dark flex-column flex-screen-center', 'method': 'post', 'action': ''},
                el('div', {'class': 'video-close'}, ''),
                el('div', {'class': 'dialog w60 flex-column'},
                    el('video', {'controls': '', 'autoplay': '', 'loop': '', 'class': 'wp100 hp100'},
                        el('source', {
                            'type': 'video/mp4',
                            'src': `/proxy/${project}/proxies/${name}_v${version}.mp4`
                        }, '')
                    )
                )
            )
        );

        // attact the close button
        this.element.querySelector('.video-close').onclick = () => {
            this.element.remove();
        };

        // append to document
        document.getElementById('modals').append(this.element);
        this.element.style.display = 'flex';
    }
}

class Filerecord {
    constructor(data, group) {
        this.data = data;
        this.type = 'filerecord';
        this.group = group;
        this.collapsed = true;

        if (group == true) {
            this.element = createElements(
                el('div', {'class': 'filerecord'},
                    el('div', {'class': 'row flex-row'},
                        el('div', {'class': 'wp40 flex-row'},
                            el('div', {'class': 'filerecord-caret icon caret-right'}, ''),
                            el('div', {'style': 'padding: 0.5em'}, this.data.name)
                        ),
                        el('div', {'class': 'wp10'}, this.data.type__name),
                        el('div', {'class': 'wp10'}, this.data.status__name),
                        el('div', {'class': 'wp5'}, this.data.version),
                        el('div', {'class': 'wp10'}, ''),
                        el('div', {'class': 'wp10'}, this.data.extension),
                        el('div', {'class': 'wp5 icon copy', 'title': 'copy'}, ''),
                        el('div', {'class': 'wp5 icon play', 'title': 'play'}, ''),
                    ),
                    el('div', {'class': 'model-group files'}, ''),
                )
            );
        } else {
            this.element = createElements(
                el('div', {'class': 'filerecord hidden'},
                    el('div', {'class': 'row flex-row'},
                        el('div', {'class': 'wp40 flex-row'},
                            el('div', {'class': 'filerecord-name'}, this.data.name)
                        ),
                        el('div', {'class': 'wp10'}, this.data.type__name),
                        el('div', {'class': 'wp10'}, this.data.status__name),
                        el('div', {'class': 'wp5'}, this.data.version),
                        el('div', {'class': 'wp10'}, ''),
                        el('div', {'class': 'wp10'}, this.data.extension),
                        el('div', {'class': 'wp5 icon copy', 'title': 'copy'}, ''),
                        el('div', {'class': 'wp5 icon play', 'title': 'play'}, ''),
                    ),
                    el('div', {'class': 'model-group files'}, ''),
                )
            );
        }

        // connect play
        this.element.querySelector('.icon.play').onclick = () => {
            new Video(this.data.project__name, this.data.name, this.data.version.toString().padStart(3, '0'))
        };

        // connect copy
        this.element.querySelector('.icon.copy').onclick = () => {
            let path = createElements(el('textarea', {}, this.data.path));
            document.body.appendChild(path);
            path.select();
            document.execCommand('copy');
            document.body.removeChild(path);
        };

        // connect the collapse button
        if (this.element.querySelector(`.${this.type}-caret`) != null) {
            this.element.querySelector(`.${this.type}-caret`).onclick = () => {
                this.element.querySelector(`.${this.type}-caret`).className = (this.collapsed) ? `${this.type}-caret icon caret-down` : `${this.type}-caret icon caret-right`;

                FILERECORDS.map(x => {
                    if (!x.group) {
                        if (x.data.name == this.data.name) {
                            x.element.style.display = (this.collapsed) ? 'block' : 'none';
                        }
                    }
                });
                this.collapsed = !this.collapsed;
            };
        }

        document.getElementById('filerecords').append(this.element);
    }
}

class Project {
    constructor(data) {
        this.data = data;
        this.type = 'project';

        this.element = createElements(
            el('div', {'class': 'project'},
                el('div', {"class": "row flex-row"},
                    el('div', {'class': 'wp30'},
                        el('div', {'class': 'project-name clickable inline'}, this.data.name),
                    ),
                    el('div', {'class': 'flex-grow'}, ''),
                ),
                el('div', {'class': 'model-group shots'}, ''),
            )
        );

        // connect slider
        this.element.querySelector('.clickable').onclick = () => {
            SLIDER.set_parent(this);
            SLIDER.element.querySelector('.parent_name').innerText = this.data.name || this.data.type__name;
            SLIDER.show();
        };

        this.data.shots.forEach(data => {
            let shot = new Shot(data, this);
            this.element.querySelector('.shots').append(shot.element);
        })
    }
}

class Shot {
    constructor(data, parent) {
        this.data = data;
        this.parent = parent;
        this.type = 'shot';

        this.element = createElements(
            el('div', {'class': 'shot'},
                el('div', {'class': 'row flex-row'},
                    el('div', {'class': 'wp25 flex-row'},
                        el('div', {'class': 'shot-caret icon caret-down'}, ''),
                        el('div', {'class': 'shot-name clickable'}, this.data.name)
                    ),
                    el('div', {'class': 'wp15 align-center'}, 'Shot'),
                    el('div', {
                        'class': 'shot-status__name wp15',
                        'style': `background-color:${this.data.status__bg_color}; color:${this.data.status__fg_color}`
                    }, this.data.status__name),
                    el('div', {'class': 'flex-grow'}, ''),
                ),
                el('div', {'class': 'model-group tasks'}, '')
            )
        );

        // load filerecords
        this.data.filerecords.forEach(data => {
            let existing_records = FILERECORDS.filter(x => {
                return x.data.name == data.name
            });

            let filerecord = new Filerecord(data, existing_records.length == 0);
            FILERECORDS.push(filerecord);
        });

        // connect slider
        this.element.querySelector('.clickable').onclick = () => {
            SLIDER.set_parent(this);
            SLIDER.element.querySelector('.parent_name').innerText = this.data.name || this.data.type__name;
            SLIDER.show();
        };

        this.data.tasks.forEach(data => {
            let task = new Task(data, this);
            this.element.querySelector('.tasks').append(task.element);
        })
    }
}

class Task {
    constructor(data, parent) {
        this.data = data;
        this.parent = parent;
        this.type = 'task';

        this.element = createElements(
            el('div', {'class': 'task'},
                el('div', {'class': 'row flex-row'},
                    el('div', {'class': 'wp25 flex-row'},
                        // el('input', {'type': 'checkbox', 'class': 'task-selected', 'style': 'visibility:hidden'}, ''),
                        el('div', {'class': 'task-name clickable'}, this.data.name)
                    ),
                    el('div', {
                        'class': 'align-center wp15',
                        'style': `background-color:${this.data.type__bg_color}; color:${this.data.type__fg_color}`
                    }, this.data.type__name),
                    el('div', {
                        'class': 'task-status__name wp15',
                        'style': `background-color:${this.data.status__bg_color}; color:${this.data.status__fg_color}`
                    }, this.data.status__name),
                    el('div', {'class': 'task-bids align-center wp5'},
                        (this.data.bids > 0) ? this.data.bids.toFixed(1) : '-'),
                    el('div', {
                            'class': 'task-actuals align-center wp5', 'title': seconds_to_hhmm(this.data.actuals)
                        },
                        (this.data.actuals > 0) ? (this.data.actuals / 3600 / 8).toFixed(2) : '-'),

                    el('div', {'class': 'align-center wp10'}, '-'),
                    el('div', {'class': 'task-assignee__userprofile__full_name align-left wp20'},
                        this.data.assignee__userprofile__full_name || '-'),
                    // el('div', {'class': 'icon plus add-subtask'}, ''),
                ),
                el('div', {'class': 'model-group subtasks'}, '')
            )
        );

        // connect slider
        this.element.querySelector('.clickable').onclick = () => {
            SLIDER.set_parent(this);
            SLIDER.element.querySelector('.parent_name').innerText = this.data.name || this.data.type__name;
            SLIDER.show();
        };

        // // create subtask
        // this.element.querySelector('.add-subtask').onclick = () => {
        //     add_subtask(this, 'subtask');
        // };

        this.data.subtasks.forEach(data => {
            let subtasks = new Subtask(data, this);
            this.element.querySelector('.subtasks').append(subtasks.element);
        });
    }
}

class Subtask {
    constructor(data, parent) {
        this.data = data;
        this.parent = parent;
        this.type = 'subtask';

        this.element = createElements(
            el('div', {'class': 'subtask'},
                el('div', {'class': 'row flex-row'},
                    el('div', {'class': 'wp25'},
                        el('div', {'class': 'subtask-name clickable inline'}, this.data.name),
                    ),
                    el('div', {'class': 'align-center wp15'}, 'Subtask'),
                    el('div', {
                        'class': 'subtask-status__name wp15',
                        'style': `background-color:${this.data.status__bg_color}; color:#c52a2e;`
                    }, this.data.status__name),

                    el('div', {'class': 'subtask-bids align-center wp5'},
                        (this.data.bids > 0) ? this.data.bids.toFixed(1) : '-'),
                    el('div', {
                            'class': 'subtask-actuals align-center wp5',
                            'title': seconds_to_hhmm(this.data.actuals)
                        },
                        (this.data.actuals > 0) ? (this.data.actuals / 3600 / 8).toFixed(2) : '-'),

                    el('div', {'class': 'subtask-work_perc align-center wp10'},
                        (this.data.work_perc > 0) ? this.data.work_perc.toFixed(1) : '-'),
                    el('div', {'class': 'subtask-assignee__userprofile__full_name align-left wp20'},
                        this.data.assignee__userprofile__full_name || '-'),
                    // el('div', {'class': 'icon edit'}, ''),
                    el('div', {'class': 'icon info'}),
                ),
            )
        );

        // connect slider
        this.element.querySelector('.clickable').onclick = () => {
            SLIDER.set_parent(this);
            SLIDER.element.querySelector('.parent_name').innerText = this.data.name || this.data.type__name;
            SLIDER.show();
        };

        // show bid breakdown
        this.element.querySelector('.info').onclick = () => {
            show_loading();
            post('get_bidactuals/', {
                subtask_id: this.data.id,
            }).then(resp => {
                show_modal('bidactuals_breakdown');
                let tbody = document.getElementById('tbody_bidactuals_breakdown');
                tbody.innerText = "";

                let tfoot = document.getElementById('tfoot_bidactuals_breakdown');
                tfoot.innerText = "";

                let totals = 0;

                resp.forEach(actual => {
                    let row = createElements(el('tr', {},
                        el('td', {}, local_date(actual.date)),
                        el('td', {}, actual.user__userprofile__full_name),
                        el('td', {}, seconds_to_hhmm(actual.actuals)),
                    ));
                    tbody.append(row);
                    totals += actual.actuals;
                });

                let row = createElements(el('tr', {},
                    el('td', {}, ''),
                    el('td', {}, ''),
                    el('td', {}, seconds_to_hhmm(totals)),
                ));
                tfoot.append(row);

                hide_loading('bidactuals_breakdown');
            });
        }

        // // connect the edit button
        // this.element.querySelector('.icon.edit').onclick = () => {
        //     let form = document.forms[`add_${this.type}`];
        //     for (let key in this.data) {
        //         if (form.hasOwnProperty(key)) {
        //             form[key].value = this.data[key];
        //             if (form[key].tagName === 'SELECT') {
        //                 let event = new Event('change');
        //                 form[key].dispatchEvent(event);
        //             }
        //         }
        //     }
        //     add_subtask(this.parent, this.type, this)
        // };
    }
}

const get_defaults = () => {
    post('get_defaults/', {}).then(resp => {

        new SlimSelect({
            select: document.getElementById('select_subtask_status'),
            data: resp.status.map(x => {
                return {'value': x.id, 'text': x.name}
            })
        });

        new SlimSelect({
            select: document.getElementById('select_subtask_assignee'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.assignee.map(x => {
                return {'value': x.id, 'text': x.userprofile__full_name}
            })),
            placeholder: 'Select Assignee',
        });
    });
};

const get_data = () => {
    return post('get_data/', {}).then(resp => {
        PROJECT = new Project(resp);
        document.getElementById('container').append(PROJECT.element);
    })
};

window.onload = async () => {
    await init('Task Overview');

    // add slider
    SLIDER = new Slider();
    document.getElementById('modals').append(SLIDER.element);

    get_defaults();
    await get_data();

    hide_loading()
};