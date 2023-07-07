let FROM_DRIVE;
let TO_DRIVE;

class File {
    constructor(data, parent) {
        this.data = data;
        this.parent = parent;
        this.element = createElements(
            el('tr', {},
                el('td', {},
                    el('div', {
                        'class': `icon ${(this.data.is_dir) ? 'folder' : 'file'}`,
                        'style': 'margin: 0 1em 0 0'
                    }, ''),
                    el('span', {}, this.data.name)
                ),
                el('td', {'class': 'align-right'},
                    (this.data.is_dir) ? '' : file_size(this.data.size)
                )
            )
        );

        this.element.onclick = () => {
            this.parent.files.forEach(file => {
                file.element.classList.remove('highlighted');
            });
            this.element.classList.add('highlighted');
        };

        if (this.data.is_dir) {
            this.element.ondblclick = () => {
                this.parent.root = this.data.path;
                this.parent.browse();
            }
        }
    }
}

class StorageDrive {
    constructor(root) {
        this.root = root;
        this.files = [];
        this.element = createElements(el('div', {
                'class': 'flex-grow flex-column',
            },
            el('div', {'class': 'flex-no-shrink flex-row bg-clouds'},
                el('div', {'class': 'flex-no-shrink icon left', 'style': 'margin: 0.5em 0 0.5em 0.5em;'}, ''),
                el('div', {'class': 'flex-grow p10 bold current_path'}, ''),
                el('div', {'class': 'flex-no-shrink icon plus', 'style': 'margin: 0.5em 0.5em 0.5em 0;'}, '')
            ),
            el('div', {'class': 'flex-grow'},
                el('table', {'class': 'table hover small-line-height'},
                    el('tbody', {'class': 'files'}), ''
                )
            ),
        ));

        // attach the back button
        this.element.querySelector('.icon.left').onclick = () => {
            this.back()
        };

        // create folder
        this.element.querySelector('.icon.plus').onclick = () => {
            let folder_name = prompt("New folder name");
            if (folder_name != null) {
                post('add_folder/', {path: `${this.root}/${folder_name}`}).then(resp => {
                    this.browse();
                })
            }
        };

        this.browse();
    }

    back() {
        let path = this.root.split('\/');

        if (path.length > 3) {
            path.pop();
            this.root = path.join('/');
            this.browse();
        }
    }

    browse() {
        show_loading();
        let body = this.element.querySelector('.files');

        // clean the existing data
        this.files.forEach(x => {
            x.element.remove()
        });
        this.files = [];

        post(`browse/`, {'path': this.root}).then(resp => {
            this.element.querySelector('.current_path').innerText = resp.path;

            resp.files.forEach(x => {
                let f = new File(x, this);
                body.append(f.element);

                this.files.push(f);
            });
        }).finally(() => {
            hide_loading();
        })
    }
}

const load_from_drive = () => {
    if (FROM_DRIVE != undefined) {
        FROM_DRIVE.element.remove();
    }

    FROM_DRIVE = new StorageDrive(document.getElementById('select_from').value);
    document.getElementById('from_drive').append(FROM_DRIVE.element);
};


const load_to_drive = () => {
    if (TO_DRIVE != undefined) {
        TO_DRIVE.element.remove();
    }

    TO_DRIVE = new StorageDrive(document.getElementById('select_to').value);
    document.getElementById('to_drive').append(TO_DRIVE.element);
};

const get_active_transfers = () => {
    return post('get_active_transfers/', {}).then(resp => {
        let active_transfers = document.getElementById('active_transfers');
        active_transfers.innerText = "";

        resp.forEach(data => {
            let duration = (new Date(data.modified_on) - new Date(data.created_on)) / 1000;

            let row = createElements(el('tr', {},
                el('td', {'title': data.id}, local_datetime(data.created_on)),
                el('td', {}, data.created_by__userprofile__full_name),
                el('td', {'class': 'text-overflow', 'title': data.from_path}, data.from_path),
                el('td', {'class': 'text-overflow', 'title': data.to_path}, data.to_path),
                el('td', {}, data.status),
                el('td', {}, data.files),
                el('td', {}, file_size(data.size)),
                el('td', {}, seconds_to_hhmm(parseInt(duration / data.percent) * (100 - data.percent))),
                el('td', {
                    'style': `background: linear-gradient(to right, #03a9f4 ${data.percent}%, #aaa ${data.percent}%); color: white; font-weight: bold; text-align: center; text-shadow: 0 0 4px black`,
                    'title': seconds_to_hhmm(duration),
                }, data.percent + '%'),
                el('td', {},
                    el('div', {'class': 'icon cancel', 'title': 'Cancel'}, ''),
                    el('div', {'class': 'icon refresh', 'title': 'Restart'}, ''),
                )
            ));

            // Cancel transfer
            if (data.status != 'running') {
                row.querySelector('.icon.cancel').remove();
            } else {
                row.querySelector('.icon.cancel').onclick = () => {
                    if (confirm(`Are you sure you want to cancel this?`)) {
                        show_loading();
                        post('cancel_transfer/', {'transfer_id': data.id}).then(resp => {
                            get_active_transfers();
                        }).finally(() => {
                            hide_loading();
                        });
                    }
                }
            }

            // Restart transfer
            if (data.status != 'failed') {
                row.querySelector('.icon.refresh').remove();
            } else {
                row.querySelector('.icon.refresh').onclick = () => {
                    if (confirm(`Are you sure you want to restart this?`)) {
                        show_loading();
                        post('restart_transfer/', {'transfer_id': data.id}).then(resp => {
                            get_active_transfers();
                        }).finally(() => {
                            hide_loading();
                        });
                    }
                }
            }

            active_transfers.append(row);
        })
    })
};

const start_transfer = () => {
    let from_files = FROM_DRIVE.files.filter(file => {
        return file.element.classList.contains('highlighted')
    });

    let to_files = TO_DRIVE.files.filter(file => {
        return file.element.classList.contains('highlighted')
    });

    if (from_files.length == 0 || from_files.length > 1 || to_files.length == 0 || to_files.length > 1) {
        alert('Please select only one file or folder');
        return false
    }

    let data = {'from_path': from_files[0].data.path, 'to_path': to_files[0].data.path};

    if (confirm(`Please confirm that you want transfer files\n\nFrom Path:\n${data['from_path']}\n\nTo Path:\n${data['to_path']}`)) {
        show_loading();
        post('start_transfer/', data).then(resp => {
            alert(`Total Files: ${resp.files}\nTotal Size: ${file_size(resp.size)}`);
        }).finally(() => {
            hide_loading();
            hide_modal('file_transfer');
            get_active_transfers();
        });
    }
};

window.onload = async () => {
    show_loading();
    await init();
    await get_active_transfers();

    // reload the data every 5 minutes
    setInterval(get_active_transfers, 300000);
    load_from_drive();
    load_to_drive();

    // set title
    document.title = 'File Transfer';
    hide_loading()
};