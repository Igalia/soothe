SOOTHE=python3 ./soothe.py

help:
	@awk -F ':|##' '/^[^\t].+?:.*?##/ { printf "\033[36m%-30s\033[0m %s\n", $$1, $$NF }' $(MAKEFILE_LIST)

install_deps: ## install Python dependencies
	python3 -m pip install -r requirements-dev.txt --break-system-packages

check: ## check that very basic tests run
	@echo "Running dummy test..."
	$(SOOTHE) list
	$(SOOTHE) list -c
	$(SOOTHE) download
	$(SOOTHE) run -e Dummy

dbg-%:
	echo "Value of $* = $($*)"

.PHONY: help check install_deps
