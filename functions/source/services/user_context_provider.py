import datetime
from firebase_admin import firestore

class UserContextProvider:
    user_id = ""
    def __init__(self, user_id):
        self.user_id = user_id


    def get_user_context(self, mentions=[]):
        now = datetime.datetime.now()
        la_time = now - datetime.timedelta(hours=7)
        current_date_time = la_time.strftime('%Y-%m-%d %H:%M:%S')

        user_context = {}
        db = firestore.client()
        user_record = db.collection("users").document(self.user_id).get()
        
        if user_record.exists:
            user_record = user_record.to_dict()
            print(f"[USER RECORD]: {user_record}\n")
        else:
            print("No user record found.")
            user_record = {}

        username_to_profile = {}
        for m in mentions:
            key = "@" + m.get("username")
            username_to_profile[key] = {
                "email": m.get("email"),
                "name": m.get("name")
            }

        user_context = {
            "name": user_record.get("name", ""),
            "current_date_and_time": current_date_time,
            "time_zone": "America/Los_Angeles",
            "mentioned_users": str(username_to_profile),
            "calendar_id": user_record.get("email", "")
        }

        return user_context

    