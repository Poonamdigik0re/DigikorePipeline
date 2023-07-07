const get_project_data = () => {
    return post('get_project_data/', {}).then(resp => {
        let project_charts = document.getElementById('project_overview_charts');
        let project_tables = document.getElementById('project_overview_tables');

        project_tables.innerText = '';

        resp.data.forEach(dept => {
            let chart = createElements(
                el('div', {'class': 'wp40 h40 p10 inline-block'},
                    el('canvas', {'id': `project_overview_${dept.name}`}, '')
                )
            );
            project_charts.append(chart);
        });

        resp.data.forEach(dept => {
            new Chart(document.getElementById(`project_overview_${dept.name}`), {
                type: 'pie',
                options: {
                    digikore: {
                        position: 'right',
                    },
                    title: {
                        fontSize: 16,
                        display: true,
                        text: dept.name.toUpperCase()
                    },
                },
                data: {
                    labels: dept.data.labels,
                    datasets: [{
                        label: dept.name,
                        data: dept.data.data,
                        backgroundColor: dept.data.backgroundColor
                    }]
                }
            });
        });

        for (let key in resp.tables) {
            let values = resp.tables[key];
            let table = createElements(
                el('div', {'class': 'p10'},
                    el('table', {'class': 'table small-line-height hover fixed'},
                        el('thead', {},
                            el('tr', {},
                                el('th', {}, key.toUpperCase()),
                                el('th', {}, 'Frames'),
                                el('th', {}, 'MM:SS +Frames'),
                                el('th', {}, 'Count')
                            )
                        ),
                        el('tbody', {}, '')
                    )
                )
            );

            let totals = {'frames': 0, 'count': 0};

            for (let task_status in values) {
                let v = values[task_status];
                let sec = frames_to_seconds(v.frames);
                let row = createElements(
                    el('tr', {},
                        el('td', {}, task_status),
                        el('td', {}, v.frames),
                        el('td', {}, `${sec[0]} : ${sec[1]} +${sec[2]}`),
                        el('td', {}, v.count)
                    )
                );
                table.querySelector('tbody').append(row);

                totals['frames'] += v.frames;
                totals['count'] += v.count;
            }

            // totals row
            let total_sec = frames_to_seconds(totals['frames']);
            let row = createElements(
                el('tr', {},
                    el('th', {}, 'Totals'),
                    el('th', {}, totals['frames']),
                    el('th', {}, `${total_sec[0]} : ${total_sec[1]} +${total_sec[2]}`),
                    el('th', {}, totals['count'])
                )
            );
            table.querySelector('tbody').append(row);

            project_tables.append(table);
        }
    })
};

window.onload = async () => {
    await init('Project Overview');
    await get_project_data();

    hide_loading()
};
