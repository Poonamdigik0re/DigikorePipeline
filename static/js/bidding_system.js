let ALL_BIDS = [];
let ALL_BID_STATUS = [];
let SLIDER;

class Bid {
    constructor(data) {
        this.data = data;
        this.type = 'bid';
        this.bid_rates = [];

        this.element = createElements(
            el('tr', {},
                el('td', {'class': 'clickable'}, this.data.client__name),
                el('td', {}, this.data.project),
                el('td', {'class': 'text-overflow', 'title': this.data.name}, this.data.name),
                el('td', {}, this.data.project_type__name),
                el('td', {},
                    el('select', {'class': 'bid_status block', 'style': 'border-radius: 0.2em; padding: 0.2em'},
                        ...ALL_BID_STATUS.map(status => {
                            return el('option', {'value': status.id,}, status.name)
                        })
                    )
                ),
                el('td', {'class': 'align-center'}, local_date(this.data.start_date)),
                el('td', {'class': 'align-center'}, local_date(this.data.end_date)),
                el('td', {'width': '50px'},
                    el('div', {'class': 'icon edit edit-bid'})
                ),
                el('td', {'width': '50px'},
                    el('a', {
                            'href': `/bidding_shots/${this.data.id}/`,
                        },
                        el('div', {'class': 'icon open'},)
                    )
                )
            )
        );

        if (has_permission('bidding_system_bid_rate')) {
            let usd = createElements(el('td', {'width': '50px'},
                el('div', {'class': 'icon usd'},)
            ));
            this.element.append(usd);
        }

        // UPDATE BID STATUS
        let select_bid_status = this.element.querySelector('.bid_status');
        select_bid_status.value = this.data.status_id;

        select_bid_status.onchange = () => {
            let reason = null;
            let reason_required = false;
            let selected_option = null;


            select_bid_status.querySelectorAll('option').forEach(option => {
                if (option.selected) selected_option = option.innerText;
            });

            if (["Rejected by digikore", 'Rejected by Client'].indexOf(selected_option) != -1) {
                reason = prompt("Please provide the reason for rejection.");
                reason_required = true
            }

            if (reason_required && reason == null) {
                alert('You did not provide a reason.')
            } else {
                show_loading();
                post('update_bid_status/', {
                    'id': this.data.id,
                    'status_id': select_bid_status.value,
                    'reason': reason
                }).then(resp => {
                    this.data.status_id = resp.id;
                    this.data.status__name = resp.name;

                    hide_loading();
                    hide_modal('update_bid_status');
                })
            }
        };

        // EDIT BID
        this.element.querySelector('.edit-bid').onclick = () => {
            let form = document.forms['edit_bid'];
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
                    } else {
                        form[key].value = this.data[key];
                    }
                }
            }

            show_modal('edit_bid');
        };

        if (has_permission('bidding_system_bid_rate')) {
            // GET BID RATES
            this.element.querySelector('.icon.usd').onclick = () => {
                show_loading();
                let all_bid_rates = document.getElementById('all_bid_rates');

                // remove existing;
                this.bid_rates.forEach(bid_rate => {
                    bid_rate.element.remove();
                });
                all_bid_rates.innerText = "";
                this.bid_rates = [];

                post('get_bid_rates/', {'bid_id': this.data.id}).then(resp => {
                    show_modal('bid_rates');

                    resp.forEach(data => {
                        let bid_rate = new BidRow(this, data.task_type__name, data.base_rate, data.rate, data.bids, 0, data.id);
                        all_bid_rates.append(bid_rate.element);
                        this.bid_rates.push(bid_rate);
                    });

                    this.update();
                    hide_loading();
                });

                // CONNECT THE SAVE BUTTON;

                document.getElementById('update_bid_rates').onclick = () => {
                    if (confirm('Please confirm that you want to update the rates')) {
                        show_loading();
                        let bid_rates = [];

                        this.bid_rates.forEach(bid_rate => {
                            bid_rates.push({'id': bid_rate.id, 'rate': bid_rate.rate})
                        });

                        post('update_bid_rates/', {'bid_id': this.data.id, 'bid_rates': bid_rates}).then(resp => {
                            hide_modal('bid_rates');
                            hide_loading();
                        })
                    }
                }
            };
        }

        // show slider
        this.element.querySelector('.clickable').onclick = () => {
            SLIDER.set_parent(this);
            SLIDER.element.querySelector('.parent_name').innerText = `${this.data.client__name} / ${this.data.project} `;
            SLIDER.show();
        };
    }

    update() {
        let total_bids = this.bid_rates.reduce((x, row) => x += parseFloat(row.bids), 0);
        let total_price = this.bid_rates.reduce((x, row) => x += parseFloat(row.price), 0);
        let weighted_margin = 0;

        this.bid_rates.forEach(row => {
            if (row.bids > 0) {
                weighted_margin += row.margin * row.bids / total_bids;
            }
        });

        document.getElementById(`total_margin`).innerText = `${weighted_margin.toFixed(2)}%`;
        document.getElementById(`total_bids`).innerText = total_bids.toFixed(2);
        document.getElementById(`total_price`).innerText = `$ ${total_price.toFixed(2)}`;
    }
}

class BidRow {
    constructor(parent, dept, base_rate, rate, bids, base_rop = 0, id = null) {
        this.parent = parent;
        this.base_rate = base_rate;
        this.rate = rate;
        this.margin = 0;
        this.bids = bids || 0;
        this.price = this.rate * this.bids;
        this.base_rop = base_rop;
        this.id = id;

        this.element = createElements(
            el('tr', {'class': 'align-center'},
                el('td', {'class': 'align-left'}, dept),
                el('td', {}, this.base_rate),
                el('td', {},
                    el('input', {
                        'class': 'no-border align-center',
                        'value': this.rate,
                        'name': 'rate',
                        'type': 'number',
                        'step': 0.01
                    }, '')
                ),
                el('td', {'class': 'margin'}, '0.00%'),
                el('td', {},
                    el('input', {
                        'class': 'no-border align-center',
                        'value': this.bids,
                        'name': 'bids',
                        'type': 'number',
                        'step': 0.01,
                    }, '')
                ),
                el('td', {'class': 'price'}, '$ 0.00'),
            )
        );

        if (this.id) {
            this.element.querySelector('input[name="bids"]').readOnly = true;
        }

        this.element.querySelectorAll('input').forEach(input => {
            input.onclick = () => {
                input.select();
            }
        });

        this.element.querySelector('input[name="rate"]').onchange = (event) => {
            this.rate = event.target.value;
            this.update();
        };
        this.element.querySelector('input[name="bids"]').onchange = (event) => {
            this.bids = event.target.value;
            this.update();
        };

        this.update();
    }

    calculate_bids() {
        this.bids = Math.round(((1440 * (this.parent.fps / 24) * this.parent.minutes) / this.base_rop) * (this.parent.budget / 80) * this.parent.resolution);
        this.element.querySelector('input[name="bids"]').value = this.bids.toFixed(2);
        this.element.querySelector('input[name="bids"]').readOnly = true;
    }

    update() {
        if (this.parent.type == 'stereo') {
            this.calculate_bids();
        }

        this.margin = (this.rate > 0) ? ((this.rate - this.base_rate) / this.rate) * 100 : 0;
        this.price = this.rate * this.bids;

        this.element.querySelector('.margin').innerText = `${this.margin.toFixed(2)}%`;
        this.element.querySelector('.price').innerText = `$ ${this.price.toFixed(2)}`;

        this.parent.update();
    }
}

class Calculator {
    constructor() {
        this.departments = ['roto', 'paint', 'depth', 'comp'];
        this.base_rate = {};
        this.base_rop = {};
        this.rows = [];
        this.type = '';
    }

    get_base_rates() {
        return post('get_base_rates/', {}).then(resp => {
            resp.forEach(rate => {
                this.base_rate[rate['task_type']] = rate['rate'];

                if (this.type == 'vfx')
                    this.departments.push(rate['task_type']);
            });
        })
    }

    get_base_rop() {
        return post('get_base_rop/', {}).then(resp => {
            resp.forEach(rate => {
                this.base_rop[rate['task_type']] = rate['rate'];
            });
        })
    }

    update() {
        let total_bids = this.rows.reduce((x, row) => x += parseFloat(row.bids), 0);
        let total_price = this.rows.reduce((x, row) => x += parseFloat(row.price), 0);
        let weighted_margin = 0;

        this.rows.forEach(row => {
            if (row.bids > 0) {
                weighted_margin += row.margin * row.bids / total_bids;
            }
        });

        let calc = (this.type == 'vfx') ? 'vbc' : 'sbc';

        document.getElementById(`${calc}_weighted_margin`).innerText = `${weighted_margin.toFixed(2)}%`;
        document.getElementById(`${calc}_total_bids`).innerText = total_bids.toFixed(2);
        document.getElementById(`${calc}_total_price`).innerText = `$ ${total_price.toFixed(2)}`;
    }
}

class StereoBidCalculator extends Calculator {
    constructor() {
        super();
        this.type = 'stereo';
        this.minutes = 1;
        this.budget = 80;
        this.fps = 24;
        this.resolution = 1;

        this.init();
    }

    async init() {
        await this.get_base_rates();
        await this.get_base_rop();

        this.element = createElements(el('tbody', {}, ''));

        this.departments.forEach(dept => {
            let row = new BidRow(this, dept, this.base_rate[dept], this.base_rate[dept], 0, this.base_rop[dept]);

            this.rows.push(row);
            this.element.append(row.element);
        });

        let table = document.getElementById('sbc_table');
        table.replaceChild(this.element, table.querySelector('tbody'));


        document.getElementById("sbc_minutes").onchange = (event) => {
            this.minutes = parseFloat(event.target.value);
            this.rows.forEach(row => row.update());
        };
        document.getElementById("sbc_budget").onchange = (event) => {
            this.budget = parseFloat(event.target.value);
            this.rows.forEach(row => row.update());
        };
        document.getElementById("sbc_fps").onchange = (event) => {
            this.fps = parseInt(event.target.value);
            this.rows.forEach(row => row.update());
        };
        document.getElementById("sbc_resolution").onchange = (event) => {
            this.resolution = parseFloat(event.target.value);
            this.rows.forEach(row => row.update());
        };

        this.update();
    }
}

class VFXBidCalculator extends Calculator {
    constructor() {
        super();
        this.type = 'vfx';
        this.init();
    }

    async init() {
        await this.get_base_rates();

        this.element = createElements(el('tbody', {}, ''));

        this.departments.forEach(dept => {
            let row = new BidRow(this, dept, this.base_rate[dept], this.base_rate[dept], 0);
            this.rows.push(row);

            this.element.append(row.element);
        });

        let table = document.getElementById('vbc_table');
        table.replaceChild(this.element, table.querySelector('tbody'));

        this.update();
    }


}

const get_defaults = () => {
    return post('get_defaults/', {}).then(resp => {
        ALL_BID_STATUS = resp.bid_status;

        new SlimSelect({
            select: document.getElementById('filter_client'),
            data: [{text: '', value: '', placeholder: true}].concat(resp.all_clients.map(x => {
                return {text: x.name, value: x.id}
            })),
            placeholder: 'Select Client',
            allowDeselect: true,
            onChange: (select) => {
                apply_filters('client_id', select.value)
            }
        });

        new SlimSelect({
            select: document.getElementById('filter_project'),
            data: [{text: '', value: '', placeholder: true}].concat(resp.all_projects.map(x => {
                return {text: x.name, value: x.name}
            })),
            placeholder: 'Select Project',
            allowDeselect: true,
            onChange: (select) => {
                apply_filters('project', select.value)
            }
        });

        // Status Filter
        let filter_status_id = document.getElementById('filter__status_id');
        resp.bid_status.forEach(x => {
            let filter = createElements(
                el('label', {'class': 'block'},
                    el('input', {
                        'type': 'checkbox', 'class': 'filter', 'checked': true, 'onclick': 'apply_filters()',
                        'data-filter_key': 'status_id', 'data-filter_value': x.id
                    }),
                    el('span', {}, x.name)
                )
            );
            filter_status_id.appendChild(filter);
        });

        // Select Default Tasks
        document.querySelectorAll('.select-default_tasks').forEach(select => {
            new SlimSelect({
                select: select,
                data: [{
                    'placeholder': true,
                    'text': '',
                    'value': ''
                }].concat(resp.task_types.map(x => {
                    return {'value': x.id, 'text': x.name}
                })),
                placeholder: 'Select Default Tasks',
            });
        });

        // update status modal
        let select_project = new SlimSelect({
            select: document.getElementById('select_project_id'),
            data: [{text: '', value: '', placeholder: true}],
            addable: function (value) {
                return {text: value, value: value}
            },
            placeholder: 'Select Project'
        });

        // select project type
        new SlimSelect({
            select: document.getElementById('select_project_type_id'),
            data: [{text: '', value: '', placeholder: true}].concat(resp.project_types.map(x => {
                return {text: x.name, value: x.id}
            })),
            placeholder: 'Select Project Type'
        });

        // Add to new bid form
        new SlimSelect({
            select: document.getElementById('select_client_id'),
            data: [{text: '', value: '', placeholder: true}].concat(resp.all_clients.map(x => {
                return {text: x.name, value: x.id}
            })),
            onChange: (select) => {
                post('get_client_projects/', {'client_id': select.value}).then(resp => {
                    select_project.setData([{
                        text: '',
                        value: '',
                        placeholder: true
                    }].concat(resp.map(x => {
                        return {text: x.name, value: x.name}
                    })))
                })
            },
            placeholder: 'Select Client',
        });
    })
};

const get_all_bids = () => {
    show_loading();

    let all_bids = document.getElementById('all_bids');

    ALL_BIDS.forEach(bid => bid.element.remove());
    ALL_BIDS = [];

    return post('get_all_bids/', {}).then(resp => {
        resp.forEach(data => {
            let bid = new Bid(data);
            ALL_BIDS.push(bid);

            // append
            all_bids.append(bid.element);
        });
        hide_loading();
    })
};

const add_bid = (form) => {
    show_loading();

    let data = formdata(form);
    post('add_bid/', data).then(resp => {
        get_all_bids();
        hide_modal('add_bid');
        hide_modal('edit_bid');
    })
};

const apply_filters = (key = null, input = null) => {
    let search_bid = document.getElementById('search_bid_name').value.toLowerCase();
    let filter_client = document.getElementById('filter_client').value;
    let filter_project = document.getElementById('filter_project').value;
    let FILTERED_PROJECTS = [];

    ALL_BIDS.forEach(bid => {
        bid.element.style.display = 'table-row';

        if (search_bid != "" && bid.data.name.toLowerCase().indexOf(search_bid) == -1) {
            bid.element.style.display = 'none';
        } else if (filter_client != "" && bid.data.client_id != filter_client) {
            bid.element.style.display = 'none';
        } else if (filter_project != "" && bid.data.project != filter_project) {
            bid.element.style.display = 'none';
        } else {
            FILTERED_PROJECTS.push(bid)
        }
    });

    base_filter(key, input, FILTERED_PROJECTS);
};

window.onload = async () => {
    await init('Bidding System');

    // add slider
    SLIDER = new Slider();
    document.getElementById('modals').append(SLIDER.element);

    // load the stereo bid calculator
    if (has_permission('bidding_system_bid_rate')) {
        new StereoBidCalculator();
        new VFXBidCalculator()
    }

    await get_defaults();
    await get_all_bids();

    hide_loading()
};