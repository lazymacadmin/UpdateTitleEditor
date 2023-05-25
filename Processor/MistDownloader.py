#!/usr/local/autopkg/python
#
# Processor to download the latest macOS installer
# in a given format

import plistlib
import subprocess
import os
import json 

from autopkglib import Processor, ProcessorError


__all__ = ["MistDownloader"]


class MistDownloader(Processor):
    description = ( "Downloads a macOS installer.",
    				"Need to specify OS and format" )
    input_variables = {
        "format": {
            "required": True,
            "description": "Installer format to be downloaded. Options: iso, image, package, application"
        },
        "type": {
            "required": True,
            "description": "Action to perform: download"
        },
        "macOS": {
            "required": True,
            "description": "Name of the macOS version to install. "
        }
    }
    output_variables = {
        "installer_path": {
             "description": "Path to the created installer."
        },
        "version": {
             "description": "macOS version"
        }
   }

    __doc__ = description

    def main(self):

        output_dir = self.env["RECIPE_CACHE_DIR"]
        version_cmd = [ "sudo", \
                    "/usr/local/bin/mist", \
                    "list", \
                    self.env[ "type" ], \
                    "--latest", \
                    self.env[ "macOS" ],\
                    "-o", \
                    "json", \
                    "-q" ]
        
        version_data = subprocess.check_output( version_cmd )
        #print(version_data)
        data = json.loads(version_data)
        version = data[0]['version']
        build = data[0]['build']
        #print(version)
    	# rename unsigned package so that we can slot the signed package into place
        command_line_list = [ "sudo", \
                              "/usr/local/bin/mist", \
                              "download", \
                              self.env[ "type" ], \
                              self.env[ "macOS" ], \
                              self.env[ "format" ], \
                              "--output-directory", \
                              output_dir, \
                              "-q" ]

        #print(command_line_list)

        # print command_line_list
        #subprocess.call( command_line_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL )
        subprocess.call( command_line_list, stderr=subprocess.DEVNULL )
        installer_path = os.path.join(self.env["RECIPE_CACHE_DIR"], "Install "+ self.env["macOS"] + " " + version + "-" + build + ".pkg")
        subprocess.call( ["sudo", "/bin/chmod", "777", installer_path] )

        self.env['installer_path'] = installer_path
        self.env['version'] = version
        return installer_path, version



if __name__ == '__main__':
    processor = MistDownloader()
    processor.execute_shell()
