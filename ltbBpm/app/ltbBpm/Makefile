#------------------------------------------------------------------------------
# This file Makefile of the libera tune prototype GUI
#------------------------------------------------------------------------------


UIC = pyuic4

all: ui_ltb.py

run: all
	python main.py

clean:
	rm -f *~ *.pyc ui_*.py

ui_ltb.py: ui_ltb.ui
	$(UIC) -x $? -o $@

