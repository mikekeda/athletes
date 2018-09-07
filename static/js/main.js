$(document).ready( function () {
    let table = $('#athletes-table').DataTable({
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
            { "data": "market_export" },
            { "data": "instagram" },
            { "data": "twiter" },
        ],
        columnDefs: [
            {
                "render": function ( data, type, row ) {
                    return '<i class="material-icons dp48 tiny text-warning">star</i>'.repeat(parseInt(data));
                },
                "targets": 7
            },
            {
                "render": function ( data, type, row ) {
                    return data ? '<i class="material-icons dp48 text-success">check</i>' : '';
                },
                "targets": 9
            },
        ],
        language: {
            "lengthMenu": "Show _MENU_ athletes per page",
            "zeroRecords": "No matching athletes found",
            "info": "Showing _START_ to _END_ of _TOTAL_ athletes",
            "infoEmpty": "No athletes available",
            "infoFiltered": "(filtered from _MAX_ total athletes)"
        }
    });

    $('#athletes-table_filter input').unbind().bind('keyup', function(e) {
        if (e.keyCode === 13) {
            table.search( this.value ).draw();
        }
    });

    // Apply the search.
    table.columns().every( function () {
        let that = this;

        $('input', this.footer()).on('keyup change', function (e) {
            if (e.keyCode === 13 && that.search() !== this.value) {
                that.search(this.value).draw();
            }
        });

        $('select', this.footer()).on('change', function () {
            let val = $(this).val();

            if (that.search() !== val) {
                that.search(val).draw();
            }
        });
    });

    $('form select').select2();

});
