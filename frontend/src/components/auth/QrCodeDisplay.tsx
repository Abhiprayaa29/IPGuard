import { AlertTriangle, Clock, RefreshCw, Smartphone } from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import type { AuthStatus, QRPayload } from '../../types/auth'

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
    <div className="relative mx-auto flex size-64 items-center justify-center rounded-2xl border border-white/10 bg-slate-900/80 p-3 shadow-2xl backdrop-blur-md">
      {/* Active QR SVG */}
      {payload && !isCreating ? (
        <div
          className={`overflow-hidden rounded-xl bg-white p-3.5 transition-all duration-300 ${
            isExpired || isError
              ? 'opacity-20 blur-[1px]'
              : isScanned
                ? 'opacity-40 scale-95'
                : 'opacity-100 scale-100'
          }`}
        >
          <QRCodeSVG
            value={qrString}
            size={204}
            level="H"
            includeMargin={false}
            fgColor="#050d18"
            bgColor="#ffffff"
          />
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center gap-3 text-slate-500">
          <div className="size-12 animate-spin rounded-full border-2 border-ip-teal-400/20 border-t-ip-teal-400" />
          <span className="text-xs uppercase tracking-wider text-slate-400">
            Generating challenge...
          </span>
        </div>
      )}

      {/* Scanned Overlay */}
      {isScanned && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 rounded-2xl bg-ip-navy-950/85 p-4 text-center backdrop-blur-sm animate-fade-in">
          <div className="relative flex size-14 items-center justify-center rounded-2xl border border-ip-teal-400/30 bg-ip-teal-400/10 text-ip-teal-300">
            <Smartphone size={28} className="animate-bounce" />
            <span className="absolute -top-1 -right-1 size-3.5 rounded-full border-2 border-ip-navy-950 bg-amber-400 animate-ping" />
          </div>
          <div>
            <h4 className="font-display text-sm font-bold text-white">
              QR Code Scanned
            </h4>
            <p className="mt-1 text-xs text-slate-400">
              Confirm authorization on your Samsung Galaxy A54...
            </p>
          </div>
        </div>
      )}

      {/* Expired Overlay */}
      {isExpired && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 rounded-2xl bg-ip-navy-950/90 p-4 text-center backdrop-blur-sm animate-fade-in">
          <div className="flex size-12 items-center justify-center rounded-2xl border border-amber-500/30 bg-amber-500/10 text-amber-400">
            <Clock size={24} />
          </div>
          <div>
            <h4 className="font-display text-sm font-bold text-white">
              Challenge Expired
            </h4>
            <p className="mt-1 text-xs text-slate-400">
              For security, QR codes expire after 60 seconds.
            </p>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="mt-1 inline-flex items-center gap-2 rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/10 px-4 py-2 text-xs font-semibold text-ip-teal-300 shadow-sm transition hover:bg-ip-teal-400/20 hover:border-ip-teal-400/50"
            >
              <RefreshCw size={14} />
              Regenerate QR
            </button>
          )}
        </div>
      )}

      {/* Error Overlay */}
      {isError && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 rounded-2xl bg-ip-navy-950/90 p-4 text-center backdrop-blur-sm animate-fade-in">
          <div className="flex size-12 items-center justify-center rounded-2xl border border-rose-500/30 bg-rose-500/10 text-rose-400">
            <AlertTriangle size={24} />
          </div>
          <div>
            <h4 className="font-display text-sm font-bold text-white">
              Connection Failure
            </h4>
            <p className="mt-1 text-xs text-slate-400">
              Unable to poll authentication service.
            </p>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="mt-1 inline-flex items-center gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-2 text-xs font-semibold text-rose-300 shadow-sm transition hover:bg-rose-500/20 hover:border-rose-500/50"
            >
              <RefreshCw size={14} />
              Retry Connection
            </button>
          )}
        </div>
      )}
    </div>
  )
}
