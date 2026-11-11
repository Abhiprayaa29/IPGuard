// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title BatchAnchorRegistry
 * @notice Minimal tamper-evident commitment registry for IPGuard M5 audit batches.
 *         Stores ONLY cryptographic commitments (Keccak-256 Merkle roots, SHA-256 head hashes,
 *         contiguous sequence bounds, block timestamp, and authorized signer address).
 *         No plaintext application data, PII, tokens, or payloads are stored on-chain.
 */
contract BatchAnchorRegistry {
    struct BatchAnchor {
        bytes32 auditChainId;
        uint64 fromSequence;
        uint64 toSequence;
        bytes32 merkleRoot;
        bytes32 headHash;
        uint64 blockTimestamp;
        address signer;
    }

    address public owner;
    address public authorizedSigner;

    mapping(bytes32 => mapping(uint256 => BatchAnchor)) private _anchors;
    mapping(bytes32 => uint256) public batchCountByChain;
    mapping(bytes32 => uint64) public lastAnchoredSequence;
    mapping(bytes32 => uint256) private _batchIndexPlusOne;

    error UnauthorizedOwner();
    error UnauthorizedSigner();
    error ZeroAddress();
    error ZeroChainId();
    error ZeroMerkleRoot();
    error ZeroHeadHash();
    error InvalidSequenceRange();
    error DuplicateOrOverlappingBatch();
    error NonContiguousSequence(uint64 expectedFromSequence, uint64 actualFromSequence);
    error BatchNotFound();

    event AuthorizedSignerUpdated(
        address indexed previousSigner,
        address indexed newSigner,
        address indexed updatedBy
    );
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event BatchAnchored(
        bytes32 indexed auditChainId,
        uint256 indexed batchIndex,
        uint64 fromSequence,
        uint64 toSequence,
        bytes32 merkleRoot,
        bytes32 headHash,
        uint64 blockTimestamp,
        address indexed signer
    );

    modifier onlyOwner() {
        if (msg.sender != owner) revert UnauthorizedOwner();
        _;
    }

    modifier onlyAuthorizedSigner() {
        if (msg.sender != authorizedSigner) revert UnauthorizedSigner();
        _;
    }

    constructor(address initialSigner) {
        if (initialSigner == address(0)) revert ZeroAddress();
        owner = msg.sender;
        authorizedSigner = initialSigner;
        emit OwnershipTransferred(address(0), msg.sender);
        emit AuthorizedSignerUpdated(address(0), initialSigner, msg.sender);
    }

    function setAuthorizedSigner(address newSigner) external onlyOwner {
        if (newSigner == address(0)) revert ZeroAddress();
        address previousSigner = authorizedSigner;
        authorizedSigner = newSigner;
        emit AuthorizedSignerUpdated(previousSigner, newSigner, msg.sender);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert ZeroAddress();
        address previousOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(previousOwner, newOwner);
    }

    function anchorBatch(
        bytes32 auditChainId,
        uint64 fromSequence,
        uint64 toSequence,
        bytes32 merkleRoot,
        bytes32 headHash
    ) external onlyAuthorizedSigner returns (uint256 batchIndex) {
        if (auditChainId == bytes32(0)) revert ZeroChainId();
        if (merkleRoot == bytes32(0)) revert ZeroMerkleRoot();
        if (headHash == bytes32(0)) revert ZeroHeadHash();
        if (fromSequence == 0 || toSequence < fromSequence) revert InvalidSequenceRange();

        bytes32 rangeKey = _rangeKey(auditChainId, fromSequence, toSequence);
        if (_batchIndexPlusOne[rangeKey] != 0) revert DuplicateOrOverlappingBatch();

        uint64 prevEnd = lastAnchoredSequence[auditChainId];
        if (prevEnd != 0) {
            if (fromSequence <= prevEnd) revert DuplicateOrOverlappingBatch();
            if (fromSequence != prevEnd + 1) {
                revert NonContiguousSequence(prevEnd + 1, fromSequence);
            }
        }

        batchIndex = batchCountByChain[auditChainId];
        uint64 ts = uint64(block.timestamp);

        _anchors[auditChainId][batchIndex] = BatchAnchor({
            auditChainId: auditChainId,
            fromSequence: fromSequence,
            toSequence: toSequence,
            merkleRoot: merkleRoot,
            headHash: headHash,
            blockTimestamp: ts,
            signer: msg.sender
        });

        batchCountByChain[auditChainId] = batchIndex + 1;
        lastAnchoredSequence[auditChainId] = toSequence;
        _batchIndexPlusOne[rangeKey] = batchIndex + 1;

        emit BatchAnchored(
            auditChainId,
            batchIndex,
            fromSequence,
            toSequence,
            merkleRoot,
            headHash,
            ts,
            msg.sender
        );
    }

    function getBatch(
        bytes32 auditChainId,
        uint256 batchIndex
    ) external view returns (BatchAnchor memory) {
        if (batchIndex >= batchCountByChain[auditChainId]) revert BatchNotFound();
        return _anchors[auditChainId][batchIndex];
    }

    function getBatchByRange(
        bytes32 auditChainId,
        uint64 fromSequence,
        uint64 toSequence
    ) external view returns (BatchAnchor memory) {
        uint256 idxPlusOne = _batchIndexPlusOne[_rangeKey(auditChainId, fromSequence, toSequence)];
        if (idxPlusOne == 0) revert BatchNotFound();
        return _anchors[auditChainId][idxPlusOne - 1];
    }

    function verifyBatch(
        bytes32 auditChainId,
        uint64 fromSequence,
        uint64 toSequence,
        bytes32 merkleRoot,
        bytes32 headHash
    ) external view returns (bool) {
        uint256 idxPlusOne = _batchIndexPlusOne[_rangeKey(auditChainId, fromSequence, toSequence)];
        if (idxPlusOne == 0) return false;
        BatchAnchor memory stored = _anchors[auditChainId][idxPlusOne - 1];
        return
            stored.auditChainId == auditChainId &&
            stored.fromSequence == fromSequence &&
            stored.toSequence == toSequence &&
            stored.merkleRoot == merkleRoot &&
            stored.headHash == headHash;
    }

    /**
     * @notice Compute deterministic Keccak-256 Merkle root matching backend/app/services/merkle.py.
     *         Leaf = keccak256(0x00 || rawEventHash)
     *         Node = keccak256(0x01 || left || right)
     *         Odd node count duplicates the final node in that level.
     */
    function computeMerkleRoot(bytes32[] calldata eventHashes) external pure returns (bytes32) {
        uint256 len = eventHashes.length;
        if (len == 0) revert ZeroMerkleRoot();

        bytes32[] memory level = new bytes32[](len);
        for (uint256 i = 0; i < len; ++i) {
            level[i] = keccak256(abi.encodePacked(bytes1(0x00), eventHashes[i]));
        }

        while (len > 1) {
            uint256 nextLen = (len + 1) / 2;
            for (uint256 i = 0; i < nextLen; ++i) {
                bytes32 left = level[i * 2];
                bytes32 right = (i * 2 + 1 < len) ? level[i * 2 + 1] : left;
                level[i] = keccak256(abi.encodePacked(bytes1(0x01), left, right));
            }
            len = nextLen;
        }

        return level[0];
    }

    function _rangeKey(
        bytes32 auditChainId,
        uint64 fromSequence,
        uint64 toSequence
    ) private pure returns (bytes32) {
        return keccak256(abi.encode(auditChainId, fromSequence, toSequence));
    }
}
