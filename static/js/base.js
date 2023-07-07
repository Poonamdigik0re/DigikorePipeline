// exported classes
let DATE_RANGE = [];
let DATE_RANGE_HEADERS = [];
let WEEKENDS = [];
let HOLIDAYS = [];

class Slider {
    constructor() {
        this.notes = [];
        this.element = createElements(
            el('div', {'class': 'flex-grow flex-column', 'id': 'slider'},
                el('div', {'class': 'heading flex-row flex-no-shrink p10'},
                    el('div', {'class': 'flex-grow parent_name'}, ''),
                    el('div', {'class': 'icon close'})
                ),
                el('div', {'class': 'flex-grow flex-column'},
                    el('div', {'class': 'flex-row flex-no-shrink tabs'},
                        el('div', {'class': 'tab active p10', 'data-tab': 'info'}, 'Info'),
                        el('div', {'class': 'tab p10', 'data-tab': 'notes'}, 'Notes'),
                        el('div', {'class': 'tab p10', 'data-tab': 'attachments'}, 'Attachments'),
                    ),

                    // info
                    el('div', {'class': 'flex-grow flex-column tab-content active', 'data-tab': 'info'},
                        el('div', {'class': 'flex-grow p5 all_info'}, '')
                    ),

                    // notes
                    el('div', {'class': 'flex-grow flex-column tab-content', 'data-tab': 'notes'},
                        el('div', {'class': 'flex-column flex-no-shrink p10 border-bottom'},
                            el('textarea', {
                                'rows': 3,
                                'class': 'note_text flex-grow',
                                'placeholder': 'Note Text',
                                'required': 'required'
                            }, ''),
                            el('br', {}, ''),
                            el('div', {'class': 'flex-row'},
                                el('select', {'class': 'wp80 note_type_id'}, ''),
                                el('button', {'style': 'margin-left: 0.5em', 'class': 'add_note wp20'}, 'Add')
                            ),
                        ),
                        el('div', {'class': 'flex-grow all_notes p5'}, '')
                    ),

                    // attachments
                    el('div', {'class': 'flex-grow flex-column tab-content', 'data-tab': 'attachments'},
                        el('div', {'class': 'flex-row flex-no-shrink p10 border-bottom'},
                            el('input', {
                                'type': 'file',
                                'class': 'attachment_files flex-grow',
                                'multiple': 'multiple'
                            }, ''),
                            el('button', {'style': 'margin-left: 0.5em', 'class': 'add_attachment'}, 'Upload File')
                        ),
                        el('div', {'class': 'flex-grow p10'},
                            el('table', {'class': 'table'},
                                el('colgroup', {},
                                    el('col', {'width': '50%'}),
                                    el('col', {'width': '40%'}),
                                    el('col', {'width': '10%'}),
                                ),
                                el('thead', {},
                                    el('tr', {},
                                        el('th', {}, 'Name'),
                                        el('th', {}, 'Created On'),
                                        el('th', {}, ''),
                                    )
                                ),
                                el('tbody', {'class': 'all_attachments'})
                            ),
                        )
                    ),
                )
            )
        );

        // hide the slider
        this.element.querySelector('.close').onclick = () => {
            this.hide();
        };

        this.select_note_type = new SlimSelect({
            select: this.element.querySelector('.note_type_id')
        });

        this.element.querySelectorAll('.tab').forEach(tab => {
            tab.onclick = (event) => {
                let data_tab = event.target.dataset['tab'];

                this.element.querySelector('.tab.active').className = 'tab p10';
                this.element.querySelector(`.tab[data-tab=${data_tab}]`).className = 'tab active p10';

                this.element.querySelector('.tab-content.active').className = 'flex-grow flex-column tab-content';
                this.element.querySelector(`.tab-content[data-tab=${data_tab}]`).className = 'flex-grow flex-column tab-content active';

                if (data_tab === 'info') {
                    this.get_model_info();
                } else if (data_tab === 'notes') {
                    this.get_notes();
                } else if (data_tab === 'attachments') {
                    this.get_attachments()
                }
            };
        });

        /*
        ADD NOTE
        */

        this.element.querySelector('.add_note').onclick = () => {
            let text = this.element.querySelector('.note_text').value;
            let type_id = this.element.querySelector('.note_type_id').value;
            if (text) {
                post('/base/add_note/', {
                    text: text,
                    type_id: type_id,
                    parent_type: this.parent.type,
                    parent_id: this.parent.data.id,
                }).then(resp => {
                    resp.forEach(data => {
                        let note = this.create_note(data);
                        this.element.querySelector('.all_notes').prepend(note);
                    });

                    this.element.querySelector('.note_text').value = '';
                })
            }
        };

        /*
        ADD ATTACHMENTS
        */

        this.element.querySelector('.add_attachment').onclick = () => {
            let attachment_files = this.element.querySelector('.attachment_files').files;

            if (attachment_files.length > 0) {
                let form_data = new FormData();

                let data = {
                    parent_type: this.parent.type,
                    parent_id: this.parent.data.id,
                };

                form_data.append('data', JSON.stringify(data));

                for (let x = 0; x < attachment_files.length; x++) {
                    form_data.append(`file${x}`, attachment_files[x]);
                }

                post('/base/add_attachments/', form_data, true).then(resp => {
                    this.get_attachments();
                    this.element.querySelector('.attachment_files').files = null;
                })
            }
        };
    }

    create_note(data) {
        return createElements(
            el('div', {'class': 'note flex-row'},
                el('div', {'class': 'note-user'},
                    el('img', {
                        'src': `/media/${data['created_by__userprofile__profile_picture']}`,
                        'width': '50px',
                        'height': '50px'
                    }),
                ),
                el('div', {'class': 'note-content'},
                    el('span', {'class': 'bold'}, data['created_by__userprofile__full_name']),
                    el('span', {
                        'class': 'badge',
                        'style': `margin-left: 1em; background: ${data.type__bg_color}; color: ${data.type__fg_color}`
                    }, data['type__name']),
                    el('div', {'style': 'margin: 0.5em 0'}, data['text']),
                    el('div', {'class': 'note-footer'}, local_datetime(data['created_on']))
                )
            )
        );
    }

    create_attachment(data) {
        return createElements(
            el('tr', {},
                el('td', {}, data.name),
                el('td', {}, local_datetime(data.created_on)),
                el('td', {},
                    el('a', {
                            'href': `/media/${data.file}`,
                            'download': data.name,
                        }, el('div', {'class': 'icon download'}, '')
                    ),
                )
            )
        );
    }

    get_model_info() {
        post('/base/get_model_info/', {
            parent_type: this.parent.type,
            parent_id: this.parent.data.id
        }).then(resp => {
            let all_info = this.element.querySelector('.all_info');
            all_info.innerText = '';
            let children = [];

            for (let k in resp) {
                if (['type__name', 'status__name', 'complexity__name', 'priority__name'].indexOf(k) != -1) {
                    let bg = resp[k.replace('__name', '__bg_color')];
                    let fg = resp[k.replace('__name', '__fg_color')];

                    children.push(el('tr', {},
                        el('th', {}, k.replace('__name', ' ')),
                        el('td', {
                            'style': `background-color:${bg}; color:${fg}`
                        }, resp[k])
                    ))
                }
            }

            for (let k in resp) {
                if (['id', 'parent_id', 'parent_type', 'created_on', 'modified_on'].indexOf(k) == -1) {
                    if (k.search(/__/g) == -1 && k.search(/_id/g) == -1) {
                        children.push(el('tr', {},
                            el('th', {}, k),
                            el('td', {}, resp[k] || '-')
                        ))
                    }
                    if (['vendor__name', 'client__name'].indexOf(k) != -1) {
                        children.push(el('tr', {},
                            el('th', {}, k.replace('__name', '')),
                            el('td', {}, resp[k] || '-')
                        ))
                    }
                }

                if (k == 'created_on' || k == 'modified_on') {
                    children.push(el('tr', {},
                        el('th', {}, k),
                        el('td', {}, local_datetime(resp[k]))
                    ))
                }

                if (k == 'created_by__userprofile__full_name') {
                    children.push(el('tr', {},
                        el('th', {}, 'created_by'),
                        el('td', {}, resp[k] || '-')
                    ))
                }
            }

            all_info.append(createElements(
                el('table', {'class': 'table fixed'},
                    el('tbody', {}, ...children)
                )
            ));
        });
    }

    get_notes() {
        post('/base/get_notes/', {
            parent_type: this.parent.type,
            parent_id: this.parent.data.id
        }).then(resp => {
            let all_notes = this.element.querySelector('.all_notes');
            all_notes.innerHTML = '';

            resp.forEach(data => {
                let note = this.create_note(data);
                all_notes.append(note)
            })
        })
    }

    get_note_types() {
        post('/base/get_note_types/', {}).then(resp => {
            this.select_note_type.setData(resp.map(x => {
                return {'value': x.id, 'text': x.name, 'selected': x.selected || false}
            }));
        })
    }

    get_attachments() {
        post('/base/get_attachments/', {
            parent_type: this.parent.type,
            parent_id: this.parent.data.id
        }).then(resp => {
            let all_attachments = this.element.querySelector('.all_attachments');
            all_attachments.innerHTML = '';

            resp.forEach(data => {
                let attachment = this.create_attachment(data);
                all_attachments.append(attachment);
            })
        })
    }

    set_parent(parent) {
        this.parent = parent;
        this.get_model_info();
        this.get_notes();
        this.get_attachments();
        this.get_note_types();
    }

    show() {
        this.element.style.right = 0;
    }

    hide() {
        this.element.style.right = window.innerWidth * -0.50 + 'px';
    }
}

class BaseClass {
    constructor(model_type, data) {
        this.model_type = model_type;
        this.data = data;
    }

    get_attachments() {
        post('/base/get_attachments/', {'parent_type': this.model_type, 'parent_id': this.data.id}).then(resp => {
            let table = document.querySelector('#attachment_list');
            let _old = table.querySelector('tbody');
            let _new = createElements(
                el('tbody', {},
                    ...resp.map((attachment, index) => {
                        return el('tr', {},
                            el('td', {}, index + 1),
                            el('td', {},
                                el('a', {
                                    'class': 'clickable',
                                    'href': `/media/${attachment.file}`,
                                    'target': '_blank'
                                }, attachment.name)
                            ),
                            el('td', {}, file_size(attachment.size)),
                            el('td', {}, attachment.created_by__userprofile__full_name),
                            el('td', {}, attachment.created_on),
                            el('td', {},
                                el('a', {'href': `/media/${attachment.file}`, 'download': attachment.name},
                                    el('div', {'class': 'icon download'}, '')
                                )
                            )
                        );
                    })
                )
            );
            table.replaceChild(_new, _old);
        })
    }

    add_attachments() {
        let attachment_files = document.querySelector('#attachment_files').files;

        if (attachment_files.length > 0) {
            let form_data = new FormData();
            form_data.append('parent_type', this.model_type);
            form_data.append('parent_id', this.data.id);

            for (let x = 0; x < attachment_files.length; x++) {
                form_data.append(`file${x}`, attachment_files[x]);
            }
            post('/base/add_attachments/', form_data, true).then(resp => {
                this.get_attachments();
                document.querySelector('#attachment_files').files = null;
            })
        }
    }
}

// create element functions
const setProp = ($target, name, value) => {
    $target.setAttribute(name, value);
};

const setProps = ($target, props) => {
    Object.keys(props).forEach(name => {
        setProp($target, name, props[name]);
    });
};

const el = (type, props, ...children) => {
    return {type, props: props, children}
};

const createElements = (node) => {
    if (typeof node === 'string' || typeof node === 'number' || node === null || node == undefined) {
        return document.createTextNode(node);
    }
    const $el = document.createElement(node.type);
    setProps($el, node.props);
    node.children
        .map(createElements)
        .forEach($el.appendChild.bind($el));
    return $el;
};

// global functions
const show_modal = (id) => {
    let form = document.getElementById(id);
    form.style.display = 'flex';
};

const hide_modal = (id) => {
    let form = document.getElementById(id);
    form.style.display = 'none';
    modal.classList.add('fade-in');

    // reset doesn't clear the hidden fields;
    if (form.nodeName === 'FORM') {
        if (form.hasOwnProperty('id')) {
            form['id'].value = '';
        }
        form.reset();

        // for select, update the slimselect
        for (let i = 0; i < form.elements.length; ++i) {
            if (form[i].tagName === 'SELECT') {
                let event = new Event('change');
                form[i].dispatchEvent(event);
            }
        }
    }
};

const show_tab = (tab, tab_id, callback = null) => {
    // toggle the tab headers
    document.querySelector('.tab.active').classList.remove('active');
    tab.classList.add('active');

    // toggle the tab contents
    document.querySelector('.tab-content.active').classList.remove('active');
    document.querySelector(`.tab-content[data-tab="${tab_id}"]`).classList.add('active');

    if (callback) callback();
};

const show_loading = () => {
    document.getElementById('loading').style.display = 'flex';
};

const hide_loading = () => {
    document.getElementById('loading').style.display = 'none';
};

const change_password = (form) => {
    return post('/base/change_password/', {
        new_password: form.new_password.value,
        confirm_password: form.confirm_password.value
    }).then(resp => {
        location.reload()
    });
};

const read_cookie = (name) => {
    let b = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return b ? b.pop() : '';
};

const formdata = (form) => {
    let data = {};
    for (let i = 0; i < form.elements.length; ++i) {
        let name = form.elements[i].name;
        if (name) {
            if (form[i].tagName === 'SELECT' && form[i].multiple == true) {
                data[name] = [];
                for (let j = 0; j < form[i].children.length; j++) {
                    let child = form[i].children[j];
                    if (child.selected) data[name].push(child.value || child.text);
                }
            } else {
                data[name] = form.elements[i].value;
            }
        }
    }
    return data;
};

function seconds_to_time(seconds) {
    let minutes = seconds / 60;
    let hours = minutes / 60;

    return [parseInt(hours), parseInt(minutes % 60), parseInt(seconds % 60)];
}

function seconds_to_hhmm(seconds) {
    let minutes = seconds / 60;
    let hours = minutes / 60;

    return `${parseInt(hours)}:${parseInt(minutes % 60)}`;
}

function frames_to_seconds(frames) {
    let seconds = frames / 24;
    let minutes = seconds / 60;

    return [parseInt(minutes % 60), parseInt(seconds % 60), parseInt(frames % 24)];
}

const datestring = (string) => {
    let dt = string;
    if (string.constructor !== Date) {
        let [y, m, d] = string.split('-');
        // in date constructor month starts from 0
        dt = new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
    }
    let year = dt.getFullYear();
    let month = dt.getMonth() + 1;
    let date = dt.getDate();

    return parseInt(`${year}${month.toString().padStart(2, "0")}${date.toString().padStart(2, "0")}`);
};

const local_date = (string) => {
    if (string == null || string == "") return "-";

    let dt = new Date(string);
    let month_name = {
            0: 'Jan',
            1: 'Feb',
            2: 'Mar',
            3: 'Apr',
            4: 'May',
            5: 'Jun',
            6: 'Jul',
            7: 'Aug',
            8: 'Sep',
            9: 'Oct',
            10: 'Nov',
            11: 'Dec'
        },
        year = dt.getFullYear(),
        month = dt.getMonth(),
        date = dt.getDate(),
        monthText = month_name[month];

    return `${monthText} ${date}, ${year}`;
};

const local_datetime = (string) => {
    if (string == null || string == "") return "-";

    // trick: add Z to convert to local timezone,
    // let dt = new Date(string + 'Z');
    let dt = new Date(string);
    let month_name = {
            0: 'Jan',
            1: 'Feb',
            2: 'Mar',
            3: 'Apr',
            4: 'May',
            5: 'Jun',
            6: 'Jul',
            7: 'Aug',
            8: 'Sep',
            9: 'Oct',
            10: 'Nov',
            11: 'Dec'
        },
        year = dt.getFullYear(),
        month = dt.getMonth(),
        date = dt.getDate(),
        hour = dt.getHours(),
        min = dt.getMinutes(),
        sec = dt.getSeconds(),
        monthText = month_name[month],
        ampm = (hour > 12) ? 'PM' : 'AM';

    return `${monthText} ${date}, ${year} ${hour % 12}:${(min < 10) ? '0' + min : min}:${(sec < 10) ? '0' + sec : sec} ${ampm}`;
};

const file_size = (bytes) => {
    let mod = `${bytes} Bytes`;

    if (bytes > 1024) {
        bytes = parseInt(bytes / 1024);
        mod = `${bytes} KB`;
    }
    if (bytes > 1024) {
        bytes = parseInt(bytes / 1024);
        mod = `${bytes} MB`;
    }
    if (bytes > 1024) {
        bytes = parseInt(bytes / 1024);
        mod = `${bytes} GB`;
    }
    if (bytes > 1024) {
        bytes = parseInt(bytes / 1024);
        mod = `${bytes} TB`;
    }

    return mod;
};

const post = (url = ``, body = {}, files = null) => {
    let args = {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': window.csrf_token
        },
    };

    if (files) {
        args['body'] = body
    } else {
        args['body'] = JSON.stringify(body);

        args['headers']['Content-Type'] = 'application/json; charset=UTF-8';
    }

    return fetch(url, args).then(response => {
        if (response.ok) {
            if (response.headers.get('Content-Type') === 'text/html; charset=utf-8') {
                return response.text();
            } else if (response.headers.get('Content-Type') === 'application/json') {
                return response.json();
            } else {
                return response;
            }
        } else {
            throw response;
        }
    }).catch(error => {
        error.text().then(message => {
            alert(message);
            console.error(message);
        });
    }).finally(() => {
        hide_loading();
    })
};


// const random_color = () => {
//     var r = Math.floor(Math.random() * 255);
//     var g = Math.floor(Math.random() * 255);
//     var b = Math.floor(Math.random() * 255);
//     return "rgb(" + r + "," + g + "," + b + ")";
// };

const random_color = () => {
    let colors = ['#A02B3E', '#E55244', '#F4793F', '#787E96',
        '#8FAEBF', '#03346D', '#4A90E2', '#61379B',
        '#A774D3', '#D34E59', '#F996AC', '#facd92',
        '#4C5760', '#00b601', '#E09F3E', '#5BC0EB',
        '#FDE74C', '#9BC53D', '#E55934', '#FA7921',
        '#50514F', '#F25F5C', '#ff00e7', '#247BA0',
        '#70C1B3', '#EF476F', '#073B4C', '#06D6A0'];

    return colors[Math.floor(Math.random() * colors.length)];
};

const base_filter = (key = null, input = null, data = [], callback = null) => {
    if (key && input) {
        document.querySelectorAll('.filter').forEach((filter) => {
            if (filter.dataset['filter_key'] === key) {
                filter.checked = input.checked;
            }
        })
    }

    // COLLECT FILTERS
    let filters = {};
    document.querySelectorAll('.filter').forEach((filter) => {
        let checked = filter.checked;
        let filter_key = filter.dataset['filter_key'];
        let filter_value = filter.dataset['filter_value'];

        if (!filters.hasOwnProperty(filter_key)) {
            filters[filter_key] = [];
        }
        if (checked) {
            filters[filter_key].push(filter_value)
        }
    });

    // FILTER ROWS
    data.forEach((d) => {
        d.element.style.display = d.element.dataset['display'] || 'table-row';

        for (let k in filters) {
            let v = filters[k];
            if (d.data.hasOwnProperty(k)) {
                if (v.indexOf(d.data[k].toString()) === -1) {
                    d.element.dataset['display'] = d.element.style.display;
                    d.element.style.display = 'none';
                }
            }
        }
    });

    // run any callback if exists;
    if (callback) callback();
};

const load_timeline_header = (callback = null) => {
    /*
    This function requires DATE_RANGE and WEEKENDS to be defined in global scope;
     */

    // reset the date headers
    DATE_RANGE = [];
    get_date_range();

    let _old = document.getElementById('timeline_header');
    let _new = createElements(el('div', {'class': 'flex-grow flex-row align-center', 'id': 'timeline_header'},
        ...DATE_RANGE.map((date, index) => {
            if (WEEKENDS.indexOf(date) != -1) {
                return el('div', {'class': 'flex-grow weekend'}, index + 1);
            } else {
                return el('div', {'class': 'flex-grow'}, index + 1);
            }
        }))
    );

    _old.parentNode.replaceChild(_new, _old);

    // run callback if mentioned
    if (callback) callback();
};

const get_date_range = () => {
    /*
    This function requires DATE_RANGE and WEEKENDS to be defined in global scope;
    */
    DATE_RANGE = [];
    DATE_RANGE_HEADERS = [];
    WEEKENDS = [];

    let select__month = document.getElementById('select__month').value;
    let [year, month] = select__month.split('-');
    let date = new Date(parseInt(year), parseInt(month), 0);
    let days = date.getDate();

    for (let i = 1; i <= days; ++i) {
        let dt = new Date(date.setDate(i));
        DATE_RANGE.push(datestring(dt));
        DATE_RANGE_HEADERS.push(['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][dt.getDay()]);

        if (dt.getDay() === 0 || dt.getDay() === 6) {
            WEEKENDS.push(datestring(dt));
        }
    }
};

const select_text = (element) => {
    let selection = window.getSelection();
    let range = document.createRange();
    range.selectNodeContents(element);
    selection.removeAllRanges();
    selection.addRange(range);
};

// functions used on several pages.

const get_all_shifts = (callback) => {
    return post('/base/get_all_shifts/', {}).then(resp => callback(resp))
};

//const get_username = (callback) => {
//    return post('/base/get_username/', {}).then(resp => callback(resp))
//};

const get_all_departments = (callback) => {
    return post('/base/get_all_departments/', {}).then(resp => callback(resp))
};

const get_all_designations = (callback) => {
    return post('/base/get_all_designations/', {}).then(resp => callback(resp))
};

const get_all_skills = (callback) => {
    return post('/base/get_all_skills/', {}).then(resp => callback(resp))
};

const get_all_locations = (callback) => {
    return post('/base/get_all_locations/', {}).then(resp => callback(resp))
};

const get_all_confirmation_status = (callback) => {
    return post('/base/get_all_confirmation_status/', {}).then(resp => callback(resp))
};

const get_all_holidays = () => {
    return post('/base/get_all_holidays/', {}).then(resp => {
        HOLIDAYS = resp;
    })
};

const get_user_details = () => {
    return post('/base/get_user_details/', {}).then(resp => {
        window.user = resp;

        if (window.user.password_reset) {
            show_modal('change_password');
            document.getElementById('change_password_label').innerText = "Please change your password";
        }
    })
};

function has_permission(permission) {
    return window.user.permissions.indexOf(permission) >= 0;
}

//*** Ticketing System Code ***///

// Auto Expand Text Areas
const autoExpand = (field) => {
    // Reset field height
    field.style.height = '5vh';
    // Get the computed styles for the element
    let computed = window.getComputedStyle(field);
    // Calculate the height
    let height = parseInt(computed.getPropertyValue('border-top-width'), 10)
        + parseInt(computed.getPropertyValue('padding-top'), 10)
        + field.scrollHeight
        + parseInt(computed.getPropertyValue('padding-bottom'), 10)
        + parseInt(computed.getPropertyValue('border-bottom-width'), 10);
    field.style.height = height + 'px';
};

//Deselect Select_All Options
const deselect_All = (ele) => {
    let children = ele.querySelectorAll(".filter");
    let chkChildren = ele.querySelectorAll(".filter:checked");
    if (children.length == chkChildren.length) {
        ele.querySelector(".select_all").checked = true
    } else
        ele.querySelector(".select_all").checked = false
};


const init_notification = () => {
    if ("Notification" in window) {
        if (Notification.permission != 'granted') {
            Notification.requestPermission()
        }
    }
};

const init_websocket = () => {
    let pathname = location.pathname.replace(/\//g, '');

    window.websocket = new WebSocket(`ws://${location.hostname}:8101/websocket/${pathname}`, 'echo-protocol');

    window.websocket.onopen = () => {
        console.log('Websocket connection established...');
    };

    window.websocket.onmessage = (msg) => {
        let message = JSON.parse(msg.data);
        let func = message['func'];
        let data = message['data'];

        let event = new Event(func);
        event.data = data;
        document.dispatchEvent(event);
    };

    window.websocket.onclose = () => {
        console.warn('Websocket connection closed...');
        if (confirm("You lost the websocket connection, its suggested that you refresh your browser. Do you want to reload now?")) {
            location.reload();
        }
    }
};

const init = async (title = null) => {
    show_loading();

    // set window.title;
    if (title != null) document.title = title;

    // location.search to dict
    window.search = {};
    if (window.location.search !== "") {
        window.location.search.split("?")[1].split("&").map((srch) => {
            window.search[srch.split('=')[0]] = decodeURIComponent(srch.split('=')[1])
        });
    } else if (window.location.hash != "") {
        window.search = JSON.parse(decodeURIComponent(window.location.hash.split('#')[1]))
    }

    // set local date
    document.querySelectorAll('.local_date').forEach((elem) => {
        elem.innerText = local_date(elem.innerText)
    });

    // set local datetime
    document.querySelectorAll('.local_datetime').forEach((elem) => {
        elem.innerText = local_datetime(elem.innerText)
    });

    // get csrftoken
    window.csrf_token = read_cookie('csrftoken');
    console.log(window.csrf_token);

    // global keypress events
    document.addEventListener('keyup', (event) => {
        // hide the modal when escape is pressed
        if (event.key === 'Escape') {
            document.querySelectorAll('.modal').forEach(modal => {
                hide_modal(modal.getAttribute('id'));
            });
        }
    });

    // datetime flatpicker
    document.querySelectorAll('.datetime').flatpickr({
        allowInput: true,
        // altInput: true,
        // altFormat: "F j, Y",
        // dateFormat: "Y-m-d"
    });

    // start notification
    init_notification();

    // get user details
    await get_user_details();
};

