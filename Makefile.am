SUBDIRS = doc conf

sjconfpluginslocalstate_DATA =

dist_bin_SCRIPTS = sjconf

EXTRA_DIST = sjconf.py sjconfparts

install-exec-hook:
	python setup.py install --root "$(DESTDIR)" --prefix "@prefix@"
