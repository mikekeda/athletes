$(document).ready( function () {
    $('#athletes-table').DataTable({
        ajax: {
            url: '/api/athletes',
            dataSrc: ''
        },
        columns: [
            { "data": "Column 1" },
            { "data": "Column 2" },
        ]
    });
});
