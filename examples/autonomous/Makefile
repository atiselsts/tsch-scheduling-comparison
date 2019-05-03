#
# This exist just for quick cleaning of the subdirectories.
# For the real configuration, see Makefile.common` and `common-conf.h`.
#

all:
	@echo "Recursive make not supported"

clean:
	$(MAKE) -C exp-local clean
	$(MAKE) -C exp-query clean
	$(MAKE) -C exp-collection clean

distclean:
	$(MAKE) -C exp-local distclean
	$(MAKE) -C exp-query distclean
	$(MAKE) -C exp-collection distclean
