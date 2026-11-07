package com.ipguard.authenticator.ui.camera

import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import java.io.Closeable
import java.util.concurrent.atomic.AtomicBoolean

class QrCodeAnalyzer(
    private val onQrCodeDetected: (String) -> Unit
) : ImageAnalysis.Analyzer, Closeable {

    private val closed = AtomicBoolean(false)
    private val detected = AtomicBoolean(false)
    private val scanner = BarcodeScanning.getClient(
        BarcodeScannerOptions.Builder()
            .setBarcodeFormats(Barcode.FORMAT_QR_CODE)
            .build()
    )

    @ExperimentalGetImage
    override fun analyze(imageProxy: ImageProxy) {
        val mediaImage = imageProxy.image
        if (closed.get() || detected.get() || mediaImage == null) {
            imageProxy.close()
            return
        }

        try {
            val inputImage = InputImage.fromMediaImage(
                mediaImage,
                imageProxy.imageInfo.rotationDegrees
            )
            scanner.process(inputImage)
                .addOnSuccessListener { barcodes ->
                    if (!closed.get()) {
                        val validBarcode = barcodes.firstOrNull { !it.rawValue.isNullOrBlank() }
                        if (validBarcode != null && !validBarcode.rawValue.isNullOrBlank()) {
                            if (detected.compareAndSet(false, true)) {
                                onQrCodeDetected(validBarcode.rawValue!!)
                            }
                        }
                    }
                }
                .addOnCompleteListener {
                    imageProxy.close()
                }
        } catch (_: Exception) {
            imageProxy.close()
        }
    }

    override fun close() {
        closed.set(true)
        scanner.close()
    }
}
