$(document).ready( function () {
    let $athletes_table = $('table#athletes-table');
    let $athletes_export_link = $('a#athletes-export-link');
    let ids;
    let e;

    let table = $athletes_table.DataTable({
        serverSide: true,
        ajax: {
            url: '/api/athletes',
            dataSrc: 'data',
            data: function (d) {
                e = document.getElementById("athletes_lists");
                d.list_id = e.options[e.selectedIndex].value;
            }
        },
        columns: [
            { "data": "pk" },
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
            { "data": "twitter" },
        ],
        columnDefs: [
            {
                "render": function ( data, type, row ) {
                    return '<input type="checkbox" class="athlete-checkbox" data-id="' + data + '">';
                },
                "width": "20px",
                "targets": 0
            },
            {
                "render": function ( data, type, row ) {
                    return '<a href="/athlete/' + row.slug + '">' + data + '</a>';
                },
                "targets": 1
            },
            {
                "render": function ( data, type, row ) {
                    if (row.team_model) {
                        return '<a href="/team/' + row.team_model + '">' + data + '</a>';
                    }
                    return data;
                },
                "targets": 6
            },
            {
                "render": function ( data, type, row ) {
                    return data ? '<i class="material-icons dp48 text-success">check</i>' : '';
                },
                "targets": 10
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

    $('[data-toggle="tooltip"]').tooltip({ boundary: 'window' });

    $('#athletes_lists').change(function() {
        table.ajax.reload();
    });

    $athletes_table.on('change', '.athlete-checkbox', function() {
        ids = '';

        $athletes_table.find('.athlete-checkbox:checked').each(function () {
            ids += ',' + this.getAttribute("data-id");
        });

        $athletes_export_link.attr("href", $athletes_export_link.data('href') + ids.substr(1));
    });

});
