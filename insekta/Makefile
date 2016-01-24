.PHONY: all css js components clean watchstatic

base_static = insekta/base/static/
scenarios_static = insekta/scenarios/static/scenarios/
components_static = ${base_static}components/

jquery_download = http://code.jquery.com/jquery-2.1.4.min.js
raphaeljs_download = http://github.com/DmitryBaranovskiy/raphael/raw/master/raphael-min.js
flot_download = http://www.flotcharts.org/downloads/flot-0.8.3.zip
mathjax_download = https://github.com/mathjax/MathJax/archive/master.zip
flot_tmp := $(shell mktemp -u).zip
mathjax_tmp := $(shell mktemp -u).zip

YUI_COMPRESSOR := $(shell scripts/yuicompressor.py --find)


static_files = $(shell find \( -name '*.css' -o -name '*.js' \) -not \( -name '*.min    .js' -o -name '*.min.css' \))

all: css js components

css: ${base_static}css/insekta.min.css

js: ${base_static}js/insekta.min.js ${scenarios_static}js/scenario.min.js

components: ${components_static}mathjax ${components_static}raphaeljs ${components_static}flot

${base_static}js/jquery.min.js:
	wget -O $@ '${jquery_download}'

${scenarios_static}css/pygments.css:
	pygmentize -S default -f html -a .highlight > $@

${base_static}css/insekta.min.css: ${base_static}css/bootstrap.css ${base_static}css/custom.css ${scenarios_static}css/custom.css ${scenarios_static}css/pygments.css
	cat $^ | $(YUI_COMPRESSOR) -o $@ --type css --charset utf-8

${base_static}js/insekta.min.js: ${base_static}js/jquery.min.js ${base_static}js/bootstrap.js ${base_static}js/base.js ${base_static}js/automath.js
	cat $^ | $(YUI_COMPRESSOR) -o $@ --type js --charset utf-8

%.min.css: %.css
	$(YUI_COMPRESSOR) -o $@ --type css --charset utf-8 $<

%.min.js: %.js
	$(YUI_COMPRESSOR) -o $@ --type js --charset utf-8 $<

%.mo: %.po
	msgfmt -o $@ $<

${components_static}raphaeljs:
	mkdir -p $@
	wget -P $@ ${raphaeljs_download}

${components_static}flot:
	wget -O ${flot_tmp} '${flot_download}'
	unzip ${flot_tmp} -d $(dir $@)
	rm ${flot_tmp}

${components_static}mathjax:
	wget -O ${mathjax_tmp} '${mathjax_download}'
	unzip ${mathjax_tmp} -d $(dir $@)
	mv $(dir $@)/MathJax-master $@
	rm -rf $@/unpacked
	rm -rf $@/docs
	rm -rf $@/tests
	rm -rf $@/fonts/HTML-CSS/TeX/png
	rm -rf $@/fonts/HTML-CSS/TeX/svg
	rm ${mathjax_tmp}

testenv: testenv/scenarios testenv/vpn testenv/vpn/ca.key testenv/vpn/ca.crt

testenv/vpn:
	mkdir -p testenv/vpn

testenv/scenarios:
	mkdir -p testenv/scenarios

testenv/vpn/ca.key:
	openssl genrsa -out $@ 2048

testenv/vpn/ca.crt: testenv/vpn/ca.key
	echo "prompt = no\ndistinguished_name=cert\n[cert]\ncommonName = Insekta CA\n" > testenv/vpn/config
	openssl req -config testenv/vpn/config -x509 -new -key $< -out $@
	rm -f testenv/vpn/config

clean:
	rm -rf ${base_static}css/insekta.css \
		   ${base_static}css/insekta.min.css \
		   ${base_static}css/bootstrap.min.css \
		   ${scenarios_static}css/pygments.css \
		   ${base_static}js/insekta.min.js \
		   ${base_static}js/jquery.min.js \
		   ${base_static}components

watchstatic:
	@while true; do \
		make css js; \
		inotifywait -qre close_write ${static_files}; \
	done
