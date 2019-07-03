CONTIKI_PROJECT = node
all: $(CONTIKI_PROJECT)

PLATFORMS_EXCLUDE = sky nrf52dk native simplelink

CONTIKI=../../..

 # force Orchestra from command line
MAKE_WITH_ORCHESTRA ?= 1
# force Security from command line
MAKE_WITH_SECURITY ?= 0
 # print #routes periodically, used for regression tests
MAKE_WITH_PERIODIC_ROUTES_PRINT ?= 1



MAKE_MAC = MAKE_MAC_TSCH

#MAKE_NET = MAKE_NET_IPV6 # ksh..
MAKE_ROUTING = MAKE_ROUTING_RPL_CLASSIC  #ksh..
CFLAGS += -DROUTING_CONF_RPL_CLASSIC=1
MODULES += os/net/routing/rpl-classic



MODULES += os/services/shell

ifeq ($(MAKE_WITH_ORCHESTRA),1)
#MODULES += os/services/orchestra
MODULES += os/services/mc-orchestra
endif

ifeq ($(MAKE_WITH_SECURITY),1)
CFLAGS += -DWITH_SECURITY=1
endif

ifeq ($(MAKE_WITH_PERIODIC_ROUTES_PRINT),1)
CFLAGS += -DWITH_PERIODIC_ROUTES_PRINT=1
endif

include $(CONTIKI)/Makefile.include
