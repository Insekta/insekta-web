$(function() {
    $('.hint-form').each(function() {
        $(this).submit(function(ev) {
            $(this).find('.hint-button').hide();
            $(this).find('.hint-content').show();
            ev.stopPropagation();
            return false;
        });
    });

    if (PING_URL !== null) {
        setInterval(function() {
            $.post(PING_URL, function(expire_time) {
                $('#expire_time').text(expire_time)
            })
        }, 60*1000);
    }

    $('#vm-panel').find('form').submit(function() {
        $('#vm-panel').hide();
        $('#vm-panel-gears').show();
        return true;
    })
});