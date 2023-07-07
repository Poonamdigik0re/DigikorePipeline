class Client {
    constructor(data) {
        this.data = data;
        this.element = createElements(el('div', {
            'class': 'client-name border-bottom',
            'style': 'padding: 0.5em'
        }, this.data.name));

        this.element.onclick = () => {
            get_all_projects(this.data.id);
            get_all_contacts(this.data.id);

            // update client info
            document.getElementById('client__name').innerText = this.data.name;
            document.getElementById('client__address').innerText = this.data.address || '-';

            // edit client info
            document.getElementById('edit_client_info').onclick = () => {
                let form = document.forms['add_new_client'];
                for (let key in this.data) {
                    if (form.hasOwnProperty(key)) {
                        form[key].value = this.data[key];
                    }
                }
                show_modal('add_new_client');
            };

            let form = document.forms['add_new_contact'];
            form.onsubmit = (event) => {
                event.preventDefault();
                show_loading();

                let data = formdata(form);
                data['client_id'] = this.data.id;

                post('add_new_contact/', data).then((resp) => {
                    get_all_contacts(this.data.id);
                    hide_modal('add_new_contact');
                    hide_loading();
                })
            }
        }
    }
}

class Contact {
    constructor(data) {
        this.data = data;

        console.log(this.data);
        console.log(this.data.contact);
        this.element = createElements(
            el('tr', {},
                el('td', {}, this.data.name),
                el('td', {}, this.data.title || '-'),
                el('td', {}, this.data.email),
                el('td', {}, this.data.contact || '-'),
                el('td', {'style': 'width: 4em'},
                    el('div', {'class': 'icon edit'})
                )
            )
        );

        // edit client info
        this.element.querySelector('.edit').onclick = () => {
            let form = document.forms['add_new_contact'];
            for (let key in this.data) {
                if (form.hasOwnProperty(key)) {
                    form[key].value = this.data[key];
                }
            }
            show_modal('add_new_contact');
        };
    }
}

const get_all_clients = () => {
    return post('get_all_clients/', {}).then(resp => {
        let clients_list = document.getElementById('clients_list');
        clients_list.innerText = "";

        resp.forEach(data => {
            let client = new Client(data);
            clients_list.append(client.element);
        })
    });
};

const get_all_projects = (client_id) => {
    post('get_all_projects/', {'client_id': client_id}).then(resp => {

        let table = document.getElementById('tbody_client_projects');
        table.innerText = '';

        resp.forEach(project => {
            let row = createElements(
                el('tr', {},
                    el('td', {}, project.name),
                    el('td', {}, project.type__name),
                    el('td', {}, project.status__name),
                )
            );
            table.append(row);
        })
    })
};

const get_all_contacts = (client_id) => {
    post('get_all_contacts/', {'client_id': client_id}).then(resp => {
        let table = document.getElementById('tbody_client_contacts');
        table.innerText = '';

        resp.forEach(data => {
            let row = new Contact(data);
            table.append(row.element);
        })
    })
};

const add_new_client = (form) => {
    show_loading();
    post('add_new_client/', formdata(form)).then(resp => {
        get_all_clients();
        hide_modal('add_new_client');
        hide_loading();
    })
};

window.onload = async () => {
    await init('Client List');
    await get_all_clients();
    hide_loading()
};