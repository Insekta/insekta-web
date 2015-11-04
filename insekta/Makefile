base_static = insekta/base/static/
scenarios_static = insekta/scenarios/static/scenarios/
katex_download = https://github.com/Khan/KaTeX/releases/download/v0.5.1/katex.tar.gz

all: css js components

css: ${base_static}css/insekta.min.css ${base_static}css/bootstrap.min.css

js: ${base_static}js/bootstrap.min.js

components: ${base_static}components/katex

${base_static}css/insekta.min.css: ${base_static}css/custom.css ${scenarios_static}css/custom.css
	cat $^ | yui-compressor -o $@ --type css --charset utf-8

%.min.css: %.css
	yui-compressor -o $@ --type css --charset utf-8 $<

%.min.js: %.js
	yui-compressor -o $@ --type js --charset utf-8 $<

%.mo: %.po
	msgfmt -o $@ $<

${base_static}components/katex:
	mkdir -p $@
	wget -O - '${katex_download}' | tar -xzC $(dir $@)

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
