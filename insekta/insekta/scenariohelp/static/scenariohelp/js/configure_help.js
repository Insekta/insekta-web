$(function() {
    function changeSupport(ev) {
        var checkbox = $(this);
        var label = checkbox.parent();
        $.post(SET_SUPPORT_URL, {
            'scenario': checkbox.attr('name'),
            'enabled': checkbox.prop('checked') ? '1' : '0'
        });
    }

    $('#chosen-scenarios').find('input[type="checkbox"]').each(function() {
        $(this).on('change', changeSupport);
    })
});