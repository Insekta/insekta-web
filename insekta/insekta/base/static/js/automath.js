$(function() {
    var mathOpts = {
        'delimiters': [
            {left: "\\[", right: "\\]", display: true},
            {left: "\\(", right: "\\)", display: false}
        ]
    };
    $('.auto-math').each(function() {
        renderMathInElement(this, mathOpts);
    })
});
