// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/PolicyReceiptAnchor.sol";

contract DeployScript is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);
        PolicyReceiptAnchor anchor = new PolicyReceiptAnchor();
        console.log("PolicyReceiptAnchor deployed at:", address(anchor));
        vm.stopBroadcast();
    }
}
