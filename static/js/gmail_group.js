class GmailGroup {
    constructor(data) {
        this.data = data;
        this.element = createElements(el('tr', {},
            el('td', {}, this.data.name),
            el('td', {}, this.data.email),
            el('td', {},
                ...this.data.members.map(member => {
                    return el('div', {
                        'class': 'username',
                        'title': member.members__email
                    }, member.members__userprofile__full_name)
                })
            ),
            el('td', {},
                el('div', {'class': 'icon edit'}, '')
            )
        ));

        this.element.querySelector('.icon.edit').onclick = () => {
            show_modal('create_group');
            let form = document.forms['create_group'];
            form.group_id.value = this.data.id;
            form.name.value = this.data.name;
            form.email.value = this.data.email;

            let members = this.data.members.map(x => {
                return parseInt(x['members__id']);
            });
            if (members.length != 0) {
                for (let c of form.members.children) {
                    if (members.indexOf(parseInt(c.value)) != -1) c.selected = true;
                }
                let event = new Event('change');
                form.members.dispatchEvent(event);
            }
        }
    }
}

const get_all_groups = () => {
    let all_groups = document.getElementById('all_groups');
    all_groups.innerText = "";

    post('get_all_groups/', {}).then(resp => {
        resp.forEach(data => {
            let group = new GmailGroup(data);
            all_groups.append(group.element);
        })
    })
};

const get_all_users = () => {
    let select_members = document.getElementById('select-group_members');
    post('get_all_users/', {}).then(resp => {
        // Select Client
        new SlimSelect({
            select: document.getElementById('select-members'),
            data: [{
                'placeholder': true,
                'text': '',
                'value': ''
            }].concat(resp.map(x => {
                return {'value': x.id, 'text': `${x['userprofile__full_name']} : ${x['email']}`}
            })),
            placeholder: "Select Members",
        });
    })
};

const create_group = (form) => {
    show_loading();
    let data = formdata(form);
    post('create_group/', data).then(resp => {
        hide_modal('create_group');
        get_all_groups();
    })
};

window.onload = async () => {
    // set title
    document.title = 'Gmail Group';
    show_loading();
    await init();
    // start

    get_all_groups();
    get_all_users();

    // end
    hide_loading()
};