.PHONY: pypi, tag, shell, typecheck, pytest, test

pypi:
	poetry publish --build
	make tag

tag:
	git tag $$(python -c "from apib2openapi import __version__; print(__version__)")
	git push --tags

shell:
	PYTHONPATH=apib2openapi:tests:$$PYTHONPATH ipython

typecheck:
	pytype apib2openapi

pytest:
	py.test -v -s --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb tests/

test:
	$(MAKE) typecheck
	$(MAKE) pytest
