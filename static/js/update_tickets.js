class UpdateTicket extends BaseClass {
    constructor(res) {
        super('ticket', res);
        let optionValues = [];

        let tkt = document.getElementById('update_ticket');
        let tkt_title = document.getElementById("title");
        tkt_title.innerText = "";
        let tkt_desc = document.getElementById("description");
        tkt_desc.innerText = "";
        let tkt_details = document.getElementById("tkt_details");
        tkt_details.innerText = "";
        let tkt_assigned_to = tkt.querySelector("#assigned_to_id");

        tkt_title.appendChild(createElements(res.title));
        tkt_desc.appendChild(createElements(res.description));


        this.element = createElements(el('tbody', {},
            el('tr', {}, el('th', {}, "Created By"), el('td', {}, el('div', {class: 'font-large'}, res.created_by__userprofile__full_name))),
            el('tr', {}, el('th', {}, "Created On"), el('td', {}, el('div', {class: 'font-large'}, local_datetime(res.created_on)))),
            el('tr', {}, el('th', {}, "Resolved By"), el('td', {}, el('div', {class: 'font-large'}, res.resolved_by__userprofile__full_name != null ? res.resolved_by__userprofile__full_name : " - "))),
            el('tr', {}, el('th', {}, "Resolved On"), el('td', {}, el('div', {class: 'font-large'}, res.resolved_on != null ? local_datetime(res.resolved_on) : " - ")))
            )
        );
        tkt_details.appendChild(this.element);

        for (let i = 1; i < tkt_assigned_to.options.length; i++) {
            optionValues.push(parseInt(tkt_assigned_to.options[i].value));
        }

        if (res['assigned_to_id'] != null && !optionValues.includes(res['assigned_to_id'])) {
            tkt_assigned_to.appendChild(createElements(el('option', {
                    'disabled': 'true',
                    'hidden': 'true',
                    'value': res['assigned_to_id']
                }, res.assigned_to__userprofile__full_name))
            );
        }

        tkt_assigned_to.value = res['assigned_to_id'];

        tkt.querySelector('#status_id').value = res['status_id'];
        tkt.querySelector('#type_id').value = res['type_id'];
        tkt.querySelector('#priority_id').value = res['priority_id'];

        tkt.querySelector('#assigned_to_id').dispatchEvent(new Event('change'));
        tkt.querySelector('#status_id').dispatchEvent(new Event('change'));
        tkt.querySelector('#type_id').dispatchEvent(new Event('change'));
        tkt.querySelector('#priority_id').dispatchEvent(new Event('change'));
    }
}

class TicketAttachments extends BaseClass {
    constructor(model_type, data) {
        super(model_type, data)
    }

    //Get Tickets Attachments
    get_attachments() {
        let tkt_attachments = document.getElementById("tkt_attachments");
        tkt_attachments.innerText = "";
        tkt_attachments.appendChild(createElements(el('div', {'class': 'flex-grow'})));
        let modalImg = document.getElementById("img01");
        let modalDoc = document.getElementById("iframe01");

        post('/base/get_attachments/', {
            parent_type: this.model_type,
            parent_id: this.data
        }).then(resp => {
            resp.forEach(data => {
                const types = ["image/png", "image/jpeg", "image/jpg", "image/gif"];
                if (types.includes(data.type)) {
                    this.file = createElements(el('img', {
                        'src': `/media/${data.file}`,
                        'class': 'border ticket-note-img-thumbnail',
                        'alt': `${data.name}`
                    }));
                    this.file.onclick = () => {
                        show_modal("myImgModal");
                        modalImg.src = `/media/${data.file}`;
                    };
                } else {
                    this.file = createElements(el('div', {
                            'class': 'border ticket-note-img-thumbnail ticket-note-file-thumbnail'
                        }, `${data.type}`)
                    );
                    this.file.onclick = () => {
                        show_modal("myDocModal");
                        modalDoc.src = `/media/${data.file}`;
                    };
                }
                tkt_attachments.appendChild(this.file);
            });
        });
    }

    // Add Notes Attachments
    add_note_attachments() {
        let attachment_files = document.querySelector('#note_files').files;

        if (attachment_files.length > 0) {
            let form_data = new FormData();
            form_data.append('parent_type', this.model_type);
            form_data.append('parent_id', this.data);

            for (let x = 0; x < attachment_files.length; x++) {
                form_data.append(`file${x}`, attachment_files[x]);
            }
            post('/base/add_attachments/', form_data, true).then(resp => {
                document.querySelector('#note_files').files = null;
                display_ticket_details();

            })
        }
    }

    //Get Notes Attachments
    get_note_attachments() {
        let add_att = document.getElementById(this.data);
        this.file = "";
        let modalImg = document.getElementById("img01");
        let modalDoc = document.getElementById("iframe01");

        post('/base/get_attachments/', {
            parent_type: this.model_type,
            parent_id: this.data
        }).then(resp => {
            resp.forEach(data => {
                const types = ["image/png", "image/jpeg", "image/jpg", "image/gif"];
                if (types.includes(data.type)) {
                    this.file = createElements(
                        el('img', {
                            'src': `/media/${data.file}`,
                            'class': 'border ticket-note-img-thumbnail',
                            'alt': `${data.name}`
                        })
                    );
                    this.file.onclick = () => {
                        show_modal("myImgModal");
                        modalImg.src = `/media/${data.file}`;
                    };
                    add_att.appendChild(this.file);

                } else {
                    this.file = createElements(el('div', {'class': 'border ticket-note-img-thumbnail ticket-note-file-thumbnail'}, `${data.type}`));
                    this.file.onclick = () => {
                        show_modal("myDocModal");
                        modalDoc.src = `/media/${data.file}`;
                    };
                    add_att.appendChild(this.file);
                }
            });
        });
    }

    // Get Ticket Notes
    get_notes() {
        post('get_notes/', {}).then(resp => {
            let ticket_notes = document.getElementById("ticket_notes");
            ticket_notes.innerText = " ";
            resp.forEach(async resp => {
                let element = createElements(
                    el('div', {'class': 'flex-column ticket_dtls'},
                        el('div', {'class': 'flex-row p10'},
                            el('img', {'src': '/static/img/default_profile.png', 'class': 'ticket-note-profile'}),
                            el('div', {
                                'class': 'flex-grow bold',
                                'style': 'padding: 2em 1em'
                            }, resp.created_by__userprofile__full_name),
                            el('div', {'style': 'padding: 2em 0em; color:white'}, local_datetime(resp.created_on))
                        ),
                        el('div', {'class': 'p5 flex-grow flex-column'},
                            el('div', {'style': 'white-space: pre-line'}, resp.text)
                        ),
                        el('div', {'class': 'p10 flex-row flex-align-right', 'id': resp.id},
                        )
                    )
                );
                ticket_notes.appendChild(element);
                let tktAttachment = new TicketAttachments('ticket', resp.id);
                await tktAttachment.get_note_attachments()
            });
        });
    };
}


const display_ticket_details = () => {
    post('get_ticket_details/', {}).then(resp => {
        resp.forEach(async res => {
            let tkt_att = await new TicketAttachments('ticket', res.id);
            await tkt_att.get_attachments();
            await tkt_att.get_notes();
            await new UpdateTicket(res);
        })
    });
};


//Get All Default values
const get_defaults = () => {
    post('/tickets/get_defaults/', {}).then(async (resp) => {
        //Select Priority of ticket
        new SlimSelect({
            select: document.getElementById('priority_id'),
            data: resp.priority.map(x => {
                return {'value': x.id, 'text': x.name}
            }),
            onChange: (select) => {
                update_ticket({'priority_id': select.value})
            },

        });
        //Select Type of ticket
        new SlimSelect({
            select: document.getElementById('type_id'),
            data: resp.type.map(x => {
                return {'value': x.id, 'text': x.name}
            }),
            onChange: (select) => {
                update_ticket({'type_id': select.value})
            }
        });
        // Select Status
        new SlimSelect({
            select: document.getElementById('status_id'),
            data: resp.status.map(x => {
                return {'value': x.id, 'text': x.name}
            }),
            onChange: (select) => {
                update_ticket({'status_id': select.value})
            }
        });
        // Select Assignee
        new SlimSelect({
            select: document.getElementById('assigned_to_id'),
            data: [{value: '', text: '', placeholder: true}].concat(resp.users.map(x => {
                return {'value': x.id, 'text': x.userprofile__full_name}
            })),
            placeholder: "Select User",
            onChange: (select) => {
                update_ticket({'assigned_to_id': select.value})
            }
        });

        document.getElementById('assigned_to_id').disabled = resp.users.length === 0;
        await display_ticket_details();
    });
};

const update_ticket = (data) => {
    post('update_ticket/', data).then(resp => {
        display_ticket_details();
    })
};

const add_note = (form) => {
    let data = formdata(form);
    post('add_note/', data).then(resp => {
        resp.forEach(async res => {
            let tktAttachment = new TicketAttachments('ticket', res.id);
            await tktAttachment.add_note_attachments();
            document.getElementById("add_note").reset();
            document.getElementById('file_count').hidden = true;
        });
    })
};

const selected_file_count = () => {
    let count = document.getElementById('note_files').files.length;
    document.getElementById('file_count').innerText = `${count} files`;
    document.getElementById('file_count').hidden = false;
};

document.addEventListener('wss_ticket_updated',(data) => {
    display_ticket_details();
});

window.onload = async () => {
    await init('Update Ticket');
    init_websocket();
    get_defaults();
    hide_loading();
};