from flask import Flask, render_template, request, send_file
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/compress", methods=["GET", "POST"])
def compress():
    if request.method == "POST":
        file = request.files["pdf_file"]
        file.save("input.pdf")

        os.system("gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH -sOutputFile=output.pdf input.pdf")

        return send_file("output.pdf", as_attachment=True)

    return render_template("Compress-tool.html")
