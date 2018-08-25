$(document).ready( function () {
    var months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ];

    $(".button-collapse").sideNav();

    var table = $('#athletes-table').DataTable({
        serverSide: true,
        ajax: {
            url: '/api/athletes',
            dataSrc: 'data'
        },
        columns: [
            { "data": "name" },
            { "data": "nationality_and_domestic_market" },
            { "data": "age" },
            { "data": "gender" },
            { "data": "location_market" },
            { "data": "team" },
            { "data": "category" },
            { "data": "marketability" },
            { "data": "optimal_campaign_time" },
            { "data": "market_transfer" },
            { "data": "instagram" },
            { "data": "twiter" },
        ],
        columnDefs: [
            {
                "render": function ( data, type, row ) {
                    return '<i class="material-icons dp48 tiny orange-text lighten-3-text">star</i>'.repeat(parseInt(data));
                },
                "targets": 7
            },
            {
                "render": function ( data, type, row ) {
                    return months[data - 1];
                },
                "targets": 8
            },
        ]
    });

    $('#athletes-table_filter input').unbind().bind('keyup', function(e) {
        if (e.keyCode == 13) {
            table.search( this.value ).draw();
        }
    });

    $('#athletes-table_wrapper select').material_select();
});
