CC = gcc
CFLAGS = -O2 -std=gnu11 -Wall -Wextra

ARCHIVE = lab3a-504666652.tar.gz
sources = Makefile README lab3a.c

all: build

build: lab3a

lab4b: 
	@$(CC) $(CFLAGS) -o $@ lab3a.c

dist:
	@tar -czvf $(ARCHIVE) $(sources)

clean:
	@rm -f lab3a *.csv