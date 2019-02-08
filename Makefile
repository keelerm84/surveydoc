.PHONY: help
help: #! Show this help message
	@echo 'Usage: make [OPTIONS] [TARGET]'
	@echo ''
	@echo 'Targets:'
	@sed -n 's/\(^.*:\).*#!\( .*\$\)/  \1\2/p' $(MAKEFILE_LIST) | column -t -s ':'

.PHONY: style
style: #! Run pycodestyle against the code base
style:
	pycodestyle surveydoc/

.PHONY: test
test: #! Run all quality checks against this codebase
test: style
