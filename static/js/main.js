$(document).ready( function () {
    let $athletes_table = $('table#athletes-table');
    let $athletes_lists = $('#athletes_lists');
    let $add_athletes_to_list = $('#add_athletes_to_list');
    let $athletes_export_link = $('a#athletes-export-link');
    let $athletes_list_form = $('#add-athletes-list form');
    let $athletes_lists_form = $('.athlete-page #athletes_lists_form');
    let $teams_lists_form = $('.team-page #teams_lists_form');
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
                    return '<i class="flag flag-' + row._domestic_market.toLowerCase() + '"></i> ' + data;
                },
                "targets": 2
            },
            {
                "render": function ( data, type, row ) {
                    return '<a href="/country/' + row._location_market + '"><i class="flag flag-' + row._location_market.toLowerCase() + '"></i> ' + data + '</a>';
                },
                "targets": 5
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
                    return data ? '<spam class="text-success h3">✓</spam>' : '';
                },
                "targets": 10
            },
            {
                "render": function ( data, type, row ) {
                    return data ? data.toLocaleString() : '';
                },
                "targets": 12
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

    $('form select, .select2').select2();

    $('[data-toggle="tooltip"]').tooltip({ boundary: 'window' });

    $athletes_lists.change(function() {
        table.ajax.reload();
    });

    $add_athletes_to_list.change(function() {
        if ($add_athletes_to_list.val() === '') {
            return false;
        }

        ids = [];
        $athletes_table.find('.athlete-checkbox:checked').each(function () {
            ids.push(this.getAttribute("data-id"));
        });

        $.ajax({
            url: '/athletes_list',
            type: 'PUT',
            beforeSend: function(xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $add_athletes_to_list.data('csrf_token'));
            },
            data: {
                athletes_ids: ids,
                list_id: $add_athletes_to_list.val()
            },
            dataType: 'json',
        });

        $add_athletes_to_list.val('');

        alert("Added");
    });

    $athletes_table.on('change', '.athlete-checkbox', function() {
        ids = '';

        $athletes_table.find('.athlete-checkbox:checked').each(function () {
            ids += ',' + this.getAttribute("data-id");
        });
        ids = ids.substr(1);

        $athletes_export_link.attr("href", $athletes_export_link.data('href') + ids);
        $athletes_list_form.find('#id_athletes').val(ids);
    });

    $athletes_list_form.submit(function (event) {
        event.preventDefault();

        $.ajax({
            url: '/athletes_list',
            type: 'POST',
            data: $athletes_list_form.serialize(),
            dataType: 'json',
            success: function (data, textStatus, jqXHR) {
                $athletes_lists.find('option:first').after($('<option>', {value: data.id, text: data.name}));
                $athletes_list_form.parents('#add-athletes-list').modal('hide');
            }
        });
    });

    $athletes_lists_form.change(function (event) {
        event.preventDefault();

        $.ajax({
            url: $athletes_lists_form.attr('action'),
            type: 'POST',
            data: $athletes_lists_form.serialize(),
            dataType: 'json'
        });
    });

    $teams_lists_form.change(function (event) {
        event.preventDefault();

        $.ajax({
            url: $teams_lists_form.attr('action'),
            type: 'POST',
            data: $teams_lists_form.serialize(),
            dataType: 'json'
        });
    });

});
