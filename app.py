from flask import Flask, render_template, request
import os, tempfile, zipfile, shutil, requests
from ftplib import FTP

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    if request.method == "POST":
        ip = request.form.get("ip", "192.168.0.2")
        url = request.form.get("url")

        try:
            tmpdir = tempfile.mkdtemp()
            zip_path = os.path.join(tmpdir, "chanlist.zip")

            r = requests.get(url, stream=True)
            if r.status_code != 200:
                raise Exception("Nie udało się pobrać pliku.")

            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(tmpdir)

            ftp = FTP(ip)
            ftp.login("root", "")

            ftp.cwd("/etc/enigma2")
            uploaded = []
            for fname in os.listdir(tmpdir):
                if fname.startswith("lamedb") or "bouquet" in fname:
                    with open(os.path.join(tmpdir, fname), "rb") as f:
                        ftp.storbinary(f"STOR {fname}", f)
                        uploaded.append(fname)

            ftp.quit()
            shutil.rmtree(tmpdir)

            message = f"Sukces: przesłano {len(uploaded)} plików do dekodera {ip}."
        except Exception as e:
            message = f"Błąd: {str(e)}"

    return render_template("index.html", message=message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
