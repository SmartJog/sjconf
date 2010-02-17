EXTRA_DIST = sjconf.m4.in

dist_autotoolspkgdata_DATA = sjconf.am
nodist_aclocal_DATA = sjconf.m4

sjconf.m4: sjconf.m4.in Makefile
	sed -e 's|@autotoolspkgdatadir[@]|$(autotoolspkgdatadir)|g' $< > $@
