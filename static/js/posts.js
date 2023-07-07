const get_post_options = () => {
    post('get_post_options/', {}).then(resp => {
        document.getElementById('post_title').innerText = resp.title;
        resp.options.forEach(option => {
            let opt = createElements(
                el('h3', {},
                    el('label', {},
                        el('input', {'type': 'radio', 'name': 'option_id', 'value': option.id}),
                        (option.link) ? el('a', {
                            'href': option.link,
                            '_target': 'blank',
                            'class': 'hyperlink'
                        }, option.title) : option.title
                    )
                )
            );
            document.getElementById('post_options').append(opt)
        })
    });
};

const vote = (form) => {
    post('vote/', {'option_id': form.option_id.value}).then(resp=>{
        alert('Your vote has been registered');
    })
};

window.onload = async () => {
    show_loading();
    await init();

    get_post_options();

    // set title
    document.title = '';
    hide_loading()
};