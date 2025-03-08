all: build

deps:
	sudo apt-get update && sudo apt-get install linux-libc-dev

build:
	gcc -fPIC -shared -o input-dir-interposer.so input-dir-interposer.c -ldl

build-test:
	gcc -o test-input-dir-interposer input-dir-interposer-test.c

test: build build-test
	LD_PRELOAD=./input-dir-interposer.so ./test-input-dir-interposer
	

