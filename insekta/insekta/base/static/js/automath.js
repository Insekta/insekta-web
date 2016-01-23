$(function() {
    var mathOpts = {
        'delimiters': [
            {left: "\\[", right: "\\]", display: true},
            {left: "\\(", right: "\\)", display: false}
        ]
    };

    function runAutoMath() {
        $('.auto-math').each(function () {
            renderMathInElement(this, mathOpts);
        });
    }
    window.runAutoMath = runAutoMath;

    runAutoMath()
});
