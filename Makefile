# vpd_audit: bootstrap, tests, smoke.
SUBMODULE_DIR := third_party/param-decomp
SUBMODULE_COMMIT := 74146b555f3eb3cd2bc639c3789fd3b7a099094a

.PHONY: bootstrap
bootstrap:
	@actual=$$(git -C $(SUBMODULE_DIR) rev-parse HEAD 2>/dev/null); \
	if [ -z "$$actual" ]; then echo "submodule $(SUBMODULE_DIR) is not checked out (git submodule update --init)"; exit 1; fi; \
	if [ "$$actual" != "$(SUBMODULE_COMMIT)" ]; then echo "submodule at $$actual, expected $(SUBMODULE_COMMIT)"; exit 1; fi; \
	echo "submodule commit $$actual"
	uv sync

.PHONY: test
test:
	uv run pytest tests -q

.PHONY: smoke
smoke:
	uv run vpd-audit smoke --run simplestories --n 8
	uv run vpd-audit smoke --run main --n 8
