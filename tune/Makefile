#------------------------------------------------------------------------------
# This file Makefile of the libera tune prototype GUI
#------------------------------------------------------------------------------


UIC = pyuic4

all: ui_tune.py

run: all
	python2.5 main.py

clean:
	rm -f *~ *.pyc ui_*.py

ui_tune.py: ui_tune.ui
	$(UIC) -x $? -o $@

