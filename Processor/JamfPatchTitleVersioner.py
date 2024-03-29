#!/usr/local/autopkg/python

"""
JamfPatchTitleVersioner processor for finding the latest software version number for a Patch Title from Jamf Pro using AutoPkg
    assembled by Anthony Reimer using code from JamfPatchUploader (by Marcel Keßler based on G Pugh's great work)
    and modified for modern Jamf Pro auth by Drew Barnes
"""

import os.path
import sys

import xml.etree.ElementTree as ET

from time import sleep
from autopkglib import ProcessorError  # pylint: disable=import-error

# to use a base module in AutoPkg we need to add this path to the sys.path.
# this violates flake8 E402 (PEP8 imports) but is unavoidable, so the following
# imports require noqa comments for E402
sys.path.insert(0, os.path.dirname(__file__))

from JamfUploaderLib.JamfUploaderBase import JamfUploaderBase  # noqa: E402

__all__ = ["JamfPatchUploader"]


class JamfPatchTitleVersioner(JamfUploaderBase):
    """Determines the latest software version being reported by a Jamf Pro Patch Management Title."""

    input_variables = {
        "JSS_URL": {
            "required": True,
            "description": "URL to a Jamf Pro server that the API user has write access "
            "to, optionally set as a key in the com.github.autopkg "
            "preference file.",
        },
        "API_USERNAME": {
            "required": False,
            "description": "Username of account with appropriate access to "
            "jss, optionally set as a key in the com.github.autopkg "
            "preference file.",
        },
        "API_PASSWORD": {
            "required": False,
            "description": "Password of api user, optionally set as a key in "
            "the com.github.autopkg preference file.",
        },
        "CLIENT_ID": {
            "required": False,
            "description": "client id on the jamf server,"
            "optionally set as a key in the com.github.autopkg "
            "preference file.",
        },
        "CLIENT_SECRET": {
            "required": False,
            "description": "client scret for the CLOIENT_ID, optionally set as a key in "
            "the com.github.autopkg preference file.",
        },
        "patch_softwaretitle": {
            "required": True,
            "description": (
                "Name of the patch software title (e.g. 'Mozilla Firefox') used in Jamf. "
            ),
            "default": "",
        },
    }

    output_variables = {
        "latest_patch_version": {
            "description": "The latest version number of the software reported by the Patch Title."
        },
    }

    def latest_patch_version(
        self,
        jamf_url,
        patch_softwaretitle_id,
        token="",
    ) -> str:
        """Returns the newest software version number for the Patch Title ID passed"""
        self.output("Looking up latest version from patch software title (by ID)...")

        # Get current software title
        object_type = "patch_software_title"
        url = "{}/{}/id/{}".format(
            jamf_url, self.api_endpoints(object_type), patch_softwaretitle_id
        )

        # "GET" patch title feed.
        r = self.curl(
            request="GET", url=url, token=token, accept_header="xml"
        )

        if r.status_code != 200:
            raise ProcessorError("ERROR: Could not fetch patch software title.")

        # Parse response as xml
        try:
            patch_softwaretitle_xml = ET.fromstring(r.output)
        except ET.ParseError as xml_error:
            raise ProcessorError from xml_error

        # Get first match of all the versions listed in the
        # software title to report the 'latest version'.
        latest_version = patch_softwaretitle_xml.find("versions/version/software_version").text
        return latest_version

    def main(self):
        """Do the main thing here"""
        self.jamf_url = self.env.get("JSS_URL")
        self.jamf_user = self.env.get("API_USERNAME")
        self.jamf_password = self.env.get("API_PASSWORD")
        self.client_id = self.env.get("CLIENT_ID")
        self.client_secret = self.env.get("CLIENT_SECRET")
        self.patch_softwaretitle = self.env.get("patch_softwaretitle")

        self.output(
            f"Checking for existing '{self.patch_softwaretitle}' on {self.jamf_url}"
        )

        # get token using oauth or basic auth depending on the credentials given
        if self.jamf_url and self.client_id and self.client_secret:
            token = self.handle_oauth(self.jamf_url, self.client_id, self.client_secret)
        elif self.jamf_url and self.jamf_user and self.jamf_password:
            token = self.handle_api_auth(
                self.jamf_url, self.jamf_user, self.jamf_password
            )
        else:
            raise ProcessorError("ERROR: Credentials not supplied")

        # Find the ID for the Patch Title
        obj_type = "patch_software_title"
        obj_name = self.patch_softwaretitle
        self.patch_softwaretitle_id = self.get_api_obj_id_from_name(
            self.jamf_url, obj_name, obj_type, token=token,
        )

        if not self.patch_softwaretitle_id:
            raise ProcessorError(
                f"ERROR: Couldn't find patch software title with name '{self.patch_softwaretitle}'.",
            )
        self.env["patch_softwaretitle_id"] = self.patch_softwaretitle_id

        # fetch the latest version reported by the Patch Title
        self.patch_version = self.latest_patch_version(
            self.jamf_url,
            self.patch_softwaretitle_id,
            token,
        )

        # Set Output Variable
        self.env["latest_patch_version"] = self.patch_version

if __name__ == "__main__":
    PROCESSOR = JamfPatchUploader()
    PROCESSOR.execute_shell()
