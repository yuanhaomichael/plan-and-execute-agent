from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from firebase_admin import firestore
import os
from google.auth.transport.requests import Request
import google_auth_oauthlib.flow



class CredentialsManager:
    SCOPES = "openid https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/gmail.compose https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/contacts.readonly"

    TOKEN_FILE_NAME = "google_token.json"
    GOOGLE_CREDS_FILE_NAME = "credentials.json"
    TOKEN_URI = "https://oauth2.googleapis.com/token"

    REDIRECT_URI = os.environ['REDIRECT_URI']

    def get_google_auth_url(self, user_id):
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            self.GOOGLE_CREDS_FILE_NAME,
            scopes=self.SCOPES)

        # Indicate where the API server will redirect the user after the user completes
        # the authorization flow. The redirect URI is required. The value must exactly
        # match one of the authorized redirect URIs for the OAuth 2.0 client, which you
        # configured in the API Console. If this value doesn't match an authorized URI,
        # you will get a 'redirect_uri_mismatch' error.
        flow.redirect_uri = os.environ["REDIRECT_URI"]

        # Generate URL for request to Google's OAuth 2.0 server.
        # Use kwargs to set optional request parameters.
        authorization_url, state = flow.authorization_url(
            # Enable offline access so that you can refresh an access token without
            # re-prompting the user for permission. Recommended for web server apps.
            access_type='offline',
            # Enable incremental authorization. Recommended as a best practice.
            include_granted_scopes='true',
            state=user_id,
            # additional params
            user_id=user_id,
            mode="auth_code")
        
        return authorization_url
    
    def credentials_to_dict(self, credentials):
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
    

    def get_and_store_google_access_and_refresh_tokens(self, auth_code, user_id):
        credentials = None
        try:
            flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
                self.GOOGLE_CREDS_FILE_NAME, scopes=self.SCOPES, state=user_id)
            
            # Fetch the OAuth 2.0 tokens
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            
            creds = self.credentials_to_dict(credentials)

            credentials = Credentials(                
                token=creds["token"],                     
                refresh_token=creds["refresh_token"],     
                client_id=os.environ.get("GOOGLE_CLIENT_ID"),                  
                client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),          
                token_uri='https://oauth2.googleapis.com/token')

            credentials.refresh(Request())

            db = firestore.client()
            # Update the user's tokens in the database
            db.collection("users").document(user_id).update({
                "access_token": creds["token"],
                "refresh_token": creds["refresh_token"]
            })

        except Exception as e:
            print(f'An unexpected error occurred: {e}')

        return credentials
    

    def get_creds(self, user_id = "", is_local = False):
        if is_local:
            creds = None

            if os.path.exists(self.TOKEN_FILE_NAME):
                creds = Credentials.from_authorized_user_file(self.TOKEN_FILE_NAME)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(self.GOOGLE_CREDS_FILE_NAME,
                                                                    self.SCOPES)
                    creds = flow.run_local_server(port=8080)

                with open(self.TOKEN_FILE_NAME, "w") as token:
                    token.write(creds.to_json())

            return creds
        
        
        ###################
        db = firestore.client()
        user_record = db.collection("users").document(user_id).get()
        
        if user_record.exists:
            user_record = user_record.to_dict()
            print(f"[USER RECORD]: {user_record}\n")
        else:
            print("No user record or credentials found.")

        # Check if access and refresh tokens are available for the user
        access_token = user_record.get("access_token")
        refresh_token = user_record.get("refresh_token")

        if access_token is not None and refresh_token is not None:
            credentials = Credentials(                
                token=access_token,                     
                refresh_token=refresh_token,     
                client_id=os.environ.get("GOOGLE_CLIENT_ID"),                  
                client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),          
                token_uri='https://oauth2.googleapis.com/token')


            if credentials:
                if credentials.expired and credentials.refresh_token:
                    print("REFRESHING GOOGLE TOKENS...")
                    credentials.refresh(Request())
                else:
                    print("VALID GOOGLE TOKENS!")
                    return credentials
        else:
            print("GETTING AUTH CODE AND EXCHANGING FOR GOOGLE TOKENS...")
            auth_code = user_record.get("auth_code")
            if auth_code:
                credentials = self.get_and_store_google_access_and_refresh_tokens(auth_code=auth_code, user_id=user_id)
                return credentials
                                
        
