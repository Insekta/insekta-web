base_static = insekta/base/static/
scenarios_static = insekta/scenarios/static/scenarios/


all: css js

css: ${base_static}css/insekta.min.css ${base_static}css/bootstrap.min.css

js: ${base_static}js/bootstrap.min.js

${base_static}css/insekta.min.css: ${base_static}css/custom.css ${scenarios_static}css/custom.css
	cat $^ | yui-compressor -o $@ --type css --charset utf-8

%.min.css: %.css
	yui-compressor -o $@ --type css --charset utf-8 $<

%.min.js: %.js
	yui-compressor -o $@ --type js --charset utf-8 $<

%.mo: %.po
	msgfmt -o $@ $<

clean:
	rm -f ${base_static}css/insekta.css \
		  ${base_static}css/insekta.min.css \
		  ${base_static}css/bootstrap.min.css
