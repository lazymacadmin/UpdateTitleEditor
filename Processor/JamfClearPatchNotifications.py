#!/usr/local/autopkg/python

import requests
import json

from autopkglib import Processor, ProcessorError

__all__ = ["JamfClearPatchNotifications"]

class JamfClearPatchNotifications(Processor):
    """Clear notifications for patch policies in Jamf Pro."""

    input_variables = {
        "patch_name": {
            "required": True,
            "description": "The title of the patch to clear notifications for.",
        },
        "version": {
            "required": True,
            "description": "The patch version to clear notifications for.",
        },
    }
    output_variables = {}

    def main(self):
        # Get the version and title from the input variables
        patch_name = self.env.get("patch_name")
        version = self.env.get("version")

        # Build the URL for the Jamf Pro API
        jamf_url = self.env.get("JSS_URL")
        auth_url = jamf_url + "/api/v1/auth/token"
        not_url = jamf_url + "/api/v1/notifications"

        username = self.env.get("API_USERNAME")
        password = self.env.get("API_PASSWORD")

        # Make a PUT request to the Jamf Pro API to clear notifications for the patch policy
        headers = {"Content-Type": "application/json"}
        tokenreq = requests.post(auth_url, auth=(username,password), headers=headers)
        token = tokenreq.json()["token"]

        # Check if the request was successful
        if tokenreq.status_code != 200:
            raise ProcessorError(f"Error getting auth token: {tokenreq.status_code}")

        headers = {"accept": "application/json", "Authorization": "Bearer {}".format(token)}
        get_not_response = requests.get(not_url, headers=headers)

        data = json.loads(get_not_response.text)
        for item in data:
            if item["params"]["softwareTitleName"] == patch_name and item["params"]["latestVersion"] == version:
                notification_id = item["id"]
                self.output(notification_id)
                break
        
        dheaders = {"Authorization": "Bearer {}".format(token)}
        dismiss_url = not_url + "/PATCH_UPDATE/" +notification_id
        self.output(dismiss_url)
        dismiss_response = requests.delete(
            url=dismiss_url,
            headers=dheaders)

        if dismiss_response.status_code not in (200, 201, 204):
            raise ProcessorError(f"Error dismissing notification: {dismiss_response.status_code}")

        self.output(f"Successfully cleared notification for {patch_name} version {version}")

if __name__ == "__main__":
    processor = JamfClearPatchNotifications()
    processor.execute_shell()
