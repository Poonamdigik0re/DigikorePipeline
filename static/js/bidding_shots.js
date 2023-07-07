let SPREADSHEET;
let TASK_TYPES = [];

const get_defaults = () => {
    return post('get_defaults/', {}).then(resp => {
        TASK_TYPES = resp.task_types;
    })
};


const get_bidshots = () => {
    return post('get_bidshots/', {}).then(resp => {
        // destroy the previous spreadsheet;
        jexcel.destroy(document.getElementById('spreadsheet'));

        let columns = [
            {title: 'ID', width: 40, readOnly: true},
            {title: 'Awarded', width: 100, type: 'checkbox'},
            {title: 'Sequence', width: 100},
            {title: 'Shot', width: 100},
            {title: 'Task', width: 150},
            {title: 'Type', width: 100, type: 'dropdown', source: TASK_TYPES},
            {title: 'Bids', width: 100, type: 'numeric'},
            {
                title: 'Client ETA',
                width: 100,
                type: 'calendar',
                options: {format: 'YYYY-MM-DD', time: 0}
            },
            {
                title: 'Internal ETA',
                width: 100,
                type: 'calendar',
                format: 'YYYY-MM-DD',
                options: {format: 'YYYY-MM-DD', time: 0}
            },
            {title: 'First Frame', width: 100, type: 'numeric'},
            {title: 'Last Frame', width: 100, type: 'numeric'},
            {title: 'Plate Ver', width: 200, type: 'numeric'},
            {title: 'Task Description', width: 500},
            {title: 'Supervisor Note', width: 500},
        ];

        // create a blank list if resp is empty
        if (resp.length == 0) resp = [[]];

        SPREADSHEET = jexcel(document.getElementById('spreadsheet'), {
            data: resp,
            columns: columns
        })
    });
};

const save_bidshots = () => {
    show_loading();
    let data = SPREADSHEET.getData();

    post('save_bidshots/', {data: data}).then(resp => {
        hide_loading();
        get_bidshots();
    })
};

window.onload = async () => {
    await init('Bidding Shots');
    await get_defaults();
    await get_bidshots();

    hide_loading();
};
