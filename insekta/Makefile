base_static = insekta/base/static/
scenarios_static = insekta/scenarios/static/scenarios/
components_static = ${base_static}components/

jquery_download = http://code.jquery.com/jquery-2.1.4.min.js
katex_download = https://github.com/Khan/KaTeX/releases/download/v0.5.1/katex.tar.gz
raphaeljs_download = http://github.com/DmitryBaranovskiy/raphael/raw/master/raphael-min.js
flot_download = http://www.flotcharts.org/downloads/flot-0.8.3.zip
flot_tmp := $(shell mktemp -u).zip

all: css js components

css: ${base_static}css/insekta.min.css ${base_static}css/bootstrap.min.css

js: ${base_static}js/bootstrap.min.js ${base_static}js/jquery.min.js

components: ${components_static}katex ${components_static}katex/katex-scenario.min.js ${components_static}raphaeljs ${components_static}flot

${base_static}js/jquery.min.js:
	wget -O $@ '${jquery_download}'

${base_static}css/insekta.min.css: ${base_static}css/custom.css ${scenarios_static}css/custom.css
	cat $^ | yui-compressor -o $@ --type css --charset utf-8

%.min.css: %.css
	yui-compressor -o $@ --type css --charset utf-8 $<

%.min.js: %.js
	yui-compressor -o $@ --type js --charset utf-8 $<

%.mo: %.po
	msgfmt -o $@ $<

${components_static}katex/katex-scenario.min.js: ${scenarios_static}/js/katex-scenario.js ${components_static}katex
	yui-compressor -o $@ --type css --charset utf-8 $<

${components_static}katex:
	mkdir -p $@
	wget -O - '${katex_download}' | tar -xzC $(dir $@)

${components_static}raphaeljs:
	mkdir -p $@
	wget -P $@ ${raphaeljs_download}

${components_static}flot:
	wget -O ${flot_tmp} '${flot_download}'
	unzip ${flot_tmp} -d $(dir $@)
	rm ${flot_tmp}

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
		   ${base_static}components
