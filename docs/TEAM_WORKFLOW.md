# IPGuard — Team Development & Collaboration Guide

Panduan ini ditujukan bagi seluruh anggota tim pengembang IPGuard untuk melakukan *clone*, *setup*, *branching*, *testing*, dan kontribusi kode melalui mekanisme *Pull Request* (PR) pada repository privat GitHub.

---

## 1. Persiapan Awal (Prerequisites)

Pastikan lingkungan lokal pengembang telah terpasang:
- **Git** (versi 2.40 atau lebih baru)
- **Node.js** (v22 LTS) & **npm**
- **Python** (v3.13 atau v3.11+) & **pip**
- **Android Studio / Android SDK Command-line Tools** (Build-Tools 36, Platform-tools `adb`)
- **PostgreSQL 17** atau **Docker Desktop**
- **GitHub CLI (`gh`)** (opsional namun disarankan)

---

## 2. Meng-clone Repository

Gunakan perintah clone via HTTPS atau SSH sesuai konfigurasi akun GitHub Anda:

```bash
# Clone repository private
git clone https://github.com/Abhiprayaa29/IPGuard.git

# Masuk ke direktori proyek
cd IPGuard
```

---

## 3. Menambahkan Anggota Tim (Collaborator)

Karena repository IPGuard bersifat **PRIVATE**, pemilik repository (`Abhiprayaa29`) perlu mengundang akun GitHub anggota tim:
1. Buka halaman repository di browser: `https://github.com/Abhiprayaa29/IPGuard`
2. Klik tab **Settings** (di pojok kanan atas).
3. Di panel navigasi sebelah kiri, pilih **Collaborators**.
4. Klik tombol hijau **Add people**.
5. Masukkan username GitHub atau alamat email anggota tim.
6. Pilih tingkat izin akses (**Write** / **Admin**).
7. Anggota tim akan menerima email undangan atau notifikasi di GitHub (`https://github.com/notifications`) dan harus menekan tombol **Accept invitation**.

---

## 4. Alur Kerja Percabangan (Branching Workflow)

Tim IPGuard menerapkan strategi percabangan berbasis fitur (*Feature Branching Workflow*). **Dilarang keras melakukan commit atau push langsung ke branch `main`!**

### A. Memulai Fitur Baru dari `main` Terbaru
Selalu pastikan branch `main` lokal Anda sinkron dengan remote sebelum membuat branch baru:

```bash
# Pindah ke branch main
git switch main

# Tarik perubahan terbaru dari GitHub
git pull origin main

# Buat branch fitur baru sesuai pekerjaan Anda
git switch -c feature/backend-device-enrollment
```

### B. Konvensi Penamaan Branch
Gunakan format penamaan branch yang jelas dan berorientasi peran:
- `feature/backend-device-enrollment` — Untuk endpoint pendaftaran public key di FastAPI.
- `feature/android-qr-challenge-signing` — Untuk pemindaian QR dan integrasi penandatanganan challenge M2.4.
- `feature/frontend-session-approval` — Untuk integrasi approval session polling di React.
- `fix/keystore-error-handling` — Untuk perbaikan bug atau penanganan error.
- `chore/update-dependencies` — Untuk pembaruan dependensi atau konfigurasi tooling.

---

## 5. Menjalankan Layanan Lokal (Local Run)

### A. Backend (FastAPI)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic -c alembic.ini upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Swagger UI: `http://localhost:8000/docs`

### B. Frontend (React)
```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```
Buka browser: `http://localhost:5173`

### C. Android Authenticator
```powershell
cd mobile-authenticator
.\gradlew.bat installDebug
adb shell am start -n com.ipguard.authenticator/.MainActivity
```

---

## 6. Aturan dan Disiplin Tim (Team Rules)

1. **Jangan Bekerja Langsung di `main`:** Semua perubahan kode harus melalui branch fitur.
2. **Satu Fitur Satu Branch:** Batasi cakupan perubahan branch hanya pada fitur atau perbaikan yang relevan.
3. **Pesan Commit yang Deskriptif:** Gunakan standar Conventional Commits:
   - `feat: implement QR challenge extraction in QrScannerScreen`
   - `fix: resolve null pointer on biometric prompt cancellation`
   - `docs: update API contract for device enrollment`
4. **Validasi Lokal Sebelum Push:** Jalankan test suite sebelum mem-push perubahan:
   - Backend: `pytest -v`
   - Frontend: `npm run typecheck && npm run build`
   - Android: `.\gradlew.bat testDebugUnitTest`
5. **Zero Secrets Policy:** Dilarang memasukkan file `.env`, file `local.properties`, private keys, atau credential apa pun ke dalam Git.
6. **Jangan Mengubah Kontrak API Tanpa Koordinasi:** Setiap perubahan pada skema Pydantic atau endpoint FastAPI harus dikoordinasikan dengan pengembang frontend dan mobile.
7. **Pull Request & Code Review:**
   - Setelah branch selesai, push ke remote: `git push -u origin feature/<nama-fitur>`.
   - Buka Pull Request ke branch `main` di GitHub.
   - PR wajib di-review minimal oleh satu rekan tim sebelum di-merge.
   - Gunakan opsi **Squash and merge** atau **Rebase and merge** untuk menjaga riwayat git tetap bersih.
