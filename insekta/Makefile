.PHONY: all css js locales components clean watchstatic installdeps

base_static = insekta/base/static/
scenarios_static = insekta/scenarios/static/scenarios/
components_static = ${base_static}components/

flot_download = http://www.flotcharts.org/downloads/flot-0.8.3.zip
flot_tmp := $(shell mktemp -u).zip

UGLIFYJS := node_modules/.bin/uglifyjs
CLEANCSS := node_modules/.bin/cleancss --skip-rebase


static_files = $(shell find \( -name '*.css' -o -name '*.js' \) -not \( -name '*.min.js' -o -name '*.min.css' \))

all: css js components locales

css: ${base_static}css/insekta.min.css

js: ${base_static}js/insekta.min.js ${base_static}js/vue.min.js ${scenarios_static}js/scenario.min.js

locales: locale/de_DE/LC_MESSAGES/django.mo locale/en_US/LC_MESSAGES/django.mo

components: ${components_static}mathjax ${components_static}flot

${scenarios_static}css/pygments.css:
	pygmentize -S default -f html -a .highlight > $@

${base_static}css/bootstrap.css: ${base_static}scss/custom.scss node_modules/bootstrap
	sass $< > $@

${base_static}css/insekta.css: ${base_static}css/bootstrap.css ${base_static}css/fa-solid.css ${base_static}css/fontawesome.css ${base_static}css/custom.css ${scenarios_static}css/custom.css ${scenarios_static}css/pygments.css
	cat $^ > $@

${base_static}js/insekta.js: node_modules/jquery/dist/jquery.min.js node_modules/bootstrap/dist/js/bootstrap.js ${base_static}js/base.js ${base_static}js/automath.js
	cat $^ > $@

${base_static}js/vue.min.js: node_modules/vue/dist/vue.min.js
	cp $< $@

%.min.css: %.css node_modules/.bin/cleancss
	$(CLEANCSS) $< > $@

%.min.js: %.js node_modules/.bin/uglifyjs
	$(UGLIFYJS) $< > $@

%.mo: %.po
	msgfmt -o $@ $<

${components_static}flot:
	wget -O ${flot_tmp} '${flot_download}'
	unzip ${flot_tmp} -d $(dir $@)
	rm ${flot_tmp}

${components_static}mathjax: node_modules/mathjax
	mkdir -p ${components_static}
	cp -r $^ $@
	rm -rf $@/unpacked
	rm -rf $@/docs
	rm -rf $@/tests
	rm -rf $@/fonts/HTML-CSS/TeX/png
	rm -rf $@/fonts/HTML-CSS/TeX/svg

node_modules: package.json
	npm install
	touch node_modules

node_modules/bootstrap: node_modules
node_modules/.bin/uglifyjs: node_modules
node_modules/.bin/cssclean: node_modules
node_modules/.bin/sass: node_modules

testenv: testenv/scenarios testenv/vpn testenv/vpn/ca.key testenv/vpn/ca.crt

testenv/vpn:
	mkdir -p testenv/vpn

testenv/scenarios:
	mkdir -p testenv/scenarios

testenv/vpn/ca.key:
	openssl genrsa -out $@ 2048

testenv/vpn/ca.crt: testenv/vpn/ca.key
	printf "prompt = no\ndistinguished_name=cert\n[cert]\ncommonName = Insekta CA\n" > testenv/vpn/config
	openssl req -config testenv/vpn/config -x509 -new -key $< -out $@
	rm -f testenv/vpn/config

clean:
	rm -rf ${base_static}css/insekta.css \
		   ${base_static}css/insekta.min.css \
		   ${base_static}css/bootstrap.css \
		   ${base_static}css/bootstrap.min.css \
		   ${scenarios_static}css/pygments.css \
		   ${base_static}js/insekta.js \
		   ${base_static}js/insekta.min.js \
		   ${base_static}components \
		   node_modules

watchstatic:
	@while true; do \
		make css js; \
		inotifywait -qre close_write ${static_files}; \
	done
