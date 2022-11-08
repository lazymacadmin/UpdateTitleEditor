#!/usr/local/autopkg/python

import os
import plistlib
import shutil
import xml
import subprocess
import json
import re
from collections import namedtuple
from datetime import datetime
from glob import glob

from base64 import b64encode
from autopkglib import ProcessorError
from autopkglib.FlatPkgUnpacker import FlatPkgUnpacker
from autopkglib.PkgPayloadUnpacker import PkgPayloadUnpacker

"""
Based off of NotifyPatchServer.py - \
https://github.com/autopkg/lrz-recipes/blob/main/SharedProcessors/NotifyPatchServer.py
########  2020 LRZ - Christoph Ostermeier

Set Title Editor URL
## Add TITLE_URL to your autopkg prefs -
    defaults write com.github.autopkg TITLE_URL https://your.title.url

## Add TITLE_USER and TITLE_PASS to your autopkg prefs -
    defaults write com.github.autopkg TITLE_USER title-editor-user
    defaults write com.github.autopkg TITLE_PASS "title-editor-pass"

"""

"""See docstring for UpdateTitleEditor class"""

__all__ = ["UpdateTitleEditor"]


class UpdateTitleEditor(PkgPayloadUnpacker, FlatPkgUnpacker):
    """
    This is a Post-Processor for AutoPkg.
    It unpacks the newly generated Package, searches for an App-Bundle and \
    extracts all Information needed forupdating Title Editor. The unpacked \
    data will be removed from disk afterwards.
    """

    description = __doc__

    input_variables = {
        "pkg_vers_key": {
            "required": False,
            "description": "Plist Version Key to read",
            },
        "patch_name": {
            "required": False,
            "description": "patch name for patch server.",
        },
        "forcevers": {
            "required": False,
            "description": "forced version from variable in previous step of \
            recipe",
        },
        "app_plist_path": {
            "required": False,
            "description": "path from cache_dir to app containing plist"
        },
        "app": {
            "required": False,
            "description": "plist file"
        },
        "debug": {
            "required": False,
            "description": "Flag to enable debugging"
        },
        "title_id": {
            "required": True,
            "description": "Title Editor ID"
        }
    }

    output_variables = {
        "patchJson": {
            "description": "patch data.",
            },
        "patch_id": {
            "description": "patch data.",
            },
        "verJson": {
            "description": "actual version string.",
            }
    }

    # Required for FlatPkgUnpacker
    source_path = None
    # Remove these directories after processing
    cleanupDirs = []

    def unpack(self):
        """Unpacks the Package file using other Processors"""
        # Emulate FlatPkgUnpacker/main-method
        self.env["destination_path"] = \
            os.path.join(self.env["RECIPE_CACHE_DIR"], "UnpackedPackage")
        self.cleanupDirs.append(self.env["destination_path"])
        self.output("Unpacking '%s' to '%s'" % (self.env["pkg_path"],
                    self.env["destination_path"]))
        self.source_path = self.env["pkg_path"]
        self.unpack_flat_pkg()
        # Emulate PkgPayloadUnpacker/main-method
        self.env["pkg_payload_path"] = \
            os.path.join(self.env["destination_path"], "Payload")
        # If there is a payload already, unpack it
        if os.path.isfile(self.env["pkg_payload_path"]):
            matches, app_glob_path = self.find_app()
        else:
            # Sometimes there is no Payload, so we have to find the .pkg which
            # contains it.
            pkgs = os.path.join(self.env["destination_path"], "*.pkg",
                                "Payload")
            payloadmatches = glob(pkgs)
            if len(payloadmatches) == 0:
                ProcessorError("No Subpackage found by globbing %s" % pkgs)
            else:
                for payloadmatch in payloadmatches:
                    self.env["pkg_payload_path"] = payloadmatch
                    matches, app_glob_path = self.find_app()
                    if len(matches) > 0:
                        break
        if len(matches) == 0:
            ProcessorError("No match found by globbing %s" % app_glob_path)
        elif len(matches) > 1:
            ProcessorError("Multiple matches found by globbing %s" %
                           app_glob_path)
        else:
            self.output("Found %s" % matches[0])
            return matches[0]

    def genPatchVersion(self, app_path):
        """Generates a PatchVersion based on the current AppBundle"""
        # Extract the Filename and open the Info.plist
        patch_title_id = self.env["title_id"]
        if self.env.get("app_plist_path"):
            app_path = self.env["app_plist_path"]
        filename = os.path.basename(app_path.rstrip("/"))
        info_plist_path = os.path.join(app_path, "Contents", "Info.plist")
        # Try to extract data to an hashtable
        try:
            with open(info_plist_path, 'rb') as fp:
                info_plist = plistlib.load(fp)
        except EnvironmentError as err:
            print('ERROR: {}'.format(err))
            raise SystemExit(1)
        except xml.parsers.expat.ExpatError:
            info_plist = self.read_binary_plist(info_plist_path)

        if self.env.get("forcevers"):
            pkgversion = self.env["forcevers"]
        elif self.env.get("pkg_vers_key"):
            pkgversion = info_plist[self.env["pkg_vers_key"]]
        else:
            pkgversion = self.env["version"]

        useVer = pkgversion
        """ Grab name (with spaces) and id (without spaces) + bundleId
            and Version from Info.plist"""
        name = filename.replace('.app', '')
        try:
            if self.env.get("patch_name"):
                patch_id = self.env["patch_name"]
            else:
                patch_id = info_plist["CFBundleName"].replace(' ', '')
        except KeyError:
            patch_id = name.replace(' ', '')
        patch_id = self.env["title_id"]
        bundle_id = info_plist["CFBundleIdentifier"]

        # If a minimumOperatingSystem is set, use that
        try:
            min_os = info_plist["LSMinimumSystemVersion"]
        except KeyError:
            min_os = "10.9"

        # get timestamps
        timestamp = datetime.utcfromtimestamp(
            os.path.getmtime(app_path)).strftime("%Y-%m-%dT%H:%M:%SZ")

        # generate patchData-
        patch = json.dumps(
            {"patchId": 0, "softwareTitleId": patch_id,
             "absoluteOrderId": 0, "version": useVer,
             "releaseDate": timestamp, "standalone": True,
             "minimumOperatingSystem": min_os, "reboot": False,
             "killApps": [{"bundleId": bundle_id,
                           "appName": filename}],
             "components": [{"name": name, "version": useVer,
                            "criteria": [{"name": "Application Bundle ID",
                                          "operator": "is", "value": bundle_id,
                                          "type": "recon", "and": True},
                                         {"name": "Application Version",
                                          "operator": "is", "value": useVer,
                                          "type": "recon"}]}],
             "capabilities": [{"name": "Operating System Version",
                               "operator": "greater than or equal",
                               "value": min_os, "type": "recon"}],
             "dependencies": []})
        self.debug_log("Patch json", patch)
        self.env['patchJson'] = patch
        verJson = json.dumps({"currentVersion": useVer,
                              "softwareTitleId": patch_id})
        self.env['verJson'] = verJson

        return patch_id, patch, verJson

    def get_enc_creds(self, user, password):
        if self.env.get("TITLE_USER") and self.env.get("TITLE_PASS"):
            username = self.env.get("TITLE_USER")
            password = self.env.get("TITLE_PASS")
        else:
            self.output("Title User and Pass are not in prefs")
            raise ProcessorError("No Title Editor Auth info supplied")

        """encode the username and password into a b64-encoded string"""
        credentials = f"{username}:{password}"
        enc_creds_bytes = b64encode(credentials.encode("utf-8"))
        enc_creds = str(enc_creds_bytes, "utf-8")
        return enc_creds

    def get_api_token(self, jamf_url, enc_creds):
        """get a token for the Jamf Pro API or
           Classic API for Jamf Pro 10.35+"""
        if self.env.get("TITLE_URL"):
            jamf_url = self.env.get("TITLE_URL")
        else:
            self.output("Title URL is not in prefs")
            raise ProcessorError("No Title Editor URL supplied")
        url = jamf_url + "/v2/auth/tokens"
        r, httpcode = self.curl(request="POST", url=url, enc_creds=enc_creds)
        try:
            token = str(r["token"])
            expires = str(r["expires"])

            return token
        except KeyError:
            self.output("ERROR: No token received")

    def curl(
            self,
            request="",
            url="",
            token="",
            enc_creds="",
            data="",
            additional_headers="",
            ):
        """ Setup the curl command """
        if url:
            curl_cmd = [
                "/usr/bin/curl",
                "--silent",
                "--show-error",
                url
            ]
            curl_cmd.extend(["--header", "Content-Type: application/json"])
            curl_cmd.extend(["-w", "\n%{http_code}"])
        else:
            raise ProcessorError("No URL supplied")

        if request:
            curl_cmd.extend(["--request", request])

        if enc_creds:
            curl_cmd.extend(["--header", f"Authorization: Basic {enc_creds}"])
        elif token:
            curl_cmd.extend(["--header", f"authorization: Bearer {token}"])

        if data:
            curl_cmd.extend(["--data", data])

        proc = subprocess.Popen(curl_cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        (out, err) = proc.communicate()

        length = len(out.decode())
        httpcode = int(out.decode()[-3:])

        self.debug_log("HTTP Code", httpcode)
        jsonload = out.decode()[0:length - 3]
        self.debug_log("Returned data", jsonload)
        jsonoutput = json.loads(jsonload)

        return jsonoutput, httpcode

    def notifyServer(self, id, patchData, currentData):
        if self.env.get("TITLE_URL"):
            my_url = self.env.get("TITLE_URL")
        else:
            self.output("Title URL is not in prefs")
            raise ProcessorError("No Title Editor URL supplied")

        if self.env.get("TITLE_USER") and self.env.get("TITLE_PASS"):
            username = self.env.get("TITLE_USER")
            password = self.env.get("TITLE_PASS")
        else:
            self.output("Title User and Pass are not in prefs")
            raise ProcessorError("No Title Editor Auth info supplied")

        enc_creds = self.get_enc_creds(username, password)
        authtoken = self.get_api_token(my_url, enc_creds)
        version = self.env["version"]
        title = self.env.get("NAME")

        """Sends the new PatchVersion to a PatchServer"""

        # Build url for the Patchtitle
        patchUrl = "%s/v2/softwaretitles/%s/patches" % (my_url, id)
        # Fire Request
        headers = {"Accept": "application/json"}
        r, httpcode = self.curl(request="POST", url=patchUrl,
                                additional_headers=headers,
                                token=authtoken, data=patchData)
        if httpcode in (200, 201):
            self.output("New version - setting currentVersion")
            versionUrl = "%s/v2/softwaretitles/%s" % (my_url, id)
            r, verhttpcode = self.curl(request="PUT", url=versionUrl,
                                       data=currentData, token=authtoken)
            # Get errors if any
            if verhttpcode not in (200, 201):
                raise ProcessorError("Error %s setting version for %s"
                                     % (verhttpcode, title))
        elif httpcode == 400:
            errData = r["errors"][0]["code"]
            if errData == 'DUPLICATE_RECORD':
                self.output("%s was already at this version" % title)
            else:
                raise ProcessorError("Error %s sending Patch-Data for %s: %s"
                                     % (httpcode, title, errData))
        else:
            raise ProcessorError("Error %s sending Patch-Data for %s: %s"
                                 % (httpcode, title, r))

    def cleanup(self):
        """Directory cleanup"""
        for directory in self.cleanupDirs:
            if os.path.isdir(directory):
                shutil.rmtree(directory)

    def main(self):
        app_path = self.unpack()
        patch_id, patchData, verJson = self.genPatchVersion(app_path)
        self.notifyServer(patch_id, patchData, verJson)
        self.cleanup()

    def find_app(self):
        """Helper Function to unpack Payloads"""
        self.env["destination_path"] = os.path.join(self.env["RECIPE_CACHE_DIR"],
                                                    "UnpackedPayload")
        self.cleanupDirs.append(self.env["destination_path"])
        self.output("Unpacking Payload to'%s'" % self.env["destination_path"])
        self.unpack_pkg_payload()
        # Find Application in unpacked Payload and return the Path
        # Try it in Apps Folder
        app_glob_path = os.path.join(self.env["destination_path"],
                                     "Applications", "*.app")
        matches = glob(app_glob_path)
        if len(matches) > 0:
            return matches, app_glob_path
        else:
            # Afterwards try it directly, fixes it for Virtualbox.
            app_glob_path = os.path.join(self.env["destination_path"], "*.app")
            return glob(app_glob_path), app_glob_path

    def read_binary_plist(self, plist_path):
        process = subprocess.Popen(
            ['plutil', '-convert', 'json', '-o', '-', plist_path],
            stdout=subprocess.PIPE
        )
        response = process.communicate()
        try:
            return json.loads(response[0])
        except ValueError:
            print('ERROR: Unable to read the application plist!')
            raise SystemExit(1)

    def debug_log(self,message,sub_string):
        ''' To use: add 
        self.debug_log("Text to desplay after DEBUG - ",variabledata)
        '''
        if self.env.get("debug"):
            print(("DEBUG - %s is %s") % (message, sub_string))

if __name__ == "__main__":
    PROCESSOR = UpdateTitleEditor()
    PROCESSOR.execute_shell()
