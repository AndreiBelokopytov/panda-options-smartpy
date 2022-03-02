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
	make compile-option-market
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

compile-option-market:
	$(SMART_PY_CLI) compile $(CONTRACTS_DIR)/option_market.py $(TEMP_DIR)
	cp $(TEMP_DIR)/xtz_usd_call_option_market/step_000_cont_2_contract.tz $(DIST_DIR)/xtz_usd_call_option_market.tz
	cp $(TEMP_DIR)/xtz_usd_call_option_market/step_000_cont_2_storage.tz $(DIST_DIR)/xtz_usd_call_option_market_storage.tz
		cp $(TEMP_DIR)/xtz_usd_put_option_market/step_000_cont_3_contract.tz $(DIST_DIR)/xtz_usd_put_option_market.tz
	cp $(TEMP_DIR)/xtz_usd_put_option_market/step_000_cont_3_storage.tz $(DIST_DIR)/xtz_usd_put_option_market_storage.tz


#Test Everything
test:
	make test-pool
	make test-option-market
	make clean

###### TESTS ######

test-pool:
	$(SMART_PY_CLI) test $(CONTRACTS_DIR)/pool.py $(TEMP_DIR)

test-option-market:
	$(SMART_PY_CLI) test $(CONTRACTS_DIR)/option_market.py $(TEMP_DIR)

###### DEPLOY ######
deploy:
	node_modules/.bin/ts-node scripts/deploy.ts

###### CLEANING ######
clean:
	rm -rf $(TEMP_DIR)
