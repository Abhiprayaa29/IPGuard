// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../contracts/BatchAnchorRegistry.sol";

interface VmScript {
    function envAddress(string calldata name) external view returns (address);
    function envOr(string calldata name, address defaultValue) external view returns (address);
    function startBroadcast() external;
    function stopBroadcast() external;
}

contract DeployScript {
    VmScript private constant vm = VmScript(address(uint160(uint256(keccak256("hevm cheat code")))));

    function run() external returns (BatchAnchorRegistry deployed) {
        // Optional separate signer address; defaults to tx broadcaster if AUTHORIZED_SIGNER_ADDRESS is unset.
        address authorizedSigner = vm.envOr("AUTHORIZED_SIGNER_ADDRESS", msg.sender);
        vm.startBroadcast();
        deployed = new BatchAnchorRegistry(authorizedSigner);
        vm.stopBroadcast();
    }
}
