// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../contracts/BatchAnchorRegistry.sol";

interface Vm {
    function prank(address) external;
    function expectRevert(bytes calldata) external;
    function expectRevert(bytes4) external;
}

contract BatchAnchorRegistryTest {
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    BatchAnchorRegistry private registry;
    address private constant SIGNER = address(0x1111111111111111111111111111111111111111);
    address private constant ATTACKER = address(0x2222222222222222222222222222222222222222);
    address private constant NEXT_SIGNER = address(0x3333333333333333333333333333333333333333);

    bytes32 private constant CHAIN_A = keccak256("ipguard-dev-1fbd21364ac24757");
    bytes32 private constant ROOT_1 = keccak256("root-1");
    bytes32 private constant HEAD_1 = keccak256("head-1");
    bytes32 private constant ROOT_2 = keccak256("root-2");
    bytes32 private constant HEAD_2 = keccak256("head-2");

    function setUp() public {
        registry = new BatchAnchorRegistry(SIGNER);
    }

    function test_AuthorizedAnchoringAndRetrieval() public {
        vm.prank(SIGNER);
        uint256 idx = registry.anchorBatch(CHAIN_A, 1, 80, ROOT_1, HEAD_1);
        require(idx == 0, "expected batch index 0");
        require(registry.batchCountByChain(CHAIN_A) == 1, "expected count 1");
        require(registry.lastAnchoredSequence(CHAIN_A) == 80, "expected last seq 80");

        BatchAnchorRegistry.BatchAnchor memory stored = registry.getBatch(CHAIN_A, 0);
        require(stored.auditChainId == CHAIN_A, "chain mismatch");
        require(stored.fromSequence == 1, "fromSequence mismatch");
        require(stored.toSequence == 80, "toSequence mismatch");
        require(stored.merkleRoot == ROOT_1, "merkleRoot mismatch");
        require(stored.headHash == HEAD_1, "headHash mismatch");
        require(stored.signer == SIGNER, "signer mismatch");
        require(registry.verifyBatch(CHAIN_A, 1, 80, ROOT_1, HEAD_1), "verifyBatch should succeed");
        require(!registry.verifyBatch(CHAIN_A, 1, 80, ROOT_2, HEAD_1), "verifyBatch must reject bad root");
    }

    function test_UnauthorizedAnchoringReverts() public {
        vm.prank(ATTACKER);
        vm.expectRevert(BatchAnchorRegistry.UnauthorizedSigner.selector);
        registry.anchorBatch(CHAIN_A, 1, 10, ROOT_1, HEAD_1);
    }

    function test_ZeroRootOrHeadReverts() public {
        vm.prank(SIGNER);
        vm.expectRevert(BatchAnchorRegistry.ZeroMerkleRoot.selector);
        registry.anchorBatch(CHAIN_A, 1, 10, bytes32(0), HEAD_1);

        vm.prank(SIGNER);
        vm.expectRevert(BatchAnchorRegistry.ZeroHeadHash.selector);
        registry.anchorBatch(CHAIN_A, 1, 10, ROOT_1, bytes32(0));
    }

    function test_InvalidSequenceRangeReverts() public {
        vm.prank(SIGNER);
        vm.expectRevert(BatchAnchorRegistry.InvalidSequenceRange.selector);
        registry.anchorBatch(CHAIN_A, 0, 10, ROOT_1, HEAD_1);

        vm.prank(SIGNER);
        vm.expectRevert(BatchAnchorRegistry.InvalidSequenceRange.selector);
        registry.anchorBatch(CHAIN_A, 10, 5, ROOT_1, HEAD_1);
    }

    function test_DuplicateAndOverlappingBatchReverts() public {
        vm.prank(SIGNER);
        registry.anchorBatch(CHAIN_A, 1, 10, ROOT_1, HEAD_1);

        vm.prank(SIGNER);
        vm.expectRevert(BatchAnchorRegistry.DuplicateOrOverlappingBatch.selector);
        registry.anchorBatch(CHAIN_A, 1, 10, ROOT_1, HEAD_1);

        vm.prank(SIGNER);
        vm.expectRevert(BatchAnchorRegistry.DuplicateOrOverlappingBatch.selector);
        registry.anchorBatch(CHAIN_A, 5, 15, ROOT_2, HEAD_2);
    }

    function test_GapSequenceRevertsAndContiguousSucceeds() public {
        vm.prank(SIGNER);
        registry.anchorBatch(CHAIN_A, 1, 10, ROOT_1, HEAD_1);

        vm.prank(SIGNER);
        vm.expectRevert(
            abi.encodeWithSelector(BatchAnchorRegistry.NonContiguousSequence.selector, uint64(11), uint64(12))
        );
        registry.anchorBatch(CHAIN_A, 12, 20, ROOT_2, HEAD_2);

        vm.prank(SIGNER);
        uint256 idx2 = registry.anchorBatch(CHAIN_A, 11, 20, ROOT_2, HEAD_2);
        require(idx2 == 1, "expected batch index 1");
        require(registry.lastAnchoredSequence(CHAIN_A) == 20, "expected last seq 20");
    }

    function test_SignerRotationByOwnerOnly() public {
        vm.prank(ATTACKER);
        vm.expectRevert(BatchAnchorRegistry.UnauthorizedOwner.selector);
        registry.setAuthorizedSigner(NEXT_SIGNER);

        registry.setAuthorizedSigner(NEXT_SIGNER);
        require(registry.authorizedSigner() == NEXT_SIGNER, "signer not updated");

        vm.prank(SIGNER);
        vm.expectRevert(BatchAnchorRegistry.UnauthorizedSigner.selector);
        registry.anchorBatch(CHAIN_A, 1, 5, ROOT_1, HEAD_1);

        vm.prank(NEXT_SIGNER);
        registry.anchorBatch(CHAIN_A, 1, 5, ROOT_1, HEAD_1);
    }

    function test_ComputeMerkleRootOddEvenAndSingle() public view {
        bytes32[] memory one = new bytes32[](1);
        one[0] = bytes32(uint256(0xabc));
        bytes32 expectedOne = keccak256(abi.encodePacked(bytes1(0x00), one[0]));
        require(registry.computeMerkleRoot(one) == expectedOne, "single-leaf root mismatch");

        bytes32[] memory three = new bytes32[](3);
        three[0] = bytes32(uint256(1));
        three[1] = bytes32(uint256(2));
        three[2] = bytes32(uint256(3));
        bytes32 l0 = keccak256(abi.encodePacked(bytes1(0x00), three[0]));
        bytes32 l1 = keccak256(abi.encodePacked(bytes1(0x00), three[1]));
        bytes32 l2 = keccak256(abi.encodePacked(bytes1(0x00), three[2]));
        bytes32 n0 = keccak256(abi.encodePacked(bytes1(0x01), l0, l1));
        bytes32 n1 = keccak256(abi.encodePacked(bytes1(0x01), l2, l2));
        bytes32 expectedThree = keccak256(abi.encodePacked(bytes1(0x01), n0, n1));
        require(registry.computeMerkleRoot(three) == expectedThree, "odd-leaf root mismatch");
    }
}
