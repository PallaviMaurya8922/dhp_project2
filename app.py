from flask import Flask, render_template, request, redirect, url_for
from PIL import Image, ImageEnhance, ImageDraw, ImageFont, ImageFilter
import io
import base64
import os
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/result', methods=['POST','GET'])
def result():
    return render_template('result.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'image' not in request.files:
            return redirect(url_for('index'))

        image = request.files['image']

        if image.filename == '':
            return redirect(url_for('index'))

        user_img = Image.open(image).convert("RGBA")

        filters = request.form.getlist('filters[]')

        if 'crop' in filters:
            left = int(request.form['left'])
            upper = int(request.form['upper'])
            right = int(request.form['right'])
            lower = int(request.form['lower'])
            user_img = user_img.crop((left, upper, right, lower))

        if 'rotate' in filters:
            angle = int(request.form['angle'])
            user_img = user_img.rotate(angle)

        if 'blur' in filters:
            user_img = user_img.filter(ImageFilter.BLUR)

        if 'brightness' in filters:
            brightness = float(request.form['brightness'])
            enhancer = ImageEnhance.Brightness(user_img)
            user_img = enhancer.enhance(brightness)

        if 'markup' in filters:
            draw = ImageDraw.Draw(user_img)
            text = request.form['text']
            position = (int(request.form['x']), int(request.form['y']))
            font_size = int(request.form['font_size'])
            font_style = request.form['font_style']
            font_color = request.form['font_color']

            font = ImageFont.truetype(font_style, font_size)
            draw.text(position, text, fill=font_color, font=font)

        # Check if 'use_celebrity' checkbox is selected
        if 'use_celebrity' in request.form and request.form['use_celebrity'] == 'yes':
            celebrity_url = request.form['celebrity']

            try:
                response = requests.get(celebrity_url)
                celebrity_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
            except Exception as e:
                print(f"Error occurred while fetching or opening celebrity image: {e}")
                return "Error: Failed to fetch or open celebrity image", 500

            user_width = int((celebrity_img.height / user_img.height) * user_img.width)
            user_img = user_img.resize((user_width, celebrity_img.height), Image.LANCZOS)

            combined_width = celebrity_img.width + user_img.width
            combined_height = max(celebrity_img.height, user_img.height)
            combined_img = Image.new('RGBA', (combined_width, combined_height))

            combined_img.paste(celebrity_img, (0, (combined_height - celebrity_img.height) // 2))
            combined_img.paste(user_img, (celebrity_img.width, (combined_height - user_img.height) // 2))

            combined_img = combined_img.convert("RGB")

            img_io = io.BytesIO()
            combined_img.save(img_io, 'JPEG')
            img_io.seek(0)
            img_base64 = base64.b64encode(img_io.getvalue()).decode()

            return render_template('edited.html', image_data=img_base64)
        else:
            img_io = io.BytesIO()
            user_img = user_img.convert("RGB")
            user_img.save(img_io, 'JPEG')
            img_io.seek(0)
            img_base64 = base64.b64encode(img_io.getvalue()).decode()

            return render_template('edited.html', image_data=img_base64)

    except Exception as e:
        print(f"Error occurred: {e}")
        return "An error occurred while processing the image", 500

if __name__ == '__main__':
    app.run(debug=True)
