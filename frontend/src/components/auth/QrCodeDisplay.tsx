import { AlertTriangle, Clock, RefreshCw, Smartphone } from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import type { AuthStatus, QRPayload } from '../../types/auth'
import { Button } from '../ui/Button'

interface QrCodeDisplayProps {
  payload: QRPayload | null
  status: AuthStatus
  onRefresh?: () => void
}

export function QrCodeDisplay({
  payload,
  status,
  onRefresh,
}: QrCodeDisplayProps) {
  const qrString = payload ? JSON.stringify(payload) : ''
  const isExpired = status === 'EXPIRED'
  const isScanned = status === 'SCANNED'
  const isError = status === 'ERROR'
  const isCreating = status === 'CREATING'

  return (
    <div className="relative mx-auto flex size-60 items-center justify-center rounded-xl border border-ip-border bg-ip-elevated p-3">
      {payload && !isCreating ? (
        <div
          className={`overflow-hidden rounded-lg bg-white p-3 transition-opacity duration-200 ${
            isExpired || isError
              ? 'opacity-15'
              : isScanned
                ? 'opacity-35'
                : 'opacity-100'
          }`}
        >
          <QRCodeSVG
            value={qrString}
            size={192}
            level="H"
            includeMargin={false}
            fgColor="#0b0d11"
            bgColor="#ffffff"
          />
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center gap-2.5 text-zinc-400">
          <div className="size-7 animate-spin rounded-full border-2 border-zinc-700 border-t-ip-accent-400" />
          <span className="text-xs font-medium text-zinc-400">
            Generating challenge...
          </span>
        </div>
      )}

      {isScanned && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2.5 rounded-xl bg-ip-surface/95 p-4 text-center">
          <div className="flex size-10 items-center justify-center rounded-lg border border-ip-accent-500/30 bg-ip-accent-500/10 text-ip-accent-300">
            <Smartphone size={20} aria-hidden="true" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-zinc-100">
              Challenge scanned
            </h4>
            <p className="mt-1 text-xs text-zinc-400">
              Complete biometric verification on your Android device.
            </p>
          </div>
        </div>
      )}

      {isExpired && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 rounded-xl bg-ip-surface/95 p-4 text-center">
          <div className="flex size-10 items-center justify-center rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-300">
            <Clock size={20} aria-hidden="true" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-zinc-100">
              Challenge expired
            </h4>
            <p className="mt-1 text-xs text-zinc-400">
              QR challenges expire after 60 seconds.
            </p>
          </div>
          {onRefresh && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onRefresh}
              iconLeft={<RefreshCw size={13} />}
            >
              Regenerate QR
            </Button>
          )}
        </div>
      )}

      {isError && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 rounded-xl bg-ip-surface/95 p-4 text-center">
          <div className="flex size-10 items-center justify-center rounded-lg border border-red-500/30 bg-red-500/10 text-red-300">
            <AlertTriangle size={20} aria-hidden="true" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-zinc-100">
              Connection failure
            </h4>
            <p className="mt-1 text-xs text-zinc-400">
              Unable to reach authentication service.
            </p>
          </div>
          {onRefresh && (
            <Button
              variant="danger"
              size="sm"
              onClick={onRefresh}
              iconLeft={<RefreshCw size={13} />}
            >
              Retry Connection
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
