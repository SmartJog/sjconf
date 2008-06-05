man8_MANS = sjconf.man
DISTCLEANFILES = sjconf.man
EXTRA_DIST = sjconf.t2t

SUFFIXES = .t2t

.t2t.man:
	txt2tags -o $@ $<
