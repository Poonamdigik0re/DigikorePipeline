let ALL_WORKSTATIONS = [];

class Workstation {
    constructor(data) {
        this.data = data;
        this.visible = true;
        this.element = createElements(el('tr', {},
            el('td', {},
                el('div', {'class': this.data.status}, '')
            ),
            el('td', {}, this.data.hostname),
            el('td', {}, this.data.user),
            el('td', {}, this.data.cpu),
            el('td', {}, this.data.ram),
            el('td', {}, this.data.ip),
            el('td', {}, this.data.mac),
            el('td', {}, this.data.hdd),
            el('td', {}, this.data.gpu),
            el('td', {}, this.data.os),
            el('td', {}, this.data.sys_vendor),
            el('td', {}, this.data.product_name),
        ));
    }
}

const get_all_workstations = () => {
    show_loading();
    return post('get_all_workstations/', {}).then(resp => {
        let workstations = document.getElementById('workstations');
        let filters = {
            'cpu': [],
            'ram': [],
            'gpu': [],
            'sys_vendor': [],
            'product_name': [],
        };

        resp.forEach(data => {
            let wrk = new Workstation(data);
            workstations.append(wrk.element);

            // add to global list
            ALL_WORKSTATIONS.push(wrk);

            // get all the filters values
            for (let key in filters) {
                if (filters[key].indexOf(data[key]) == -1) {
                    filters[key].push(data[key])
                }
            }
        });

        for (let key in filters) {
            new SlimSelect({
                select: document.getElementById(`filter__${key}`),
                data: [{placeholder: true, text: '', value: ''}].concat(filters[key].map(x => {
                    return {text: x, value: x}
                })),
                allowDeselect: true,
                placeholder: `Filter by ${key}`,
                onChange: (select) => {
                    apply_filters()
                }
            });
        }

        document.getElementById('total_machines').innerText = resp.length;
        hide_loading();
    })
};

const apply_filters = () => {
    let filters = ['cpu', 'ram', 'gpu', 'sys_vendor', 'product_name'];

    // unhide all rows
    ALL_WORKSTATIONS.forEach(wrk => {
        wrk.element.style.display = 'table-row';
        wrk.visible = true;
    });

    // hide rows that don't match the filter
    filters.forEach(filter => {
        let value = document.getElementById(`filter__${filter}`).value;
        if (value != "") {
            ALL_WORKSTATIONS.forEach(wrk => {
                if (wrk.data[filter] != value) {
                    wrk.element.style.display = 'none';
                    wrk.visible = false
                }
            });
        }
    });

    // update the count
    document.getElementById('total_machines').innerText = ALL_WORKSTATIONS.filter(x => {
        return x.visible == true
    }).length;
};

window.onload = async () => {
    show_loading();
    await init();
    await get_all_workstations();

    // set title
    document.title = 'Workstations';
    hide_loading()
};