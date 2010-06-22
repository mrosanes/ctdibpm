#------------------------------------------------------------------------------
# This file Makefile of the Libera Graphical User Interface
#------------------------------------------------------------------------------


UIC = pyuic4

all: ui_about.py ui_gainscheme.py ui_libera.py ui_settime.py ui_statusbar.py ui_synchronize.py ui_log.py

run: all
	python ctdibpm.py

clean:
	rm -f *~ *.pyc ui_*.py

ui_about.py: ui_about.ui
	$(UIC) -x $? -o $@

ui_gainscheme.py: ui_gainscheme.ui
	$(UIC) -x $? -o $@

ui_libera.py: ui_libera.ui
	$(UIC) -x $? -o $@

ui_settime.py: ui_settime.ui
	$(UIC) -x $? -o $@

ui_statusbar.py: ui_statusbar.ui
	$(UIC) -x $? -o $@

ui_synchronize.py: ui_synchronize.ui
	$(UIC) -x $? -o $@

ui_log.py: ui_log.ui
	$(UIC) -x $? -o $@

