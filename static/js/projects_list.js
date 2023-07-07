let ALL_PROJECTS = [];
let SLIMSELECT_CONTACTS;

class Project extends BaseClass {
    constructor(data) {
        super('project', data);

        this.element = createElements(el('tr', {},
            el('td', {'class': 'link'}, this.data.name),
            el('td', {'class': 'link'}, this.data.client__name),
            el('td', {'class': 'link'}, this.data.type__name),
            el('td', {'class': 'link'}, this.data.status__name),
            el('td', {'class': 'link'}, local_date(this.data.start_date)),
            el('td', {'class': 'link'}, local_date(this.data.end_date)),
            el('td', {'style': 'width:4em'},
                el('div', {'class': 'dropdown'},
                    el('div', {'class': 'icon list'}, ''),
                    el('div', {'class': 'menu'},
                        el('a', {'class': 'item edit-project'}, 'Edit Project'),
                        el('a', {
                            'class': 'item project-access',
                            'href': `/projects_permission/${this.data.id}/`
                        }, 'Project Access'),
                        el('a', {
                            'class': 'item project-access',
                            'href': `/projects_overview/${this.data.id}/`
                        }, 'Project Overview'),
                        el('a', {'class': 'item add-attachments'}, 'Documents'),
                    ),
                )
            ),
        ));

        this.element.querySelectorAll('.link').forEach(link => {
            link.onclick = () => {
                location.href = `/projects/${data.id}/`;
            }
        });

        // let thumbnail = (data.thumbnail.startsWith('/static')) ? data.thumbnail : `/media/${data.thumbnail}`;
        // this.element = createElements(
        //     el('div', {'class': 'project-tile'},
        //         el('div', {'class': 'flex-row edit-project'},
        //             el('div', {'class': 'project-name flex-grow'}, this.data.name),
        //             el('div', {'class': 'icon edit'}, ''),
        //         ),
        //         el('a', {'href': `/projects/${data.id}/`},
        //             el('img', {'width': '212px', 'height': '120px', 'src': thumbnail}),
        //         ),
        //     ),
        // );

        if (has_permission('projects_list_add_project')) {
            this.element.querySelector('.edit-project').onclick = () => {
                // get the contacts list
                post('get_client_contacts/', {'client_id': this.data.client_id}).then(resp => {
                    SLIMSELECT_CONTACTS.setData([{'placeholder': true, 'text': 'Select Client Contacts'}].concat(resp));

                    let form = document.forms['add_new_project'];

                    // update the keys
                    for (let key in this.data) {
                        if (form.hasOwnProperty(key)) {
                            if (form[key].tagName === 'SELECT') {
                                if (form[key].multiple == true) {
                                    if (this.data[key].length != 0) {
                                        for (let c of form[key].children) {
                                            if (this.data[key].indexOf(parseInt(c.value)) != -1) c.selected = true;
                                        }
                                        // form[key].value = this.data[key];
                                        let event = new Event('change');
                                        form[key].dispatchEvent(event);
                                    }
                                } else {
                                    form[key].value = this.data[key];
                                    let event = new Event('change');
                                    form[key].dispatchEvent(event);
                                }
                            } else if (form[key].tagName == 'INPUT' && form[key].type == 'file') {
                                // pass
                            } else {
                                form[key].value = this.data[key];
                            }
                        }
                    }

                    show_modal('add_new_project');
                });
            }
        } else {
            this.element.querySelector('.edit-project').remove();

        }

        if (!has_permission('projects_permission')) {
            this.element.querySelector('.project-access').remove();
        }

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

const get_project_defaults = () => {
    return post('get_project_defaults/', {}).then(resp => {
        // Select Project Vendors
        SLIMSELECT_CONTACTS = new SlimSelect({
            select: document.getElementById('select-contacts'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }],
            placeholder: 'Select client',
        });

        // Select Client
        new SlimSelect({
            select: document.getElementById('select-client_id'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.clients.map(x => {
                return {'value': x.id, 'text': x.name}
            })),
            placeholder: "Select Client",
            onChange: function (select) {
                post('get_client_contacts/', {'client_id': select.value}).then(resp => {
                    SLIMSELECT_CONTACTS.setData([{'placeholder': true, 'text': 'Select Client Contacts'}].concat(resp))
                })
            }
        });

        // Select Project Type
        new SlimSelect({
            select: document.getElementById('select-project_type'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.project_types.map(x => {
                return {'value': x.id, 'text': x.name}
            })),
            placeholder: 'Select Project Type',
        });

        // Select Project Status
        new SlimSelect({
            select: document.getElementById('select-project_status'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.project_statuses.map(x => {
                return {'value': x.id, 'text': x.name}
            })),
            placeholder: 'Select Project Status',
        });

        // Select Digikore Producers
        new SlimSelect({
            select: document.getElementById('select-producers'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.producers.map(x =>
            {
//            console.log('response from map: ', resp);
                return {'value': x.id, 'text': x.userprofile__full_name}
            })),
            placeholder: 'Select Producers',
        });

        // Select Digikore Department
        new SlimSelect({
            select: document.getElementById('select-department'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.department.map(x => {
//            console.log('response from map: ', resp);

                return {'value': x.id, 'text': x.name}
            })),
            placeholder: 'Select Department',
        });


        // Select Digikore Show managers
        new SlimSelect({
            select: document.getElementById('select-production'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.production.map(x => {
                return {'value': x.id, 'text': x.userprofile__full_name}
            })),
            placeholder: 'Select Production',
        });

        // Select Digikore Show Co-Ordinator
//        new SlimSelect({
//            select: document.getElementById('select-showCoOrdinator'),
//            data: [{
//                'placeholder': true,
//                'text': '',
//                'value': ''
//            }].concat(resp.producers.map(x => {
//                return {'value': x.id, 'text': x.userprofile__full_name}
//            })),
//            placeholder: 'Select Show Co-Ordinator',
//        });




        // Select Digikore Supervisors
        new SlimSelect({
            select: document.getElementById('select-supervisors'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.supervisors.map(x => {
                return {'value': x.id, 'text': x.userprofile__full_name}
            })),
            placeholder: 'Select Supervisors',
        });

        // Select Project Vendors
        new SlimSelect({
            select: document.getElementById('select-vendors'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.vendors.map(x => {
                return {'value': x.id, 'text': x.name}
            })),
            placeholder: 'Select Vendors',
        });

        // Select Default Tasks
        new SlimSelect({
            select: document.getElementById('select-default_tasks'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.default_tasks.map(x => {
                return {'value': x.id, 'text': x.name}
            })),
            placeholder: 'Select Default Tasks',
        });

        /*
        FILTERS
         */

        // Type Filter
        new SlimSelect({
            select: document.getElementById('filter_project_type'),
            data: [{'value': '', 'text': '', 'placeholder': true}].concat(resp.project_types.map(x => {
                return {'value': x.id, 'text': x.name}
            })),
            placeholder: 'Filter Project Type',
            allowDeselect: true,
            onChange: function () {
                get_all_projects();
            }
        });
        // Status Filter
        new SlimSelect({
            select: document.getElementById('filter_project_status'),
            data: resp.project_statuses.map(x => {
                return {'value': x.id, 'text': x.name}
            }),
            placeholder: 'Filter Project Status',
            onChange: function () {
                get_all_projects();
            }
        });
    })
};

const get_all_projects = () => {
    return post('get_all_projects/', {
        'type__id': document.getElementById('filter_project_type').value,
        'status__id': document.getElementById('filter_project_status').value,
    }).then(response => {
        let projects_list = document.getElementById('projects_list');
        projects_list.innerText = "";

        response.forEach(data => {
            let project = new Project(data);
            projects_list.appendChild(project.element);

            ALL_PROJECTS.push(project);
        });
    })
};

const add_new_project = (form) => {
    show_loading();
    let form_data = new FormData();

    form_data.append('data', JSON.stringify(formdata(form)));
    form_data.append('thumbnail', form.thumbnail.files[0]);

    post('add_new_project/', form_data, true).then(resp => {
        get_all_projects();
        hide_modal('add_new_project');

        hide_loading();
    })
};

const filter_projects = (input) => {
    let search = input.value.toLowerCase();

    ALL_PROJECTS.forEach(project => {
        project.element.style.display = 'table-row';

        if (project.data.name.toLowerCase().indexOf(search) == -1) project.element.style.display = 'none';
    })
};

window.onload = async () => {
    await init('Projects List');
    await get_project_defaults();
    await get_all_projects();

    hide_loading()
};
