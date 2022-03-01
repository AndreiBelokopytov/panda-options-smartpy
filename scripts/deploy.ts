import { readFileSync } from "fs";
import path from "path";
import { InMemorySigner } from "@taquito/signer";
import { Operation, TezosToolkit } from "@taquito/taquito";

const { PRIVATE_KEY, RPC } = process.env;

const DIST_FOLDER = "./dist";
const CONFIRMATIONS_COUNT = 1;

if (!RPC) {
  throw "RPC environment variable must be provided";
}

if (!PRIVATE_KEY) {
  throw "PRIVATE_KEY environment variable must be provided";
}

const Tezos = new TezosToolkit(RPC);
Tezos.setProvider({
  signer: new InMemorySigner(PRIVATE_KEY),
});

(async function deploy() {
  console.log("⏳ waiting for contracts origination");
  const poolContract = await originateContract("pool");
  const optionFA2Contract = await originateContract("option_fa2");
  const optionManagerContract = await originateContract("option_manager");
  console.log("⏳ initializing contracts");
  await confirmOperation(
    await optionFA2Contract.methods["set_administrator"](
      optionManagerContract.address
    ).send()
  );
  await confirmOperation(
    await optionManagerContract.methods["set_pool_address"](
      poolContract.address
    ).send()
  );
  await confirmOperation(
    await optionManagerContract.methods["set_option_fa2_address"](
      optionFA2Contract.address
    ).send()
  );
  console.log("🎉 everything is done!");
})();

async function confirmOperation(op: Operation) {
  return op.confirmation(CONFIRMATIONS_COUNT);
}

async function originateContract(
  contractName: string,
  storageName: string = `${contractName}_storage`
) {
  const code = readFileSync(
    path.join(DIST_FOLDER, contractName + ".tz")
  ).toString();
  const init = readFileSync(
    path.join(DIST_FOLDER, storageName + ".tz")
  ).toString();
  const op = await Tezos.contract.originate({
    code,
    init,
  });
  const contract = await op.contract();
  console.log(
    `✅ "${contractName}" contract originated: ${op.contractAddress}`
  );
  return contract;
}
