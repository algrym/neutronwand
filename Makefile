# This works for Macs.  Need to update for other platforms.
UF2_DIR=/Volumes/RPI-RP2
#CIRCUIT_PYTHON_DIR=/Volumes/CIRCUITPY
CIRCUIT_PYTHON_DIR=/Volumes/FEATHERM4
CIRCUIT_PYTHON_VER=8.2.8
CIRCUIT_PYTHON_LIB_VER=8.x
CIRCUIT_PYTHON_LIB_DATE=20231121
CODEPY_DIR=$(CIRCUIT_PYTHON_DIR)/
CODEPY_LIB_DIR=$(CIRCUIT_PYTHON_DIR)/lib

# These shouldn't need changing, but eh ...
CURLFLAGS="--location"

all: venv downloads .gitignore version.py

venv: venv/touchfile

venv/touchfile: requirements.txt
	test -d venv || virtualenv venv
	. venv/bin/activate; pip install --upgrade pip
	. venv/bin/activate; pip install -Ur requirements.txt
	touch venv/touchfile

version.py: code.py
	date -r code.py "+__version__ = %'%Y-%m-%d %H:%M:%S%'" > version.py

test: venv
	. venv/bin/activate; nosetests project/test

.gitignore:
	curl https://www.toptal.com/developers/gitignore/api/python,circuitpython,git,virtualenv,macos,vim,pycharm -o .gitignore
	printf "\n# ignore the downloads directory\ndownloads\n" >> .gitignore
	printf "\n# ignore .idea/ directory\n.idea/\n" >> .gitignore
	printf "\n# ignore version.py that updates each install\nversion.py\n" >> .gitignore

downloads: \
	downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-$(CIRCUIT_PYTHON_VER).uf2 \
	downloads/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE).zip

downloads/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE).zip:
	test -d downloads || mkdir downloads
	curl $(CURLFLAGS) https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/$(CIRCUIT_PYTHON_LIB_DATE)/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE).zip -o $(@)
	unzip $(@) -d downloads/

downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-$(CIRCUIT_PYTHON_VER).uf2:
	test -d downloads || mkdir downloads
	curl $(CURLFLAGS) https://downloads.circuitpython.org/bin/raspberry_pi_pico/en_US/adafruit-circuitpython-raspberry_pi_pico-en_US-$(CIRCUIT_PYTHON_VER).uf2 -o $(@)

install_circuit_python: downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-$(CIRCUIT_PYTHON_VER).uf2
	cp downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-$(CIRCUIT_PYTHON_VER).uf2 $(UF2_DIR)/

install: all
	rsync -avlcC \
		version.py code.py \
			$(CODEPY_DIR)
	test -d $(CODEPY_LIB_DIR) || mkdir $(CODEPY_LIB_DIR)
	cd downloads/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE)/lib && rsync -avlcC \
		neopixel* \
		*debouncer* \
		*adafruit_fancyled* \
		adafruit_lis3dh \
		adafruit_bus_device \
			$(CODEPY_LIB_DIR)

clean:
	rm -rf venv downloads
	find . -iname '*.pyc' -delete
