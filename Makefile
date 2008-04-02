PREFIX=/usr/local
BIN_DIR=$(DESTDIR)/$(PREFIX)/bin
LIB_DIR=$(DESTDIR)/$(PREFIX)/lib
CONF_DIR=$(DESTDIR)/etc/smartjog
PLUGINS_DIR=$(LIB_DIR)/sjconf/plugins
TEMPLATES_DIR=$(CONF_DIR)/templates

MAJOR=1
MINOR=0
REV=0
V=$(MAJOR).$(MINOR).$(REV)

clean:

distclean:

dist: distclean
	mkdir -p sjconf-$(V)
	cp -a ChangeLog Makefile sjconf conf sjconf-$(V)
	for dir in `find sjconf-$(V) -name '\.svn'`; do rm -rf "$$dir" ; done
	tar czf sjconf-$(V).tar.gz sjconf-$(V)

install:
	install -d $(BIN_DIR)
	install -m 755 sjconf $(BIN_DIR)
	install -d $(CONF_DIR)
	cd conf; find . -type f -exec install -D -m 644 {} $(CONF_DIR)/{} \;
	install -d $(PLUGINS_DIR)
	install -d $(TEMPLATES_DIR)
