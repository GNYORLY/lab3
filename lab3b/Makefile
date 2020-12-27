CC = python3
ARCHIVE = lab3b-504666652.tar.gz
sources = Makefile README lab3b.py 

all: lab3b

run: lab3b

lab3b:
	@$(CC) $@.py
	echo success!
	echo usage: python3 lab3.py filename

dist:
	@tar -cvzf $(ARCHIVE) $(sources)


clean:
	@rm -f *.csv