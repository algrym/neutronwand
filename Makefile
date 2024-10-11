# This works for Macs.  Need to update for other platforms.
UF2_DIR=/Volumes/FEATHERBOOT
CIRCUIT_PYTHON_BOARD=feather_m4_express
CIRCUIT_PYTHON_DIR=/Volumes/FEATHERM4
CIRCUIT_PYTHON_VER=9.1.4
CIRCUIT_PYTHON_LIB_VER=9.x
CIRCUIT_PYTHON_LIB_DATE=20241005
CODEPY_DIR=$(CIRCUIT_PYTHON_DIR)/
CODEPY_LIB_DIR=$(CIRCUIT_PYTHON_DIR)/lib

# These shouldn't need changing, but eh ...
CURLFLAGS=--location

# Rsync flags to work around failures during write
RSYNCFLAGS=--archive --copy-links --checksum --cvs-exclude --inplace --partial --update --checksum

all: venv downloads .gitignore code.py

venv: venv/touchfile

venv/touchfile: requirements.txt
	test -d venv || python3 -m venv --system-site-packages --upgrade-deps venv
	. venv/bin/activate; pip install --upgrade pip
	. venv/bin/activate; pip install -Ur requirements.txt
	touch venv/touchfile

code.py: neutronpack.py Makefile
	printf "#!/usr/bin/env python3\n" > $@
	printf "import neutronpack\n\n" >> $@
	date -r $< "+__version__ = %'%Y-%m-%d %H:%M:%S%'" >> $@
	printf "\nif __name__ == '__main__':\n" >> $@
	printf "	neutronpack.main_loop()\n" >> $@

test: venv
	. venv/bin/activate; nosetests project/test

.gitignore:
	curl https://www.toptal.com/developers/gitignore/api/python,circuitpython,git,virtualenv,macos,vim,pycharm -o .gitignore
	printf "\n# ignore the downloads directory\ndownloads\n" >> .gitignore
	printf "\n# ignore .idea/ directory\n.idea/\n" >> .gitignore
	printf "\n# ignore mp3 files\n*.mp3\n" >> .gitignore
	printf "\n# ignore code.py that updates each install\ncode.py\n" >> .gitignore

downloads: \
	downloads/adafruit-circuitpython-$(CIRCUIT_PYTHON_BOARD)-en_US-$(CIRCUIT_PYTHON_VER).uf2 \
	downloads/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE).zip

downloads/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE).zip:
	test -d downloads || mkdir downloads
	curl $(CURLFLAGS) https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/$(CIRCUIT_PYTHON_LIB_DATE)/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE).zip -o $(@)
	unzip $(@) -d downloads/

downloads/adafruit-circuitpython-$(CIRCUIT_PYTHON_BOARD)-en_US-$(CIRCUIT_PYTHON_VER).uf2:
	test -d downloads || mkdir downloads
	curl $(CURLFLAGS) https://downloads.circuitpython.org/bin/$(CIRCUIT_PYTHON_BOARD)/en_US/adafruit-circuitpython-$(CIRCUIT_PYTHON_BOARD)-en_US-$(CIRCUIT_PYTHON_VER).uf2 -o $(@)

install_circuit_python: downloads/adafruit-circuitpython-$(CIRCUIT_PYTHON_BOARD)-en_US-$(CIRCUIT_PYTHON_VER).uf2
	rsync $(RSYNCFLAGS) --progress downloads/adafruit-circuitpython-$(CIRCUIT_PYTHON_BOARD)-en_US-$(CIRCUIT_PYTHON_VER).uf2 $(UF2_DIR)/

install: all
	rsync $(RSYNCFLAGS) \
		neutronpack.py code.py \
			$(CODEPY_DIR)
	test -d $(CODEPY_LIB_DIR) || mkdir $(CODEPY_LIB_DIR)
	cd downloads/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE)/lib && rsync -avlcC \
		neopixel* \
		*debouncer* \
		*adafruit_fancyled* \
		adafruit_lis3dh* \
		adafruit_bus_device \
			$(CODEPY_LIB_DIR)

clean:
	rm -rf venv downloads
	find . -iname '*.pyc' -delete
