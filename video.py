import os
import threading
import time
import pyfiglet
from pathlib import Path

# Konfigurasi Global
global letter, recoveredLocation, available_drives, total_iteration

class VideoRecovery:
    def __init__(self, filetype):
        self.filetype = filetype

    def DataRecovery(self, fileName, fileStart, fileEnd):
        self._fileName = fileName
        self._fileStart = fileStart
        self._fileEnd = fileEnd

        # Menggunakan jalur fisik untuk menembus proteksi Windows
        drive = f"\\\\.\\{letter}:"
        try:
            # Menaikkan buffer size ke 1MB untuk performa video yang besar
            size = 1024 * 1024 
            fileD = open(drive, "rb")
            offs = 0
            rcvd = 0

            print(f"[*] Scanning for {self._fileName}...")

            while True:
                byte = fileD.read(size)
                if not byte: break
                
                found = byte.find(self._fileStart)
                if found >= 0:
                    print(f'\n[!] Found {self._fileName} header at: ' + str(hex(found+(size*offs))))
                    
                    # Buat file baru
                    file_path = recoveredLocation / f"recovered_{rcvd}.{self._fileName}"
                    with open(file_path, "wb") as fileN:
                        fileN.write(byte[found:])
                        
                        # Terus membaca sampai menemukan footer atau batas ukuran (misal 500MB)
                        detecting = True
                        max_size = 500 * 1024 * 1024 # Batasan 500MB per video
                        current_video_size = 0
                        
                        while detecting and current_video_size < max_size:
                            v_byte = fileD.read(size)
                            if not v_byte: break
                            
                            bfind = v_byte.find(self._fileEnd)
                            if bfind >= 0:
                                fileN.write(v_byte[:bfind + len(self._fileEnd)])
                                print(f'---> Success: Saved to {file_path}')
                                detecting = False
                                rcvd += 1
                            else:
                                fileN.write(v_byte)
                                current_video_size += size
                offs += 1
            fileD.close()
        except PermissionError:
            print(f"\n[ERROR] Akses ditolak ke {letter}:. Pastikan RUN AS ADMINISTRATOR.")
        except Exception as e:
            print(f"\n[ERROR] Terjadi kesalahan: {e}")

# ... (Fungsi progress_bar tetap sama) ...

# Inisialisasi Drive dan Folder
available_drives = [chr(x) for x in range(65,91) if os.path.exists(chr(x) + ":")]
recoveredLocation = Path.cwd() / 'RecoveredVideos'
recoveredLocation.mkdir(exist_ok=True)

# Format Video (Common MP4/MOV signatures)
mp4 = VideoRecovery('mp4')
mov = VideoRecovery('mov')

while True:
    print(f"\nDrive tersedia: {available_drives}")
    letter = input("Masukkan Huruf Drive SD Card (contoh E) atau 'Exit': ").upper()
    
    if letter == "EXIT": break
    
    if len(letter) == 1 and letter in available_drives:
        # Thread 1: MP4 (Mencari atom 'ftyp')
        t1 = threading.Thread(target=mp4.DataRecovery, args=('mp4', b'\x00\x00\x00\x18\x66\x74\x79\x70', b'\x66\x72\x65\x65'))
        # Thread 2: MOV/Quicktime
        t2 = threading.Thread(target=mov.DataRecovery, args=('mov', b'\x00\x00\x00\x14\x66\x74\x79\x70', b'\x6d\x64\x61\x74'))
        
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        print("\n[✓] Proses Selesai. Cek folder RecoveredVideos.")
    else:
        print("Drive tidak valid!")