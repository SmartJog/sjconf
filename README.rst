=======
 SJConf
=======

SJConf is a configuration editing tool written in Python.

SJConf handles global and server specific configuration, deployment
and service restart.

SJConf in itself does not have any knowledge of configuration files
and their settings, everything is done through the use of plugins.


License
=======

SJConf is released under the `GNU LGPL 2.1 <http://www.gnu.org/licenses/lgpl-2.1.html>`_.


Build and installation
=======================

Bootstrapping
-------------

SJConf uses the autotools for its build system.

If you checked out code from the git repository, you will need
autoconf and automake to generate the configure script and Makefiles.

To generate them, simply run::

    $ autoreconf -fvi

Building
--------

SJConf builds like your typical autotools-based project::

    $ ./configure && make && make install


Development
===========

We use `semantic versioning <http://semver.org/>`_ for
versioning. When working on a development release, we append ``~dev``
to the current version to distinguish released versions from
development ones. This has the advantage of working well with Debian's
version scheme, where ``~`` is considered smaller than everything (so
version 1.10.0 is more up to date than 1.10.0~dev).


Authors
=======

SJConf was started at SmartJog by Philippe Bridant. Most of the code
was heavily redesigned by Jean-Philippe Garcia Ballester in 2008 to
give it its current API / class hierarchy. Various employees and
interns from SmartJog fixed bugs and added features since then.

* Alexandre Bossard <alexandre.bossard@smartjog.com>
* Alexandre Bique <alexandre.bique@smartjog.com>
* Benoit Mauduit <benoit.mauduit@smartjog.com>
* Clément Gauthey <clement.gauthey@smartjog.com>
* Gilles Dartiguelongue <gilles.dartiguelongue@smartjog.com>
* Grégory Charbonneau <gregory.charbonneau@smartjog.com>
* Jean-Baptiste Denis <jeanbaptiste.denis@smartjog.com>
* Jean-Philippe Garcia Ballester <jeanphilippe.garciaballester@smartjog.com>
* Mathieu Dupuy <mathieu.dupuy@smartjog.com>
* Matthieu Bouron <matthieu.bouron@smartjog.com>
* Nicolas Noirbent <nicolas.noirbent@smartjog.com>
* Philippe Bridant <philippe.bridant@smartjog.com>
* Rémi Cardona <remi.cardona@smartjog.com>
* Thomas Sanchez <thomas.sanchez@smartjog.com>
