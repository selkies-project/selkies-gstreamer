PREFIX ?= /usr/local
PKG_NAME ?= selkies-js-interposer

all:
	gcc -shared -fPIC -o joystick_interposer.so joystick_interposer.c -ldl

install: all
	mkdir -p $(PREFIX)/lib/$(PKG_NAME)
	cp *.so $(PREFIX)/lib/$(PKG_NAME)/
clean:
	rm -f *.so
