import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import threading
import jwt
# from Controllers.api_key_master_controller import save_api_key_count
from Model.api_key_master_model import API_Key_Master
from database import SessionLocal
from Model.bses_token_model import BSES_Token
from utils.save_api_count import save_api_key_count


class TokenManager:
    def __init__(self):
        self.jwt_token = None
        self.delhiv2_token = None
        self.jwt_expiry = None
        self.delhiv2_expiry = None
        self.lock = threading.Lock()

    def get_token(self, token_type="jwt"):
        with self.lock:
            if token_type == "jwt":
                # Step 1: If not cached, try DB
                if not self.jwt_token:
                    db_token = BSES_Token.find_one()
                    if db_token and db_token.bses_jwt_token and not self._is_expired(db_token.bses_jwt_token_expiry):
                        self.jwt_token = db_token.bses_jwt_token
                        self.jwt_expiry = db_token.bses_jwt_token_expiry

                # Step 2: Refresh if missing or expired
                if not self.jwt_token or self._is_expired(self.jwt_expiry):
                    self._refresh_jwt_token()

                return self.jwt_token

            elif token_type == "delhiv2":
                # Step 1: If not cached, try DB
                if not self.delhiv2_token:
                    db_token = BSES_Token.find_one()
                    if db_token and db_token.bses_delhiv2_token and not self._is_expired(db_token.bses_delhiv2_token_expiry):
                        self.delhiv2_token = db_token.bses_delhiv2_token
                        self.delhiv2_expiry = db_token.bses_delhiv2_token_expiry

                # Step 2: Refresh if missing or expired
                if not self.delhiv2_token or self._is_expired(self.delhiv2_expiry):
                    self._refresh_delhiv2_token()

                return self.delhiv2_token

    def _is_expired(self, expiry_time):
        """Check if token expired or about to expire in 10 minutes."""
        return not expiry_time or datetime.now() >= expiry_time - timedelta(minutes=10)

    def _refresh_jwt_token(self):
        print("Refreshing JWT Token...")
        record = API_Key_Master.find_one(api_name="JWT Token Generation")
        url = record.api_url

        # Extract values safely
        jwt_token_headers = record.api_headers or {}
        jwt_token_content_type = jwt_token_headers.get("Content-Type")
        jwt_token_soap_action = jwt_token_headers.get("SOAPAction")

        # url = "https://test.bsesbrpl.co.in/DBTest_Delhiv2/ISUService.asmx"
        # headers = {
        #     "Content-Type": "text/xml; charset=utf-8",
        #     "SOAPAction": "http://tempuri.org/GenerateAuthenticationToken",
        # }

        headers = {
            "Content-Type": jwt_token_content_type,
            "SOAPAction": jwt_token_soap_action,
        }
        payload = """<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <GenerateAuthenticationToken xmlns="http://tempuri.org/">
            <userName>DelhiV2ServiceUser</userName>
            <password>9*bS#7zT!xLwQ3vF</password>
            </GenerateAuthenticationToken>
        </soap:Body>
        </soap:Envelope>"""

        res = requests.post(url, headers=headers, data=payload)
        res.raise_for_status()
        response_text = res.text

        save_api_key_count("Token Manager","JWT Token Generation", payload, response_text)

        token = self._parse_token(res.text)
        self.jwt_token = token
        self.jwt_expiry = self._extract_expiry(token)
        db_session = SessionLocal()
        # Save or update in Postgres
        existing = db_session.query(BSES_Token).first()
        if existing:
            existing.bses_jwt_token = self.jwt_token
            existing.bses_jwt_token_expiry = self.jwt_expiry
        else:
            new_token = BSES_Token(
                bses_jwt_token=self.jwt_token,
                bses_jwt_token_expiry=self.jwt_expiry
            )
            db_session.add(new_token)
        db_session.commit()

    def _refresh_delhiv2_token(self):
        print("Refreshing delhiv2 Token...")

        record = API_Key_Master.find_one(api_name="DelhiV2 Token Generation")

        url = record.api_url

        # Extract values safely
        v2_token_headers = record.api_headers or {}
        v2_token_content_type = v2_token_headers.get("Content-Type")
        v2_token_soap_action = v2_token_headers.get("SOAPAction")


        # url = "https://bsesapps.bsesdelhi.com/delhiv2/ISUService.asmx?op=GenerateAuthenticationToken"
        # headers = {
        #     "Content-Type": "text/xml; charset=utf-8",
        #     "SOAPAction": '"http://tempuri.org/GenerateAuthenticationToken"',
        # }

        headers = {
            "Content-Type": v2_token_content_type,
            "SOAPAction": v2_token_soap_action,
        }

        payload = """<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                    xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <GenerateAuthenticationToken xmlns="http://tempuri.org/">
            <userName>DelhiV2ServiceUser</userName>
            <password>X!9q#Ld7@Vw$35Nz</password>
            </GenerateAuthenticationToken>
        </soap:Body>
        </soap:Envelope>"""

        res = requests.post(url, headers=headers, data=payload)
        res.raise_for_status()
        response_text = res.text

        save_api_key_count("Token Manager","DelhiV2 Token Generation", payload, response_text)
        
        token = self._parse_token(res.text)
        self.delhiv2_token = token
        self.delhiv2_expiry = self._extract_expiry(token)
        db_session = SessionLocal()
        # Update in Postgres
        existing = db_session.query(BSES_Token).first()
        if existing:
            existing.bses_delhiv2_token = self.delhiv2_token
            existing.bses_delhiv2_token_expiry = self.delhiv2_expiry
        else:
            new_token = BSES_Token(
                bses_delhiv2_token=self.delhiv2_token,
                bses_delhiv2_token_expiry=self.delhiv2_expiry
            )
            db_session.add(new_token)
        db_session.commit()

    def _parse_token(self, xml_response):
        tree = ET.fromstring(xml_response)
        namespaces = {"soap": "http://schemas.xmlsoap.org/soap/envelope/", "ns": "http://tempuri.org/"}
        result = tree.find(".//ns:GenerateAuthenticationTokenResult", namespaces)
        return result.text if result is not None else None

    def _extract_expiry(self, token):
        decoded = jwt.decode(token, options={"verify_signature": False})
        expiry = decoded.get("exp")
        return datetime.fromtimestamp(expiry) if expiry else datetime.now() + timedelta(hours=24)


# Global instance
token_manager = TokenManager()
