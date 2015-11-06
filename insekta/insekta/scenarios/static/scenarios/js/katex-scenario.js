$(function() {
    $('.math-inline').each(function() {
        katex.render($(this).text(), this, {
            'displayMode': false,
            'throwOnError': false
        });
    });
    $('.math-block').each(function() {
        katex.render($(this).text(), this, {
            'displayMode': true,
            'throwOnError': false
        });
    });
});