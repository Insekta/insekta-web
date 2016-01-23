$(function() {
    function changeSupport(ev) {
        var checkbox = $(this);
        $.post(SET_SUPPORT_URL, {
            'scenario': checkbox.attr('name'),
            'enabled': checkbox.prop('checked') ? '1' : '0'
        });
    }

    $('#chosen-scenarios input[type="checkbox"]').each(function() {
        $(this).on('change', changeSupport);
    });
});