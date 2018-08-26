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
            { "data": "domestic_market" },
            { "data": "age" },
            { "data": "gender" },
            { "data": "location_market" },
            { "data": "team" },
            { "data": "category" },
            { "data": "marketability" },
            { "data": "optimal_campaign" },
            { "data": "market_transfer" },
            { "data": "instagram" },
            { "data": "twiter" },
        ],
        columnDefs: [
            {
                "width": "210px",
                "targets": 6
            },
            {
                "render": function ( data, type, row ) {
                    return '<i class="material-icons dp48 tiny orange-text">star</i>'.repeat(parseInt(data));
                },
                "width": "140px",
                "targets": 7
            },
            {
                "width": "150px",
                "targets": 8
            },
            {
                "render": function ( data, type, row ) {
                    return data ? '<i class="material-icons dp48 green-text">check</i>' : '';
                },
                "targets": 9
            },
        ]
    });

    $('#athletes-table_filter input').unbind().bind('keyup', function(e) {
        if (e.keyCode == 13) {
            table.search( this.value ).draw();
        }
    });

    // Apply the search
    table.columns().every( function () {
        var that = this;

        $('input', this.footer()).on('keyup change', function (e) {
            if (e.keyCode == 13 && that.search() !== this.value) {
                that.search(this.value).draw();
            }
        });

        $('select', this.footer()).on('change', function () {
            var val = $(this).val();

            if (that.search() !== val) {
                that.search(val).draw();
            }
        });
    });

    $('#athletes-table_wrapper select').material_select();
});
