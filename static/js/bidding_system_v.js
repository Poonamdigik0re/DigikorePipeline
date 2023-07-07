window.onload = async () => {
    // set title
    document.title = 'Bidding System';
    show_loading();
    await init();
    // start callbacks


    // end callbacks
    hide_loading()
};