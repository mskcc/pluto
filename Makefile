export SHELL:=/bin/bash
.ONESHELL:
UNAME:=$(shell uname)

export PATH:=$(CURDIR)/conda/bin:$(CURDIR)/bin:$(PATH)
unexport PYTHONPATH
unexport PYTHONHOME

ifeq ($(UNAME), Darwin)
CONDASH:=Miniconda3-4.7.12-MacOSX-x86_64.sh
endif

ifeq ($(UNAME), Linux)
CONDASH:=Miniconda3-4.7.12-Linux-x86_64.sh
endif

CONDAURL:=https://repo.anaconda.com/miniconda/$(CONDASH)

conda:
	@set +e
	echo ">>> Setting up conda..."
	wget "$(CONDAURL)"
	bash "$(CONDASH)" -b -p conda
	rm -f "$(CONDASH)"

install: conda
	pip install -r requirements.txt

bash:
	bash

test:
	python3 test_tools.py
	python3 test_serializer.py
	python3 test_classes.py
	python3 test_tables.py
	CWL_ENGINE=toil PRINT_TESTNAME=T PRINT_COMMAND=T PRINT_STATS=T python3 test_tools.py
	CWL_ENGINE=toil python3 test_serializer.py
