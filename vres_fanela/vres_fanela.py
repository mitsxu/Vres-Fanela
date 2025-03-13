import time
import smtplib
from email.message import EmailMessage
import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from playsound import playsound
from slack_sdk import WebClient
import threading
import pygame

# --- Ρυθμίσεις email ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = ""  
EMAIL_PASSWORD = ""  

# --- Ρυθμίσεις slack ---
SLACK_TOKEN = ""

# --- Λίστα μεγεθών ---
SIZES = ["LARGE", "MEDIUM","XLARGE"]

class StockCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vres Fanela")
        self.root.geometry("300x300")

        try:
            self.root.iconphoto(False, tk.PhotoImage(file="logo.png"))
        except:
            print("⚠️ Δεν βρέθηκε εικόνα εικονιδίου.")

        tk.Label(root, text="Επιλέξτε Μέγεθος:").pack(pady=5)
        self.size_var = tk.StringVar(value="SMALL")
        self.size_menu = tk.OptionMenu(root, self.size_var, *SIZES)
        self.size_menu.pack()

        tk.Label(root, text="Email (προαιρετικά):").pack(pady=5)
        self.email_entry = tk.Entry(root, width=30)
        self.email_entry.pack()

        self.start_button = tk.Button(root, text="Έναρξη Ελέγχου", command=self.start_check)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(root, text="Διακοπή Ελέγχου", command=self.stop_check, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.result_label = tk.Label(root, text="Αναμονή για έλεγχο...")
        self.result_label.pack()

        self.running = False

        # 🔊 Αρχικοποίηση pygame mixer
        pygame.mixer.init()

    def start_check(self):
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        selected_size = self.size_var.get()
        email = self.email_entry.get()

        messagebox.showinfo("Ενημέρωση", f"Ξεκινάει ο έλεγχος για {selected_size}...")
        threading.Thread(target=self.check_availability, args=(selected_size, email), daemon=True).start()

    def stop_check(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.result_label.config(text="Ο έλεγχος διακόπηκε.", fg="blue")    

    def play_sound(self):
        try:
            pygame.mixer.music.load("notification.mp3")  # 🔊 Αρχείο ήχου
            pygame.mixer.music.play()
        except Exception as e:
            print(f"⚠️ Σφάλμα αναπαραγωγής ήχου: {e}")

    def check_availability(self, selected_size, email):
        while self.running:
            options = webdriver.ChromeOptions()
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get("https://www.redstore.gr/el/emfaniseis-2/entos/andrika/andriko-fanela-epeteiaki-100-chronia-mn_136330/")

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//select[contains(@class, 'dim-select')]"))
                )

                size_elements = driver.find_elements(By.XPATH, "//select[contains(@class, 'dim-select')]//option")
                sizes = size_elements[1:]  # Αγνοούμε το "Μέγεθος"

                size_status = {SIZES[i]: sizes[i].get_attribute("disabled") is None for i in range(len(SIZES))}

                if size_status[selected_size]:
                    self.result_label.config(text=f"✅ {selected_size} διαθέσιμο!", fg="green")
                    self.play_sound()  # 🔊 Καλούμε τη μέθοδο σωστά
                    self.send_slack(self, selected_size)
                    if email:
                        self.send_email(email, selected_size)
                    self.running = False  # Σταματάει ο έλεγχος
                    self.start_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.DISABLED)
                else:
                    self.result_label.config(text=f"❌ {selected_size} Sold Out", fg="red")

            except Exception as e:
                self.result_label.config(text=f"⚠️ Σφάλμα: {e}", fg="orange")

            driver.quit()
            time.sleep(60)  # Έλεγχος κάθε 60 δευτερόλεπτα

    def send_email(self, to_email, size):
        try:
            msg = EmailMessage()
            msg["Subject"] = "🚨 Διαθεσιμότητα Φανέλας - Τρέξε!"
            msg["From"] = EMAIL_SENDER
            msg["To"] = to_email
            msg.set_content(f"Η φανέλα σε μέγεθος {size} είναι πλέον διαθέσιμη! Δες την εδώ: https://www.redstore.gr/el/emfaniseis-2/entos/andrika/andriko-fanela-epeteiaki-100-chronia-mn_136330/")

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            print(f"📩 Email στάλθηκε στο {to_email} για μέγεθος {size}!")
        
        except Exception as e:
            print(f"⚠️ Σφάλμα κατά την αποστολή email: {e}")
    
    def send_slack(self, size)
        try:
            message = f"Η φανέλα σε μέγεθος {size} είναι πλέον διαθέσιμη! Δες την εδώ: https://www.redstore.gr/el/emfaniseis-2/entos/andrika/andriko-fanela-epeteiaki-100-chronia-mn_136330/"

            # Set up a WebClient with the Slack OAuth token
            client = WebClient(token=SLACK_TOKEN)

            # Send a message
            client.chat_postMessage(
                channel="bot-updates", 
                text=message, 
                username="Bot Redstore"
            )
        except Exception as e:
            print(f"⚠️ Σφάλμα κατά την αποστολή slack: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = StockCheckerApp(root)
    root.mainloop()
