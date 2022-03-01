SMART_PY_CLI := ~/smartpy-cli/SmartPy.sh
DIST_DIR := ./dist
TEMP_DIR := ./temp
CONTRACTS_DIR := ./contracts

###### AGGREGATE TARGETS ######

# Build everything
all:
	make test
	make compile

# Compile Everything
compile:
	make compile-pool
	make compile-option-fa2
	make compile-option-manager
	make clean

###### COMPILATIONs ######
compile-pool:
	$(SMART_PY_CLI) compile $(CONTRACTS_DIR)/pool.py $(TEMP_DIR)
	cp $(TEMP_DIR)/pool/step_000_cont_0_contract.tz $(DIST_DIR)/pool.tz
	cp $(TEMP_DIR)/pool/step_000_cont_0_storage.tz $(DIST_DIR)/pool_storage.tz

compile-option-fa2:
	$(SMART_PY_CLI) compile $(CONTRACTS_DIR)/option_fa2.py $(TEMP_DIR)
	cp $(TEMP_DIR)/option_fa2/step_000_cont_0_contract.tz $(DIST_DIR)/option_fa2.tz
	cp $(TEMP_DIR)/option_fa2/step_000_cont_0_storage.tz $(DIST_DIR)/option_fa2_storage.tz

compile-option-manager:
	$(SMART_PY_CLI) compile $(CONTRACTS_DIR)/option_manager.py $(TEMP_DIR)
	cp $(TEMP_DIR)/option_manager/step_000_cont_2_contract.tz $(DIST_DIR)/option_manager.tz
	cp $(TEMP_DIR)/option_manager/step_000_cont_2_storage.tz $(DIST_DIR)/option_manager_storage.tz


#Test Everything
test:
	make test-pool
	make test-option-manager
	make clean

###### TESTS ######

test-pool:
	$(SMART_PY_CLI) test $(CONTRACTS_DIR)/pool.py $(TEMP_DIR)

test-option-manager:
	$(SMART_PY_CLI) test $(CONTRACTS_DIR)/option_manager.py $(TEMP_DIR)

###### DEPLOY ######
deploy:
	node_modules/.bin/ts-node scripts/deploy.ts

###### CLEANING ######
clean:
	rm -rf $(TEMP_DIR)
