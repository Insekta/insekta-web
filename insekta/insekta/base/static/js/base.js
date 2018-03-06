(function() {
    // Code from https://docs.djangoproject.com/en/1.9/ref/csrf/#ajax

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    var csrftoken = getCookie('csrftoken');

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

})();

// Taken from Underscore.js
// Copyright (c) 2009-2016 Jeremy Ashkenas, DocumentCloud and Investigative
// Reporters & Editors
// MIT License, see https://github.com/jashkenas/underscore/blob/master/LICENSE
function debounce(func, wait, immediate) {
    var timeout;
    return function() {
        var context = this, args = arguments;
        var later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        var callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

var htmlReplacements = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;'
};

function escapeHtml(s) {
    return s.replace(/[&<>"]/g, function (m) {
        return entityMap[m];
    });
}

// Simple JavaScript Templating
// John Resig - http://ejohn.org/ - MIT Licensed
// modified to use [% %] instead of <% %>,  check for [% instead of \W for element-id or string template
/*
 * Use it like:
 * <script type="text/html" id="users_template">
 *    [[ for (var i = 0; i < users.length; i++) { ]]
 *        <a href="[[=users[i].urk]]">[[=escapeHtml(users[i].name)]]<a/>
 *    [[ } ]]
 * </script>
 * tmpl('users_template', {'users': [...]})
 */
(function () {
    var cache = {};

    this.tmpl = function tmpl(str, data) {
        // Figure out if we're getting a template, or if we need to
        // load the template - and be sure to cache the result.
        var fn = !/\[%/.test(str) ?
            cache[str] = cache[str] ||
                tmpl(document.getElementById(str).innerHTML) :

            // Generate a reusable function that will serve as a template
            // generator (and which will be cached).
            new Function("obj",
                "var p=[],print=function(){p.push.apply(p,arguments);};" +

                    // Introduce the data as local variables using with(){}
                "with(obj){p.push('" +

                    // Convert the template into pure JavaScript
                str
                    .replace(/[\r\t\n]/g, " ")
                    .split("[%").join("\t")
                    .replace(/((^|%\])[^\t]*)'/g, "$1\r")
                    .replace(/\t=(.*?)%\]/g, "',$1,'")
                    .split("\t").join("');")
                    .split("%]").join("p.push('")
                    .split("\r").join("\\'")
                + "');}return p.join('');");

        // Provide some basic currying to the user
        return data ? fn(data) : fn;
    };
})();

jQuery.fn.center = function () {
    var jWindow = $(window);
    var topValue = Math.max(0, (jWindow.height() - this.outerHeight()) / 2 + jWindow.scrollTop());
    var leftValue = Math.max(0, (jWindow.width() - this.outerWidth()) / 2 + jWindow.scrollLeft());
    this.css('position', 'absolute')
        .css('top', topValue + 'px')
        .css('left', leftValue + 'px');
    return this;
};
