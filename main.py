from flask import Flask, render_template, request, send_file
from openai import OpenAI
from pathlib import Path
import json
from fpdf import FPDF
import requests
import io
import firebase_admin
from firebase_admin import credentials, storage
import math
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy.video.VideoClip import ImageClip
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage   # <-- Add this
from email import encoders
import tkinter as tk
from tkinter import messagebox

app = Flask(__name__)
cred = credentials.Certificate("firebase-key.json")  # your service account key
firebase_admin.initialize_app(cred, {
    'storageBucket': 'ruya-8ccf1.firebasestorage.app'   # replace with your bucket
})
speech_file_path = Path(__file__).parent / "speech.mp3"
speech_file_path2 = Path(__file__).parent / "flipbookspeech.mp3"

meditation_entries = []
feedback_list = []

@app.route('/')
def home():
    smtp_host = "smtp.gmail.com"  # Use your email provider's SMTP server
    smtp_port = 587  # Standard port for sending email (587 for TLS)
    email_user = "daliahqzidan@gmail.com"  # Your email address
    email_password = "gpqs umkb xmgl siud"  # Your email password or app-specific password

    sender_email = "daliahqzidan@gmail.com"  # Your email address
    receiver_email = "daliaruyahackathon@gmail.com"  # Recipient's email address
    subject = "REMINDER: Fill out your journal entry today!"
    body = f"Dalia, this is a quick reminder to fill out your journal entry for today. You rock!"

    # Create a multipart message and set headers
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain'))
    try:
        # Establish a connection with the server
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(email_user, email_password)

        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("Email sent successfully!")
        server.quit()
    except Exception as e:
        print(f"Error: {e}")
    return render_template('index.html')

@app.route('/meditation', methods=['POST', 'GET'])
def meditation():
    voice = ""
    if request.method == 'POST':
        voice = request.form['voice']
        if voice == "male":
            voice = "onyx"
        else:
            voice = "coral"
        desc = request.form['description']
        duration = int(request.form['duration'])
        response = client.responses.create(
            model="gpt-5",
            input=f"Please create a short meditation script catering to fit the user's desc: {desc}. Make sure the script is around {duration} seconds and is VERY personalized."
        )

        script = response.output_text
        with client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                input=f"{script}",
                instructions=f"Speak in a calm, relaxing manner. Make sure you speak within {duration} seconds.",
        ) as response:
            response.stream_to_file(speech_file_path)
            meditation_audio_path = "./speech.mp3"
            background_music_path = "./background_music2.mp3"
            image_path = "./calming_image.webp"
            output_video_path = "./output_video.mp4"

            # Load audio clips
            meditation_audio = AudioFileClip(meditation_audio_path)
            background_audio = AudioFileClip(background_music_path)

            # Mix audio
            final_audio = CompositeAudioClip([
                background_audio.with_duration(meditation_audio.duration),
                meditation_audio
            ])

            # Create video from image
            video_clip = ImageClip(image_path).with_duration(meditation_audio.duration)
            video_clip = video_clip.with_audio(final_audio)

            # Export video
            video_clip.write_videofile(
                output_video_path,
                fps=1,  # one frame per second is enough for a static image
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                ffmpeg_params=["-pix_fmt", "yuv420p"]
            )
        # SMTP setup
        def show_notification(title, message, is_success=True):
            """Try multiple methods to show notification"""
            print(f"\n{'=' * 50}")
            print(f"{title}: {message}")
            print('=' * 50)

            # Method 1: Try tkinter
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                root.lift()  # Bring to front
                root.attributes('-topmost', True)  # Keep on top

                if is_success:
                    messagebox.showinfo(title, message)
                else:
                    messagebox.showerror(title, message)
                root.destroy()
                print("✓ Popup notification shown!")
                return True
            except Exception as e:
                print(f"✗ Tkinter popup failed: {e}")

            # Method 2: Try system notification (Windows)
            try:
                import win10toast
                toaster = win10toast.ToastNotifier()
                toaster.show_toast(title, message, duration=5)
                print("✓ Windows toast notification shown!")
                return True
            except:
                pass

            # Method 3: Try plyer (cross-platform)
            try:
                from plyer import notification
                notification.notify(
                    title=title,
                    message=message,
                    timeout=10
                )
                print("✓ System notification shown!")
                return True
            except:
                pass

            # Method 4: Console notification with sound
            try:
                import os
                print("\a")  # System beep
                if os.name == 'nt':  # Windows
                    os.system('echo \a')
                print("✓ Console notification with beep!")
                return True
            except:
                pass

            print("✗ All notification methods failed - check console output above")
            return False

        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        email_user = "daliahqzidan@gmail.com"
        email_password = "gpqs umkb xmgl siud"

        # Email details
        sender_email = "daliahqzidan@gmail.com"
        receiver_email = "daliaruyahackathon@gmail.com"
        subject = "Meditation Audio"

        # Create a multipart message
        msg = MIMEMultipart("related")  # "related" allows inline images
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Create the alternative part (plain text + HTML)
        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)

        # Plain text version (fallback)
        text = "Hi Dalia! Here is your meditation audio"
        msg_alternative.attach(MIMEText(text, 'plain'))

        # HTML version with inline image reference
        html = """
        <html>
          <body>
            <img src="cid:image1" width="200" height="200">
            <h1><strong>JournalAId</strong></h1>
            <br/>
            <p>Hi Dalia! Here is your meditation audio!🌟</p>
          </body>
        </html>
        """
        msg_alternative.attach(MIMEText(html, 'html'))

        # Attach the inline image
        try:
            with open("./logo.png", "rb") as img_file:
                img = MIMEImage(img_file.read())
                img.add_header("Content-ID", "<image1>")
                img.add_header("Content-Disposition", "inline", filename="./logo.png")
                msg.attach(img)
                print("✓ Logo attached successfully")
        except FileNotFoundError:
            print("✗ Warning: logo.png not found, email will be sent without logo")

        # Attach your audio/video as a normal file
        attachment_file_path = "./output_video.mp4"
        try:
            with open(attachment_file_path, "rb") as attachment_file:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment_file.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={attachment_file_path.split('/')[-1]}")
                msg.attach(part)
                print("✓ Video attachment added successfully")
        except FileNotFoundError:
            print("✗ Warning: output_video.mp4 not found, email will be sent without attachment")

        # Send email
        server = None
        try:
            print("\n📧 Starting email process...")
            print("🔗 Connecting to SMTP server...")
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()

            print("🔐 Logging in...")
            server.login(email_user, email_password)

            print("📤 Sending email...")
            server.sendmail(sender_email, receiver_email, msg.as_string())

            print("✅ Email sent successfully!")
            show_notification("Success", "Email sent successfully! 🎉\n\nYour meditation audio has been delivered.",
                              True)

        except Exception as e:
            print(f"❌ Error occurred: {e}")
            show_notification("Email Error", f"Failed to send email:\n{str(e)}", False)
        finally:
            if server:
                try:
                    server.quit()
                    print("🔒 SMTP connection closed.")
                except:
                    pass

        print("\n🏁 Script completed.")
    return render_template('meditation.html')

@app.route('/journal', methods=['GET', 'POST'])
def journal():
    analysis_text = ""
    summary = client.responses.create(
        model="gpt-5",
        input=f"""Based off of the users' meditation entries: {meditation_entries}, please give an overall overview of the users mood and how they have improved over the last couple of days and what feedback they have given. Don't make it too long. Make it relatively short! If the meditation entries var is empty, just say "For analysis to be generated, more meditation entries are needed.''"""
    )
    if request.method == 'POST':
        entry = request.form['entry']
        meditation_entries.append(entry)
        response = client.responses.create(
            model="gpt-5",
            input=f"""Based on the description the user provided, give them comforting words. Please keep in mind the users' previous feedback: {feedback_list}. Here is their desc of what they're struggling with: {entry}
                        Please tailor your response exactly to what they are saying. Also, provide a list of suggestions for what they could do. Additionally, if the meditiation_entries variable is not empty, please make sure your response keeps in mind the users' previous responses. Here is the var: {meditation_entries}.
                        Also, include a summary of what the user has said. Make sure the suggestions you are coming up with are
                        UNIQUE and innovative. The response should be innovative too. Just give 3 suggestions ONLY!! NO MORE THAN 3. They should be short. Don't ask the user to give more responses or anything, just give comforting words very personalized based off of their problems.

                        Store your response in JSON format like:
                          "response": "Intro and comforting words...",
                          "suggestions": ["Suggestion 1", "Suggestion 2", "Suggestion 3"],
                          "summary": "Summary of what the user said, please note if they are feeling better or worse.

                        If the user's feedback variable is not empty, ensure that your response takes their feedback into account."""
        )
        analysis_text = json.loads(response.output_text)
        print(analysis_text)
    return render_template('journal.html', text=analysis_text, summary=summary.output_text)

@app.route('/flipbook', methods=['GET', 'POST'])
def generator():
    final_script = ""
    if request.method == 'POST':
        flipbook_desc = request.form['flipbook_desc']
        language = request.form['language']
        length = int(request.form['length'])

        completion = client.chat.completions.create(
            model="gpt-5",
            response_format={"type": "json_object"},
            messages=[
                {"role": "developer", "content": f"""Generate a very interesting, engaging script about {flipbook_desc}. Make sure 
                           that the text you generate is in a JSON form that follows: {{"page1": {{"text1": "...", "text2": "..."}}, "page2": {{"text1": "...", "text2": "..."}}}}. . I
                           want this text to go onto different pages of a flipbook. Do NOT say anything else
                           or give a response before or after the script. Make it {length} pages. Please translate the text you create to {language} and make the script about {length} pages
                           length.""",
                 }
            ]
        )

        pdf = FPDF()
        script = completion.choices[0].message.content
        script = json.loads(script)

        pdf.add_font('DejaVu', '', "DejaVuSerif-BoldItalic.ttf", uni=True)
        pdf.set_auto_page_break(False)  # control layout manually
        pdf.set_margins(0, 0, 0)

        count = 0
        for page in script:
            final_script = " " + script[page]['text2']
            count += 1
            body = script[page]['text2']

            # --- keep image generation unchanged ---
            img = client.images.generate(
                prompt=f"Elegant illustration about the subject that talks about {flipbook_desc}. Like mathematics, english, etc. hen generating an image for the user you will always create an image devoid of text.",
                n=1,
                size="1024x1024"
            )
            image_url = img.data[0].url
            img_data = requests.get(image_url).content
            img_path = f'./static/images/image{count}.png'
            with open(img_path, 'wb') as handler:
                handler.write(img_data)

            # --- new page ---
            pdf.add_page()

            # Background: soft top band + subtle full-page tint
            pdf.set_fill_color(248, 250, 255)  # very light base
            pdf.rect(0, 0, pdf.w, pdf.h, 'F')
            pdf.set_fill_color(235, 244, 255)  # top band
            pdf.rect(0, 0, pdf.w, 120, 'F')


            # Image area: shadow + white backdrop + bordered frame (keeps your image)
            img_w = pdf.w - 80
            img_h = img_w * 0.65
            x_img = (pdf.w - img_w) / 2
            y_img = 80

            # subtle shadow
            pdf.set_fill_color(230, 230, 235)
            pdf.rect(x_img + 4, y_img + 6, img_w, img_h, 'F')

            # white panel behind image
            pdf.set_fill_color(255, 255, 255)
            pdf.rect(x_img, y_img, img_w, img_h, 'F')

            # thin border
            pdf.set_draw_color(210, 210, 215)
            pdf.set_line_width(0.6)
            pdf.rect(x_img, y_img, img_w, img_h)

            # place the actual image slightly inset
            inset = 6
            pdf.image(img_path, x=x_img + inset, y=y_img + inset,
                      w=img_w - 2 * inset, h=img_h - 2 * inset)

            # Body text panel (dynamic height based on text length)
            pdf.set_font('DejaVu', '', 14)
            pdf.set_text_color(50, 50, 50)

            # approximate chars per line (using current font metrics)
            char_w = pdf.get_string_width('a') or 4.0
            usable_w = pdf.w - 70
            chars_per_line = max(20, int(usable_w / char_w))
            lines_needed = math.ceil(len(body) / max(1, chars_per_line))
            line_h = 7
            box_h = max(60, lines_needed * line_h + 16)

            y_body = y_img + img_h + 18
            x_body = 35
            w_body = pdf.w - 70

            # body background panel (white) with subtle border
            pdf.set_fill_color(255, 255, 255)
            pdf.set_draw_color(220, 220, 220)
            pdf.rect(x_body, y_body, w_body, box_h, 'F')  # filled
            pdf.rect(x_body, y_body, w_body, box_h)  # border

            # text inside panel (centered, nicely padded)
            pdf.set_xy(x_body + 12, y_body + 10)
            pdf.multi_cell(w_body - 24, line_h, body, align='C')

            # soft footer (page number and small brand line)
            pdf.set_font('DejaVu', '', 11)
            pdf.set_text_color(130, 130, 140)
            pdf.set_xy(0, pdf.h - 22)
            pdf.cell(pdf.w, 8, f"Page {count}", align='C')
            pdf.set_xy(12, pdf.h - 12)
            pdf.cell(pdf.w - 24, 8, "Created with ♥ by The Visionaries", align='R')
        # ---------- end improved page design ----------
        pdf.output("finalsample.pdf")
        local_pdf_path = "finalsample.pdf"
        bucket = storage.bucket()
        blob = bucket.blob(f"flipbooks/finalsample.pdf")
        blob.upload_from_filename(local_pdf_path)
        blob.make_public()

        firebase_url = blob.public_url
        with client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice="onyx",
                input=f"{final_script}",
                instructions=f"Speak in a calm, relaxing manner.",
        ) as response:
            response.stream_to_file(speech_file_path2)

        client_id = "1132144d3321cb0b"
        response = requests.get(f"https://heyzine.com/api1?pdf={firebase_url}&k={client_id}&t=Math")
        url = response.url

        def show_notification(title, message, is_success=True):
            """Try multiple methods to show notification"""
            print(f"\n{'=' * 50}")
            print(f"{title}: {message}")
            print('=' * 50)

            # Method 1: Try tkinter
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                root.lift()  # Bring to front
                root.attributes('-topmost', True)  # Keep on top

                if is_success:
                    messagebox.showinfo(title, message)
                else:
                    messagebox.showerror(title, message)
                root.destroy()
                print("✓ Popup notification shown!")
                return True
            except Exception as e:
                print(f"✗ Tkinter popup failed: {e}")

            # Method 2: Console notification with sound
            try:
                import os
                print("\a")  # System beep
                if os.name == 'nt':  # Windows
                    os.system('echo \a')
                print("✓ Console notification with beep!")
                return True
            except:
                pass

            print("✗ All notification methods failed - check console output above")
            return False

        # Email configuration
        smtp_host = "smtp.gmail.com"  # Use your email provider's SMTP server
        smtp_port = 587  # Standard port for sending email (587 for TLS)
        email_user = "daliahqzidan@gmail.com"  # Your email address
        email_password = "gpqs umkb xmgl siud"  # Your email password or app-specific password

        # Email details
        sender_email = "daliahqzidan@gmail.com"  # Your email address
        receiver_email = "daliaruyahackathon@gmail.com"  # Recipient's email address
        subject = "Mental Health Flipbook"

        # You'll need to define the URL variable
        url = "https://your-flipbook-url.com"  # Replace with your actual URL

        body = f"You rock! Here is the url to your customized flipbook: {url}. The audio has also been attached! "
        attachment_file_path = "./flipbookspeech.mp3"  # Specify the full path to your file

        # Create a multipart message
        msg = MIMEMultipart("related")  # "related" allows inline images
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Create the alternative part (plain text + HTML)
        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)

        # Plain text version (fallback)
        text = "Hi Dalia! Here is the link to your flipbook!"
        msg_alternative.attach(MIMEText(text, 'plain'))

        # HTML version with inline image reference
        html = f"""
            <html>
              <body>
                <img src="cid:image1" width="200" height="200">
                <h1><strong>JournalAId</strong></h1>
                <br/>
                <p>Hi Dalia! Here is the link to your flipbook!🌟</p>
                <p><a href="{url}">{url}</a></p>
              </body>
            </html>
            """
        msg_alternative.attach(MIMEText(html, 'html'))

        # Attach the inline image
        try:
            with open("./logo.png", "rb") as img_file:
                img = MIMEImage(img_file.read())
                img.add_header("Content-ID", "<image1>")
                img.add_header("Content-Disposition", "inline", filename="./logo.png")
                msg.attach(img)
                print("✓ Logo attached successfully")
        except FileNotFoundError:
            print("✗ Warning: logo.png not found, email will be sent without logo")

        # Attach the audio file (FIXED - this was missing from your original code)
        try:
            with open(attachment_file_path, "rb") as attachment_file:
                # Create MIMEBase object
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment_file.read())  # Read the file and encode it
                encoders.encode_base64(part)  # Encode the file in base64

                # Add header with filename (THIS WAS MISSING!)
                part.add_header("Content-Disposition", f"attachment; filename={attachment_file_path.split('/')[-1]}")
                msg.attach(part)  # Attach to message (THIS WAS MISSING!)
                print("✓ Audio attachment added successfully")
        except FileNotFoundError:
            print("✗ Warning: flipbookspeech.mp3 not found, email will be sent without audio attachment")

        # Send email
        server = None
        try:
            print("\n📧 Starting email process...")
            print("🔗 Connecting to SMTP server...")
            # Establish a connection with the server
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()

            print("🔐 Logging in...")
            server.login(email_user, email_password)

            print("📤 Sending email...")
            # Send email
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)

            print("✅ Email sent successfully!")
            show_notification("Success",
                              f"Flipbook email sent successfully! 🎉\n\nYour flipbook has been delivered to {receiver_email}",
                              True)

        except Exception as e:
            print(f"❌ Error occurred: {e}")
            show_notification("Email Error", f"Failed to send flipbook email:\n{str(e)}", False)
        finally:
            if server:
                try:
                    server.quit()
                    print("🔒 SMTP connection closed.")
                except:
                    pass

        print("\n🏁 Script completed.")
    return render_template('generator.html')

if __name__ == "__main__":
    app.run(debug=True)
