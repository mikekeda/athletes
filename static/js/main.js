$(document).ready( function () {
    $(".button-collapse").sideNav();

    $('#athletes-table').DataTable({
        ajax: {
            url: '/api/athletes',
            dataSrc: ''
        },
        columns: [
            { "data": "name" },
            { "data": "nationality_and_domestic_market" },
            { "data": "age" },
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
});
