const get_projects = () => {
    return post('get_projects/', {}).then(resp => {
        let projects = document.getElementById('projects');
        projects.innerText = "";

        resp.forEach(proj => {
            let row = createElements(el('tr', {},
                el('td', {}, proj.name),
                el('td', {}, proj.status__name),
                el('td', {}, local_datetime(proj.archive_ready_on)),
                el('td', {}, local_datetime(proj.archive_started_on)),
                el('td', {}, proj.archive_started_by__userprofile__full_name || '-'),
                el('td', {}, local_datetime(proj.archive_completed_on)),
                el('td', {}, file_size(proj.archive_size)),
                el('td', {'class': 'align-center'},
                    el('button', {
                        'class': 'start_archival block',
                        'style': 'background-color: #2ecc71'
                    }, 'Start Archival')
                )
            ));

            if (proj.status__name != 'Ready for Archival') {
                row.querySelector('button').style = 'background-color: #ddd; color: #aaa';

            } else {
                row.querySelector('button').onclick = () => {
                    if (confirm("Please confirm that you want to start the archival process for this project.")) {
                        show_loading();
                        post('start_archival/', {project_id: proj.id}).then(resp => {
                            get_projects();
                        })
                    }
                }
            }

            projects.append(row);
        })
    })
};

window.onload = async () => {
    show_loading();
    await init();

    await get_projects();

    // set title
    document.title = '';
    hide_loading()
};