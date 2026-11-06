package com.ipguard.authenticator.security

data class TestScenarioResult(
    val id: String,
    val name: String,
    val passed: Boolean,
    val detail: String,
    val error: String? = null
)

data class FullVerificationSuiteResult(
    val totalTests: Int,
    val passedCount: Int,
    val failedCount: Int,
    val allPassed: Boolean,
    val results: List<TestScenarioResult>,
    val finalKeyMetadata: KeySecurityMetadata?,
    val finalExportedPublicKey: ExportedPublicKey?
)

object DeviceKeyVerificationRunner {

    fun runAll(
        deviceKeyManager: DeviceKeyManager = AndroidKeystoreDeviceKeyManager(),
        requireUserAuthentication: Boolean = true
    ): FullVerificationSuiteResult {
        val testResults = mutableListOf<TestScenarioResult>()

        var initialFingerprint: String? = null

        // Step 0: Clean up any prior test key to start fresh for KA-01
        try {
            deviceKeyManager.deleteSigningKey()
        } catch (_: Throwable) {}

        // KA-01: Membuat signing key pertama kali
        try {
            val metadata = deviceKeyManager.generateSigningKey(requireUserAuthentication)
            testResults.add(
                TestScenarioResult(
                    id = "KA-01",
                    name = "Generate signing key for the first time",
                    passed = true,
                    detail = "Key created with alias '${metadata.alias}', algorithm='${metadata.algorithm}', size=${metadata.keySize}, securityLevel='${metadata.securityLevel.label}'"
                )
            )
        } catch (e: Throwable) {
            testResults.add(
                TestScenarioResult(
                    id = "KA-01",
                    name = "Generate signing key for the first time",
                    passed = false,
                    detail = "Failed to generate signing key",
                    error = "${e.javaClass.simpleName}: ${e.message}"
                )
            )
        }

        // KA-02: Memeriksa key setelah dibuat
        try {
            val exists = deviceKeyManager.hasSigningKey()
            testResults.add(
                TestScenarioResult(
                    id = "KA-02",
                    name = "Check key availability after creation",
                    passed = exists,
                    detail = if (exists) "Key is present in Android Keystore" else "Key not found after generation"
                )
            )
        } catch (e: Throwable) {
            testResults.add(
                TestScenarioResult(
                    id = "KA-02",
                    name = "Check key availability after creation",
                    passed = false,
                    detail = "Exception checking key presence",
                    error = "${e.javaClass.simpleName}: ${e.message}"
                )
            )
        }

        // KA-03: Menjalankan inisialisasi kembali (Idempotent)
        try {
            val pubKey1 = deviceKeyManager.getExportedPublicKey()
            initialFingerprint = pubKey1.sha256Fingerprint

            // Call ensureSigningKey: must NOT regenerate or change public key
            val metadata2 = deviceKeyManager.ensureSigningKey(requireUserAuthentication)
            val pubKey2 = deviceKeyManager.getExportedPublicKey()
            val isIdempotent = (pubKey1.sha256Fingerprint == pubKey2.sha256Fingerprint) &&
                    (pubKey1.base64Encoded == pubKey2.base64Encoded)

            testResults.add(
                TestScenarioResult(
                    id = "KA-03",
                    name = "Run initialization again (Idempotency test)",
                    passed = isIdempotent,
                    detail = if (isIdempotent) {
                        "ensureSigningKey() preserved existing key (Fingerprint matched: ${pubKey1.sha256Fingerprint})"
                    } else {
                        "Key was regenerated unexpectedly!"
                    }
                )
            )
        } catch (e: Throwable) {
            testResults.add(
                TestScenarioResult(
                    id = "KA-03",
                    name = "Run initialization again (Idempotency test)",
                    passed = false,
                    detail = "Exception in idempotency test",
                    error = "${e.javaClass.simpleName}: ${e.message}"
                )
            )
        }

        // KA-04: Menutup dan membuka aplikasi (Persistence across manager reload)
        try {
            val freshManager = AndroidKeystoreDeviceKeyManager(DeviceKeyManager.KEY_ALIAS)
            val exists = freshManager.hasSigningKey()
            val freshPubKey = freshManager.getExportedPublicKey()
            val isPersistent = exists && (freshPubKey.sha256Fingerprint == initialFingerprint)

            testResults.add(
                TestScenarioResult(
                    id = "KA-04",
                    name = "Persistence after application reload",
                    passed = isPersistent,
                    detail = if (isPersistent) {
                        "Key retained in Android Keystore with identical fingerprint after fresh provider reload"
                    } else {
                        "Key missing or changed after reload"
                    }
                )
            )
        } catch (e: Throwable) {
            testResults.add(
                TestScenarioResult(
                    id = "KA-04",
                    name = "Persistence after application reload",
                    passed = false,
                    detail = "Exception during persistence verification",
                    error = "${e.javaClass.simpleName}: ${e.message}"
                )
            )
        }

        // KA-05: Mengambil public key
        try {
            val pubKey = deviceKeyManager.getExportedPublicKey()
            val hasNoLines = !pubKey.base64Encoded.contains("\n") && !pubKey.base64Encoded.contains("\r")
            val isValid = pubKey.base64Encoded.isNotBlank() && hasNoLines && pubKey.format == "X.509"

            testResults.add(
                TestScenarioResult(
                    id = "KA-05",
                    name = "Export public key in X.509 Base64 format",
                    passed = isValid,
                    detail = if (isValid) {
                        "Exported X.509 Base64 (${pubKey.base64Encoded.length} chars, no line wrapping). Fingerprint: ${pubKey.sha256Fingerprint}"
                    } else {
                        "Invalid exported public key structure"
                    }
                )
            )
        } catch (e: Throwable) {
            testResults.add(
                TestScenarioResult(
                    id = "KA-05",
                    name = "Export public key in X.509 Base64 format",
                    passed = false,
                    detail = "Exception exporting public key",
                    error = "${e.javaClass.simpleName}: ${e.message}"
                )
            )
        }

        // KA-06: Membaca ulang public key
        try {
            val pubKey = deviceKeyManager.getExportedPublicKey()
            val canParse = deviceKeyManager.validatePublicKeyParsing(pubKey.base64Encoded)

            testResults.add(
                TestScenarioResult(
                    id = "KA-06",
                    name = "Reparse exported public key with KeyFactory",
                    passed = canParse,
                    detail = "Public key parsed successfully into standard Java PublicKey using KeyFactory('EC')"
                )
            )
        } catch (e: Throwable) {
            testResults.add(
                TestScenarioResult(
                    id = "KA-06",
                    name = "Reparse exported public key with KeyFactory",
                    passed = false,
                    detail = "Failed to reparse exported public key",
                    error = "${e.javaClass.simpleName}: ${e.message}"
                )
            )
        }

        // KA-07: Memeriksa private key (Non-exportable)
        try {
            val isNonExportable = deviceKeyManager.verifyPrivateKeyNonExportable()
            testResults.add(
                TestScenarioResult(
                    id = "KA-07",
                    name = "Verify private key is strictly non-exportable",
                    passed = isNonExportable,
                    detail = if (isNonExportable) {
                        "privateKey.encoded == null confirmed. Private key cannot leave Android Keystore."
                    } else {
                        "CRITICAL FAILURE: private key returned non-null encoded bytes!"
                    }
                )
            )
        } catch (e: Throwable) {
            testResults.add(
                TestScenarioResult(
                    id = "KA-07",
                    name = "Verify private key is strictly non-exportable",
                    passed = false,
                    detail = "Exception inspecting private key exportability",
                    error = "${e.javaClass.simpleName}: ${e.message}"
                )
            )
        }

        // KA-08: Memeriksa KeyInfo
        try {
            val metadata = deviceKeyManager.getKeySecurityMetadata()
            val hasValidInfo = metadata.algorithm == "EC" && metadata.keySize == 256 && metadata.digests.contains("SHA-256")

            testResults.add(
                TestScenarioResult(
                    id = "KA-08",
                    name = "Retrieve KeyInfo security metadata",
                    passed = hasValidInfo,
                    detail = "Security Level='${metadata.securityLevel.label}', isInsideSecureHardware=${metadata.isInsideSecureHardware}, keySize=${metadata.keySize}"
                )
            )
        } catch (e: Throwable) {
            testResults.add(
                TestScenarioResult(
                    id = "KA-08",
                    name = "Retrieve KeyInfo security metadata",
                    passed = false,
                    detail = "Failed to query KeyInfo metadata",
                    error = "${e.javaClass.simpleName}: ${e.message}"
                )
            )
        }

        // KA-09: Memeriksa autentikasi key
        try {
            val metadata = deviceKeyManager.getKeySecurityMetadata()
            val authMatches = (metadata.userAuthenticationRequired == requireUserAuthentication)

            testResults.add(
                TestScenarioResult(
                    id = "KA-09",
                    name = "Verify user authentication policy on key",
                    passed = authMatches,
                    detail = "userAuthenticationRequired=${metadata.userAuthenticationRequired} (expected: $requireUserAuthentication), durationSeconds=${metadata.userAuthenticationValidityDurationSeconds}"
                )
            )
        } catch (e: Throwable) {
            testResults.add(
                TestScenarioResult(
                    id = "KA-09",
                    name = "Verify user authentication policy on key",
                    passed = false,
                    detail = "Exception verifying user authentication policy",
                    error = "${e.javaClass.simpleName}: ${e.message}"
                )
            )
        }

        // KA-10: Menghapus key secara eksplisit
        try {
            val deleted = deviceKeyManager.deleteSigningKey()
            val existsAfterDelete = deviceKeyManager.hasSigningKey()
            val isSuccess = deleted && !existsAfterDelete

            testResults.add(
                TestScenarioResult(
                    id = "KA-10",
                    name = "Explicitly delete signing key",
                    passed = isSuccess,
                    detail = if (isSuccess) "Key alias successfully deleted and confirmed absent" else "Key alias still present after deletion"
                )
            )
        } catch (e: Throwable) {
            testResults.add(
                TestScenarioResult(
                    id = "KA-10",
                    name = "Explicitly delete signing key",
                    passed = false,
                    detail = "Exception during explicit key deletion",
                    error = "${e.javaClass.simpleName}: ${e.message}"
                )
            )
        }

        // Finally, generate a persistent signing key so the device remains in a ready/enrolled state
        var finalMetadata: KeySecurityMetadata? = null
        var finalExportedKey: ExportedPublicKey? = null
        try {
            finalMetadata = deviceKeyManager.ensureSigningKey(requireUserAuthentication)
            finalExportedKey = deviceKeyManager.getExportedPublicKey()
        } catch (_: Throwable) {}

        val passedCount = testResults.count { it.passed }
        val failedCount = testResults.size - passedCount

        return FullVerificationSuiteResult(
            totalTests = testResults.size,
            passedCount = passedCount,
            failedCount = failedCount,
            allPassed = (failedCount == 0),
            results = testResults,
            finalKeyMetadata = finalMetadata,
            finalExportedPublicKey = finalExportedKey
        )
    }
}
