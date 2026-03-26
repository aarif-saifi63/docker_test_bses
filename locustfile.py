from locust import HttpUser, task, between
import uuid
import time
import itertools

# We use itertools.cycle to create a continuous loop of options.
# As Locust spawns all 200 users concurrently, it hands the next option 
# in the list to each new user.
menu_cycler = itertools.cycle([
    "Meter Reading Schedule BRPL",
    "New Connection Status BRPL",
    "Prepaid Meter - Check Balance / Recharge BRPL",
    "Consumption History BRPL",
    "Duplicate Bill BRPL",
    "Payment Status BRPL",
    "Payment History BRPL",
    "Bill History BRPL",
    "Complaint Status (NCC) BRPL",
    "Branches Nearby BRPL"
])

# menu_cycler = itertools.cycle([
#     "Virtual Customer Care Centre (BYPL) / Connect Virtually (BRPL) BRPL",
#     "New Connection Application BRPL",
#     "New Connection Status BRPL",
#     "Streetlight Complaint BRPL",
#     "Visually Impaired BRPL",
#     "Change Language BRPL",
#     "FAQs BRPL",
#     "Branches Nearby BRPL"
# ])


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

        # Set the authentication cookies
        self.client.cookies.set("chatbot_access_token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZW5kZXJfaWQiOiJlYWE2NzdjOC01N2I4LTRhNGUtYjliZS1iM2RhOTgzNDJjZDEiLCJleHAiOjE3NzQ0MzcyNTAsImlhdCI6MTc3NDQzNjM1MCwidHlwZSI6ImFjY2VzcyJ9.Asd4mJ1xLvLSI8djuDBJ3a4jdHwgE96Fc1Qrx-1HGfo")
        self.client.cookies.set("chatbot_refresh_token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZW5kZXJfaWQiOiJlYWE2NzdjOC01N2I4LTRhNGUtYjliZS1iM2RhOTgzNDJjZDEiLCJleHAiOjE3NzUwNDExNTAsImlhdCI6MTc3NDQzNjM1MCwidHlwZSI6InJlZnJlc2giLCJqdGkiOiIxMzAxYmI5Mjk3ZDMxNWE2ZjBhZDRjMzY0ZTg5NGI3NiJ9.8L1ZOk6MDwFvbZzJGt1YXVP743GjQ36t4SkbpHWi5C8")

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

        # --- STEP 2: Registered Consumer ---
        if not fire_step("Step 2", {"sender_id": self.sender_id, "message": "New Consumer BRPL", "lastSelectedOption": "", "source": "web"}): return
        time.sleep(1)

        # --- STEP 3: CA Verified ---
        if not fire_step("Step 3", {"sender_id": self.sender_id, "message": "ca verified BRPL", "lastSelectedOption": "", "source": "web"}): return
        time.sleep(1)

        # --- STEP 4: OTP Verified ---
        if not fire_step("Step 4", {"sender_id": self.sender_id, "message": "otp verified BRPL", "lastSelectedOption": "", "source": "web"}): return
        time.sleep(1)

        # --- STEP 5: English Selection ---
        if not fire_step("Step 5", {"sender_id": self.sender_id, "message": "English BRPL", "lastSelectedOption": "", "source": "web"}): return
        time.sleep(2)

        # --- STEP 6: Concurrent Dedicated Menu Option ---
        # Each concurrent user fires their specifically assigned option simultaneously
        step_6_payload = {
            "sender_id": self.sender_id,
            "message": self.my_menu_message,
            "lastSelectedOption": self.my_menu_option_clean,
            "source": "web",
            "is_menu_visible": "true",
            "type_of_user": "registered"
        }
        fire_step(f"Step 6 ({self.my_menu_option_clean})", step_6_payload)
