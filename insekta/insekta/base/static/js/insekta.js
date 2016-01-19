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

jQuery.fn.center = function () {
    var jWindow = $(window);
    var topValue = Math.max(0, (jWindow.height() - this.outerHeight()) / 2 + jWindow.scrollTop());
    var leftValue = Math.max(0, (jWindow.width() - this.outerWidth()) / 2 + jWindow.scrollLeft());
    this.css('position', 'absolute')
        .css('top', topValue + 'px')
        .css('left', leftValue + 'px');
    return this;
};
