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
                el('td', {}, file_size(this.data.size))
            )
        );

        if (this.data.is_dir) {
            this.element.onclick = () => {
                this.parent.current_path = this.data.path;
                console.log("data:",data)
                this.parent.browse(this.data.path);
            }
        }
    }
}

class Browser {
    constructor(site, callback) {
        this.site = site;
        console.log("project id:",this.site)
        this.current_path = '';
        this.all_files = [];

        this.element = createElements(
            el('form', {'class': 'modal flex-column flex-screen-center', 'method': 'post', 'action': ''},
                el('div', {'class': 'dialog w60 h60 flex-column'},
                    el('div', {'class': 'heading flex-row flex-no-shrink'},
                        el('div', {'class': 'flex-grow'}, 'File Browser'),
                        el('div', {'class': 'close'}, '')
                    ),
                    el('div', {'class': 'content flex-column flex-grow'},
                        el('div', {'class': 'flex-no-shrink flex-row border-bottom'},
                            el('div', {'style': 'margin: 0.5em 0.5em 0.5em 0', 'class': 'go-back'},
                                el('div', {'class': 'icon left'}, '')
                            ),
                            el('input', {
                                'class': 'block current-path',
                                'type': 'text',
                                'readonly': 'readonly',
                                'style': 'border: none'
                            }, ''),
                            el('div', {'class': 'icon copy copy-path'}, '')
                        ),
                        el('div', {'class': 'flex-no-shrink'},
                            el('table', {'class': 'table'},
                                el('colgroup', {},
                                    el('col', {'width': '60%'}, ''),
                                    el('col', {'width': '40%'}, '')
                                ),
                                el('thead', {},
                                    el('tr', {},
                                        el('th', {}, 'Name'),
                                        el('th', {}, 'Size'),
                                    )
                                )
                            )
                        ),
                        el('div', {'class': 'flex-grow flex-column'},
                            el('table', {'class': 'table hover'},
                                el('colgroup', {},
                                    el('col', {'width': '60%'}, ''),
                                    el('col', {'width': '40%'}, '')
                                ),
                                el('tbody', {'class': 'all-files'}, '')
                            )
                        )
                    ),
                    el('div', {'class': 'footer flex-row flex-no-shrink'},
                        el('div', {'class': 'flex-grow'}, ''),
                        el('div', {},
                            el('button', {'type': 'button', 'class': 'button-select'}, 'Select'))
                    )
                )
            )
        );

        this.element.querySelector('.close').onclick = () => {
            this.element.remove();
        };

        this.element.querySelector('.go-back').onclick = () => {
            this.goback();
        };

        this.element.querySelector('.copy-path').onclick = () => {
            this.copy_path();
        };

        this.element.querySelector('.button-select').onclick = () => {
            callback(this.current_path);
            this.element.remove();
        };

        // append to document
        document.getElementById('modals').append(this.element);
        this.element.style.display = 'flex';
        this.browse();
    }

    copy_path() {
        let path = createElements(el('textarea', {}, this.current_path));
        document.body.appendChild(path);
        path.select();
        document.execCommand('copy');
        document.body.removeChild(path);
    }

    goback() {
        if (this.current_path) {
            let current_path = this.current_path.split("/");
            current_path.pop();
            this.current_path = current_path.join("/");
            this.browse(this.current_path);
        }
    }

    browse(path = this.site) {
    console.log('path1:',path)
    this.current_path = path;
        let current_path = this.element.querySelector('.current-path');
        let all_files = this.element.querySelector('.all-files');


        // remove all existing files
        this.all_files.forEach(f => {
            f.element.remove()
        });
        this.all_files = [];


if (path !== this.site) {
            const searchParams = new URLSearchParams();
            console.log('path2:',path)
            searchParams.set('current_path', path);
            window.history.pushState(null, '', `?${searchParams.toString()}`);
            this.current_path = path;
            console.log(this.current_path)
        }

        // Make the API request

        const url = `http://localhost:5000/?current_path=${encodeURIComponent(this.current_path)}`
        console.log("url:",url)
        fetch(`http://localhost:5000/?current_path=${encodeURIComponent(this.current_path)}`)
            .then(resp => resp.json())
            .then(data => {

                data.files.forEach(x => {
                    let row = new File(x, this);
                    all_files.append(row.element);
                    // Add to the list
                    this.all_files.push(row);
                });

                current_path.value = data.path;
                this.current_path = data.path;
            })
            .catch(error => {
    console.error(error);
    alert("No project added. Directory not found.");
  });

    }
}