import requests
import xml.etree.ElementTree as ET
from django.conf import settings

class ShortMessageHelper:

    @staticmethod
    def send_sms_via_robi(message, phone):
        url = f"{settings.MOBIREACH_URL}/SendTextMultiMessage"

        payload = {
            "Username": settings.MOBIREACH_USERNAME,
            "Password": settings.MOBIREACH_PASSWORD,
            "From": settings.MOBIREACH_SENDER,
            "To": phone,
            "Message": message
        }

        try:
            response = requests.post(url, data=payload, timeout=30)

            try:
                xml_root = ET.fromstring(response.text)
            except ET.ParseError:
                return False

            status = xml_root.find(".//Status")

            print(f"Robi SMS API response: {response.text}")

            print(f"Status: {status}")
            if status is not None and status.text == "0":

                # Optional logging
                # SmsLog.objects.create(
                #     provider="robi",
                #     username=username,
                #     phone=phone,
                #     message=message,
                #     response=response.text
                # )

                return True

        except Exception as exc:
            print("Error sending SMS via Robi", exc)
            return False

        return False