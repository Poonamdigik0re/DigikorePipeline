let ALL_TICKETS = [];

class Tickets {
    constructor(data) {
        this.data = data;
        this.element = createElements(
            el('tr', {'class': 'link'},
                el('td', {}, this.data.id),
                el('td', {}, this.data.title),
                el('td', {}, this.data.priority__name),
                el('td', {}, this.data.status__name),
                el('td', {}, this.data.type__name),
                el('td', {}, local_date(this.data.created_on)),
                el('td', {}, this.data.created_by__userprofile__full_name),
                el('td', {}, (this.data.assigned_to__userprofile__full_name != null) ? this.data.assigned_to__userprofile__full_name : " ")
            )
        );

        this.element.onclick = () => {
            location.href = `${this.data.id}/`
        }
    }
};

class AddTicketAttachment extends BaseClass {
    constructor(data) {
        super('ticket', data)
    }

    add_attachments() {

        let attachment_files = document.querySelector('#ticket_files').files;

        if (attachment_files.length > 0) {
            let form_data = new FormData();
            form_data.append('parent_type', this.model_type);
            form_data.append('parent_id', this.data);

            for (let x = 0; x < attachment_files.length; x++) {
                form_data.append(`file${x}`, attachment_files[x]);
            }

            post('/base/add_attachments/', form_data, true).then(resp => {
                //Added Ticket Attachments
                document.querySelector('#ticket_files').files = null;
            })
        }
    }
};


//Get All Default Values for Tickets
const get_defaults = () => {
    post('/tickets/get_defaults/', {}).then((resp) => {
        // All tickets filter
        let priority_filter = document.getElementById('filter__priority');
        let status_filter = document.getElementById('filter__status');
        let type_filter = document.getElementById('filter__type');

        // All tickets filter priority
        resp.priority.forEach((priority) => {
            let filter = createElements(
                el('label', {'class': 'block'},
                    el('input', {
                        'type': 'checkbox',
                        'class': 'filter',
                        'checked': true,
                        'onchange': `apply_filters(); deselect_All(filter__priority)`,
                        'data-filter_key': 'priority_id',
                        'data-filter_value': priority.id
                    }),
                    el('span', {}, priority.name)
                )
            );
            priority_filter.appendChild(filter);
        });

        // All ticket filter type
        resp.type.forEach((type) => {
            let filter = createElements(
                el('label', {'class': 'block'},
                    el('input', {
                        'type': 'checkbox',
                        'class': 'filter',
                        'checked': true,
                        'onchange': `apply_filters(); deselect_All(filter__type)`,
                        'data-filter_key': 'type_id',
                        'data-filter_value': type.id
                    }),
                    el('span', {}, type.name)
                )
            );
            type_filter.appendChild(filter);
        });

        // All ticket filter status
        resp.status.forEach((status) => {
            let filter = createElements(
                el('label', {'class': 'block'},
                    el('input', {
                        'type': 'checkbox',
                        'class': 'filter',
                        'checked': true,
                        'onchange': `apply_filters(); deselect_All(filter__status)`,
                        'data-filter_key': 'status_id',
                        'data-filter_value': status.id
                    }),
                    el('span', {}, status.name)
                )
            );
            status_filter.appendChild(filter);
        });

        // New ticket select priority
        new SlimSelect({
            select: document.getElementById('priority_id'),
            data: resp.priority.map(x => {
                return {'value': x.id, 'text': x.name, 'selected': x.default || false}
            })
        });

        // New ticket select type
        new SlimSelect({
            select: document.getElementById('type_id'),
            data: resp.type.map(x => {
                return {'value': x.id, 'text': x.name, 'selected': x.default || false}
            })
        });
    });
};

const get_all_tickets = (ticket_id = null) => {
    return post('get_all_tickets/', {ticket_id: ticket_id}).then(resp => {
        let tickets = document.getElementById('tickets');

        // tickets.innerText = "";
        // ALL_TICKETS.forEach(ticket => {
        //     ticket.element.remove();
        // });
        // ALL_TICKETS = [];

        resp.forEach((data) => {
            let tkt = new Tickets(data);
            tickets.append(tkt.element);
            ALL_TICKETS.push(tkt);
        });

        document.getElementById('total_tickets').innerText = ALL_TICKETS.length;
        apply_filters();
    });
};

const update_total_count = () => {
    document.getElementById('total_tickets').innerText = ALL_TICKETS.filter(tkt => {
        return tkt.element.style.display !== 'none'
    }).length;
};

const apply_filters = (key = null, input = null) => {
    base_filter(key, input, ALL_TICKETS, update_total_count);
};


const add_ticket = (form) => {
    let data = formdata(form);
    post('add_ticket/', data).then(resp => {
        new AddTicketAttachment(resp.id).add_attachments();
        hide_modal('add_ticket');
    })
};

document.addEventListener('wss_ticket_created',(data) => {
   get_all_tickets(data.data.id);
});


window.onload = async () => {
    await init('Ticket Manager');
    get_defaults();
    await get_all_tickets();
    hide_loading();

    if (has_permission('tickets_maintainer') || has_permission('tickets_admin')) {
        init_websocket();
    }
};