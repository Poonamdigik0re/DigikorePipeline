let SPREADSHEET;
let PROJECTS = [];
let DEPARTMENTS = [];
let OTHER_DEPARTMENTS = [];
let INITIALIZED = false;

const get_cell = (index, col_offset = 0) => {
    // A = 65, Z = 90
    let col = 65 + parseInt(index) + col_offset;
    let cell = String.fromCharCode(col);
    if (col > 90) {
        let a = 65;
        let b = col - 90 + 64;

        cell = String.fromCharCode(a) + String.fromCharCode(b);
    }

    return cell;
};

const get_departments = () => {
    return post('get_departments/', {}).then(resp => {
        let tabs = document.querySelector('.tabs');

        resp.forEach(dept => {
            let tab = createElements(el('div', {
                'onclick': 'load_data(this)',
                'class': 'tab',
                'data-tab': dept.id,
                'data-name': dept.name
            }, dept.name));
            tabs.append(tab);
        });

        let tab = createElements(el('div', {
            'onclick': 'load_annual_projection(this)',
            'class': 'tab',
            'data-tab': 'overview',
        }, 'All Departments'));
        tabs.append(tab);

        let tab2 = createElements(el('div', {
            'onclick': 'load_annual_charts(this)',
            'class': 'tab',
            'data-tab': 'charts',
        }, 'Charts'));
        tabs.append(tab2);

        DEPARTMENTS = resp;
    })
};

const get_headcount = (department_id, row, col_offset) => {
    post(`get_headcount/`, {
        'department_id': department_id,
        'date_range': DATE_RANGE
    }).then(resp => {
        resp.forEach((d, i) => {
            let cell = get_cell(i, col_offset);
            SPREADSHEET.setValue(`${cell}${row}`, d);
        })
    })
};

const get_working_hours = (department_id, row, col_offset) => {
    post(`get_working_hours/`, {
        'department_id': department_id,
        'date_range': DATE_RANGE
    }).then(resp => {
        resp.forEach((d, i) => {
            let cell = get_cell(i, col_offset);
            SPREADSHEET.setValue(`${cell}${row}`, d);
        })
    })
};

const get_resource_share = (department_id, row, col_offset) => {
    post('get_resource_share/', {
        'department_id': department_id,
        'date_range': DATE_RANGE
    }).then(resp => {
        for (let date in resp.borrowed) {
            let value = resp.borrowed[date];
            console.log(date, value);
            if (value > 0 && value != null) {
                let column = DATE_RANGE.indexOf(datestring(date));
                let cell = get_cell(column, col_offset);

                SPREADSHEET.setValue(`${cell}${row}`, value);
            }
        }

        // update the row count
        row += 1;

        resp.lend.forEach(share => {
            let column = DATE_RANGE.indexOf(datestring(share.date));
            let row_offset = OTHER_DEPARTMENTS.indexOf(OTHER_DEPARTMENTS.filter(dept => {
                return dept.id == share.to_department_id
            })[0]) + row;
            let cell = get_cell(column, col_offset);

            SPREADSHEET.setValue(`${cell}${row_offset}`, share.count);
        })
    })
};

const get_leaves = (department_id, row, col_offset) => {
    post(`get_leaves/`, {
        'department_id': department_id,
        'date_range': DATE_RANGE
    }).then(resp => {
        resp.forEach((d, i) => {
            let cell = get_cell(i, col_offset);
            SPREADSHEET.setValue(`${cell}${row}`, d);
        })
    })
};

const get_absents = (department_id, row, col_offset) => {
    post(`get_absents/`, {
        'department_id': department_id,
        'date_range': DATE_RANGE
    }).then(resp => {
        resp.forEach((d, i) => {
            let cell = get_cell(i, col_offset);
            SPREADSHEET.setValue(`${cell}${row}`, d);
        })
    })
};

const get_holidays = (col_offset) => {
    return post('get_holidays/', {date_range: DATE_RANGE}).then(resp => {
        HOLIDAYS = resp;

        // update holidays
        HOLIDAYS.map(d => {
            let index = DATE_RANGE.indexOf(datestring(d));
            if (index >= 0) {
                let cell = get_cell(index, col_offset);
                SPREADSHEET.setStyle(`${cell}1`, 'background-color', 'deepskyblue');
                SPREADSHEET.setStyle(`${cell}2`, 'background-color', 'deepskyblue');
                SPREADSHEET.setStyle(`${cell}3`, 'background-color', 'deepskyblue');
                SPREADSHEET.setStyle(`${cell}4`, 'background-color', 'deepskyblue');
                SPREADSHEET.setStyle(`${cell}5`, 'background-color', 'deepskyblue');
                SPREADSHEET.setStyle(`${cell}6`, 'background-color', 'deepskyblue');
                SPREADSHEET.setStyle(`${cell}7`, 'background-color', 'deepskyblue');
                SPREADSHEET.setStyle(`${cell}8`, 'background-color', 'deepskyblue');
                SPREADSHEET.setStyle(`${cell}9`, 'background-color', 'deepskyblue');
                SPREADSHEET.setStyle(`${cell}10`, 'background-color', 'deepskyblue');
                SPREADSHEET.setStyle(`${cell}11`, 'background-color', 'deepskyblue');
                SPREADSHEET.setStyle(`${cell}12`, 'background-color', 'deepskyblue');
                SPREADSHEET.setStyle(`${cell}13`, 'background-color', 'deepskyblue');
                SPREADSHEET.setStyle(`${cell}14`, 'background-color', 'deepskyblue');
            }
        });
    })
};

const get_projects = (department_id, department_name, row_offset, col_offset) => {
    return post('get_projects/', {
        department_id: department_id,
        department_name: department_name,
        date_range: DATE_RANGE
    }).then(resp => {
        PROJECTS = [];

        resp.forEach((proj, i) => {
            proj['row'] = i + row_offset;
            let last_cell = get_cell(DATE_RANGE.length, col_offset - 1);

            // update this if new column is added
            let row = [
                proj.client__name,
                proj.name,
                proj.type__name,
                proj.status__name,
                proj.bids.toFixed(2),
                proj.actuals.toFixed(2),
                proj.variance.toFixed(2),
                `=ROUND(SUM(I${proj.row}:${last_cell}${proj.row}) + ${proj.projected}, 2)`,
            ];
            SPREADSHEET.insertRow(row);

            // update the color for variance
            if (proj.variance < 0) {
                SPREADSHEET.setStyle(`G${proj.row}`, 'color', 'red');
            }

            // update alignment
            SPREADSHEET.setStyle(`A${proj.row}`, 'text-align', 'left');
            SPREADSHEET.setStyle(`B${proj.row}`, 'text-align', 'left');
            SPREADSHEET.setStyle(`H${proj.row}`, 'border-right', '3px solid black');

            // update weekends marker
            WEEKENDS.forEach(d => {
                let cell = get_cell(DATE_RANGE.indexOf(d), col_offset);
                SPREADSHEET.setStyle(`${cell}${i + row_offset}`, 'background-color', 'lightgrey');
            });

            // update holidays
            HOLIDAYS.forEach(d => {
                // for the holidays that are not in month, we get -1, which turns everything blue.
                let index = DATE_RANGE.indexOf(datestring(d));
                if (index >= 0) {
                    let cell = get_cell(index, col_offset);
                    SPREADSHEET.setStyle(`${cell}${i + row_offset}`, 'background-color', 'deepskyblue');
                }
            });

            // // update start date marker
            // if (proj.start_date) {
            //     let index = DATE_RANGE.indexOf(datestring(proj.start_date));
            //     if (index != -1) {
            //         let cell = get_cell(index, col_offset);
            //         SPREADSHEET.setStyle(`${cell}${i + row_offset}`, 'border', '2px solid blue')
            //     }
            // }
            //
            // // update end date marker
            // if (proj.end_date) {
            //     let index = DATE_RANGE.indexOf(datestring(proj.end_date));
            //     if (index != -1) {
            //         let cell = get_cell(index, col_offset);
            //         SPREADSHEET.setStyle(`${cell}${i + row_offset}`, 'border', '2px solid red')
            //     }
            // }

            // add into global
            PROJECTS.push(proj);
        });

        // Load the Allocated Header after the projects are loaded because project length is required
        DATE_RANGE.map((d, i) => {
            let cell = get_cell(i, col_offset);
            SPREADSHEET.setValue(`${cell}13`, `=SUM(${cell}16:${cell}${resp.length + 16})`);
        });
    })
};

const get_resources = (department_id, department_name, row = null, col_offset) => {
    return post('get_resources/', {
        department_id: department_id,
        department_name: department_name,
        date_range: DATE_RANGE
    }).then(resp => {
        if (row == null) {
            PROJECTS.forEach(proj => {
                resp.filter(res => {
                    return res.project_id == proj.id
                }).forEach(res => {
                    let row = proj.row;
                    let col = DATE_RANGE.indexOf(datestring(res.date));
                    let cell = get_cell(col, col_offset);

                    if (res.projected > 0) {
                        SPREADSHEET.setValue(`${cell}${row}`, res.projected);
                    }
                })
            });
        } else {
            DATE_RANGE.forEach((date, index) => {
                let value = resp.filter(x => {
                    return datestring(x.date) == date
                }).reduce((x, y) => x + y.projected, 0);

                let cell = get_cell(index, col_offset);
                SPREADSHEET.setValue(`${cell}${row}`, value);
            })
        }
    });
};

const load_annual_projection = (tab = null) => {
    show_loading();

    // get default department
    if (tab != null) {
        if (document.querySelector('.tab.active') != null) {
            document.querySelector('.tab.active').classList.remove('active');
        }
        tab.classList.add('active');
    }

    // remove existing spreadsheet
    jexcel.destroy(document.getElementById('spreadsheet'));
    document.getElementById('spreadsheet').innerText = "";

    post('get_annual_projection/', {}).then(resp => {
        let columns = [{title: 'Department', width: 200, readOnly: true}].concat(...resp[1].map(x => {
            return {title: x, width: 50}
        }));
        let nestedHeaders = [[{title: ""}, ...resp[0].map(x => {
            return {title: x}
        })]];

        resp.shift();
        resp.shift();

        // load spreadsheet
        SPREADSHEET = jexcel(document.getElementById('spreadsheet'), {
            columns: columns,
            nestedHeaders: nestedHeaders,
            data: resp,
            allowManualInsertColumn: false,
            allowManualInsertRow: false,
            allowDeleteColumn: false,
            allowDeleteRow: false,
            allowRenameColumn: false,
            contextMenu: false,
        });

        resp.map((row, index) => {
            if (row[0].match(/Available/g)) {
                row.shift();
                row.forEach((r, i) => {
                    let cell = get_cell(i, 1);
                    if (r <= 0) {
                        SPREADSHEET.setStyle(`${cell}${index + 1}`, 'backgroundColor', 'greenyellow');
                        SPREADSHEET.setStyle(`${cell}${index + 1}`, 'color', 'black');
                    } else {
                        SPREADSHEET.setStyle(`${cell}${index + 1}`, 'backgroundColor', 'red');
                        SPREADSHEET.setStyle(`${cell}${index + 1}`, 'color', 'white');
                    }
                })
            }
        });

        hide_loading();
    })
};

const load_annual_charts = (tab = null) => {
    show_loading();

    // get default department
    if (tab != null) {
        if (document.querySelector('.tab.active') != null) {
            document.querySelector('.tab.active').classList.remove('active');
        }
        tab.classList.add('active');
    }

    // remove existing spreadsheet
    jexcel.destroy(document.getElementById('spreadsheet'));
    document.getElementById('spreadsheet').innerText = "";

    post('get_annual_charts/', {}).then(resp => {
        for (let key in resp.data) {
            let data = resp.data[key];
            let chart = createElements(el('canvas', {'height': '100px', 'style': 'margin-bottom: 4em'}, ''));

            let projects = [];
            for (let key in data.projects) {
                let project = data.projects[key];
                projects.push({
                    label: project.label,
                    backgroundColor: random_color(),
                    data: project.data,
                    stack: 3
                })
            }

            document.getElementById('spreadsheet').append(chart);

            new Chart(chart, {
                type: 'bar',
                data: {
                    labels: resp.labels,
                    datasets: [
                        {
                            label: "Man-days",
                            backgroundColor: data.mandays.backgroundColor,
                            data: data.mandays.data,
                            stack: 1
                        },
                        {
                            label: "Allocated",
                            backgroundColor: data.allocated.backgroundColor,
                            data: data.allocated.data,
                            stack: 2
                        },
                        {
                            label: "Available",
                            backgroundColor: data.available.backgroundColor,
                            data: data.available.data,
                            stack: 2
                        },
                        ...projects
                    ]
                },
                options: {
                    digikore: {
                        display: true,
                        position: 'bottom',
                    },
                    title: {
                        display: true,
                        text: `${key} Resources`,
                        fontSize: 20
                    },
                    scales: {
                        xAxes: [{
                            barPercentage: 1,
                            barThickness: 8,
                            stacked: true,
                        }],
                        yAxes: [{
                            stacked: true,
                        }]
                    }
                }
            });
        }

        hide_loading();
    })
};

const load_data = async (tab = null, col_offset = 8) => {
    INITIALIZED = false;
    get_date_range();

    let department_id;
    let department_name;
    // get default department
    if (tab == null) {
        department_id = document.querySelector('.tab.active').dataset['tab'];
        department_name = document.querySelector('.tab.active').dataset['name'];
    } else {
        department_id = tab.dataset['tab'];
        department_name = tab.dataset['name'];
        if (document.querySelector('.tab.active') != null) {
            document.querySelector('.tab.active').classList.remove('active');
        }
        tab.classList.add('active');
    }

    // remove existing spreadsheet
    jexcel.destroy(document.getElementById('spreadsheet'));
    document.getElementById('spreadsheet').innerText = "";

    // load headers
    let columns = DATE_RANGE.map((d, i) => {
        return {title: i + 1, width: 35}
    });

    let column_headers = DATE_RANGE_HEADERS.map((d, i) => {
        return {title: d, width: 35}
    });

    // get selected month
    let month = document.getElementById('select__month').value;

    // clear other departments
    OTHER_DEPARTMENTS = DEPARTMENTS.filter(dept => {
        return dept.id != department_id
    });

    // load spreadsheet
    SPREADSHEET = jexcel(document.getElementById('spreadsheet'), {
        columns: [
            {width: 150, readOnly: true},
            {width: 100, readOnly: true},
            {width: 100, readOnly: true},
            {width: 100, readOnly: true},
            {width: 70, readOnly: true},
            {width: 70, readOnly: true},
            {width: 70, readOnly: true},
            {width: 70, readOnly: true},
            ...columns
        ],
        nestedHeaders: [
            [
                {title: '', colspan: col_offset},
                ...column_headers
            ],
        ],
        data: [
            ['Headcount'],
            ['Working Hours'],
            [`Total borrowed resources`],
            ...OTHER_DEPARTMENTS.map(dept => {
                return [`Resources lend to ${dept['name']}`]
            }),
            ['Leaves'],
            ['Absents'],
            ['Allocated'],
            ['Available'],
            ['Client', 'Project', 'Type', 'Status', 'Bids', 'Actuals', 'Variance', 'Allocated']
        ],
        mergeCells: {
            A1: [col_offset, 1],
            A2: [col_offset, 1],
            A3: [col_offset, 1],
            A4: [col_offset, 1],
            A5: [col_offset, 1],
            A6: [col_offset, 1],
            A7: [col_offset, 1],
            A8: [col_offset, 1],
            A9: [col_offset, 1],
            A10: [col_offset, 1],
            A11: [col_offset, 1],
            A12: [col_offset, 1],
            A13: [col_offset, 1],
            A14: [col_offset, 1],
        },
        style: {
            A1: 'font-weight: bold; text-align: right; border-right: 3px solid black',
            A2: 'font-weight: bold; text-align: right; border-right: 3px solid black',
            A3: 'font-weight: bold; text-align: right; border-right: 3px solid black',
            A4: 'font-weight: bold; text-align: right; border-right: 3px solid black',
            A5: 'font-weight: bold; text-align: right; border-right: 3px solid black',
            A6: 'font-weight: bold; text-align: right; border-right: 3px solid black',
            A7: 'font-weight: bold; text-align: right; border-right: 3px solid black',
            A8: 'font-weight: bold; text-align: right; border-right: 3px solid black',
            A9: 'font-weight: bold; text-align: right; border-right: 3px solid black',
            A10: 'font-weight: bold; text-align: right; border-right: 3px solid black',
            A11: 'font-weight: bold; text-align: right; border-right: 3px solid black',
            A12: 'font-weight: bold; text-align: right; border-right: 3px solid black',
            A13: 'font-weight: bold; text-align: right; border-right: 3px solid black',
            A14: 'font-weight: bold; text-align: right; border-right: 3px solid black; border-bottom: 3px solid black;',
            A15: 'font-weight: bold; background-color: lightgrey; text-align: left',
            B15: 'font-weight: bold; background-color: lightgrey; text-align: left',
            C15: 'font-weight: bold; background-color: lightgrey',
            D15: 'font-weight: bold; background-color: lightgrey',
            E15: 'font-weight: bold; background-color: dimgrey; color: white',
            F15: 'font-weight: bold; background-color: dimgrey; color: white',
            G15: 'font-weight: bold; background-color: dimgrey; color: white',
            H15: 'font-weight: bold; background-color: lightgrey;border-right: 3px solid black',
        },
        allowManualInsertColumn: false,
        allowManualInsertRow: false,
        allowDeleteColumn: false,
        allowDeleteRow: false,
        allowRenameColumn: false,
        contextMenu: false,
        csvFileName: `${department_name}_${month}`,
        onchange: (instance, cell, x, y, value) => {
            // y and x 0 = 1, the index starts from 0
            if (SPREADSHEET != undefined) {

                // update the Available header
                if (y == 13) {
                    if (value == 0) {
                        cell.style.backgroundColor = '#555';
                        cell.style.color = 'white'
                    } else if (value > 0) {
                        cell.style.backgroundColor = 'greenyellow';
                        cell.style.color = 'black'
                    } else if (value < 0) {
                        cell.style.backgroundColor = 'red';
                        cell.style.color = 'white'
                    }
                }

                if (INITIALIZED) {
                    // update the working hours
                    if (y == 1 && x >= col_offset) {
                        let date = DATE_RANGE[x - col_offset];
                        let working_hours = parseInt(value);

                        if (!isNaN(working_hours)) {
                            post('update_working_hours/', {
                                department_id: department_id,
                                date: date,
                                working_hours: working_hours || 0
                            })
                        }
                    }


                    // when the "Resource lend to" is updated
                    if (y >= 3 && y <= 9 && x >= col_offset) {
                        let date = DATE_RANGE[x - col_offset];
                        let count = parseFloat(value);

                        if (!isNaN(count)) {
                            post('add_resource_share/', {
                                from_department_id: department_id,
                                to_department_id: OTHER_DEPARTMENTS[y - 3]['id'],
                                date: date,
                                count: count || 0,
                            })
                        }
                    }

                    // when the bids are updated
                    if (y >= 15 && x >= col_offset) {
                        let project = SPREADSHEET.getValueFromCoords(1, y);
                        let date = DATE_RANGE[x - col_offset];

                        if (project != "") {
                            post('add_resources/', {
                                department_id: department_id,
                                department_name: department_name,
                                project: project,
                                date: date,
                                value: value
                            })
                        } else {
                            console.log(cell)
                        }
                    }
                }
            }
        },
    });

    let today = datestring(new Date());

    // set the available formula
    DATE_RANGE.map((d, i) => {
        let cell = get_cell(i, col_offset);
        // following cell-7 is the row-7 not column 7
        // THIS IS IMPORTANT
        SPREADSHEET.setValue(`${cell}14`, `=((${cell}1 + ${cell}3 - SUM(${cell}4:${cell}12)) * (${cell}2/8)) - ${cell}13`);

        if (d == today) {
            SPREADSHEET.setStyle(`${cell}15`, 'background-color', 'orange')
        } else {
            SPREADSHEET.setStyle(`${cell}15`, 'background-color', 'lightgrey');
        }

        SPREADSHEET.setStyle(`${cell}14`, 'border-bottom', '3px solid black')
    });

    // update weekends
    WEEKENDS.map(d => {
        let cell = get_cell(DATE_RANGE.indexOf(d), col_offset);
        SPREADSHEET.setStyle(`${cell}1`, 'background-color', 'lightgrey');
        SPREADSHEET.setStyle(`${cell}2`, 'background-color', 'lightgrey');
        SPREADSHEET.setStyle(`${cell}3`, 'background-color', 'lightgrey');
        SPREADSHEET.setStyle(`${cell}4`, 'background-color', 'lightgrey');
        SPREADSHEET.setStyle(`${cell}5`, 'background-color', 'lightgrey');
        SPREADSHEET.setStyle(`${cell}6`, 'background-color', 'lightgrey');
        SPREADSHEET.setStyle(`${cell}7`, 'background-color', 'lightgrey');
        SPREADSHEET.setStyle(`${cell}8`, 'background-color', 'lightgrey');
        SPREADSHEET.setStyle(`${cell}9`, 'background-color', 'lightgrey');
        SPREADSHEET.setStyle(`${cell}10`, 'background-color', 'lightgrey');
        SPREADSHEET.setStyle(`${cell}11`, 'background-color', 'lightgrey');
        SPREADSHEET.setStyle(`${cell}12`, 'background-color', 'lightgrey');
        SPREADSHEET.setStyle(`${cell}13`, 'background-color', 'lightgrey');
        SPREADSHEET.setStyle(`${cell}14`, 'background-color', 'lightgrey');
    });

    // get data
    get_headcount(department_id, 1, col_offset);
    get_working_hours(department_id, 2, col_offset);
    get_resource_share(department_id, 3, col_offset);
    get_leaves(department_id, 11, col_offset);
    get_absents(department_id, 12, col_offset);

    await get_holidays(col_offset);
    await get_projects(department_id, department_name, 16, col_offset);
    await get_resources(department_id, department_name, null, col_offset);

    INITIALIZED = true;
};

const download_sheet = () => {
    if (document.querySelector('.tab.active').innerText == "All Departments") {
        location.href = "download_as_csv/";
    } else {
        SPREADSHEET.download();
    }
};

window.onload = async () => {
    show_loading();
    await init();

    let today = new Date();
    let select__month = document.getElementById('select__month');
    select__month.value = `${today.getFullYear()}-${(today.getMonth() + 1).toString().padStart(2, "0")}`;

    // get all departments
    await get_departments();

    // set title
    document.title = '';
    hide_loading()
};