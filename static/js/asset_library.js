let SLIDER;
let ASSETS = [];

class Asset {
    constructor(data) {
        this.data = data;
        this.type = 'assetgroup';
        this.element = createElements(
            el('div', {'class': 'asset-tile'},
                el('img', {
                    'src': (this.data.thumbnail.startsWith('/static/')) ? '/static/img/default_thumbnail.png' : `/media/${this.data.thumbnail}`,
                    'width': '177px',
                    'height': '100px'
                }),
                el('div', {'class': 'asset-name'}, this.data.name)
            )
        );

        // show slider
        this.element.onclick = () => {
            SLIDER.set_parent(this);
            SLIDER.element.querySelector('.parent_name').innerText = this.data.name;
            SLIDER.show();
        };
    }
}

const get_all_assets = () => {
    return post('get_all_assets/', {}).then(resp => {
        let all_assets = document.getElementById('asset_library');
        resp.forEach(data => {
            let asset = new Asset(data);
            ASSETS.push(asset);
            // append into dom
            all_assets.append(asset.element);
        });
    })
};

const apply_filters = (input) => {
    let val = input.value.toLowerCase();

    if (!val) {
        ASSETS.forEach(asset => {
            asset.element.style.display = 'block'
        })
    } else {
        ASSETS.forEach(asset => {
            if (asset.data.name.indexOf(val) !== -1) {
                asset.element.style.display = 'block'
            } else {
                asset.element.style.display = 'none'
            }
        })
    }
};

window.onload = async () => {
    await init('Asset Library');

    // import slider
    SLIDER = new Slider();
    document.getElementById('modals').append(SLIDER.element);

    await get_all_assets();
    hide_loading();
};