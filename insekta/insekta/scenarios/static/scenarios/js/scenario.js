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

    function showCommentIcons() {
        $('*[data-comment-id]').each(function() {
            var commentId = $(this).data('comment-id');
            if (commentId == '') {
                return;
            }
            var numComments = NUM_USER_COMMENTS[commentId];
            if (typeof(numComments) == 'undefined') {
                numComments = 0;
            }
            var commentIcon = $('<a><span class="glyphicon glyphicon-comment"></span></a>');
            commentIcon.prepend(numComments + ' ');
            commentIcon.on('click', (function(commentId) {
                return function(ev) {
                    $.get(GET_COMMENTS_URL, {'comment_id': commentId}, function(html) {
                        showComments(commentId, html);
                    });
                }
            })(commentId));

            var commentSpan = $('<span class="comment"> </span>').prepend(commentIcon);
            $(this).prepend(commentSpan);
        });
    }

    function hideCommentIcons() {
        $('.comment').remove();
    }

    function setCommentState(enabled) {
        if (enabled) {
            commentsState.enabled = true;
            $('#scenario-comments-off').hide();
            $('#scenario-comments-on').show();
            showCommentIcons();
            $.post(SAVE_COMMENTS_STATE_URL, {'enabled': '1'});
        } else {
            commentsState.enabled = false;
            $('#scenario-comments-off').show();
            $('#scenario-comments-on').hide();
            hideCommentIcons();
            $.post(SAVE_COMMENTS_STATE_URL, {'enabled': '0'});
        }
    }

    function toggleCommentIcons() {
        setCommentState(!commentsState.enabled);
    }

    function showComments(commentId, html) {
        var scenarioModal = $('#scenario-modal');
        var modalBody = scenarioModal.find('.modal-body');
        modalBody.empty();
        var paragraph = $('[data-comment-id="' + commentId + '"]').clone();
        paragraph.attr('data-comment-id', '').find('.comment').remove();
        var blockquote = $('<blockquote></blockquote>').append(paragraph);
        var commentDiv = $('<div></div>').html(html);
        commentDiv.find('form').on('submit', function() {
            ev.stopPropagation();
            ev.preventDefault();
            return false;
        });
        commentDiv.find('button[name="preview"]').on('click', function() {
            var comment = commentDiv.find('textarea').val();
            $.post(PREVIEW_COMMENT_URL, {'comment': comment}, function(preview) {
                commentDiv.find('#scenario-post-comment-preview').html(preview);
                runAutoMath();
            });
        });
        commentDiv.find('button[name="save"]').on('click', function() {
            var comment = commentDiv.find('textarea').val();
            if (comment.trim() == '') {
                return;
            }
            $.post(SAVE_COMMENT_URL, {
                'comment_id': commentId,
                'comment': comment
            }, function(html) {
                showComments(commentId, html);
                NUM_USER_COMMENTS[commentId]++;
                hideCommentIcons();
                showCommentIcons();
            });
        });
        modalBody.append(blockquote).append(commentDiv);
        runAutoMath();
        scenarioModal.modal();
    }

    if (!$.isEmptyObject(NUM_USER_COMMENTS)) {
        setCommentState(USER_COMMENTS_ENABLED);
        $('#scenario-comments-link').css('display', 'block').click(toggleCommentIcons);
    }
});
