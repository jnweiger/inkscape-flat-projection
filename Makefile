# a simple makefile to pull a tar ball.

PREFIX?=/usr
EXTNAME=flat-projection
DISTNAME=inkscape-$(EXTNAME)
EXCL=--exclude \*.orig --exclude \*.pyc
ALL=README.md *.png *.sh *.rules *.py *.inx
VERS=$$(echo '<xml height="0"/>' | python ./$(EXTNAME).py --version /dev/stdin)


DEST=$(DESTDIR)$(PREFIX)/share/inkscape/extensions

all: clean build check

build: $(EXTNAME).py

dist:   build check
	cd distribute; sh ./distribute.sh

check:
	sh test/test.sh


$(EXTNAME).py:
	sed >  $@ -e '/INLINE_BLOCK_START/,$$d' < src/flatproj.py
	sed >> $@ -e '/if __name__ ==/,$$d' < src/inksvg.py
	sed >> $@ -e '/if __name__ ==/,$$d' -e '/^from\s\s*__future__\s\s*import\s/d' < src/zsort42.py
	sed >> $@ -e '1,/INLINE_BLOCK_END/d' < src/flatproj.py

#install and install_de is used by deb/dist.sh
install:
	mkdir -p $(DEST)
	install -m 644 -t $(DEST) $(EXTNAME).inx
	# CAUTION: cp -a does not work under fakeroot. Use cp -r instead.
	install -m 755 -t $(DEST) *.py


tar_dist_classic: clean
	name=$(DISTNAME)-$(VERS); echo "$$name"; echo; \
	tar jcvf $$name.tar.bz2 $(EXCL) --transform="s,^,$$name/," $(ALL)
	grep about_version ./$(EXTNAME).inx
	@echo version should be $(VERS)

tar_dist:
	python setup.py sdist --format=bztar
	mv dist/*.tar* .
	rm -rf dist

clean:
	rm -f $(EXTNAME).py
	rm -f *.orig */*.orig
	rm -rf distribute/$(DISTNAME)
	rm -rf distribute/deb/files

