import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b")) # slate-500
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(1.5 * cm, 28.5 * cm, "IPGuard - Panduan Onboarding & Kolaborasi Tim")
            self.drawRightString(A4[0] - 1.5 * cm, 28.5 * cm, "Milestone 3 & 4 Ready")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(1.5 * cm, 28.3 * cm, A4[0] - 1.5 * cm, 28.3 * cm)
            
        # Footer
        footer_text = f"Halaman {self._pageNumber} dari {page_count}"
        self.drawRightString(A4[0] - 1.5 * cm, 1.2 * cm, footer_text)
        self.drawString(1.5 * cm, 1.2 * cm, "CONFIDENTIAL - Internal Engineering Guide | Abhiprayaa29/IPGuard (Private)")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(1.5 * cm, 1.6 * cm, A4[0] - 1.5 * cm, 1.6 * cm)
        
        self.restoreState()


def build_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm
    )

    styles = getSampleStyleSheet()
    
    # Custom palette
    primary_color = colors.HexColor("#0f172a") # Slate 900
    brand_blue = colors.HexColor("#0284c7")    # Sky 600
    emerald = colors.HexColor("#059669")       # Emerald 600
    dark_gray = colors.HexColor("#334155")     # Slate 700
    bg_code = colors.HexColor("#f8fafc")       # Slate 50

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=brand_blue,
        spaceAfter=10
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=dark_gray
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=brand_blue,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=dark_gray,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=10,
        firstLineIndent=-6,
        spaceAfter=2
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
        backColor=bg_code,
        borderColor=colors.HexColor("#cbd5e1"),
        borderWidth=0.5,
        borderPadding=5,
        spaceBefore=3,
        spaceAfter=4
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=dark_gray
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold',
        textColor=primary_color
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#065f46")
    )

    story = []

    # Title & Header
    story.append(Paragraph("IPGuard - Panduan Onboarding & Rekayasa Kolaborator", title_style))
    story.append(Paragraph("Panduan Memulai Kontribusi untuk Aliza (aliali8230) & Anisa (Anisa1112-source)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=brand_blue, spaceBefore=0, spaceAfter=6))

    # Meta Info Card
    meta_data = [
        [
            Paragraph("<b>Repository:</b> https://github.com/Abhiprayaa29/IPGuard", meta_style),
            Paragraph("<b>Target Milestone:</b> Milestone 3 & Milestone 4", meta_style)
        ],
        [
            Paragraph("<b>Repository Owner:</b> @Abhiprayaa29", meta_style),
            Paragraph("<b>Visibility:</b> PRIVATE (Wajib Dipertahankan)", meta_style)
        ],
        [
            Paragraph("<b>Tanggal Dokumen:</b> 8 November 2026", meta_style),
            Paragraph("<b>Status Undangan:</b> Undangan Resmi Dikirimkan via GitHub API", meta_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[9.5 * cm, 8.5 * cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    # Section 1: Sambutan & Gambaran Proyek
    story.append(Paragraph("1. Sambutan & Ikhtisar Arsitektur IPGuard", h1_style))
    story.append(Paragraph(
        "Selamat datang di tim pengembang <b>IPGuard (Secure Digital Asset Protection)</b>! "
        "IPGuard adalah platform perlindungan aset digital yang menerapkan arsitektur <b>Zero-Trust Device Binding</b>. "
        "Alih-alih mengandalkan kata sandi statis atau OTP SMS yang rentan terhadap phishing dan pembajakan sesi (QR-jacking), "
        "IPGuard mewajibkan setiap operasi login dan akses data sensitif ditandatangani secara kriptografis oleh perangkat fisik Android "
        "menggunakan pasangan kunci <b>ECDSA NIST P-256</b> yang tersimpan aman di dalam Android Keystore (TEE / StrongBox).",
        body_style
    ))

    story.append(Paragraph(
        "Arsitektur monorepo IPGuard terdiri dari tiga subsistem utama:",
        body_style
    ))
    story.append(Paragraph("&bull; <b>Frontend Management Console (frontend/):</b> Aplikasi web React 19, TypeScript, dan Vite yang menyajikan kode QR otentikasi dinamis (60 detik TTL) serta polling status sesi aman (Anti QR-Jacking SEC-02).", bullet_style))
    story.append(Paragraph("&bull; <b>Backend Cryptographic API (backend/):</b> REST API Python 3.13 FastAPI dan PostgreSQL 17 dengan verifikasi matematis tanda tangan ECDSA, pessimistic row locking (SEC-01), dan validasi origin (SEC-03).", bullet_style))
    story.append(Paragraph("&bull; <b>Android Native Authenticator (mobile-authenticator/):</b> Aplikasi mobile Kotlin + Jetpack Compose (API 28-36) yang memindai QR melalui CameraX + ML Kit, lalu menandatangani challenge setelah konfirmasi biometrik Class 3 atau PIN perangkat.", bullet_style))

    # Section 2: Status Undangan & Hak Akses
    story.append(Paragraph("2. Status Undangan & Akses Kolaborator GitHub", h1_style))
    story.append(Paragraph(
        "Undangan kolaborasi resmi telah berhasil dikirimkan oleh Repository Owner (@Abhiprayaa29) kepada kedua partner melalui GitHub API:",
        body_style
    ))

    invite_data = [
        [
            Paragraph("Partner", table_header_style),
            Paragraph("GitHub Username", table_header_style),
            Paragraph("Status Undangan", table_header_style),
            Paragraph("Hak Akses (Role)", table_header_style),
            Paragraph("ID Undangan", table_header_style)
        ],
        [
            Paragraph("Aliza", table_cell_bold),
            Paragraph("aliali8230", table_cell_style),
            Paragraph("<font color='#059669'><b>Sent (Pending Acceptance)</b></font>", table_cell_style),
            Paragraph("Write (Push & PR)", table_cell_style),
            Paragraph("342172112", table_cell_style)
        ],
        [
            Paragraph("Anisa", table_cell_bold),
            Paragraph("Anisa1112-source", table_cell_style),
            Paragraph("<font color='#059669'><b>Sent (Pending Acceptance)</b></font>", table_cell_style),
            Paragraph("Write (Push & PR)", table_cell_style),
            Paragraph("342172124", table_cell_style)
        ]
    ]
    invite_table = Table(invite_data, colWidths=[2.5 * cm, 4.0 * cm, 4.5 * cm, 3.5 * cm, 3.5 * cm])
    invite_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(invite_table)
    story.append(Spacer(1, 4))

    # Action callout
    callout_data = [[
        Paragraph(
            "<b>CARA MENERIMA UNDANGAN GITHUB:</b><br/>"
            "1. Buka browser dan login ke akun GitHub masing-masing.<br/>"
            "2. Buka tautan resmi berikut: <b>https://github.com/Abhiprayaa29/IPGuard/invitations</b><br/>"
            "3. Klik tombol hijau <b>Accept invitation</b>.<br/>"
            "<i>Catatan Keamanan: Repositori ini bersifat PRIVATE. Jangan pernah mengubah status visibilitas atau membagikan source code ke pihak luar.</i>",
            callout_style
        )
    ]]
    callout_table = Table(callout_data, colWidths=[18.0 * cm])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ecfdf5")), # emerald-50
        ('BOX', (0, 0), (-1, -1), 1, emerald),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(callout_table)

    story.append(PageBreak())

    # Section 3: Setup Lingkungan Lokal
    story.append(Paragraph("3. Panduan Setup Lingkungan Pengembangan Lokal", h1_style))
    story.append(Paragraph(
        "Pastikan komputer Anda telah terinstal alat-alat berikut: Git 2.40+, Python 3.13 (atau 3.11+), Node.js 22 LTS (npm), OpenJDK 17, Android Studio (API 34-36), dan PostgreSQL 17.",
        body_style
    ))

    story.append(Paragraph("Langkah 1 - Clone Repositori & Salin Konfigurasi Environment", h2_style))
    story.append(Paragraph(
        "Kloning repositori privat dan inisialisasi file .env dari template contoh. Dilarang keras melakukan commit file .env nyata yang berisi kredensial!",
        body_style
    ))
    story.append(Paragraph(
        "git clone https://github.com/Abhiprayaa29/IPGuard.git<br/>"
        "cd IPGuard<br/>"
        "cp .env.example .env &amp;&amp; cp backend/.env.example backend/.env &amp;&amp; cp frontend/.env.example frontend/.env",
        code_style
    ))

    story.append(Paragraph("Langkah 2 - Inisialisasi Database PostgreSQL & Migrasi Alembic", h2_style))
    story.append(Paragraph(
        "Jalankan PostgreSQL (via Docker Compose: <code>docker-compose up -d</code>), aktifkan virtual environment Python, lalu jalankan migrasi schema:",
        body_style
    ))
    story.append(Paragraph(
        "cd backend<br/>"
        "python -m venv .venv<br/>"
        "# Windows: .\\.venv\\Scripts\\Activate.ps1 | Linux/macOS: source .venv/bin/activate<br/>"
        "pip install -r requirements.txt<br/>"
        "alembic -c alembic.ini upgrade head",
        code_style
    ))

    story.append(Paragraph("Langkah 3 - Menjalankan Backend & Frontend Development Server", h2_style))
    story.append(Paragraph(
        "<b>Terminal 1 - Backend FastAPI (Port 8000):</b>",
        body_style
    ))
    story.append(Paragraph(
        "cd backend<br/>"
        "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 60<br/>"
        "# Swagger UI interaktif tersedia di: http://localhost:8000/docs",
        code_style
    ))
    story.append(Paragraph(
        "<b>Terminal 2 - Frontend React + Vite (Port 5173):</b>",
        body_style
    ))
    story.append(Paragraph(
        "cd frontend &amp;&amp; npm install &amp;&amp; npm run dev<br/>"
        "# Buka browser ke: http://localhost:5173 (Halaman login QR di /login)",
        code_style
    ))

    story.append(Paragraph("Langkah 4 - Menjalankan Android Authenticator via ADB Reverse", h2_style))
    story.append(Paragraph(
        "Saat menggunakan perangkat fisik Android (USB Debugging aktif), jalankan port forwarding ADB reverse agar HP dapat menjangkau backend di port 8000 host:",
        body_style
    ))
    story.append(Paragraph(
        "adb reverse tcp:8000 tcp:8000<br/>"
        "cd mobile-authenticator<br/>"
        ".\\gradlew.bat installDebug<br/>"
        "adb shell am start -n com.ipguard.authenticator/.MainActivity",
        code_style
    ))

    story.append(Paragraph("4. Pengujian Otomatis (Pre-Push Quality Gate)", h1_style))
    story.append(Paragraph(
        "Sebelum membuat commit atau membuka Pull Request, jalankan rangkaian pengujian otomatis di ketiga subsistem:",
        body_style
    ))
    story.append(Paragraph(
        "# 1. Backend Pytest suite (65 pengujian lolos)<br/>"
        "cd backend &amp;&amp; python -m pytest -v<br/><br/>"
        "# 2. Frontend Strict Typecheck &amp; Production Build (0 error)<br/>"
        "cd ../frontend &amp;&amp; npm run build<br/><br/>"
        "# 3. Android Unit Tests &amp; Debug APK Compilation<br/>"
        "cd ../mobile-authenticator &amp;&amp; .\\gradlew.bat testDebugUnitTest assembleDebug --no-daemon",
        code_style
    ))

    story.append(PageBreak())

    # Section 5: Aturan Rekayasa & Alur Kerja Git
    story.append(Paragraph("5. Standar Rekayasa & Alur Kerja Git Kolaboratif", h1_style))
    story.append(Paragraph(
        "Untuk menjaga stabilitas arsitektur IPGuard, seluruh anggota tim wajib mematuhi aturan berikut:",
        body_style
    ))

    rules_data = [
        [
            Paragraph("Aturan Rekayasa", table_header_style),
            Paragraph("Penjelasan & Standar Implementasi", table_header_style)
        ],
        [
            Paragraph("<b>Dilarang Direct Push ke main</b>", table_cell_bold),
            Paragraph("Branch <code>main</code> adalah branch produksi terlindungi. Seluruh pekerjaan wajib dikerjakan pada feature branch dan digabungkan hanya melalui Pull Request (PR) yang telah direview.", table_cell_style)
        ],
        [
            Paragraph("<b>Konvensi Penamaan Branch</b>", table_cell_bold),
            Paragraph("Gunakan format:<br/>&bull; <code>feature/m3-asset-vault</code> atau <code>feature/m3-file-encryption</code><br/>&bull; <code>feature/m4-audit-chain</code><br/>&bull; <code>fix/nama-perbaikan</code><br/>&bull; <code>docs/nama-dokumen</code>", table_cell_style)
        ],
        [
            Paragraph("<b>Conventional Commits</b>", table_cell_bold),
            Paragraph("Terapkan format commit konvensional:<br/>&bull; <code>feat(crypto): implement AES-256-GCM cipher</code><br/>&bull; <code>test(backend): add signature verification tests</code><br/>&bull; <code>fix(android): resolve okhttp connection timeout</code>", table_cell_style)
        ],
        [
            Paragraph("<b>Kebijakan Nol Rahasia (Zero Secrets)</b>", table_cell_bold),
            Paragraph("Dilarang keras menyertakan file <code>.env</code>, kunci privat, password database, atau keystore ke Git. Selalu cek <code>git status</code> sebelum melakukan <code>git add</code>.", table_cell_style)
        ],
        [
            Paragraph("<b>Prosedur Pull Request (PR)</b>", table_cell_bold),
            Paragraph("Buka PR ke branch <code>main</code>, gunakan template PR yang tersedia di <code>.github/PULL_REQUEST_TEMPLATE.md</code>, dan sertakan bukti pengujian.", table_cell_style)
        ]
    ]
    rules_table = Table(rules_data, colWidths=[5.5 * cm, 12.5 * cm])
    rules_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(rules_table)
    story.append(Spacer(1, 6))

    # Section 6: Roadmap Tugas Milestone 3 & Milestone 4
    story.append(Paragraph("6. Roadmap Pembagian Tugas (Milestone 3 & 4)", h1_style))
    story.append(Paragraph(
        "Berikut adalah daftar kandidat issue teknis yang siap dikerjakan pada tahap Milestone 3 dan 4. "
        "<b>Pilih tugas bersama Repository Owner (@Abhiprayaa29) sebelum mulai membuat branch:</b>",
        body_style
    ))

    m3_data = [
        [
            Paragraph("Issue ID", table_header_style),
            Paragraph("Judul & Subsistem", table_header_style),
            Paragraph("Tujuan Teknis & Ruang Lingkup", table_header_style)
        ],
        [
            Paragraph("<b>#M3-01</b>", table_cell_bold),
            Paragraph("Digital Asset Vault Architecture<br/><i>(Backend & DB)</i>", table_cell_style),
            Paragraph("Merancang tabel PostgreSQL <code>assets</code>, migrasi Alembic, dan endpoint CRUD metadata aset digital terenkripsi.", table_cell_style)
        ],
        [
            Paragraph("<b>#M3-02</b>", table_cell_bold),
            Paragraph("File Encryption &amp; Decryption Pipeline<br/><i>(Backend &amp; Frontend)</i>", table_cell_style),
            Paragraph("Membangun streaming symmetric file encryption/decryption untuk file hingga 100MB dengan format chunk terotentikasi.", table_cell_style)
        ],
        [
            Paragraph("<b>#M3-03</b>", table_cell_bold),
            Paragraph("Secure Notes Cryptographic Storage<br/><i>(Full-Stack)</i>", table_cell_style),
            Paragraph("Fitur pencatatan rahasia terenkripsi end-to-end (zero-knowledge) dengan client-side encryption pada web console.", table_cell_style)
        ],
        [
            Paragraph("<b>#M3-04</b>", table_cell_bold),
            Paragraph("AES-256-GCM Symmetric Cipher<br/><i>(Backend Crypto)</i>", table_cell_style),
            Paragraph("Modul cipher authenticated encryption AES-256-GCM dengan 96-bit random IV dan verifikasi 128-bit authentication tag.", table_cell_style)
        ],
        [
            Paragraph("<b>#M3-05</b>", table_cell_bold),
            Paragraph("XChaCha20-Poly1305 Cipher<br/><i>(Backend Crypto)</i>", table_cell_style),
            Paragraph("Implementasi alternatif cipher modern dengan 192-bit extended nonce untuk keamanan collision-resistant pada volume tinggi.", table_cell_style)
        ],
        [
            Paragraph("<b>#M3-06</b>", table_cell_bold),
            Paragraph("Argon2id Key Derivation Function<br/><i>(Backend Crypto)</i>", table_cell_style),
            Paragraph("Derivasi kunci enkripsi master aset dari passphrase pengguna menggunakan Argon2id (memory cost 64MB, 3 iterasi, 4 thread).", table_cell_style)
        ],
        [
            Paragraph("<b>#M3-08</b>", table_cell_bold),
            Paragraph("PNG LSB Steganography Engine<br/><i>(Backend &amp; Image)</i>", table_cell_style),
            Paragraph("Menyisipkan hash integritas atau metadata kepemilikan aset secara tak kasat mata pada least-significant bits citra PNG (PSNR > 40dB).", table_cell_style)
        ],
        [
            Paragraph("<b>#M4-01</b>", table_cell_bold),
            Paragraph("SHA-256 Integrity Monitoring<br/><i>(Backend Worker)</i>", table_cell_style),
            Paragraph("Worker background otomatis yang menghitung ulang hash digest file aset dan mendeteksi perubahan ilegal (tampering).", table_cell_style)
        ],
        [
            Paragraph("<b>#M4-03</b>", table_cell_bold),
            Paragraph("Cryptographic Audit Hash Chain<br/><i>(Database &amp; Audit)</i>", table_cell_style),
            Paragraph("Tabel audit log append-only bertautan kriptografis (Merkle-linked) di mana setiap entri mengikat hash rekaman sebelumnya.", table_cell_style)
        ],
        [
            Paragraph("<b>#M4-06</b>", table_cell_bold),
            Paragraph("Interactive Hash Chain Explorer UI<br/><i>(Frontend React)</i>", table_cell_style),
            Paragraph("Visualisasi blok bertautan interaktif di web console untuk membuktikan integritas audit chain secara visual.", table_cell_style)
        ]
    ]
    m3_table = Table(m3_data, colWidths=[2.2 * cm, 4.8 * cm, 11.0 * cm])
    m3_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(m3_table)
    story.append(Spacer(1, 6))

    # Section 7: Kontak & Troubleshooting
    story.append(Paragraph("7. Troubleshooting Cepat & Saluran Koordinasi", h1_style))
    story.append(Paragraph("&bull; <b>ADB Reverse Terputus:</b> Jika Android Authenticator melempar ConnectException, pastikan kabel USB terpasang dan jalankan ulang perintah <code>adb reverse tcp:8000 tcp:8000</code>.", bullet_style))
    story.append(Paragraph("&bull; <b>Lock Screen Diperlukan:</b> Android Keystore mewajibkan PIN/Pola/Biometrik pada perangkat pengujian. Jika muncul DeviceLockScreenRequiredException, aktifkan kunci layar di menu Settings HP.", bullet_style))
    story.append(Paragraph("&bull; <b>CORS / Origin Mismatch:</b> Pastikan browser mengakses dari http://localhost:5173 dan origin terdaftar di backend/.env pada CORS_ORIGINS.", bullet_style))
    story.append(Paragraph("&bull; <b>Saluran Diskusi:</b> Untuk kendala teknis atau arsitektur, koordinasikan langsung dengan project lead <b>@Abhiprayaa29</b> atau buat issue melalui GitHub Discussions.", bullet_style))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully built: {filename}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "IPGUARD_COLLABORATOR_ONBOARDING_GUIDE.pdf"
    build_pdf(out_file)
