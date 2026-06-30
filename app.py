import io
import os
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from rembg import remove, new_session
from PIL import Image

app = Flask(__name__)
CORS(app)  # allow all origins; restrict via origins= if needed

MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}

# u2netp = lightweight model (~5MB vs ~176MB), fits free tier RAM (512MB)
SESSION = new_session("u2netp")


@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "service": "voidcut-bg-remover"}), 200


@app.route("/remove-bg", methods=["POST"])
def remove_bg():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided. Use form field 'image'."}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    if file.mimetype not in ALLOWED_MIME_TYPES:
        return jsonify({"error": f"Unsupported file type: {file.mimetype}"}), 400

    try:
        input_bytes = file.read()

        # Validate it's a real image before passing to rembg
        try:
            Image.open(io.BytesIO(input_bytes)).verify()
        except Exception:
            return jsonify({"error": "Uploaded file is not a valid image."}), 400

        output_bytes = remove(input_bytes, session=SESSION)

        return send_file(
            io.BytesIO(output_bytes),
            mimetype="image/png",
            as_attachment=False,
            download_name="result.png",
        )

    except Exception as e:
        app.logger.exception("Background removal failed")
        return jsonify({"error": "Failed to process image.", "details": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
