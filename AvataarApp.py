import sys
import pyttsx3
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QFileDialog
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer
from PIL import Image
from io import BytesIO

class AvatarApp(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize Text-to-Speech engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Speed of the speech

        # Set up the UI
        self.setWindowTitle("Interactive Avatar and Text-to-Speech App")
        self.setGeometry(100, 100, 600, 500)

        self.avatar_image = None  # Placeholder for the avatar image
        self.avatar_pixmap = None  # Displayed pixmap for the avatar
        self.avatar_pil_image = None  # PIL image for manipulation
        self.moustache_image = None  # Placeholder for the moustache image
        self.beard_image = None  # Placeholder for the beard image
        self.goggles_image = None  # Placeholder for the goggles image

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Image area for displaying the avatar
        self.avatar_label = QLabel(self)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setText("No avatar uploaded")
        layout.addWidget(self.avatar_label)

        # Upload Avatar Button
        self.upload_btn = QPushButton("Upload Avatar", self)
        self.upload_btn.clicked.connect(self.upload_avatar)
        layout.addWidget(self.upload_btn)

        # Moustache Button
        self.moustache_btn = QPushButton("Add Moustache", self)
        self.moustache_btn.clicked.connect(self.add_moustache)
        layout.addWidget(self.moustache_btn)

        # Beard Button
        self.beard_btn = QPushButton("Add Beard", self)
        self.beard_btn.clicked.connect(self.add_beard)
        layout.addWidget(self.beard_btn)

        # Goggles Button
        self.goggles_btn = QPushButton("Wear Goggles", self)
        self.goggles_btn.clicked.connect(self.add_goggles)  # Adding the event for goggles button
        layout.addWidget(self.goggles_btn)

        # Text Input for Avatar
        self.text_input = QLineEdit(self)
        self.text_input.setPlaceholderText("Enter text here...")
        layout.addWidget(self.text_input)

        # Read Text Button
        self.read_btn = QPushButton("Read Text", self)
        self.read_btn.clicked.connect(self.read_text)
        layout.addWidget(self.read_btn)

        # Set the layout
        self.setLayout(layout)

        # Timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_avatar)
        self.timer.start(100)

        self.x_pos = 0  # Initial position for animation
        self.y_pos = 0

        # Load images for moustache, beard, and goggles from URLs
        self.load_images_from_urls()

    def load_images_from_urls(self):
        # Replace these with your actual local file paths or URLs for moustache, beard, and goggles images
        self.moustache_image = 'moustache.png'
        self.beard_image = 'beard.png'
        self.goggles_image = 'goggles.png'

    def upload_avatar(self):
        # Open file dialog to select an image
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Avatar Image", "", "Image Files (*.png *.jpg *.bmp)", options=options)
        
        if file_path:
            # Display the uploaded image as avatar
            self.avatar_pil_image = Image.open(file_path)
            self.avatar_pixmap = QPixmap(file_path).scaled(150, 150, Qt.KeepAspectRatio)

            self.avatar_label.setPixmap(self.avatar_pixmap)
            self.avatar_label.setText("")  # Clear default text

            # Load OpenCV Haar cascades for facial detection
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.nose_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_mcs_nose.xml')

    def add_moustache(self):
        if self.avatar_pil_image and self.moustache_image:
            # Detect face and place the moustache just below the nose
            self.overlay_face_feature(self.moustache_image, 'moustache')
            self.update_avatar_display()

    def add_beard(self):
        if self.avatar_pil_image and self.beard_image:
            # Detect face and place the beard just below the chin
            self.overlay_face_feature(self.beard_image, 'beard')
            self.update_avatar_display()

    def add_goggles(self):
        if self.avatar_pil_image and self.goggles_image:
            # Detect face and place the goggles over the eyes region
            self.overlay_face_feature(self.goggles_image, 'goggles')
            self.update_avatar_display()

    def overlay_face_feature(self, overlay_image, feature_type):
        # Convert avatar image to OpenCV format (BGR)
        avatar_cv = np.array(self.avatar_pil_image)
        avatar_cv = avatar_cv[:, :, ::-1].copy()  # Convert to BGR
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(avatar_cv, cv2.COLOR_BGR2GRAY)

        # Detect faces in the image
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) == 0:
            return  # No faces detected, return early
        
        for (x, y, w, h) in faces:
            # Get region of interest (ROI) for placing the feature (based on type)
            roi = avatar_cv[y:y + h, x:x + w]
            
            if feature_type == 'moustache':
                # Place the moustache just below the nose region
                self.place_overlay(overlay_image, roi, x, y, w, h, 'moustache')
            
            elif feature_type == 'beard':
                # Place the beard just below the chin region
                self.place_overlay(overlay_image, roi, x, y, w, h, 'beard')

            elif feature_type == 'goggles':
                # Place the goggles over the eyes
                self.place_overlay(overlay_image, roi, x, y, w, h, 'goggles')

    def place_overlay(self, overlay_image, roi, x, y, w, h, feature_type):
        # Open the overlay image
        overlay = Image.open(overlay_image).convert("RGBA")
        overlay_width, overlay_height = overlay.size

        if feature_type == 'moustache':
            # Place the moustache just below the nose region
            nose_region = roi[int(h * 0.3):int(h * 0.45), int(w * 0.3):int(w * 0.7)]
            overlay = overlay.resize((nose_region.shape[1], int(nose_region.shape[0] * 0.4)))
            self.avatar_pil_image.paste(overlay, (x + int(w * 0.25), y + int(h * 0.3)), overlay)
        
        elif feature_type == 'beard':
            # Place the beard just below the chin region
            beard_region = roi[int(h * 0.6):int(h * 0.8), int(w * 0.2):int(w * 0.8)]
            overlay = overlay.resize((beard_region.shape[1], int(beard_region.shape[0] * 0.6)))
            self.avatar_pil_image.paste(overlay, (x + int(w * 0.2), y + int(h * 0.6)), overlay)
        
        elif feature_type == 'goggles':
            # Place the goggles over the eyes
            eyes_region = roi[int(h * 0.2):int(h * 0.4), int(w * 0.3):int(w * 0.7)]
            overlay = overlay.resize((eyes_region.shape[1], int(eyes_region.shape[0] * 0.4)))
            self.avatar_pil_image.paste(overlay, (x + int(w * 0.3), y + int(h * 0.2)), overlay)

    def update_avatar_display(self):
        # Update the QPixmap to show the modified image
        modified_image = self.avatar_pil_image.convert("RGB")
        modified_image.save("modified_avatar.png")  # Save as temp file
        self.avatar_pixmap = QPixmap("modified_avatar.png").scaled(150, 150, Qt.KeepAspectRatio)
        self.avatar_label.setPixmap(self.avatar_pixmap)

    def read_text(self):
        text = self.text_input.text()
        if text:
            # Speak the entered text
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            self.avatar_label.setText("Please enter some text.")

    def animate_avatar(self):
        if self.avatar_pixmap:
            # Move the avatar image (simple animation by changing the position)
            self.x_pos += 5
            if self.x_pos > self.width():
                self.x_pos = 0  # Reset position once it moves off-screen

            self.avatar_label.setPixmap(self.avatar_pixmap)
            self.avatar_label.move(self.x_pos, self.y_pos)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = AvatarApp()
    ex.show()

    sys.exit(app.exec_())
