let ALL_FILES = [];
let DEFAULTS = {};

class Filerecord {
    constructor(data) {
        this.data = data;
        console.log(data)
        this.element = createElements(
            el('tr', {},
                el('td', {},
                    el('input', {'class': 'block file_name', 'value': this.data.name}, '')
                ),
                el('td', {},
                    el('select', {'class': 'file_parent_type'},
                        el('option', {'value': ''}, '-'),
                        el('option', {'value': 'project'}, 'Project'),
                        el('option', {'value': 'sequence'}, 'Sequence'),
                        el('option', {'value': 'shot'}, 'Shot'),
                        // el('option', {'value': 'task'}, 'Task'),
                        el('option', {'value': 'assetgroup'}, 'Assetgroup'),
                        // el('option', {'value': 'asset'}, 'Asset'),
                    )
                ),
                el('td', {},
                    el('select', {'class': 'file_parent_id'},)
                ),
                el('td', {},
                    el('select', {'class': 'file_type_id'},)
                ),
                el('td', {'class': 'version'}, '-'),
                el('td', {}, this.data.first_frame || '-'),
                el('td', {}, this.data.last_frame || '-'),
                el('td', {}, this.data.padding),
                el('td', {}, this.data.extension),
                el('td', {},
                    el('div', {'class': 'icon trash'}, '')
                ),
            )
        );

        // connect file name
        this.element.querySelector('.file_name').onchange = (event) => {
            this.data.name = event.target.value;
            this.get_version();
        };

        // Select Parent ID
        let select_parent_id = new SlimSelect({
            select: this.element.querySelector('.file_parent_id'),
            onChange: (select) => {
                this.data.parent_id = select.value;
                this.get_version();
            }
        });

        // Select Parent Type
        new SlimSelect({
            select: this.element.querySelector('.file_parent_type'),
            onChange: (select) => {
                this.data.parent_type = select.value;
                this.get_version();

                let project_id = document.getElementById('select_project').value;

                post('get_parents/', {'project_id': project_id, 'model_type': select.value}).then(resp => {
                    select_parent_id.setData([{
                        'placeholder': true,
                        'text': '',
                        'value': ''
                    }].concat(resp.map(r => {
                        return {'text': r.name, 'value': r.id}
                    })))
                })
            }
        });

        // Select Filerecord Type
        new SlimSelect({
            select: this.element.querySelector('.file_type_id'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(DEFAULTS['file_type'].map(r => {
                return {'text': r.name, 'value': r.id}
            })),
            placeholder: 'Select Type',
            onChange: (select) => {
                this.data.type_id = select.value;
                this.get_version();
            },
        });

        this.element.querySelector('.trash').onclick = () => {
            document.getElementById('tbody_files').removeChild(this.element);
            ALL_FILES.splice(ALL_FILES.indexOf(this), 1);
        }
    }

    get_version() {
        if (this.data.parent_type != undefined && this.data.parent_id != undefined && this.data.type_id != undefined) {
            post('get_version/', {
                'parent_type': this.data.parent_type,
                'parent_id': this.data.parent_id,
                'type_id': this.data.type_id,
                'name': this.data.name
            }).then(resp => {
                this.data.version = resp;
                this.element.querySelector('.version').innerText = resp;
            })
        }
    }
}

const get_defaults = () => {
    post('get_defaults/', {}).then(resp => {
        DEFAULTS = resp;
    })
};

const get_projects = () => {
    post('get_projects/', {}).then(resp => {
        new SlimSelect({
            select: document.getElementById('select_project'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.map(r => {
                return {'text': r.name, 'value': r.id}
            })),
            placeholder: 'Select Project',
        })
    })
};

const get_data = (path) => {
    ALL_FILES = [];
    let tbody_files = document.getElementById('tbody_files');
    tbody_files.innerText = '';
    console.log("**###*")

    show_loading();
    post('get_data/', {'path': path}).then(resp => {
    console.log(resp)
        resp.forEach(data => {
            let row = new Filerecord(data);
            tbody_files.append(row.element);
            ALL_FILES.push(row);
        });
        hide_loading();
    });
};

const start_ingest = () => {
    ALL_FILES.forEach(file => {
        {
            show_loading();
            post('start_ingest/', {
                'project_id': document.getElementById('select_project').value,
                'data': ALL_FILES.map(x => {
                    return x.data
                })
            }).then(resp => {
                location.reload();
            })
        }
    })
};

window.onload = async () => {
    await init('Ingest System');

    get_defaults();
    get_projects();

    // connect the browse storage button
    document.getElementById('browse_storage').onclick = () => {
        let select_project = document.getElementById('select_project');
        let selectedOption = select_project.options[select_project.selectedIndex];
        console.log("******:",selectedOption.text)
        if (select_project.value) {

            new Browser(selectedOption.text, get_data);
        } else {
            alert('Please select the project')
        }
    };

    hide_loading()
};