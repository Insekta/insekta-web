$(function() {
    function runAutoMath() {
        MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
    }
    window.runAutoMath = runAutoMath;
});
