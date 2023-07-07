function post(url, args) {
    fetch(url, args).then(response => {
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
    })
}

function play() {
    rvsession.evaluate('play()')
}

function stop() {
    rvsession.evaluate('stop()');
}


function get_projects() {
    let project_list = document.getElementById('project_list');
    project_list.innerText = "";
    post('get_projects/', {}).then(resp => {
        let project_list = document.getElementById('project_list');
        project_list.innerText = resp;
    })
}