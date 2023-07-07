let ALL_LEAVES = [];
let ALL_COMP_OFFS = [];

class LeaveLog {
    constructor(data) {
        this.data = data;

        this.element = createElements(el('tr', {},
            el('td', {}, local_date(this.data.created_on)),
            el('td', {}, this.data.total_days),
            el('td', {}, this.data.leave_type),
            el('td', {}, this.data.comment),
        ));
    }
}


class Leave {
    constructor(data) {
        this.data = data;

        this.approve_btn = el('div', {}, '');
        this.reject_btn = el('div', {}, '');
        this.cancel_btn = el('div', {}, '');

        if (this.data.user_id == window.user.id && this.data.status == 'approved') {
            this.cancel_btn = el('div', {'class': 'icon cancel', 'onclick': `cancel_leave(${this.data.id})`}, '');
        }

        this.element = createElements(el('tr', {},
            el('td', {}, this.data.user__userprofile__full_name),
            el('td', {}, this.data.user__userprofile__team__lead__userprofile__full_name),
            el('td', {}, local_date(this.data.created_on)),
            el('td', {}, local_date(this.data.from_date)),
            el('td', {}, local_date(this.data.to_date)),
            el('td', {}, this.data.total_days),
            el('td', {}, this.data.status),
            el('td', {}, this.data.leave_type.replace('_', " ")),
            el('td', {}, this.data.reason),
            el('td', {'class': 'flex-row'}, this.approve_btn, this.reject_btn, this.cancel_btn)
        ));
    }
}

class Compoff {
    constructor(data) {
        this.data = data;

        this.element = createElements(el('tr', {'class': `this.data_status ${this.data.status}`},
            el('td', {'class': 'checkbox'}, ''),
            el('td', {}, this.data.user__userprofile__full_name),
            el('td', {}, this.data.user__userprofile__team__lead__userprofile__full_name),
            el('td', {}, local_date(this.data.date)),
            el('td', {}, this.data.total_days),
            el('td', {}, this.data.status),
            el('td', {}, this.data.reason),
        ));
    }
}

const get_leave_count = () => {
    return post('get_leave_count/', {}).then(resp => {
        document.querySelector('#paid_leave_count').innerText = resp.paid_leave;
        document.querySelector('#casual_leave_count').innerText = resp.casual_leave;
        document.querySelector('#comp_off_count').innerText = resp.comp_off;
    })
};

const get_leave_log = () => {
    let leave_log_table = document.querySelector('#leave_log');

    return post('get_leave_log/', {}).then(resp => {
        resp.forEach(data => {
            let log = new LeaveLog(data);
            leave_log_table.append(log.element);
        })
    })
};

// ALL LEAVES

const get_all_leaves = () => {
    let all_leaves_table = document.querySelector('#all_leaves');

    ALL_LEAVES.forEach(leave => {
        leave.element.remove();
    });
    ALL_LEAVES = [];

    return post('get_all_leaves/', {}).then(resp => {
        resp.forEach(data => {
            let leave = new Leave(data);
            all_leaves_table.append(leave.element);

            ALL_LEAVES.push(leave);
        })
    })
};

const apply_leave = (form) => {
    hide_modal('apply_leave');
    show_loading();

    let data = {
        leave_type: form.leave_type.value,
        from_date: form.from_date.value,
        to_date: form.to_date.value,
        reason: form.reason.value
    };

    post('apply_leave/', data).then(resp => {
        get_leave_count();
        get_leave_log();
    });
};

const cancel_leave = (id) => {
    return post('cancel_leave/', {id: id}).then(resp => {
        get_all_leaves();
    });
};

const reject_leave = (id) => {
    return post('reject_leave/', {id: id}).then(resp => {
        get_all_leaves();
    })
};

const approve_leave = (id) => {
    return post('approve_leave/', {id: id}).then(resp => {
        get_all_leaves();
    })
};

// ALL COMP OFFS

const get_all_comp_offs = () => {
    let all_comp_offs_table = document.querySelector('#all_comp_offs');
    ALL_COMP_OFFS.forEach(comp_off => {
        comp_off.element.remove();
    });
    ALL_COMP_OFFS = [];

    return post('get_all_comp_offs/', {}).then(resp => {
        resp.forEach(data => {
            let comp_off = new Compoff(data);
            all_comp_offs_table.append(comp_off.element);

            ALL_COMP_OFFS.push(comp_off);
        })
    })
};

// ALL LATE MARKS

const get_all_late_marks = () => {
    return post('get_all_late_marks/', {}).then(resp => {

    })
};

window.onload = async () => {
    show_loading();
    await init();

    get_leave_count();
    get_leave_log();

    // set title
    document.title = 'Leave Manager';
    hide_loading()
};