let QUILL = null;

const get_upcoming_birthdays = () => {
    post('/home/get_upcoming_birthdays/', {}).then(resp => {
        let upcoming_birthdays = document.getElementById('upcoming_birthdays');

        resp.forEach(bday => {
            let resp = createElements(
                el('tr', {},
                    el('td', {}, bday.name),
                    el('td', {}, bday.day)
                )
            );
            upcoming_birthdays.append(resp);
        });
    })
};

const get_announcements = () => {
    post('/home/get_announcements/', {}).then(resp => {
        let all_announcements = document.getElementById('all_announcements');
        all_announcements.innerText = "";

        resp.forEach(data => {
            let annoucement = createElements(el('div', {'class': 'announcement'}, ''));
            annoucement.innerHTML = data.text;
            all_announcements.append(annoucement);
        });

        hide_loading();
    });
};

const add_announcement = (form) => {
    show_loading();
    let text = document.querySelector('.ql-editor').innerHTML;

    if (text != "" && form.valid_till.value != "") {
        post('/home/add_announcement/', {'text': text, 'valid_till': form.valid_till.value}).then(resp => {
            hide_modal('add_announcement');
            get_announcements();
        })
    }
};

window.onload = async () => {
    await init('Central');

    get_upcoming_birthdays();
    get_announcements();

    QUILL = new Quill("#editor-container", {
        modules: {
            toolbar: '#toolbar-container'
        },
        theme: 'snow',
        placeholder: 'Type here..'
    });

    hide_loading();
};