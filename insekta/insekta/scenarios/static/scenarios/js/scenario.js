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


    /*
     * Scenario notes
     */
    var scenarioNotesContainer = $('#scenario-notes-container');
    var notesTextarea = scenarioNotesContainer.find('textarea');

    $('#scenario-notes-link').on('click', function() {
        scenarioNotesContainer.toggle().center();
    });
    var saveNotes = debounce(function() {
        var notes = notesTextarea.val();
        $.post(NOTES_SAVE_URL, {'notes': notes}, function() {
            scenarioNotesContainer.find('.scenario-notes-saved').show();
        });
    }, 500);
    scenarioNotesContainer.find('.close').on('click', function() {
        scenarioNotesContainer.hide();
    });
    notesTextarea.on('keyup', debounce(function() {
        scenarioNotesContainer.find('.scenario-notes-saved').hide();
        saveNotes();
    }));
    $(window).on('scroll resize', debounce(function() {
        scenarioNotesContainer.center();
    }));


    /*
     * Comments to paragraphs
     */
    var commentsState = {'enabled': false};

    function showComments() {
        $('*[data-comment-id]').each(function() {
            var hash = $(this).data('comment-id');
            var numComments = NUM_USER_COMMENTS[hash];
            if (typeof(numComments) == 'undefined') {
                numComments = 0;
            }
            var commentIcon = $('<a><span class="glyphicon glyphicon-comment"></span></a>');
            commentIcon.prepend(numComments + ' ');
            var commentSpan = $('<span class="comment"> </span>').prepend(commentIcon);
            $(this).prepend(commentSpan);
        });
    }

    function hideComments() {
        $('.comment').remove();
    }

    function setCommentState(enabled) {
        if (enabled) {
            commentsState.enabled = true;
            $('#scenario-comments-off').hide();
            $('#scenario-comments-on').show();
            showComments();
            $.post(SAVE_COMMENTS_STATE_URL, {'enabled': '1'});
        } else {
            commentsState.enabled = false;
            $('#scenario-comments-off').show();
            $('#scenario-comments-on').hide();
            hideComments();
            $.post(SAVE_COMMENTS_STATE_URL, {'enabled': '0'});
        }
    }

    function toggleComments() {
        setCommentState(!commentsState.enabled);
    }

    setCommentState(USER_COMMENTS_ENABLED);

    $('#scenario-comments-link').click(toggleComments);
});
