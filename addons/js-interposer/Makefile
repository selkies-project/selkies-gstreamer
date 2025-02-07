PREFIX ?= /usr

all: build build32

deps:
	@sudo apt-get update
	@sudo apt-get install -y build-essential evtest strace joystick libsdl2-dev gcc-multilib libevdev-dev

build:
	gcc -shared -fPIC -o selkies_joystick_interposer.so joystick_interposer.c -ldl -Wall

build32:
	gcc -m32 -shared -fPIC -o selkies_joystick_interposer_i386.so joystick_interposer.c -ldl -Wall

install: build
	mkdir -p $(PREFIX)/lib/$(gcc -print-multiarch | sed -e 's/i.*86/i386/')
	cp *.so $(PREFIX)/lib/$(gcc -print-multiarch | sed -e 's/i.*86/i386/')/
clean:
	rm -f *.so
	sudo rm -f /dev/input/js0 /dev/input/event1000

fake-devices:
	@sudo touch /dev/input/js0 && sudo chmod 777 /dev/input/js0
	@sudo touch /dev/input/event1000 && sudo chmod 777 /dev/input/event1000

py-js-test:
	python3 js-interposer-test.py /tmp/selkies_js0.sock

py-ev-test:
	python3 js-interposer-test.py /tmp/selkies_event1000.sock

jstest: build
	LD_PRELOAD=$(PWD)/selkies_joystick_interposer.so jstest /dev/input/js0

evtest: build fake-devices
	LD_PRELOAD=$(PWD)/selkies_joystick_interposer.so evtest /dev/input/event1000

sdltest: build fake-devices
	gcc -o sdl_joystick_reader sdl-js-test.c -lSDL2
	LD_PRELOAD=$(PWD)/selkies_joystick_interposer.so ./sdl_joystick_reader

winetest: build build32 fake-devices
	LD_PRELOAD=$(PWD)/selkies_joystick_interposer.so wine control