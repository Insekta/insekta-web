$(function() {
    /*
     * Show hints if their buttons are clicked
     */
    $('.hint-form').each(function() {
        $(this).submit(function(ev) {
            $(this).find('.hint-button').hide();
            $(this).find('.hint-content').show();
            ev.stopPropagation();
            return false;
        });
    });


    /*
     * Ping to avoid virtual machines being destroyed
     */
    if (PING_URL !== null) {
        setInterval(function() {
            $.post(PING_URL, function(expire_time) {
                $('#expire_time').text(expire_time)
            })
        }, 60*1000);
    }


    /*
     * Progress gears on starting/destroying virtual machines
     */
    $('#vm-panel').find('form').submit(function() {
        $('#vm-panel').hide();
        $('#vm-panel-gears').show();
        return true;
    });

    /*
     * Scenario Bar
     */
    var scenarioBar = $('#scenario-bar');
    var scenarioBarContainer = $('#scenario-bar-container');
    scenarioBarContainer.css('height', scenarioBar.outerHeight(true));
    var scenarioBarOffset = scenarioBar.offset();
    $(document).on('scroll', debounce(function(ev) {
        if ($(document).scrollTop() > scenarioBarOffset.top) {
            scenarioBar.removeClass('scenario-bar-absolute');
            scenarioBar.addClass('scenario-bar-fixed');
        } else {
            scenarioBar.removeClass('scenario-bar-fixed');
            scenarioBar.addClass('scenario-bar-absolute');
        }
    }));

    function fixScenarioBarWidth() {
        scenarioBar.css('width', scenarioBarContainer.width());
    }
    fixScenarioBarWidth();
    $(window).on('resize', fixScenarioBarWidth);
});