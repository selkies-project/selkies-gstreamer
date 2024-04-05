PREFIX ?= /usr
PKG_NAME ?= selkies-js-interposer

all:
	gcc -shared -fPIC -o joystick_interposer.so joystick_interposer.c -ldl

install: all
	mkdir -p $(PREFIX)/lib/$(gcc -print-multiarch | sed -e 's/i.*86/i386/')/$(PKG_NAME)
	cp *.so $(PREFIX)/lib/$(gcc -print-multiarch | sed -e 's/i.*86/i386/')/$(PKG_NAME)/
clean:
	rm -f *.so