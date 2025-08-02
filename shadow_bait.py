import os
import sys
import re
import time
import getpass
import json
import smtplib
import phonenumbers
import qrcode
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from colorama import Fore, Style, init
from functools import lru_cache
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread
from bs4 import BeautifulSoup
from art import text2art
try:
    import pywifi
except ImportError:
    pywifi = None

# Initialize colorama
init(autoreset=True)

def clear_screen():
    """Clear screen for mobile and desktop compatibility"""
    os.system('cls' if os.name == 'nt' else 'clear')

def loading_animation(message, duration=2):
    """Display a loading animation"""
    frames = ['|', '/', '-', '\\']
    print(Fore.LIGHTCYAN_EX + message, end=" ")
    for _ in range(duration * 4):
        print(Fore.LIGHTYELLOW_EX + frames[_ % 4], end="\r")
        time.sleep(0.25)
    print("\r" + " " * 50 + "\r", end="")

def show_disclaimer():
    """Display disclaimer banner for 7 seconds"""
    clear_screen()
    print(Fore.RED + r"""
    ╔════════════════════════════════════════════════════╗
    ║                   DISCLAIMER                       ║
    ║ This tool is for ethical social engineering testing.║
    ║ Use only with explicit permission. Unauthorized use ║
    ║ may violate laws. T.R.C.H is not responsible for    ║
    ║ misuse. Proceed with caution.                      ║
    ╚════════════════════════════════════════════════════╝
    """)
    time.sleep(7)
    clear_screen()

def authenticate():
    """Password authentication with 3-attempt limit"""
    max_attempts = 3
    correct_password = "P@55word"
    
    for attempt in range(max_attempts):
        clear_screen()
        print(Fore.LIGHTCYAN_EX + "[*] ShadowBait Authentication")
        password = getpass.getpass(Fore.LIGHTBLUE_EX + "[?] Enter password: ")
        
        if password == correct_password:
            clear_screen()
            print(Fore.GREEN + "[+] Authentication Verified. Happy Hacking!")
            loading_animation("Initializing ShadowBait", 2)
            return True
        else:
            print(Fore.RED + f"[!] Incorrect password. {max_attempts - attempt - 1} attempts remaining.")
            time.sleep(1)
    
    clear_screen()
    print(Fore.RED + "[!] Too many failed attempts.")
    print(Fore.YELLOW + "[!] We see you're having some problem with the password.")
    print(Fore.YELLOW + "[!] Redirecting to our Facebook page to request the tool password...")
    print(Fore.LIGHTBLUE_EX + "https://www.facebook.com/profile.php?id=61555424416864")
    time.sleep(3)
    sys.exit(1)

class TrackingServer(BaseHTTPRequestHandler):
    """Simple HTTP server to track interactions"""
    def do_GET(self):
        self.server.results.append({
            "path": self.path,
            "ip": self.client_address[0],
            "user_agent": self.headers.get("User-Agent", "Unknown"),
            "timestamp": time.ctime(),
            "method": "GET"
        })
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(self.server.templates.get(self.path.lstrip("/"), "<html><body><h1>ShadowBait Tracking</h1></body></html>").encode())

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode()
        self.server.results.append({
            "path": self.path,
            "ip": self.client_address[0],
            "user_agent": self.headers.get("User-Agent", "Unknown"),
            "timestamp": time.ctime(),
            "method": "POST",
            "data": post_data
        })
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Submitted</h1></body></html>")

class ShadowBait:
    def __init__(self):
        self.results = []
        self.low_data_mode = False
        self.target_history = []
        self.templates = {
            "email_cred": {"name": "Password Reset", "subject": "Reset Your Password", "body": "Click to reset: {url}"},
            "email_link": {"name": "Urgent Update", "subject": "Urgent Account Update", "body": "Click here: {url}"},
            "sms": {"name": "Account Update", "body": "Urgent: Update your account: {url}"},
            "attachment": {"name": "Invoice.pdf", "content": b"Dummy PDF"},
            "login_page": {"name": "Google Login", "body": "<html><form method='POST'><input name='user'/><input type='password' name='pass'/><input type='submit'/></form></html>"},
            "social_media": {"name": "Verification", "body": "Verify your account: {url}"},
            "vishing": {"name": "Account Verification", "body": "Please call back to verify your account."},
            "qr_code": {"name": "Reward Claim", "body": "Scan to claim your reward: {url}"},
            "usb_drop": {"name": "shortcut.lnk", "content": b"Dummy Shortcut"},
            "wifi": {"name": "Free_WiFi", "body": "Connect to Free WiFi"}
        }
        self.template_file = "templates.json"
        self.load_templates()
        self.server = None
        self.server_thread = None

    def load_templates(self):
        """Load templates from JSON file"""
        try:
            with open(self.template_file, "r") as f:
                loaded = json.load(f)
                self.templates.update(loaded)
        except FileNotFoundError:
            with open(self.template_file, "w") as f:
                json.dump(self.templates, f, indent=2)

    def save_templates(self):
        """Save templates to JSON file"""
        with open(self.template_file, "w") as f:
            json.dump(self.templates, f, indent=2)

    def copy_template(self, template_type, source):
        """Copy a phishing template from source (file or text)"""
        try:
            if os.path.isfile(source):
                with open(source, "r") as f:
                    content = f.read()
            else:
                content = source
            
            soup = BeautifulSoup(content, "html.parser") if template_type in ["email_cred", "email_link", "login_page", "social_media"] else None
            name = f"Custom_{template_type}_{len(self.templates)}"
            
            if template_type in ["email_cred", "email_link"]:
                subject = soup.find("title").text if soup.find("title") else f"Custom {template_type}"
                self.templates[name] = {"name": name, "subject": subject, "body": content}
            elif template_type == "login_page":
                self.templates[name] = {"name": name, "body": content}
            elif template_type in ["sms", "social_media", "vishing", "qr_code"]:
                self.templates[name] = {"name": name, "body": content}
            elif template_type == "attachment":
                with open(source, "rb") as f:
                    self.templates[name] = {"name": os.path.basename(source), "content": f.read()}
            elif template_type == "usb_drop":
                with open(source, "rb") as f:
                    self.templates[name] = {"name": os.path.basename(source), "content": f.read()}
            elif template_type == "wifi":
                self.templates[name] = {"name": content, "body": content}
            
            self.save_templates()
            return name
        except Exception as e:
            return f"Error copying template: {str(e)}"

    def create_template(self, template_type, name, content, subject=None):
        """Create a custom phishing template"""
        try:
            ascii_banner = text2art(name, font="small") if template_type in ["email_cred", "email_link", "login_page"] else ""
            if template_type in ["email_cred", "email_link"]:
                self.templates[name] = {"name": name, "subject": subject or f"Custom {template_type}", "body": f"{ascii_banner}\n{content}"}
            elif template_type == "login_page":
                self.templates[name] = {"name": name, "body": f"<html><body>{ascii_banner}<br>{content}</body></html>"}
            elif template_type in ["sms", "social_media", "vishing", "qr_code"]:
                self.templates[name] = {"name": name, "body": content}
            elif template_type in ["attachment", "usb_drop"]:
                self.templates[name] = {"name": name, "content": content.encode()}
            elif template_type == "wifi":
                self.templates[name] = {"name": name, "body": content}
            
            self.save_templates()
            return name
        except Exception as e:
            return f"Error creating template: {str(e)}"

    def start_tracking_server(self):
        """Start a local HTTP server for tracking"""
        TrackingServer.results = self.results
        TrackingServer.templates = {k: v["body"] for k, v in self.templates.items() if "body" in v}
        self.server = HTTPServer(('localhost', 8080), TrackingServer)
        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop_tracking_server(self):
        """Stop the tracking server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            self.server_thread = None

    def toggle_low_data_mode(self, enabled):
        """Toggle low data mode"""
        self.low_data_mode = enabled

    def validate_input(self, input_type, value):
        """Validate input based on type"""
        try:
            if input_type == "email":
                return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value))
            elif input_type == "phone":
                parsed = phonenumbers.parse(value, None)
                return phonenumbers.is_valid_number(parsed)
            elif input_type == "url":
                return bool(re.match(r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", value))
            elif input_type == "file":
                return os.path.isfile(value)
            elif input_type == "ssid":
                return bool(re.match(r"^[a-zA-Z0-9_-]{1,32}$", value))
            elif input_type == "template":
                return value in self.templates
            return True
        except:
            return False

    @lru_cache(maxsize=10)
    def simulate_email_cred(self, email, template_name):
        """Simulate email phishing for credential harvesting"""
        result = {"type": "email_cred", "value": email, "data": {}, "error": None}
        loading_animation(f"Simulating email phishing for {email}")
        
        try:
            if not self.validate_input("email", email) or not self.validate_input("template", template_name):
                result["error"] = "Invalid email or template"
                return result
            
            self.start_tracking_server()
            url = f"http://localhost:8080/{template_name}"
            msg = MIMEMultipart()
            msg["Subject"] = self.templates[template_name]["subject"]
            msg["To"] = email
            msg.attach(MIMEText(self.templates[template_name]["body"].format(url=url), "html"))
            
            result["data"] = {
                "template_name": template_name,
                "recipient": email,
                "click_rate": len([r for r in self.results if r["path"] == f"/{template_name}"]),
                "submission_rate": len([r for r in self.results if r["path"] == f"/{template_name}" and r["method"] == "POST"]),
                "credentials": [r["data"] for r in self.results if r["path"] == f"/{template_name}" and r["method"] == "POST"],
                "ip": self.results[-1]["ip"] if self.results else "None",
                "user_agent": self.results[-1]["user_agent"] if self.results else "None",
                "timestamp": self.results[-1]["timestamp"] if self.results else "None",
                "browser": self.results[-1]["user_agent"].split("(")[1].split(")")[0] if self.results else "None",
                "geolocation": "Offline GeoIP not available"
            }
            self.stop_tracking_server()

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        self.results.append(result)
        return result

    @lru_cache(maxsize=10)
    def simulate_email_link(self, email, template_name):
        """Simulate email phishing for link clicking"""
        result = {"type": "email_link", "value": email, "data": {}, "error": None}
        loading_animation(f"Simulating email link phishing for {email}")
        
        try:
            if not self.validate_input("email", email) or not self.validate_input("template", template_name):
                result["error"] = "Invalid email or template"
                return result
            
            self.start_tracking_server()
            url = f"http://localhost:8080/{template_name}"
            msg = MIMEMultipart()
            msg["Subject"] = self.templates[template_name]["subject"]
            msg["To"] = email
            msg.attach(MIMEText(self.templates[template_name]["body"].format(url=url), "html"))
            
            result["data"] = {
                "template_name": template_name,
                "recipient": email,
                "click_rate": len([r for r in self.results if r["path"] == f"/{template_name}"]),
                "page_visited": f"/{template_name}" in [r["path"] for r in self.results],
                "time_spent": 0,
                "ip": self.results[-1]["ip"] if self.results else "None",
                "user_agent": self.results[-1]["user_agent"] if self.results else "None",
                "timestamp": self.results[-1]["timestamp"] if self.results else "None",
                "referrer": "None",
                "device_type": "Mobile" if "Mobile" in self.results[-1]["user_agent"] else "Desktop" if self.results else "None"
            }
            self.stop_tracking_server()

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        self.results.append(result)
        return result

    @lru_cache(maxsize=10)
    def simulate_sms(self, phone, template_name):
        """Simulate SMS phishing (smishing)"""
        result = {"type": "sms", "value": phone, "data": {}, "error": None}
        loading_animation(f"Simulating SMS phishing for {phone}")
        
        try:
            if not self.validate_input("phone", phone) or not self.validate_input("template", template_name):
                result["error"] = "Invalid phone or template"
                return result
            
            parsed = phonenumbers.parse(phone, None)
            self.start_tracking_server()
            url = f"http://localhost:8080/{template_name}"
            
            result["data"] = {
                "phone_number": phone,
                "template_name": template_name,
                "click_rate": len([r for r in self.results if r["path"] == f"/{template_name}"]),
                "ip": self.results[-1]["ip"] if self.results else "None",
                "user_agent": self.results[-1]["user_agent"] if self.results else "None",
                "timestamp": self.results[-1]["timestamp"] if self.results else "None",
                "carrier": phonenumbers.carrier.name_for_number(parsed, "en"),
                "device_type": "Mobile" if "Mobile" in self.results[-1]["user_agent"] else "Desktop" if self.results else "None",
                "response_time": 0,
                "geolocation": "Offline GeoIP not available"
            }
            self.stop_tracking_server()

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        self.results.append(result)
        return result

    @lru_cache(maxsize=10)
    def simulate_attachment(self, email, template_name):
        """Simulate malicious attachment"""
        result = {"type": "attachment", "value": email, "data": {}, "error": None}
        loading_animation(f"Simulating attachment phishing for {email}")
        
        try:
            if not self.validate_input("email", email) or not self.validate_input("template", template_name):
                result["error"] = "Invalid email or template"
                return result
            
            self.start_tracking_server()
            url = f"http://localhost:8080/{template_name}"
            file_hash = hashlib.sha256(self.templates[template_name]["content"]).hexdigest()
            
            result["data"] = {
                "attachment_type": self.templates[template_name]["name"],
                "template_name": template_name,
                "download_rate": len([r for r in self.results if r["path"] == f"/{template_name}"]),
                "ip": self.results[-1]["ip"] if self.results else "None",
                "user_agent": self.results[-1]["user_agent"] if self.results else "None",
                "timestamp": self.results[-1]["timestamp"] if self.results else "None",
                "file_hash": file_hash,
                "device_type": "Mobile" if "Mobile" in self.results[-1]["user_agent"] else "Desktop" if self.results else "None",
                "os": self.results[-1]["user_agent"].split("(")[1].split(")")[0] if self.results else "None",
                "interaction_time": 0
            }
            self.stop_tracking_server()

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        self.results.append(result)
        return result

    @lru_cache(maxsize=10)
    def simulate_login_page(self, url, template_name):
        """Simulate fake login page"""
        result = {"type": "login_page", "value": url, "data": {}, "error": None}
        loading_animation(f"Simulating login page for {url}")
        
        try:
            if not self.validate_input("url", url) or not self.validate_input("template", template_name):
                result["error"] = "Invalid URL or template"
                return result
            
            self.start_tracking_server()
            result["data"] = {
                "template_name": template_name,
                "url": url,
                "submission_rate": len([r for r in self.results if r["path"] == f"/{template_name}" and r["method"] == "POST"]),
                "credentials": [r["data"] for r in self.results if r["path"] == f"/{template_name}" and r["method"] == "POST"],
                "ip": self.results[-1]["ip"] if self.results else "None",
                "user_agent": self.results[-1]["user_agent"] if self.results else "None",
                "timestamp": self.results[-1]["timestamp"] if self.results else "None",
                "browser": self.results[-1]["user_agent"].split("(")[1].split(")")[0] if self.results else "None",
                "device_type": "Mobile" if "Mobile" in self.results[-1]["user_agent"] else "Desktop" if self.results else "None",
                "referrer": "None"
            }
            self.stop_tracking_server()

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        self.results.append(result)
        return result

    @lru_cache(maxsize=10)
    def simulate_social_media(self, platform, template_name):
        """Simulate social media phishing"""
        result = {"type": "social_media", "value": platform, "data": {}, "error": None}
        loading_animation(f"Simulating social media phishing for {platform}")
        
        try:
            if not self.validate_input("template", template_name):
                result["error"] = "Invalid template"
                return result
            
            self.start_tracking_server()
            url = f"http://localhost:8080/{template_name}"
            result["data"] = {
                "platform": platform,
                "template_name": template_name,
                "click_rate": len([r for r in self.results if r["path"] == f"/{template_name}"]),
                "ip": self.results[-1]["ip"] if self.results else "None",
                "user_agent": self.results[-1]["user_agent"] if self.results else "None",
                "timestamp": self.results[-1]["timestamp"] if self.results else "None",
                "profile_details": "None",
                "device_type": "Mobile" if "Mobile" in self.results[-1]["user_agent"] else "Desktop" if self.results else "None",
                "interaction_time": 0,
                "geolocation": "Offline GeoIP not available"
            }
            self.stop_tracking_server()

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        self.results.append(result)
        return result

    @lru_cache(maxsize=10)
    def simulate_vishing(self, phone, template_name):
        """Simulate voice phishing"""
        result = {"type": "vishing", "value": phone, "data": {}, "error": None}
        loading_animation(f"Simulating vishing for {phone}")
        
        try:
            if not self.validate_input("phone", phone) or not self.validate_input("template", template_name):
                result["error"] = "Invalid phone or template"
                return result
            
            parsed = phonenumbers.parse(phone, None)
            result["data"] = {
                "script_name": template_name,
                "phone_number": phone,
                "call_duration": 0,
                "response": "None",
                "timestamp": time.ctime(),
                "carrier": phonenumbers.carrier.name_for_number(parsed, "en"),
                "device_type": "Unknown",
                "recorded_input": "None",
                "call_time": time.ctime(),
                "region": phonenumbers.region_code_for_number(parsed)
            }

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        self.results.append(result)
        return result

    @lru_cache(maxsize=10)
    def simulate_qr_code(self, url, template_name):
        """Simulate QR code phishing"""
        result = {"type": "qr_code", "value": url, "data": {}, "error": None}
        loading_animation(f"Simulating QR code phishing for {url}")
        
        try:
            if not self.validate_input("url", url) or not self.validate_input("template", template_name):
                result["error"] = "Invalid URL or template"
                return result
            
            qr = qrcode.make(url)
            qr.save(f"phishing_{template_name}.png")
            self.start_tracking_server()
            result["data"] = {
                "template_name": template_name,
                "scan_rate": len([r for r in self.results if r["path"] == f"/{template_name}"]),
                "ip": self.results[-1]["ip"] if self.results else "None",
                "user_agent": self.results[-1]["user_agent"] if self.results else "None",
                "timestamp": self.results[-1]["timestamp"] if self.results else "None",
                "device_type": "Mobile" if "Mobile" in self.results[-1]["user_agent"] else "Desktop" if self.results else "None",
                "camera_details": "Unknown",
                "geolocation": "Offline GeoIP not available",
                "page_visited": f"/{template_name}" in [r["path"] for r in self.results],
                "time_on_page": 0
            }
            self.stop_tracking_server()

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        self.results.append(result)
        return result

    @lru_cache(maxsize=10)
    def simulate_usb_drop(self, file_path, template_name):
        """Simulate USB drop attack"""
        result = {"type": "usb_drop", "value": file_path, "data": {}, "error": None}
        loading_animation(f"Simulating USB drop for {file_path}")
        
        try:
            if not self.validate_input("file", file_path) or not self.validate_input("template", template_name):
                result["error"] = "Invalid file or template"
                return result
            
            file_hash = hashlib.sha256(self.templates[template_name]["content"]).hexdigest()
            self.start_tracking_server()
            result["data"] = {
                "template_name": template_name,
                "insertion_rate": len([r for r in self.results if r["path"] == f"/{template_name}"]),
                "ip": self.results[-1]["ip"] if self.results else "None",
                "user_agent": self.results[-1]["user_agent"] if self.results else "None",
                "timestamp": self.results[-1]["timestamp"] if self.results else "None",
                "device_type": "Mobile" if "Mobile" in self.results[-1]["user_agent"] else "Desktop" if self.results else "None",
                "os": self.results[-1]["user_agent"].split("(")[1].split(")")[0] if self.results else "None",
                "execution_status": False,
                "file_hash": file_hash,
                "interaction_time": 0
            }
            self.stop_tracking_server()

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        self.results.append(result)
        return result

    @lru_cache(maxsize=10)
    def simulate_wifi_phishing(self, ssid, template_name):
        """Simulate Wi-Fi phishing (evil twin)"""
        result = {"type": "wifi", "value": ssid, "data": {}, "error": None}
        loading_animation(f"Simulating Wi-Fi phishing for {ssid}")
        
        try:
            if not self.validate_input("ssid", ssid) or not self.validate_input("template", template_name):
                result["error"] = "Invalid SSID or template"
                return result
            
            result["data"] = {
                "ssid": ssid,
                "template_name": template_name,
                "connection_rate": 0,
                "ip": "None",
                "user_agent": "None",
                "timestamp": time.ctime(),
                "device_type": "Unknown",
                "mac_address": "None",
                "encryption": "Unknown",
                "channel": "Unknown"
            }
            if pywifi:
                wifi = pywifi.PyWiFi()
                iface = wifi.interfaces()[0]
                result["data"]["encryption"] = "WPA2"
                result["data"]["channel"] = "1"

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        self.results.append(result)
        return result

class ShadowBaitInterface:
    def __init__(self):
        show_disclaimer()
        if not authenticate():
            sys.exit(1)
        self.recon = ShadowBait()
        self.clear_screen()
        self.show_banner()

    def clear_screen(self):
        """Clear screen for clean display"""
        clear_screen()

    def show_banner(self):
        """ShadowBait banner with slogan"""
        self.clear_screen()
        banner = text2art("ShadowBait", font="small")
        print(Fore.RED + banner)
        print(Fore.LIGHTCYAN_EX + "  ShadowBait v2.0 - by T.R.C.H")
        print(Fore.LIGHTGREEN_EX + "  Lure, Learn, Secure")
        print(Fore.LIGHTBLACK_EX + "  Mobile-Optimized Phishing Simulation\n")

    def show_menu(self):
        """Touch-friendly menu"""
        menu = [
            ("1", "Set Target"),
            ("2", "Show Recent Targets"),
            ("3", "Simulate Email Cred Phishing"),
            ("4", "Simulate Email Link Phishing"),
            ("5", "Simulate SMS Phishing"),
            ("6", "Simulate Attachment Phishing"),
            ("7", "Simulate Login Page"),
            ("8", "Simulate Social Media Phishing"),
            ("9", "Simulate Vishing"),
            ("10", "Simulate QR Code Phishing"),
            ("11", "Simulate USB Drop"),
            ("12", "Simulate Wi-Fi Phishing"),
            ("13", "Copy Phishing Template"),
            ("14", "Create Custom Template"),
            ("15", "List Templates"),
            ("16", "Toggle Low Data Mode"),
            ("17", "View Results"),
            ("0", "Exit")
        ]
        print(Fore.LIGHTWHITE_EX + "┌" + "─"*34 + "┐")
        for num, text in menu:
            print(Fore.LIGHTWHITE_EX + "│ " + 
                  f"{Fore.LIGHTRED_EX}{num.ljust(2)}{Fore.LIGHTWHITE_EX} {Fore.LIGHTGREEN_EX}{text.ljust(30)}" + 
                  Fore.LIGHTWHITE_EX + "│")
        print(Fore.LIGHTWHITE_EX + "└" + "─"*34 + "┘")

    def touch_input(self, prompt):
        """Mobile-friendly input"""
        print(Fore.LIGHTBLUE_EX + f"[?] {prompt}: ", end="")
        try:
            user_input = input().strip()
            if not user_input:
                print(Fore.YELLOW + "[!] Input cannot be empty")
                return None
            print(Fore.LIGHTBLACK_EX + "[*] Input received")
            return user_input
        except KeyboardInterrupt:
            print(Fore.RED + "\n[!] Operation cancelled")
            sys.exit(1)

    def set_target(self):
        """Set and validate target"""
        self.clear_screen()
        self.show_banner()
        target = self.touch_input("Enter target (Email, Phone, URL, File, SSID)")
        if not target:
            return
        
        target_type = None
        for t in ["email", "phone", "url", "file", "ssid"]:
            if self.recon.validate_input(t, target):
                target_type = t
                break
        
        if target_type:
            if (target_type, target) not in self.recon.target_history:
                self.recon.target_history.append((target_type, target))
                if len(self.recon.target_history) > 5:
                    self.recon.target_history.pop(0)
            print(Fore.GREEN + f"[+] Target set: {target} ({target_type})")
        else:
            print(Fore.RED + "[!] Invalid target format")

    def show_recent_targets(self):
        """Show recent targets"""
        self.clear_screen()
        self.show_banner()
        if not self.recon.target_history:
            print(Fore.YELLOW + "[!] No recent targets")
            return
        print(Fore.LIGHTCYAN_EX + "[*] Recent Targets:")
        for i, (t_type, target) in enumerate(self.recon.target_history, 1):
            print(Fore.LIGHTGREEN_EX + f"  {i}. {target} ({t_type})")
        choice = self.touch_input("Select a target number (or Enter to cancel)")
        if choice and choice.isdigit() and 1 <= int(choice) <= len(self.recon.target_history):
            print(Fore.GREEN + f"[+] Selected target: {self.recon.target_history[int(choice) - 1][1]}")

    def copy_template(self):
        """Copy a phishing template"""
        self.clear_screen()
        self.show_banner()
        template_type = self.touch_input("Enter template type (email_cred, email_link, sms, attachment, login_page, social_media, vishing, qr_code, usb_drop, wifi)")
        source = self.touch_input("Enter source (file path or text)")
        if template_type and source:
            result = self.recon.copy_template(template_type, source)
            print(Fore.GREEN + f"[+] Template copied: {result}" if "Error" not in result else Fore.RED + f"[!] {result}")

    def create_template(self):
        """Create a custom phishing template"""
        self.clear_screen()
        self.show_banner()
        template_type = self.touch_input("Enter template type (email_cred, email_link, sms, attachment, login_page, social_media, vishing, qr_code, usb_drop, wifi)")
        name = self.touch_input("Enter template name")
        content = self.touch_input("Enter template content")
        subject = self.touch_input("Enter subject (for email templates)") if template_type in ["email_cred", "email_link"] else None
        if template_type and name and content:
            result = self.recon.create_template(template_type, name, content, subject)
            print(Fore.GREEN + f"[+] Template created: {result}" if "Error" not in result else Fore.RED + f"[!] {result}")

    def list_templates(self):
        """List all available templates"""
        self.clear_screen()
        self.show_banner()
        print(Fore.LIGHTCYAN_EX + "[*] Available Templates:")
        for name, data in self.recon.templates.items():
            print(Fore.LIGHTGREEN_EX + f"  {name}: {data['name']}")

    def gather_info(self, method, input_type):
        """Generic method to simulate attacks"""
        self.clear_screen()
        self.show_banner()
        target = self.touch_input(f"Enter {input_type} to simulate")
        template_name = self.touch_input("Enter template name")
        if not target or not template_name or not self.recon.validate_input(input_type, target) or not self.recon.validate_input("template", template_name):
            print(Fore.RED + f"[!] Invalid {input_type} or template")
            return
        result = method(target, template_name)
        self.display_result(result)

    def display_result(self, result):
        """Display a single result"""
        print(Fore.LIGHTCYAN_EX + f"[*] Results for {result['type']}: {result['value']}")
        if result["error"]:
            print(Fore.RED + f"[!] Error: {result['error']}")
        else:
            for key, value in result["data"].items():
                print(Fore.LIGHTGREEN_EX + f"  {key.capitalize()}:")
                if isinstance(value, list):
                    for item in value:
                        print(Fore.LIGHTWHITE_EX + f"    - {item}")
                else:
                    print(Fore.LIGHTWHITE_EX + f"    {value}")
        time.sleep(1)

    def show_results(self):
        """Display all results"""
        self.clear_screen()
        self.show_banner()
        if not self.recon.results:
            print(Fore.YELLOW + "[!] No results available")
            return
        print(Fore.LIGHTCYAN_EX + "[*] All Results:")
        for i, result in enumerate(self.recon.results, 1):
            print(Fore.LIGHTWHITE_EX + f"  {i}. {result['type'].capitalize()}: {result['value']}")
            if result["error"]:
                print(Fore.RED + f"    Error: {result['error']}")
            else:
                for key, value in result["data"].items():
                    print(Fore.LIGHTGREEN_EX + f"    {key.capitalize()}:")
                    if isinstance(value, list):
                        for item in value:
                            print(Fore.LIGHTWHITE_EX + f"      - {item}")
                    else:
                        print(Fore.LIGHTWHITE_EX + f"      {value}")

    def run(self):
        """Main application loop"""
        while True:
            self.clear_screen()
            self.show_banner()
            self.show_menu()
            choice = self.touch_input("Select option")
            if not choice:
                continue

            if choice == "1":
                self.set_target()
            elif choice == "2":
                self.show_recent_targets()
            elif choice == "3":
                self.gather_info(self.recon.simulate_email_cred, "email")
            elif choice == "4":
                self.gather_info(self.recon.simulate_email_link, "email")
            elif choice == "5":
                self.gather_info(self.recon.simulate_sms, "phone")
            elif choice == "6":
                self.gather_info(self.recon.simulate_attachment, "email")
            elif choice == "7":
                self.gather_info(self.recon.simulate_login_page, "url")
            elif choice == "8":
                self.gather_info(self.recon.simulate_social_media, "platform")
            elif choice == "9":
                self.gather_info(self.recon.simulate_vishing, "phone")
            elif choice == "10":
                self.gather_info(self.recon.simulate_qr_code, "url")
            elif choice == "11":
                self.gather_info(self.recon.simulate_usb_drop, "file")
            elif choice == "12":
                self.gather_info(self.recon.simulate_wifi_phishing, "ssid")
            elif choice == "13":
                self.copy_template()
            elif choice == "14":
                self.create_template()
            elif choice == "15":
                self.list_templates()
            elif choice == "16":
                self.recon.toggle_low_data_mode(not self.recon.low_data_mode)
                print(Fore.GREEN + f"[+] Low data mode: {'Enabled' if self.recon.low_data_mode else 'Disabled'}")
            elif choice == "17":
                self.show_results()
            elif choice == "0":
                print(Fore.RED + "[+] Exiting...")
                sys.exit(0)
            else:
                print(Fore.RED + "[!] Invalid option")
            
            input(Fore.LIGHTBLACK_EX + "\n[Press Enter to continue...")

if __name__ == "__main__":
    try:
        app = ShadowBaitInterface()
        app.run()
    except KeyboardInterrupt:
        clear_screen()
        print(Fore.RED + "\n[!] Closed by user")
        sys.exit(1)