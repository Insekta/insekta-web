function runAutoMath(element) {
    if (!window.MathJax || !MathJax.typesetPromise) {
        setTimeout(function() { runAutoMath(element); }, 100);
        return;
    }
    return MathJax.typesetPromise(element ? [element] : undefined)
        .catch(function(err) {
            console.error('MathJax typeset failed:', err);
        });
}
window.runAutoMath = runAutoMath;
