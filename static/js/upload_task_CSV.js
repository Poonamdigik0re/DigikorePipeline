function updateData() {
    var table = document.getElementById('editable-table');
    var rows = table.getElementsByTagName('tr');
    var data = [];

    for (var i = 0; i < rows.length; i++) {
        var row = rows[i];
        var cells = row.getElementsByTagName('td');
        var rowData = [];

        for (var j = 0; j < cells.length; j++) {
            var cellValue = cells[j].innerText.trim();
            rowData.push(cellValue);
        }

        data.push(rowData);
    }

    var headerRow = data[0];
    var dataWithoutHeader = data.slice(1);
    var formattedData = [headerRow.map(cell => cell.replace(/^"|"$/g, ''))].concat(dataWithoutHeader.map(row => row.map(cell => cell.replace(/^"|"$/g, '')))).join('\n').trim();

    // Make a POST request to the update URL with the updated data
    fetch('/task_list/upload_task/update_csv/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': '{{ csrf_token }}',
        },
        body: 'data[]=' + encodeURIComponent(formattedData),
    })
    .then(response => {
        if (response.ok) {
        alert('CSV uploaded successfully!');
            // Redirect to the original page after successful update
            window.location.href = '/upload_task/';

        } else {
            console.error('Update request failed.');
        }
    })
    .catch(error => {
        console.error('Update request failed:', error);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    var updateButton = document.getElementById('update-button');
    updateButton.addEventListener('click', function(event) {
        event.preventDefault();
        updateData();
    });
});

window.onload = async () => {-
    await init('upload task CSV');
    if (has_permission('upload_task_CSV')) {
    }

    hide_loading()

};
