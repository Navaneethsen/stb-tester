# stb-tester

Automated User Interface Testing for Set-Top Boxes & Smart TVs

* Copyright (C) 2013-2014 Stb-tester.com Ltd,
  2012-2014 YouView TV Ltd. and other contributors.
* License: LGPL v2.1 or (at your option) any later version (see [LICENSE]).
* <a href="https://travis-ci.org/stb-tester/stb-tester">
    <img src="https://travis-ci.org/stb-tester/stb-tester.png?branch=master">
  </a>

**For commercial support and turn-key test automation appliances** see
[Stb-tester.com].

**For community-supported documentation and mailing list** see our [wiki], in
particular [Getting Started].

**[Python API documentation]**.

**Command-line documentation:** [stbt(1) man page].

------------------------------------------------------------------------------

**Documentation for maintainers**

To make a release:

* `make check enable_stbt_camera=yes`
* Update docs/release-notes.md
* `git tag -a vXX && git push vXX`
* Package Fedora release:

        extra/fedora/fedora-shell.sh -c "make srpm; sudo make rpm"
        extra/fedora/test-rpm.sh stb-tester-$version-1.fc20.x86_64.rpm
        extra/fedora/copr-publish.sh stb-tester-$version-1.fc20.src.rpm

* Package Ubuntu release:

        make deb
        make check-ubuntu
        make ppa-publish

* Announce on <http://stb-tester.com/blog> and twitter.


[Stb-tester.com]: http://stb-tester.com
[LICENSE]: https://github.com/stb-tester/stb-tester/blob/master/LICENSE
[wiki]: https://github.com/stb-tester/stb-tester/wiki
[Getting Started]: https://github.com/stb-tester/stb-tester/wiki/Getting-started-with-stb-tester
[stbt(1) man page]: https://github.com/stb-tester/stb-tester/blob/master/docs/stbt.1.rst
[Python API documentation]: http://stb-tester.com/stb-tester-one/rev2015.1/python-api
