class Vendor {
    constructor(data) {
        this.data = data;
        this.element = createElements(el('div', {
            'class': 'vendor-name border-bottom',
            'style': 'padding: 0.5em'
        }, this.data.name));

        this.element.onclick = () => {
            get_all_projects(this.data.id);
            get_all_contacts(this.data.id);

            // update vendor info
            document.getElementById('vendor__name').innerText = this.data.name;
            document.getElementById('vendor__address').innerText = this.data.address || '-';


            let form = document.forms['add_new_contact'];
            form.onsubmit = (event) => {
                event.preventDefault();

                let data = formdata(form);
                data['vendor_id'] = this.data.id;

                post('add_new_contact/', data).then((resp) => {
                    get_all_contacts(this.data.id);
                    hide_modal('add_new_contact');
                })
            }
        }
    }
}

const get_all_vendors = () => {
    return post('get_all_vendors/', {}).then(resp => {
        let vendors_list = document.getElementById('vendors_list');
        vendors_list.innerText = "";

        resp.forEach(data => {
            let vendor = new Vendor(data);
            vendors_list.append(vendor.element);
        })
    });
};

const get_all_projects = (vendor_id) => {
    post('get_all_projects/', {'vendor_id': vendor_id}).then(resp => {

        let table = document.getElementById('tbody_vendor_projects');
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

const get_all_contacts = (vendor_id) => {
    post('get_all_contacts/', {'vendor_id': vendor_id}).then(resp => {
        let table = document.getElementById('tbody_vendor_contacts');
        table.innerText = '';

        resp.forEach(contact => {
            let row = createElements(
                el('tr', {},
                    el('td', {}, contact.name),
                    el('td', {}, contact.title || '-'),
                    el('td', {}, contact.email),
                    el('td', {}, contact.contact || '-'),
                )
            );
            table.append(row);
        })
    })
};

const add_new_vendor = (form) => {
    post('add_new_vendor/', formdata(form)).then(resp => {
        get_all_vendors();
        hide_modal('add_new_vendor');
    })
};

window.onload = async () => {
    await init('Vendor List');
    await get_all_vendors();

    hide_loading()
};