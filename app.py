from flask import Flask, render_template, request, jsonify
from dataclasses import dataclass
import os, json
from datetime import datetime

app = Flask(__name__)

# Lokasi file JSON untuk menyimpan histori
HISTORY_FILE = 'data/history.json'

@dataclass
class Tugas:
    nama: str
    deadline: int
    skor_prioritas: int
    difficulty: int = 0

# Algoritma Greedy
def greedy_penjadwalan(tugas_list, waktu_luang):
    tugas_list.sort(key=lambda t: (t.deadline, -t.skor_prioritas, t.nama))
    hasil, waktu_dipakai, total_skor = [], 0, 0
    for tugas in tugas_list:
        if waktu_dipakai < waktu_luang:
            hasil.append(tugas)
            waktu_dipakai += 1
            total_skor += tugas.skor_prioritas
    return hasil, total_skor

# Algoritma Backtracking
def backtracking_penjadwalan(tugas_list, waktu_luang):
    n, solusi_terbaik, skor_maks = len(tugas_list), [], [0]

    def backtrack(i, waktu_terpakai, skor_saat_ini, solusi_sementara):
        if waktu_terpakai > waktu_luang:
            return
        if i == n:
            if skor_saat_ini > skor_maks[0]:
                skor_maks[0] = skor_saat_ini
                solusi_terbaik.clear()
                solusi_terbaik.extend(solusi_sementara)
            return
        backtrack(i + 1, waktu_terpakai + 1, skor_saat_ini + tugas_list[i].skor_prioritas, solusi_sementara + [tugas_list[i]])
        backtrack(i + 1, waktu_terpakai, skor_saat_ini, solusi_sementara)

    backtrack(0, 0, 0, [])
    return solusi_terbaik, skor_maks[0]

# Load histori dari file JSON
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

# Simpan histori ke file
def save_history(data):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/schedule', methods=['POST'])
def schedule():
    data = request.get_json()
    tasks = data.get('tasks', [])
    method = data.get('method', 'greedy')
    nama_mahasiswa = data.get('nama_mahasiswa', '-').strip() or '-'

    tugas_list = [Tugas(
        t['name'],
        int(t['deadline']),
        int(t['priority']),
        int(t.get('difficulty', 0))
    ) for t in tasks]

    if method == 'greedy':
        hasil, skor = greedy_penjadwalan(tugas_list, len(tasks))
    else:
        hasil, skor = backtracking_penjadwalan(tugas_list, len(tasks))
        # Urutkan berdasarkan deadline agar tampil rapi
        hasil.sort(key=lambda t: (t.deadline, -t.skor_prioritas))

    hasil_json = [{
        'name': t.nama,
        'deadline': t.deadline,
        'priority': t.skor_prioritas,
        'difficulty': t.difficulty
    } for t in hasil]

    riwayat = load_history()
    riwayat.insert(0, {
        'method': method,
        'result': hasil_json,
        'score': skor,
        'time': datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
        'nama_mahasiswa': nama_mahasiswa
    })
    save_history(riwayat)

    return jsonify({
        'scheduled': hasil_json,
        'total_score': skor,
        'nama_mahasiswa': nama_mahasiswa
    })

@app.route('/history')
def get_history():
    return jsonify(load_history())

@app.route('/delete-history/<int:index>', methods=['DELETE'])
def delete_history(index):
    data = load_history()
    if 0 <= index < len(data):
        del data[index]
        save_history(data)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Index tidak valid'})

if __name__ == '__main__':
    app.run(debug=True, port=5050)
