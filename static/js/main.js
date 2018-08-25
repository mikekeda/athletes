$(document).ready( function () {
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
        ]
    });

    $('#athletes-table_filter input').unbind().bind('keyup', function(e) {
        if (e.keyCode == 13) {
            table.search( this.value ).draw();
        }
    });

    $('#athletes-table_wrapper select').material_select();
});
