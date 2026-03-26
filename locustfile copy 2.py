from locust import HttpUser, task, between
import uuid
import time
import itertools
 
# We use itertools.cycle to create a continuous loop of options.
# As Locust spawns all users concurrently, it hands the next option 
# in the list to each new user.
menu_cycler = itertools.cycle([
    "Virtual Customer Care Centre (BYPL) / Connect Virtually (BRPL) BRPL",
    "New Connection Application BRPL",
    "New Connection Status BRPL",
    "Streetlight Complaint BRPL",
    "Visually Impaired BRPL",
    "Change Language BRPL",
    "FAQs BRPL",
    "Branches Nearby BRPL"
])
 
class BSESBotUser(HttpUser):
    # Wait 5 to 15 seconds between full conversational journeys
    wait_time = between(5, 15)
 
    def on_start(self):
        """
        on_start runs ONCE per simulated user when they first 'connect'.
        """
        # Generate a unique sender_id for this specific concurrent user
        self.sender_id = str(uuid.uuid4())
        # Assign this specific user their dedicated menu option for the whole test
        self.my_menu_message = next(menu_cycler)
        # Clean the option for the "lastSelectedOption" field
        self.my_menu_option_clean = self.my_menu_message.replace(" BRPL", "").strip()
        # Set the global headers
        self.client.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://bsestest.greymatterz.com",
            "Referer": "https://bsestest.greymatterz.com/",
            "User-Agent": "Locust Load Testing Swarm"
        })
 
        # Set the fresh authentication cookies from your latest curl payload
        self.client.cookies.set("chatbot_access_token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZW5kZXJfaWQiOiIzZWNlYjVjNS1kNGMxLTRlMjctYWE0NS1lYWQ2YzdhNzM5YTEiLCJleHAiOjE3NzQ0NDQ4NTksImlhdCI6MTc3NDQ0Mzk1OSwidHlwZSI6ImFjY2VzcyJ9.A7RfgxKAKFSpam54fOdxI2NOolen7kCDshPnNmaZBDY")
        self.client.cookies.set("chatbot_refresh_token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZW5kZXJfaWQiOiIzZWNlYjVjNS1kNGMxLTRlMjctYWE0NS1lYWQ2YzdhNzM5YTEiLCJleHAiOjE3NzUwNDg3NTksImlhdCI6MTc3NDQ0Mzk1OSwidHlwZSI6InJlZnJlc2giLCJqdGkiOiJlMTgzMzM0ZDEzNDdiMjg2YTEwZmRjNDhiYThmODVmYSJ9.sCr7yL8EEqODlkfgThZBpvWPDTwzJOZqV5gXghQO_14")
 
    @task
    def execute_user_journey(self):
        """
        When you set 200 users in Locust, it runs 200 instances of this 
        function at the exact same time.
        """
        def fire_step(step_name, payload):
            with self.client.post("/api/webhook", json=payload, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                    return True
                else:
                    response.failure(f"{step_name} Failed: {response.status_code}")
                    return False
 
        # --- STEP 1: Initial Greeting ---
        if not fire_step("Step 1", {"sender_id": self.sender_id, "message": "BSES Rajdhani BRPL", "lastSelectedOption": "", "source": "web"}): return
        time.sleep(1)
 
        # --- STEP 2: New Consumer ---
        if not fire_step("Step 2", {"sender_id": self.sender_id, "message": "New Consumer / नया उपभोक्ता BRPL", "lastSelectedOption": "", "source": "web"}): return
        time.sleep(1)
 
        # --- STEP 3: English Selection ---
        if not fire_step("Step 3", {"sender_id": self.sender_id, "message": "English BRPL", "lastSelectedOption": "", "source": "web"}): return
        time.sleep(2)
 
        # --- STEP 4: Concurrent Dedicated Menu Option ---
        # Each concurrent user fires their specifically assigned option simultaneously
        step_4_payload = {
            "sender_id": self.sender_id,
            "message": self.my_menu_message,
            "lastSelectedOption": self.my_menu_option_clean,
            "source": "web",
            "is_menu_visible": "true",
            "type_of_user": "new" 
        }
        fire_step(f"Step 4 ({self.my_menu_option_clean})", step_4_payload)