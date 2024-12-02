import threading
import cv2
import os
import face_recognition
import pickle
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from datetime import datetime
import winsound
import pyttsx3
import numpy as np

save_dir = "./faces"
log_file = "./attendance.log"
encodings_file = "./face_encodings_final"

if not os.path.exists(save_dir):
    os.makedirs(save_dir)

if os.path.exists(encodings_file):
    with open(encodings_file, "rb") as f:
        data = pickle.load(f)
else:
    data = {"encodings": [], "names": []}

cap = None

def save_encodings():
    with open(encodings_file, "wb") as f:
        pickle.dump(data, f)

def is_present_today(name):
    today_date = datetime.now().strftime('%Y-%m-%d')
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            for line in f:
                if line.startswith(name) and today_date in line:
                    return True
    return False

def save_attendance(name):
    if not is_present_today(name):
        with open(log_file, "a") as f:
            f.write(f"{name} - Present on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

def chk_face(frame):
    global face_match
    face_match = None
    try:
        imgS = cv2.resize(frame, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faces_cur_frame = face_recognition.face_locations(imgS)
        encodes_cur_frame = face_recognition.face_encodings(imgS, faces_cur_frame)

        for encode_face, face_loc in zip(encodes_cur_frame, faces_cur_frame):
            matches = face_recognition.compare_faces(data["encodings"], encode_face)
            face_dis = face_recognition.face_distance(data["encodings"], encode_face)
            match_index = np.argmin(face_dis) if len(face_dis) > 0 else None

            if match_index is not None and matches[match_index]:
                name = data["names"][match_index]
                face_match = name
                if not is_present_today(face_match):
                    save_attendance(face_match)
                    engine = pyttsx3.init()
                    rate = 100
                    engine.say(f"Hello {face_match}")
                    engine.setProperty('rate', rate)
                    winsound.Beep(1000, 200)
                    engine.runAndWait()
                break
    except Exception as e:
        face_match = None

def attendance_camera():
    global face_match, cap
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    counter = 0
    face_match = None

    while True:
        ret, frame = cap.read()
        cv2.putText(frame, "'Q' key to exit", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
        if ret:
            if counter % 60 == 0:
                threading.Thread(target=chk_face, args=(frame.copy(),)).start()
            counter += 1

            if face_match:
                cv2.putText(frame, f"{face_match} - Present", (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

            cv2.imshow("Face Recognition", frame)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def add_user():
    global cap
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    def update_frame():
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = cv2.resize(frame_rgb, (320, 240))
            img_pil = Image.fromarray(img)
            img_tk = ImageTk.PhotoImage(image=img_pil)
            label_img.imgtk = img_tk
            label_img.configure(image=img_tk)
        label_img.after(10, update_frame)

    def save_face():
        name = entry.get()
        if name:
            ret, frame = cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locs = face_recognition.face_locations(rgb_frame)
                if len(face_locs) > 0:
                    face_encoding = face_recognition.face_encodings(rgb_frame, face_locs)[0]
                    data["encodings"].append(face_encoding)
                    data["names"].append(name)
                    save_encodings()
                    messagebox.showinfo("Success", f"User {name} added successfully!")
                    cap.release()
                    window.destroy()
                else:
                    messagebox.showerror("Error", "No face detected. Try again.")
            else:
                messagebox.showerror("Error", "Failed to capture image.")
        else:
            messagebox.showwarning("Input Error", "Please enter a name.")

    window = tk.Toplevel()
    window.title("Add User")
    window.geometry("400x300")
    window.configure(bg="#f0f8ff")

    tk.Label(window, text="Enter Full Name:", font=("Helvetica", 12), bg="#f0f8ff").pack(pady=10)
    entry = tk.Entry(window, font=("Helvetica", 12))
    entry.pack(pady=5)
    tk.Button(window, text="Capture", command=save_face, font=("Helvetica", 12), bg="#4CAF50", fg="white").pack(pady=10)

    label_img = tk.Label(window, bg="#f0f8ff")
    label_img.pack(pady=10)

    update_frame()

def attendance_logs():
    log_window = tk.Toplevel()
    log_window.title("Attendance Logs")
    log_window.geometry("600x400")

    tree = ttk.Treeview(log_window, columns=("Name", "Timestamp"), show='headings')
    tree.heading("Name", text="Name")
    tree.heading("Timestamp", text="Timestamp")
    tree.column("Name", anchor="center")
    tree.column("Timestamp", anchor="center")

    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            for line in f:
                name, timestamp = line.strip().split(" - Present on ")
                tree.insert("", "end", values=(name, timestamp))

    tree.pack(expand=True, fill='both')
    scrollbar = ttk.Scrollbar(log_window, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side='right', fill='y')

def on_closing():
    global cap
    if cap is not None:
        cap.release()
    root.destroy()

def main_menu():
    global root
    root = tk.Tk()
    root.iconbitmap("./facey.ico")
    root.title("Facey")
    root.geometry("400x300")
    root.configure(bg="#f0f8ff")

    tk.Label(root, text="Face Recognition Attendance System", font=("Helvetica", 16), bg="#f0f8ff").pack(pady=20)

    tk.Button(root, text="Attendance Camera", command=attendance_camera, width=30, font=("Helvetica", 12), bg="#2196F3", fg="white").pack(pady=5)
    tk.Button(root, text="Add User", command=add_user, width=30, font=("Helvetica", 12), bg="#FF9800", fg="white").pack(pady=5)
    tk.Button(root, text="Attendance Logs", command=attendance_logs, width=30, font=("Helvetica", 12), bg="#9C27B0", fg="white").pack(pady=5)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main_menu()