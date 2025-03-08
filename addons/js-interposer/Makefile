PREFIX ?= /usr

all: build build32

deps:
	@sudo apt-get update
	@sudo apt-get install -y build-essential evtest strace joystick libsdl2-dev gcc-multilib libevdev-dev

build:
	gcc -shared -fPIC -o selkies_joystick_interposer.so joystick_interposer.c dev/input-dir-interposer.c -ldl -Wall

build32:
	gcc -m32 -shared -fPIC -o selkies_joystick_interposer_i386.so joystick_interposer.c -ldl -Wall

build-docker-ubuntu-%:
	docker build --platform=linux/amd64 --build-arg=PKG_NAME=selkies-js-interposer --build-arg PKG_VERSION=0.0.0 --build-arg DISTRIB_IMAGE=ubuntu --build-arg DISTRIB_RELEASE=$* -f Dockerfile.debpkg -t selkies-js-interposer:ubuntu-$* .

build-docker: build-docker-ubuntu-24.04 build-docker-ubuntu-22.04 build-docker-ubuntu-20.04

install: build build32
	sudo cp selkies_joystick_interposer.so /usr/lib/x86_64-linux-gnu/selkies_joystick_interposer.so
	sudo cp selkies_joystick_interposer_i386.so /usr/lib/i386-linux-gnu/selkies_joystick_interposer.so

clean:
	rm -f *.so
	sudo rm -f /dev/input/js0 /dev/input/event1000

fake-devices:
	@sudo mkdir -p /dev/input
	@sudo touch /dev/input/js0 && sudo chmod 777 /dev/input/js0
	@sudo touch /dev/input/event1000 && sudo chmod 777 /dev/input/event1000

py-js-test:
	python3 js-interposer-test.py /tmp/selkies_js0.sock

py-ev-test:
	python3 js-interposer-test.py /tmp/selkies_event1000.sock

py-selkies-test:
	python3 ../../src/selkies_gstreamer/gamepad.py

jstest: build
	LD_PRELOAD=$(PWD)/selkies_joystick_interposer.so jstest /dev/input/js0

evtest: build fake-devices
	LD_PRELOAD=$(PWD)/selkies_joystick_interposer.so evtest /dev/input/event1000

sdltest: build
	gcc -o sdl_joystick_reader sdl-js-test.c -lSDL2
	LD_PRELOAD=$(PWD)/selkies_joystick_interposer.so SDL_JOYSTICK_DEVICE=/dev/input/event1000 ./sdl_joystick_reader

sdltest32: build32 fake-devices
	gcc -m32 -o sdl_joystick_reader_i386 sdl-js-test.c -lSDL2
	LD_PRELOAD=$(PWD)/selkies_joystick_interposer_i386.so SDL_JOYSTICK_DEVICE=/dev/input/event1000 ./sdl_joystick_reader_i386

sdltest-debug: build fake-devices
	gcc -o sdl_joystick_reader sdl-js-test.c -g -I/usr/local/include -L/usr/local/lib -lSDL2
	LD_PRELOAD=$(PWD)/selkies_joystick_interposer.so LD_LIBRARY_PATH=/usr/local/lib gdb ./sdl_joystick_reader

winetest: build build32 fake-devices
	LD_PRELOAD=$(PWD)/selkies_joystick_interposer.so wine control

xvfbtest: build
	LD_PRELOAD=$(PWD)/selkies_joystick_interposer.so Xvfb

gamepadtool:
	cd /tmp && curl -LO https://generalarcade.com/gamepadtool/linux/gamepadtool_1.2_amd64.deb && \
		sudo apt-get install -y /tmp/gamepadtool_1.2_amd64.deb

gamepadtool32:
	cd /tmp && curl -LO https://generalarcade.com/gamepadtool/linux/gamepadtool_1.2_i386.deb && \
		sudo apt-get install -y /tmp/gamepadtool_1.2_i386.deb

gamepadtool-test: gamepadtool build fake-devices
	LD_PRELOAD=$(PWD)/selkies_joystick_interposer.so SDL_JOYSTICK_DISABLE_UDEV=1 gamepad-tool

gamepadtool32-test: gamepadtool32 build32 fake-devices
	LD_PRELOAD=$(PWD)/selkies_joystick_interposer_i386.so SDL_JOYSTICK_DISABLE_UDEV=1 gamepad-tool